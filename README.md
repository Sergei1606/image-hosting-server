#  Image Hosting Server

Веб-приложение для хостинга изображений с возможностью загрузки, просмотра и управления файлами.

## 🚀 Возможности

- ✅ Загрузка изображений (JPG, PNG, GIF)
- ✅ Drag & Drop интерфейс  
- ✅ Просмотр загруженных файлов
- ✅ Копирование ссылок на изображения
- ✅ Удаление изображений
- ✅ Адаптивный дизайн
- ✅ Docker контейнеризация

## 🛠️ Технологии

- **Backend**: Python 3.11, HTTP server
- **Frontend**: HTML5, CSS3, JavaScript
- **Web server**: Nginx
- **Containerization**: Docker, Docker Compose
- **Хранение**: Local Storage, файловая система

## 📦 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <your-repo-url>
cd image-hosting-server
```

### 2. Запуск с Docker Compose
```bash
# Сборка и запуск
docker-compose up --build

# Запуск в фоновом режиме  
docker-compose up -d

# Остановка
docker-compose down
```

### 3. Доступ к приложению
- **Веб-интерфейс**: http://localhost:8080
- **API сервер**: http://localhost:8000

## 🐳 Docker структура

```
services:
  app:      # Python backend (порт 8000)
  nginx:    # Web server (порт 8080)

volumes:
  images:   # Загруженные изображения
  logs:     # Логи приложения
```

## 📋 API endpoints

### GET /
- Главная страница
- Возвращает HTML интерфейс

### POST /upload  
- Загрузка файла
- Поддерживает: JPG, PNG, GIF
- Максимальный размер: 5MB

### GET /images/{filename}
- Получение изображения

### DELETE /images/{filename}  
- Удаление изображения

## 🔧 Настройка

### Переменные окружения
- `PORT` - порт приложения (по умолчанию: 8000)
- `MAX_FILE_SIZE` - максимальный размер файла (по умолчанию: 5MB)

### Изменение портов
Отредактируйте `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # вместо 8000:8000  
  - "8081:80"    # вместо 8080:80
```

## 🧪 Тестирование

### Тестовые запросы
```bash
# Проверка работы сервера
curl http://localhost:8000

# Загрузка тестового изображения
curl -X POST http://localhost:8000/upload -F "file=@static/assets/images/cat.png"
```

### Логи
```bash
# Просмотр логов
docker-compose logs app
docker-compose logs nginx
```

## 📁 Структура проекта

```
my_website/
├── app.py              # Основное приложение
├── Dockerfile          # Конфигурация Docker
├── docker-compose.yml  # Docker Compose
├── nginx.conf         # Конфиг Nginx
├── requirements.txt    # Зависимости Python
├── static/            # Статические файлы
│   ├── index.html     # Главная страница
│   ├── style.css      # Стили
│   ├── script.js      # JavaScript
│   └── assets/        # Изображения и ресурсы
├── images/            # Загруженные файлы
└── logs/              # Логи приложения
```

## 🐛 Решение проблем

### Ошибка портов
Если порты заняты, измените их в `docker-compose.yml`

### Ошибка сборки
```bash
# Очистка и пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Доступ к файлам
```bash
# Просмотр загруженных изображений
docker exec -it my_website-app-1 ls -la /app/images
```

## 📝 Лицензия

MIT License - смотрите файл [LICENSE](LICENSE) для деталей.
