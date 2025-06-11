from flask import Flask
from config import Config
from flask_socketio import SocketIO
from flask_login import LoginManager
from .models import Admin
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import temporal_users
from datetime import datetime
from datetime import timedelta

socketio = SocketIO()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return Admin(user_id, "admin123") if user_id == "admin" else None

login_manager.login_view = "routes.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

def delete_expired_users():
    current_time = datetime.utcnow()
    result = temporal_users.delete_many({'Expiration Time': {'$lt': current_time}})
    print(f"Deleted {result.deleted_count} expired temporal users.")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(minutes=20)  # 30-minute session timeout
    app.config.from_object(Config)
    socketio.init_app(app)
    login_manager.init_app(app)
    from app.routes import routes_blueprint, mail
    routes_blueprint.app = app
    mail.init_app(app)
    app.register_blueprint(routes_blueprint)
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=delete_expired_users, trigger='interval', minutes=5)  # Run every 5 minutes
    scheduler.start()
    return app

