import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *

def create_tables():
    """Create all tables including the new UserSwipe table"""
    with app.app_context():
        print("Creating all tables including UserSwipe...")
        try:
            # This will create the UserSwipe table as well
            db.create_all()
            print("All tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
            # In case of SQLAlchemy issue, try raw SQL approach
            print("Attempting raw SQL approach...")
            from sqlalchemy import text
            try:
                # Check if table exists first
                result = db.session.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_swipe');")
                )
                table_exists = result.fetchone()[0]
                
                if not table_exists:
                    print("Creating user_swipe table with raw SQL...")
                    create_sql = """
                    CREATE TABLE user_swipe (
                        id SERIAL PRIMARY KEY,
                        swiper_id INTEGER NOT NULL,
                        swipee_id INTEGER NOT NULL,
                        action VARCHAR(10) NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(swiper_id, swipee_id)
                    );
                    """
                    db.session.execute(text(create_sql))
                    db.session.commit()
                    print("✓ user_swipe table created successfully")
                else:
                    print("user_swipe table already exists")
            except Exception as e2:
                print(f"Error with raw SQL approach: {e2}")

if __name__ == "__main__":
    create_tables()