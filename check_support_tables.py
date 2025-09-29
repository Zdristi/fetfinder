#!/usr/bin/env python3
"""
Check database schema for support tables
"""

import sqlite3
import os

def check_support_tables():
    """Check support ticket tables schema"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    print(f"Checking support ticket tables in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check support_ticket table schema
        cursor.execute("PRAGMA table_info(support_ticket)")
        ticket_columns = cursor.fetchall()
        print("\nSupport Ticket Table Schema:")
        for col in ticket_columns:
            print(f"  {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''} {'NOT NULL' if col[3] else ''}")
        
        # Check support_message table schema
        cursor.execute("PRAGMA table_info(support_message)")
        message_columns = cursor.fetchall()
        print("\nSupport Message Table Schema:")
        for col in message_columns:
            print(f"  {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''} {'NOT NULL' if col[3] else ''}")
        
        # Check foreign keys
        cursor.execute("PRAGMA foreign_key_list(support_ticket)")
        ticket_fk = cursor.fetchall()
        print("\nSupport Ticket Foreign Keys:")
        for fk in ticket_fk:
            print(f"  {fk[2]}.{fk[3]} -> {fk[4]}.{fk[5]}")
        
        cursor.execute("PRAGMA foreign_key_list(support_message)")
        message_fk = cursor.fetchall()
        print("\nSupport Message Foreign Keys:")
        for fk in message_fk:
            print(f"  {fk[2]}.{fk[3]} -> {fk[4]}.{fk[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking support ticket tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_support_tables()