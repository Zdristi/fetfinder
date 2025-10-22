# render_wsgi.py
import sys
import os

# Add the project directory to the Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import the Flask app and create tables
from app import app, create_tables

# Create tables when starting the app
with app.app_context():
    create_tables()

# For WSGI servers
if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)