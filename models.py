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
    is_premium = db.Column(db.Boolean, default=False)  # Premium subscription
    premium_expires = db.Column(db.DateTime)  # When premium subscription expires
    blocked_reason = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Дополнительные поля для расширенного профиля
    about_me_video = db.Column(db.String(200), nullable=True)  # Ссылка на видео о себе
    relationship_goals = db.Column(db.String(200), nullable=True)  # Цели в отношениях
    lifestyle = db.Column(db.String(200), nullable=True)  # Образ жизни
    diet = db.Column(db.String(100), nullable=True)  # Питание
    smoking = db.Column(db.String(50), nullable=True)  # Отношение к курению
    drinking = db.Column(db.String(50), nullable=True)  # Отношение к алкоголю
    occupation = db.Column(db.String(100), nullable=True)  # Род занятий
    education = db.Column(db.String(100), nullable=True)  # Образование
    children = db.Column(db.String(50), nullable=True)  # Дети
    pets = db.Column(db.String(50), nullable=True)  # Домашние животные
    
    # Виртуальная валюта
    coins = db.Column(db.Integer, default=0)  # Количество монет пользователя
    
    # Relationship with fetishes and interests
    fetishes = db.relationship('Fetish', backref='user', lazy=True)
    interests = db.relationship('Interest', backref='user', lazy=True)
    photos = db.relationship('UserPhoto', backref='user', lazy=True)
    matches = db.relationship('Match', foreign_keys='Match.user_id', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Fetish(db.Model):
    __tablename__ = 'fetish'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Fetish {self.name}>'

class Interest(db.Model):
    __tablename__ = 'interest'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Interest {self.name}>'

class Match(db.Model):
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure we don't have duplicate matches
    __table_args__ = (db.UniqueConstraint('user_id', 'matched_user_id'),)
    
    def __repr__(self):
        return f'<Match {self.user_id} -> {self.matched_user_id}>'

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
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Кто вызвал уведомление
    type = db.Column(db.String(50), nullable=False)  # 'match', 'message', 'like', 'visit'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    url = db.Column(db.String(300), nullable=True)  # URL для перехода
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def __repr__(self):
        return f'<Notification {self.type} for {self.user_id}>'


class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кто оставляет отзыв
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кого оценивают
    rating = db.Column(db.Integer, nullable=False)  # Рейтинг от 1 до 5
    comment = db.Column(db.Text)  # Комментарий
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Уникальность: один пользователь может оставить только один отзыв другому пользователю
    __table_args__ = (db.UniqueConstraint('reviewer_id', 'reviewed_user_id'),)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    reviewed_user = db.relationship('User', foreign_keys=[reviewed_user_id])
    
    def __repr__(self):
        return f'<Review from {self.reviewer_id} to {self.reviewed_user_id}, rating: {self.rating}>'


class UserPhoto(db.Model):
    __tablename__ = 'user_photo'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photo_path = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)  # Описание фото
    is_primary = db.Column(db.Boolean, default=False)  # Основное фото
    is_premium = db.Column(db.Boolean, default=False)  # Только для премиум-пользователей
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('user_photos', lazy=True))
    
    def __repr__(self):
        return f'<UserPhoto {self.photo_path} for user {self.user_id}>'


class Gift(db.Model):
    __tablename__ = 'gift'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)  # Описание подарка
    image_url = db.Column(db.String(200))  # Путь к изображению подарка
    price_coins = db.Column(db.Integer, nullable=False)  # Цена в монетах
    category = db.Column(db.String(50))  # Категория подарка
    is_premium_only = db.Column(db.Boolean, default=False)  # Только для премиум-пользователей
    is_active = db.Column(db.Boolean, default=True)  # Активен ли подарок
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Gift {self.name}, price: {self.price_coins} coins>'


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