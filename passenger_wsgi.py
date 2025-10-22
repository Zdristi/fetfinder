import sys
import os

# Добавляем путь к директории приложения
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application

if __name__ == "__main__":
    application.run()