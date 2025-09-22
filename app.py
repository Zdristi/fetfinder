from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import hashlib

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)

# Set secret key if not configured
if not app.config.get('SECRET_KEY'):
    app.secret_key = 'your-secret-key-here-change-this-in-production'
else:
    app.secret_key = app.config['SECRET_KEY']

# Site configuration
SITE_NAME = 'FetFinder'

# Configuration
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'static/uploads')
DATABASE_FILE = app.config.get('DATABASE_FILE', 'users.json')
MATCHES_FILE = app.config.get('MATCHES_FILE', 'matches.json')

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
    users = load_users()
    user_data = users.get(user_id)
    if user_data:
        return User(
            id=user_id,
            username=user_data.get('username', user_id),
            email=user_data.get('email'),
            photo=user_data.get('photo'),
            country=user_data.get('country'),
            city=user_data.get('city'),
            bio=user_data.get('bio'),
            is_admin=user_data.get('is_admin', False),
            is_blocked=user_data.get('is_blocked', False),
            blocked_reason=user_data.get('blocked_reason')
        )
    return None

# Country and city data
COUNTRIES_CITIES = {
    "Russia": ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod", "Chelyabinsk", "Samara", "Omsk", "Rostov-on-Don"],
    "USA": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"],
    "UK": ["London", "Birmingham", "Leeds", "Glasgow", "Sheffield", "Bradford", "Liverpool", "Manchester", "Edinburgh", "Bristol"],
    "Germany": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Dusseldorf", "Leipzig", "Dortmund", "Essen"],
    "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille"]
}

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_matches():
    if os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_matches(matches):
    with open(MATCHES_FILE, 'w') as f:
        json.dump(matches, f, indent=2)

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
        
        users = load_users()
        
        # Check if username already exists
        for user_id, user_data in users.items():
            if user_data.get('username') == username:
                flash(get_text('username_exists'))
                return redirect(url_for('register'))
        
        # Create new user
        user_id = str(uuid.uuid4())
        
        # Check if this is the first user (make them admin)
        is_admin = len(users) == 0
        
        users[user_id] = {
            'username': username,
            'email': email,
            'password': hash_password(password),
            'photo': '',
            'country': '',
            'city': '',
            'bio': '',
            'fetishes': [],
            'interests': [],
            'is_admin': is_admin,
            'is_blocked': False,
            'created_at': datetime.now().isoformat()
        }
        
        save_users(users)
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
        hashed_password = hash_password(password)
        
        users = load_users()
        
        # Find user
        for user_id, user_data in users.items():
            if user_data.get('username') == username and user_data.get('password') == hashed_password:
                # Log in the user
                user = User(
                    id=user_id,
                    username=user_data.get('username', ''),
                    email=user_data.get('email', ''),
                    photo=user_data.get('photo', ''),
                    country=user_data.get('country', ''),
                    city=user_data.get('city', ''),
                    bio=user_data.get('bio', '')
                )
                
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

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    users = load_users()
    user_data = users.get(current_user.id, {})
    
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
        photo_filename = user_data.get('photo')
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
        users[current_user.id] = {
            'username': user_data.get('username', ''),
            'email': user_data.get('email', ''),
            'password': user_data.get('password', ''),
            'photo': photo_filename,
            'country': country,
            'city': city,
            'bio': bio,
            'fetishes': selected_fetishes,
            'interests': selected_interests,
            'created_at': user_data.get('created_at', datetime.now().isoformat())
        }
        
        save_users(users)
        
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
    
    users = load_users()
    if user_id not in users:
        flash('User not found!')
        return redirect(url_for('home'))
    
    user_data = users[user_id]
    
    # If viewing own profile, check if it's complete
    if user_id == current_user.id:
        is_complete = bool(user_data.get('country') and user_data.get('city'))
        return render_template('profile.html', user_data=user_data, is_complete=is_complete)
    
    # Viewing another user's profile
    return render_template('profile.html', user_data=user_data, is_complete=True)

@app.route('/users')
@login_required
def users():
    users = load_users()
    return render_template('users.html', users=users)

@app.route('/swipe')
@login_required
def swipe():
    return render_template('swipe.html')

@app.route('/api/users')
@login_required
def api_users():
    users = load_users()
    # Remove current user from the list
    other_users = {k: v for k, v in users.items() if k != current_user.id}
    return jsonify(list(other_users.items()))

@app.route('/api/match', methods=['POST'])
@login_required
def api_match():
    data = request.get_json()
    user2 = data.get('user2')
    action = data.get('action')  # 'like' or 'dislike'
    
    if action == 'like':
        matches = load_matches()
        if current_user.id not in matches:
            matches[current_user.id] = []
        if user2 not in matches[current_user.id]:
            matches[current_user.id].append(user2)
        save_matches(matches)
    
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
def block_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    users = load_users()
    if user_id in users:
        reason = request.form.get('reason', 'Violation of terms of service')
        users[user_id]['is_blocked'] = True
        users[user_id]['blocked_reason'] = reason
        users[user_id]['blocked_by'] = current_user.id
        users[user_id]['blocked_at'] = datetime.now().isoformat()
        save_users(users)
        flash(f'User {users[user_id].get("username")} has been blocked')
    else:
        flash('User not found')
    
    return redirect(url_for('admin'))

@app.route('/admin/unblock_user/<user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    users = load_users()
    if user_id in users:
        users[user_id]['is_blocked'] = False
        users[user_id].pop('blocked_reason', None)
        users[user_id].pop('blocked_by', None)
        users[user_id].pop('blocked_at', None)
        save_users(users)
        flash(f'User {users[user_id].get("username")} has been unblocked')
    else:
        flash('User not found')
    
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    users = load_users()
    if user_id in users:
        username = users[user_id].get('username')
        del users[user_id]
        save_users(users)
        flash(f'User {username} has been deleted')
    else:
        flash('User not found')
    
    return redirect(url_for('admin'))

@app.route('/admin/make_admin/<user_id>', methods=['POST'])
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    users = load_users()
    if user_id in users:
        users[user_id]['is_admin'] = True
        save_users(users)
        flash(f'User {users[user_id].get("username")} is now an admin')
    else:
        flash('User not found')
    
    return redirect(url_for('admin'))

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
    
    # For Render and other hosting platforms
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)