import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db, app

def run_migration():
    """Выполнение миграции базы данных для добавления полей подтверждения email"""
    with app.app_context():
        try:
            # Выполняем SQL-запросы для добавления столбцов
            print("Выполняем миграцию базы данных...")
            
            # Добавляем столбцы в таблицу user
            db.session.execute(db.text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS confirmation_code VARCHAR(6),
                ADD COLUMN IF NOT EXISTS confirmation_code_expires TIMESTAMP
            """))
            
            db.session.commit()
            print("Миграция успешно выполнена!")
            
        except Exception as e:
            print(f"Ошибка при выполнении миграции: {e}")
            db.session.rollback()

if __name__ == "__main__":
    run_migration()