"""Database migration for Windows environment"""
import os
import sys
from config import DATABASE_URL
import psycopg2
from urllib.parse import urlparse

def run_migration_windows():
    """Execute database migration using psycopg2 on Windows"""
    
    # Parse the database URL to extract components
    parsed_url = urlparse(DATABASE_URL)
    
    # Extract components
    username = parsed_url.username
    password = parsed_url.password
    hostname = parsed_url.hostname
    port = parsed_url.port or 5432
    database = parsed_url.path[1:]  # Remove leading slash
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        cur = conn.cursor()
        
        # SQL commands to add missing columns and create new tables
        sql_commands = [
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS about_me_video TEXT;",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS relationship_goals VARCHAR(200);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS lifestyle VARCHAR(200);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS diet VARCHAR(100);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS smoking VARCHAR(50);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS drinking VARCHAR(50);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS occupation VARCHAR(100);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS education VARCHAR(100);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS children VARCHAR(50);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS pets VARCHAR(50);",
            "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 0;",
            """CREATE TABLE IF NOT EXISTS user_swipe (
                id SERIAL PRIMARY KEY,
                swiper_id INTEGER NOT NULL,
                swipee_id INTEGER NOT NULL,
                action VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(swiper_id, swipee_id)
            );"""
        ]
        
        # Execute each SQL command
        for i, sql_cmd in enumerate(sql_commands, 1):
            print(f"Executing migration step {i}...")
            try:
                cur.execute(sql_cmd)
                conn.commit()
                print(f"[SUCCESS] Successfully executed step {i}")
            except Exception as e:
                print(f"[ERROR] Error executing step {i}: {e}")
                conn.rollback()  # Rollback in case of error
        
        cur.close()
        conn.close()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == '__main__':
    run_migration_windows()