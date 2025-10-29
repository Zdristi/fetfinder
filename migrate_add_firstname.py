"""
Скрипт миграции для добавления поля first_name к таблице пользователей
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
        # Проверяем, существует ли столбец first_name
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'first_name' not in columns:
            # Добавляем столбец first_name
            cursor.execute("ALTER TABLE user ADD COLUMN first_name TEXT")
            print("Столбец first_name добавлен к таблице user")
        else:
            print("Столбец first_name уже существует")

        conn.commit()
        print("Миграция завершена успешно!")
        return True
        
    except sqlite3.Error as e:
        print(f"Ошибка при миграции базы данных: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()