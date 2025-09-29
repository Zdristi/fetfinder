#!/usr/bin/env python3
"""
Create test data for support chat system
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, UserModel, SupportTicket, SupportMessage

def create_test_data():
    """Create test data for support chat system"""
    with app.app_context():
        try:
            # Check if we have any users
            user_count = UserModel.query.count()
            print(f"Total users in database: {user_count}")
            
            if user_count == 0:
                print("No users found. Creating test user...")
                user = UserModel(
                    username='testuser',
                    email='test@example.com'
                )
                user.set_password('testpass123')
                db.session.add(user)
                db.session.commit()
                print(f"Created test user with ID: {user.id}")
            else:
                # Get first user
                user = UserModel.query.first()
                print(f"Using existing user: {user.username} (ID: {user.id})")
            
            # Create a test support ticket
            print("Creating test support ticket...")
            ticket = SupportTicket(
                user_id=user.id,
                subject='Test Support Request',
                status='open'
            )
            db.session.add(ticket)
            db.session.commit()
            print(f"Created test ticket with ID: {ticket.id}")
            
            # Create a test message from user
            print("Creating test message from user...")
            user_message = SupportMessage(
                ticket_id=ticket.id,
                sender_id=user.id,
                content='Hello, I need help with my profile.',
                is_admin=False
            )
            db.session.add(user_message)
            
            # Update ticket timestamp
            ticket.updated_at = user_message.timestamp
            
            db.session.commit()
            print(f"Created test user message with ID: {user_message.id}")
            
            # Create a test message from admin (simulate admin response)
            print("Creating test message from admin...")
            admin_message = SupportMessage(
                ticket_id=ticket.id,
                sender_id=user.id,  # For simplicity, using same user as sender
                content='Hello! I\'m here to help you with your profile. What seems to be the problem?',
                is_admin=True
            )
            db.session.add(admin_message)
            
            # Update ticket status and timestamp
            ticket.status = 'replied'
            ticket.updated_at = admin_message.timestamp
            
            db.session.commit()
            print(f"Created test admin message with ID: {admin_message.id}")
            
            print("Test data created successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_test_data()