from pymongo import MongoClient
import certifi
from config import Config
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

client = MongoClient(Config.MONGODB_URI, tlsCAFile=certifi.where())

db = client['Access_Control_Database']
permanent_users = db['Permanent_Users']
temporal_users = db['Temporal_Users']
access_logs = db['Access_Log']
admin_users = db['Admin_Users']  

class Admin(UserMixin):
    def __init__(self, username, password_hash):
        self.id = username  
        self.username = username
        self.password_hash = password_hash

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def authenticate(username, password):
        admin_data = admin_users.find_one({'username': username})
        if admin_data and check_password_hash(admin_data['password_hash'], password):
            return Admin(username, admin_data['password_hash'])
        return None

    @staticmethod
    def change_password(username, old_password, new_password):
        admin_data = admin_users.find_one({'username': username})
        if admin_data and check_password_hash(admin_data['password_hash'], old_password):
            new_password_hash = generate_password_hash(new_password)
            admin_users.update_one(
                {'username': username},
                {'$set': {'password_hash': new_password_hash}}
            )
            return True
        return False

# Initializing admin user 
if admin_users.count_documents({}) == 0:
    admin_users.insert_one({
        'username': 'admin',
        'password_hash': generate_password_hash('admin123')
    })

def add_permanent_user(full_name, email, face_embedding):
    permanent_users.insert_one({
        'Full Name': full_name,
        'Email': email,
        'Registration Time': datetime.utcnow(), 
        'Face Embedding': face_embedding
    })

def add_temporal_user(full_name, email, reason, duration, registration_time, expiration_time, qr_code):

    temporal_users.insert_one({
        'Full Name': full_name,
        'Email': email,
        'Reason of Visit': reason,
        'Duration (hours)': duration,
        'Registration Time': registration_time,  
        'Expiration Time': expiration_time,  
        'QR Code': qr_code
    })

def log_access(timestamp, user_name, status, reason):
    access_logs.insert_one({
        'Timestamp': timestamp,
        'User Name': user_name,
        'Status': status,
        'Reason': reason
    })
