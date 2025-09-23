import json
import os
from datetime import datetime
from app import db, UserModel, Fetish, Interest, Match, Message

def export_data_to_json():
    """Экспорт всех данных в JSON файл"""
    data = {
        'users': [],
        'fetishes': [],
        'interests': [],
        'matches': [],
        'messages': []
    }
    
    # Экспорт пользователей
    users = UserModel.query.all()
    for user in users:
        data['users'].append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'photo': user.photo,
            'country': user.country,
            'city': user.city,
            'bio': user.bio,
            'is_admin': user.is_admin,
            'is_blocked': user.is_blocked,
            'blocked_reason': user.blocked_reason,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    
    # Экспорт фетишей
    fetishes = Fetish.query.all()
    for fetish in fetishes:
        data['fetishes'].append({
            'id': fetish.id,
            'name': fetish.name,
            'user_id': fetish.user_id
        })
    
    # Экспорт интересов
    interests = Interest.query.all()
    for interest in interests:
        data['interests'].append({
            'id': interest.id,
            'name': interest.name,
            'user_id': interest.user_id
        })
    
    # Экспорт матчей
    matches = Match.query.all()
    for match in matches:
        data['matches'].append({
            'id': match.id,
            'user_id': match.user_id,
            'matched_user_id': match.matched_user_id,
            'created_at': match.created_at.isoformat() if match.created_at else None
        })
    
    # Экспорт сообщений
    messages = Message.query.all()
    for message in messages:
        data['messages'].append({
            'id': message.id,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat() if message.timestamp else None,
            'is_read': message.is_read
        })
    
    # Сохранение в файл
    with open('data_backup.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Экспортировано: {len(users)} пользователей, {len(fetishes)} фетишей, {len(interests)} интересов, {len(matches)} матчей, {len(messages)} сообщений")

def import_data_from_json():
    """Импорт данных из JSON файла"""
    if not os.path.exists('data_backup.json'):
        print("Файл data_backup.json не найден")
        return
    
    with open('data_backup.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Импорт пользователей
    for user_data in data['users']:
        # Проверяем, существует ли уже пользователь
        existing_user = UserModel.query.get(user_data['id'])
        if not existing_user:
            user = UserModel(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                photo=user_data['photo'],
                country=user_data['country'],
                city=user_data['city'],
                bio=user_data['bio'],
                is_admin=user_data['is_admin'],
                is_blocked=user_data['is_blocked'],
                blocked_reason=user_data['blocked_reason']
            )
            if user_data['created_at']:
                user.created_at = datetime.fromisoformat(user_data['created_at'])
            db.session.add(user)
    
    # Импорт фетишей
    for fetish_data in data['fetishes']:
        existing_fetish = Fetish.query.get(fetish_data['id'])
        if not existing_fetish:
            fetish = Fetish(
                id=fetish_data['id'],
                name=fetish_data['name'],
                user_id=fetish_data['user_id']
            )
            db.session.add(fetish)
    
    # Импорт интересов
    for interest_data in data['interests']:
        existing_interest = Interest.query.get(interest_data['id'])
        if not existing_interest:
            interest = Interest(
                id=interest_data['id'],
                name=interest_data['name'],
                user_id=interest_data['user_id']
            )
            db.session.add(interest)
    
    # Импорт матчей
    for match_data in data['matches']:
        # Проверяем, существует ли уже такой матч
        existing_match = Match.query.filter_by(
            user_id=match_data['user_id'],
            matched_user_id=match_data['matched_user_id']
        ).first()
        if not existing_match:
            match = Match(
                id=match_data['id'],
                user_id=match_data['user_id'],
                matched_user_id=match_data['matched_user_id']
            )
            if match_data['created_at']:
                match.created_at = datetime.fromisoformat(match_data['created_at'])
            db.session.add(match)
    
    # Импорт сообщений
    for message_data in data['messages']:
        existing_message = Message.query.get(message_data['id'])
        if not existing_message:
            message = Message(
                id=message_data['id'],
                sender_id=message_data['sender_id'],
                recipient_id=message_data['recipient_id'],
                content=message_data['content'],
                is_read=message_data['is_read']
            )
            if message_data['timestamp']:
                message.timestamp = datetime.fromisoformat(message_data['timestamp'])
            db.session.add(message)
    
    try:
        db.session.commit()
        print(f"Импортировано: {len(data['users'])} пользователей, {len(data['fetishes'])} фетишей, {len(data['interests'])} интересов, {len(data['matches'])} матчей, {len(data['messages'])} сообщений")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при импорте данных: {e}")

if __name__ == "__main__":
    # Вы можете запустить этот файл отдельно для экспорта/импорта
    # export_data_to_json()
    # import_data_from_json()
    pass