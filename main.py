import os
from app import app

if __name__ == "__main__":
    # Create database tables
    from app import create_tables
    create_tables()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))