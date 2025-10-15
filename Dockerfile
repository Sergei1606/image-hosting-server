FROM python:3.11-slim AS builder

WORKDIR /app

# Копируем зависимости отдельно для кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копируем зависимости из builder stage
COPY --from=builder /root/.local /root/.local

# Копируем код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p images logs backups static/assets/images \
    && chmod 755 images logs backups static static/assets static/assets/images

# Делаем скрипты исполняемыми
RUN chmod +x wait-for-db.py

# Добавляем .local/bin в PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Запускаем ожидание БД, затем приложение
CMD ["sh", "-c", "python wait-for-db.py && python app.py"]