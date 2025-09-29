#!/usr/bin/env python3
"""
Test script for support chat system
"""

import sqlite3
import os
from datetime import datetime

def test_support_system():
    """Test support chat system"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    print(f"Testing support chat system in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test tables existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('support_ticket', 'support_message')")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("Existing support tables:")
        for table in existing_tables:
            print(f"  - {table}")
        
        # Test table schemas
        print("\nTable Schemas:")
        
        cursor.execute("PRAGMA table_info(support_ticket)")
        ticket_columns = cursor.fetchall()
        print("  Support Ticket:")
        for col in ticket_columns:
            print(f"    {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''}")
        
        cursor.execute("PRAGMA table_info(support_message)")
        message_columns = cursor.fetchall()
        print("  Support Message:")
        for col in message_columns:
            print(f"    {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''}")
        
        # Test foreign keys
        print("\nForeign Keys:")
        
        cursor.execute("PRAGMA foreign_key_list(support_ticket)")
        ticket_fk = cursor.fetchall()
        print("  Support Ticket:")
        for fk in ticket_fk:
            print(f"    -> {fk[2]}.{fk[3]} references {fk[4]}.{fk[5]}")
        
        cursor.execute("PRAGMA foreign_key_list(support_message)")
        message_fk = cursor.fetchall()
        print("  Support Message:")
        for fk in message_fk:
            print(f"    -> {fk[2]}.{fk[3]} references {fk[4]}.{fk[5]}")
        
        # Test sample data
        print("\nSample Data:")
        
        # Check if there are any support tickets
        cursor.execute("SELECT COUNT(*) FROM support_ticket")
        ticket_count = cursor.fetchone()[0]
        print(f"  Support Tickets: {ticket_count}")
        
        # Check if there are any support messages
        cursor.execute("SELECT COUNT(*) FROM support_message")
        message_count = cursor.fetchone()[0]
        print(f"  Support Messages: {message_count}")
        
        if ticket_count > 0:
            cursor.execute("SELECT id, user_id, subject, status FROM support_ticket LIMIT 5")
            tickets = cursor.fetchall()
            print("  Sample Tickets:")
            for ticket in tickets:
                print(f"    ID: {ticket[0]}, User: {ticket[1]}, Subject: {ticket[2]}, Status: {ticket[3]}")
        
        if message_count > 0:
            cursor.execute("SELECT id, ticket_id, sender_id, content, is_admin FROM support_message LIMIT 5")
            messages = cursor.fetchall()
            print("  Sample Messages:")
            for msg in messages:
                print(f"    ID: {msg[0]}, Ticket: {msg[1]}, Sender: {msg[2]}, Content: {msg[3][:50]}..., Is Admin: {bool(msg[4])}")
        
        conn.close()
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error testing support chat system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_support_system()