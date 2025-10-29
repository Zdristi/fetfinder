FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем директорию для загрузок и базы данных
RUN mkdir -p /app/uploads /app/uploads/optimized
RUN touch /app/fetdate_production.db

EXPOSE 8080

# Устанавливаем переменные окружения для production
ENV DATABASE_URL=sqlite:////app/fetdate_production.db
ENV UPLOAD_FOLDER=/app/uploads

# Создаем скрипт запуска для корректного запуска приложения с логгированием ошибок
RUN echo '#!/bin/bash\n\necho "Starting application setup..."\npython -c "from app import app; app.app_context().push(); from models import db; db.create_all(); print(\\\"Database setup completed\\\")" 2>&1 | tee -a /app/startup.log || echo "Database setup completed with potential issues"\n\necho "Starting Flask application..."\ngunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 120 --chdir /app app:app 2>&1 | tee -a /app/gunicorn.log' > /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]