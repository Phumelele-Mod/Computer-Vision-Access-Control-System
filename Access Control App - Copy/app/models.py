from pymongo import MongoClient
import certifi
from config import Config
from flask_login import UserMixin
from datetime import datetime

client = MongoClient(Config.MONGODB_URI, tlsCAFile=certifi.where())

db = client['Access_Control_Database']
permanent_users = db['Permanent_Users']
temporal_users = db['Temporal_Users']
access_logs = db['Access_Log']

class Admin(UserMixin):
    def __init__(self, username, password):
        self.id = username  
        self.username = username
        self.password = password

    @staticmethod
    def authenticate(username, password):
        admin_username = "admin"
        admin_password = "admin123"

        if username == admin_username and password == admin_password:
            return Admin(username, password)
        return None

def add_permanent_user(full_name, email, face_embedding):
    permanent_users.insert_one({
        'Full Name': full_name,
        'Email': email,
        'Registration Time': datetime.utcnow(), 
        'Face Embedding': face_embedding
    })

def add_temporal_user(full_name, email, reason, duration, registration_time, expiration_time):

    temporal_users.insert_one({
        'Full Name': full_name,
        'Email': email,
        'Reason of Visit': reason,
        'Duration (hours)': duration,
        'Registration Time': registration_time,  
        'Expiration Time': expiration_time  
    })

def log_access(timestamp, user_name, status, reason):
    access_logs.insert_one({
        'Timestamp': timestamp,
        'User Name': user_name,
        'Status': status,
        'Reason': reason
    })