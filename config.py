# Configuration file for Render
import os

# Enable debug mode for development
DEBUG = False if os.environ.get('FLASK_ENV') == 'production' else True

# Secret key for sessions
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fetfinder.db')
# Handle PostgreSQL URL format for SQLAlchemy
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# SQLAlchemy configuration
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Upload folder
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')

# Google OAuth (if you want to use it)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Host and Port
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 5000))