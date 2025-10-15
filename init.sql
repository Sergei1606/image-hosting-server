-- Создание таблицы для хранения метаданных изображений
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    original_name TEXT NOT NULL,
    size INTEGER NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_type TEXT NOT NULL
);

-- Создание индекса для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_upload_time ON images(upload_time);