from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import hashlib

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    photo = db.Column(db.String(200), nullable=True)  # Основная фотография профиля
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    
    # Добавим поля для видео-презентации
    about_me_video = db.Column(db.String(200), nullable=True)  # Путь к видео-презентации
    
    # Добавим поля для дополнительной информации
    relationship_goals = db.Column(db.String(200), nullable=True)  # Цели отношений
    lifestyle = db.Column(db.String(200), nullable=True)  # Образ жизни
    diet = db.Column(db.String(100), nullable=True)  # Диета
    smoking = db.Column(db.String(100), nullable=True)  # Отношение к курению
    drinking = db.Column(db.String(100), nullable=True)  # Отношение к алкоголю
    occupation = db.Column(db.String(100), nullable=True)  # Род занятий
    education = db.Column(db.String(100), nullable=True)  # Образование
    children = db.Column(db.String(100), nullable=True)  # Дети
    pets = db.Column(db.String(100), nullable=True)  # Домашние животные
    
    # Премиум статус
    is_premium = db.Column(db.Boolean, default=False)
    premium_expires = db.Column(db.DateTime, nullable=True)
    
    # Виртуальная валюта (монеты)
    coins = db.Column(db.Integer, default=0)
    
    # Настройки геолокации для поиска
    match_by_city = db.Column(db.Boolean, default=False)  # Искать только по городу
    match_by_country = db.Column(db.Boolean, default=False)  # Искать только по стране
    
    # Поля для подтверждения email
    email_confirmed = db.Column(db.Boolean, default=False)
    confirmation_code = db.Column(db.String(6), nullable=True)
    confirmation_code_expires = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fetishes = db.relationship('Fetish', backref='user', lazy=True, cascade='all, delete-orphan')
    interests = db.relationship('Interest', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set user password (hash)"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Check user password"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Fetish(db.Model):
    __tablename__ = 'fetish'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Fetish {self.name}>'


class Interest(db.Model):
    __tablename__ = 'interest'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Interest {self.name}>'


class Match(db.Model):
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Prevent duplicate matches
    __table_args__ = (db.UniqueConstraint('user_id', 'matched_user_id', name='unique_match'),)
    
    def __repr__(self):
        return f'<Match {self.user_id} <-> {self.matched_user_id}>'


class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    
    def __repr__(self):
        return f'<Message from {self.sender_id} to {self.recipient_id}>'


class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # like, match, message, etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    url = db.Column(db.String(300), nullable=True)  # Optional URL to navigate to
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class Gift(db.Model):
    __tablename__ = 'gift'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # Цена в монетах
    icon = db.Column(db.String(100), nullable=True)  # Иконка подарка
    category = db.Column(db.String(50), nullable=True)  # Категория подарка
    
    def __repr__(self):
        return f'<Gift {self.name}>'


class UserGift(db.Model):
    __tablename__ = 'user_gift'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кто отправляет подарок
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кому отправляют подарок
    gift_id = db.Column(db.Integer, db.ForeignKey('gift.id'), nullable=False)  # Какой подарок
    message = db.Column(db.Text)  # Сообщение к подарку
    is_anonymous = db.Column(db.Boolean, default=False)  # Анонимный подарок
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)  # Прочитан ли подарок
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    gift = db.relationship('Gift')
    
    def __repr__(self):
        return f'<UserGift from {self.sender_id} to {self.recipient_id}, gift: {self.gift_id}>'


class SupportTicket(db.Model):
    __tablename__ = 'support_ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='open')  # open, closed, replied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with messages
    messages = db.relationship('SupportMessage', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    # Relationship with user
    user = db.relationship('User', backref='support_tickets', lazy=True)
    
    def __repr__(self):
        return f'<SupportTicket {self.id}: {self.subject}>'


class SupportMessage(db.Model):
    __tablename__ = 'support_message'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # True if sent by admin
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationship with sender
    sender = db.relationship('User', backref='support_messages', lazy=True)
    
    def __repr__(self):
        return f'<SupportMessage {self.id}: {self.content[:50]}>'


class UserSwipe(db.Model):
    __tablename__ = 'user_swipe'
    
    id = db.Column(db.Integer, primary_key=True)
    swiper_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кто свайпнул
    swipee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кого свайпнули
    action = db.Column(db.String(10), nullable=False)  # 'like' или 'dislike'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Уникальное ограничение, чтобы предотвратить дубликаты свайпов
    __table_args__ = (db.UniqueConstraint('swiper_id', 'swipee_id', name='unique_swipe'),)
    
    def __repr__(self):
        return f'<UserSwipe {self.swiper_id}->{self.swipee_id}: {self.action}>'

class Rating(db.Model):
    __tablename__ = 'rating'
    
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stars = db.Column(db.Integer, nullable=False)  # 1-5 stars
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate ratings
    __table_args__ = (db.UniqueConstraint('rater_id', 'rated_user_id', name='unique_user_rating'),)
    
    def __repr__(self):
        return f'<Rating {self.rater_id}->{self.rated_user_id}: {self.stars} stars>'