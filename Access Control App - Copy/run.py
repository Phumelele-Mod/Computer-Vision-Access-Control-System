from app import create_app, socketio
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = create_app()

atexit.register(lambda: BackgroundScheduler().shutdown())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)