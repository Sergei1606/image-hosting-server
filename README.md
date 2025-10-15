# 🖼️ Image Hosting Server


![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![Nginx](https://img.shields.io/badge/Nginx-Ready-green?logo=nginx)

**Веб-приложение для хостинга изображений с возможностью загрузки, просмотра и управления файлами.**

## 🚀 Возможности

- 📤 **Загрузка файлов** через drag & drop или выбор через проводник
- 🖼️ **Просмотр изображений** в отдельной вкладке браузера
- 📋 **Список файлов** с информацией о размере, дате загрузки и типе
- 🗑️ **Удаление изображений** с подтверждением операции
- 📊 **Автоматическое резервное копирование** базы данных
- 🎨 **Случайные фоновые изображения** на главной странице

## --- Ограничения
- Максимальный размер файла: 5MB
- Поддерживаемые форматы: JPG, PNG, GIF

## 🛠️ Технологии

- **Backend**: Python 3.11, HTTP.server, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: PostgreSQL 15
- **Image Processing**: Pillow (PIL)
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx

## 📦 Установка и запуск
### 1. Клонирование репозитория
```bash
git clone https://github.com/Sergei1606/image-hosting-server.git
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
- **Веб-интерфейс**: http://localhost:8000
- **База данных**: PostgreSQL на порту 5432

## 🗂️ Структура проекта

```
my_website/
├── 📁 backups/              # Резервные копии БД
├── 📁 logs/                 # Логи приложения
│   └── app.log             # Основной лог-файл
├── 📁 static/               # Статические файлы фронтенда
│   ├── index.html          # Главная страница
│   ├── style.css           # Стили оформления
│   ├── script.js           # Клиентский JavaScript
│   └── 📁 images/          # Фоновые изображения
│       ├── bird.png
│       ├── cat.png
│       └── dog1-3.png
├── app.py                  # Основной серверный модуль
├── backup.py               # Скрипт резервного копирования
├── docker-compose.yml      # Конфигурация Docker
├── Dockerfile              # Сборка Docker-образа
├── init.sql               # Инициализация БД
├── nginx.conf             # Конфигурация Nginx
├── requirements.txt       # Зависимости Python
└── wait-for-db.py        # Ожидание готовности БД
```
## 📝 Руководство пользователя
### Загрузка изображений
1. Откройте главную страницу приложения
2. Перейдите на вкладку "Upload"
3. Перетащите файл в выделенную зону или нажмите "Browse your file"
4. После загрузки скопируйте ссылку на файл кнопкой "COPY"

### Просмотр и управление
1. Нажмите кнопку "Images" для просмотра всех загруженных файлов
2. Для каждого файла отображается:
- Оригинальное имя
- Ссылка для просмотра
- Размер файла
- Дата загрузки
- Тип файла
3. Для удаления файла нажмите кнопку с иконкой корзины

### Особенности работы
- Авто-обновление списка после загрузки нового файла
- Подтверждение при удалении файлов
- Валидация форматов и размера файлов
- Уведомления о результатах операций

## 🔧 Мониторинг логов
```bash
# Просмотр логов в реальном времени
docker-compose logs -f app

# Только логи базы данных
docker-compose logs db
```
## 📋 API Endpoints
- `GET /` - Главная страница с формой загрузки
- `POST /upload` - Загрузка изображений  
- `GET /images-list` - HTML страница со списком файлов
- `GET /images-list-data` - JSON API для фронтенда
- `DELETE /delete/{id}` - Удаление изображения
- `GET /images/{filename}` - Получение файла

## 🗃️ База данных
```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
### Просмотр загруженных файлов
```bash
docker exec -it my_website-app-1 ls -la /app/images
```


## 📝 Лицензия

MIT License - свободное использование и модификация.
