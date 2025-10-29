#!/usr/bin/env python3
"""
Скрипт для очистки старых данных пользователей после повторного создания аккаунтов с теми же email-адресами.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def cleanup_all_user_related_data():
    """Полная очистка всех пользовательских данных, кроме самих пользователей"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'fetdate_local.db')
        
        if not os.path.exists(db_path):
            print(f"База данных не найдена: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Список таблиц для очистки (кроме таблицы user, чтобы не удалить пользователей)
        tables_to_cleanup = ['user_swipe', 'match', 'message', 'user_photo']
        
        for table in tables_to_cleanup:
            if table_exists(cursor, table):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"DELETE FROM {table}")
                print(f"Удалено {count} записей из таблицы {table}")
            else:
                print(f"Таблица {table} не найдена")
        
        conn.commit()
        conn.close()
        
        print("Все пользовательские данные (кроме аккаунтов) очищены.")
        print("Теперь новые пользователи смогут видеть друг друга при свайпинге.")
        return True
        
    except Exception as e:
        print(f"Ошибка при полной очистке данных: {e}")
        import traceback
        traceback.print_exc()
        return False

def table_exists(cursor, table_name):
    """Проверяет, существует ли таблица"""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

if __name__ == "__main__":
    print("Запуск скрипта очистки старых пользовательских данных...")
    result = cleanup_all_user_related_data()
    
    if result:
        print("\nОчистка завершена успешно!")
        print("Теперь новые пользователи должны видеть друг друга при свайпинге.")
    else:
        print("\nПроизошла ошибка при очистке данных.")