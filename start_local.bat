@echo off
REM Скрипт для установки зависимостей и запуска приложения локально

echo Установка зависимостей...
pip install -r requirements.txt

echo Запуск приложения...
python main.py