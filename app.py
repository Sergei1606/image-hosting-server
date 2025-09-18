"""
Основной модуль бэкенд-сервера для хостинга изображений.

Сервер предоставляет API для загрузки изображений и обслуживания статических файлов.
Взаимодействует с Nginx для раздачи загруженных файлов.
"""

import http.server
import re
import logging
import json
import os
import uuid
from urllib.parse import urlparse

# Конфигурационные константы
STATIC_FILES_DIR = 'static'  # Директория со статическими файлами фронтенда
UPLOAD_DIR = 'images'  # Директория для загруженных изображений
MAX_FILE_SIZE = 5 * 1024 * 1024  # Максимальный размер файла (5MB)
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']  # Разрешенные форматы
LOG_DIR = 'logs'  # Директория для логов

# Создание необходимых директорий
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)


class ImageHostingHandler(http.server.BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для сервера хостинга изображений."""

    def _set_headers(self, status_code=200, content_type='text/html'):
        """
        Устанавливает базовые заголовки HTTP-ответа.
        """
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def _get_content_type(self, file_path):
        """
        Определяет Content-Type по расширению файла.
        """
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
        """
        Добавляет CORS заголовки к ответу для кросс-доменных запросов.
        """
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        """
        Обрабатывает OPTIONS запросы для CORS preflight.
        """
        self._set_headers(200)
        self.end_headers()

    def do_GET(self):
        """
        Обрабатывает GET запросы. Обслуживает статические файлы и загруженные изображения.
        """
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Обслуживание статических файлов
        if path == '/' or path == '/index.html':
            # Главная страница
            self._serve_static_file('index.html')

        elif path.startswith('/static/'):
            # Статические файлы (CSS, JS, изображения)
            file_path = path[8:]  # Убираем '/static/' из пути
            self._serve_static_file(file_path)

        elif path.startswith('/images/'):
            # Загруженные пользователем изображения
            self._serve_uploaded_file(path)

        else:
            # Файл не найден
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 Not Found")
            logging.warning(f"Файл не найден: {self.path}")

    def _serve_static_file(self, file_path):
        """
        Обслуживает статические файлы из папки static.
        """
        try:
            # Формируем полный путь к файлу
            full_path = os.path.join(STATIC_FILES_DIR, file_path)

            # Защита от path traversal атак
            full_path = os.path.abspath(full_path)
            static_dir = os.path.abspath(STATIC_FILES_DIR)

            if not full_path.startswith(static_dir):
                self._set_headers(403, 'text/plain')
                self.wfile.write(b"403 Forbidden")
                logging.warning(f"Попытка доступа вне статической директории: {full_path}")
                return

            if os.path.exists(full_path) and os.path.isfile(full_path):
                self._set_headers(200, self._get_content_type(full_path))
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                logging.info(f"Обслужен статический файл: {file_path}")
            else:
                self._set_headers(404, 'text/plain')
                self.wfile.write(b"404 Not Found")
                logging.warning(f"Статический файл не найден: {file_path}")

        except Exception as e:
            self._set_headers(500, 'text/plain')
            self.wfile.write(b"500 Internal Server Error")
            logging.error(f"Ошибка при обслуживании статического файла {file_path}: {e}")

    def _serve_uploaded_file(self, file_path):
        """
        Обслуживает загруженные пользователем изображения.
        """
        try:
            # Извлекаем имя файла из пути
            filename = os.path.basename(file_path)

            # Правильный путь к файлу
            full_path = os.path.join(UPLOAD_DIR, filename)

            # Защита от path traversal
            full_path = os.path.abspath(full_path)
            upload_dir = os.path.abspath(UPLOAD_DIR)

            if not full_path.startswith(upload_dir):
                self._set_headers(403, 'text/plain')
                self.wfile.write(b"403 Forbidden")
                logging.warning(f"Попытка доступа вне директории загрузок: {full_path}")
                return

            if os.path.exists(full_path) and os.path.isfile(full_path):
                self._set_headers(200, self._get_content_type(full_path))
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                logging.info(f"Обслужено загруженное изображение: {filename}")
            else:
                self._set_headers(404, 'text/plain')
                self.wfile.write(b"404 Not Found")
                logging.warning(f"Загруженное изображение не найдено: {filename} (путь: {full_path})")

        except Exception as e:
            self._set_headers(500, 'text/plain')
            self.wfile.write(b"500 Internal Server Error")
            logging.error(f"Ошибка при обслуживании изображения {file_path}: {e}")

    def do_POST(self):
        """
        Обрабатывает POST запросы для загрузки изображений.
        """
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/upload':
            self._handle_file_upload()
        else:
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 Not Found")
            logging.warning(f"Неизвестный POST запрос: {self.path}")

    def do_DELETE(self):
        """
        Обрабатывает DELETE запросы для удаления изображений.
        """
        parsed_path = urlparse(self.path)

        if parsed_path.path.startswith('/images/'):
            self._handle_file_delete(parsed_path.path)
        else:
            self._set_headers(404, 'text/plain')
            self.wfile.write(b"404 Not Found")
            logging.warning(f"Неизвестный DELETE запрос: {self.path}")

    def _handle_file_delete(self, file_path):
        """
        Удаляет файл из файловой системы.
        """
        try:
            # Извлекаем имя файла из пути
            filename = os.path.basename(file_path)

            # Правильный путь к файлу
            full_path = os.path.join(UPLOAD_DIR, filename)

            # Защита от path traversal
            full_path = os.path.abspath(full_path)
            upload_dir = os.path.abspath(UPLOAD_DIR)

            if not full_path.startswith(upload_dir):
                self._set_headers(403, 'text/plain')
                self.wfile.write(b"403 Forbidden")
                logging.warning(f"Попытка удаления вне директории: {full_path}")
                return

            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Удаляем файл
                os.remove(full_path)
                self._set_headers(200, 'application/json')
                response = {"status": "success", "message": "Файл успешно удален"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                logging.info(f"Файл удален: {filename}")
            else:
                self._set_headers(404, 'application/json')
                response = {"status": "error", "message": "Файл не найден"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                logging.warning(f"Файл для удаления не найден: {filename}")

        except Exception as e:
            self._set_headers(500, 'application/json')
            response = {"status": "error", "message": "Ошибка при удалении файла"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            logging.error(f"Ошибка при удалении файла {file_path}: {e}")

    def _handle_file_upload(self):
        """Внутренный метод для обработки загрузки файлов."""
        # Проверка Content-Type
        content_type_header = self.headers.get('Content-Type', '')
        if not content_type_header.startswith('multipart/form-data'):
            self._send_error_response(400, "Ожидается multipart/form-data")
            logging.warning("Ошибка загрузки: некорректный Content-Type")
            return

        # Извлечение boundary
        try:
            boundary = content_type_header.split('boundary=')[1].encode('utf-8')
        except IndexError:
            self._send_error_response(400, "Boundary не найден в Content-Type")
            logging.warning("Ошибка загрузки: boundary не найден")
            return

        # Чтение тела запроса
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

        # Парсинг multipart данных
        file_data, filename = self._parse_multipart_data(raw_body, boundary)
        if not file_data or not filename:
            self._send_error_response(400, "Файл не найден в запросе")
            logging.warning("Файл не найден в multipart-запросе")
            return

        # Валидация и сохранение файла
        self._validate_and_save_file(file_data, filename)

    def _parse_multipart_data(self, raw_body, boundary):
        """
        Парсит multipart/form-data и извлекает файл.
        """
        parts = raw_body.split(b'--' + boundary)

        for part in parts:
            if b'Content-Disposition: form-data;' in part and b'filename=' in part:
                try:
                    headers_end = part.find(b'\r\n\r\n')
                    headers_str = part[:headers_end].decode('utf-8', errors='ignore')

                    # Извлечение имени файла
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
        """
        Валидирует и сохраняет загруженный файл.
        """
        file_size = len(file_data)
        file_extension = os.path.splitext(filename)[1].lower()

        # Проверка формата
        if file_extension not in ALLOWED_EXTENSIONS:
            self._send_error_response(400,
                                      f"Неподдерживаемый формат файла. Допустимы: {', '.join(ALLOWED_EXTENSIONS)}")
            logging.warning(f"Неподдерживаемый формат: {filename}")
            return

        # Проверка размера
        if file_size > MAX_FILE_SIZE:
            self._send_error_response(400,
                                      f"Файл превышает максимальный размер {MAX_FILE_SIZE / (1024 * 1024):.0f}MB")
            logging.warning(f"Файл превышает размер: {filename}, {file_size} байт")
            return

        # Генерация уникального имени и сохранение
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        target_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            with open(target_path, 'wb') as f:
                f.write(file_data)

            file_url = f"/images/{unique_filename}"
            logging.info(f"Изображение '{filename}' сохранено как '{unique_filename}'")

            self._send_success_response({
                "status": "success",
                "message": "Файл успешно загружен.",
                "filename": unique_filename,
                "url": file_url,
                "original_name": filename
            })

        except Exception as e:
            self._send_error_response(500, "Ошибка при сохранении файла")
            logging.error(f"Ошибка сохранения файла '{filename}': {e}")

    def _send_error_response(self, status_code, message):
        """
        Отправляет JSON ответ с ошибкой.
        """
        self._set_headers(status_code, 'application/json')
        response = {"status": "error", "message": message}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def _send_success_response(self, data):
        """
        Отправляет JSON ответ с успешным результатом.
        """
        self._set_headers(200, 'application/json')
        self.wfile.write(json.dumps(data).encode('utf-8'))


def run_server(port=8000):
    """
    Запускает HTTP сервер.
    """
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, ImageHostingHandler)

    logging.info(f"Сервер запущен на порту {port}")
    logging.info(f"Директория загрузок: {os.path.abspath(UPLOAD_DIR)}")
    logging.info(f"Директория логов: {os.path.abspath(LOG_DIR)}")
    logging.info(f"Статическая директория: {os.path.abspath(STATIC_FILES_DIR)}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания")
    finally:
        httpd.server_close()
        logging.info("Сервер остановлен")


if __name__ == '__main__':
    run_server()