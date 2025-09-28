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
from models import db, User as UserModel, Fetish, Interest, Match, Message
import hmac
import hashlib

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
        'search': 'Search',
        'search_query': 'Search Query',
        'search_placeholder': 'Search users...',
        'age_range': 'Age Range',
        'min_age': 'Min Age',
        'max_age': 'Max Age',
        'to': 'to',
        'clear_filters': 'Clear Filters',
        'search_results': 'Search Results',
        'search_instructions': 'Use the filters above to search for users',
        'no_users_found': 'No users found matching your criteria',
        'search_error': 'Error loading search results',
        'send_message': 'Send Message',
        'view_profile': 'View Profile',
        'leave_review': 'Leave a Review',
        'write_review': 'Write a Review',
        'rating': 'Rating',
        'review_comment': 'Your Comment',
        'submit_review': 'Submit Review',
        'user_reviews': 'User Reviews',
        'no_reviews_yet': 'No reviews yet',
        'average_rating': 'Average Rating',
        'your_review': 'Your Review',
        'edit_review': 'Edit Review',
        'delete_review': 'Delete Review',
        'reviews': 'reviews',
        'please_select_rating': 'Please select a rating',
        'review_too_short': 'Review should be at least 10 characters',
        'review_submitted_successfully': 'Review submitted successfully',
        'error_submitting_review': 'Error submitting review',
        'about_me_video': 'Video about me',
        'relationship_goals': 'Relationship goals',
        'lifestyle': 'Lifestyle',
        'diet': 'Diet',
        'smoking': 'Smoking',
        'drinking': 'Drinking',
        'occupation': 'Occupation',
        'education': 'Education',
        'children': 'Children',
        'pets': 'Pets',
        'additional_photos': 'Additional Photos',
        'upload_photos': 'Upload Photos',
        'set_primary_photo': 'Set as primary',
        'delete_photo': 'Delete',
        'premium_photos': 'Premium Photos',
        'premium_photos_desc': 'These photos will only be visible to premium users',\n        'add_photo_description': 'Add photo description',\n        'save_changes': 'Save Changes',\n        'extended_profile': 'Extended Profile',\n        'select_option': 'Select option',\n        'long_term_relationship': 'Long-term relationship',\n        'short_term_fun': 'Short-term fun',\n        'marriage': 'Marriage',\n        'friends': 'Friends',\n        'open_relationship': 'Open relationship',\n        'active': 'Active',\n        'sedentary': 'Sedentary',\n        'moderate': 'Moderate',\n        'very_active': 'Very Active',\n        'vegetarian': 'Vegetarian',\n        'vegan': 'Vegan',\n        'omnivore': 'Omnivore',\n        'pescatarian': 'Pescatarian',\n        'keto': 'Keto',\n        'paleo': 'Paleo',\n        'never': 'Never',\n        'occasionally': 'Occasionally',\n        'socially': 'Socially',\n        'regularly': 'Regularly',\n        'none': 'None',\n        'yes': 'Yes',\n        'want_someday': 'Want someday',\n        'dont_want': 'Don\'t want',\n        'comma_separated': 'comma separated',\n        'ctrl_click_multiple': 'Ctrl+Click to select multiple files',\n        'current_photos': 'Current Photos',\n        'primary': 'Primary',\n        'premium': 'Premium',\n        'update_profile': 'Update Profile'\n    },
    'ru': {
        'welcome': 'Добро пожаловать в FetFinder!',
        'find_match': 'Найдите свою идеальную пару',
        'description': 'FetFinder - это современная платформа для знакомств, где вы можете найти совпадения по общим интересам и фетишам.',
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
        'mark_all_read': 'Отметить все как прочитанные',
        'no_notifications': 'Пока нет уведомлений',
        'search': 'Поиск',
        'search_query': 'Поисковый запрос',
        'search_placeholder': 'Поиск пользователей...',
        'age_range': 'Возрастной диапазон',
        'min_age': 'Мин. возраст',
        'max_age': 'Макс. возраст',
        'to': 'до',
        'clear_filters': 'Очистить фильтры',
        'search_results': 'Результаты поиска',
        'search_instructions': 'Используйте фильтры выше для поиска пользователей',
        'no_users_found': 'Не найдено пользователей, соответствующих критериям',
        'search_error': 'Ошибка при загрузке результатов поиска',
        'send_message': 'Отправить сообщение',
        'view_profile': 'Просмотреть профиль',
        'leave_review': 'Оставить отзыв',
        'write_review': 'Написать отзыв',
        'rating': 'Рейтинг',
        'review_comment': 'Ваш комментарий',
        'submit_review': 'Отправить отзыв',
        'user_reviews': 'Отзывы пользователя',
        'no_reviews_yet': 'Пока нет отзывов',
        'average_rating': 'Средний рейтинг',
        'your_review': 'Ваш отзыв',
        'edit_review': 'Редактировать отзыв',
        'delete_review': 'Удалить отзыв',
        'reviews': 'отзывов',
        'please_select_rating': 'Пожалуйста, выберите рейтинг',
        'review_too_short': 'Отзыв должен содержать не менее 10 символов',
        'review_submitted_successfully': 'Отзыв успешно отправлен',
        'error_submitting_review': 'Ошибка при отправке отзыва',
        'about_me_video': 'Видео о себе',
        'relationship_goals': 'Цели в отношениях',
        'lifestyle': 'Образ жизни',
        'diet': 'Питание',
        'smoking': 'Курение',
        'drinking': 'Употребление алкоголя',
        'occupation': 'Род занятий',
        'education': 'Образование',
        'children': 'Дети',
        'pets': 'Домашние животные',
        'additional_photos': 'Дополнительные фото',
        'upload_photos': 'Загрузить фото',
        'set_primary_photo': 'Сделать основным',
        'delete_photo': 'Удалить',
        'premium_photos': 'Премиум-фото',
        'premium_photos_desc': 'Эти фото будут видны только премиум-пользователям',
        'add_photo_description': 'Добавить описание к фото',
        'save_changes': 'Сохранить изменения',
        'extended_profile': 'Расширенный профиль',
        'select_option': 'Выберите вариант',
        'long_term_relationship': 'Долгосрочные отношения',
        'short_term_fun': 'Краткосрочное веселье',
        'marriage': 'Брак',
        'friends': 'Дружба',
        'open_relationship': 'Открытые отношения',
        'active': 'Активный',
        'sedentary': 'Малоподвижный',
        'moderate': 'Умеренный',
        'very_active': 'Очень активный',
        'vegetarian': 'Вегетарианец',
        'vegan': 'Веган',
        'omnivore': 'Всеядный',
        'pescatarian': 'Пескатарианец',
        'keto': 'Кето',
        'paleo': 'Палео',
        'never': 'Никогда',
        'occasionally': 'Иногда',
        'socially': 'По случаю',
        'regularly': 'Регулярно',
        'none': 'Нет',
        'yes': 'Да',
        'want_someday': 'Хочу когда-нибудь',
        'dont_want': 'Не хочу',
        'comma_separated': 'через запятую',
        'ctrl_click_multiple': 'Ctrl+Клик для выбора нескольких файлов',
        'current_photos': 'Текущие фото',
        'primary': 'Основное',
        'premium': 'Премиум',
        'update_profile': 'Обновить профиль',
        'primary_photo_set': 'Основное фото установлено',
        'error_setting_primary_photo': 'Ошибка при установке основного фото',
        'confirm_delete_photo': 'Вы уверены, что хотите удалить это фото?',
        'photo_deleted': 'Фото успешно удалено',
        'error_deleting_photo': 'Ошибка при удалении фото',
        'gift_shop': 'Магазин подарков',
        'available_gifts': 'Доступные подарки',
        'send_gift': 'Отправить подарок',
        'gift_message': 'Сообщение к подарку',
        'send_anonymously': 'Отправить анонимно',
        'your_coins': 'Ваши монеты',
        'buy_coins': 'Купить монеты',
        'gift_sent_successfully': 'Подарок успешно отправлен!',
        'error_sending_gift': 'Ошибка при отправке подарка',
        'not_enough_coins': 'Недостаточно монет для отправки этого подарка',
        'my_gifts': 'Мои подарки',
        'received_gifts': 'Полученные подарки',
        'sent_gifts': 'Отправленные подарки',
        'no_gifts_yet': 'Пока нет подарков',
        'view_all_gifts': 'Посмотреть все подарки',
        'gift_categories': 'Категории подарков',
        'all_categories': 'Все категории',
        'free_gifts': 'Бесплатные подарки',
        'premium_gifts': 'Премиум-подарки'
    },
        'current_photos': 'Текущие фото'
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
    
    # Get user's reviews
    user_reviews = Review.query.filter_by(reviewed_user_id=user.id).all()
    avg_rating = sum(r.rating for r in user_reviews) / len(user_reviews) if user_reviews else 0
    
    # Check if current user has reviewed this user
    current_user_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_user_id=user.id
    ).first()
    
    user_data = {
        'username': user.username,
        'email': user.email,
        'photo': user.photo,
        'country': user.country,
        'city': user.city,
        'bio': user.bio,
        'fetishes': user_fetishes,
        'interests': user.interests,
        'created_at': user.created_at.isoformat(),
        'is_premium': is_premium_user(user),
        'avg_rating': round(avg_rating, 1),
        'total_reviews': len(user_reviews),
        'current_review': current_user_review
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
        
        # Update extended profile fields
        current_user.about_me_video = request.form.get('about_me_video')
        current_user.relationship_goals = request.form.get('relationship_goals')
        current_user.lifestyle = request.form.get('lifestyle')
        current_user.diet = request.form.get('diet')
        current_user.smoking = request.form.get('smoking')
        current_user.drinking = request.form.get('drinking')
        current_user.occupation = request.form.get('occupation')
        current_user.education = request.form.get('education')
        current_user.children = request.form.get('children')
        current_user.pets = request.form.get('pets')
        
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
        
        # Handle additional photos upload
        if 'additional_photos' in request.files:
            photos = request.files.getlist('additional_photos')
            for photo in photos:
                if photo and photo.filename != '':
                    # Create unique filename
                    ext = photo.filename.split('.')[-1]
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo.save(filepath)
                    
                    # Create UserPhoto record
                    user_photo = UserPhoto(
                        user_id=current_user.id,
                        photo_path=filename,
                        is_primary=False  # First uploaded photo will be set as primary below
                    )
                    db.session.add(user_photo)
        
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
    
    # Get user's additional photos
    user_photos = UserPhoto.query.filter_by(user_id=current_user.id).all()
    
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
        'about_me_video': current_user.about_me_video,
        'relationship_goals': current_user.relationship_goals,
        'lifestyle': current_user.lifestyle,
        'diet': current_user.diet,
        'smoking': current_user.smoking,
        'drinking': current_user.drinking,
        'occupation': current_user.occupation,
        'education': current_user.education,
        'children': current_user.children,
        'pets': current_user.pets,
        'photos': user_photos
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


@app.route('/search')
@login_required
def search():
    # Get all countries and cities for filter options
    countries_cities = {
        'Russia': ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg'],
        'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston'],
        'UK': ['London', 'Birmingham', 'Manchester', 'Glasgow'],
        'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne'],
        'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse']
    }
    
    # Get all available fetishes and interests for filter options
    all_fetishes = [f.name for f in Fetish.query.distinct(Fetish.name)]
    all_interests = [i.name for i in Interest.query.distinct(Interest.name)]
    
    return render_template('search.html', 
                          countries=countries_cities.keys(), 
                          cities_by_country=countries_cities,
                          fetishes=all_fetishes,
                          interests=all_interests)


@app.route('/api/users')
@login_required
def api_users():
    try:
        # Get query parameters for filtering
        min_age = request.args.get('min_age', type=int)
        max_age = request.args.get('max_age', type=int)
        country = request.args.get('country')
        city = request.args.get('city')
        fetish_filter = request.args.get('fetish')
        interest_filter = request.args.get('interest')
        search_query = request.args.get('q', '')  # For general search
        
        # Start with base query
        query = UserModel.query.filter(
            UserModel.id != int(current_user.id),
            UserModel.is_blocked == False
        )
        
        # Apply age filter
        if min_age or max_age:
            # Assuming we have a birth_date field or calculate age from registration date
            # For now using a simplified approach based on registration date
            from datetime import datetime, timedelta
            if min_age:
                min_date = datetime.utcnow() - timedelta(days=min_age*365)
                query = query.filter(UserModel.created_at <= min_date)
            if max_age:
                max_date = datetime.utcnow() - timedelta(days=max_age*365)
                query = query.filter(UserModel.created_at >= max_date)
        
        # Apply location filters
        if country:
            query = query.filter(UserModel.country == country)
        if city:
            query = query.filter(UserModel.city == city)
        
        # Apply search query
        if search_query:
            query = query.filter(
                db.or_(
                    UserModel.username.contains(search_query),
                    UserModel.bio.contains(search_query)
                )
            )
        
        db_users = query.all()
        
        users = []
        for user in db_users:
            try:
                user_fetishes = [f.name for f in Fetish.query.filter_by(user_id=user.id).all()]
                user_interests = [i.name for i in Interest.query.filter_by(user_id=user.id).all()]
                
                # Apply fetish and interest filters after getting all users
                if fetish_filter and fetish_filter not in user_fetishes:
                    continue
                if interest_filter and interest_filter not in user_interests:
                    continue
                
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
        
        print(f"Returning {len(users)} users for search")
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
    if not is_premium_user(current_user):
        return jsonify({
            'status': 'error', 
            'error': 'Undo swipe is a premium feature'
        })
    
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
    
    # Check message limit for non-premium users
    if not is_premium_user(current_user):
        messages_today_count = messages_today(current_user.id)
        if messages_today_count >= 1:  # Limit to 1 message per day for free users
            return jsonify({
                'status': 'error', 
                'error': 'Free users can only send 1 message per day. Upgrade to Premium for unlimited messaging!'
            })
    
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
    """Check if user has reached their daily message limit"""
    if is_premium_user(current_user):
        return jsonify({'status': 'success', 'limit_reached': False})
    
    # Check how many messages user has sent today
    messages_today_count = messages_today(current_user.id)
    if messages_today_count >= 1:
        return jsonify({'status': 'error', 'limit_reached': True, 'message': 'Daily message limit reached'})
    
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


@app.route('/subscribe_premium', methods=['POST'])
@login_required
def subscribe_premium():
    from payment_config import InterKassaConfig
    
    try:
        # Создаем экземпляр конфигурации InterKassa
        ik_config = InterKassaConfig()
        
        # Генерируем уникальный ID заказа
        order_id = f"premium_{current_user.id}_{int(datetime.utcnow().timestamp())}"
        
        # Создаем данные для формы оплаты
        form_data = ik_config.create_payment_form(
            order_id=order_id,
            amount=4.99,  # Стоимость премиум-подписки
            description="Premium subscription for FetFinder",
            user_email=current_user.email,
            user_id=current_user.id
        )
        
        # Сохраняем ID заказа в сессии для последующей проверки
        session['pending_order_id'] = order_id
        
        return render_template('interkassa_payment.html', form_data=form_data)
        
    except Exception as e:
        flash(f'Error creating payment form: {str(e)}')
        return redirect(url_for('premium'))

@app.route('/premium_success')
@login_required
def premium_success():
    # Эта страница показывается после успешного возврата из InterKassa
    # Но подписка устанавливается через вебхук
    flash('Payment successful! Your premium status will be updated shortly.')
    return redirect(url_for('profile'))


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
    # In a real application, you would handle cancellation with a payment provider
    # For now, we'll just remove the premium status
    current_user.is_premium = False
    current_user.premium_expires = None
    db.session.commit()
    flash('Your premium subscription has been cancelled.')
    
    return redirect(url_for('profile'))

@app.route('/interkassa_webhook', methods=['POST'])
def interkassa_webhook():
    """Обработка вебхуков от InterKassa"""
    from payment_config import InterKassaConfig
    
    try:
        # Проверяем подпись
        ik_config = InterKassaConfig()
        is_valid = ik_config.verify_payment(request.form)
        
        if not is_valid:
            print("Invalid signature from InterKassa webhook")
            return 'Invalid signature', 400
        
        # Получаем данные из запроса
        order_id = request.form.get('ik_inv_id')
        user_id = request.form.get('user_id')
        status = request.form.get('ik_inv_st', 'pending')  # Статус заказа
        
        if status == 'success' and user_id:
            # Обновляем статус пользователя
            user = UserModel.query.get(int(user_id))
            if user:
                user.is_premium = True
                user.premium_expires = datetime.utcnow() + timedelta(days=30)  # 30 дней премиум
                db.session.commit()
                
                print(f"Premium status updated for user {user_id}")
        
        # Возвращаем ответ, подтверждающий получение вебхука
        return 'OK', 200
        
    except Exception as e:
        print(f"Error processing InterKassa webhook: {str(e)}")
        return 'Error', 500


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

@app.route('/api/notifications')
@login_required
def api_notifications():
    """Получение уведомлений пользователя"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc())
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify([{
        'id': n.id,
        'type': n.type,
        'title': n.title,
        'content': n.content,
        'is_read': n.is_read,
        'timestamp': n.timestamp.isoformat(),
        'url': n.url,
        'sender': {
            'id': n.sender.id,
            'username': n.sender.username,
            'photo': n.sender.photo
        } if n.sender else None
    } for n in notifications.items])


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Отметить уведомление как прочитанное"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Отметить все уведомления как прочитанные"""
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/photo/<int:photo_id>/set_primary', methods=['POST'])
@login_required
def set_primary_photo(photo_id):
    """Установить фото как основное"""
    photo = UserPhoto.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
    
    # Сбросить все другие фото как неосновные
    UserPhoto.query.filter_by(user_id=current_user.id).update({'is_primary': False})
    
    # Установить выбранное фото как основное
    photo.is_primary = True
    db.session.commit()
    
    # Также обновить основную фотографию пользователя
    current_user.photo = photo.photo_path
    db.session.commit()
    
    return jsonify({'status': 'success'})


@app.route('/api/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Удалить фото"""
    photo = UserPhoto.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
    
    # Удалить файл с диска
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_path)
    if os.path.exists(photo_path):
        os.remove(photo_path)
    
    # Удалить запись из базы данных
    db.session.delete(photo)
    db.session.commit()
    
    return jsonify({'status': 'success'})


@app.route('/api/reviews/<int:user_id>')
@login_required
def api_user_reviews(user_id):
    """Получить отзывы о пользователе"""
    reviews = Review.query.filter_by(reviewed_user_id=user_id).all()
    
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'reviewer': {
                'id': review.reviewer.id,
                'username': review.reviewer.username,
                'photo': review.reviewer.photo
            },
            'rating': review.rating,
            'comment': review.comment,
            'timestamp': review.timestamp.isoformat()
        })
    
    # Calculate average rating
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    
    return jsonify({
        'reviews': reviews_data,
        'average_rating': round(avg_rating, 1),
        'total_reviews': len(reviews)
    })


@app.route('/api/review', methods=['POST'])
@login_required
def api_create_review():
    """Создать или обновить отзыв"""
    data = request.get_json()
    reviewed_user_id = data.get('reviewed_user_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not reviewed_user_id or not rating or not 1 <= rating <= 5:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Check if user is trying to review themselves
    if int(reviewed_user_id) == current_user.id:
        return jsonify({'error': 'Cannot review yourself'}), 400
    
    # Check if review already exists
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id
    ).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
    else:
        review = Review(
            reviewer_id=current_user.id,
            reviewed_user_id=reviewed_user_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
    
    db.session.commit()
    
    return jsonify({'status': 'success'})


@app.route('/api/review/<int:review_id>', methods=['DELETE'])
@login_required
def api_delete_review(review_id):
    """Удалить отзыв"""
    review = Review.query.filter_by(id=review_id, reviewer_id=current_user.id).first_or_404()
    db.session.delete(review)
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/photo/<int:photo_id>/set_primary', methods=['POST'])
@login_required
def set_primary_photo(photo_id):
    """Установить фото как основное"""
    photo = UserPhoto.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
    
    # Сбросить все другие фото как неосновные
    UserPhoto.query.filter_by(user_id=current_user.id).update({'is_primary': False})
    
    # Установить выбранное фото как основное
    photo.is_primary = True
    db.session.commit()
    
    # Также обновить основную фотографию пользователя
    current_user.photo = photo.photo_path
    db.session.commit()
    
    return jsonify({'status': 'success'})


@app.route('/api/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Удалить фото"""
    photo = UserPhoto.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
    
    # Удалить файл с диска
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_path)
    if os.path.exists(photo_path):
        os.remove(photo_path)
    
    # Удалить запись из базы данных
    db.session.delete(photo)
    db.session.commit()
    
    return jsonify({'status': 'success'})


@app.route('/gifts')
@login_required
def gift_shop():
    """Магазин подарков"""
    # Получить все доступные подарки
    gifts = Gift.query.filter_by(is_active=True).all()
    
    # Получить категории подарков
    categories = db.session.query(Gift.category).filter(Gift.is_active == True).distinct().all()
    categories = [c[0] for c in categories if c[0]]  # Извлечь категории из кортежей
    
    # Получить количество монет пользователя
    user_coins = current_user.coins
    
    return render_template('gift_shop.html', 
                          gifts=gifts, 
                          categories=categories, 
                          user_coins=user_coins)


@app.route('/api/gifts')
@login_required
def api_gifts():
    """API для получения подарков"""
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    
    query = Gift.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if min_price is not None:
        query = query.filter(Gift.price_coins >= min_price)
    
    if max_price is not None:
        query = query.filter(Gift.price_coins <= max_price)
    
    gifts = query.all()
    
    return jsonify([{
        'id': gift.id,
        'name': gift.name,
        'description': gift.description,
        'image_url': gift.image_url,
        'price_coins': gift.price_coins,
        'category': gift.category,
        'is_premium_only': gift.is_premium_only
    } for gift in gifts])


@app.route('/api/send_gift', methods=['POST'])
@login_required
def api_send_gift():
    """API для отправки подарка"""
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    gift_id = data.get('gift_id')
    message = data.get('message', '')
    is_anonymous = data.get('is_anonymous', False)
    
    if not recipient_id or not gift_id:
        return jsonify({'error': 'Missing recipient_id or gift_id'}), 400
    
    # Проверить, существует ли получатель
    recipient = UserModel.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
    
    # Проверить, существует ли подарок
    gift = Gift.query.get(gift_id)
    if not gift:
        return jsonify({'error': 'Gift not found'}), 404
    
    # Проверить, достаточно ли монет у отправителя
    if current_user.coins < gift.price_coins:
        return jsonify({'error': 'Not enough coins'}), 400
    
    # Списать монеты у отправителя
    current_user.coins -= gift.price_coins
    
    # Создать запись о подарке
    user_gift = UserGift(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        gift_id=gift_id,
        message=message,
        is_anonymous=is_anonymous
    )
    
    db.session.add(user_gift)
    db.session.commit()
    
    # Создать уведомление для получателя
    create_notification(
        user_id=recipient_id,
        sender_id=current_user.id,
        type='gift',
        title='New Gift Received',
        content=f'You received a gift from {current_user.username if not is_anonymous else "Anonymous"}',
        url=url_for('my_gifts')
    )
    
    return jsonify({'status': 'success'})


@app.route('/my_gifts')
@login_required
def my_gifts():
    """Мои подарки (полученные и отправленные)"""
    # Получить полученные подарки
    received_gifts = UserGift.query.filter_by(recipient_id=current_user.id).order_by(UserGift.timestamp.desc()).all()
    
    # Получить отправленные подарки
    sent_gifts = UserGift.query.filter_by(sender_id=current_user.id).order_by(UserGift.timestamp.desc()).all()
    
    return render_template('my_gifts.html', 
                          received_gifts=received_gifts, 
                          sent_gifts=sent_gifts)


# Existing functions continue here...