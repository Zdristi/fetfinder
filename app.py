import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import hashlib
from models import db, User as UserModel, Fetish, Interest, Match, Message

# Create Flask app
app = Flask(__name__)

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
    DATABASE_URL = app.config.get('DATABASE_URL', 'sqlite:///fetfinder.db')

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
SITE_NAME = 'FetFinder'

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
        'welcome': 'Welcome to FetFinder!',
        'find_match': 'Find your perfect match',
        'description': 'FetFinder is a modern dating platform where you can find matches based on shared interests and fetishes.',
        'create_profile': 'Create Profile',
        'complete_profile': 'Complete Profile',
        'discover': 'Discover Matches',
        'connect': 'Connect',
        'signup': 'Sign Up',
        'login': 'Login',
        'logout': 'Logout',
        'swipe_feature': 'Swipe through potential matches',
        'chat': 'Start meaningful conversations',
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
        'edit_profile': 'Edit Profile'
    },
    'ru': {
        'welcome': 'Добро пожаловать в FetFinder!',
        'find_match': 'Найдите свою идеальную пару',
        'description': 'FetFinder - это современная платформа для знакомств, где вы можете найти совпадения по общим интересам и фетишам.',
        'create_profile': 'Создать профиль',
        'complete_profile': 'Завершить профиль',
        'discover': 'Откройте для себя совпадения',
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
        'discover_matches': 'Откройте для себя совпадения',
        'no_more_users': 'Больше нет пользователей для показа',
        'check_later': 'Загляните позже для новых совпадений!',
        'reject': 'Отклонить',
        'superlike': 'Супер Лайк',
        'like': 'Лайк',
        'home': 'Главная',
        'profile': 'Профиль',
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
        'edit_profile': 'Редактировать профиль'
    }
}

def get_text(key):
    """Get translated text based on current language"""
    lang = session.get('language', 'en')
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)

@app.context_processor
def inject_language():
    return dict(
        get_text=get_text, 
        countries=['Russia', 'USA', 'UK', 'Germany', 'France'],
        SITE_NAME=SITE_NAME
    )

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
    # Get user's fetishes and interests
    user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=current_user.id).all()]
    user_interests = [i.name for i in Interest.query.filter_by(user_id=current_user.id).all()]
    
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'photo': current_user.photo,
        'country': current_user.country,
        'city': current_user.city,
        'bio': current_user.bio,
        'fetishes': user_fetishes,
        'interests': user_interests,
        'created_at': current_user.created_at.isoformat()
    }
    
    is_complete = bool(current_user.country and current_user.city)
    return render_template('profile.html', user_data=user_data, is_complete=is_complete)

@app.route('/swipe')
@login_required
def swipe():
    return render_template('swipe.html')

@app.route('/api/users')
@login_required
def api_users():
    db_users = UserModel.query.filter(UserModel.id != int(current_user.id)).all()
    users = []
    for user in db_users:
        user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
        user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
        users.append([
            str(user.id),
            {
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
        ])
    return jsonify(users)

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

@app.route('/matches')
@login_required
def matches():
    # Get mutual matches for current user
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
        
        matches_with_info.append({
            'user': match,
            'fetishes': match_fetishes,
            'interests': match_interests
        })
    
    return render_template('matches.html', matches=matches_with_info)

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

# Create database tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()

# For Render and other hosting platforms
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)