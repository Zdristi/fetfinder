#!/usr/bin/env python3
"""
Script to add new columns to the existing user table
"""

import sqlite3
import os

def update_db_columns():
    """Add new columns to the user table"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Please run create_all_tables.py first.")
        return
    
    print(f"Updating database {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user);")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add match_by_city column if it doesn't exist
        if 'match_by_city' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN match_by_city BOOLEAN DEFAULT 0;")
            print("Added match_by_city column")
        else:
            print("match_by_city column already exists")
            
        # Add match_by_country column if it doesn't exist
        if 'match_by_country' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN match_by_country BOOLEAN DEFAULT 0;")
            print("Added match_by_country column")
        else:
            print("match_by_country column already exists")
        
        conn.commit()
        conn.close()
        
        print("Database updated successfully!")
    
    except Exception as e:
        print(f"Error updating database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    update_db_columns()