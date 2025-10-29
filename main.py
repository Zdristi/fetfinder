import os
from app import app, db
from config import config

# Create database tables when the module is imported
try:
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
except Exception as e:
    print(f"Error creating database tables: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    # For local development
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)