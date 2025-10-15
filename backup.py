#!/usr/bin/env python3
"""Скрипт для резервного копирования базы данных PostgreSQL."""

import os
import subprocess
import datetime
import logging

# Конфигурация
BACKUP_DIR = 'backups'
DB_NAME = 'images_db'
DB_USER = 'postgres'
DB_PASSWORD = 'password'
DB_HOST = 'localhost'
DB_PORT = '5432'

# Создаем директорию для бэкапов
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)


def create_backup():
    """Создает резервную копию базы данных."""
    try:
        # Генерируем имя файла с timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        # Команда для создания бэкапа
        cmd = [
            'pg_dump',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-d', DB_NAME,
            '-f', backup_path
        ]

        # Устанавливаем переменную окружения с паролем
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD

        # Выполняем команду
        logging.info(f"Создание резервной копии: {backup_filename}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            # Получаем размер файла
            file_size = os.path.getsize(backup_path)
            logging.info(f"Резервная копия успешно создана: {backup_filename} ({file_size} байт)")
            return True
        else:
            logging.error(f"Ошибка при создании резервной копии: {result.stderr}")
            return False

    except Exception as e:
        logging.error(f"Исключение при создании резервной копии: {e}")
        return False


def list_backups():
    """Выводит список доступных резервных копий."""
    if not os.path.exists(BACKUP_DIR):
        print("Директория бэкапов не существует")
        return

    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith('backup_') and filename.endswith('.sql'):
            file_path = os.path.join(BACKUP_DIR, filename)
            file_size = os.path.getsize(file_path)
            file_time = os.path.getctime(file_path)
            backups.append({
                'filename': filename,
                'size': file_size,
                'time': datetime.datetime.fromtimestamp(file_time)
            })

    if backups:
        print("Доступные резервные копии:")
        for backup in sorted(backups, key=lambda x: x['time'], reverse=True):
            print(f"  {backup['filename']} - {backup['size']} байт - {backup['time'].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Резервные копии не найдены")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_backups()
    else:
        success = create_backup()
        if success:
            print("Резервное копирование завершено успешно")
            sys.exit(0)
        else:
            print("Ошибка при резервном копировании")
            sys.exit(1)