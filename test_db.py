from app import app
from models import db

def test_db_connection():
    """Тест подключения к базе данных и наличия таблиц"""
    with app.app_context():
        try:
            # Проверяем подключение к базе данных
            db.create_all()  # Это создаст таблицы, если они не существуют
            print("Успешно подключились к базе данных и создали таблицы")
            
            # Попробуем получить список пользователей, чтобы проверить, что таблица существует
            from models import User
            users = User.query.all()
            print(f"Количество пользователей в базе: {len(users)}")
            
            # Попробуем получить список фетишей
            from models import Fetish
            fetishes = Fetish.query.all()
            print(f"Количество фетишей в базе: {len(fetishes)}")
            
            # Попробуем получить список интересов
            from models import Interest
            interests = Interest.query.all()
            print(f"Количество интересов в базе: {len(interests)}")
            
            print("Тестирование базы данных прошло успешно")
            
        except Exception as e:
            print(f"Ошибка при тестировании базы данных: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_db_connection()