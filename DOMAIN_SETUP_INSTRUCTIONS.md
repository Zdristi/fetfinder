# Настройка домена fetdate.online

## 1. Остановка Apache (важно!)

Если вы видите папку cgi-bin при открытии домена, это означает, что Apache уже запущен и использует порты 80/443:

1. Остановите Apache:
```bash
sudo systemctl stop apache2
sudo systemctl disable apache2  # чтобы Apache не запускался при перезагрузке
```

## 2. Настройка DNS

1. В панели управления доменом (у регистратора доменов) необходимо создать следующие DNS-записи:
   - A запись: `fetdate.online` -> `IP_адрес_сервера`
   - A запись: `www.fetdate.online` -> `IP_адрес_сервера`

## 3. Установка SSL-сертификата

1. Установите certbot для получения SSL-сертификатов Let's Encrypt:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

2. Получите SSL-сертификат:
```bash
sudo certbot --nginx -d fetdate.online -d www.fetdate.online
```

3. При первом запуске certbot автоматически обновит конфигурацию nginx.

4. Настройте автопереновление сертификата:
```bash
sudo crontab -e
# Добавьте строку для ежедневной проверки обновления сертификатов:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 4. Подготовка сертификатов для Docker

1. Создайте директории для SSL-сертификатов:
```bash
mkdir -p ssl_certs ssl_private
```

2. Скопируйте сертификаты в эти директории:
```bash
sudo cp /etc/letsencrypt/live/fetdate.online/fullchain.pem ssl_certs/fetdate.online.crt
sudo cp /etc/letsencrypt/live/fetdate.online/privkey.pem ssl_private/fetdate.online.key
```

3. Установите правильные права доступа:
```bash
chmod 644 ssl_certs/fetdate.online.crt
chmod 600 ssl_private/fetdate.online.key
```

## 5. Запуск приложения

1. Убедитесь, что все переменные окружения заданы в файле `.env`

2. Запустите приложение:
```bash
docker-compose up -d
```

## 6. Дополнительные настройки безопасности

1. Установите и настройте fail2ban для защиты от атак:
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

2. Настройте firewall:
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw reload
```

## 7. Мониторинг и логирование

1. Проверьте статус приложения:
```bash
docker-compose ps
```

2. Просмотрите логи:
```bash
docker-compose logs -f
```

## 8. Резервное копирование

Для регулярного резервного копирования базы данных создайте скрипт:
```bash
#!/bin/bash
# backup_script.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec db pg_dump -U fetdate_user fetdate_db > backup_$TIMESTAMP.sql
# Удалите бэкапы старше 7 дней
find . -name "backup_*.sql" -mtime +7 -delete
```

## Важно

- Обязательно остановите Apache перед запуском приложения, иначе порты 80/443 будут заняты
- Убедитесь, что порты 80 и 443 открыты в firewall
- Сертификаты Let's Encrypt действительны 90 дней и требуют периодического обновления
- Рекомендуется использовать SSL-сертификаты от проверенных центров сертификации для продакшена