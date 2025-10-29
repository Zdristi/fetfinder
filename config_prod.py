import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Используем переменную окружения для DATABASE_URL
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # Опции для SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Опции для gunicorn
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 8080))
    
    # Другие настройки приложения
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'sup.fetdate@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'sup.fetdate@gmail.com')
    
    # Настройки кэширования
    CACHE_TYPE = 'null'
    CACHE_DEFAULT_TIMEOUT = 0
    
    # Настройки upload-папки
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
    
    # Дополнительные настройки для production
    DEBUG = False
    TESTING = False
    
    # Настройки для безопасности сессий
    PERMANENT_SESSION_LIFETIME = 2592000  # 30 дней в секундах