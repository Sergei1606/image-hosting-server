"""Основной модуль бэкенд-сервера для хостинга изображений с базой данных."""

import http.server
import re
import logging
import json
import os
import uuid
import time
from urllib.parse import urlparse, parse_qs
import io
from PIL import Image
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурационные константы из .env
STATIC_FILES_DIR = 'static'
UPLOAD_DIR = 'images'
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 5 * 1024 * 1024))
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', '.jpg,.jpeg,.png,.gif').split(',')
LOG_DIR = 'logs'
ITEMS_PER_PAGE = 10

# Конфигурация БД из .env
DB_CONFIG = {
    "dbname": os.getenv('POSTGRES_DB', 'images_db'),
    "user": os.getenv('POSTGRES_USER', 'postgres'),
    "password": os.getenv('POSTGRES_PASSWORD', 'password'),
    "host": os.getenv('DATABASE_HOST', 'db'),
    "port": os.getenv('DATABASE_PORT', '5432')
}

# Создание необходимых директорий
for directory in [UPLOAD_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)


def require_db_connection(func):
    """Декоратор для проверки подключения к БД."""

    def wrapper(self, *args, **kwargs):
        if not db.is_connected():
            self._send_error_response(503, "Сервис временно недоступен - нет подключения к базе данных")
            return None
        return func(self, *args, **kwargs)

    return wrapper


class Database:
    """Класс для работы с базой данных PostgreSQL."""

    def __init__(self):
        self.connection = None
        self.max_retries = 10
        self.retry_delay = 3
        self.connect()

    def connect(self):
        """Устанавливает соединение с базой данных."""
        logging.info("Попытка подключения к базе данных...")
        for attempt in range(self.max_retries):
            try:
                self.connection = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                logging.info("Успешное подключение к базе данных")
                return
            except Exception as e:
                logging.warning(f"Попытка {attempt + 1}/{self.max_retries}: Ошибка подключения: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logging.error("Не удалось подключиться к базе данных после всех попыток")
                    self.connection = None

    def is_connected(self):
        """Проверяет, активно ли соединение с базой данных."""
        try:
            if self.connection and not self.connection.closed:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return True
        except Exception:
            self.connection = None
        return False

    def ensure_connection(self):
        """Гарантирует, что соединение с БД установлено."""
        if not self.is_connected():
            self.connect()
        return self.is_connected()

    def execute_query(self, query, params=None, fetch=False):
        """Выполняет SQL запрос к базе данных."""
        if not self.ensure_connection():
            logging.error("Нет подключения к базе данных")
            return None

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                self.connection.commit()
                return True
        except psycopg2.OperationalError as e:
            logging.error(f"Ошибка подключения к БД: {e}")
            self.connection = None
            return None
        except Exception as e:
            logging.error(f"Ошибка выполнения запроса: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def save_image_metadata(self, filename, original_name, size, file_type):
        """Сохраняет метаданные изображения в базу данных."""
        query = "INSERT INTO images (filename, original_name, size, file_type) VALUES (%s, %s, %s, %s)"
        return self.execute_query(query, (filename, original_name, size, file_type))

    def get_images(self, page=1, per_page=ITEMS_PER_PAGE):
        """Получает список изображений с пагинацией."""
        offset = (page - 1) * per_page
        query = "SELECT * FROM images ORDER BY upload_time DESC LIMIT %s OFFSET %s"
        result = self.execute_query(query, (per_page, offset), fetch=True)
        return result if result else []

    def get_total_images_count(self):
        """Возвращает общее количество изображений в базе."""
        query = "SELECT COUNT(*) as count FROM images"
        result = self.execute_query(query, fetch=True)
        return result[0]['count'] if result else 0

    def get_image(self, **filters):
        """Получает информацию об изображении по указанным фильтрам."""
        if not filters:
            return None

        conditions = []
        params = []
        for field, value in filters.items():
            conditions.append(f"{field} = %s")
            params.append(value)

        query = f"SELECT * FROM images WHERE {' AND '.join(conditions)} LIMIT 1"
        result = self.execute_query(query, params, fetch=True)
        return result[0] if result else None

    def delete_image(self, image_id):
        """Удаляет изображение из базы данных по ID."""
        query = "DELETE FROM images WHERE id = %s"
        return self.execute_query(query, (image_id,))


# Глобальный объект для работы с базой данных
db = Database()


class ImageHostingHandler(http.server.BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для сервера хостинга изображений."""

    def _set_headers(self, status_code=200, content_type='text/html'):
        """Устанавливает базовые заголовки HTTP-ответа."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def _get_content_type(self, file_path):
        """Определяет Content-Type по расширению файла."""
        extension = file_path.lower()
        if extension.endswith('.html'):
            return 'text/html'
        elif extension.endswith('.css'):
            return 'text/css'
        elif extension.endswith('.js'):
            return 'application/javascript'
        elif extension.endswith('.png'):
            return 'image/png'
        elif extension.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif extension.endswith('.gif'):
            return 'image/gif'
        else:
            return 'application/octet-stream'

    def end_headers(self):
        """Добавляет CORS заголовки к ответу."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        """Обрабатывает OPTIONS запросы для CORS preflight."""
        self._set_headers(200)

    def do_GET(self):
        """Обрабатывает GET запросы."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/' or path == '/index.html':
            self._serve_static_file('index.html')
        elif path == '/images-list':
            self._serve_images_list(parsed_path.query)
        elif path == '/images-list-data':
            self._serve_images_list_data()
        elif path.startswith('/static/'):
            file_path = path[8:]
            self._serve_static_file(file_path)
        elif path.startswith('/images/'):
            self._serve_uploaded_file(path)
        else:
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 Not Found")
            logging.warning(f"Файл не найден: {self.path}")

    @require_db_connection
    def _serve_images_list_data(self):
        """Возвращает JSON с данными изображений для фронтенда."""
        try:
            images = db.get_images(1, 1000)
            images_data = []
            for img in images:
                images_data.append({
                    'id': img['id'],
                    'filename': img['filename'],
                    'original_name': img['original_name'],
                    'size': img['size'],
                    'upload_time': img['upload_time'].isoformat(),
                    'file_type': img['file_type']
                })

            self._set_headers(200, 'application/json')
            self.wfile.write(json.dumps(images_data).encode('utf-8'))
            logging.info(f"Отправлены данные {len(images_data)} изображений для фронтенда")
        except Exception as e:
            logging.error(f"Ошибка при получении данных для фронтенда: {e}")
            self._send_error_response(500, f"Ошибка при получении данных: {e}")

    @require_db_connection
    def _serve_images_list(self, query_string):
        """Отображает страницу со списком изображений."""
        try:
            params = parse_qs(query_string)
            page = int(params.get('page', [1])[0])
            if page < 1:
                page = 1

            images = db.get_images(page)
            total_count = db.get_total_images_count()
            total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            html = self._generate_images_list_html(images, page, total_pages)
            self._set_headers(200, 'text/html')
            self.wfile.write(html.encode('utf-8'))
            logging.info(f"Отображен список изображений, страница {page}")
        except Exception as e:
            self._set_headers(500, 'text/plain')
            self.wfile.write(b"500 Internal Server Error")
            logging.error(f"Ошибка при отображении списка изображений: {e}")

    def _generate_images_list_html(self, images, current_page, total_pages):
        """Генерирует HTML для страницы списка изображений."""
        table_rows = ""
        if images:
            for img in images:
                size_kb = img['size'] / 1024
                upload_time = img['upload_time'].strftime('%Y-%m-%d %H:%M:%S')
                table_rows += f"""
                <tr>
                    <td><a href="/images/{img['filename']}" class="file-link" target="_blank">{img['filename']}</a></td>
                    <td>{img['original_name']}</td>
                    <td>{size_kb:.1f}</td>
                    <td>{upload_time}</td>
                    <td>{img['file_type']}</td>
                    <td><button class="delete-btn" onclick="deleteImage({img['id']})">Удалить</button></td>
                </tr>
                """
        else:
            table_rows = '<tr><td colspan="6" class="no-data">Нет загруженных изображений</td></tr>'

        pagination = '<div class="pagination">'
        if current_page > 1:
            pagination += f'<a href="/images-list?page={current_page - 1}">Предыдущая</a>'
        pagination += f'<span class="current">Страница {current_page} из {total_pages}</span>'
        if current_page < total_pages:
            pagination += f'<a href="/images-list?page={current_page + 1}">Следующая</a>'
        pagination += '</div>'

        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Список изображений</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="container">
                <h1>Список загруженных изображений</h1>
                <p><a href="/">Вернуться на главную</a></p>
                <table class="images-table">
                    <thead>
                        <tr>
                            <th>Имя файла</th>
                            <th>Оригинальное имя</th>
                            <th>Размер (КБ)</th>
                            <th>Дата загрузки</th>
                            <th>Тип файла</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>{table_rows}</tbody>
                </table>
                {pagination}
            </div>
            <script>
                function deleteImage(imageId) {{
                    if (confirm('Вы уверены, что хотите удалить это изображение?')) {{
                        fetch('/delete/' + imageId, {{ method: 'DELETE' }})
                            .then(response => response.json())
                            .then(data => {{
                                if (data.status === 'success') {{
                                    alert('Изображение успешно удалено');
                                    location.reload();
                                }} else {{
                                    alert('Ошибка при удалении: ' + data.message);
                                }}
                            }})
                            .catch(error => {{
                                alert('Ошибка при удалении: ' + error);
                            }});
                    }}
                }}
            </script>
        </body>
        </html>
        """
        return html

    def _serve_file(self, file_path, base_dir, file_type="static"):
        """Обслуживает файлы из указанной базовой директории."""
        try:
            filename = os.path.basename(file_path)
            full_path = os.path.join(base_dir, filename)
            full_path = os.path.abspath(full_path)
            base_dir_abs = os.path.abspath(base_dir)

            if not full_path.startswith(base_dir_abs):
                self._set_headers(403, 'text/plain')
                self.wfile.write(b"403 Forbidden")
                logging.warning(f"Попытка доступа вне директории {file_type}: {full_path}")
                return

            if os.path.exists(full_path) and os.path.isfile(full_path):
                self._set_headers(200, self._get_content_type(full_path))
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                logging.info(f"Обслужен {file_type} файл: {filename}")
            else:
                self._set_headers(404, 'text/plain')
                self.wfile.write(b"404 Not Found")
                logging.warning(f"{file_type.capitalize()} файл не найден: {filename}")
        except Exception as e:
            self._set_headers(500, 'text/plain')
            self.wfile.write(b"500 Internal Server Error")
            logging.error(f"Ошибка при обслуживании {file_type} файла {file_path}: {e}")

    def _serve_static_file(self, file_path):
        """Обслуживает статические файлы из папки static."""
        self._serve_file(file_path, STATIC_FILES_DIR, "static")

    def _serve_uploaded_file(self, file_path):
        """Обслуживает загруженные пользователем изображения."""
        filename = os.path.basename(file_path)
        self._serve_file(filename, UPLOAD_DIR, "uploaded")

    def do_POST(self):
        """Обрабатывает POST запросы для загрузки изображений."""
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/upload':
            self._handle_file_upload()
        else:
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 Not Found")
            logging.warning(f"Неизвестный POST запрос: {self.path}")

    def do_DELETE(self):
        """Обрабатывает DELETE запросы для удаления изображений."""
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/delete/'):
            image_id = parsed_path.path.split('/')[-1]
            self._handle_file_delete(image_id)
        else:
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 Not Found")
            logging.warning(f"Неизвестный DELETE запрос: {self.path}")

    @require_db_connection
    def _handle_file_delete(self, image_id):
        """Удаляет файл из файловой системы и базы данных."""
        try:
            image_info = db.get_image(id=image_id)
            if not image_info:
                self._send_error_response(404, "Изображение не найдено в базе данных")
                logging.warning(f"Изображение с ID {image_id} не найдено в базе данных")
                return

            filename = image_info['filename']
            full_path = os.path.join(UPLOAD_DIR, filename)
            full_path = os.path.abspath(full_path)
            upload_dir = os.path.abspath(UPLOAD_DIR)

            if not full_path.startswith(upload_dir):
                self._send_error_response(403, "Запрещенный путь")
                logging.warning(f"Попытка удаления вне директории: {full_path}")
                return

            if os.path.exists(full_path) and os.path.isfile(full_path):
                os.remove(full_path)
                logging.info(f"Файл удален с диска: {filename}")
            else:
                logging.warning(f"Файл не найден на диске: {filename}")

            if db.delete_image(image_id):
                self._set_headers(200, 'application/json')
                response = {"status": "success", "message": "Файл успешно удален"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                logging.info(f"Запись удалена из базы данных: ID {image_id}, файл {filename}")
            else:
                self._send_error_response(500, "Ошибка при удалении из базы данных")
                logging.error(f"Ошибка при удалении записи из базы данных: ID {image_id}")
        except Exception as e:
            self._send_error_response(500, "Ошибка при удалении файла")
            logging.error(f"Ошибка при удалении файла ID {image_id}: {e}")

    def _handle_file_upload(self):
        """Обрабатывает загрузку файлов."""
        content_type_header = self.headers.get('Content-Type', '')
        if not content_type_header.startswith('multipart/form-data'):
            self._send_error_response(400, "Ожидается multipart/form-data")
            logging.warning("Ошибка загрузки: некорректный Content-Type")
            return

        try:
            boundary = content_type_header.split('boundary=')[1].encode('utf-8')
        except IndexError:
            self._send_error_response(400, "Boundary не найден в Content-Type")
            logging.warning("Ошибка загрузки: boundary не найден")
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > MAX_FILE_SIZE * 2:
                self._send_error_response(413, "Запрос слишком большой")
                logging.warning(f"Запрос превышает размер: {content_length} байт")
                return
            raw_body = self.rfile.read(content_length)
        except (TypeError, ValueError):
            self._send_error_response(411, "Некорректный Content-Length")
            logging.error("Ошибка: некорректный Content-Length")
            return
        except Exception as e:
            self._send_error_response(500, "Ошибка при чтении запроса")
            logging.error(f"Ошибка при чтении тела запроса: {e}")
            return

        file_data, filename = self._parse_multipart_data(raw_body, boundary)
        if not file_data or not filename:
            self._send_error_response(400, "Файл не найден в запросе")
            logging.warning("Файл не найден в multipart-запросе")
            return

        self._validate_and_save_file(file_data, filename)

    def _parse_multipart_data(self, raw_body, boundary):
        """Парсит multipart/form-data и извлекает файл."""
        parts = raw_body.split(b'--' + boundary)
        for part in parts:
            if b'Content-Disposition: form-data;' in part and b'filename=' in part:
                try:
                    headers_end = part.find(b'\r\n\r\n')
                    headers_str = part[:headers_end].decode('utf-8', errors='ignore')
                    filename_match = re.search(r'filename="([^"]+)"', headers_str)
                    if filename_match:
                        filename = filename_match.group(1)
                        file_data = part[headers_end + 4:].strip()
                        return file_data, filename
                except Exception as e:
                    logging.error(f"Ошибка при парсинге multipart: {e}")
                    continue
        return None, None

    def _validate_and_save_file(self, file_data, filename):
        """Валидирует и сохраняет загруженный файл."""
        file_size = len(file_data)
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension not in ALLOWED_EXTENSIONS:
            self._send_error_response(400, f"Неподдерживаемый формат файла. Допустимы: {', '.join(ALLOWED_EXTENSIONS)}")
            logging.warning(f"Неподдерживаемый формат: {filename}")
            return

        if file_size > MAX_FILE_SIZE:
            self._send_error_response(400, f"Файл превышает максимальный размер {MAX_FILE_SIZE / (1024 * 1024):.0f}MB")
            logging.warning(f"Файл превышает размер: {filename}, {file_size} байт")
            return

        try:
            image_data = io.BytesIO(file_data)
            validation_image = Image.open(image_data)
            validation_image.verify()
            image_data.seek(0)
            image = Image.open(image_data)

            if image.format not in ['JPEG', 'PNG', 'GIF']:
                self._send_error_response(400, f"Неподдерживаемый формат изображения: {image.format}")
                logging.warning(f"Pillow обнаружил неподдерживаемый формат: {filename} -> {image.format}")
                return

            if image.width > 10000 or image.height > 10000:
                self._send_error_response(400, "Слишком большие размеры изображения")
                logging.warning(f"Изображение слишком большое: {image.size}")
                return

        except Exception as e:
            self._send_error_response(400, f"Ошибка валидации изображения: {str(e)}")
            logging.error(f"Ошибка Pillow при валидации '{filename}': {e}")
            return

        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        target_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            with open(target_path, 'wb') as f:
                f.write(file_data)

            file_type = image.format.lower() if image.format else file_extension[1:]
            if db.save_image_metadata(unique_filename, filename, file_size, file_type):
                file_url = f"/images/{unique_filename}"
                logging.info(f"Изображение '{filename}' сохранено как '{unique_filename}'")
                self._send_success_response({
                    "status": "success",
                    "message": "Файл успешно загружен.",
                    "filename": unique_filename,
                    "url": file_url,
                    "original_name": filename
                })
            else:
                if os.path.exists(target_path):
                    os.remove(target_path)
                self._send_error_response(500, "Ошибка при сохранении метаданных в базу данных")
                logging.error(f"Ошибка сохранения метаданных для файла '{filename}'")
        except Exception as e:
            self._send_error_response(500, "Ошибка при сохранении файла")
            logging.error(f"Ошибка сохранения файла '{filename}': {e}")

    def _send_error_response(self, status_code, message):
        """Отправляет JSON ответ с ошибкой."""
        self._set_headers(status_code, 'application/json')
        response = {"status": "error", "message": message}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def _send_success_response(self, data):
        """Отправляет JSON ответ с успешным результатом."""
        self._set_headers(200, 'application/json')
        self.wfile.write(json.dumps(data).encode('utf-8'))


def run_server(port=8000):
    """Запускает HTTP сервер."""
    logging.info("Ожидание инициализации базы данных...")
    time.sleep(5)

    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, ImageHostingHandler)

    logging.info(f"Сервер запущен на порту {port}")
    logging.info(f"Директория загрузок: {os.path.abspath(UPLOAD_DIR)}")
    logging.info(f"Директория логов: {os.path.abspath(LOG_DIR)}")
    logging.info(f"Статическая директория: {os.path.abspath(STATIC_FILES_DIR)}")

    if db.is_connected():
        logging.info("Подключение к базе данных активно")
    else:
        logging.warning("Подключение к базе данных отсутствует")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания")
    finally:
        if db.connection:
            db.connection.close()
        httpd.server_close()
        logging.info("Сервер остановлен")


if __name__ == '__main__':
    run_server()