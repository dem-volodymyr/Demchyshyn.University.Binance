# Dockerfile
FROM python:3.12-slim

# Системні залежності для psycopg2 та PIL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо requirements.txt і встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект
COPY . .

# Змінна середовища для Django
ENV PYTHONUNBUFFERED=1

# Стартовий скрипт
CMD ["sh", "-c", "python create_socialapp.py && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn BinanceXchange.wsgi:application --bind 0.0.0.0:8000"]