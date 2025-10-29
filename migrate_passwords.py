from werkzeug.security import generate_password_hash
import hashlib

def migrate_password_if_needed(user, password):
    """
    Мигрирует пароль пользователя со старого формата (SHA-256) на новый (werkzeug)
    если текущий пароль подходит, но закодирован старым способом
    """
    # Проверим, является ли хэш старого формата
    old_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if user.password_hash == old_hash:
        # Это старый формат, нужно обновить хэш до нового безопасного формата
        new_hash = generate_password_hash(password)
        
        # Обновим хэш в сессии базы данных
        user.password_hash = new_hash
        from app import db
        db.session.commit()
        print(f"Пароль пользователя {user.username} обновлён до нового безопасного формата")