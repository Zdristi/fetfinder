#!/usr/bin/env python3
"""
Скрипт для отладки пользовательских данных и проблемы с отображением пользователей
"""

import os
import sys
import sqlite3
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_users():
    """Отладка пользовательских данных"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'fetdate_local.db')
        
        if not os.path.exists(db_path):
            print(f"База данных не найдена: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем всех пользователей
        cursor.execute("SELECT id, username, email, city, country, match_by_city, match_by_country, is_blocked FROM user")
        users = cursor.fetchall()
        
        print("=== Информация о пользователях ===")
        for user in users:
            user_id, username, email, city, country, match_by_city, match_by_country, is_blocked = user
            print(f"ID: {user_id}, Имя: {username}, Email: {email}")
            print(f"  Город: {city or 'не указан'}, Страна: {country or 'не указана'}")
            print(f"  Фильтр по городу: {bool(match_by_city)}, Фильтр по стране: {bool(match_by_country)}")
            print(f"  Заблокирован: {bool(is_blocked)}")
            print()
        
        # Получаем количество свайпов
        cursor.execute("SELECT COUNT(*) FROM user_swipe")
        swipe_count = cursor.fetchone()[0]
        print(f"=== Сводка ===")
        print(f"Всего пользователей: {len(users)}")
        print(f"Всего свайпов: {swipe_count}")
        
        # Проверяем, есть ли свайпы текущего пользователя (предполагая, что это админ с ID 1)
        if users:
            for user in users:
                user_id = user[0]
                cursor.execute("SELECT COUNT(*) FROM user_swipe WHERE swiper_id = ?", (user_id,))
                user_swipes_out = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM user_swipe WHERE swipee_id = ?", (user_id,))
                user_swipes_in = cursor.fetchone()[0]
                
                print(f"Пользователь {user[1]} (ID: {user_id}): отправлено свайпов {user_swipes_out}, получено свайпов {user_swipes_in}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при отладке данных: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Запуск скрипта отладки пользовательских данных...")
    result = debug_users()
    
    if result:
        print("\nОтладка завершена!")
        print("\nВажные моменты для проверки:")
        print("- У пользователя не должны быть включены match_by_city или match_by_country, если вы хотите видеть всех")
        print("- Пользователи должны иметь заполненные поля city/country, если используются фильтры")
        print("- Убедитесь, что в базе есть хотя бы 2 пользователя")
    else:
        print("\nПроизошла ошибка при отладке данных.")