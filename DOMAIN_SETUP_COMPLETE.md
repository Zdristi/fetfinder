# Полное руководство по настройке домена fetdate.online

## Шаг 1: Проверка владения доменом

1. Убедитесь, что вы являетесь владельцем домена fetdate.online
2. Имеете доступ к панели управления DNS у регистратора домена
3. Имеете доступ к серверу, на который будет указывать домен

## Шаг 2: Настройка DNS

1. В панели управления доменом создайте следующие записи:
   - A запись: `@` -> `IP_адрес_вашего_сервера`
   - A запись: `www` -> `IP_адрес_вашего_сервера`

2. Запишите IP-адрес сервера, на котором будет размещено приложение

## Шаг 3: Подготовка проекта на сервере

1. Скопируйте проект на сервер:
```bash
# На сервере (Linux)
mkdir -p /home/Project
cd /home/Project
# Скопируйте файлы проекта в эту директорию
```

2. Установите Docker и Docker Compose (если не установлены):
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce -y

# Установите Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавьте вашего пользователя в группу docker
sudo usermod -aG docker $USER
```

## Шаг 4: Остановка Apache и освобождение портов (важно!)

Если вы видите папку cgi-bin при открытии домена, это означает, что Apache веб-сервер уже запущен и занимает порты 80/443 на сервере.

1. Остановите Apache на сервере:
```bash
sudo systemctl stop apache2
sudo systemctl disable apache2  # чтобы Apache не запускался при перезагрузке
```

2. Проверьте статус Apache:
```bash
sudo systemctl status apache2
```

3. Проверьте, какие процессы используют порты 80 и 443:
```bash
sudo netstat -tulnp | grep :80
sudo netstat -tulnp | grep :443
```

## Шаг 5: Настройка переменных окружения

1. Создайте файл `.env` в корне проекта:
```bash
cat > .env << EOF
DB_PASSWORD=fetdate_password
SECRET_KEY=your_very_secure_secret_key_for_production_change_this_immediately_5a7b9c3d1e2f4a6b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=sup.fetdate@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=sup.fetdate@gmail.com
EOF
```

2. Установите права доступа к файлу:
```bash
chmod 600 .env
```

## Шаг 6: Настройка SSL-сертификата

1. Установите certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
```

2. Получите SSL-сертификат:
```bash
sudo certbot --nginx -d fetdate.online -d www.fetdate.online
```

3. Создайте директории для сертификатов в проекте:
```bash
mkdir -p ssl_certs ssl_private
```

4. Скопируйте сертификаты:
```bash
sudo cp /etc/letsencrypt/live/fetdate.online/fullchain.pem ssl_certs/fetdate.online.crt
sudo cp /etc/letsencrypt/live/fetdate.online/privkey.pem ssl_private/fetdate.online.key
```

5. Установите права доступа:
```bash
chmod 644 ssl_certs/fetdate.online.crt
chmod 600 ssl_private/fetdate.online.key
```

## Шаг 7: Запуск приложения

1. Перейдите в директорию проекта:
```bash
cd /home/Project/fetdate
```

2. Запустите приложение:
```bash
docker-compose up -d
```

3. Проверьте статус:
```bash
docker-compose ps
```

4. Проверьте логи:
```bash
docker-compose logs -f
```

## Шаг 8: Настройка автоматического обновления SSL-сертификатов

1. Добавьте задачу в crontab:
```bash
sudo crontab -e
```

2. Добавьте строку:
```
0 12 * * * /usr/bin/certbot renew --quiet
```

## Шаг 9: Настройка firewall

1. Установите и настройте firewall:
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw reload
```

## Шаг 10: Проверка работы

1. Откройте браузер и перейдите по адресу: https://fetdate.online

2. Убедитесь, что:
   - Сайт открывается
   - SSL-сертификат действителен
   - Все функции работают правильно
   - Регистрация пользователей работает (подтверждение по email)

## Шаг 11: Локальное тестирование (если нужно)

Если вы хотите протестировать приложение локально на вашем компьютере (Windows или Linux), выполните следующее:

### Для Windows:
1. Добавьте запись в файл hosts (C:\Windows\System32\drivers\etc\hosts):
```
127.0.0.1 fetdate.online
```

2. Запустите Flask-приложение:
```bash
python app.py
```

3. Откройте в браузере: http://fetdate.online:5000

### Для Linux/Mac:
1. Добавьте запись в файл /etc/hosts:
```
127.0.0.1 fetdate.online
```

2. Запустите Flask-приложение:
```bash
python app.py
```

3. Откройте в браузере: http://fetdate.online:5000

## Шаг 12: Мониторинг и обслуживание

1. Регулярно проверяйте логи:
```bash
docker-compose logs -f --tail=100
```

2. Создайте скрипт резервного копирования:
```bash
#!/bin/bash
# backup_script.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec db pg_dump -U fetdate_user fetdate_db > backup_$TIMESTAMP.sql
# Удалите бэкапы старше 7 дней
find . -name "backup_*.sql" -mtime +7 -delete
```

3. Установите автоматическое выполнение скрипта резервного копирования:
```bash
crontab -e
# Добавьте строку для ежедневного резервного копирования в 2:00
0 2 * * * /path/to/backup_script.sh
```

## Troubleshooting

Если сайт не открывается:
1. Проверьте, правильно ли настроены DNS-записи (может потребоваться до 48 часов для обновления)
2. Убедитесь, что Apache остановлен и не занимает порты 80/443 на сервере
3. Убедитесь, что порты 80 и 443 открыты в firewall на сервере
4. Проверьте статус контейнеров: `docker-compose ps`
5. Посмотрите логи: `docker-compose logs -f`

Если по-прежнему отображается cgi-bin папка:
1. Удостоверьтесь, что Apache полностью остановлен: `sudo systemctl status apache2`
2. Проверьте, какие процессы используют порты: `sudo netstat -tulnp | grep :80`
3. Перезагрузите сервер, если необходимо
4. Убедитесь, что Nginx запущен: `docker-compose ps`

Если SSL не работает:
1. Проверьте, правильно ли скопированы сертификаты
2. Убедитесь, что права доступа к файлам сертификатов установлены правильно
3. Проверьте конфигурацию nginx в файле nginx.conf

## Важные замечания

- Не используйте пример SECRET_KEY из примеров в продакшене
- Обязательно используйте пароль приложения Gmail, а не обычный пароль
- Регулярно обновляйте SSL-сертификаты
- Настройте автоматические резервные копии базы данных
- Мониторьте использование ресурсов сервера
- ВАЖНО: Убедитесь, что Apache веб-сервер остановлен на сервере перед запуском приложения, иначе Nginx в Docker не сможет использовать порты 80/443
- DNS-записи могут обновляться до 48 часов, но обычно обновляются в течение 1-4 часов