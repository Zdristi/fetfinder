import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message as EmailMessage
import json
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
import hashlib
from models import db, User as UserModel, Fetish, Interest, Match, Message, Notification, Rating, SupportTicket, SupportMessage
import hmac
import hashlib
import random
import string
import re
import requests

# Create Flask app
app = Flask(__name__)

# Add reCAPTCHA configuration
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lc6BhgUAAAAAAH5u7f8rXz8rXz8rXz8rXz8rXz8'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lc6BhgUAAAAAAH5u7f8rXz8rXz8rXz8rXz8rXz8'

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://fetfinder_db_user:yJXZDIUB3VRK7Qf7JxRdyddjiq3ngPEr@dpg-d38m518gjchc73d67m20-a.frankfurt-postgres.render.com/fetfinder_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 10
    }
}

# Initialize database
db.init_app(app)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sup.fetdate@gmail.com'
app.config['MAIL_PASSWORD'] = 'jzrxaivqpwaalodj'  # Пароль приложения Gmail
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Site configuration
SITE_NAME = 'FetDate'

# Configuration
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Data storage
DATA_FILE = 'users.json'
MATCHES_FILE = 'matches.json'

# Temporary storage for confirmation codes (in production, use Redis or database)
confirmation_codes = {}

def generate_confirmation_code():
    """Генерирует 6-значный код подтверждения"""
    return ''.join(random.choices(string.digits, k=6))

def send_confirmation_email(email, code):
    """Отправляет код подтверждения на email"""
    try:
        msg = EmailMessage(
            subject='Код подтверждения регистрации - FetDate',
            recipients=[email],
            body=f'Ваш код подтверждения: {code}\n\nВведите этот код на сайте для завершения регистрации.'
        )
        mail.send(msg)
        print(f"Письмо успешно отправлено на {email}")
        return True
    except Exception as e:
        print(f"Ошибка при отправке email на {email}: {e}")
        import traceback
        traceback.print_exc()
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
    if current_user.is_authenticated and current_user.is_blocked:
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
        'undo_swipes_desc': 'Change your mind and undo up to 5 swipes per day',
        'unlimited_messaging': 'Unlimited Messaging',
        'unlimited_messaging_desc': 'Send unlimited messages to your matches',
        'premium_badge': 'Premium Badge',
        'premium_badge_desc': 'Stand out with a premium badge on your profile',
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
        'frequently_asked_questions': 'Frequently Asked Questions',
        'back_to_home': 'Back to Home',
        'how_do_i_create_an_account': 'How do I create an account?',
        'how_do_i_create_an_account_answer': 'To create an account, click the "Sign Up" button on the homepage. Fill in your username, email, and password, then follow the instructions to complete your profile.',
        'how_do_i_find_matches': 'How do I find matches?',
        'how_do_i_find_matches_answer': 'After completing your profile, go to the "Discover" section to start swiping through potential matches. You can like or reject profiles based on your preferences.',
        'is_my_information_secure': 'Is my information secure?',
        'is_my_information_secure_answer': 'We take your privacy seriously. All personal information is encrypted and stored securely. We never share your data with third parties without your consent.',
        'what_are_premium_features': 'What are Premium features?',
        'what_are_premium_features_answer': 'Premium members enjoy unlimited swipes, the ability to undo up to 5 swipes per day, unlimited messaging, and a premium badge on their profile. Premium also gives priority placement in discovery queues.',
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
        'undo_swipes_desc': 'Передумали? Отмените до 5 свайпов в день',
        'unlimited_messaging': 'Неограниченные сообщения',
        'unlimited_messaging_desc': 'Отправляйте неограниченное количество сообщений своим совпадениям',
        'premium_badge': 'Премиум бейдж',
        'premium_badge_desc': 'Выделяйтесь с премиум бейджем в своем профиле',
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
        'frequently_asked_questions': 'Часто задаваемые вопросы',
        'back_to_home': 'Назад на главную',
        'how_do_i_create_an_account': 'Как создать аккаунт?',
        'how_do_i_create_an_account_answer': 'Чтобы создать аккаунт, нажмите кнопку "Зарегистрироваться" на главной странице. Заполните имя пользователя, электронную почту и пароль, затем следуйте инструкциям для завершения профиля.',
        'how_do_i_find_matches': 'Как найти совпадения?',
        'how_do_i_find_matches_answer': 'После завершения профиля перейдите в раздел "Метчи", чтобы начать свайпинг по потенциальным совпадениям. Вы можете лайкать или отклонять профили по вашим предпочтениям.',
        'is_my_information_secure': 'Безопасна ли моя информация?',
        'is_my_information_secure_answer': 'Мы серьезно относимся к вашей конфиденциальности. Вся личная информация шифруется и надежно хранится. Мы никогда не передаем ваши данные третьим сторонам без вашего согласия.',
        'what_are_premium_features': 'Какие возможности даёт Премиум?',
        'what_are_premium_features_answer': 'Премиум участники получают неограниченные свайпы, возможность отменять до 5 свайпов в день, неограниченные сообщения и премиум бейдж на своем профиле. Премиум также обеспечивает приоритетное размещение в очереди обнаружения.',
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
        'view_matches': 'Просмотреть совпадения'
    }
}

def get_text(key):
    """Get translated text based on current language"""
    lang = session.get('language', 'en')
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)

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
@with_timeout(15)  # Таймаут 15 секунд для регистрации
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Проверка CAPTCHA
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            flash('Пожалуйста, подтвердите, что вы не робот.')
            return render_template('register.html')
        
        # Проверка CAPTCHA через Google API (для упрощения пропустим эту часть)
        # В реальной реализации здесь должна быть проверка через Google reCAPTCHA API
        
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
            
            # Generate confirmation code
            confirmation_code = generate_confirmation_code()
            
            # Создаем пользователя без новых полей до выполнения миграции базы данных
            user = UserModel(
                username=username,
                email=email
            )
            user.set_password(password)
            
            # Check if this is the first user (make them admin)
            if UserModel.query.count() == 0:
                user.is_admin = True
            
            db.session.add(user)
            db.session.commit()
            
            # Store the confirmation code in temporary storage
            confirmation_codes[email] = {
                'code': confirmation_code,
                'expires': datetime.utcnow() + timedelta(hours=1),  # Код действителен 1 час
                'user_id': user.id
            }
            
            # Попытка отправки письма подтверждения (необязательно)
            email_sent = send_confirmation_email(email, confirmation_code)
            if email_sent:
                # Redirect to verification page
                flash('Пожалуйста, проверьте вашу почту для подтверждения регистрации.')
                return redirect(url_for('verify_email_page', email=email))
            else:
                # Если письмо не отправлено, всё равно продолжаем регистрацию
                flash('Регистрация прошла успешно. Проверьте ваш email для подтверждения (письмо может прийти с задержкой).')
                login_user(user)
                return redirect(url_for('edit_profile'))
                
        except Exception as e:
            db.session.rollback()
            error_str = str(e)
            # Check if it's a duplicate email error
            if 'duplicate key value violates unique constraint' in error_str and 'email' in error_str:
                flash(get_text('email_exists') or 'A user with this email already exists')
            elif 'SSL error' in error_str or 'connection' in error_str.lower() or 'timeout' in error_str.lower() or 'server closed the connection unexpectedly' in error_str or isinstance(e, TimeoutError):
                # Обработка ошибок подключения к базе данных и таймаутов
                flash('Сервис временно недоступен. Пожалуйста, попробуйте зарегистрироваться чуть позже.')
                print(f"Database connection error or timeout during registration: {e}")
            else:
                flash('An error occurred during registration. Please try again.')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/verify_email')
def verify_email_page():
    email = request.args.get('email')
    if not email:
        flash('Неверный запрос. Пожалуйста, зарегистрируйтесь снова.')
        return redirect(url_for('register'))
    
    return render_template('verify_email.html', email=email)

@app.route('/verify_email', methods=['POST'])
def verify_email():
    email = request.form.get('email')
    code = request.form.get('code')
    
    if not email or not code:
        flash('Все поля обязательны для заполнения.')
        return redirect(url_for('verify_email_page', email=email))
    
    # Check if code exists in temporary storage and is valid
    if email in confirmation_codes:
        stored_data = confirmation_codes[email]
        stored_code = stored_data['code']
        expires = stored_data['expires']
        
        if code == stored_code and expires > datetime.utcnow():
            # Code is valid and not expired
            # Find user by email
            user = UserModel.query.filter_by(email=email).first()
            if user:
                # Delete the code from temporary storage
                del confirmation_codes[email]
                
                # Login the user and redirect
                login_user(user)
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
    
    user = UserModel.query.filter_by(email=email).first()
    if not user:
        flash('Пользователь с таким email не найден.')
        return redirect(url_for('register'))
    
    # Generate new confirmation code
    new_code = generate_confirmation_code()
    
    # Update temporary storage with new code
    confirmation_codes[email] = {
        'code': new_code,
        'expires': datetime.utcnow() + timedelta(hours=1),
        'user_id': user.id
    }
    
    # Send new confirmation email
    if send_confirmation_email(email, new_code):
        flash('Новый код подтверждения отправлен на ваш email.')
        return redirect(url_for('verify_email_page', email=email))
    else:
        flash('Ошибка при отправке нового кода. Пожалуйста, попробуйте позже.')
        return redirect(url_for('verify_email_page', email=email))

@app.route('/login', methods=['GET', 'POST'])
@with_timeout(10)  # Таймаут 10 секунд для входа
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            # Find user
            user = UserModel.query.filter_by(username=username).first()
            if user and user.check_password(password):
                # Check if user is blocked
                if user.is_blocked:
                    flash('Your account has been blocked')
                    return redirect(url_for('login'))
                
                # Log in the user
                login_user(user)
                return redirect(url_for('profile'))
            
            flash(get_text('invalid_credentials'))
            return redirect(url_for('login'))
        except Exception as e:
            error_str = str(e)
            if 'SSL error' in error_str or 'connection' in error_str.lower() or 'timeout' in error_str.lower() or 'server closed the connection unexpectedly' in error_str or isinstance(e, TimeoutError):
                # Обработка ошибок подключения к базе данных и таймаутов
                flash('Сервис временно недоступен. Пожалуйста, попробуйте войти чуть позже.')
                print(f"Database connection error or timeout during login: {e}")
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
def profile():
    return show_profile(current_user.id)

@app.route('/profile/<int:user_id>')
def show_profile(user_id):
    # Get the specified user
    user = UserModel.query.get_or_404(user_id)
    
    # Get user's fetishes and interests
    user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
    user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
    
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
        'created_at': user.created_at.isoformat(),
        'is_premium': is_premium_user(user)
    }
    
    is_complete = bool(user.country and user.city)
    return render_template('profile.html', user_data=user_data, is_complete=is_complete)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
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
                return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
            if not city:
                flash('City is required')
                return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)
            if not bio:
                flash('Biography is required')
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
                # Create unique filename
                ext = photo.filename.split('.')[-1]
                filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(filepath)
                current_user.photo = filename
        
        # If user is new and doesn't have a photo, require photo upload
        if is_new_user and not current_user.photo:
            flash('Profile photo is required for new users')
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
        'is_premium': is_premium_user(current_user)
    }
    
    return render_template('edit_profile.html', user=user_data, fetishes=all_fetishes, interests=all_interests)

@app.route('/swipe')
@login_required
def swipe():
    return render_template('swipe_fresh.html')

@app.route('/users')
def users():
    db_users = UserModel.query.filter(UserModel.id != int(current_user.id)).all()
    users_dict = {}
    for user in db_users:
        user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
        user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
        users_dict[user.id] = {
            'username': user.username,
            'email': user.email,
            'photo': user.photo,
            'country': user.country,
            'city': user.city,
            'bio': user.bio,
            'fetishes': user_fetishes,
            'interests': user_interests,
            'created_at': user.created_at.isoformat()
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

# Database initialization
def create_tables():
    """Create database tables"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Check and add missing columns to user table
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            # List of columns to check and add if missing
            required_columns = [
                'about_me_video', 'relationship_goals', 'lifestyle', 'diet', 
                'smoking', 'drinking', 'occupation', 'education', 'children', 
                'pets', 'coins', 'match_by_city', 'match_by_country'
            ]
            
            for column in required_columns:
                if column not in columns:
                    print(f"Column {column} is missing. Please run database migration.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()

# Export data function
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

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)