#!/usr/bin/env python3
"""
Check test data in support chat system
"""

import sqlite3
import os

def check_test_data():
    """Check test data in support chat system"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    print(f"Checking test data in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"Total users: {user_count}")
        
        # Check support tickets
        cursor.execute("SELECT COUNT(*) FROM support_ticket")
        ticket_count = cursor.fetchone()[0]
        print(f"Total support tickets: {ticket_count}")
        
        # Check support messages
        cursor.execute("SELECT COUNT(*) FROM support_message")
        message_count = cursor.fetchone()[0]
        print(f"Total support messages: {message_count}")
        
        # Show sample tickets
        if ticket_count > 0:
            print("\nSample tickets:")
            cursor.execute("SELECT id, user_id, subject, status FROM support_ticket LIMIT 5")
            tickets = cursor.fetchall()
            for ticket in tickets:
                print(f"  Ticket ID: {ticket[0]}, User: {ticket[1]}, Subject: {ticket[2]}, Status: {ticket[3]}")
        
        # Show sample messages
        if message_count > 0:
            print("\nSample messages:")
            cursor.execute("SELECT id, ticket_id, sender_id, content, is_admin FROM support_message LIMIT 5")
            messages = cursor.fetchall()
            for msg in messages:
                print(f"  Message ID: {msg[0]}, Ticket: {msg[1]}, Sender: {msg[2]}, Content: {msg[3][:50]}..., Is Admin: {bool(msg[4])}")
        
        conn.close()
        
        print("\nTest data check completed successfully!")
        
    except Exception as e:
        print(f"Error checking test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_test_data()