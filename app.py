import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
import hashlib
from models import db, User as UserModel, Fetish, Interest, Match, Message, Notification, Rating, SupportTicket, SupportMessage
import hmac
import hashlib

# Create Flask app
app = Flask(__name__)

# Add cache control headers to prevent browser caching
@app.after_request
def after_request(response):
    # Prevent caching for all responses to avoid any kind of cached content showing
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# Serve static files with cache control headers
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files with appropriate cache control headers"""
    from flask import send_from_directory
    response = send_from_directory(app.static_folder, filename)
    
    # Add version-based cache control for CSS and JS files
    if filename.endswith(('.css', '.js')):
        # For CSS and JS files, use version-based caching
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year for versioned files
    elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
        # For image files, use longer cache
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    else:
        # For other static files
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
    
    return response

# Load configuration
app.config.from_pyfile('config.py', silent=True)

# Set secret key if not configured
if not app.config.get('SECRET_KEY'):
    app.secret_key = 'your-secret-key-here-change-this-in-production'
else:
    app.secret_key = app.config['SECRET_KEY']

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = app.config.get('DATABASE_URL', 'postgresql://fetfinder_db_user:yJXZDIUB3VRK7Qf7JxRdyddjiq3ngPEr@dpg-d38m518gjchc73d67m20-a.frankfurt-postgres.render.com/fetfinder_db')

# Handle PostgreSQL URL format for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

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

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        user = UserModel.query.get(int(user_id))
        if user:
            return user
        return None
    except ValueError:
        # Handle UUID or other non-integer user IDs
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
        'error_sending_message': 'Error sending message. Please try again.'
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
        'just_per_month': 'Всего $9.99/месяц',
        'cancel_anytime': 'Отменить в любое время',
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
        'support_welcome_message': 'Здравствуйте! Добро пожаловать в поддержку FetDate. Чем мы можем вам помочь?',
        'need_immediate_help': 'Нужна срочная помощь?',
        'contact_us_by_email': 'Вы также можете связаться с нами по электронной почте:',
        'error_sending_message': 'Ошибка отправки сообщения. Пожалуйста, попробуйте снова.',
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
        'no_files_chosen': 'Файлы не выбраны'
    }
}

def get_text(key):
    """Get translated text based on current language"""
    lang = session.get('language', 'en')
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)

@app.context_processor
def inject_language():
    # Define countries and their cities
    countries_cities = {
        'Russia': ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg'],
        'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston'],
        'UK': ['London', 'Birmingham', 'Manchester', 'Glasgow'],
        'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne'],
        'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse']
    }
    return dict(
        get_text=get_text, 
        countries=['Russia', 'USA', 'UK', 'Germany', 'France'],
        COUNTRIES_CITIES=countries_cities,
        SITE_NAME=SITE_NAME,
        is_premium_user=is_premium_user
    )


@app.route('/get_cities/<country>')
def get_cities(country):
    countries_cities = {
        'Russia': ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg'],
        'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston'],
        'UK': ['London', 'Birmingham', 'Manchester', 'Glasgow'],
        'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne'],
        'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse']
    }
    cities = countries_cities.get(country, [])
    return jsonify(cities)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['language'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username already exists
        existing_user = UserModel.query.filter_by(username=username).first()
        if existing_user:
            flash(get_text('username_exists'))
            return redirect(url_for('register'))
        
        # Create new user
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
        
        flash(get_text('registration_success'))
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
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
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    return show_profile(current_user.id)


@app.route('/profile/<int:user_id>')
@login_required
def show_profile(user_id):
    # Get the specified user
    user = UserModel.query.get_or_404(user_id)
    
    # Get user's fetishes and interests
    user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
    user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
    
    user_data = {
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
@login_required
def edit_profile():
    if request.method == 'POST':
        # Update user profile information
        current_user.country = request.form.get('country')
        current_user.city = request.form.get('city')
        current_user.bio = request.form.get('bio')
        
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
    return render_template('swipe.html')

@app.route('/users')
@login_required
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


@app.route('/api/users')
@login_required
def api_users():
    try:
        # Get all users except current user and blocked users
        # For testing, we'll show all users, even those with incomplete profiles
        db_users = UserModel.query.filter(
            UserModel.id != int(current_user.id),
            UserModel.is_blocked == False
        ).all()
        
        users = []
        for user in db_users:
            try:
                user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
                user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
                users.append([
                    str(user.id),
                    {
                        'username': user.username or 'Anonymous',
                        'email': user.email or '',
                        'photo': user.photo or '',
                        'country': user.country or '',
                        'city': user.city or '',
                        'bio': user.bio or '',
                        'fetishes': user_fetishes,
                        'interests': user_interests,
                        'created_at': user.created_at.isoformat() if user.created_at else ''
                    }
                ])
            except Exception as e:
                print(f"Error processing user {user.id}: {e}")
                continue
        
        print(f"Returning {len(users)} users for swipe")
        return jsonify(users)
    except Exception as e:
        print(f"Error in api_users: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500

@app.route('/api/match', methods=['POST'])
@login_required
def api_match():
    data = request.get_json()
    user2 = data.get('user2')
    action = data.get('action')  # 'like' or 'dislike'
    

    
    is_mutual_match = False
    
    if action == 'like':
        # Check if match already exists
        existing_match = Match.query.filter_by(
            user_id=int(current_user.id), 
            matched_user_id=int(user2)
        ).first()
        
        if not existing_match:
            match = Match(
                user_id=int(current_user.id),
                matched_user_id=int(user2)
            )
            db.session.add(match)
            db.session.commit()
            
            # Check if this is a mutual match
            reverse_match = Match.query.filter_by(
                user_id=int(user2),
                matched_user_id=int(current_user.id)
            ).first()
            
            # Return True if it's a mutual match
            is_mutual_match = reverse_match is not None
    elif action == 'dislike':
        # Record dislike (we may need this for undo functionality)
        # We don't need to store dislikes in a separate table for now
        # as they don't create matches
        pass

    response = {'status': 'success'}
    
    # If it's a mutual match, add notification
    if is_mutual_match:
        response['mutual_match'] = True
        response['matched_user_id'] = user2
        # Get matched user info
        matched_user = UserModel.query.get(int(user2))
        if matched_user:
            response['matched_user_name'] = matched_user.username
            response['matched_user_photo'] = matched_user.photo
    
    return jsonify(response)


def likes_today(user_id, target_date=None):
    """Count likes sent by user today"""
    from datetime import datetime, date
    if target_date is None:
        target_date = datetime.utcnow().date()
    
    count = Match.query.filter(
        Match.user_id == user_id,
        db.func.date(Match.created_at) == target_date
    ).count()
    
    return count

@app.route('/blocked')
def blocked():
    if not current_user.is_authenticated or not current_user.is_blocked:
        return redirect(url_for('home'))
    return render_template('blocked.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    users = UserModel.query.all()
    return render_template('admin.html', users=users)

@app.route('/chat')
@login_required
def chat_list():
    # Get mutual matches for current user (these are the users they can chat with)
    user_matches = Match.query.filter_by(user_id=int(current_user.id)).all()
    match_user_ids = [match.matched_user_id for match in user_matches]
    
    # Get reverse matches (people who liked current user)
    reverse_matches = Match.query.filter_by(matched_user_id=int(current_user.id)).all()
    reverse_match_user_ids = [match.user_id for match in reverse_matches]
    
    # Mutual matches are intersection of both lists
    mutual_match_ids = list(set(match_user_ids) & set(reverse_match_user_ids))
    
    # Get user objects for mutual matches
    mutual_matches = UserModel.query.filter(UserModel.id.in_(mutual_match_ids)).all()
    
    # Add additional info for each match
    matches_with_info = []
    for match in mutual_matches:
        match_fetishes = [f.name for f in Fetish.query.filter_by(user_id=match.id).all()]
        match_interests = [i.name for i in Interest.query.filter_by(user_id=match.id).all()]
        
        # Count unread messages from this match
        unread_count = Message.query.filter_by(
            sender_id=match.id, 
            recipient_id=current_user.id, 
            is_read=False
        ).count()
        
        matches_with_info.append({
            'user': match,
            'fetishes': match_fetishes,
            'interests': match_interests,
            'unread_count': unread_count
        })
    
    return render_template('matches.html', matches=matches_with_info)


@app.route('/chat/<int:recipient_id>', methods=['GET', 'POST'])
@login_required
def chat(recipient_id):
    recipient = UserModel.query.get_or_404(recipient_id)
    
    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            message = Message(
                sender_id=current_user.id,
                recipient_id=recipient_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            return redirect(url_for('chat', recipient_id=recipient_id))
    
    # Get conversation messages
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    # Mark unread messages as read
    unread_messages = Message.query.filter_by(
        sender_id=recipient_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    return render_template('chat.html', recipient=recipient, messages=messages)


def messages_today(user_id, target_date=None):
    """Count messages sent by user today"""
    from datetime import datetime, date
    if target_date is None:
        target_date = datetime.utcnow().date()
    
    count = Message.query.filter(
        Message.sender_id == user_id,
        db.func.date(Message.timestamp) == target_date
    ).count()
    
    return count


@app.route('/api/undo_swipe', methods=['POST'])
@login_required
def api_undo_swipe():

    
    # In a full implementation, you would:
    # 1. Check if user has used their undo quota for the day (e.g., 5 undos per day)
    # 2. Remove the last like/dislike action from the database
    # For this example, we'll just return success to allow the frontend to handle it
    
    return jsonify({'status': 'success'})


@app.route('/api/send_message', methods=['POST'])
@login_required
def api_send_message():
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if not recipient_id or not content:
        return jsonify({'status': 'error', 'error': 'Missing recipient_id or content'})
    
    recipient = UserModel.query.get(recipient_id)
    if not recipient:
        return jsonify({'status': 'error', 'error': 'Recipient not found'})
    
    # No message limits - users can communicate freely
    # The premium restriction is on interactions (likes/swipes) not on messaging
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    # Return message data in the format expected by the chat UI
    return jsonify({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sender_id': message.sender_id
        }
    })


@app.route('/api/message_limit_check')
@login_required
def api_message_limit_check():
    """Check if user has reached their daily message limit - always returns success"""
    return jsonify({'status': 'success', 'limit_reached': False})


@app.route('/api/user_info/<int:user_id>')
@login_required
def api_user_info(user_id):
    user = UserModel.query.get_or_404(user_id)
    
    # Get user's fetishes and interests
    user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
    user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
    
    return jsonify({
        'fetishes': user_fetishes,
        'interests': user_interests
    })


# Admin routes for user management
@app.route('/admin/block_user/<int:user_id>', methods=['POST'])
@login_required
def admin_block_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot block yourself')
    else:
        user.is_blocked = True
        db.session.commit()
        flash(f'User {user.username} has been blocked')
    
    return redirect(url_for('admin'))


@app.route('/admin/unblock_user/<int:user_id>', methods=['POST'])
@login_required
def admin_unblock_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    user.is_blocked = False
    db.session.commit()
    flash(f'User {user.username} has been unblocked')
    
    return redirect(url_for('admin'))


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account')
    else:
        # Delete related records first
        Fetish.query.filter_by(user_id=user.id).delete()
        Interest.query.filter_by(user_id=user.id).delete()
        Match.query.filter_by(user_id=user.id).delete()
        Match.query.filter_by(matched_user_id=user.id).delete()
        Message.query.filter_by(sender_id=user.id).delete()
        Message.query.filter_by(recipient_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted')
    
    return redirect(url_for('admin'))


@app.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@login_required
def admin_make_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You are already an admin')
    else:
        user.is_admin = True
        db.session.commit()
        flash(f'User {user.username} is now an admin')
    
    return redirect(url_for('admin'))


# Premium subscription routes
@app.route('/premium')
@login_required
def premium():
    from datetime import datetime
    return render_template('premium.html', user=current_user, now=datetime.utcnow())

















@app.route('/remove_premium/<int:user_id>', methods=['POST'])
@login_required
def remove_premium(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    user = UserModel.query.get_or_404(user_id)
    user.is_premium = False
    user.premium_expires = None
    db.session.commit()
    flash(f'Premium status removed from user {user.username}')
    
    return redirect(url_for('admin'))


@app.route('/unsubscribe_premium', methods=['POST'])
@login_required
def unsubscribe_premium():
    # For now, we'll just remove the premium status
    current_user.is_premium = False
    current_user.premium_expires = None
    db.session.commit()
    flash('Your premium subscription has been cancelled.')
    
    return redirect(url_for('profile'))


@app.route('/subscribe_premium', methods=['POST'])
@login_required
def subscribe_premium():
    # Grant premium status to user
    current_user.is_premium = True
    current_user.premium_expires = datetime.utcnow() + timedelta(days=30)  # 30 days premium
    db.session.commit()
    
    flash('Congratulations! You are now a premium member.')
    return redirect(url_for('profile'))


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/support_chat')
@login_required
def support_chat():
    return render_template('support_chat.html')


@app.route('/admin/support_chat')
@login_required
def admin_support_chat():
    # Check if user is admin
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    return render_template('admin_support_chat.html')


# API routes for support chat
@app.route('/api/support/send_message', methods=['POST'])
@login_required
def api_support_send_message():
    """Send a message from user to support"""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'status': 'error', 'message': 'Message content is required'})
        
        # Check if user already has an open ticket
        ticket = SupportTicket.query.filter_by(
            user_id=current_user.id, 
            status='open'
        ).first()
        
        # If no open ticket, create a new one
        if not ticket:
            ticket = SupportTicket(
                user_id=current_user.id,
                subject=f'Support request from {current_user.username}',
                status='open'
            )
            db.session.add(ticket)
            db.session.flush()  # Get ticket ID
        
        # Create the message
        message = SupportMessage(
            ticket_id=ticket.id,
            sender_id=current_user.id,
            content=content,
            is_admin=False
        )
        db.session.add(message)
        
        # Update ticket timestamp
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Message sent successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error sending support message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Error sending message: {str(e)}'})


@app.route('/api/admin/support/tickets')
@login_required
def api_admin_support_tickets():
    """Get all support tickets for admin"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'})
        
        # Get all tickets ordered by last update
        tickets = SupportTicket.query.order_by(SupportTicket.updated_at.desc()).all()
        
        # Convert to dictionary format
        tickets_data = []
        for ticket in tickets:
            try:
                tickets_data.append({
                    'id': ticket.id,
                    'user_id': ticket.user_id,
                    'user': {
                        'id': ticket.user.id if ticket.user else None,
                        'username': ticket.user.username if ticket.user else 'Unknown User'
                    },
                    'subject': ticket.subject,
                    'status': ticket.status,
                    'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                    'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None
                })
            except AttributeError as ae:
                print(f"Error accessing ticket.user: {ae}")
                # Handle orphaned tickets gracefully
                tickets_data.append({
                    'id': ticket.id,
                    'user_id': ticket.user_id,
                    'user': {
                        'id': None,
                        'username': 'Deleted User'
                    },
                    'subject': ticket.subject,
                    'status': ticket.status,
                    'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                    'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None
                })
        
        return jsonify({'status': 'success', 'tickets': tickets_data})
        
    except Exception as e:
        print(f"Error getting support tickets: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Error loading tickets: {str(e)}'})


@app.route('/api/admin/support/ticket/<int:ticket_id>/messages')
@login_required
def api_admin_support_ticket_messages(ticket_id):
    """Get messages for a specific support ticket"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'})
        
        # Get the ticket
        ticket = SupportTicket.query.get_or_404(ticket_id)
        
        # Get all messages for this ticket
        messages = SupportMessage.query.filter_by(ticket_id=ticket_id).order_by(SupportMessage.timestamp.asc()).all()
        
        # Convert to dictionary format
        messages_data = []
        for message in messages:
            try:
                messages_data.append({
                    'id': message.id,
                    'ticket_id': message.ticket_id,
                    'sender_id': message.sender_id,
                    'sender': {
                        'id': message.sender.id if message.sender else None,
                        'username': message.sender.username if message.sender else 'Unknown User'
                    },
                    'content': message.content,
                    'is_admin': message.is_admin,
                    'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                    'is_read': message.is_read
                })
            except AttributeError as ae:
                print(f"Error accessing message.sender: {ae}")
                # Handle orphaned messages gracefully
                messages_data.append({
                    'id': message.id,
                    'ticket_id': message.ticket_id,
                    'sender_id': message.sender_id,
                    'sender': {
                        'id': None,
                        'username': 'Deleted User'
                    },
                    'content': message.content,
                    'is_admin': message.is_admin,
                    'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                    'is_read': message.is_read
                })
        
        return jsonify({'status': 'success', 'messages': messages_data})
        
    except Exception as e:
        print(f"Error getting ticket messages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Error loading messages: {str(e)}'})


@app.route('/api/admin/support/send_message', methods=['POST'])
@login_required
def api_admin_support_send_message():
    """Send a message from admin to user"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': 'Access denied'})
        
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        content = data.get('content', '').strip()
        
        if not ticket_id or not content:
            return jsonify({'status': 'error', 'message': 'Ticket ID and message content are required'})
        
        # Get the ticket
        ticket = SupportTicket.query.get_or_404(ticket_id)
        
        # Create the message
        message = SupportMessage(
            ticket_id=ticket.id,
            sender_id=current_user.id,
            content=content,
            is_admin=True
        )
        db.session.add(message)
        
        # Update ticket status and timestamp
        ticket.status = 'replied'
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Message sent successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error sending admin support message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Error sending message: {str(e)}'})


@app.route('/test_match')
@login_required
def test_match():
    """Test route to create a mutual match for testing"""
    # Get another user (not the current user)
    other_user = UserModel.query.filter(UserModel.id != int(current_user.id)).first()
    if not other_user:
        flash('No other users found')
        return redirect(url_for('home'))
    
    # Create mutual matches
    match1 = Match(user_id=int(current_user.id), matched_user_id=other_user.id)
    match2 = Match(user_id=other_user.id, matched_user_id=int(current_user.id))
    
    # Check if matches already exist
    existing1 = Match.query.filter_by(user_id=int(current_user.id), matched_user_id=other_user.id).first()
    existing2 = Match.query.filter_by(user_id=other_user.id, matched_user_id=int(current_user.id)).first()
    
    if not existing1:
        db.session.add(match1)
    if not existing2:
        db.session.add(match2)
    
    db.session.commit()
    
    flash(f'Created test mutual match with {other_user.username}')
    return redirect(url_for('matches'))


# API routes for notifications
@app.route('/api/notifications')
@login_required
def api_notifications():
    """Get current user's notifications"""
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


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Notification not found'}), 404


@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_mark_all_notifications_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    return jsonify({'status': 'success'})

def create_tables():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

def export_data():
    """Export all data to JSON backup"""
    with app.app_context():
        from data_migration import export_data_to_json
        export_data_to_json()

def import_data():
    """Import data from JSON backup"""
    with app.app_context():
        from data_migration import import_data_from_json
        import_data_from_json()


# API routes for star ratings
@app.route('/api/rating', methods=['POST'])
@login_required
def api_set_rating():
    """Set a star rating for a user"""
    data = request.get_json()
    rated_user_id = data.get('rated_user_id')
    stars = data.get('stars')
    
    if not rated_user_id or not stars:
        return jsonify({'status': 'error', 'message': 'Missing rated_user_id or stars'})
    
    if not (1 <= stars <= 5):
        return jsonify({'status': 'error', 'message': 'Stars must be between 1 and 5'})
    
    # Check if user is trying to rate themselves
    if int(rated_user_id) == int(current_user.id):
        return jsonify({'status': 'error', 'message': 'Cannot rate yourself'})
    
    # Check if rated user exists
    rated_user = UserModel.query.get(rated_user_id)
    if not rated_user:
        return jsonify({'status': 'error', 'message': 'Rated user not found'})
    
    # Check if rating already exists
    existing_rating = Rating.query.filter_by(
        rater_id=int(current_user.id),
        rated_user_id=int(rated_user_id)
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.stars = stars
        existing_rating.timestamp = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Rating updated successfully'})
    else:
        # Create new rating
        rating = Rating(
            rater_id=int(current_user.id),
            rated_user_id=int(rated_user_id),
            stars=stars
        )
        db.session.add(rating)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Rating created successfully'})


@app.route('/api/rating/<int:user_id>')
def api_get_user_rating(user_id):
    """Get a user's average rating"""
    user = UserModel.query.get_or_404(user_id)
    
    # Calculate average rating
    ratings = Rating.query.filter_by(rated_user_id=user.id).all()
    total_ratings = len(ratings)
    avg_rating = sum(rating.stars for rating in ratings) / total_ratings if total_ratings > 0 else 0
    
    return jsonify({
        'avg_rating': round(avg_rating, 1),
        'total_ratings': total_ratings
    })


# Create database tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()

# Run database migrations to add missing columns if they don't exist
with app.app_context():
    try:
        from migrate_db import check_and_add_columns
        check_and_add_columns()
        print("Database migrations completed successfully!")
    except Exception as e:
        print(f"Error running Python-based database migrations: {e}")
        print("Attempting psql-based migration instead...")
        try:
            from psql_migration import run_psql_migration
            run_psql_migration()
            print("Psql-based database migrations completed successfully!")
        except Exception as e2:
            print(f"Error running psql-based database migrations: {e2}")
            import traceback
            traceback.print_exc()

def is_premium_user(user):
    """Check if user has an active premium subscription"""
    if not user.is_premium:
        return False
    if user.premium_expires and user.premium_expires < datetime.utcnow():
        # Subscription has expired, remove premium status
        user.is_premium = False
        user.premium_expires = None
        db.session.commit()
        return False
    return True

def get_static_version(filename):
    """Generate a version string based on file modification time to bust cache"""
    import os
    try:
        file_path = os.path.join(app.static_folder, filename)
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            # Include full timestamp to ensure uniqueness
            return f"?v={int(mtime * 1000000)}"  # Use microseconds to make unique
        else:
            return "?v=1.0"
    except:
        return "?v=1.0"


@app.context_processor
def inject_static_version():
    return dict(static_version=get_static_version)


# For Render and other hosting platforms
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)