# Деплой FetDate на виртуальной машине с Ubuntu

## Подготовка виртуальной машины

1. Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Установите Docker:
```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce -y
```

3. Установите Docker Compose:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

4. Добавьте вашего пользователя в группу docker:
```bash
sudo usermod -aG docker $USER
```

5. Перезагрузите систему или выйдите и снова зайдите в систему, чтобы изменения вступили в силу.

## Подготовка проекта

1. Скопируйте всю директорию проекта в `/home/Project/fetdate` на виртуальной машине:
```bash
# На виртуальной машине:
mkdir -p /home/Project
# Загрузите проект в /home/Project/fetdate
```

2. Перейдите в директорию проекта:
```bash
cd /home/Project/fetdate
```

## Настройка окружения

1. Создайте файл `.env` для хранения секретов:
```bash
cat > .env << EOF
DB_PASSWORD=fetdate_password
SECRET_KEY=your_default_secret_key_for_local_development_please_change_in_production_5a7b9c3d1e2f4a6b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=sup.fetdate@gmail.com
MAIL_PASSWORD=cvjorlnpwtvygrcx
MAIL_DEFAULT_SENDER=sup.fetdate@gmail.com
EOF
```

2. Убедитесь, что у файла `.env` правильные права доступа:
```bash
chmod 600 .env
```

## Настройка email (важно!)

Приложение использует email для подтверждения регистрации пользователей. Для настройки:

1. Используйте Gmail (или другой SMTP-сервер)
2. Для Gmail: 
   - Включите "Двухфакторную аутентификацию"
   - Создайте "Пароль приложения" в настройках Google аккаунта
   - Используйте этот пароль приложения в переменной MAIL_PASSWORD
3. Если используете другой SMTP-сервер, измените соответствующие параметры в .env файле

## Запуск приложения

1. Запустите приложение с помощью Docker Compose:
```bash
docker-compose up -d
```

2. Проверьте статус контейнеров:
```bash
docker-compose ps
```

## Настройка прокси-сервера (если нужно использовать порт 80)

Если вы хотите использовать порт 80, а не прокидывать порты вручную, как описано в требованиях, просто оставьте настройки в docker-compose.yml как есть, nginx будет слушать порт 80.

## Проверка работы приложения

1. Проверьте, что приложение запущено:
```bash
# Проверьте логи приложения
docker-compose logs app
# Проверьте логи nginx
docker-compose logs nginx
```

2. Откройте веб-браузер и перейдите по адресу: `http://IP_адрес_вашей_виртуальной_машины`

## Обновление приложения

1. Остановите текущее приложение:
```bash
docker-compose down
```

2. Обновите файлы приложения в директории `/home/Project/fetdate`

3. Пересоберите образы:
```bash
docker-compose build
```

4. Запустите приложение:
```bash
docker-compose up -d
```

## Управление приложением

- Остановить приложение: `docker-compose down`
- Перезапустить приложение: `docker-compose restart`
- Просмотреть логи: `docker-compose logs -f`
- Просмотреть логи конкретного сервиса: `docker-compose logs -f <service_name>`

## Резервное копирование

Для резервного копирования базы данных:
```bash
docker-compose exec db pg_dump -U fetdate_user fetdate_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Восстановление из резервной копии

Для восстановления базы данных из резервной копии:
```bash
cat backup_file.sql | docker-compose exec -T db psql -U fetdate_user fetdate_db
```

## Дополнительные рекомендации

1. Установите SSL-сертификат с помощью Let's Encrypt, если планируете использовать приложение в продакшене
2. Настройте firewall, чтобы разрешить только необходимые порты
3. Регулярно обновляйте Docker и систему
4. Мониторьте использование ресурсов и логи приложения