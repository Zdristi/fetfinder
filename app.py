from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import json
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import hashlib
from models import db, User as UserModel, Fetish, Interest, Match

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)

# Set secret key if not configured
if not app.config.get('SECRET_KEY'):
    app.secret_key = 'your-secret-key-here-change-this-in-production'
else:
    app.secret_key = app.config['SECRET_KEY']

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fetfinder.db')
# Handle PostgreSQL URL format for SQLAlchemy
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Site configuration
SITE_NAME = 'FetFinder'

# Configuration
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'static/uploads')

# Initialize database
db.init_app(app)

# Configuration for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
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
DATA_FILE = DATABASE_FILE
MATCHES_FILE = MATCHES_FILE

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email=None, photo=None, country=None, city=None, bio=None, 
                 is_admin=False, is_blocked=False, blocked_reason=None):
        self.id = id
        self.username = username
        self.email = email
        self.photo = photo
        self.country = country
        self.city = city
        self.bio = bio
        self.is_admin = is_admin
        self.is_blocked = is_blocked
        self.blocked_reason = blocked_reason
        self.created_at = datetime.now().isoformat()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user = UserModel.query.get(int(user_id))
    if user:
        # Create a User object compatible with our existing code
        return User(
            id=str(user.id),
            username=user.username,
            email=user.email,
            photo=user.photo,
            country=user.country,
            city=user.city,
            bio=user.bio,
            is_admin=user.is_admin,
            is_blocked=user.is_blocked,
            blocked_reason=user.blocked_reason
        )
    return None

# User class for Flask-Login (compatible with database)
class User(UserMixin):
    def __init__(self, id, username, email=None, photo=None, country=None, city=None, bio=None, 
                 is_admin=False, is_blocked=False, blocked_reason=None):
        self.id = id
        self.username = username
        self.email = email
        self.photo = photo
        self.country = country
        self.city = city
        self.bio = bio
        self.is_admin = is_admin
        self.is_blocked = is_blocked
        self.blocked_reason = blocked_reason
        self.created_at = datetime.now().isoformat()

# Country and city data
COUNTRIES_CITIES = {
    "Russia": ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod", "Chelyabinsk", "Samara", "Omsk", "Rostov-on-Don"],
    "USA": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"],
    "UK": ["London", "Birmingham", "Leeds", "Glasgow", "Sheffield", "Bradford", "Liverpool", "Manchester", "Edinburgh", "Bristol"],
    "Germany": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Dusseldorf", "Leipzig", "Dortmund", "Essen"],
    "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille"]
}

def load_users():
    # This function is kept for compatibility but not used with database
    users = {}
    db_users = UserModel.query.all()
    for user in db_users:
        users[str(user.id)] = {
            'username': user.username,
            'email': user.email,
            'password': user.password_hash,
            'photo': user.photo,
            'country': user.country,
            'city': user.city,
            'bio': user.bio,
            'is_admin': user.is_admin,
            'is_blocked': user.is_blocked,
            'blocked_reason': user.blocked_reason,
            'created_at': user.created_at.isoformat()
        }
    return users

def save_users(users):
    # This function is kept for compatibility but not used with database
    pass

def load_matches():
    # This function is kept for compatibility but not used with database
    matches = {}
    db_matches = Match.query.all()
    for match in db_matches:
        if str(match.user_id) not in matches:
            matches[str(match.user_id)] = []
        matches[str(match.user_id)].append(str(match.matched_user_id))
    return matches

def save_matches(matches):
    # This function is kept for compatibility but not used with database
    pass

def get_user_by_id(user_id):
    return UserModel.query.get(user_id)

def get_all_users():
    return UserModel.query.all()

def create_user(username, email, password):
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
    return user

def update_user_profile(user_id, bio, country, city, photo_filename):
    user = UserModel.query.get(user_id)
    if user:
        user.bio = bio
        user.country = country
        user.city = city
        if photo_filename:
            user.photo = photo_filename
        db.session.commit()
        return True
    return False

def add_user_fetishes(user_id, fetishes):
    user = UserModel.query.get(user_id)
    if user:
        # Remove existing fetishes
        Fetish.query.filter_by(user_id=user_id).delete()
        # Add new fetishes
        for fetish_name in fetishes:
            fetish = Fetish(name=fetish_name, user_id=user_id)
            db.session.add(fetish)
        db.session.commit()
        return True
    return False

def add_user_interests(user_id, interests):
    user = UserModel.query.get(user_id)
    if user:
        # Remove existing interests
        Interest.query.filter_by(user_id=user_id).delete()
        # Add new interests
        for interest_name in interests:
            interest = Interest(name=interest_name, user_id=user_id)
            db.session.add(interest)
        db.session.commit()
        return True
    return False

def get_user_fetishes(user_id):
    fetishes = Fetish.query.filter_by(user_id=user_id).all()
    return [f.name for f in fetishes]

def get_user_interests(user_id):
    interests = Interest.query.filter_by(user_id=user_id).all()
    return [i.name for i in interests]

def block_user(user_id, reason="", blocked_by=None):
    user = UserModel.query.get(user_id)
    if user:
        user.is_blocked = True
        user.blocked_reason = reason
        db.session.commit()
        return True
    return False

def unblock_user(user_id):
    user = UserModel.query.get(user_id)
    if user:
        user.is_blocked = False
        user.blocked_reason = None
        db.session.commit()
        return True
    return False

def delete_user(user_id):
    user = UserModel.query.get(user_id)
    if user:
        # Delete related records
        Fetish.query.filter_by(user_id=user_id).delete()
        Interest.query.filter_by(user_id=user_id).delete()
        Match.query.filter_by(user_id=user_id).delete()
        Match.query.filter_by(matched_user_id=user_id).delete()
        
        db.session.delete(user)
        db.session.commit()
        return True
    return False

def make_admin(user_id):
    user = UserModel.query.get(user_id)
    if user:
        user.is_admin = True
        db.session.commit()
        return True
    return False

def add_match(user_id, matched_user_id):
    # Check if match already exists
    existing_match = Match.query.filter_by(
        user_id=user_id, 
        matched_user_id=matched_user_id
    ).first()
    
    if not existing_match:
        match = Match(
            user_id=user_id,
            matched_user_id=matched_user_id
        )
        db.session.add(match)
        db.session.commit()
        return True
    return False

def get_other_users(current_user_id):
    return UserModel.query.filter(UserModel.id != current_user_id).all()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Predefined list of common fetishes for users to choose from
COMMON_FETISHES = [
    "Feet", "Hands", "Hair", "Lingerie", "Uniforms", "Tattoos", 
    "Piercings", "Muscles", "Curves", "Voice", "Smiles", "Eyes",
    "Age Play", "Role Play", "Costumes", "Fantasy Scenarios"
]

# Predefined list of common hobbies/interests for users to choose from
COMMON_INTERESTS = [
    "Music", "Travel", "Fitness", "Cooking", "Art", "Movies", 
    "Books", "Gaming", "Photography", "Dancing", "Sports",
    "Technology", "Nature", "Animals", "Fashion", "Food",
    "Writing", "Languages", "Meditation", "Yoga", "Hiking"
]

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

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.before_request
def check_blocked_user():
    if current_user.is_authenticated and current_user.is_blocked:
        if request.endpoint not in ['blocked', 'logout']:
            return redirect(url_for('blocked'))

@app.context_processor
def inject_language():
    return dict(
        get_text=get_text, 
        countries=list(COUNTRIES_CITIES.keys()),
        COUNTRIES_CITIES=COUNTRIES_CITIES,
        SITE_NAME=SITE_NAME
    )

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['language'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/get_cities/<country>')
def get_cities(country):
    cities = COUNTRIES_CITIES.get(country, [])
    return jsonify(cities)

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
        user = create_user(username, email, password)
        
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
            user_obj = User(
                id=str(user.id),
                username=user.username,
                email=user.email,
                photo=user.photo,
                country=user.country,
                city=user.city,
                bio=user.bio,
                is_admin=user.is_admin,
                is_blocked=user.is_blocked
            )
            
            login_user(user_obj)
            return redirect(url_for('profile'))
        
        flash(get_text('invalid_credentials'))
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = UserModel.query.get(int(current_user.id))
    if not user:
        flash('User not found')
        return redirect(url_for('home'))
    
    # Get user's current data
    user_fetishes = get_user_fetishes(int(current_user.id))
    user_interests = get_user_interests(int(current_user.id))
    
    user_data = {
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
    
    if request.method == 'POST':
        bio = request.form['bio']
        country = request.form.get('country', '')
        city = request.form.get('city', '')
        
        # Get selected fetishes
        selected_fetishes = request.form.getlist('fetishes')
        # Add custom fetish if provided
        custom_fetish = request.form.get('custom_fetish', '').strip()
        if custom_fetish and custom_fetish not in selected_fetishes:
            selected_fetishes.append(custom_fetish)
            
        # Get selected interests
        selected_interests = request.form.getlist('interests')
        # Add custom interest if provided
        custom_interest = request.form.get('custom_interest', '').strip()
        if custom_interest and custom_interest not in selected_interests:
            selected_interests.append(custom_interest)
        
        # Handle photo upload
        photo_filename = user.photo
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{current_user.id}_{uuid.uuid4().hex}.{extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                photo_filename = filename
        
        # Update user data
        update_user_profile(int(current_user.id), bio, country, city, photo_filename)
        add_user_fetishes(int(current_user.id), selected_fetishes)
        add_user_interests(int(current_user.id), selected_interests)
        
        # Update current user object
        current_user.bio = bio
        current_user.country = country
        current_user.city = city
        current_user.photo = photo_filename
        
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', 
                         fetishes=COMMON_FETISHES, 
                         interests=COMMON_INTERESTS,
                         countries=COUNTRIES_CITIES.keys(),
                         user_data=user_data)

@app.route('/profile')
@app.route('/profile/<user_id>')
@login_required
def profile(user_id=None):
    # If no user_id specified, show current user's profile
    if user_id is None:
        user_id = current_user.id
    
    try:
        user_id_int = int(user_id)
        user = UserModel.query.get(user_id_int)
    except (ValueError, TypeError):
        user = UserModel.query.filter_by(username=user_id).first()
        if user:
            user_id_int = user.id
        else:
            flash('User not found!')
            return redirect(url_for('home'))
    
    if not user:
        flash('User not found!')
        return redirect(url_for('home'))
    
    # Get user's fetishes and interests
    user_fetishes = get_user_fetishes(user_id_int)
    user_interests = get_user_interests(user_id_int)
    
    user_data = {
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
    
    # If viewing own profile, check if it's complete
    if str(user_id_int) == current_user.id:
        is_complete = bool(user.country and user.city)
        return render_template('profile.html', user_data=user_data, is_complete=is_complete)
    
    # Viewing another user's profile
    return render_template('profile.html', user_data=user_data, is_complete=True)

@app.route('/users')
@login_required
def users():
    db_users = UserModel.query.all()
    users = {}
    for user in db_users:
        user_fetishes = get_user_fetishes(user.id)
        user_interests = get_user_interests(user.id)
        users[str(user.id)] = {
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
    return render_template('users.html', users=users)

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
        user_fetishes = get_user_fetishes(user.id)
        user_interests = get_user_interests(user.id)
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
    
    if action == 'like':
        add_match(int(current_user.id), int(user2))
    
    return jsonify({'status': 'success'})

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
    
    users = load_users()
    return render_template('admin.html', users=users)

@app.route('/admin/block_user/<user_id>', methods=['POST'])
@login_required
def admin_block_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    try:
        user_id_int = int(user_id)
        reason = request.form.get('reason', 'Violation of terms of service')
        if block_user(user_id_int, reason):
            user = UserModel.query.get(user_id_int)
            if user:
                flash(f'User {user.username} has been blocked')
            else:
                flash('User blocked')
        else:
            flash('Error blocking user')
    except (ValueError, TypeError):
        flash('Invalid user ID')
    
    return redirect(url_for('admin'))

@app.route('/admin/unblock_user/<user_id>', methods=['POST'])
@login_required
def admin_unblock_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    try:
        user_id_int = int(user_id)
        if unblock_user(user_id_int):
            user = UserModel.query.get(user_id_int)
            if user:
                flash(f'User {user.username} has been unblocked')
            else:
                flash('User unblocked')
        else:
            flash('Error unblocking user')
    except (ValueError, TypeError):
        flash('Invalid user ID')
    
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    try:
        user_id_int = int(user_id)
        user = UserModel.query.get(user_id_int)
        if user:
            username = user.username
            if delete_user(user_id_int):
                flash(f'User {username} has been deleted')
            else:
                flash('Error deleting user')
        else:
            flash('User not found')
    except (ValueError, TypeError):
        flash('Invalid user ID')
    
    return redirect(url_for('admin'))

@app.route('/admin/make_admin/<user_id>', methods=['POST'])
@login_required
def admin_make_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    try:
        user_id_int = int(user_id)
        user = UserModel.query.get(user_id_int)
        if user:
            if make_admin(user_id_int):
                flash(f'User {user.username} is now an admin')
            else:
                flash('Error making user admin')
        else:
            flash('User not found')
    except (ValueError, TypeError):
        flash('Invalid user ID')
    
    return redirect(url_for('admin'))

def create_tables():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we need to migrate existing data
        if os.path.exists('users.json'):
            migrate_from_json()

def migrate_from_json():
    """Migrate data from JSON files to database"""
    if os.path.exists('users.json'):
        try:
            with open('users.json', 'r') as f:
                users_data = json.load(f)
            
            for user_id, user_data in users_data.items():
                # Check if user already exists
                existing_user = UserModel.query.filter_by(username=user_data.get('username')).first()
                if not existing_user:
                    user = UserModel(
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        country=user_data.get('country'),
                        city=user_data.get('city'),
                        bio=user_data.get('bio'),
                        is_admin=user_data.get('is_admin', False),
                        is_blocked=user_data.get('is_blocked', False),
                        blocked_reason=user_data.get('blocked_reason')
                    )
                    user.set_password('temp')  # Temporary password, user will need to reset
                    db.session.add(user)
                    db.session.commit()
                    
                    # Add fetishes
                    for fetish_name in user_data.get('fetishes', []):
                        fetish = Fetish(name=fetish_name, user_id=user.id)
                        db.session.add(fetish)
                    
                    # Add interests
                    for interest_name in user_data.get('interests', []):
                        interest = Interest(name=interest_name, user_id=user.id)
                        db.session.add(interest)
            
            db.session.commit()
            print("Data migration completed successfully")
        except Exception as e:
            print(f"Error during data migration: {e}")

if __name__ == '__main__':
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
    
    # Create database tables
    create_tables()
    
    # For Render and other hosting platforms
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)