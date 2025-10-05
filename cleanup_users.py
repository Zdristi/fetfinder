import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db, app
from models import UserModel

def cleanup_users():
    """Удаляет всех пользователей из базы данных, кроме Zdristi"""
    with app.app_context():
        try:
            print("Начинаем очистку пользователей...")
            
            # Найдем ID пользователя Zdristi
            zdristi_user = UserModel.query.filter_by(username='Zdristi').first()
            
            if not zdristi_user:
                print("Пользователь Zdristi не найден в базе данных!")
                return
            
            print(f"Найден пользователь Zdristi с ID: {zdristi_user.id}")
            
            # Удаляем всех пользователей, кроме Zdristi
            deleted_count = db.session.execute(
                db.text('DELETE FROM "user" WHERE username != :username'),
                {"username": "Zdristi"}
            )
            
            db.session.commit()
            print(f"Успешно удалены все пользователи, кроме Zdristi")
            
        except Exception as e:
            print(f"Ошибка при удалении пользователей: {e}")
            db.session.rollback()

if __name__ == "__main__":
    cleanup_users()