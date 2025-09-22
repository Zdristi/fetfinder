import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, create_tables

if __name__ == '__main__':
    create_tables()
    print("Database tables created successfully!")