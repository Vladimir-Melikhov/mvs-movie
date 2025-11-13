# Dockerfile

# Используем последнюю версию Python
FROM python:3.12-slim

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    gettext \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/staticfiles /app/media /app/sent_emails

# Собираем статические файлы
RUN python manage.py collectstatic --noinput || true

# Устанавливаем права доступа
RUN chmod +x /app/manage.py

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 django && \
    chown -R django:django /app

# Переключаемся на непривилегированного пользователя
USER django

# Expose порт для gunicorn
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]