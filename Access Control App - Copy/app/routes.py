from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify, flash, Response
from app.models import add_permanent_user, add_temporal_user, permanent_users, temporal_users, access_logs, log_access
import qrcode
from io import BytesIO
import numpy as np
from bson import ObjectId
import os
import cv2
import time
from datetime import datetime, timedelta
import base64
import json
from mtcnn import MTCNN  
from deepface import DeepFace
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Admin
import csv
from io import StringIO
from flask_socketio import emit
from app import socketio  
from flask_mail import Mail, Message
import app
from functools import wraps
from config import Config
from cryptography.fernet import Fernet

# Create a Blueprint for the routes
routes_blueprint = Blueprint('routes', __name__)
mail = Mail()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('video_frame')
def handle_video_frame(data):
    socketio.emit('update_frame', data)

@socketio.on('gate_status')
def handle_gate_status(data):
    socketio.emit('update_gate_status', data)

cipher = Fernet(Config.QR_CODE_SECRET.encode())

def encrypt_data(data):
    json_data = json.dumps(data)  
    encrypted_data = cipher.encrypt(json_data.encode())  
    return base64.urlsafe_b64encode(encrypted_data).decode()  

# Login route
@routes_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.authenticate(username, password)
        if admin:
            login_user(admin)  
            return redirect(url_for('routes.index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

# Logout route
@routes_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('routes.login'))

@routes_blueprint.route('/live_feed')
@login_required
def live_feed():
    return render_template('live_feed.html')

@routes_blueprint.route('/gate_control', methods=['GET', 'POST'])
@login_required
def gate_control():
    if request.method == 'POST':
        action = request.form.get('action')
        print(f"Emitting gate command: {action}")
        socketio.emit('gate_command', {
            'command': action
        })
        flash(f'Gate {action} command sent')
    return render_template('gate_control.html')

@routes_blueprint.route('/')
@login_required
def index():
    return render_template('index.html')

@routes_blueprint.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        full_name = request.form.get('full_name')
        email = request.form.get('email')

        if user_type == 'permanent':
            # Handle image upload and face recognition
            if 'face_image' not in request.files:
                return "No image uploaded", 400
            face_image = request.files['face_image']
            if face_image.filename == '':
                return "No image selected", 400

            # Save the image temporarily
            image_path = f"temp_{face_image.filename}"
            face_image.save(image_path)

            try:
                image = cv2.imread(image_path)
                if image is None:
                    return "Invalid image file. Please upload a valid image.", 400

                face_embedding_dict = DeepFace.represent(image, model_name="ArcFace", enforce_detection=False)
                face_embedding = face_embedding_dict[0]["embedding"]
                add_permanent_user(full_name, email, face_embedding)

            except Exception as e:
                return f"Error processing image: {str(e)}", 400

            finally:
                if os.path.exists(image_path):
                    os.remove(image_path)

        else:
            reason = request.form.get('reason')
            duration = request.form.get('duration')
            registration_time = datetime.utcnow()
            expiration_time = registration_time + timedelta(hours=int(duration))

            # Prepare user data for QR code
            temporal_user = {
                'Full Name': full_name,
                'Email': email,
                'Reason': reason,
                'Duration (hours)': duration,
                'Registration Time': registration_time.isoformat(),
                'Expiration Time': expiration_time.isoformat()
            }

            # Encrypt the data before generating the QR code
            encrypted_content = encrypt_data(temporal_user)

            # Generate QR code

            qr = qrcode.QRCode(
                version=11,  # Use version 11
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
                box_size=10,  # Each module is 10x10 pixels
                border=5  # 5-module-wide quiet zone
            )

            qr.add_data(encrypted_content)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            img_bytes = BytesIO()
            img.save(img_bytes)
            img_bytes.seek(0)

            # Send email with encrypted QR code
            msg = Message(
                subject="Your Secure QR Code for Access",
                recipients=[email],
                sender=Config.MAIL_DEFAULT_SENDER
            )
            msg.body = f"Dear {full_name},\n\nPlease find your QR code attached for access.\n\nReason: {reason}\nQR Code Validity: {duration} hours"
            msg.attach("qrcode.png", "image/png", img_bytes.getvalue())
            mail.send(msg)
            flash('Temporal user registered and secure QR code sent via email.', 'success')
            add_temporal_user(full_name, email, reason, duration, registration_time, expiration_time)

            return redirect(url_for('routes.index'))

    return render_template('register.html')

@routes_blueprint.route('/logs')
@login_required
def logs():
    logs = list(access_logs.find().sort('Timestamp', -1).limit(100))  # Get latest 100 logs
    return render_template('logs.html', logs=logs)

@routes_blueprint.route('/view_users')
@login_required
def view_users():
    permanent_users_list = list(permanent_users.find())
    temporal_users_list = list(temporal_users.find())
    return render_template('view_users.html', 
                         permanent_users=permanent_users_list, 
                         temporal_users=temporal_users_list)

@routes_blueprint.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    data = request.get_json()
    user_type = data.get('user_type')
    user_id = data.get('user_id')

    try:
        if user_type == 'permanent':
            result = permanent_users.delete_one({'_id': ObjectId(user_id)})
        elif user_type == 'temporal':
            result = temporal_users.delete_one({'_id': ObjectId(user_id)})
        else:
            return jsonify({'success': False, 'message': 'Invalid user type'}), 400

        if result.deleted_count == 1:
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@routes_blueprint.route('/export_logs')
@login_required
def export_logs():
    logs = list(access_logs.find().sort('Timestamp', -1).limit(100))  
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(['Timestamp', 'User Name', 'Status', 'Reason'])

    for log in logs:
        timestamp_str = log['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')  
        csv_writer.writerow([
            timestamp_str,  
            log['User Name'],
            log['Status'],
            log['Reason']
        ])

    response = Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=access_logs.csv'
        }
    )
    return response

def init_app(app):
    socketio.init_app(app)