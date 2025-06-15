#dependancies
import cv2
import os
import numpy as np
from deepface import DeepFace
from picamera2 import Picamera2
import time
from datetime import datetime
from mtcnn import MTCNN
from scipy.spatial.distance import cosine
import RPi.GPIO as GPIO
from pyzbar.pyzbar import decode
import threading
import base64
import socketio
from pymongo import MongoClient
import certifi
from queue import Queue
import concurrent.futures
from cryptography.fernet import Fernet

sio = socketio.Client() # Initialize SocketIO

# Configuration
LOCAL_WS_URL = "http://<ip_address>:<port>"   
WIDTH, HEIGHT = 640, 480
FACE_RECOGNITION_INTERVAL = 5  # Process every 20th frame
SIMILARITY_THRESHOLD = 0.5
GATE_OPEN_TIME = 5  # seconds
GATE_CYCLE = 0
gate_status = 'closed'

# GPIO setup for gate control
GATE_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(GATE_PIN, GPIO.OUT)

# MongoDB Atlas connection, do not hardcode use environment variables
MONGO_URI = "mongodb+srv://<username>:<password>(nD@cluster0.ryakn.mongodb.net/Access_Control_System?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['Access_Control_Database']
permanent_users = db['Permanent_Users']
temporal_users = db['Temporal_Users']
access_logs = db['Access_Log']

# Global variables
frame_queue = Queue(maxsize=1)  
running = True
user_cache = {}  # Cache user data from MongoDB

executor = concurrent.futures.ThreadPoolExecutor(max_workers=2) # ThreadPoolExecutor for parallel processing

API_SECRET = 'apisecret'
SECRET_KEY = b'<your_symmetric_key>' 

# Initialize the Raspberry Pi camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (WIDTH, HEIGHT)}))
picam2.start()
time.sleep(2.0)  # Allow the camera to warm up

detector = MTCNN()# Load MTCNN for face detection - initialize once

#Handle connection to client (web app)
@sio.event
def connect():
    print('Connected to server')
    load_user_data() # Pre-fetch and cache user data on connection

#Handle disconnection to client (web app)
@sio.event
def disconnect():
    print('Disconnected from server')

#Handle connection errors
@sio.event
def connect_error(data):
    print(f'Connection error: {data}')
    if '401' in str(data):
        print("Invalid API secret. Please check your configuration")

#Handle remote gate commands
@sio.on('gate_command')
def handle_gate_command(data):
    command = data.get('command')
    if command == 'open':
        log_access(datetime.now(), "Admin", "Granted", "Trusted Client")
        open_gate()
    elif command == 'close':
        close_gate()

#function to open the gate
def open_gate():
    try:
        global gate_status
        GPIO.output(GATE_PIN, GPIO.HIGH)
        gate_status = 'open'
        time.sleep(GATE_OPEN_TIME)
        close_gate()
    except Exception as e:
        print(f"Error opening gate: {e}")

#function to close the gate
def close_gate():
    try:
        global gate_status
        GPIO.output(GATE_PIN, GPIO.LOW)
        gate_status = 'closed'
    except Exception as e:
        print(f"Error closing gate: {e}")

#function to compute facial embeddings from a detected face
def get_face_embedding(face_img):
    try:
        embedding_dict = DeepFace.represent(face_img, model_name="ArcFace", enforce_detection=False)
        embedding = embedding_dict[0]["embedding"]
        return embedding
    
    except Exception as e:
        print(f"Error computing face embedding: {e}")
        return None

#Function to cache permanent users from MongoDB
def load_user_data():
    try:
        users = list(permanent_users.find({}, {'Face Embedding': 1, 'Full Name': 1}))
        for user in users:
            user_cache[user['Full Name']] = user['Face Embedding']
        print(f"Loaded {len(users)} users into cache")
    except Exception as e:
        print(f"Error loading user data: {e}")

#Function to generate frames from the camera
def generate_frames():
    frame_count = 0
    
    while running:
        try:
            frame_bgr = picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGRA2BGR).astype(np.uint8)
            gpu_frame = cv2.UMat(frame_rgb) # Upload frame to GPU
            frame_count += 1
            
            # Process only every 5th frame for face recognition
            if frame_count % FACE_RECOGNITION_INTERVAL == 0:
                if not frame_queue.full():
                    frame_queue.put(gpu_frame)
            
            current_frame = cv2.cvtColor(gpu_frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', current_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            
            sio.emit('video_frame', {
                'frame': frame_base64,
            })
            time.sleep(0.04)  #25 FPS

        except Exception as e:
            print(f"Error in generate_frames: {e}")
            time.sleep(1)

#Function for face matching
def recognize_face(face_roi):
    try:
        if face_roi is None or face_roi.size == 0:
            return "Unknown"
            
        # Get embedding with caching
        face_embedding = get_face_embedding(face_roi)
        if face_embedding is None:
            return "Unknown"

        # Compare with cached user data
        similarity_scores = []
        for name, embedding in user_cache.items():
            similarity = 1 - cosine(face_embedding, embedding)
            similarity_scores.append((similarity, name))

        # Find the maximum similarity score
        if similarity_scores:
            max_similarity, best_match = max(similarity_scores, key=lambda x: x[0])
            
            if max_similarity > SIMILARITY_THRESHOLD:
                print(f"\nBest Match Score with {best_match}: {max_similarity:.4f}")
                return best_match
            
            print(f"Best similarity score: {max_similarity:.4f} with {best_match} (below threshold)")
        return "Unknown"

    except Exception as e:
        print(f"Error recognizing face: {e}")
        return "Unknown"

#Function for QR code data matching
def verify_qr_data(qr_data):
    try:
        decrypted_data = decrypt_qr_data(qr_data)
        if not decrypted_data:
            print("? Invalid QR Code: Decryption failed")
            return "Unknown"
        temp_user = temporal_users.find_one(
            {"QR Code": qr_data},  
            {"registration_time": 0, "expiration_time": 0}
        )
        if temp_user:
            return temp_user.get("Full Name", "Unknown")
        return "Unknown"
    
    except Exception as e:
        print(f"Error verifying QR data: {e}")
        return "Unknown"
    
# Function to decrypt QR code data
def decrypt_qr_data(encrypted_data):
    try:
        cipher = Fernet(SECRET_KEY)
        decoded_data = base64.urlsafe_b64decode(encrypted_data)  # Decode from Base64
        decrypted_data = cipher.decrypt(decoded_data)  # Decrypt using Fernet
        return decrypted_data.decode('utf-8')  # Convert bytes to string
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

#Function for user authentication
def process_frame():
    while running:
        try:
            if not frame_queue.empty():
                gpu_frame = frame_queue.get()
                frame_rgb = cv2.UMat.get(gpu_frame) # Download frame from GPU to CPU for MTCNN
                faces = detector.detect_faces(frame_rgb) # Detect faces using MTCNN
                
                if faces:
                    face = faces[0] # Process the first detected face (most prominent)
                    x, y, w, h = face["box"]
                    x, y, w, h = max(0, x), max(0, y), abs(w), abs(h)
                    
                    x2, y2 = min(frame_rgb.shape[1], x + w), min(frame_rgb.shape[0], y + h) # Ensure face coordinates are within frame boundaries
                    face_roi = frame_rgb[y:y2, x:x2]
                    
                    # Skip if face ROI is too small
                    if face_roi.size == 0 or face_roi.shape[0] < 20 or face_roi.shape[1] < 20:
                        continue
                    
                    future = executor.submit(recognize_face, face_roi) # Submit face recognition to thread pool
                    name = future.result(timeout=3)  # Set timeout to prevent long waits
                    
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    
                    # Handle access based on recognition result
                    if name != "Unknown":
                        log_access(datetime.now(), name, "Granted", "Face recognized")
                        open_gate()
                        print(f"Access Granted to {name}")
                        clear_queue() # clear queue
                    
                    else:
                        # Check for QR code only if face is not recognized
                        qr_codes = decode(frame_rgb)
                        if qr_codes:
                            qr_data = qr_codes[0].data.decode("utf-8")
                            print(f"QR Code Data: {qr_data}")
                            
                            temp_name = verify_qr_data(qr_data)
                            
                            if temp_name != "Unknown":
                                log_access(datetime.now(), temp_name, "Granted", "QR code recognized")
                                open_gate()
                                print(f"Access Granted to {temp_name} via QR")
                                clear_queue() # clear queue
                            else:
                                log_access(datetime.now(), "Unknown", "Denied", "Invalid QR code") 
                        else:
                            log_access(datetime.now(), "Unknown", "Denied", "No valid identification")
                
                else:
                    # No faces detected, check QR codes
                    qr_codes = decode(frame_rgb)
                    if qr_codes:
                        qr_data = qr_codes[0].data.decode("utf-8")
                        print(f"QR Code Data: {qr_data}")
                        temp_name = verify_qr_data(qr_data)
                        
                        if temp_name != "Unknown":
                            log_access(datetime.now(), temp_name, "Granted", "QR code recognized")
                            open_gate()
                            print(f"Access Granted to {temp_name} via QR")
                            clear_queue() # clear queue
                        else:
                            log_access(datetime.now(), "Unknown", "Denied", "Invalid QR code")
                
        except Exception as e:
            print(f"Error in process_frame: {e}")

#Function to the frame queue after granting access to avoid multiple gate opening for the same person, since the processor is slow
def clear_queue():
    with frame_queue.mutex:
        frame_queue.queue.clear()

def log_access(timestamp, user_name, status, reason):
    try:
        # Create log document
        log_doc = {
            'Timestamp': timestamp,
            'User Name': user_name,
            'Status': status,
            'Reason': reason
        }
        access_logs.insert_one(log_doc)# Insert in database
        
    except Exception as e:
        print(f"Error logging access: {e}")

def periodic_cache_refresh():
    while running:
        try:
            time.sleep(300)  # Refresh every 5 minutes
            load_user_data()
        except Exception as e:
            print(f"Error in periodic cache refresh: {e}")

def start_application():
    try:
        # Connect to local WebSocket server
        sio.connect(
            LOCAL_WS_URL
            #headers={'X-API-SECRET': API_SECRET}
            )
        
        # Start frame processing thread
        processing_thread = threading.Thread(target=process_frame)
        processing_thread.daemon = True
        processing_thread.start()

        # Start video streaming thread
        streaming_thread = threading.Thread(target=generate_frames)
        streaming_thread.daemon = True
        streaming_thread.start()
        
        #Thread for periodic permanent user caching
        refresh_thread = threading.Thread(target=periodic_cache_refresh)
        refresh_thread.daemon = True
        refresh_thread.start()
        
        # Keep main thread alive
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")
    finally:
        cleanup()

def cleanup():
    global running
    running = False
    
    executor.shutdown(wait=False) # Shutdown thread pool
    picam2.stop() # Release camera
    GPIO.cleanup() # Clean up GPIO
    
    # Disconnect from Socket.IO
    if sio.connected:
        sio.disconnect()

if __name__ == "__main__":
    try:
        start_application()
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        cleanup()
