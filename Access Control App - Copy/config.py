from decouple import config

class Config:
    MONGODB_URI = config('MONGODB_URI') 
    SECRET_KEY = config('SECRET_KEY', default='your-secret-key')
    API_SECRET = config('API_SECRET', default='your-api-secret')
    MAIL_USERNAME = config('MAIL_USERNAME', default='your-mail-username')
    MAIL_PASSWORD = config('MAIL_PASSWORD', default='your-mail-password')
    MAIL_DEFAULT_SENDER = config('MAIL_DEFAULT_SENDER', default='your-mail-default-sender') 
    MAIL_SERVER = config('MAIL_SERVER', default='your-mail-server') 
    QR_CODE_SECRET = config('QR_CODE_SECRET', default='your-qr-code-secret')
    GATE_PIN = config('GATE_PIN', default='your-gate-pin')
    MAIL_PORT = config('MAIL_PORT', default=587, cast=int)  
    MAIL_USE_TLS = config('MAIL_USE_TLS', default=True, cast=bool)
    