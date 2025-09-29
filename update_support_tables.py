#!/usr/bin/env python3
"""
Update support ticket tables with proper relationships
"""

import sqlite3
import os

def update_support_tables():
    """Update support ticket tables with proper relationships"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return
    
    print(f"Updating support ticket tables in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('support_ticket', 'support_message')")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if 'support_ticket' not in existing_tables:
            print("Creating support_ticket table...")
            cursor.execute('''
                CREATE TABLE support_ticket (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')
        else:
            print("support_ticket table already exists")
        
        if 'support_message' not in existing_tables:
            print("Creating support_message table...")
            cursor.execute('''
                CREATE TABLE support_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    sender_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    FOREIGN KEY (ticket_id) REFERENCES support_ticket (id),
                    FOREIGN KEY (sender_id) REFERENCES user (id)
                )
            ''')
        else:
            print("support_message table already exists")
        
        # Add indexes for better performance
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_ticket_user ON support_ticket (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_ticket_status ON support_ticket (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_message_ticket ON support_message (ticket_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_message_sender ON support_message (sender_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_message_timestamp ON support_message (timestamp)')
            print("Indexes created successfully")
        except Exception as e:
            print(f"Warning: Error creating indexes: {e}")
        
        conn.commit()
        conn.close()
        
        print("Support ticket tables updated successfully!")
        
    except Exception as e:
        print(f"Error updating support ticket tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    update_support_tables()