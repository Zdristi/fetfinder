#!/usr/bin/env python3
"""
Main application runner for FetDate
Implements secure configuration loading and proper error handling
"""

import os
import sys
from app import app, db
from config import config

def create_app():
    """Factory function to create and configure the Flask app."""
    # Configure the app from our config object
    app.config.from_object(config)
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
            sys.exit(1)
    
    return app

if __name__ == "__main__":
    # Create the app with proper configuration
    application = create_app()
    
    # Run the application
    try:
        application.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)