#!/usr/bin/env python
# export_data.py
"""Скрипт для экспорта данных в JSON файл"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from data_migration import export_data_to_json, import_data_from_json

def main():
    print("Выберите действие:")
    print("1. Экспорт данных в backup")
    print("2. Импорт данных из backup")
    
    choice = input("Введите 1 или 2: ").strip()
    
    with app.app_context():
        if choice == "1":
            try:
                export_data_to_json()
                print("Данные успешно экспортированы в data_backup.json")
            except Exception as e:
                print(f"Ошибка при экспорте: {e}")
        elif choice == "2":
            try:
                import_data_from_json()
                print("Данные успешно импортированы из data_backup.json")
            except Exception as e:
                print(f"Ошибка при импорте: {e}")
        else:
            print("Неверный выбор")

if __name__ == "__main__":
    main()