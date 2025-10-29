#!/usr/bin/env python3
"""
Расширенная диагностика системы свайпинга
"""

import os
import sys
import sqlite3
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnose_swipe_system():
    """Полная диагностика системы свайпинга"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'fetdate_local.db')
        
        if not os.path.exists(db_path):
            print(f"ERROR: Database not found: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== SWIPE SYSTEM DIAGNOSTICS ===")
        
        # 1. Check users
        print("\\n=== USER INFORMATION ===")
        cursor.execute("""
            SELECT id, username, email, city, country, bio, photo, 
                   match_by_city, match_by_country, is_blocked, is_admin
            FROM user
        """)
        users = cursor.fetchall()
        
        for user in users:
            user_id, username, email, city, country, bio, photo, match_by_city, match_by_country, is_blocked, is_admin = user
            print(f"ID: {user_id} | Username: {username} | Email: {email}")
            print(f"  City/Country: {city or '—'}/{country or '—'}")
            print(f"  Bio: {'Yes' if bio else 'No'} | Photo: {'Yes' if photo else 'No'}")
            print(f"  Filter by city: {bool(match_by_city)}, by country: {bool(match_by_country)}")
            print(f"  Blocked: {bool(is_blocked)}, Admin: {bool(is_admin)}")
            print()
        
        # 2. Check tables related to users
        print("=== TABLE STATISTICS ===")
        tables = ['user', 'user_swipe', 'match', 'message', 'user_photo']
        
        for table in tables:
            if table_exists(cursor, table):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
            else:
                print(f"  {table}: TABLE NOT FOUND")
        
        # 3. Check which users are available for swiping
        print(f"\\n=== USER AVAILABILITY ANALYSIS ===")
        
        for current_user in users:
            current_user_id, current_username, _, current_city, current_country, _, _, current_match_by_city, current_match_by_country, _, _ = current_user
            
            print(f"\\n  Analysis for user {current_username} (ID: {current_user_id}):")
            
            # Check who they can see without filters
            query = "SELECT id, username FROM user WHERE id != ?"
            params = [current_user_id]
            
            cursor.execute(query, params)
            all_others = cursor.fetchall()
            print(f"    Total other users: {len(all_others)}")
            
            # Check who they could see with location filters
            if current_match_by_city and current_city:
                query += " AND city = ?"
                params.append(current_city)
                cursor.execute(query, params)
                filtered_others = cursor.fetchall()
                print(f"    After city filter '{current_city}': {len(filtered_others)}")
            elif current_match_by_country and current_country:
                query = "SELECT id, username FROM user WHERE id != ? AND country = ?"
                params = [current_user_id, current_country]
                cursor.execute(query, params)
                filtered_others = cursor.fetchall()
                print(f"    After country filter '{current_country}': {len(filtered_others)}")
            else:
                print("    Without location filtering")
            
            # Check who they already swiped
            cursor.execute("SELECT swipee_id FROM user_swipe WHERE swiper_id = ?", [current_user_id])
            swiped_ids = [row[0] for row in cursor.fetchall()]
            print(f"    Already swiped users: {len(swiped_ids)} (IDs: {swiped_ids if swiped_ids else 'none'})")
            
            # Check who they can see now (with swipe filters)
            available_query = "SELECT id, username FROM user WHERE id != ?"
            available_params = [current_user_id]
            
            if current_match_by_city and current_city:
                available_query += " AND city = ?"
                available_params.append(current_city)
            elif current_match_by_country and current_country:
                available_query = "SELECT id, username FROM user WHERE id != ? AND country = ?"
                available_params = [current_user_id, current_country]
            
            if swiped_ids:
                placeholders = ','.join(['?' for _ in swiped_ids])
                available_query += f" AND id NOT IN ({placeholders})"
                available_params.extend(swiped_ids)
            
            cursor.execute(available_query, available_params)
            available_users = cursor.fetchall()
            print(f"    Available for swiping: {len(available_users)}")
            
            for available_user in available_users:
                print(f"      - ID {available_user[0]}: {available_user[1]}")
        
        # 4. Check blocked users
        print(f"\\n=== BLOCKED USERS ===")
        cursor.execute("SELECT id, username FROM user WHERE is_blocked = 1")
        blocked_users = cursor.fetchall()
        if blocked_users:
            for user in blocked_users:
                print(f"  ID {user[0]}: {user[1]}")
        else:
            print("  No blocked users")
        
        # 5. Check user information completeness
        print(f"\\n=== USER INFORMATION ANALYSIS ===")
        cursor.execute("SELECT id, username, city, country, bio, photo FROM user")
        all_users_info = cursor.fetchall()
        
        for user_info in all_users_info:
            user_id, username, city, country, bio, photo = user_info
            issues = []
            
            if not city and not country:
                issues.append("no location")
            if not bio:
                issues.append("no bio")
            if not photo:
                issues.append("no photo")
            
            status = "COMPLETE PROFILE" if not issues else f"PROBLEMS: {', '.join(issues)}"
            print(f"  ID {user_id} ({username}): {status}")
        
        conn.close()
        print(f"\\nDIAGNOSTICS COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"ERROR DURING DIAGNOSTICS: {e}")
        import traceback
        traceback.print_exc()
        return False

def table_exists(cursor, table_name):
    """Проверяет, существует ли таблица"""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

if __name__ == "__main__":
    print("=== Запуск расширенной диагностики системы свайпинга ===")
    result = diagnose_swipe_system()
    
    if result:
        print("\\n=== РЕКОМЕНДАЦИИ ===")
        print("Если пользователи не видят друг друга:")
        print("1. Убедитесь, что у них не включены фильтры по местоположению")
        print("2. Убедитесь, что у них есть базовая информация (город/страна, био, фото)")
        print("3. Проверьте, не являются ли они заблокированными")
        print("4. Убедитесь, что в системе более одного пользователя")
        
    else:
        print("\\nПроизошла ошибка при диагностике.")