#!/usr/bin/env python3
"""
Скрипт для создания администратора в базе данных напрямую
Используется в случае проблем с регистрацией/входом
"""
import os
import sys
import hashlib
import secrets

# Добавляем путь к основному приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User as UserModel

def create_admin(username, email, password):
    """Создает администратора напрямую в базе данных"""
    with app.app_context():
        # Проверяем, существует ли уже админ
        existing_admin = UserModel.query.filter_by(is_admin=True).first()
        if existing_admin:
            print(f"Администратор уже существует: {existing_admin.username}")
            return False
        
        # Проверяем, существует ли пользователь с таким именем
        existing_user = UserModel.query.filter_by(username=username).first()
        if existing_user:
            print(f"Пользователь с именем {username} уже существует")
            return False
        
        # Проверяем, существует ли пользователь с таким email
        existing_email = UserModel.query.filter_by(email=email).first()
        if existing_email:
            print(f"Пользователь с email {email} уже существует")
            return False
        
        # Создаем нового администратора с безопасным хешированием пароля
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        full_hash = f"{password_hash}:{salt}"
        
        admin_user = UserModel(
            username=username,
            email=email,
            password_hash=full_hash,
            is_admin=True,
            is_blocked=False,
            email_confirmed=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"Администратор {username} успешно создан")
            return True
        except Exception as e:
            print(f"Ошибка при создании администратора: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin(username, email, password)