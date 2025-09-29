import sys
import os

# Add the project directory to the Python path
path = '/home/your_username/fetdate'
if path not in sys.path:
    sys.path.append(path)

# Change to the project directory
os.chdir(path)

# Import the Flask app
from app import app as application

# For debugging purposes
if __name__ == '__main__':
    application.run()