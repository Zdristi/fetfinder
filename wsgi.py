# wsgi.py
# Создаем экземпляр приложения для использования с wsgi-серверами
from app import app

if __name__ == "__main__":
    app.run()