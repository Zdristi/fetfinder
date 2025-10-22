# Настройка домена fetdate.online для Flask-приложения

## Для локального тестирования на Windows

1. Добавьте запись в файл hosts:
   - Откройте файл C:\Windows\System32\drivers\etc\hosts в текстовом редакторе с правами администратора
   - Добавьте строку: `127.0.0.1 fetdate.online`
   - Сохраните файл

2. Запустите приложение:
   ```
   python app.py
   ```

3. Откройте браузер и перейдите по адресу: http://fetdate.online:5000

## Для настройки на сервере (Linux)

Если вы видите папку cgi-bin вместо вашего Flask-приложения на сервере, значит:

1. На сервере запущен Apache веб-сервер, который занимает порты 80/443
2. Необходимо остановить Apache и запустить наше Flask-приложение через Docker

### Шаги для настройки на сервере:

1. Подключитесь к вашему серверу по SSH
2. Убедитесь, что домен fetdate.online направлен на IP-адрес этого сервера
3. Остановите Apache:
   ```
   sudo systemctl stop apache2
   sudo systemctl disable apache2
   ```
   
4. Установите Docker и Docker Compose:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt update
   sudo apt install docker-ce -y

   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   sudo usermod -aG docker $USER
   ```

5. Скопируйте все файлы проекта в `/home/Project/fetdate` на сервере

6. Создайте файл `.env`:
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

7. Установите права доступа:
   ```bash
   chmod 600 .env
   ```

8. Установите и настройте SSL-сертификат:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d fetdate.online -d www.fetdate.online
   mkdir -p ssl_certs ssl_private
   sudo cp /etc/letsencrypt/live/fetdate.online/fullchain.pem ssl_certs/fetdate.online.crt
   sudo cp /etc/letsencrypt/live/fetdate.online/privkey.pem ssl_private/fetdate.online.key
   chmod 644 ssl_certs/fetdate.online.crt
   chmod 600 ssl_private/fetdate.online.key
   ```

9. Запустите приложение:
   ```bash
   cd /home/Project/fetdate
   docker-compose up -d
   ```

10. Проверьте статус:
    ```bash
    docker-compose ps
    ```

11. Если все контейнеры запущены успешно, откройте браузер и перейдите по адресу: https://fetdate.online

## Важные замечания

- Apache (и связанная с ним папка cgi-bin) работает на сервере, а не на вашем локальном компьютере
- На вашем локальном компьютере с Windows Apache не установлен или не запущен
- Для изменения поведения домена fetdate.online, вам нужно настроить сервер, на который направлен этот домен
- Если вы не владеете доменом fetdate.online или не управляете сервером, на который он направлен, вы не сможете изменить его содержимое