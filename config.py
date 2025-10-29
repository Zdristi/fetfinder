# Configuration file for local development and production
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Debug mode - enabled by default for development, disabled for production
    DEBUG = False if os.environ.get('FLASK_ENV') == 'production' else True
    
    # Secret key for sessions - must be set in environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in environment variables")
    
    # Database configuration - can be SQLite or PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fetdate_local.db')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@fetdate.com')
    
    # Check if required email configuration is present
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("Warning: Email credentials not set in environment variables")
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/oauth/google/callback')
    
    # reCAPTCHA configuration
    RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')
    
    # Host and Port
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Engine options for SQLite/PostgreSQL
    DEFAULT_ENGINE_OPTIONS = {
        'poolclass': None,  # No pooling for SQLite, adjust for production databases
        'connect_args': {
            'check_same_thread': False  # Required for Flask-SQLAlchemy with threading
        }
    }
    
    # Export the engine options
    SQLALCHEMY_ENGINE_OPTIONS = DEFAULT_ENGINE_OPTIONS


# Create configuration instance
config = Config()

