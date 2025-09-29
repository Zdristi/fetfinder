#!/usr/bin/env python3
"""
Migration script to add support ticket tables to the database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import SupportTicket, SupportMessage

def create_support_tables():
    """Create support ticket tables"""
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("Support ticket tables created successfully!")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'support_ticket' in tables and 'support_message' in tables:
                print("✓ Support ticket tables verified")
            else:
                print("✗ Some support ticket tables are missing")
                
        except Exception as e:
            print(f"Error creating support ticket tables: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_support_tables()