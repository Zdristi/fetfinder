import sqlite3
import sys
import os
from urllib.parse import urlparse

# Добавим путь к проекту, чтобы можно было импортировать config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_URL

def create_user_swipe_table():
    # Parse database URL to get SQLite file path
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL to create the table (SQLite version)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_swipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            swiper_id INTEGER NOT NULL,
            swipee_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(swiper_id, swipee_id)
        );
        """
        
        try:
            cursor.execute(create_table_sql)
            conn.commit()
            print("Таблица user_swipe создана успешно в SQLite!")
        except Exception as e:
            print(f"Ошибка при создании таблицы: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    else:
        print("База данных не является SQLite")

if __name__ == '__main__':
    create_user_swipe_table()