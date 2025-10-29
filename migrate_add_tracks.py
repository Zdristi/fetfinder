"""
Скрипт миграции для добавления таблицы пользовательских треков
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
        # Проверим, существует ли таблица user_track
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_track'")
        if cursor.fetchone() is None:
            # Создаем таблицу user_track
            cursor.execute("""
                CREATE TABLE user_track (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    artist TEXT,
                    file_path TEXT NOT NULL,
                    duration INTEGER,
                    is_public BOOLEAN DEFAULT 1,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    play_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            """)
            print("Таблица user_track создана")
        else:
            print("Таблица user_track уже существует")
        
        conn.commit()
        print("Миграция таблицы пользовательских треков завершена успешно!")
        return True
        
    except sqlite3.Error as e:
        print(f"Ошибка при миграции базы данных: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()