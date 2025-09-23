import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, create_tables, import_data

if __name__ == '__main__':
    create_tables()
    print("Database tables created successfully!")
    
    # Try to import data from backup if it exists
    try:
        import_data()
        print("Data imported from backup successfully!")
    except Exception as e:
        print(f"No backup data to import or import failed: {e}")