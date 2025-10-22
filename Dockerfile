FROM python:3.9-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей системы
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Ensure gunicorn is installed as it's required for the CMD instruction
RUN pip install --no-cache-dir gunicorn

# Копирование исходного кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p static/uploads

# Установка прав доступа
RUN chmod +x /app

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Открытие порта
EXPOSE 5000

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]