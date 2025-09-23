# test_app.py
import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test if we can import the app
try:
    from app import app
    print("App imported successfully!")
    
    # Test if we can import models
    from models import db, User, Fetish, Interest, Match, Message
    print("Models imported successfully!")
    
    print("All imports successful! The app should work correctly.")
    
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()