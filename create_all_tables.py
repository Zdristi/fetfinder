#!/usr/bin/env python3
"""
Create all database tables for the application
"""

import sqlite3
import os

def create_all_tables():
    """Create all database tables"""
    # Database file path
    db_path = 'instance/fetdate.db'
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    print(f"Creating all database tables in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create user table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                photo TEXT,
                country TEXT,
                city TEXT,
                bio TEXT,
                is_admin BOOLEAN DEFAULT 0,
                is_blocked BOOLEAN DEFAULT 0,
                about_me_video TEXT,
                relationship_goals TEXT,
                lifestyle TEXT,
                diet TEXT,
                smoking TEXT,
                drinking TEXT,
                occupation TEXT,
                education TEXT,
                children TEXT,
                pets TEXT,
                is_premium BOOLEAN DEFAULT 0,
                premium_expires TIMESTAMP,
                coins INTEGER DEFAULT 0,
                match_by_city BOOLEAN DEFAULT 0,
                match_by_country BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create fetish table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fetish (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # Create interest table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # Create match table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                matched_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, matched_user_id)
            )
        ''')
        
        # Create message table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES user (id),
                FOREIGN KEY (recipient_id) REFERENCES user (id)
            )
        ''')
        
        # Create notification table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # Create gift table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gift (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                icon TEXT,
                category TEXT
            )
        ''')
        
        # Create user_gift table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_gift (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                gift_id INTEGER NOT NULL,
                message TEXT,
                is_anonymous BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES user (id),
                FOREIGN KEY (recipient_id) REFERENCES user (id),
                FOREIGN KEY (gift_id) REFERENCES gift (id)
            )
        ''')
        
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
        
        # Create rating table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rating (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rater_id INTEGER NOT NULL,
                rated_user_id INTEGER NOT NULL,
                stars INTEGER NOT NULL CHECK(stars >= 1 AND stars <= 5),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rater_id, rated_user_id),
                FOREIGN KEY (rater_id) REFERENCES user (id),
                FOREIGN KEY (rated_user_id) REFERENCES user (id)
            )
        ''')
        
        # Add indexes for better performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_user_username ON user (username)',
            'CREATE INDEX IF NOT EXISTS idx_user_email ON user (email)',
            'CREATE INDEX IF NOT EXISTS idx_fetish_user ON fetish (user_id)',
            'CREATE INDEX IF NOT EXISTS idx_interest_user ON interest (user_id)',
            'CREATE INDEX IF NOT EXISTS idx_match_user ON match (user_id)',
            'CREATE INDEX IF NOT EXISTS idx_match_matched_user ON match (matched_user_id)',
            'CREATE INDEX IF NOT EXISTS idx_message_sender ON message (sender_id)',
            'CREATE INDEX IF NOT EXISTS idx_message_recipient ON message (recipient_id)',
            'CREATE INDEX IF NOT EXISTS idx_message_timestamp ON message (timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_notification_user ON notification (user_id)',
            'CREATE INDEX IF NOT EXISTS idx_notification_timestamp ON notification (timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_user_gift_sender ON user_gift (sender_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_gift_recipient ON user_gift (recipient_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_gift_timestamp ON user_gift (timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_support_ticket_user ON support_ticket (user_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_ticket_status ON support_ticket (status)',
            'CREATE INDEX IF NOT EXISTS idx_support_message_ticket ON support_message (ticket_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_message_sender ON support_message (sender_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_message_timestamp ON support_message (timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_rating_rater ON rating (rater_id)',
            'CREATE INDEX IF NOT EXISTS idx_rating_rated ON rating (rated_user_id)'
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        conn.commit()
        conn.close()
        
        print("All database tables created successfully!")
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_all_tables()