FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY pyproject.toml ./

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/scripts

# Указываем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда по умолчанию
CMD ["python", "main.py", "--api"]