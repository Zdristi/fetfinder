#!/usr/bin/env python3
"""
List all tables in the database
"""

import sqlite3
import os

def list_database_tables():
    """List all tables in the database"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    print(f"Listing tables in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error listing tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    list_database_tables()