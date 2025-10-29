"""
Скрипт миграции для добавления таблиц подарков
"""
import sqlite3
import os

def migrate_database():
    # Подключаемся к базе данных
    db_path = 'fetdate_local.db'
    if not os.path.exists(db_path):
        print("База данных не найдена!")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Проверим, существует ли таблица gift
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gift'")
        if cursor.fetchone() is None:
            # Создаем таблицу gift
            cursor.execute("""
                CREATE TABLE gift (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL,
                    icon TEXT,
                    category TEXT,
                    thumbnail_url TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Таблица gift создана")
        else:
            print("Таблица gift уже существует")
        
        # Проверим, существует ли таблица user_gift
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_gift'")
        if cursor.fetchone() is None:
            # Создаем таблицу user_gift
            cursor.execute("""
                CREATE TABLE user_gift (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    recipient_id INTEGER NOT NULL,
                    gift_id INTEGER NOT NULL,
                    message TEXT,
                    is_anonymous BOOLEAN DEFAULT 0,
                    is_read BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES user(id),
                    FOREIGN KEY (recipient_id) REFERENCES user(id),
                    FOREIGN KEY (gift_id) REFERENCES gift(id)
                )
            """)
            print("Таблица user_gift создана")
        else:
            print("Таблица user_gift уже существует")

        conn.commit()
        print("Миграция таблиц подарков завершена успешно!")
        return True
        
    except sqlite3.Error as e:
        print(f"Ошибка при миграции базы данных: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()