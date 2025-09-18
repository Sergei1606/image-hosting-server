FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости и код
COPY --from=builder /root/.local /root/.local
COPY . .

# Создаем папки и устанавливаем права
RUN mkdir -p images logs && \
    chmod 755 images logs

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000

CMD ["python", "app.py"]