#!/usr/bin/env python3
"""
Standalone script to create support ticket tables
"""

import sqlite3
import os

def create_support_tables():
    """Create support ticket tables in SQLite database"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    print(f"Creating support ticket tables in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create support_ticket table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_ticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # Create support_message table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_message (
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
        
        # Add indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_ticket_user ON support_ticket (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_ticket_status ON support_ticket (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_message_ticket ON support_message (ticket_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_message_sender ON support_message (sender_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_message_timestamp ON support_message (timestamp)')
        
        conn.commit()
        conn.close()
        
        print("Support ticket tables created successfully!")
        
    except Exception as e:
        print(f"Error creating support ticket tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_support_tables()