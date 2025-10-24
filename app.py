import os
import sys
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения из файла .env
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message as EmailMessage
from flask_caching import Cache
import json
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
import hashlib
from models import db, User as UserModel, UserPhoto, Fetish, Interest, Match, Message, Notification, Rating, SupportTicket, SupportMessage
import hmac
import hashlib
import random
import string
import re
import requests

# Import configuration
from config import SECRET_KEY

# Import face detection functionality
try:
    from face_detection import validate_avatar_image
    FACE_DETECTION_AVAILABLE = True
except ImportError:
    FACE_DETECTION_AVAILABLE = False
    print("Warning: face_detection module not available. Avatar validation disabled.")

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Add reCAPTCHA configuration
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lc6BhgUAAAAAAH5u7f8rXz8rXz8rXz8rXz8rXz8'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lc6BhgUAAAAAAH5u7f8rXz8rXz8rXz8rXz8rXz8'

# Disable cache completely to save memory
app.config['CACHE_TYPE'] = 'null'
app.config['CACHE_DEFAULT_TIMEOUT'] = 0
cache = Cache(app)

# Configure SQLAlchemy - Force SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fetdate_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import SQLAlchemy engine options from config
from config import SQLALCHEMY_ENGINE_OPTIONS
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS

# Initialize database
db.init_app(app)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'sup.fetdate@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Пароль приложения Gmail
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'sup.fetdate@gmail.com')

# Function to ensure database connection before requests that need it
@app.before_request
def before_request():
    # For requests that might use the database, ensure connection is alive
    # Only for routes that we know will access the database
    if request.endpoint and not request.endpoint.startswith('static'):
        # Test connection - this will handle reconnection if needed
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            print(f"Database connection error in before_request: {e}")
            try:
                # For SQLite, dispose connection as needed
                db.engine.dispose()
            except Exception as dispose_error:
                print(f"Error disposing database connection in before_request: {dispose_error}")

# Инициализация Flask-Mail
mail = Mail(app)

# Create templates and static directories if they don't exist
if not os.path.exists('templates'):
    os.makedirs('templates')
if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('static/css'):
    os.makedirs('static/css')
if not os.path.exists('static/js'):
    os.makedirs('static/js')
if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

from datetime import timedelta

# Configure session permanent
app.permanent_session_lifetime = timedelta(days=30)  # Сессия будет действовать 30 дней

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = "strong"

# Site configuration
SITE_NAME = 'FetDate'

# Configuration
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Data storage
DATA_FILE = 'users.json'
MATCHES_FILE = 'matches.json'

# Temporary storage for confirmation codes (in production, use Redis or database)
confirmation_codes = {}

def cleanup_expired_confirmation_codes():
    """Удаляет истекшие коды подтверждения из памяти"""
    current_time = datetime.utcnow()
    expired_emails = []
    
    for email, data in confirmation_codes.items():
        if data['expires'] < current_time:
            expired_emails.append(email)
    
    for email in expired_emails:
        del confirmation_codes[email]
    
    return len(expired_emails)

def generate_confirmation_code():
    """Генерирует 6-значный код подтверждения"""
    return ''.join(random.choices(string.digits, k=6))

def send_confirmation_email(email, code):
    """Отправляет код подтверждения на email (асинхронно, без блокировки)"""
    try:
        # Создание сообщения
        msg = EmailMessage()
        msg.subject = 'Код подтверждения регистрации'
        msg.recipients = [email]
        
        # Текст письма
        msg.body = f"""
        Здравствуйте!
        
        Спасибо за регистрацию на нашем сайте FetDate.
        
        Ваш код подтверждения: {code}
        
        Пожалуйста, введите этот код на странице подтверждения, чтобы завершить регистрацию.
        
        Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.
        
        С уважением,
        Команда FetDate
        """
        
        # Отправка письма в отдельном потоке, чтобы не блокировать основной процесс
        import threading
        
        def send_email_async():
            try:
                mail.send(msg)
                print(f"Код подтверждения отправлен на {email}: {code}")
            except Exception as e:
                print(f"Ошибка при асинхронной отправке email на {email}: {str(e)}")
        
        # Запускаем отправку email в отдельном потоке
        email_thread = threading.Thread(target=send_email_async)
        email_thread.daemon = True
        email_thread.start()
        
        # Возвращаем True сразу, не дожидаясь отправки
        return True
    except Exception as e:
        # В случае критической ошибки логируем её
        print(f"Критическая ошибка при подготовке email для {email}: {str(e)}")
        return False

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        # Try to load user with all fields (including new ones)
        user = UserModel.query.get(int(user_id))
        if user:
            return user
        return None
    except Exception as e:
        # If there's an error (like missing columns), try to load a basic user
        # This handles the case where the database hasn't been migrated yet
        try:
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT id, username, email, password_hash, is_admin, is_blocked FROM \"user\" WHERE id = :id"),
                {"id": int(user_id)}
            )
            row = result.fetchone()
            if row:
                # Create a minimal user object that supports only basic functionality
                class BasicUser:
                    def __init__(self, id, username, email, password_hash, is_admin, is_blocked):
                        self.id = id
                        self.username = username
                        self.email = email
                        self.password_hash = password_hash
                        self.is_admin = is_admin
                        self.is_blocked = is_blocked
                    
                    def is_authenticated(self):
                        return True
                    
                    def is_active(self):
                        return not self.is_blocked
                    
                    def is_anonymous(self):
                        return False
                    
                    def get_id(self):
                        return str(self.id)
                
                user = BasicUser(
                    id=row[0], 
                    username=row[1], 
                    email=row[2], 
                    password_hash=row[3],
                    is_admin=row[4],
                    is_blocked=row[5]
                )
                return user
        except Exception:
            pass
        
        return None

# Block check before each request
@app.before_request
def check_blocked_user():
    if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and current_user.is_blocked:
        if request.endpoint not in ['blocked', 'logout']:
            return redirect(url_for('blocked'))

# Language dictionaries
LANGUAGES = {
    'en': {
        'welcome': 'Welcome to FetDate!',
        'find_match': 'Find your perfect match',
        'description': 'FetDate is a modern dating platform where you can find matches based on shared interests and fetishes.',
        'create_profile': 'Create Profile',
        'complete_profile': 'Complete Profile',
        'discover': 'Discover Matches',
        'connect': 'Connect',
        'signup': 'Sign Up',
        'login': 'Login',
        'logout': 'Logout',
        'swipe_feature': 'Swipe through potential matches',
        'chat': 'Chat',
        'my_chats': 'My Chats',
        'no_active_chats': 'You don\'t have any active chats yet.',
        'start_chatting': 'Start chatting by going to the',
        'swipe_page': 'swipe page',
        'and_connect': 'and connecting with other users!',
        'get_started': 'Get Started',
        'how_works': 'How It Works',
        'step1': 'Sign Up',
        'step1_desc': 'Create your profile and tell us about your interests and preferences.',
        'step2': 'Swipe',
        'step2_desc': 'Discover and swipe through potential matches in our modern interface.',
        'step3': 'Connect',
        'step3_desc': 'When you both like each other, start chatting and see where it leads!',
        'username': 'Username',
        'email': 'Email',
        'password': 'Password',
        'bio': 'Bio',
        'location': 'Location',
        'country': 'Country',
        'city': 'City',
        'select_country': 'Select Country',
        'select_city': 'Select City',
        'photo': 'Profile Photo',
        'fetishes': 'Fetishes (Sexual Preferences)',
        'interests': 'Interests & Hobbies',
        'add_fetish': 'Add your own fetish',
        'add_interest': 'Add your own interest',
        'submit': 'Create Profile',
        'update_profile': 'Update Profile',
        'view_profile': 'View Profile',
        'all_users': 'All Users',
        'swipe_now': 'Start Swiping',
        'no_users': 'No users registered yet',
        'be_first': 'Be the first to join our community!',
        'member_since': 'Member since',
        'about': 'About',
        'about_us': 'About Us',
        'our_story': 'Our Story',
        'our_story_content': 'Founded with the vision of creating meaningful connections, FetDate is dedicated to providing a unique and inclusive dating experience. Our platform brings together individuals who share similar interests, values, and lifestyles, fostering genuine relationships in a comfortable environment.',
        'our_mission': 'Our mission is to create a safe space where individuals can express themselves authentically and find compatible partners without judgment. We believe that everyone deserves to find love and companionship that aligns with their unique preferences.',
        'our_community': 'Our Growing Community',
        'information': 'Information',
        'no_bio': 'No bio provided',
        'no_fetishes': 'No fetishes listed',
        'no_interests': 'No interests listed',
        'discover_matches': 'Discover Matches',
        'no_more_users': 'No more users to show',
        'check_later': 'Check back later for new matches!',
        'reject': 'Reject',
        'superlike': 'Super Like',
        'like': 'Like',
        'home': 'Home',
        'profile': 'Profile',
        'chat': 'Chat',
        'language': 'Language',
        'english': 'English',
        'russian': 'Русский',
        'login_with_google': 'Login with Google',
        'welcome_back': 'Welcome back',
        'profile_completed': 'Your profile is complete!',
        'please_complete_profile': 'Please complete your profile',
        'invalid_credentials': 'Invalid username or password',
        'username_exists': 'Username already exists',
        'email_exists': 'A user with this email already exists. Please use a different email address.',
        'registration_success': 'Registration successful! Please log in.',
        'already_have_account': 'Already have an account?',
        'no_account': 'Don\'t have an account?',
        'required_field': 'This field is required',
        'quick_actions': 'Quick Actions',
        'edit_profile': 'Edit Profile',
        'notifications': 'Notifications',
        'mark_all_read': 'Mark all read',
        'no_notifications': 'No notifications yet',
        'rate_this_user': 'Rate This User',
        'your_rating': 'Your Rating:',
        'submit_rating': 'Submit Rating',
        'premium_membership': 'Premium Membership',
        'upgrade_to_premium': 'Upgrade to Premium',
        'back_to_profile': 'Back to Profile',
        'premium': 'Premium',
        'unlock_exclusive_features': 'Unlock exclusive features and enhance your experience',
        'premium_features': 'Premium Features',
        'undo_swipes': 'Undo Swipes',
        'undo_swipes_desc': 'Change your mind and undo unlimited swipes per day',
        'unlimited_messaging': 'Unlimited Messaging',
        'unlimited_messaging_desc': 'Send unlimited messages to your matches',
        'premium_badge': 'Premium Badge',
        'premium_badge_desc': 'Stand out with a premium badge on your profile',
        'subscription_details': 'Subscription Details',
        'currency': 'Currency',
        'billing_cycle': 'Billing Cycle',
        'billing_cycle_desc': 'Monthly (Automatically renews)',
        'payment_methods': 'Payment Methods',
        'payment_methods_desc': 'Credit/Debit Cards, PayPal',
        'refund_policy_info': 'Refund Policy',
        'refund_policy_desc': '7-day money-back guarantee for new subscriptions',
        'how_it_works': 'How It Works',
        'secure_payment': 'Secure Payment',
        'secure_payment_desc': 'All payment information is processed through secure, encrypted channels. We never store your full credit card details on our servers. Our payment processor is PCI DSS compliant to ensure your financial information is protected.',
        'by_subscribing_premium': 'By subscribing to premium service, you agree to our Terms of Use and Refund Policy.',
        'why_users_love_premium': 'Why Users Love Premium',
        'priority_matching': 'Priority matching',
        'advanced_filters': 'Advanced filters',
        'extended_profile_visibility': 'Extended profile visibility',
        'click_get_premium_now': 'Click "Get Premium Now" to proceed with payment',
        'enter_payment_info': 'Enter your payment information securely',
        'subscription_activated': 'Your subscription will be activated immediately',
        'enjoy_premium_features': 'Enjoy premium features without interruption',
        'subscription_renews': 'Subscription renews automatically each month',
        'cancel_anytime_account': 'Cancel anytime through your account settings',
        'testimonial_1': '"Premium features helped me connect with more people who share my interests. The unlimited messaging is a game-changer!"',
        'testimonial_2': '"The ability to undo swipes has saved me from accidentally passing on potential matches. Worth every penny!"',
        'testimonial_3': '"The premium badge makes me stand out in the crowd. I\'ve received significantly more matches since upgrading."',
        'set_primary_photo': 'Set as Primary',
        'primary': 'Primary',
        'just_per_month': 'Just $9.99/month',
        'cancel_anytime': 'Cancel anytime',
        'already_premium_member': 'You\'re already a premium member!',
        'expires': 'Expires',
        'cancel_subscription': 'Cancel Subscription',
        'subscription_expired': 'Your premium subscription has expired.',
        'get_premium_now': 'Get Premium Now',
        'by_subscribing': 'By subscribing, you agree to our terms of service and privacy policy.',
        'ready_to_find_love': 'Ready to Find Love?',
        'discover_new_connections': 'Discover new connections and find your perfect match today.',
        'why_choose_us': 'Why Choose Us?',
        'safe_and_secure': 'Safe & Secure',
        'privacy_protection': 'Your privacy is our top priority with advanced security measures.',
        'verified_profiles': 'Verified Profiles',
        'authentic_people': 'Meet authentic people with verified profiles and photos.',
        'instant_matching': 'Instant Matching',
        'real_time_connect': 'Connect with compatible matches in real-time.',
        'join_our_community': 'Join Our Community Today!',
        'find_your_perfect_match': 'Find your perfect match and connect with like-minded individuals who share your interests and passions.',
        'join_thousands': 'Join Thousands of Happy Members!',
        'active_users': 'Active Users',
        'successful_matches': 'Successful Matches',
        'satisfaction_rate': 'Satisfaction Rate',
        'choose_file': 'Choose File',
        'no_file_chosen': 'No file chosen',
        'choose_files': 'Choose Files',
        'no_files_chosen': 'No files chosen',
        'current_photos': 'Current Photos',
        'set_primary_photo': 'Set as Primary',
        'confirm_delete_photo': 'Are you sure you want to delete this photo?',
        'photo_deleted': 'Photo deleted successfully',
        'error_deleting_photo': 'Error deleting photo',
        'primary_photo_set': 'Primary photo set successfully',
        'error_setting_primary_photo': 'Error setting primary photo',
        'delete': 'Delete',
        'faq': 'FAQ',
        'support': 'Support',
        'contacts': 'Contacts',
        'agreement_to_terms': 'Agreement to Terms',
        'agreement_to_terms_desc': 'By accessing and using FetDate (\"the Service\"), you agree to be bound by these Terms of Use (\"Terms\"). If you disagree with any part of the terms, you may not access the Service.',
        'description_of_service': 'Description of Service',
        'description_of_service_desc': 'FetDate is a dating platform that allows users to connect with others based on shared interests and fetishes. The Service provides features such as profile creation, matching, swiping, and messaging to facilitate connections.',
        'user_accounts': 'User Accounts',
        'user_accounts_desc1': 'When you create an account with us, you must provide accurate and complete information. You are responsible for maintaining the security of your account and are fully responsible for all activities that occur under your account.',
        'user_accounts_desc2': 'You must notify us immediately upon becoming aware of any unauthorized use of your account or any other breach of security.',
        'subscription_and_payment': 'Subscription and Payment',
        'subscription_and_payment_desc1': 'Our Service offers premium subscriptions. Premium subscriptions are automatically renewed until cancelled. You may cancel your subscription at any time by contacting us.',
        'subscription_and_payment_desc2': 'All fees are inclusive of applicable taxes where required by law. We may change our subscription fees at any time, with reasonable notice to you.',
        'purchases': 'Purchases',
        'purchases_desc1': 'If you make purchases through the Service, you agree to provide current, complete, and accurate purchase and account information. You further agree to pay all fees as described when making a purchase.',
        'purchases_desc2': 'We reserve the right to refuse any order you place through the Service.',
        'accuracy_of_information': 'Accuracy of Information',
        'accuracy_of_information_desc': 'While we strive to provide accurate information about our Service, we make no representations about the completeness, accuracy, reliability, or suitability of any information, products, or services contained on our Service.',
        'intellectual_property': 'Intellectual Property',
        'intellectual_property_desc': 'The Service and its original content, features, and functionality are owned by FetDate and are protected by international copyright, trademark, and other intellectual property laws.',
        'termination': 'Termination',
        'termination_desc1': 'We may terminate or suspend your account immediately, without prior notice, for any reason whatsoever, including without limitation if you breach the Terms.',
        'termination_desc2': 'Upon termination, your right to use the Service will cease immediately.',
        'limitation_of_liability': 'Limitation of Liability',
        'limitation_of_liability_desc': 'In no event shall FetDate, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses.',
        'governing_law': 'Governing Law',
        'governing_law_desc': 'These Terms shall be governed and construed in accordance with the laws, without regard to its conflict of law provisions.',
        'changes_to_terms': 'Changes to Terms',
        'changes_to_terms_desc': 'We reserve the right, at our sole discretion, to modify or replace these Terms at any time. By continuing to access or use our Service after those revisions become effective, you agree to be bound by the revised terms.',
        'contact_us': 'Contact Us',
        'contact_us_desc': 'If you have any questions about these Terms, please contact us at',
        'privacy_policy': 'Privacy Policy',
        'information_we_collect': 'Information We Collect',
        'information_we_collect_desc': 'At FetDate, we collect information you provide directly to us, such as when you create an account, update your profile, or communicate with other users. This includes:',
        'personal_information_item': 'Personal information (name, email address, phone number)',
        'profile_information_item': 'Profile information (photos, bio, interests, fetishes)',
        'location_data_item': 'Location data (country and city)',
        'payment_information_item': 'Payment information when purchasing premium features',
        'communication_preferences_item': 'Communication preferences',
        'how_we_use_your_information': 'How We Use Your Information',
        'how_we_use_your_information_desc': 'We use the information we collect to:',
        'provide_maintain_improve_item': 'Provide, maintain, and improve our services',
        'process_transactions_item': 'Process transactions and send related information',
        'send_technical_notices_item': 'Send technical notices and support messages',
        'link_combine_information_item': 'Link or combine user information with other sources',
        'protect_investigate_item': 'Protect, investigate, and deter against fraudulent, unauthorized, or illegal activity',
        'information_sharing_disclosure': 'Information Sharing and Disclosure',
        'information_sharing_disclosure_desc': 'We do not share, sell, or rent your personal information to third parties for marketing purposes. We may share information with:',
        'service_providers_item': 'Service providers who perform services on our behalf',
        'other_users_item': 'Other users as per your profile settings and preferences',
        'third_parties_item': 'Third parties in connection with a merger, acquisition, or sale of assets',
        'legal_authorities_item': 'Legal authorities when required by law',
        'data_security': 'Data Security',
        'data_security_desc': 'We implement appropriate technical and organizational measures to protect the security of your personal information. However, no method of transmission over the internet or method of electronic storage is 100% secure.',
        'your_data_protection_rights': 'Your Data Protection Rights',
        'your_data_protection_rights_desc': 'Depending on your location, you may have the right to:',
        'access_your_data_item': 'Access your personal data',
        'rectify_data_item': 'Rectify inaccurate data',
        'request_deletion_item': 'Request deletion of your data',
        'object_to_processing_item': 'Object to processing',
        'data_portability_item': 'Data portability',
        'withdraw_consent_item': 'Withdraw consent',
        'childrens_privacy': 'Children\'s Privacy',
        'childrens_privacy_desc': 'Our service does not address anyone under the age of 18. We do not knowingly collect personal information from children under 18.',
        'changes_to_privacy_policy': 'Changes to This Privacy Policy',
        'changes_to_privacy_policy_desc': 'We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page.',
        'contact_us_privacy': 'Contact Us (Privacy)',
        'contact_us_privacy_desc': 'If you have any questions about this Privacy Policy, please contact us at',
        'refund_policy': 'Refund Policy',
        'premium_subscription_refunds': 'Premium Subscription Refunds',
        'premium_subscription_refunds_desc': 'We offer a 7-day refund policy for our premium subscriptions. If you are not satisfied with our premium service, you may request a refund within 7 days of your initial purchase.',
        'eligibility_for_refund': 'Eligibility for Refund',
        'eligibility_for_refund_desc': 'To be eligible for a refund, your premium subscription must:',
        'purchased_within_7_days_item': 'Have been purchased within the last 7 days',
        'not_extensively_used_item': 'Not have been used extensively (limited messaging, limited use of premium features)',
        'before_renewal_date_item': 'Be requested before any renewal date',
        'non_refundable_items': 'Non-Refundable Items',
        'non_refundable_items_desc': 'The following items are non-refundable:',
        'individual_coins_item': 'Individual coins purchased for gifts or features',
        'gifts_sent_item': 'Gifts sent to other users',
        'subscriptions_7_days_item': 'Subscriptions that have been active for more than 7 days',
        'heavily_used_subscriptions_item': 'Subscriptions that have been heavily used',
        'how_to_request_refund': 'How to Request a Refund',
        'how_to_request_refund_desc': 'To request a refund, please contact us at with the following information:',
        'username_item': 'Your username',
        'date_of_purchase_item': 'Date of purchase',
        'reason_for_refund_item': 'Reason for requesting a refund',
        'transaction_id_item': 'Transaction ID (if available)',
        'processing_time': 'Processing Time',
        'processing_time_desc': 'Once your refund request is received and reviewed, we will send you an email confirming acceptance or rejection of your refund request. If accepted, your refund will be processed and a credit will automatically be applied to your original payment method within 5-10 business days.',
        'subscription_renewals': 'Subscription Renewals',
        'subscription_renewals_desc': 'If your subscription renews automatically before a refund is processed, we will refund the most recent billing cycle if you are still within the 7-day window and meet the eligibility requirements.',
        'special_circumstances': 'Special Circumstances',
        'special_circumstances_desc': 'In certain exceptional circumstances, we may consider refund requests beyond the 7-day window, including:',
        'technical_issues_item': 'Technical issues preventing service use',
        'billing_errors_item': 'Billing errors on our part',
        'account_suspension_item': 'Account suspension or termination not due to user misconduct',
        'chargebacks_and_disputes': 'Chargebacks and Disputes',
        'chargebacks_and_disputes_desc': 'Filing a chargeback or payment dispute with your financial institution voids your right to any refund from us. Please contact us first if you have concerns about your purchase.',
        'changes_to_refund_policy': 'Changes to Refund Policy',
        'changes_to_refund_policy_desc': 'We reserve the right to modify this refund policy at any time. Changes will be effective immediately upon posting to our website. Your continued use of our service after changes constitutes acceptance of the modified policy.',
        'contact_us_refund': 'Contact Us (Refund)',
        'contact_us_refund_desc': 'If you have any questions or concerns about our refund policy, please contact us at',
        'terms_of_service': 'Terms of Service',
        'service_description': 'Service Description',
        'service_description_desc': 'FetDate is a digital dating platform that provides users with the ability to create profiles, connect with others based on shared interests and fetishes, and communicate through various features. Our service operates as a software platform accessible via web browser.',
        'account_registration_process': 'Account Registration Process',
        'account_registration_process_desc': 'To use our services, users must create an account by providing accurate and complete information including but not limited to username, email address, and password. Users must be at least 18 years old to register. Accounts must be maintained with accurate and current information.',
        'payment_and_billing': 'Payment and Billing',
        'payment_and_billing_desc': 'Our platform offers both free and premium services:',
        'free_services_item': 'Free services include basic profile creation, limited swiping, and basic matching',
        'premium_services_item': 'Premium services include features such as unlimited messaging, advanced matching, and special badges',
        'premium_cost_item': 'Premium subscriptions are charged monthly at $9.99 USD',
        'payment_processing_item': 'Payment is processed securely through our payment processor',
        'automatic_renewal_item': 'Subscriptions automatically renew until cancelled by the user',
        'digital_content_delivery': 'Digital Content Delivery',
        'digital_content_delivery_desc': 'All digital products and services are provided immediately upon purchase:',
        'premium_access_item': 'Premium subscription access is granted instantly upon successful payment',
        'in_app_currency_item': 'In-app currency (coins) are added to your account immediately',
        'enhanced_features_item': 'Enhanced features become available immediately after purchase',
        'user_responsibilities': 'User Responsibilities',
        'user_responsibilities_desc': 'Users are responsible for:',
        'confidentiality_item': 'Maintaining the confidentiality of their account information',
        'accurate_information_item': 'Providing accurate and up-to-date profile information',
        'respectful_behavior_item': 'Acting respectfully toward other users',
        'compliance_item': 'Complying with all applicable laws and regulations',
        'service_availability': 'Service Availability',
        'service_availability_desc': 'We strive to maintain our service availability 24/7. However, service may be temporarily unavailable during scheduled maintenance or in case of technical issues. We are not liable for any inconvenience caused by temporary service interruptions.',
        'data_protection': 'Data Protection',
        'data_protection_desc': 'All user data is encrypted and stored securely. We implement industry-standard security measures to protect user information. Personal information is processed in accordance with our Privacy Policy.',
        'cancellation_and_account_termination': 'Cancellation and Account Termination',
        'cancellation_and_account_termination_desc': 'Users may cancel their subscriptions at any time. For premium memberships, cancellation will be effective at the end of the current billing period. Users may close their accounts entirely by contacting support. Account closure results in immediate deactivation of the profile and removal from matching systems.',
        'customer_support': 'Customer Support',
        'customer_support_desc': 'Customer support is available through our in-app support system and email at',
        'customer_support_desc_continued': 'We aim to respond to all inquiries within 24 hours. Support is available for account issues, billing questions, and technical problems.',
        'limitation_of_liability': 'Limitation of Liability',
        'limitation_of_liability_desc': 'Our liability is limited to the amount paid by the user for services in the 12 months prior to the event giving rise to the claim. We are not liable for indirect, incidental, or consequential damages.',
        'dispute_resolution': 'Dispute Resolution',
        'dispute_resolution_desc': 'Any disputes related to our services should first be addressed through our customer support channel. If unresolved, disputes may be subject to binding arbitration as specified in our Terms of Use.',
        'governing_law': 'Governing Law',
        'governing_law_desc': 'These Terms of Service are governed by international law with respect to the delivery of digital services. Any legal action related to these terms must be brought in the jurisdiction where our company is registered.',
        'modifications_to_service': 'Modifications to Service',
        'modifications_to_service_desc': 'We reserve the right to modify our services, features, and these Terms of Service at any time. Users will be notified of significant changes via email or in-app notice. Continued use of the service constitutes acceptance of modified terms.',
        'contact_information': 'Contact Information',
        'contact_information_desc': 'For questions regarding these Terms of Service, please contact us at',
        'contact_us_title': 'Contact Us',
        'get_in_touch': 'Get in Touch',
        'get_in_touch_desc': 'We\'re here to help! If you have any questions, concerns, or feedback about our service, please don\'t hesitate to reach out to us.',
        'support_email': 'Support Email',
        'support_team_response_desc': 'Our support team typically responds within 24 hours. Please include your username in your message for faster assistance.',
        'mailing_address': 'Mailing Address',
        'legal_matters_desc': 'For legal matters and formal correspondence:',
        'fetdate_support_team': 'FetDate Support Team',
        'attention_legal_dept': 'Attn: Legal Department',
        'physical_address': '[Physical Address for Legal Disputes]',
        'city_state_zip': '[City, State, ZIP Code]',
        'phone_support': 'Phone Support',
        'immediate_assistance_desc': 'For immediate assistance, you can reach us at:',
        'urgent_account_issues': '(For urgent account issues)',
        'phone_hours': 'Phone support is available Monday-Friday, 9:00 AM - 6:00 PM EST',
        'report_an_issue': 'Report an Issue',
        'report_an_issue_desc': 'If you need to report a user, content, or technical issue:',
        'report_user_button': 'Use the \"Report User\" button on any profile',
        'moderation_team_email': 'Contact our moderation team at',
        'in_app_support_chat': 'Use the in-app support chat feature',
        'business_inquiries': 'Business Inquiries',
        'business_inquiries_desc': 'For business partnerships, press inquiries, or advertising opportunities:',
        'business_email': 'business@fetdate.online',
        'feedback_and_suggestions': 'Feedback and Suggestions',
        'feedback_and_suggestions_desc': 'We value your feedback and suggestions for improving our service. Please send your ideas to:',
        'feedback_email': 'feedback@fetdate.online',
        'frequently_asked_questions': 'Frequently Asked Questions',
        'back_to_home': 'Back to Home',
        'how_do_i_create_an_account': 'How do I create an account?',
        'how_do_i_create_an_account_answer': 'To create an account, click the "Sign Up" button on the homepage. Fill in your username, email, and password, then follow the instructions to complete your profile.',
        'how_do_i_find_matches': 'How do I find matches?',
        'how_do_i_find_matches_answer': 'After completing your profile, go to the "Discover" section to start swiping through potential matches. You can like or reject profiles based on your preferences.',
        'is_my_information_secure': 'Is my information secure?',
        'is_my_information_secure_answer': 'We take your privacy seriously. All personal information is encrypted and stored securely. We never share your data with third parties without your consent.',
        'what_are_premium_features': 'What are Premium features?',
        'what_are_premium_features_answer': 'Premium members enjoy unlimited swipes, the ability to undo unlimited swipes per day, unlimited messaging, and a premium badge on their profile. Premium also gives priority placement in discovery queues.',
        'how_do_i_contact_support': 'How do I contact support?',
        'how_do_i_contact_support_answer': 'You can contact our support team through the "Contact Support" link in your profile menu, or by emailing support@fetdate.online. Our team typically responds within 24 hours.',
        'still_have_questions': 'Still have questions?',
        'contact_our_support_team': 'Contact our support team for personalized assistance.',
        'contact_support': 'Contact Support',
        'support_chat': 'Support Chat',
        'back_to_profile': 'Back to Profile',
        'location_matching_settings': 'Location Matching Settings',
        'match_by_city': 'Match only with users from my city',
        'match_by_country': 'Match only with users from my country',
        'location_matching_note': 'Note: These settings control which users appear in your swipe feed. If both are checked, city takes priority.',
        'welcome_to_support_chat': 'Welcome to Support Chat!',
        'support_will_respond_soon': 'Our support team will respond to your messages as soon as possible.',
        'type_your_message': 'Type your message...',
        'support_auto_response': 'Thank you for your message. Our support team has received your inquiry and will respond as soon as possible. In the meantime, you might find answers to common questions in our FAQ section.',
        'support_welcome_message': 'Hello! Welcome to FetDate support. How can we help you today?',
        'need_immediate_help': 'Need immediate help?',
        'contact_us_by_email': 'You can also contact us by email:',
        'typical_response_time': 'Typical response time: 24 hours',
        'admin_support_chat': 'Admin Support Chat',
        'back_to_admin_panel': 'Back to Admin Panel',
        'users': 'Users',
        'select_user_to_chat': 'Select a user to start chatting',
        'select_user_to_begin_chat': 'Select a user from the list to begin chatting',
        'loading': 'Loading...',
        'no_users_found': 'No users found',
        'hello_how_can_i_help': 'Hello, how can I help you?',
        'thanks_for_your_help': 'Thanks for your help!',
        'i_have_a_question': 'I have a question about...',
        'loading_chat_history': 'Loading chat history...',
        'no_messages_yet': 'No messages yet',
        'i_need_help_with_my_profile': 'I need help with my profile',
        'sure_ill_help_you_with_that': 'Sure, I\'ll help you with that. What seems to be the problem?',
        'support_tickets': 'Support Tickets',
        'select_ticket_to_chat': 'Select a ticket to start chatting',
        'select_ticket_to_begin_chat': 'Select a ticket from the list to begin chatting',
        'error_loading_tickets': 'Error loading tickets',
        'no_tickets_found': 'No tickets found',
        'error_loading_messages': 'Error loading messages',
        'error_sending_message': 'Error sending message. Please try again.',
        'welcome_to_support_chat': 'Welcome to Support Chat!',
        'support_will_respond_soon': 'Our support team will respond to your messages as soon as possible.',
        'support_welcome_message': 'Hello! Welcome to FetDate support. How can we help you today?',
        'support_online': 'Support Online',
        'admin': 'Admin',
        'close_ticket': 'Close Ticket',
        'confirm_close_ticket': 'Are you sure you want to close this ticket?',
        'no_ticket_selected_info': 'Select a ticket from the left panel to view and respond to support requests',
        'support_chat_with': 'Support Chat with',
        'select_ticket_to_begin_chat': 'Select a ticket from the list to begin chatting',
        'need_immediate_help': 'Need immediate help?',
        'contact_us_by_email': 'You can also contact us by email:',
        'error_sending_message': 'Error sending message. Please try again.',
        'required_fields_note': 'Fields marked with * are required to complete registration'
    },
    'ru': {
        'welcome': 'Добро пожаловать в FetDate!',
        'find_match': 'Найдите свою идеальную пару',
        'description': 'FetDate - это современная платформа для знакомств, где вы можете найти совпадения по общим интересам и фетишам.',
        'create_profile': 'Создать профиль',
        'complete_profile': 'Завершить профиль',
        'discover': 'Метчи',
        'connect': 'Связаться',
        'signup': 'Зарегистрироваться',
        'login': 'Войти',
        'logout': 'Выйти',
        'swipe_feature': 'Проведите пальцем по потенциальным совпадениям',
        'chat': 'Начните содержательные беседы',
        'get_started': 'Начать',
        'how_works': 'Как это работает',
        'step1': 'Регистрация',
        'step1_desc': 'Создайте свой профиль и расскажите нам о своих интересах и предпочтениях.',
        'step2': 'Свайп',
        'step2_desc': 'Откройте для себя потенциальные совпадения и проведите по ним пальцем в нашем современном интерфейсе.',
        'step3': 'Связаться',
        'step3_desc': 'Когда вы оба лайкните друг друга, начните чат и посмотрите, куда это приведет!',
        'username': 'Имя пользователя',
        'email': 'Электронная почта',
        'password': 'Пароль',
        'bio': 'Биография',
        'location': 'Местоположение',
        'country': 'Страна',
        'city': 'Город',
        'select_country': 'Выберите страну',
        'select_city': 'Выберите город',
        'photo': 'Фото профиля',
        'fetishes': 'Фетиши (Сексуальные предпочтения)',
        'interests': 'Интересы и хобби',
        'add_fetish': 'Добавить свой фетиш',
        'add_interest': 'Добавить свой интерес',
        'submit': 'Создать профиль',
        'update_profile': 'Обновить профиль',
        'view_profile': 'Просмотреть профиль',
        'all_users': 'Все пользователи',
        'swipe_now': 'Начать свайпинг',
        'no_users': 'Пока нет зарегистрированных пользователей',
        'be_first': 'Будьте первым, кто присоединится к нашему сообществу!',
        'member_since': 'Участник с',
        'about': 'О себе',
        'about_us': 'О нас',
        'our_story': 'Наша история',
        'our_story_content': 'Основанный с видением создания осмысленных связей, FetDate посвящен предоставлению уникального и инклюзивного дейтинг-опыта. Наша платформа объединяет людей, которые разделяют схожие интересы, ценности и образ жизни, способствуя установлению настоящих отношений в комфортной обстановке.',
        'our_mission': 'Наша миссия - создать безопасное пространство, где люди могут аутентично выражать себя и находить совместимых партнеров без осуждения. Мы верим, что каждый заслуживает любовь и товарищество, которое соответствует их уникальным предпочтениям.',
        'our_community': 'Наше растущее сообщество',
        'information': 'Информация',
        'no_bio': 'Биография не указана',
        'no_fetishes': 'Фетиши не указаны',
        'no_interests': 'Интересы не указаны',
        'discover_matches': 'Метчи',
        'no_more_users': 'Больше нет пользователей для показа',
        'check_later': 'Загляните позже для новых совпадений!',
        'reject': 'Отклонить',
        'superlike': 'Супер Лайк',
        'like': 'Лайк',
        'home': 'Главная',
        'profile': 'Профиль',
        'chat': 'Чат',
        'my_chats': 'Мои чаты',
        'no_active_chats': 'У вас пока нет активных чатов.',
        'start_chatting': 'Начните общаться, перейдя на',
        'swipe_page': 'страницу свайпов',
        'and_connect': 'и подключайтесь к другим пользователям!',
        'language': 'Язык',
        'english': 'English',
        'russian': 'Русский',
        'login_with_google': 'Войти через Google',
        'welcome_back': 'С возвращением',
        'profile_completed': 'Ваш профиль завершен!',
        'please_complete_profile': 'Пожалуйста, завершите свой профиль',
        'invalid_credentials': 'Неверное имя пользователя или пароль',
        'username_exists': 'Имя пользователя уже существует',
        'email_exists': 'Пользователь с этой электронной почтой уже зарегестрирован. Пожалуйста, используйте другой адрес электронной почты.',
        'registration_success': 'Регистрация успешна! Пожалуйста, войдите.',
        'already_have_account': 'Уже есть аккаунт?',
        'no_account': 'Нет аккаунта?',
        'required_field': 'Это поле обязательно для заполнения',
        'quick_actions': 'Быстрые действия',
        'edit_profile': 'Редактировать профиль',
        'notifications': 'Уведомления',
        'mark_all_read': 'Прочитать',
        'no_notifications': 'Пока нет уведомлений',
        'rate_this_user': 'Оцените этого пользователя',
        'your_rating': 'Ваша оценка:',
        'submit_rating': 'Отправить оценку',
        'premium_membership': 'Премиум подписка',
        'upgrade_to_premium': 'Премиум подписка',
        'back_to_profile': 'Назад к профилю',
        'premium': 'Премиум',
        'unlock_exclusive_features': 'Откройте эксклюзивные функции и улучшите свой опыт',
        'premium_features': 'Премиум возможности',
        'undo_swipes': 'Отмена свайпов',
        'undo_swipes_desc': 'Передумали? Отмените неограниченное количество свайпов в день',
        'unlimited_messaging': 'Неограниченные сообщения',
        'unlimited_messaging_desc': 'Отправляйте неограниченное количество сообщений своим совпадениям',
        'premium_badge': 'Премиум бейдж',
        'premium_badge_desc': 'Выделяйтесь с премиум бейджем в своем профиле',
        'subscription_details': 'Детали подписки',
        'currency': 'Валюта',
        'billing_cycle': 'Биллинговый цикл',
        'billing_cycle_desc': 'Ежемесячно (Автоматически продлевается)',
        'payment_methods': 'Способы оплаты',
        'payment_methods_desc': 'Кредитные/дебетовые карты, PayPal',
        'refund_policy_info': 'Политика возврата',
        'refund_policy_desc': 'Гарантия возврата денег в течение 7 дней для новых подписок',
        'how_it_works': 'Как это работает',
        'secure_payment': 'Безопасный платеж',
        'secure_payment_desc': 'Вся информация об оплате обрабатывается через безопасные зашифрованные каналы. Мы никогда не храним полные данные вашей кредитной карты на наших серверах. Наш платежный процессор соответствует стандарту PCI DSS для обеспечения защиты вашей финансовой информации.',
        'by_subscribing_premium': 'При подписке на премиум-услуги вы соглашаетесь с Условиями использования и Политикой возврата.',
        'why_users_love_premium': 'Почему пользователи любят премиум',
        'priority_matching': 'Приоритетный подбор',
        'advanced_filters': 'Расширенные фильтры',
        'extended_profile_visibility': 'Расширенная видимость профиля',
        'click_get_premium_now': 'Нажмите "Получить премиум сейчас", чтобы продолжить оплату',
        'enter_payment_info': 'Безопасно введите информацию о платеже',
        'subscription_activated': 'Ваша подписка будет активирована немедленно',
        'enjoy_premium_features': 'Наслаждайтесь премиум-функциями без перерывов',
        'subscription_renews': 'Подписка автоматически продлевается каждый месяц',
        'cancel_anytime_account': 'Отмените в любое время через настройки аккаунта',
        'testimonial_1': '"Премиум-функции помогли мне находить связи с людьми, разделяющими мои интересы. Неограниченные сообщения - это революция!"',
        'testimonial_2': '"Возможность отменить свайпы сохранила меня от случайного пропуска потенциальных совпадений. Каждая копейка стоит того!"',
        'testimonial_3': '"Премиум-бейдж выделяет меня из толпы. С момента обновления я получил(а) значительно больше совпадений."',
        'set_primary_photo': 'Сделать основной',
        'primary': 'Основная',
        'just_per_month': 'Всего $9.99/месяц',
        'cancel_anytime': 'Отменить в любое время',
        'current_photos': 'Текущие фотографии',
        'location_matching_settings': 'Настройки геолокации',
        'match_by_city': 'Показывать только пользователей из моего города',
        'match_by_country': 'Показывать только пользователей из моей страны',
        'location_matching_note': 'Примечание: Эти настройки контролируют, какие пользователи будут показываться в ленте. Если отмечены оба варианта, приоритет отдается городу.',
        'set_primary_photo': 'Сделать основной',
        'confirm_delete_photo': 'Вы уверены, что хотите удалить эту фотографию?',
        'photo_deleted': 'Фотография успешно удалена',
        'error_deleting_photo': 'Ошибка при удалении фотографии',
        'primary_photo_set': 'Основная фотография установлена успешно',
        'error_setting_primary_photo': 'Ошибка при установке основной фотографии',
        'delete': 'Удалить',
        'already_premium_member': 'Вы уже премиум участник!',
        'expires': 'Истекает',
        'cancel_subscription': 'Отменить подписку',
        'subscription_expired': 'Ваша премиум подписка истекла.',
        'get_premium_now': 'Получить премиум сейчас',
        'by_subscribing': 'Оформляя подписку, вы соглашаетесь с условиями обслуживания и политикой конфиденциальности.',
        'faq': 'Частые вопросы',
        'support': 'Поддержка',
        'contacts': 'Контакты',
        'agreement_to_terms': 'Соглашение с условиями',
        'agreement_to_terms_desc': 'Доступаясь к использованию FetDate (\"Сервис\"), вы соглашаетесь с соблюдением этих Условий использования (\"Условия\"). Если вы не согласны с какой-либо частью условий, вы не можете использовать Сервис.',
        'description_of_service': 'Описание сервиса',
        'description_of_service_desc': 'FetDate - это платформа для знакомств, которая позволяет пользователям находить связи с другими людьми на основе общих интересов и фетишей. Сервис предоставляет такие функции, как создание профиля, поиск совпадений, свайпинг и обмен сообщениями для облегчения установления контактов.',
        'user_accounts': 'Пользовательские аккаунты',
        'user_accounts_desc1': 'При создании учетной записи у нас вы должны предоставить точную и полную информацию. Вы несете ответственность за обеспечение безопасности вашей учетной записи и полностью несете ответственность за все действия, происходящие под вашей учетной записью.',
        'user_accounts_desc2': 'Вы должны немедленно сообщить нам, если узнаете о любом несанкционированном использовании вашей учетной записи или любом другом нарушении безопасности.',
        'subscription_and_payment': 'Подписка и оплата',
        'subscription_and_payment_desc1': 'Наш сервис предлагает премиум-подписки. Премиум-подписки автоматически продляются до тех пор, пока не будут отменены. Вы можете отменить подписку в любое время, обратившись к нам.',
        'subscription_and_payment_desc2': 'Все сборы включают применимые налоги, если это требуется законом. Мы можем изменить стоимость подписки в любое время с разумным уведомлением вам.',
        'purchases': 'Покупки',
        'purchases_desc1': 'Если вы совершаете покупки через Сервис, вы соглашаетесь предоставить актуальную, полную и точную информацию о покупке и учетной записи. Вы также соглашаетесь оплатить все сборы, указанные при совершении покупки.',
        'purchases_desc2': 'Мы оставляем за собой право отказать в любом заказе, который вы размещаете через Сервис.',
        'accuracy_of_information': 'Точность информации',
        'accuracy_of_information_desc': 'Хотя мы стремимся предоставлять точную информацию о нашем Сервисе, мы не даем никаких гарантий относительно полноты, точности, надежности или пригодности какой-либо информации, продукции или услуг, содержащихся в нашем Сервисе.',
        'intellectual_property': 'Интеллектуальная собственность',
        'intellectual_property_desc': 'Сервис и его оригинальный контент, функции и функциональность принадлежат FetDate и защищены международными законами об авторском праве, товарных знаках и другой интеллектуальной собственности.',
        'termination': 'Прекращение',
        'termination_desc1': 'Мы можем прекратить или приостановить вашу учетную запись немедленно, без предварительного уведомления, по любой причине, включая, помимо прочего, нарушение Условий.',
        'termination_desc2': 'После прекращения действия ваши права на использование Сервиса прекращаются немедленно.',
        'limitation_of_liability': 'Ограничение ответственности',
        'limitation_of_liability_desc': 'В любом случае FetDate, а также его директора, сотрудники, партнеры, агенты, поставщики или филиалы не несут ответственности за какие-либо косвенные, случайные, специальные, косвенные или штрафные убытки, включая, помимо прочего, упущенную прибыль, данные, использование, деловую репутацию или другие нематериальные потери.',
        'governing_law': 'Применимое право',
        'governing_law_desc': 'Настоящие Условия регулируются и толкуются в соответствии с законами, без учета положений о конфликте законов.',
        'changes_to_terms': 'Изменения в условиях',
        'changes_to_terms_desc': 'Мы оставляем за собой право по своему собственному усмотрению изменять или заменять настоящие Условия в любое время. Продолжая получать доступ или использовать наш Сервис после вступления этих изменений в силу, вы соглашаетесь соблюдать измененные условия.',
        'contact_us': 'Свяжитесь с нами',
        'contact_us_desc': 'Если у вас есть какие-либо вопросы о настоящих Условиях, пожалуйста, свяжитесь с нами по адресу',
        'privacy_policy': 'Политика конфиденциальности',
        'information_we_collect': 'Информация, которую мы собираем',
        'information_we_collect_desc': 'В FetDate мы собираем информацию, которую вы предоставляете нам напрямую, например, при создании учетной записи, обновлении профиля или общении с другими пользователями. Это включает:',
        'personal_information_item': 'Персональная информация (имя, адрес электронной почты, номер телефона)',
        'profile_information_item': 'Информация профиля (фото, биография, интересы, фетиши)',
        'location_data_item': 'Данные о местоположении (страна и город)',
        'payment_information_item': 'Платежная информация при покупке премиум-функций',
        'communication_preferences_item': 'Предпочтения в общении',
        'how_we_use_your_information': 'Как мы используем вашу информацию',
        'how_we_use_your_information_desc': 'Мы используем собранную информацию для:',
        'provide_maintain_improve_item': 'Предоставления, обслуживания и улучшения наших услуг',
        'process_transactions_item': 'Обработки транзакций и отправки связанной информации',
        'send_technical_notices_item': 'Отправки технических уведомлений и сообщений поддержки',
        'link_combine_information_item': 'Связывания или объединения информации пользователя с другими источниками',
        'protect_investigate_item': 'Защиты, расследования и предотвращения мошенничества, несанкционированных или незаконных действий',
        'information_sharing_disclosure': 'Раскрытие и передача информации',
        'information_sharing_disclosure_desc': 'Мы не передаем, не продаем и не сдаем в аренду вашу личную информацию третьим лицам в целях маркетинга. Мы можем передавать информацию:',
        'service_providers_item': 'Поставщикам услуг, которые выполняют услуги от нашего имени',
        'other_users_item': 'Другим пользователям в соответствии с настройками и предпочтениями вашего профиля',
        'third_parties_item': 'Третьим лицам в связи с объединением, приобретением или продажей активов',
        'legal_authorities_item': 'Органам правопорядка, когда это требует закон',
        'data_security': 'Безопасность данных',
        'data_security_desc': 'Мы применяем соответствующие технические и организационные меры для защиты безопасности вашей личной информации. Однако ни один метод передачи через Интернет или метод электронного хранения не является на 100% безопасным.',
        'your_data_protection_rights': 'Ваши права на защиту данных',
        'your_data_protection_rights_desc': 'В зависимости от вашего местоположения, вы можете иметь право:',
        'access_your_data_item': 'Получать доступ к вашим персональным данным',
        'rectify_data_item': 'Исправлять неточную информацию',
        'request_deletion_item': 'Запрашивать удаление ваших данных',
        'object_to_processing_item': 'Возражать против обработки',
        'data_portability_item': 'Портативность данных',
        'withdraw_consent_item': 'Отозвать согласие',
        'childrens_privacy': 'Конфиденциальность детей',
        'childrens_privacy_desc': 'Наш сервис не предназначен для лиц моложе 18 лет. Мы не собираем намеренно личную информацию от детей моложе 18 лет.',
        'changes_to_privacy_policy': 'Изменения в настоящей Политике конфиденциальности',
        'changes_to_privacy_policy_desc': 'Мы можем время от времени обновлять нашу Политику конфиденциальности. Мы уведомим вас о любых изменениях, разместив новую Политику конфиденциальности на этой странице.',
        'contact_us_privacy': 'Свяжитесь с нами (Конфиденциальность)',
        'contact_us_privacy_desc': 'Если у вас есть какие-либо вопросы о настоящей Политике конфиденциальности, пожалуйста, свяжитесь с нами по адресу',
        'refund_policy': 'Политика возврата',
        'premium_subscription_refunds': 'Возвраты премиум-подписки',
        'premium_subscription_refunds_desc': 'Мы предлагаем 7-дневную политику возврата для наших премиум-подписок. Если вы недовольны нашим премиум-сервисом, вы можете запросить возврат в течение 7 дней после первоначальной покупки.',
        'eligibility_for_refund': 'Право на возврат',
        'eligibility_for_refund_desc': 'Чтобы иметь право на возврат, ваша премиум-подписка должна:',
        'purchased_within_7_days_item': 'Быть приобретена в последние 7 дней',
        'not_extensively_used_item': 'Не использоваться в значительной степени (ограниченное общение, ограниченное использование премиум-функций)',
        'before_renewal_date_item': 'Запрашиваться до даты продления',
        'non_refundable_items': 'Пункты, не подлежащие возврату',
        'non_refundable_items_desc': 'Следующие пункты не подлежат возврату:',
        'individual_coins_item': 'Отдельные монеты, приобретенные для подарков или функций',
        'gifts_sent_item': 'Подарки, отправленные другим пользователям',
        'subscriptions_7_days_item': 'Подписки, которые были активны более 7 дней',
        'heavily_used_subscriptions_item': 'Подписки, которые использовались в значительной степени',
        'how_to_request_refund': 'Как запросить возврат',
        'how_to_request_refund_desc': 'Чтобы запросить возврат, пожалуйста, свяжитесь с нами по следующему адресу с указанием следующей информации:',
        'username_item': 'Ваше имя пользователя',
        'date_of_purchase_item': 'Дата покупки',
        'reason_for_refund_item': 'Причина запроса возврата',
        'transaction_id_item': 'ID транзакции (если доступно)',
        'processing_time': 'Срок обработки',
        'processing_time_desc': 'После получения и проверки запроса на возврат, мы вышлем вам электронное письмо с подтверждением принятия или отказа в вашем запросе на возврат. Если запрос одобрен, возврат будет обработан и кредит будет автоматически применен к вашему первоначальному методу оплаты в течение 5-10 рабочих дней.',
        'subscription_renewals': 'Продление подписки',
        'subscription_renewals_desc': 'Если ваша подписка продлевается автоматически до обработки возврата, мы вернем средства за последний расчетный цикл, если вы все еще находитесь в течение 7-дневного окна и соответствуете требованиям для возврата.',
        'special_circumstances': 'Особые обстоятельства',
        'special_circumstances_desc': 'В определенных исключительных обстоятельствах мы можем рассмотреть запросы на возврат за пределами 7-дневного окна, включая:',
        'technical_issues_item': 'Технические проблемы, препятствующие использованию сервиса',
        'billing_errors_item': 'Ошибки в выставлении счетов с нашей стороны',
        'account_suspension_item': 'Приостановка или прекращение действия аккаунта не по вине пользователя',
        'chargebacks_and_disputes': 'Чарджбэки и споры',
        'chargebacks_and_disputes_desc': 'Подача чарджбэка или спора по оплате в ваше финансовое учреждение аннулирует ваше право на любой возврат от нас. Пожалуйста, свяжитесь с нами в первую очередь, если у вас есть вопросы о вашей покупке.',
        'changes_to_refund_policy': 'Изменения в политике возврата',
        'changes_to_refund_policy_desc': 'Мы оставляем за собой право изменять эту политику возврата в любое время. Изменения вступают в силу немедленно после публикации на нашем веб-сайте. Ваше дальнейшее использование нашего сервиса после изменений означает принятие измененной политики.',
        'contact_us_refund': 'Свяжитесь с нами (Возврат)',
        'contact_us_refund_desc': 'Если у вас есть какие-либо вопросы или опасения относительно нашей политики возврата, пожалуйста, свяжитесь с нами по адресу',
        'terms_of_service': 'Условия предоставления услуг',
        'service_description': 'Описание сервиса',
        'service_description_desc': 'FetDate - это цифровая платформа для знакомств, которая предоставляет пользователям возможность создавать профили, находить связи с другими людьми на основе общих интересов и фетишей и общаться через различные функции. Наш сервис работает как программная платформа, доступная через веб-браузер.',
        'account_registration_process': 'Процесс регистрации аккаунта',
        'account_registration_process_desc': 'Чтобы использовать наши услуги, пользователи должны создать аккаунт, предоставив точную и полную информацию, включая, помимо прочего, имя пользователя, адрес электронной почты и пароль. Пользователям должно быть не менее 18 лет для регистрации. Аккаунты должны поддерживаться с точной и актуальной информацией.',
        'payment_and_billing': 'Оплата и выставление счетов',
        'payment_and_billing_desc': 'Наша платформа предлагает как бесплатные, так и премиум-услуги:',
        'free_services_item': 'Бесплатные услуги включают в себя создание базового профиля, ограниченный свайпинг и базовый подбор',
        'premium_services_item': 'Премиум-услуги включают в себя такие функции, как неограниченные сообщения, продвинутый подбор и специальные значки',
        'premium_cost_item': 'Премиум-подписки оплачиваются ежемесячно по цене 9,99 долл. США',
        'payment_processing_item': 'Оплата обрабатывается безопасно через нашего платежного процессора',
        'automatic_renewal_item': 'Подписки автоматически продлеваются до тех пор, пока пользователь не отменит их',
        'digital_content_delivery': 'Доставка цифрового контента',
        'digital_content_delivery_desc': 'Все цифровые продукты и услуги предоставляются сразу после покупки:',
        'premium_access_item': 'Доступ к премиум-подписке предоставляется мгновенно после успешной оплаты',
        'in_app_currency_item': 'Внутриигровая валюта (монеты) добавляется на ваш аккаунт немедленно',
        'enhanced_features_item': 'Расширенные функции становятся доступными сразу после покупки',
        'user_responsibilities': 'Обязанности пользователя',
        'user_responsibilities_desc': 'Пользователи несут ответственность за:',
        'confidentiality_item': 'Сохранение конфиденциальности информации своей учетной записи',
        'accurate_information_item': 'Предоставление точной и актуальной информации профиля',
        'respectful_behavior_item': 'Уважительное поведение по отношению к другим пользователям',
        'compliance_item': 'Соблюдение всех применимых законов и нормативных актов',
        'service_availability': 'Доступность сервиса',
        'service_availability_desc': 'Мы стремимся обеспечить доступность нашего сервиса 24/7. Однако сервис может быть временно недоступен во время планового технического обслуживания или в случае технических проблем. Мы не несем ответственности за какие-либо неудобства, вызванные временным прерыванием работы сервиса.',
        'data_protection': 'Защита данных',
        'data_protection_desc': 'Все пользовательские данные зашифрованы и хранятся безопасно. Мы применяем стандартные отраслевые меры безопасности для защиты пользовательской информации. Персональная информация обрабатывается в соответствии с нашей Политикой конфиденциальности.',
        'cancellation_and_account_termination': 'Отмена и прекращение аккаунта',
        'cancellation_and_account_termination_desc': 'Пользователи могут отменить свои подписки в любое время. Для премиум-членств отмена будет действовать в конце текущего расчетного периода. Пользователи могут полностью закрыть свои аккаунты, обратившись в службу поддержки. Закрытие аккаунта приводит к немедленной деактивации профиля и удалению из систем подбора.',
        'customer_support': 'Поддержка клиентов',
        'customer_support_desc': 'Поддержка клиентов доступна через нашу внутреннюю систему поддержки и по электронной почте',
        'customer_support_desc_continued': 'Мы стремимся отвечать на все запросы в течение 24 часов. Поддержка доступна для вопросов, связанных с аккаунтами, оплатой и техническими проблемами.',
        'limitation_of_liability': 'Ограничение ответственности',
        'limitation_of_liability_desc': 'Наша ответственность ограничена суммой, уплаченной пользователем за услуги в течение 12 месяцев перед событием, повлекшим за собой претензию. Мы не несем ответственности за косвенный, случайный или косвенный ущерб.',
        'dispute_resolution': 'Решение споров',
        'dispute_resolution_desc': 'Любые споры, связанные с нашими услугами, должны сначала быть решены через наш канал поддержки клиентов. Если спор не будет решен, он может быть передан на обязательную арбитражную процедуру в соответствии с нашими Условиями использования.',
        'governing_law': 'Применимое право',
        'governing_law_desc': 'Настоящие Условия предоставления услуг регулируются международным правом в отношении доставки цифровых услуг. Любые судебные разбирательства, связанные с этими условиями, должны быть инициированы в юрисдикции, где зарегистрирована наша компания.',
        'modifications_to_service': 'Изменения в сервисе',
        'modifications_to_service_desc': 'Мы оставляем за собой право в любое время изменять наши услуги, функции и настоящие Условия предоставления услуг. Пользователи будут уведомлены о существенных изменениях по электронной почте или через внутреннее уведомление. Продолжение использования сервиса означает принятие измененных условий.',
        'contact_information': 'Контактная информация',
        'contact_information_desc': 'По вопросам, касающимся настоящих Условий предоставления услуг, пожалуйста, свяжитесь с нами по адресу',
        'contact_us_title': 'Свяжитесь с нами',
        'get_in_touch': 'Свяжитесь с нами',
        'get_in_touch_desc': 'Мы здесь, чтобы помочь! Если у вас есть какие-либо вопросы, опасения или отзывы о нашем сервисе, пожалуйста, не стесняйтесь обращаться к нам.',
        'support_email': 'Электронная почта поддержки',
        'support_team_response_desc': 'Наша команда поддержки обычно отвечает в течение 24 часов. Пожалуйста, укажите ваше имя пользователя в сообщении для более быстрой помощи.',
        'mailing_address': 'Почтовый адрес',
        'legal_matters_desc': 'По юридическим вопросам и официальной переписке:',
        'fetdate_support_team': 'Команда поддержки FetDate',
        'attention_legal_dept': 'Команде: Юридический отдел',
        'physical_address': '[Физический адрес для юридических споров]',
        'city_state_zip': '[Город, Штат, Почтовый индекс]',
        'phone_support': 'Телефонная поддержка',
        'immediate_assistance_desc': 'Для срочной помощи вы можете связаться с нами по:',
        'urgent_account_issues': '(По срочным вопросам аккаунта)',
        'phone_hours': 'Телефонная поддержка доступна с понедельника по пятницу с 9:00 до 18:00 по восточному времени США',
        'report_an_issue': 'Сообщить о проблеме',
        'report_an_issue_desc': 'Если вам нужно сообщить о пользователе, контенте или технической проблеме:',
        'report_user_button': 'Используйте кнопку \"Пожаловаться на пользователя\" в любом профиле',
        'moderation_team_email': 'Свяжитесь с нашей командой модерации по адресу',
        'in_app_support_chat': 'Используйте внутреннюю функцию чата поддержки',
        'business_inquiries': 'Коммерческие запросы',
        'business_inquiries_desc': 'По вопросам делового сотрудничества, запросам прессы или рекламным возможностям:',
        'business_email': 'business@fetdate.online',
        'feedback_and_suggestions': 'Отзывы и предложения',
        'feedback_and_suggestions_desc': 'Мы ценим ваши отзывы и предложения по улучшению нашего сервиса. Пожалуйста, отправляйте свои идеи на:',
        'feedback_email': 'feedback@fetdate.online',
        'frequently_asked_questions': 'Часто задаваемые вопросы',
        'back_to_home': 'Назад на главную',
        'how_do_i_create_an_account': 'Как создать аккаунт?',
        'how_do_i_create_an_account_answer': 'Чтобы создать аккаунт, нажмите кнопку "Зарегистрироваться" на главной странице. Заполните имя пользователя, электронную почту и пароль, затем следуйте инструкциям для завершения профиля.',
        'how_do_i_find_matches': 'Как найти совпадения?',
        'how_do_i_find_matches_answer': 'После завершения профиля перейдите в раздел "Метчи", чтобы начать свайпинг по потенциальным совпадениям. Вы можете лайкать или отклонять профили по вашим предпочтениям.',
        'is_my_information_secure': 'Безопасна ли моя информация?',
        'is_my_information_secure_answer': 'Мы серьезно относимся к вашей конфиденциальности. Вся личная информация шифруется и надежно хранится. Мы никогда не передаем ваши данные третьим сторонам без вашего согласия.',
        'what_are_premium_features': 'Какие возможности даёт Премиум?',
        'what_are_premium_features_answer': 'Премиум участники получают неограниченные свайпы, возможность отменять неограниченное количество свайпов в день, неограниченные сообщения и премиум бейдж на своем профиле. Премиум также обеспечивает приоритетное размещение в очереди обнаружения.',
        'how_do_i_contact_support': 'Как связаться с поддержкой?',
        'how_do_i_contact_support_answer': 'Вы можете связаться с нашей командой поддержки через ссылку "Связаться с поддержкой" в меню профиля или по электронной почте support@fetdate.online. Наша команда обычно отвечает в течение 24 часов.',
        'still_have_questions': 'Остались вопросы?',
        'contact_our_support_team': 'Свяжитесь с нашей командой поддержки для персональной помощи.',
        'contact_support': 'Связаться с поддержкой',
        'support_chat': 'Чат с поддержкой',
        'back_to_profile': 'Назад к профилю',
        'welcome_to_support_chat': 'Добро пожаловать в чат с поддержкой!',
        'support_will_respond_soon': 'Наша команда поддержки ответит на ваши сообщения как можно скорее.',
        'type_your_message': 'Введите ваше сообщение...',
        'support_auto_response': 'Спасибо за ваше сообщение. Наша команда поддержки получила ваш запрос и ответит как можно скорее. Тем временем вы можете найти ответы на часто задаваемые вопросы в нашем разделе FAQ.',
        'support_welcome_message': 'Здравствуйте! Добро пожаловать в поддержку FetDate. Чем мы можем вам помочь?',
        'need_immediate_help': 'Нужна срочная помощь?',
        'contact_us_by_email': 'Вы также можете связаться с нами по электронной почте:',
        'typical_response_time': 'Среднее время ответа: 24 часа',
        'admin_support_chat': 'Чат поддержки для администраторов',
        'back_to_admin_panel': 'Назад к панели администратора',
        'users': 'Пользователи',
        'select_user_to_chat': 'Выберите пользователя для начала чата',
        'select_user_to_begin_chat': 'Выберите пользователя из списка, чтобы начать чат',
        'loading': 'Загрузка...',
        'no_users_found': 'Пользователи не найдены',
        'hello_how_can_i_help': 'Здравствуйте, чем могу помочь?',
        'thanks_for_your_help': 'Спасибо за вашу помощь!',
        'i_have_a_question': 'У меня есть вопрос о...',
        'loading_chat_history': 'Загрузка истории чата...',
        'no_messages_yet': 'Пока нет сообщений',
        'i_need_help_with_my_profile': 'Мне нужна помощь с моим профилем',
        'sure_ill_help_you_with_that': 'Конечно, я помогу вам с этим. В чем проблема?',
        'support_tickets': 'Запросы в поддержку',
        'select_ticket_to_chat': 'Выберите запрос для начала чата',
        'select_ticket_to_begin_chat': 'Выберите запрос из списка, чтобы начать чат',
        'support_online': 'Поддержка онлайн',
        'admin': 'Админ',
        'close_ticket': 'Закрыть тикет',
        'confirm_close_ticket': 'Вы уверены, что хотите закрыть этот тикет?',
        'no_ticket_selected_info': 'Выберите тикет слева, чтобы посмотреть и ответить на запросы в поддержку',
        'support_chat_with': 'Чат поддержки с',
        'error_loading_tickets': 'Ошибка загрузки запросов',
        'no_tickets_found': 'Запросы не найдены',
        'error_loading_messages': 'Ошибка загрузки сообщений',
        'error_sending_message': 'Ошибка отправки сообщения. Пожалуйста, попробуйте снова.',
        'welcome_to_support_chat': 'Добро пожаловать в чат с поддержкой!',
        'support_will_respond_soon': 'Наша команда поддержки ответит на ваши сообщения как можно скорее.',
        'type_your_message': 'Введите ваше сообщение...',
        'support_auto_response': 'Спасибо за ваше сообщение. Наша команда поддержки получила ваш запрос и ответит как можно скорее. Тем временем вы можете найти ответы на часто задаваемые вопросы в нашем разделе FAQ.',
        'support_welcome_message': 'Здравствуйте! Добро пожаловать в поддержку FetDate. Чем мы можем вам помочь?',
        'need_immediate_help': 'Нужна срочная помощь?',
        'contact_us_by_email': 'Вы также можете связаться с нами по электронной почте:',
        'typical_response_time': 'Среднее время ответа: 24 часа',
        'ready_to_find_love': 'Готовы найти любовь?',
        'discover_new_connections': 'Откройте для себя новые связи и найдите свою идеальную пару уже сегодня.',
        'why_choose_us': 'Почему выбирают нас?',
        'safe_and_secure': 'Безопасно и надежно',
        'privacy_protection': 'Ваша конфиденциальность - наш приоритет с передовыми мерами безопасности.',
        'verified_profiles': 'Проверенные профили',
        'authentic_people': 'Познакомьтесь с аутентичными людьми, у которых есть проверенные профили и фотографии.',
        'instant_matching': 'Мгновенное подбор пар',
        'real_time_connect': 'Свяжитесь с совместимыми парами в режиме реального времени.',
        'join_our_community': 'Присоединяйтесь к нашему сообществу уже сегодня!',
        'find_your_perfect_match': 'Найдите свою идеальную пару и общайтесь с единомышленниками, которые разделяют ваши интересы и страсти.',
        'join_thousands': 'Присоединяйтесь к тысячам довольных участников!',
        'active_users': 'Активные пользователи',
        'successful_matches': 'Успешные совпадения',
        'satisfaction_rate': 'Уровень удовлетворенности',
        'choose_file': 'Выберите файл',
        'no_file_chosen': 'Файл не выбран',
        'choose_files': 'Выберите файлы',
        'extended_profile': 'Расширенный профиль',
        'about_me_video': 'Видео о себе',
        'relationship_goals': 'Цели отношений',
        'long_term_relationship': 'Долгосрочные отношения',
        'short_term_fun': 'Краткосрочное веселье',
        'marriage': 'Брак',
        'friends': 'Дружба',
        'open_relationship': 'Открытые отношения',
        'lifestyle': 'Образ жизни',
        'active': 'Активный',
        'sedentary': 'Малоподвижный',
        'moderate': 'Умеренный',
        'very_active': 'Очень активный',
        'diet': 'Диета',
        'vegetarian': 'Вегетарианец',
        'vegan': 'Веган',
        'omnivore': 'Всеядный',
        'pescatarian': 'Пескатарианец',
        'keto': 'Кето-диета',
        'paleo': 'Палео-диета',
        'smoking': 'Курение',
        'never': 'Никогда',
        'occasionally': 'Иногда',
        'socially': 'Социально',
        'regularly': 'Регулярно',
        'drinking': 'Употребление алкоголя',
        'occupation': 'Род занятий',
        'education': 'Образование',
        'children': 'Дети',
        'none': 'Нет',
        'yes': 'Да',
        'want_someday': 'Хочу когда-нибудь',
        'dont_want': 'Не хочу',
        'pets': 'Домашние животные',
        'comma_separated': 'через запятую',
        'no_files_chosen': 'Файлы не выбраны',
        'send_message_instead': 'Отправить сообщение вместо лайка',
        'message_limit_info': 'У вас есть 1 бесплатное сообщение в день. Перейдите на Премиум, чтобы получить неограниченные сообщения.',
        'write_message_placeholder': 'Напишите ваше сообщение здесь...',
        'cancel': 'Отмена',
        'send_message': 'Отправить сообщение',
        'note': 'Примечание',
        'continue_swiping': 'Продолжить свайпинг',
        'view_matches': 'Просмотреть совпадения',
        'terms_of_use': 'Условия использования',
        'privacy_policy': 'Политика конфиденциальности',
        'refund_policy': 'Политика возврата',
        'terms_of_service': 'Условия предоставления услуг'
    }
}

def get_text(key):
    """Get translated text based on current language"""
    lang = session.get('language', 'en')
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)

def static_version(filename):
    """Generate a version string for static files to avoid caching issues"""
    try:
        # Check for both the original file and its minified version
        min_filename = filename.replace('.css', '.min.css').replace('.js', '.min.js')
        min_file_path = os.path.join(app.root_path, 'static', min_filename)
        
        # Use minified file if it exists, otherwise use original
        if os.path.exists(min_file_path):
            return '?v=' + str(int(os.path.getmtime(min_file_path)))
        
        file_path = os.path.join(app.root_path, 'static', filename)
        if os.path.exists(file_path):
            return '?v=' + str(int(os.path.getmtime(file_path)))
        else:
            return '?v=' + str(int(os.path.getmtime(os.path.join(app.root_path, 'static', 'css', 'style.css'))))
    except:
        return '?v=' + str(int(time.time()))


@app.context_processor
def inject_static_version():
    """Make static_version available in all templates"""
    return dict(static_version=static_version)


@app.context_processor
def inject_language():
    lang = session.get('language', 'en')
    
    # Define countries and their cities
    countries_cities = {
        'Russia': ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg', 'Kazan', 'Nizhny Novgorod', 'Chelyabinsk', 'Samara', 'Omsk', 'Rostov-on-Don'],
        'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'],
        'UK': ['London', 'Birmingham', 'Manchester', 'Glasgow', 'Liverpool', 'Leeds', 'Sheffield', 'Bristol', 'Edinburgh', 'Cardiff'],
        'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne', 'Frankfurt', 'Stuttgart', 'Duesseldorf', 'Leipzig', 'Dortmund', 'Essen'],
        'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille'],
        'Japan': ['Tokyo', 'Osaka', 'Yokohama', 'Nagoya', 'Sapporo', 'Fukuoka', 'Kobe', 'Kyoto', 'Saitama', 'Hiroshima'],
        'Canada': ['Toronto', 'Montreal', 'Vancouver', 'Calgary', 'Edmonton', 'Ottawa', 'Winnipeg', 'Quebec City', 'Hamilton', 'Kitchener'],
        'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Gold Coast', 'Newcastle', 'Wollongong', 'Logan City', 'Geelong'],
        'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Palermo', 'Genoa', 'Bologna', 'Florence', 'Bari', 'Catania'],
        'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Zaragoza', 'Malaga', 'Murcia', 'Palma', 'Valladolid', 'Vigo'],
        'Brazil': ['Sao Paulo', 'Rio de Janeiro', 'Brasilia', 'Salvador', 'Fortaleza', 'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Porto Alegre'],
        'Mexico': ['Mexico City', 'Ecatepec', 'Guadalajara', 'Puebla', 'Tijuana', 'Leon', 'Juarez', 'Zapopan', 'Monterrey', 'Nezahualcoyotl'],
        'South Korea': ['Seoul', 'Busan', 'Incheon', 'Daegu', 'Daejeon', 'Gwangju', 'Suwon', 'Ulsan', 'Bucheon', 'Goyang'],
        'India': ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow'],
        'China': ['Shanghai', 'Beijing', 'Chongqing', 'Tianjin', 'Guangzhou', 'Shenzhen', 'Chengdu', 'Nanjing', 'Wuhan', 'Hangzhou'],
        'Netherlands': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven', 'Tilburg', 'Groningen', 'Almere', 'Breda', 'Nijmegen'],
        'Sweden': ['Stockholm', 'Gothenburg', 'Malmo', 'Uppsala', 'Vasteras', 'Orebro', 'Linkoping', 'Helsingborg', 'Jonkoping', 'Norrkoping'],
        'Norway': ['Oslo', 'Bergen', 'Trondheim', 'Stavanger', 'Drammen', 'Fredrikstad', 'Kristiansand', 'Tromso', 'Sandnes', 'Sarpsborg'],
        'Denmark': ['Copenhagen', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg', 'Randers', 'Kolding', 'Horsens', 'Silkeborg', 'Vejle'],
        'Finland': ['Helsinki', 'Espoo', 'Tampere', 'Vantaa', 'Oulu', 'Turku', 'Jyvaskyla', 'Lahti', 'Kuopio', 'Pori'],
        'Poland': ['Warsaw', 'Krakow', 'Lodz', 'Wroclaw', 'Poznan', 'Gdansk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Katowice'],
        'Ukraine': ['Kyiv', 'Kharkiv', 'Odessa', 'Dnipro', 'Donetsk', 'Zaporizhzhia', 'Lviv', 'Kryvyi Rih', 'Mykolaiv', 'Mariupol'],
        'Turkey': ['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Adana', 'Gaziantep', 'Konya', 'Antalya', 'Diyarbakir', 'Mersin'],
        'Saudi Arabia': ['Riyadh', 'Jeddah', 'Mecca', 'Medina', 'Dammam', 'Taif', 'Tabuk', 'Buraidah', 'Al Hofuf', 'Khamis Mushait'],
        'United Arab Emirates': ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Fujairah', 'Ras al Khaimah', 'Khor Fakkan', 'Al Ain', 'Umm al Quwain', 'Dibba Al-Fujairah'],
        'South Africa': ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Port Elizabeth', 'Bloemfontein', 'East London', 'Pietermaritzburg', 'Polokwane', 'Nelspruit']
    }
    
    # If Russian language is selected, return translated countries and cities
    if lang == 'ru':
        # Translations for countries
        country_translations = {
            'Russia': 'Россия',
            'USA': 'США',
            'UK': 'Великобритания',
            'Germany': 'Германия',
            'France': 'Франция',
            'Japan': 'Япония',
            'Canada': 'Канада',
            'Australia': 'Австралия',
            'Italy': 'Италия',
            'Spain': 'Испания',
            'Brazil': 'Бразилия',
            'Mexico': 'Мексика',
            'South Korea': 'Южная Корея',
            'India': 'Индия',
            'China': 'Китай',
            'Netherlands': 'Нидерланды',
            'Sweden': 'Швеция',
            'Norway': 'Норвегия',
            'Denmark': 'Дания',
            'Finland': 'Финляндия',
            'Poland': 'Польша',
            'Ukraine': 'Украина',
            'Turkey': 'Турция',
            'Saudi Arabia': 'Саудовская Аравия',
            'United Arab Emirates': 'Объединенные Арабские Эмираты',
            'South Africa': 'Южная Африка'
        }
        
        # Translations for cities
        city_translations = {
            # Russia
            'Moscow': 'Москва',
            'Saint Petersburg': 'Санкт-Петербург',
            'Novosibirsk': 'Новосибирск',
            'Yekaterinburg': 'Екатеринбург',
            'Kazan': 'Казань',
            'Nizhny Novgorod': 'Нижний Новгород',
            'Chelyabinsk': 'Челябинск',
            'Samara': 'Самара',
            'Omsk': 'Омск',
            'Rostov-on-Don': 'Ростов-на-Дону',
            # USA
            'New York': 'Нью-Йорк',
            'Los Angeles': 'Лос-Анджелес',
            'Chicago': 'Чикаго',
            'Houston': 'Хьюстон',
            'Phoenix': 'Феникс',
            'Philadelphia': 'Филадельфия',
            'San Antonio': 'Сан-Антонио',
            'San Diego': 'Сан-Диего',
            'Dallas': 'Даллас',
            'San Jose': 'Сан-Хосе',
            # UK
            'London': 'Лондон',
            'Birmingham': 'Бирмингем',
            'Manchester': 'Манчестер',
            'Glasgow': 'Глазго',
            'Liverpool': 'Ливерпуль',
            'Leeds': 'Лидс',
            'Sheffield': 'Шеффилд',
            'Bristol': 'Бристоль',
            'Edinburgh': 'Эдинбург',
            'Cardiff': 'Кардифф',
            # Germany
            'Berlin': 'Берлин',
            'Hamburg': 'Гамбург',
            'Munich': 'Мюнхен',
            'Cologne': 'Кёльн',
            'Frankfurt': 'Франкфурт-на-Майне',
            'Stuttgart': 'Штутгарт',
            'Duesseldorf': 'Дюссельдорф',
            'Leipzig': 'Лейпциг',
            'Dortmund': 'Дортмунд',
            'Essen': 'Эссен',
            # France
            'Paris': 'Париж',
            'Marseille': 'Марсель',
            'Lyon': 'Лион',
            'Toulouse': 'Тулуза',
            'Nice': 'Ницца',
            'Nantes': 'Нант',
            'Strasbourg': 'Страсбург',
            'Montpellier': 'Монпелье',
            'Bordeaux': 'Бордо',
            'Lille': 'Лилль',
            # Japan
            'Tokyo': 'Токио',
            'Osaka': 'Осака',
            'Yokohama': 'Йокогама',
            'Nagoya': 'Нагоя',
            'Sapporo': 'Саппоро',
            'Fukuoka': 'Фукуока',
            'Kobe': 'Кобе',
            'Kyoto': 'Киото',
            'Saitama': 'Сайтама',
            'Hiroshima': 'Хиросима',
            # Canada
            'Toronto': 'Торонто',
            'Montreal': 'Монреаль',
            'Vancouver': 'Ванкувер',
            'Calgary': 'Калгари',
            'Edmonton': 'Эдмонтон',
            'Ottawa': 'Оттава',
            'Winnipeg': 'Виннипег',
            'Quebec City': 'Квебек',
            'Hamilton': 'Хамильтон',
            'Kitchener': 'Китченер',
            # Australia
            'Sydney': 'Сидней',
            'Melbourne': 'Мельбурн',
            'Brisbane': 'Брисбен',
            'Perth': 'Перт',
            'Adelaide': 'Аделаида',
            'Gold Coast': 'Золотой берег',
            'Newcastle': 'Ньюкасл',
            'Wollongong': 'Воллонгонг',
            'Logan City': 'Логан',
            'Geelong': 'Джилонг',
            # Italy
            'Rome': 'Рим',
            'Milan': 'Милан',
            'Naples': 'Неаполь',
            'Turin': 'Турин',
            'Palermo': 'Палермо',
            'Genoa': 'Генуя',
            'Bologna': 'Болонья',
            'Florence': 'Флоренция',
            'Bari': 'Бари',
            'Catania': 'Катания',
            # Spain
            'Madrid': 'Мадрид',
            'Barcelona': 'Барселона',
            'Valencia': 'Валенсия',
            'Seville': 'Севилья',
            'Zaragoza': 'Сарагоса',
            'Malaga': 'Малага',
            'Murcia': 'Мурсия',
            'Palma': 'Пальма',
            'Valladolid': 'Вальядолид',
            'Vigo': 'Виго',
            # Brazil
            'Sao Paulo': 'Сан-Паулу',
            'Rio de Janeiro': 'Рио-де-Жанейро',
            'Brasilia': 'Бразилиа',
            'Salvador': 'Сальвадор',
            'Fortaleza': 'Форталеза',
            'Belo Horizonte': 'Белу-Оризонти',
            'Manaus': 'Манаус',
            'Curitiba': 'Куричитба',
            'Recife': 'Ресифи',
            'Porto Alegre': 'Порту-Алегри',
            # Mexico
            'Mexico City': 'Мехико',
            'Ecatepec': 'Экатегек',
            'Guadalajara': 'Гвадалахара',
            'Puebla': 'Пуэбла',
            'Tijuana': 'Тихуана',
            'Leon': 'Леон',
            'Juarez': 'Хуарес',
            'Zapopan': 'Сапопан',
            'Monterrey': 'Монтеррей',
            'Nezahualcoyotl': 'Нецахуалькойотль',
            # South Korea
            'Seoul': 'Сеул',
            'Busan': 'Пусан',
            'Incheon': 'Инчхон',
            'Daegu': 'Тэгу',
            'Daejeon': 'Тэджон',
            'Gwangju': 'Кванджу',
            'Suwon': 'Сувон',
            'Ulsan': 'Ульсан',
            'Bucheon': 'Пучхон',
            'Goyang': 'Коян',
            # India
            'Mumbai': 'Мумбаи',
            'Delhi': 'Дели',
            'Bangalore': 'Бангалор',
            'Hyderabad': 'Хайдарабад',
            'Chennai': 'Ченнаи',
            'Kolkata': 'Калькутта',
            'Pune': 'Пуна',
            'Ahmedabad': 'Ахмедабад',
            'Jaipur': 'Джайпур',
            'Lucknow': 'Лакноу',
            # China
            'Shanghai': 'Шанхай',
            'Beijing': 'Пекин',
            'Chongqing': 'Чунцин',
            'Tianjin': 'Тяньцзинь',
            'Guangzhou': 'Гуанчжоу',
            'Shenzhen': 'Шэньчжэнь',
            'Chengdu': 'Чэнду',
            'Nanjing': 'Нанкин',
            'Wuhan': 'Ухань',
            'Hangzhou': 'Ханчжоу',
            # Netherlands
            'Amsterdam': 'Амстердам',
            'Rotterdam': 'Роттердам',
            'The Hague': 'Гаага',
            'Utrecht': 'Утрехт',
            'Eindhoven': 'Эйндховен',
            'Tilburg': 'Тилбург',
            'Groningen': 'Гронинген',
            'Almere': 'Альмере',
            'Breda': 'Бреда',
            'Nijmegen': 'Неймеген',
            # Sweden
            'Stockholm': 'Стокгольм',
            'Gothenburg': 'Гётеборг',
            'Malmo': 'Мальмё',
            'Uppsala': 'Упсала',
            'Vasteras': 'Вестерос',
            'Orebro': 'Эребру',
            'Linkoping': 'Линчёпинг',
            'Helsingborg': 'Хельсингборг',
            'Jonkoping': 'Йёнчёпинг',
            'Norrkoping': 'Норрчёпинг',
            # Norway
            'Oslo': 'Осло',
            'Bergen': 'Берген',
            'Trondheim': 'Тронхейм',
            'Stavanger': 'Ставангер',
            'Drammen': 'Драммен',
            'Fredrikstad': 'Фредрикстад',
            'Kristiansand': 'Кристиансанд',
            'Tromso': 'Тромсё',
            'Sandnes': 'Санднес',
            'Sarpsborg': 'Сарпсборг',
            # Denmark
            'Copenhagen': 'Копенгаген',
            'Aarhus': 'Орхус',
            'Odense': 'Оденсе',
            'Aalborg': 'Ольборг',
            'Esbjerg': 'Эсбьерг',
            'Randers': 'Рандерс',
            'Kolding': 'Колдинг',
            'Horsens': 'Хорсенс',
            'Silkeborg': 'Силькеборг',
            'Vejle': 'Вейле',
            # Finland
            'Helsinki': 'Хельсинки',
            'Espoo': 'Эспоо',
            'Tampere': 'Тампере',
            'Vantaa': 'Вантаа',
            'Oulu': 'Оулу',
            'Turku': 'Турку',
            'Jyvaskyla': 'Ювяскюля',
            'Lahti': 'Лахти',
            'Kuopio': 'Куопио',
            'Pori': 'Пори',
            # Poland
            'Warsaw': 'Варшава',
            'Krakow': 'Краков',
            'Lodz': 'Лодзь',
            'Wroclaw': 'Вроцлав',
            'Poznan': 'Познань',
            'Gdansk': 'Гданьск',
            'Szczecin': 'Щецин',
            'Bydgoszcz': 'Быдгощ',
            'Lublin': 'Люблин',
            'Katowice': 'Катовице',
            # Ukraine
            'Kyiv': 'Киев',
            'Kharkiv': 'Харьков',
            'Odessa': 'Одесса',
            'Dnipro': 'Днепр',
            'Donetsk': 'Донецк',
            'Zaporizhzhia': 'Запорожье',
            'Lviv': 'Львов',
            'Kryvyi Rih': 'Кривой Рог',
            'Mykolaiv': 'Николаев',
            'Mariupol': 'Мариуполь',
            # Turkey
            'Istanbul': 'Стамбул',
            'Ankara': 'Анкара',
            'Izmir': 'Измир',
            'Bursa': 'Бурса',
            'Adana': 'Адана',
            'Gaziantep': 'Газиантеп',
            'Konya': 'Конья',
            'Antalya': 'Анталья',
            'Diyarbakir': 'Диярбакыр',
            'Mersin': 'Мерсин',
            # Saudi Arabia
            'Riyadh': 'Эр-Рияд',
            'Jeddah': 'Джидда',
            'Mecca': 'Мекка',
            'Medina': 'Медина',
            'Dammam': 'Даммам',
            'Taif': 'Тайф',
            'Tabuk': 'Табук',
            'Buraidah': 'Бураидах',
            'Al Hofuf': 'Хафуф',
            'Khamis Mushait': 'Хамис-Мушайт',
            # United Arab Emirates
            'Dubai': 'Дубай',
            'Abu Dhabi': 'Абу-Даби',
            'Sharjah': 'Шарджа',
            'Ajman': 'Аджман',
            'Fujairah': 'Фуджейра',
            'Ras al Khaimah': 'Рас-эль-Хайма',
            'Khor Fakkan': 'Хор-Факкан',
            'Al Ain': 'Эль-Айн',
            'Umm al Quwain': 'Умм-эль-Кувейн',
            'Dibba Al-Fujairah': 'Дибба-Аль-Фуджейра',
            # South Africa
            'Johannesburg': 'Йоханнесбург',
            'Cape Town': 'Кейптаун',
            'Durban': 'Дурбан',
            'Pretoria': 'Претория',
            'Port Elizabeth': 'Порт-Элизабет',
            'Bloemfontein': 'Блумфонтейн',
            'East London': 'Ист-Лондон',
            'Pietermaritzburg': 'Пьетермарицбург',
            'Polokwane': 'Полокване',
            'Nelspruit': 'Нелспруйт'
        }
        
        # Create translated countries and cities
        translated_countries = [country_translations.get(country, country) for country in countries_cities.keys()]
        translated_countries_cities = {}
        for country, cities in countries_cities.items():
            translated_country = country_translations.get(country, country)
            translated_cities = [city_translations.get(city, city) for city in cities]
            translated_countries_cities[translated_country] = translated_cities
        
        return dict(
            get_text=get_text, 
            countries=translated_countries,
            COUNTRIES_CITIES=translated_countries_cities,
            SITE_NAME=SITE_NAME,
            is_premium_user=is_premium_user
        )
    else:
        # Return original English values
        return dict(
            get_text=get_text, 
            countries=['Russia', 'USA', 'UK', 'Germany', 'France', 'Japan', 'Canada', 'Australia', 'Italy', 'Spain', 'Brazil', 'Mexico', 'South Korea', 'India', 'China', 'Netherlands', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Ukraine', 'Turkey', 'Saudi Arabia', 'United Arab Emirates', 'South Africa'],
            COUNTRIES_CITIES=countries_cities,
            SITE_NAME=SITE_NAME,
            is_premium_user=is_premium_user
        )

@app.route('/get_cities/<country>')
def get_cities(country):
    lang = session.get('language', 'en')
    
    # Define countries and their cities
    countries_cities = {
        'Russia': ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg', 'Kazan', 'Nizhny Novgorod', 'Chelyabinsk', 'Samara', 'Omsk', 'Rostov-on-Don'],
        'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'],
        'UK': ['London', 'Birmingham', 'Manchester', 'Glasgow', 'Liverpool', 'Leeds', 'Sheffield', 'Bristol', 'Edinburgh', 'Cardiff'],
        'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne', 'Frankfurt', 'Stuttgart', 'Duesseldorf', 'Leipzig', 'Dortmund', 'Essen'],
        'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille'],
        'Japan': ['Tokyo', 'Osaka', 'Yokohama', 'Nagoya', 'Sapporo', 'Fukuoka', 'Kobe', 'Kyoto', 'Saitama', 'Hiroshima'],
        'Canada': ['Toronto', 'Montreal', 'Vancouver', 'Calgary', 'Edmonton', 'Ottawa', 'Winnipeg', 'Quebec City', 'Hamilton', 'Kitchener'],
        'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Gold Coast', 'Newcastle', 'Wollongong', 'Logan City', 'Geelong'],
        'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Palermo', 'Genoa', 'Bologna', 'Florence', 'Bari', 'Catania'],
        'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Zaragoza', 'Malaga', 'Murcia', 'Palma', 'Valladolid', 'Vigo'],
        'Brazil': ['Sao Paulo', 'Rio de Janeiro', 'Brasilia', 'Salvador', 'Fortaleza', 'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Porto Alegre'],
        'Mexico': ['Mexico City', 'Ecatepec', 'Guadalajara', 'Puebla', 'Tijuana', 'Leon', 'Juarez', 'Zapopan', 'Monterrey', 'Nezahualcoyotl'],
        'South Korea': ['Seoul', 'Busan', 'Incheon', 'Daegu', 'Daejeon', 'Gwangju', 'Suwon', 'Ulsan', 'Bucheon', 'Goyang'],
        'India': ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow'],
        'China': ['Shanghai', 'Beijing', 'Chongqing', 'Tianjin', 'Guangzhou', 'Shenzhen', 'Chengdu', 'Nanjing', 'Wuhan', 'Hangzhou'],
        'Netherlands': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven', 'Tilburg', 'Groningen', 'Almere', 'Breda', 'Nijmegen'],
        'Sweden': ['Stockholm', 'Gothenburg', 'Malmo', 'Uppsala', 'Vasteras', 'Orebro', 'Linkoping', 'Helsingborg', 'Jonkoping', 'Norrkoping'],
        'Norway': ['Oslo', 'Bergen', 'Trondheim', 'Stavanger', 'Drammen', 'Fredrikstad', 'Kristiansand', 'Tromso', 'Sandnes', 'Sarpsborg'],
        'Denmark': ['Copenhagen', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg', 'Randers', 'Kolding', 'Horsens', 'Silkeborg', 'Vejle'],
        'Finland': ['Helsinki', 'Espoo', 'Tampere', 'Vantaa', 'Oulu', 'Turku', 'Jyvaskyla', 'Lahti', 'Kuopio', 'Pori'],
        'Poland': ['Warsaw', 'Krakow', 'Lodz', 'Wroclaw', 'Poznan', 'Gdansk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Katowice'],
        'Ukraine': ['Kyiv', 'Kharkiv', 'Odessa', 'Dnipro', 'Donetsk', 'Zaporizhzhia', 'Lviv', 'Kryvyi Rih', 'Mykolaiv', 'Mariupol'],
        'Turkey': ['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Adana', 'Gaziantep', 'Konya', 'Antalya', 'Diyarbakir', 'Mersin'],
        'Saudi Arabia': ['Riyadh', 'Jeddah', 'Mecca', 'Medina', 'Dammam', 'Taif', 'Tabuk', 'Buraidah', 'Al Hofuf', 'Khamis Mushait'],
        'United Arab Emirates': ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Fujairah', 'Ras al Khaimah', 'Khor Fakkan', 'Al Ain', 'Umm al Quwain', 'Dibba Al-Fujairah'],
        'South Africa': ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Port Elizabeth', 'Bloemfontein', 'East London', 'Pietermaritzburg', 'Polokwane', 'Nelspruit']
    }
    
    # Translations for countries
    country_translations = {
        'Russia': 'Россия',
        'USA': 'США',
        'UK': 'Великобритания',
        'Germany': 'Германия',
        'France': 'Франция',
        'Japan': 'Япония',
        'Canada': 'Канада',
        'Australia': 'Австралия',
        'Italy': 'Италия',
        'Spain': 'Испания',
        'Brazil': 'Бразилия',
        'Mexico': 'Мексика',
        'South Korea': 'Южная Корея',
        'India': 'Индия',
        'China': 'Китай',
        'Netherlands': 'Нидерланды',
        'Sweden': 'Швеция',
        'Norway': 'Норвегия',
        'Denmark': 'Дания',
        'Finland': 'Финляндия',
        'Poland': 'Польша',
        'Ukraine': 'Украина',
        'Turkey': 'Турция',
        'Saudi Arabia': 'Саудовская Аравия',
        'United Arab Emirates': 'Объединенные Арабские Эмираты',
        'South Africa': 'Южная Африка'
    }
    
    # Reverse the translation dictionary for lookup
    reverse_country_translations = {v: k for k, v in country_translations.items()}
    
    # Translations for cities
    city_translations = {
        # Russia
        'Moscow': 'Москва',
        'Saint Petersburg': 'Санкт-Петербург',
        'Novosibirsk': 'Новосибирск',
        'Yekaterinburg': 'Екатеринбург',
        'Kazan': 'Казань',
        'Nizhny Novgorod': 'Нижний Новгород',
        'Chelyabinsk': 'Челябинск',
        'Samara': 'Самара',
        'Omsk': 'Омск',
        'Rostov-on-Don': 'Ростов-на-Дону',
        # USA
        'New York': 'Нью-Йорк',
        'Los Angeles': 'Лос-Анджелес',
        'Chicago': 'Чикаго',
        'Houston': 'Хьюстон',
        'Phoenix': 'Феникс',
        'Philadelphia': 'Филадельфия',
        'San Antonio': 'Сан-Антонио',
        'San Diego': 'Сан-Диего',
        'Dallas': 'Даллас',
        'San Jose': 'Сан-Хосе',
        # UK
        'London': 'Лондон',
        'Birmingham': 'Бирмингем',
        'Manchester': 'Манчестер',
        'Glasgow': 'Глазго',
        'Liverpool': 'Ливерпуль',
        'Leeds': 'Лидс',
        'Sheffield': 'Шеффилд',
        'Bristol': 'Бристоль',
        'Edinburgh': 'Эдинбург',
        'Cardiff': 'Кардифф',
        # Germany
        'Berlin': 'Берлин',
        'Hamburg': 'Гамбург',
        'Munich': 'Мюнхен',
        'Cologne': 'Кёльн',
        'Frankfurt': 'Франкфурт-на-Майне',
        'Stuttgart': 'Штутгарт',
        'Duesseldorf': 'Дюссельдорф',
        'Leipzig': 'Лейпциг',
        'Dortmund': 'Дортмунд',
        'Essen': 'Эссен',
        # France
        'Paris': 'Париж',
        'Marseille': 'Марсель',
        'Lyon': 'Лион',
        'Toulouse': 'Тулуза',
        'Nice': 'Ницца',
        'Nantes': 'Нант',
        'Strasbourg': 'Страсбург',
        'Montpellier': 'Монпелье',
        'Bordeaux': 'Бордо',
        'Lille': 'Лилль',
        # Japan
        'Tokyo': 'Токио',
        'Osaka': 'Осака',
        'Yokohama': 'Йокогама',
        'Nagoya': 'Нагоя',
        'Sapporo': 'Саппоро',
        'Fukuoka': 'Фукуока',
        'Kobe': 'Кобе',
        'Kyoto': 'Киото',
        'Saitama': 'Сайтама',
        'Hiroshima': 'Хиросима',
        # Canada
        'Toronto': 'Торонто',
        'Montreal': 'Монреаль',
        'Vancouver': 'Ванкувер',
        'Calgary': 'Калгари',
        'Edmonton': 'Эдмонтон',
        'Ottawa': 'Оттава',
        'Winnipeg': 'Виннипег',
        'Quebec City': 'Квебек',
        'Hamilton': 'Хамильтон',
        'Kitchener': 'Китченер',
        # Australia
        'Sydney': 'Сидней',
        'Melbourne': 'Мельбурн',
        'Brisbane': 'Брисбен',
        'Perth': 'Перт',
        'Adelaide': 'Аделаида',
        'Gold Coast': 'Золотой берег',
        'Newcastle': 'Ньюкасл',
        'Wollongong': 'Воллонгонг',
        'Logan City': 'Логан',
        'Geelong': 'Джилонг',
        # Italy
        'Rome': 'Рим',
        'Milan': 'Милан',
        'Naples': 'Неаполь',
        'Turin': 'Турин',
        'Palermo': 'Палермо',
        'Genoa': 'Генуя',
        'Bologna': 'Болонья',
        'Florence': 'Флоренция',
        'Bari': 'Бари',
        'Catania': 'Катания',
        # Spain
        'Madrid': 'Мадрид',
        'Barcelona': 'Барселона',
        'Valencia': 'Валенсия',
        'Seville': 'Севилья',
        'Zaragoza': 'Сарагоса',
        'Malaga': 'Малага',
        'Murcia': 'Мурсия',
        'Palma': 'Пальма',
        'Valladolid': 'Вальядолид',
        'Vigo': 'Виго',
        # Brazil
        'Sao Paulo': 'Сан-Паулу',
        'Rio de Janeiro': 'Рио-де-Жанейро',
        'Brasilia': 'Бразилиа',
        'Salvador': 'Сальвадор',
        'Fortaleza': 'Форталеза',
        'Belo Horizonte': 'Белу-Оризонти',
        'Manaus': 'Манаус',
        'Curitiba': 'Куричитба',
        'Recife': 'Ресифи',
        'Porto Alegre': 'Порту-Алегри',
        # Mexico
        'Mexico City': 'Мехико',
        'Ecatepec': 'Экатегек',
        'Guadalajara': 'Гвадалахара',
        'Puebla': 'Пуэбла',
        'Tijuana': 'Тихуана',
        'Leon': 'Леон',
        'Juarez': 'Хуарес',
        'Zapopan': 'Сапопан',
        'Monterrey': 'Монтеррей',
        'Nezahualcoyotl': 'Нецахуалькойотль',
        # South Korea
        'Seoul': 'Сеул',
        'Busan': 'Пусан',
        'Incheon': 'Инчхон',
        'Daegu': 'Тэгу',
        'Daejeon': 'Тэджон',
        'Gwangju': 'Кванджу',
        'Suwon': 'Сувон',
        'Ulsan': 'Ульсан',
        'Bucheon': 'Пучхон',
        'Goyang': 'Коян',
        # India
        'Mumbai': 'Мумбаи',
        'Delhi': 'Дели',
        'Bangalore': 'Бангалор',
        'Hyderabad': 'Хайдарабад',
        'Chennai': 'Ченнаи',
        'Kolkata': 'Калькутта',
        'Pune': 'Пуна',
        'Ahmedabad': 'Ахмедабад',
        'Jaipur': 'Джайпур',
        'Lucknow': 'Лакноу',
        # China
        'Shanghai': 'Шанхай',
        'Beijing': 'Пекин',
        'Chongqing': 'Чунцин',
        'Tianjin': 'Тяньцзинь',
        'Guangzhou': 'Гуанчжоу',
        'Shenzhen': 'Шэньчжэнь',
        'Chengdu': 'Чэнду',
        'Nanjing': 'Нанкин',
        'Wuhan': 'Ухань',
        'Hangzhou': 'Ханчжоу',
        # Netherlands
        'Amsterdam': 'Амстердам',
        'Rotterdam': 'Роттердам',
        'The Hague': 'Гаага',
        'Utrecht': 'Утрехт',
        'Eindhoven': 'Эйндховен',
        'Tilburg': 'Тилбург',
        'Groningen': 'Гронинген',
        'Almere': 'Альмере',
        'Breda': 'Бреда',
        'Nijmegen': 'Неймеген',
        # Sweden
        'Stockholm': 'Стокгольм',
        'Gothenburg': 'Гётеборг',
        'Malmo': 'Мальмё',
        'Uppsala': 'Упсала',
        'Vasteras': 'Вестерос',
        'Orebro': 'Эребру',
        'Linkoping': 'Линчёпинг',
        'Helsingborg': 'Хельсингборг',
        'Jonkoping': 'Йёнчёпинг',
        'Norrkoping': 'Норрчёпинг',
        # Norway
        'Oslo': 'Осло',
        'Bergen': 'Берген',
        'Trondheim': 'Тронхейм',
        'Stavanger': 'Ставангер',
        'Drammen': 'Драммен',
        'Fredrikstad': 'Фредрикстад',
        'Kristiansand': 'Кристиансанд',
        'Tromso': 'Тромсё',
        'Sandnes': 'Санднес',
        'Sarpsborg': 'Сарпсборг',
        # Denmark
        'Copenhagen': 'Копенгаген',
        'Aarhus': 'Орхус',
        'Odense': 'Оденсе',
        'Aalborg': 'Ольборг',
        'Esbjerg': 'Эсбьерг',
        'Randers': 'Рандерс',
        'Kolding': 'Колдинг',
        'Horsens': 'Хорсенс',
        'Silkeborg': 'Силькеборг',
        'Vejle': 'Вейле',
        # Finland
        'Helsinki': 'Хельсинки',
        'Espoo': 'Эспоо',
        'Tampere': 'Тампере',
        'Vantaa': 'Вантаа',
        'Oulu': 'Оулу',
        'Turku': 'Турку',
        'Jyvaskyla': 'Ювяскюля',
        'Lahti': 'Лахти',
        'Kuopio': 'Куопио',
        'Pori': 'Пори',
        # Poland
        'Warsaw': 'Варшава',
        'Krakow': 'Краков',
        'Lodz': 'Лодзь',
        'Wroclaw': 'Вроцлав',
        'Poznan': 'Познань',
        'Gdansk': 'Гданьск',
        'Szczecin': 'Щецин',
        'Bydgoszcz': 'Быдгощ',
        'Lublin': 'Люблин',
        'Katowice': 'Катовице',
        # Ukraine
        'Kyiv': 'Киев',
        'Kharkiv': 'Харьков',
        'Odessa': 'Одесса',
        'Dnipro': 'Днепр',
        'Donetsk': 'Донецк',
        'Zaporizhzhia': 'Запорожье',
        'Lviv': 'Львов',
        'Kryvyi Rih': 'Кривой Рог',
        'Mykolaiv': 'Николаев',
        'Mariupol': 'Мариуполь',
        # Turkey
        'Istanbul': 'Стамбул',
        'Ankara': 'Анкара',
        'Izmir': 'Измир',
        'Bursa': 'Бурса',
        'Adana': 'Адана',
        'Gaziantep': 'Газиантеп',
        'Konya': 'Конья',
        'Antalya': 'Анталья',
        'Diyarbakir': 'Диярбакыр',
        'Mersin': 'Мерсин',
        # Saudi Arabia
        'Riyadh': 'Эр-Рияд',
        'Jeddah': 'Джидда',
        'Mecca': 'Мекка',
        'Medina': 'Медина',
        'Dammam': 'Даммам',
        'Taif': 'Тайф',
        'Tabuk': 'Табук',
        'Buraidah': 'Бураидах',
        'Al Hofuf': 'Хафуф',
        'Khamis Mushait': 'Хамис-Мушайт',
        # United Arab Emirates
        'Dubai': 'Дубай',
        'Abu Dhabi': 'Абу-Даби',
        'Sharjah': 'Шарджа',
        'Ajman': 'Аджман',
        'Fujairah': 'Фуджейра',
        'Ras al Khaimah': 'Рас-эль-Хайма',
        'Khor Fakkan': 'Хор-Факкан',
        'Al Ain': 'Эль-Айн',
        'Umm al Quwain': 'Умм-эль-Кувейн',
        'Dibba Al-Fujairah': 'Дибба-Аль-Фуджейра',
        # South Africa
        'Johannesburg': 'Йоханнесбург',
        'Cape Town': 'Кейптаун',
        'Durban': 'Дурбан',
        'Pretoria': 'Претория',
        'Port Elizabeth': 'Порт-Элизабет',
        'Bloemfontein': 'Блумфонтейн',
        'East London': 'Ист-Лондон',
        'Pietermaritzburg': 'Пьетермарицбург',
        'Polokwane': 'Полокване',
        'Nelspruit': 'Нелспруйт'
    }
    
    # Check if the country parameter is in Russian and translate it back to English
    original_country = reverse_country_translations.get(country, country) if lang == 'ru' else country
    
    cities = countries_cities.get(original_country, [])
    
    # If Russian language is selected, translate cities to Russian
    if lang == 'ru':
        translated_cities = [city_translations.get(city, city) for city in cities]
        return jsonify(translated_cities)
    else:
        return jsonify(cities)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['language'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/chat_list')
@login_required
def chat_list():
    # Заглушка для списка чатов
    # В реальной реализации здесь будет логика получения списка чатов
    # Для шаблона chat.html нам нужно передать recipient, но для списка чатов нужен другой шаблон
    # Создадим пользовательский шаблон для списка чатов
    return render_template('chat_list.html')

@app.route('/premium')
@login_required
def premium():
    # Заглушка для страницы премиум-подписки
    # В реальной реализации здесь будет логика оформления премиум-подписки
    return render_template('premium.html')

@app.route('/faq')
def faq():
    # Заглушка для страницы FAQ
    # В реальной реализации здесь будет логика отображения часто задаваемых вопросов
    return render_template('faq.html')

@app.route('/about')
def about():
    # Заглушка для страницы "О нас"
    # В реальной реализации здесь будет логика отображения информации о проекте
    return render_template('about.html')

@app.route('/terms')
def terms():
    # Страница условий использования
    return render_template('terms.html')

@app.route('/refund-policy')
def refund_policy():
    # Страница политики возврата
    return render_template('refund_policy.html')

@app.route('/delivery')
def delivery():
    # Страница условий доставки/услуг
    return render_template('delivery.html')

@app.route('/contacts')
def contacts():
    # Страница контактов
    return render_template('contacts.html')

@app.route('/privacy-policy')
def privacy_policy():
    # Страница политики конфиденциальности (добавлена для полноты)
    return render_template('privacy_policy.html')

@app.route('/support_chat', methods=['GET', 'POST'])
@login_required
def support_chat():
    from datetime import datetime
    
    # Получаем или создаем тикет поддержки для текущего пользователя
    ticket = SupportTicket.query.filter_by(user_id=current_user.id, status='open').first()
    if not ticket:
        # Создаем новый тикет, если нет открытого
        ticket = SupportTicket(
            user_id=current_user.id,
            subject='Support Request',
            status='open'
        )
        db.session.add(ticket)
        db.session.commit()
    
    # Получаем сообщения для этого тикета
    messages = SupportMessage.query.filter_by(ticket_id=ticket.id).order_by(SupportMessage.timestamp).all()
    
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            # Создаем новое сообщение в тикете
            message = SupportMessage(
                ticket_id=ticket.id,
                sender_id=current_user.id,
                content=content,
                is_admin=False  # Пользователь отправляет сообщение
            )
            db.session.add(message)
            db.session.commit()
            
            # Отправляем JSON-ответ для AJAX-запроса
            return jsonify({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat(),
                    'is_admin': False
                }
            })
    
    current_time = datetime.now()
    return render_template('support_chat.html', current_time=current_time, ticket=ticket, messages=messages)

@app.route('/api/support_messages/<int:ticket_id>')
@login_required
def api_support_messages(ticket_id):
    """API endpoint для получения сообщений тикета"""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Проверяем, что пользователь либо является владельцем тикета, либо администратор
    if current_user.id != ticket.user_id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    messages = SupportMessage.query.filter_by(ticket_id=ticket_id).order_by(SupportMessage.timestamp).all()
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'is_admin': message.is_admin,
            'sender_name': message.sender.username
        })
    
    return jsonify(messages_data)

@app.route('/api/send_support_message', methods=['POST'])
@login_required
def api_send_support_message():
    """API endpoint для отправки сообщений в тикет поддержки"""
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    content = data.get('content')
    
    if not ticket_id or not content:
        return jsonify({'status': 'error', 'error': 'Missing ticket_id or content'}), 400
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Проверяем, что пользователь либо является владельцем тикета, либо администратор
    if current_user.id != ticket.user_id and not current_user.is_admin:
        return jsonify({'status': 'error', 'error': 'Access denied'}), 403
    
    # Создаем новое сообщение
    message = SupportMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        content=content,
        is_admin=current_user.is_admin
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'is_admin': message.is_admin,
            'sender_name': current_user.username
        }
    })

@app.route('/admin')
@login_required
def admin():
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    # Получаем всех пользователей для отображения в админ-панели
    users = UserModel.query.all()
    return render_template('admin.html', users=users)


@app.route('/admin/chat_history/<int:user1_id>/<int:user2_id>')
@login_required
def admin_chat_history(user1_id, user2_id):
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    # Получаем пользователей для отображения их имен
    user1 = UserModel.query.get_or_404(user1_id)
    user2 = UserModel.query.get_or_404(user2_id)
    
    # Получаем переписку между двумя пользователями (в обе стороны)
    messages = Message.query.filter(
        ((Message.sender_id == user1_id) & (Message.recipient_id == user2_id)) |
        ((Message.sender_id == user2_id) & (Message.recipient_id == user1_id))
    ).order_by(Message.timestamp).all()
    
    return render_template('admin_chat_history.html', 
                          user1=user1, user2=user2, messages=messages)


@app.route('/admin/chat_history')
@login_required
def admin_chat_history_list():
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    # Получаем все уникальные пары пользователей, которые переписывались
    chat_partners = db.session.query(
        Message.sender_id, 
        Message.recipient_id
    ).distinct().filter(
        (Message.sender_id != Message.recipient_id)
    ).all()
    
    # Преобразуем в список уникальных пар
    unique_pairs = set()
    for sender_id, recipient_id in chat_partners:
        # Сортируем ID, чтобы пара (A, B) и (B, A) считалась одинаковой
        pair = tuple(sorted((sender_id, recipient_id)))
        unique_pairs.add(pair)
    
    # Преобразуем ID в объекты пользователей
    chat_data = []
    for user1_id, user2_id in unique_pairs:
        user1 = UserModel.query.get(user1_id)
        user2 = UserModel.query.get(user2_id)
        if user1 and user2:
            # Получаем последнее сообщение для отображения в списке
            last_message = Message.query.filter(
                ((Message.sender_id == user1_id) & (Message.recipient_id == user2_id)) |
                ((Message.sender_id == user2_id) & (Message.recipient_id == user1_id))
            ).order_by(Message.timestamp.desc()).first()
            
            chat_data.append({
                'user1': user1,
                'user2': user2,
                'last_message': last_message,
                'message_count': Message.query.filter(
                    ((Message.sender_id == user1_id) & (Message.recipient_id == user2_id)) |
                    ((Message.sender_id == user2_id) & (Message.recipient_id == user1_id))
                ).count()
            })
    
    return render_template('admin_chat_list.html', chat_data=chat_data)

@app.route('/admin_support_chat')
@login_required
def admin_support_chat():
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    # Получаем ID тикета из параметров запроса, если он есть
    ticket_id = request.args.get('ticket_id', type=int)
    
    # Получаем все открытые тикеты (и возможно недавно закрытые для истории)
    open_tickets = SupportTicket.query.filter(
        (SupportTicket.status == 'open') | (SupportTicket.status == 'closed')
    ).order_by(SupportTicket.updated_at.desc()).all()
    
    # Загружаем сообщения для каждого тикета
    for ticket in open_tickets:
        ticket.messages = SupportMessage.query.filter_by(ticket_id=ticket.id).order_by(SupportMessage.timestamp).all()
    
    selected_ticket = None
    if ticket_id:
        selected_ticket = SupportTicket.query.get(ticket_id)
        if selected_ticket:
            # Загружаем сообщения для выбранного тикета
            selected_ticket.messages = SupportMessage.query.filter_by(ticket_id=ticket_id).order_by(SupportMessage.timestamp).all()
    
    return render_template('admin_support_chat.html', 
                          open_tickets=open_tickets, 
                          selected_ticket=selected_ticket)

@app.route('/admin/unblock_user/<int:user_id>', methods=['POST'])
@login_required
def admin_unblock_user(user_id):
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    user.is_blocked = False
    db.session.commit()
    flash(f'Пользователь {user.username} разблокирован.')
    return redirect(url_for('admin'))

@app.route('/admin/block_user/<int:user_id>', methods=['POST'])
@login_required
def admin_block_user(user_id):
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    user.is_blocked = True
    db.session.commit()
    flash(f'Пользователь {user.username} заблокирован.')
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.username} удален.')
    return redirect(url_for('admin'))

@app.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@login_required
def admin_make_admin(user_id):
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'Пользователь {user.username} теперь администратор.')
    return redirect(url_for('admin'))

@app.route('/admin/close_support_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def admin_close_support_ticket(ticket_id):
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'error': 'Access denied'}), 403
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = 'closed'
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/buy_coins')
@login_required
def buy_coins():
    # Заглушка для покупки монет
    return render_template('buy_coins.html')

@app.route('/chat/<int:recipient_id>')
@login_required
def chat(recipient_id):
    # Заглушка для чата с конкретным пользователем
    recipient = UserModel.query.get_or_404(recipient_id)
    return render_template('chat.html', recipient=recipient)

@app.route('/gift_shop')
@login_required
def gift_shop():
    # Заглушка для магазина подарков
    return render_template('gift_shop.html')

@app.route('/')
def home():
    return render_template('index.html')

# Validation functions
def validate_email(email):
    """Проверяет, является ли email адрес действительным"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_disposable_email(email):
    """Проверяет, является ли email одноразовым (disposable)"""
    disposable_domains = {
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com', 'sharklasers.com',
        'yopmail.com', 'mailinator.com', 'temp-mail.org', 'throwawaymail.com',
        'dispostable.com', 'getairmail.com', 'grr.la', 'guerrillamailblock.com',
        'pokemail.net', 'spam4.me', 'tempinbox.com', 'trashmail.com'
    }
    domain = email.split('@')[1].lower()
    return domain in disposable_domains

def validate_email_address(email):
    """Полная проверка email адреса"""
    if not validate_email(email):
        return False, "Неверный формат email адреса"
    
    if is_disposable_email(email):
        return False, "Использование временных email адресов запрещено"
    
    return True, "Email адрес действителен"

# Registration function with improved validation and CAPTCHA
import signal
from functools import wraps

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def with_timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Устанавливаем таймаут только в Unix-подобных системах
            if hasattr(signal, 'alarm'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Для Windows используем таймаут через threading
                import threading
                result = [None]
                exception = [None]

                def target():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(seconds)
                
                if thread.is_alive():
                    raise TimeoutError("Operation timed out")
                
                if exception[0]:
                    raise exception[0]
                
                return result[0]
        return wrapper
    return decorator

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Проверка CAPTCHA была отключена для локального запуска
        # recaptcha_response = request.form.get('g-recaptcha-response')
        # if not recaptcha_response:
        #     flash('Пожалуйста, подтвердите, что вы не робот.')
        #     return render_template('register.html')
        
        # Валидация email
        is_valid, message = validate_email_address(email)
        if not is_valid:
            flash(message)
            return render_template('register.html')
        
        try:
            # Check if username already exists
            existing_user = UserModel.query.filter_by(username=username).first()
            if existing_user:
                flash(get_text('username_exists'))
                return render_template('register.html')
            
            # Check if email already exists
            existing_email = UserModel.query.filter_by(email=email).first()
            if existing_email:
                flash(get_text('email_exists') or 'A user with this email already exists')
                return render_template('register.html')
            
            # Clean up expired confirmation codes to prevent memory buildup
            cleanup_expired_confirmation_codes()
            
            # Generate confirmation code
            confirmation_code = generate_confirmation_code()
            
            # Store the confirmation code in temporary storage - user will be created after verification
            confirmation_codes[email] = {
                'code': confirmation_code,
                'expires': datetime.utcnow() + timedelta(hours=1),  # Код действителен 1 час
                'username': username,
                'email': email,
                'password': password,  # Will be hashed when creating the user
                'is_first_user': UserModel.query.count() == 0  # Check if this will be the first user
            }
            
            # Вместо отправки email, сразу показываем код пользователю (для избежания таймаутов)
            flash('Пожалуйста, используйте код подтверждения, отображенный ниже.')
            return redirect(url_for('verify_email_page', email=email, code=confirmation_code))
                
        except Exception as e:
            error_str = str(e)
            if 'connection' in error_str.lower() or 'timeout' in error_str.lower() or isinstance(e, TimeoutError):
                # Обработка ошибок подключения к базе данных и таймаутов
                flash('Сервис временно недоступен. Пожалуйста, попробуйте зарегистрироваться чуть позже.')
                print(f"Database connection error or timeout during registration: {e}")
                # Dispose connection to ensure fresh connection on next attempt
                try:
                    db.engine.dispose()
                except Exception as dispose_error:
                    print(f"Error disposing database connection in registration: {dispose_error}")
            else:
                flash('An error occurred during registration. Please try again.')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/verify_email')
def verify_email_page():
    email = request.args.get('email')
    code = request.args.get('code')  # Код может быть передан как параметр для отладки
    if not email:
        flash('Неверный запрос. Пожалуйста, зарегистрируйтесь снова.')
        return redirect(url_for('register'))
    
    return render_template('verify_email.html', email=email, code=code)

@app.route('/verify_email', methods=['POST'])
def verify_email():
    email = request.form.get('email')
    code = request.form.get('code')
    
    if not email or not code:
        flash('Все поля обязательны для заполнения.')
        return redirect(url_for('verify_email_page', email=email))
    
    # Clean up expired confirmation codes to prevent memory buildup
    cleanup_expired_confirmation_codes()
    
    # Check if code exists in temporary storage and is valid
    if email in confirmation_codes:
        stored_data = confirmation_codes[email]
        stored_code = stored_data['code']
        expires = stored_data['expires']
        
        if code == stored_code and expires > datetime.utcnow():
            # Code is valid and not expired
            # Check if user with this email already exists (to prevent multiple verifications)
            existing_user = UserModel.query.filter_by(email=email).first()
            if existing_user:
                flash('Аккаунт с этой электронной почтой уже существует.')
                # Delete the code from temporary storage
                del confirmation_codes[email]
                return redirect(url_for('login'))
            
            # Create user after successful verification
            user = UserModel(
                username=stored_data['username'],
                email=email
            )
            user.set_password(stored_data['password'])
            
            # Check if this is the first user (make them admin)
            if stored_data.get('is_first_user', False) or UserModel.query.count() == 0:
                user.is_admin = True
            
            db.session.add(user)
            db.session.commit()
            
            # Delete the code from temporary storage
            del confirmation_codes[email]
            
            # Login the user and redirect (with remember=True to persist session)
            login_user(user, remember=True)
            flash(get_text('registration_success'))
            return redirect(url_for('edit_profile'))
    
    flash('Неверный или просроченный код подтверждения.')
    return redirect(url_for('verify_email_page', email=email))

@app.route('/resend_confirmation')
def resend_confirmation():
    email = request.args.get('email')
    if not email:
        flash('Неверный запрос.')
        return redirect(url_for('register'))
    
    # Clean up expired confirmation codes to prevent memory buildup
    cleanup_expired_confirmation_codes()
    
    # Check if confirmation code exists for this email
    if email not in confirmation_codes:
        flash('Запрос на подтверждение не найден. Пожалуйста, зарегистрируйтесь снова.')
        return redirect(url_for('register'))
    
    # Generate new confirmation code
    new_code = generate_confirmation_code()
    
    # Update temporary storage with new code, keeping other data
    stored_data = confirmation_codes[email]
    confirmation_codes[email] = {
        'code': new_code,
        'expires': datetime.utcnow() + timedelta(hours=1),
        'username': stored_data['username'],
        'email': stored_data['email'],
        'password': stored_data['password'],
        'is_first_user': stored_data['is_first_user']
    }
    
    # Вместо отправки email, просто показываем новый код
    flash('Новый код подтверждения сгенерирован.')
    return redirect(url_for('verify_email_page', email=email, code=new_code))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            # Find user
            user = UserModel.query.filter_by(username=username).first()
            
            # Debug logging
            if user:
                print(f"User found: {user.username}")
                print(f"Password hash: {user.password_hash}")
                print(f"Trying to authenticate user with password: {'*' * len(password)}")
                
                # Check if password matches
                password_match = user.check_password(password)
                print(f"Password match result: {password_match}")
                
                if password_match:
                    # Check if user is blocked
                    if user.is_blocked:
                        flash('Your account has been blocked')
                        return redirect(url_for('login'))
                    
                    # Log in the user with permanent session
                    login_user(user, remember=True)
                    return redirect(url_for('profile'))
                else:
                    print(f"Password check failed for user: {username}")
            else:
                print(f"User not found: {username}")
            
            flash(get_text('invalid_credentials'))
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Exception during login: {e}")
            error_str = str(e)
            if 'connection' in error_str.lower() or 'timeout' in error_str.lower() or isinstance(e, TimeoutError):
                # Обработка ошибок подключения к базе данных и таймаутов
                flash('Сервис временно недоступен. Пожалуйста, попробуйте войти чуть позже.')
                print(f"Database connection error or timeout during login: {e}")
                # Dispose connection to ensure fresh connection on next attempt
                try:
                    db.engine.dispose()
                except Exception as dispose_error:
                    print(f"Error disposing database connection in login: {dispose_error}")
                return render_template('login.html')
            else:
                flash(get_text('invalid_credentials'))
                return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    return show_profile(current_user.id)

@app.route('/profile/<int:user_id>')
def show_profile(user_id):
    # Get the specified user
    user = UserModel.query.get_or_404(user_id)
    
    # Get user's fetishes and interests in optimized way
    user_fetishes = [f.name for f in Fetish.query.filter(Fetish.user_id == user.id).limit(50).all()]  # Limit to prevent memory issues
    user_interests = [i.name for i in Interest.query.filter(Interest.user_id == user.id).limit(50).all()]  # Limit to prevent memory issues
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'photo': user.photo,
        'country': user.country,
        'city': user.city,
        'bio': user.bio,
        'fetishes': user_fetishes,
        'interests': user_interests,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'is_premium': is_premium_user(user)
    }
    
    is_complete = bool(user.country and user.city)
    return render_template('profile.html', user_data=user_data, is_complete=is_complete)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Проверяем, что пользователь аутентифицирован
    if not current_user or not current_user.is_authenticated:
        flash('You need to be logged in to edit your profile.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        country = request.form.get('country', '').strip()
        city = request.form.get('city', '').strip()
        bio = request.form.get('bio', '').strip()
        
        # Validate required fields for new users (empty profile)
        is_new_user = not current_user.country and not current_user.city  # If both are empty, assume new user
        if is_new_user:
            if not country:
                flash('Country is required')
                # Create minimal user_data for error cases
                user_data = {
                    'username': current_user.username,
                    'email': current_user.email,
                    'photo': current_user.photo,
                    'country': current_user.country,
                    'city': current_user.city,
                    'bio': current_user.bio,
                    'fetishes': [],
                    'interests': [],
                    'created_at': current_user.created_at.isoformat(),
                    'is_premium': is_premium_user(current_user),
                    'user_photos': []
                }
                
                # Get user's additional photos
                user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
                user_data['user_photos'] = user_photos
                
                return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
            if not city:
                flash('City is required')
                # Create minimal user_data for error cases
                user_data = {
                    'username': current_user.username,
                    'email': current_user.email,
                    'photo': current_user.photo,
                    'country': current_user.country,
                    'city': current_user.city,
                    'bio': current_user.bio,
                    'fetishes': [],
                    'interests': [],
                    'created_at': current_user.created_at.isoformat(),
                    'is_premium': is_premium_user(current_user),
                    'user_photos': []
                }
                
                # Get user's additional photos
                user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
                user_data['user_photos'] = user_photos
                
                return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
            if not bio:
                flash('Biography is required')
                # Create minimal user_data for error cases
                user_data = {
                    'username': current_user.username,
                    'email': current_user.email,
                    'photo': current_user.photo,
                    'country': current_user.country,
                    'city': current_user.city,
                    'bio': current_user.bio,
                    'fetishes': [],
                    'interests': [],
                    'created_at': current_user.created_at.isoformat(),
                    'is_premium': is_premium_user(current_user),
                    'user_photos': []
                }
                
                # Get user's additional photos
                user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
                user_data['user_photos'] = user_photos
                
                return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
        
        # Update user profile information
        current_user.country = country
        current_user.city = city
        current_user.bio = bio
        
        # Update location matching settings
        current_user.match_by_city = bool(request.form.get('match_by_city'))
        current_user.match_by_country = bool(request.form.get('match_by_country'))
        
        # Handle photo upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename != '':
                # Validate the image for face detection if the module is available
                if FACE_DETECTION_AVAILABLE:
                    # Validate the image for human faces
                    validation_result = validate_avatar_image(photo)
                    if not validation_result['valid']:
                        flash(f'Ошибка при проверке аватара: {validation_result["message"]}')
                        # Create minimal user_data for error cases
                        user_data = {
                            'username': current_user.username,
                            'email': current_user.email,
                            'photo': current_user.photo,
                            'country': current_user.country,
                            'city': current_user.city,
                            'bio': current_user.bio,
                            'fetishes': [],
                            'interests': [],
                            'created_at': current_user.created_at.isoformat(),
                            'is_premium': is_premium_user(current_user),
                            'user_photos': []
                        }
                        
                        # Get user's additional photos
                        user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
                        user_data['user_photos'] = user_photos
                        
                        return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
                
                # Create unique filename
                ext = photo.filename.split('.')[-1]
                filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(filepath)
                current_user.photo = filename
        
        # If user is new and doesn't have a photo, require photo upload
        if is_new_user and not current_user.photo:
            flash('Profile photo is required for new users')
            # Create minimal user_data for error cases
            user_data = {
                'username': current_user.username,
                'email': current_user.email,
                'photo': current_user.photo,
                'country': current_user.country,
                'city': current_user.city,
                'bio': current_user.bio,
                'fetishes': [],
                'interests': [],
                'created_at': current_user.created_at.isoformat(),
                'is_premium': is_premium_user(current_user),
                'user_photos': []
            }
            
            # Get user's additional photos
            user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
            user_data['user_photos'] = user_photos
            
            return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
        
        # Update user's fetishes
        Fetish.query.filter_by(user_id=current_user.id).delete()  # Remove old fetishes
        selected_fetishes = request.form.getlist('fetishes')  # Get all selected fetishes
        for fetish_name in selected_fetishes:
            fetish = Fetish(user_id=current_user.id, name=fetish_name)
            db.session.add(fetish)
        
        # Add custom fetish if provided
        custom_fetish = request.form.get('custom_fetish')
        if custom_fetish:
            # Add to current user's profile
            fetish = Fetish(user_id=current_user.id, name=custom_fetish)
            db.session.add(fetish)
        
        # Update user's interests
        Interest.query.filter_by(user_id=current_user.id).delete()  # Remove old interests
        selected_interests = request.form.getlist('interests')  # Get all selected interests
        for interest_name in selected_interests:
            interest = Interest(user_id=current_user.id, name=interest_name)
            db.session.add(interest)
        
        # Add custom interest if provided
        custom_interest = request.form.get('custom_interest')
        if custom_interest:
            # Add to current user's profile
            interest = Interest(user_id=current_user.id, name=custom_interest)
            db.session.add(interest)
        
        # Handle additional photos upload
        if 'additional_photos' in request.files:
            photo_files = request.files.getlist('additional_photos')
            for photo_file in photo_files:
                if photo_file and photo_file.filename != '':
                    # Validate the image for face detection if the module is available
                    if FACE_DETECTION_AVAILABLE:
                        # Validate the image for human faces
                        validation_result = validate_avatar_image(photo_file)
                        if not validation_result['valid']:
                            flash(f'Ошибка при проверке дополнительной фотографии: {validation_result["message"]}')
                            # Create minimal user_data for error cases
                            user_data = {
                                'username': current_user.username,
                                'email': current_user.email,
                                'photo': current_user.photo,
                                'country': current_user.country,
                                'city': current_user.city,
                                'bio': current_user.bio,
                                'fetishes': [],
                                'interests': [],
                                'created_at': current_user.created_at.isoformat(),
                                'is_premium': is_premium_user(current_user),
                                'user_photos': []
                            }
                            
                            # Get user's additional photos
                            user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
                            user_data['user_photos'] = user_photos
                            
                            return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
                    
                    # Create unique filename
                    ext = photo_file.filename.split('.')[-1]
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo_file.save(filepath)
                    
                    # Create UserPhoto record
                    user_photo = UserPhoto(
                        user_id=current_user.id,
                        photo_path=filename
                    )
                    db.session.add(user_photo)
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    # Get user's fetishes and interests
    user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=current_user.id).all()]
    user_interests = [i.name for i in Interest.query.filter_by(user_id=current_user.id).all()]
    
    # Get all available fetishes and interests
    db_fetishes = [f.name for f in Fetish.query.distinct(Fetish.name)]
    db_interests = [i.name for i in Interest.query.distinct(Interest.name)]
    
    # Get current language
    current_language = session.get('language', 'en')
    
    # Predefined popular fetishes and interests with translations
    if current_language == 'ru':
        predefined_fetishes = [
            'Кожа', 'Латекс', 'Бондаж', 'Доминирование', 'Подчинение', 
            'Ролевые игры', 'Игра на возраст', 'Водные игры', 'Игра с болью', 'Экспозиционизм',
            'Фурри', 'Возрастной фетиш', 'Гигантизм', 'Игра с животными', 'Целомудрие', 
            'Принудительный оргазм', 'Игра с ощущениями', 'Игра с ударами', 'Оскорбление'
        ]
        
        predefined_interests = [
            'Пешие прогулки', 'Фотография', 'Кулинария', 'Путешествия', 'Чтение', 
            'Музыка', 'Фильмы', 'Игры', 'Искусство', 'Танцы',
            'Спорт', 'Йога', 'Медитация', 'Садоводство', 'Рыбалка',
            'Велоспорт', 'Плавание', 'Бег', 'Дайвинг', 'Технологии'
        ]
    else:  # English
        predefined_fetishes = [
            'Leather', 'Latex', 'Bondage', 'Dominance', 'Submission', 
            'Roleplay', 'Age Play', 'Water Sports', 'Pain Play', 'Exhibitionism',
            'Furry', 'Age Fetish', 'Giantess', 'Pet Play', 'Chastity', 
            'Forced Orgasm', 'Sensation Play', 'Impact Play', 'Humiliation'
        ]
        
        predefined_interests = [
            'Hiking', 'Photography', 'Cooking', 'Travel', 'Reading', 
            'Music', 'Movies', 'Gaming', 'Art', 'Dancing',
            'Sports', 'Yoga', 'Meditation', 'Gardening', 'Fishing',
            'Cycling', 'Swimming', 'Running', 'Diving', 'Technology'
        ]
    
    # Combine database values with predefined values
    all_fetishes = list(set(db_fetishes + predefined_fetishes))
    all_interests = list(set(db_interests + predefined_interests))
    
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'photo': current_user.photo,
        'country': current_user.country,
        'city': current_user.city,
        'bio': current_user.bio,
        'fetishes': user_fetishes,
        'interests': user_interests,
        'created_at': current_user.created_at.isoformat(),
        'is_premium': is_premium_user(current_user),
        'user_photos': []
    }
    
    # Get user's additional photos
    user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
    user_data['user_photos'] = user_photos
    
    return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)

@app.route('/swipe')
@login_required
def swipe():
    return render_template('swipe_fresh.html')

@app.route('/users')
@login_required
def users():
    # Get all users except current user
    db_users = UserModel.query.filter(UserModel.id != int(current_user.id)).all()
    
    # Optimize by getting all fetishes and interests at once, rather than N+1 queries
    all_fetishes = Fetish.query.all()
    all_interests = Interest.query.all()
    
    # Group fetishes and interests by user ID for efficient lookup
    fetishes_by_user = {}
    interests_by_user = {}
    
    for fetish in all_fetishes:
        if fetish.user_id not in fetishes_by_user:
            fetishes_by_user[fetish.user_id] = []
        fetishes_by_user[fetish.user_id].append(fetish.name)
    
    for interest in all_interests:
        if interest.user_id not in interests_by_user:
            interests_by_user[interest.user_id] = []
        interests_by_user[interest.user_id].append(interest.name)
    
    users_dict = {}
    for user in db_users:
        user_fetishes = fetishes_by_user.get(user.id, [])
        user_interests = interests_by_user.get(user.id, [])
        users_dict[user.id] = {
            'username': user.username,
            'email': user.email,
            'photo': user.photo,
            'country': user.country,
            'city': user.city,
            'bio': user.bio,
            'fetishes': user_fetishes,
            'interests': user_interests,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    
    return render_template('users.html', users=users_dict)

# API routes for notifications
@app.route('/api/notifications')
@login_required
def api_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'content': notification.content,
            'is_read': notification.is_read,
            'timestamp': notification.timestamp.isoformat(),
            'url': notification.url
        })
    
    return jsonify(notifications_data)


# API route for users data for swipe functionality
@app.route('/api/users')
@login_required
def api_users():
    """Return users data for swipe functionality - optimized for low memory usage"""
    try:
        # Get all users except current user with basic info only
        # Limit to 50 users to prevent memory issues
        db_users = UserModel.query.filter(
            UserModel.id != int(current_user.id)
        ).limit(50).all()
        
        # Create a lightweight representation of users data
        users_list = []
        for user in db_users:
            # Only include essential information for swipe cards
            user_data = {
                'username': user.username,
                'photo': user.photo,
                'city': user.city,
                'country': user.country,
                'bio': user.bio[:100] if user.bio else '',  # Limit bio length
            }
            
            # Add user to the list with their ID
            users_list.append([user.id, user_data])
        
        return jsonify(users_list)
    except Exception as e:
        print(f"Error in api_users: {e}")
        # Return empty list on error
        return jsonify([])

# Helper function to check if user is premium
def is_premium_user(user):
    """Check if user is premium and not expired"""
    if not user.is_premium:
        return False
    if user.premium_expires and user.premium_expires < datetime.utcnow():
        # Premium expired, update user status
        user.is_premium = False
        user.premium_expires = None
        db.session.commit()
        return False
    return True

# API routes for managing additional user photos
@app.route('/api/photo/<int:photo_id>/set_primary', methods=['POST'])
@login_required
def set_primary_photo(photo_id):
    """Set a user's additional photo as primary"""
    photo = UserPhoto.query.filter_by(id=photo_id, user_id=current_user.id).first()
    
    if not photo:
        return jsonify({'status': 'error', 'message': 'Photo not found'}), 404
    
    # First, set all photos to non-primary
    UserPhoto.query.filter_by(user_id=current_user.id).update({'is_primary': False})
    db.session.commit()
    
    # Then set selected photo as primary
    photo.is_primary = True
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Primary photo updated successfully'})


@app.route('/api/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Delete a user's additional photo"""
    photo = UserPhoto.query.filter_by(id=photo_id, user_id=current_user.id).first()
    
    if not photo:
        return jsonify({'status': 'error', 'message': 'Photo not found'}), 404
    
    # Delete the photo file
    import os
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_path)
    if os.path.exists(photo_path):
        os.remove(photo_path)
    
    # Remove optimized version if exists
    optimized_path = os.path.join(app.config['UPLOAD_FOLDER'], 'optimized', photo.photo_path)
    if os.path.exists(optimized_path):
        os.remove(optimized_path)
    
    # Delete from database
    db.session.delete(photo)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Photo deleted successfully'})


@app.route('/optimized_image/<filename>')
def optimized_image(filename):
    """Serve optimized images with WebP conversion when possible (without caching to save memory)"""
    import os
    from PIL import Image
    import io
    
    # Check if optimized version exists
    optimized_path = os.path.join(app.config['UPLOAD_FOLDER'], 'optimized', filename)
    
    if os.path.exists(optimized_path):
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'optimized'), filename)
    
    # Original image path
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(original_path):
        # Return a default image if file doesn't exist
        return send_from_directory('static', 'uploads/default.jpg')
    
    # Check if client accepts WebP
    accept_webp = 'image/webp' in request.headers.get('Accept', '')
    
    # Convert and optimize image
    try:
        with Image.open(original_path) as img:
            # Create optimized directory if it doesn't exist
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'optimized'), exist_ok=True)
            
            # Optimize the image with lower quality to save memory
            img = img.convert('RGB')  # Convert to RGB if necessary
            
            # Resize large images to save memory
            max_size = (800, 800)  # Reduce image size
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            
            if accept_webp:
                # Save as WebP with lower quality to save memory
                img.save(output, format='WEBP', quality=60, optimize=True)  # Reduced quality from 80 to 60
                output.seek(0)
                
                # Save optimized version for future requests
                with open(optimized_path + '.webp', 'wb') as f:
                    f.write(output.getvalue())
                
                output.seek(0)
                return send_file(output, mimetype='image/webp')
            else:
                # Save as JPEG with lower quality to save memory
                img.save(output, format='JPEG', quality=70, optimize=True)  # Reduced quality from 85 to 70
                output.seek(0)
                
                # Save optimized version for future requests
                with open(optimized_path, 'wb') as f:
                    f.write(output.getvalue())
                
                output.seek(0)
                return send_file(output, mimetype='image/jpeg')
    except Exception as e:
        # If optimization fails, serve original image
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def ensure_db_connection():
    """Ensure SQLite database connection is alive and working"""
    try:
        # Test the connection by executing a simple query
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception as e:
        error_str = str(e)
        print(f"Database connection test failed: {e}")
        
        try:
            # For SQLite, attempt to dispose and recreate the connection
            db.engine.dispose()
            return True  # Return True to continue application, connection will be re-established on next use
        except Exception as dispose_error:
            print(f"Error disposing database connection: {dispose_error}")
            return False

def create_tables():
    """Create database tables for SQLite"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            print("Database tables created successfully!")
            return True
            
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()
    
    print("Continuing application startup despite database issues...")
    print("Application will continue startup, but some features may be limited due to database issues...")
    
    # Even if table creation fails, continue with the application
    return False
def export_data():
    """Export all data to JSON files"""
    try:
        # Export users
        users = UserModel.query.all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'photo': user.photo,
                'country': user.country,
                'city': user.city,
                'bio': user.bio,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'is_admin': user.is_admin,
                'is_blocked': user.is_blocked
            })
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
        
        # Export matches
        matches = Match.query.all()
        matches_data = []
        for match in matches:
            matches_data.append({
                'id': match.id,
                'user_id': match.user_id,
                'matched_user_id': match.matched_user_id,
                'created_at': match.created_at.isoformat() if match.created_at else None
            })
        
        with open(MATCHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, ensure_ascii=False, indent=2)
        
        print("Data exported successfully!")
    except Exception as e:
        print(f"Error exporting data: {e}")

def print_server_info():
    """Выводит информацию о том, к какому адресу привязан сервер"""
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Получаем внешний IP (если возможно)
    external_ip = "Не удалось определить"
    try:
        import urllib.request
        external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
    except:
        pass
    
    print("="*70)
    print("ИНФОРМАЦИЯ О СЕРВЕРЕ:")
    print(f"Сервер запущен на хосте: {host}:{port}")
    print(f"Внешний IP-адрес: {external_ip}")
    print(f"Доступ к приложению:")
    print(f"  - Локально: http://127.0.0.1:{port}")
    print(f"  - В локальной сети: http://{host}:{port}")
    print(f"  - Если этот IP является публичным: http://{external_ip}:{port}")
    print(f"  - Если вы настроили домен на этот IP: http://fetdate.online:{port}")
    print("="*70)

# Initialize the database tables when the application starts
with app.app_context():
    create_tables()

# Add a periodic connection check
def check_db_connection():
    """Periodic function to check database connection"""
    with app.app_context():
        ensure_db_connection()

# Schedule regular connection checks (optional, can be used with schedulers like APScheduler)

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Выводим информацию о сервере перед запуском
    print_server_info()
    
    app.run(host=host, port=port, debug=True)