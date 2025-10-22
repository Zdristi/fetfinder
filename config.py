# Configuration file for Render
import os

# Enable debug mode for development
DEBUG = False if os.environ.get('FLASK_ENV') == 'production' else True

# Secret key for sessions - using a fixed key for persistent sessions across restarts
import secrets
SECRET_KEY = os.environ.get('SECRET_KEY', 'your_fixed_secret_key_for_local_development_please_change_in_production_5a7b9c3d1e2f4a6b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fetdate_local.db')

# Handle PostgreSQL URL format for SQLAlchemy
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
elif DATABASE_URL.startswith('mysql://'):
    # MySQL configuration for hosting
    pass

# Configure SSL options for PostgreSQL - using 'prefer' mode for better Render compatibility
if 'postgresql://' in DATABASE_URL and 'render.com' in DATABASE_URL:
    # For Render PostgreSQL, add SSL parameters with 'prefer' mode
    if '?' not in DATABASE_URL:
        DATABASE_URL += "?sslmode=prefer"
    else:
        DATABASE_URL += "&sslmode=prefer"

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
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'sup.fetdate@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')  # Пароль приложения Gmail
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'sup.fetdate@gmail.com')

# Google OAuth (if you want to use it)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Host and Port
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 5000))

# Additional engine options for PostgreSQL on Render
if 'postgresql://' in DATABASE_URL:
    DEFAULT_ENGINE_OPTIONS = {
        'pool_size': 3,
        'pool_recycle': 299,
        'pool_pre_ping': True,
        'pool_timeout': 20,
        'max_overflow': 5,
        'connect_args': {
            'connect_timeout': 20,
            'sslmode': 'prefer',  # Changed to 'prefer' for better Render compatibility
            'keepalives_idle': 299,
            'keepalives_interval': 29,
            'keepalives_count': 5
        }
    }
else:
    DEFAULT_ENGINE_OPTIONS = {}

# For cPanel hosting compatibility
if 'pythonanywhere' in os.environ.get('HOSTNAME', '') or os.environ.get('CPANEL_HOSTING'):
    # Configuration for shared hosting like HostIQ.ua
    if 'postgresql://' in DATABASE_URL:
        # Update existing options if PostgreSQL is configured
        if 'DEFAULT_ENGINE_OPTIONS':
            DEFAULT_ENGINE_OPTIONS.update({
                'pool_pre_ping': True,
                'pool_recycle': 300,
            })
    else:
        # Default options for non-PostgreSQL databases
        DEFAULT_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }

# Export the engine options
SQLALCHEMY_ENGINE_OPTIONS = DEFAULT_ENGINE_OPTIONS

