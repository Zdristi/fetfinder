import unittest
import tempfile
import os
from app import app, db
from models import User, Fetish, Interest, Match
from werkzeug.security import generate_password_hash


class BasicTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test variables and initialize app."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create a test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpassword')
            )
            db.session.add(test_user)
            db.session.commit()
            self.test_user_id = test_user.id

    def test_home_page(self):
        """Test the home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'FetDate', response.data)

    def test_registration_page(self):
        """Test the registration page loads."""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        """Test the login page loads."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_login_functionality(self):
        """Test user login functionality."""
        # Test successful login
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Test failed login
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on login page

    def test_profile_access(self):
        """Test profile access (should redirect if not logged in)."""
        response = self.client.get('/profile')
        # Should redirect to login since not authenticated
        self.assertEqual(response.status_code, 302)  # Redirect status code

    def test_user_model(self):
        """Test basic user model functionality."""
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')
            # Test password hashing
            self.assertTrue(user.check_password('testpassword'))
            self.assertFalse(user.check_password('wrongpassword'))

    def test_fetish_model(self):
        """Test fetish model functionality."""
        with self.app.app_context():
            user = User.query.get(self.test_user_id)
            fetish = Fetish(user_id=user.id, name='Test Fetish')
            db.session.add(fetish)
            db.session.commit()
            
            self.assertEqual(fetish.user_id, user.id)
            self.assertEqual(fetish.name, 'Test Fetish')

    def test_interest_model(self):
        """Test interest model functionality."""
        with self.app.app_context():
            user = User.query.get(self.test_user_id)
            interest = Interest(user_id=user.id, name='Test Interest')
            db.session.add(interest)
            db.session.commit()
            
            self.assertEqual(interest.user_id, user.id)
            self.assertEqual(interest.name, 'Test Interest')

    def tearDown(self):
        """Clean up after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == '__main__':
    unittest.main()