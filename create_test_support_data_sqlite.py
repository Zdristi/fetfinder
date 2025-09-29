#!/usr/bin/env python3
"""
Create test data for support chat system using SQLite directly
"""

import sqlite3
import os
from datetime import datetime

def create_test_data():
    """Create test data for support chat system"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    print(f"Creating test data in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if we have any users
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"Total users in database: {user_count}")
        
        user_id = None
        if user_count == 0:
            print("No users found. Creating test user...")
            cursor.execute("""
                INSERT INTO user (username, email, password_hash) 
                VALUES (?, ?, ?)
            """, ('testuser', 'test@example.com', 'hashed_password_here'))
            user_id = cursor.lastrowid
            print(f"Created test user with ID: {user_id}")
        else:
            # Get first user
            cursor.execute("SELECT id FROM user ORDER BY id LIMIT 1")
            user_id = cursor.fetchone()[0]
            print(f"Using existing user with ID: {user_id}")
        
        # Create a test support ticket
        print("Creating test support ticket...")
        cursor.execute("""
            INSERT INTO support_ticket (user_id, subject, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, 'Test Support Request', 'open', datetime.utcnow(), datetime.utcnow()))
        ticket_id = cursor.lastrowid
        print(f"Created test ticket with ID: {ticket_id}")
        
        # Create a test message from user
        print("Creating test message from user...")
        cursor.execute("""
            INSERT INTO support_message (ticket_id, sender_id, content, is_admin, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (ticket_id, user_id, 'Hello, I need help with my profile.', 0, datetime.utcnow()))
        user_message_id = cursor.lastrowid
        print(f"Created test user message with ID: {user_message_id}")
        
        # Update ticket timestamp
        cursor.execute("""
            UPDATE support_ticket SET updated_at = ? WHERE id = ?
        """, (datetime.utcnow(), ticket_id))
        
        # Create a test message from admin (simulate admin response)
        print("Creating test message from admin...")
        cursor.execute("""
            INSERT INTO support_message (ticket_id, sender_id, content, is_admin, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (ticket_id, user_id, 'Hello! I\'m here to help you with your profile. What seems to be the problem?', 1, datetime.utcnow()))
        admin_message_id = cursor.lastrowid
        print(f"Created test admin message with ID: {admin_message_id}")
        
        # Update ticket status and timestamp
        cursor.execute("""
            UPDATE support_ticket SET status = ?, updated_at = ? WHERE id = ?
        """, ('replied', datetime.utcnow(), ticket_id))
        
        conn.commit()
        conn.close()
        
        print("Test data created successfully!")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_data()