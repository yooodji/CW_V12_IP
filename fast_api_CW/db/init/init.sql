-- Создание базы данных, если она отсутствует
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'coursework') THEN
        CREATE DATABASE coursework;
    END IF;
END $$;

-- Подключение к базе данных
\connect coursework;

-- Создание таблицы cities 
CREATE TABLE IF NOT EXISTS cities (
    name_city TEXT PRIMARY KEY,
    region TEXT,
    population INTEGER
);

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