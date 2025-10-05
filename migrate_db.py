"""Database migration script to add missing columns to existing user table"""
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def check_and_add_columns():
    """Add missing columns to user table if they don't exist"""
    with app.app_context():
        # Get the database engine
        engine = db.engine
        
        print("Checking and adding missing columns to user table...")
        
        # List of columns that need to be added
        columns_to_add = [
            ("about_me_video", "TEXT"),
            ("relationship_goals", "VARCHAR(200)"),
            ("lifestyle", "VARCHAR(200)"),
            ("diet", "VARCHAR(100)"),
            ("smoking", "VARCHAR(50)"),
            ("drinking", "VARCHAR(50)"),
            ("occupation", "VARCHAR(100)"),
            ("education", "VARCHAR(100)"),
            ("children", "VARCHAR(50)"),
            ("pets", "VARCHAR(50)"),
            ("coins", "INTEGER DEFAULT 0"),
            ("match_by_city", "BOOLEAN DEFAULT FALSE"),
            ("match_by_country", "BOOLEAN DEFAULT FALSE")
        ]
        
        for column_name, column_type in columns_to_add:
            # Check if column exists
            exists_query = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = :column_name
            """)
            
            result = db.session.execute(exists_query, {"column_name": column_name})
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                print(f"Adding column {column_name} to user table...")
                try:
                    alter_query = text(f"ALTER TABLE \"user\" ADD COLUMN {column_name} {column_type};")
                    db.session.execute(alter_query)
                    db.session.commit()
                    print(f"✓ Successfully added column {column_name}")
                except Exception as e:
                    print(f"✗ Error adding column {column_name}: {e}")
                    db.session.rollback()
            else:
                print(f"✓ Column {column_name} already exists")
        
        print("\nDatabase migration completed!")
        return True

if __name__ == '__main__':
    check_and_add_columns()