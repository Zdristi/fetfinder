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

def cleanup_old_swipe_data():
    """Очистка старых данных свайпов"""
    try:
        # Определяем путь к базе данных
        db_path = os.path.join(os.path.dirname(__file__), 'database.db')
        
        if not os.path.exists(db_path):
            print(f"База данных не найдена: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Считаем количество записей до очистки
        cursor.execute("SELECT COUNT(*) FROM user_swipe")
        count_before = cursor.fetchone()[0]
        
        # Удаляем все записи из таблицы user_swipe
        cursor.execute("DELETE FROM user_swipe")
        
        # Считаем количество записей после очистки
        cursor.execute("SELECT COUNT(*) FROM user_swipe")
        count_after = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"Очистка завершена. Удалено {count_before} записей из user_swipe. Осталось {count_after}.")
        return True
        
    except Exception as e:
        print(f"Ошибка при очистке данных: {e}")
        return False

def cleanup_all_user_related_data():
    """Полная очистка всех пользовательских данных"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'database.db')
        
        if not os.path.exists(db_path):
            print(f"База данных не найдена: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['user_swipe', 'match', 'message', 'user_photo']
        
        for table in tables:
            if table_exists(cursor, table):
                cursor.execute("SELECT COUNT(*) FROM " + table.replace("'", "''"))
                count = cursor.fetchone()[0]
                
                cursor.execute("DELETE FROM " + table.replace("'", "''"))
                print(f"Удалено {count} записей из таблицы {table}")
        
        conn.commit()
        conn.close()
        
        print("Все пользовательские данные очищены.")
        return True
        
    except Exception as e:
        print(f"Ошибка при полной очистке данных: {e}")
        return False

def table_exists(cursor, table_name):
    """Проверяет, существует ли таблица"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

if __name__ == "__main__":
    print("Запуск скрипта очистки старых данных...")
    
    choice = input("Выберите действие:\n1 - Очистить только данные свайпов\n2 - Очистить все пользовательские данные\nВведите 1 или 2: ")
    
    if choice == "1":
        result = cleanup_old_swipe_data()
    elif choice == "2":
        result = cleanup_all_user_related_data()
    else:
        print("Неверный выбор.")
        sys.exit(1)
    
    if result:
        print("Очистка завершена успешно!")
        print("\nТеперь вы можете создавать новых пользователей, и они будут видеть друг друга.")
    else:
        print("Ошибка при выполнении очистки.")