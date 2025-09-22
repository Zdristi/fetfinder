import os
from app import app, create_tables

if __name__ == "__main__":
    # Create database tables
    create_tables()
    
    # For Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)