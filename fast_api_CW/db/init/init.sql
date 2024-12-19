-- Создание базы данных, если она отсутствует
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'coursework') THEN
        CREATE DATABASE coursework;
    END IF;
END $$;

-- Подключение к базе данных
\connect coursework;


CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,           -- Уникальный идентификатор
    name_city TEXT NOT NULL,         -- Название города
    region TEXT NOT NULL,            -- Регион
    population INTEGER NOT NULL,     -- Население
    UNIQUE (name_city, region)       -- Уникальное сочетание названия города и региона
);
-- -- Создание таблицы cities 
-- CREATE TABLE IF NOT EXISTS cities (
--     name_city TEXT PRIMARY KEY,
--     region TEXT,
--     population INTEGER
-- );

-- Создание таблицы highways
CREATE TABLE IF NOT EXISTS highways (
    number_highways INTEGER PRIMARY KEY,
    city_a TEXT,
    city_b TEXT
);


-- -- Создание таблицы cities
-- CREATE TABLE IF NOT EXISTS cities (
--     name_city TEXT PRIMARY KEY,
--     region TEXT,
--     population INTEGER
-- );

-- -- Создание таблицы highways
-- CREATE TABLE IF NOT EXISTS highways (
--     number_highways INTEGER PRIMARY KEY,
--     city_a TEXT REFERENCES cities (name_city),
--     city_b TEXT REFERENCES cities (name_city)
-- );