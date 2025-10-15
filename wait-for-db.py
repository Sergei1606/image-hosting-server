#!/usr/bin/env python3  # ✅ ДОБАВЛЕН #
"""Скрипт для ожидания готовности базы данных."""

import time
import psycopg2
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)


def wait_for_db(max_retries=30, retry_interval=2):
    """Ожидает готовности базы данных к подключению."""
    logging.info("Ожидание готовности базы данных...")

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname="images_db",
                user="postgres",
                password="password",
                host="db",
                port="5432",
                connect_timeout=5
            )
            conn.close()
            logging.info("✅ База данных готова!")
            return True

        except Exception as e:
            logging.warning(f"Попытка {attempt + 1}/{max_retries}: База данных еще не готова - {e}")
            time.sleep(retry_interval)

    logging.error("❌ Не удалось подключиться к базе данных после всех попыток")
    return False


if __name__ == '__main__':
    success = wait_for_db()
    sys.exit(0 if success else 1)