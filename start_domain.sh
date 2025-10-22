#!/bin/bash
# Скрипт для запуска приложения FetDate с поддержкой домена fetdate.online

echo "Настройка и запуск FetDate для домена fetdate.online..."

# Проверяем, существует ли файл .env
if [ ! -f .env ]; then
    echo "Файл .env не найден. Создайте его с необходимыми переменными окружения."
    echo "Пример содержимого .env:"
    echo "DB_PASSWORD=fetdate_password"
    echo "SECRET_KEY=your_secret_key_here"
    echo "MAIL_SERVER=smtp.gmail.com"
    echo "MAIL_PORT=587"
    echo "MAIL_USE_TLS=true"
    echo "MAIL_USE_SSL=false"
    echo "MAIL_USERNAME=your_email@gmail.com"
    echo "MAIL_PASSWORD=your_app_password"
    echo "MAIL_DEFAULT_SENDER=your_email@gmail.com"
    exit 1
fi

# Создаем директории для SSL сертификатов, если они не существуют
mkdir -p ssl_certs ssl_private

echo "Запуск приложения с помощью Docker Compose..."
docker-compose up -d

# Проверка статуса контейнеров
echo "Проверка статуса контейнеров..."
sleep 5
docker-compose ps

echo ""
echo "Приложение запущено!"
echo "Откройте в браузере: http://fetdate.online (если DNS настроен) или http://IP_адрес_сервера"
echo ""
echo "Для проверки логов используйте: docker-compose logs -f"
echo "Для остановки приложения используйте: docker-compose down"