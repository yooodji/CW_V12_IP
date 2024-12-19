from fastapi import FastAPI, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles # Подключение статических файлов (CSS, JS, изображения)
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import asyncpg # Асинхронный клиент для работы с PostgreSQL
import os
# Инициализация приложения и шаблонов
app = FastAPI() # Создание экземпляра приложения FastAPI, которое используется для маршрутизации запросов
templates = Jinja2Templates(directory="moto_templates") # Инициализация папки с HTML-шаблонами moto_templates

# Подключение папки со статикой
app.mount("/static", StaticFiles(directory="static"), name="static") # Подключение папки static для хранения статических файлов

# Чтение переменных окружения через функцию os.getenv(): если переменная не найдена, используется значение по умолчанию
DB_HOST=os.getenv("DB_HOST", "postgres")
DB_USER=os.getenv("DB_USER", "postgres")
DB_PASSWORD=os.getenv("DB_PASSWORD", "postgres")
DB_NAME=os.getenv("DB_NAME", "coursework")
async def get_db_connection(): # Асинхронное подключение к PostgreSQL с использованием asyncpg
    return await asyncpg.connect(
       host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

# DB_HOST = 'localhost'
# DB_USER = 'postgres'
# DB_PASSWORD = 'postgres'
# DB_NAME = 'Motorways'

# async def get_db_connection():
#     return await asyncpg.connect(
#         host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
#     )

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def main(request: Request): # Определение маршрута для главной страницы, возвращающего HTML-ответ
    conn = await get_db_connection() # Подключение к базе данных PostgreSQL
    highways = await conn.fetch("SELECT * FROM highways") # Выполнение SQL-запросов для получения данных из таблиц highways и cities
    cities = await conn.fetch("SELECT * FROM cities")
    await conn.close() # Закрытие соединения с базой данных

    return templates.TemplateResponse("mainpage.html", {"request": request, "highways": highways, "cities": cities}) # Возвращает HTML-шаблон mainpage.html с передачей данных о трассах и городах

# Маршруты для управления страницами
@app.get("/delete_city_page", response_class=HTMLResponse) # Определение маршрута для перехода на страницу удаления города
async def delete_city_page(request: Request):
    return templates.TemplateResponse("delete_city.html", {"request": request})

@app.get("/add_city_page", response_class=HTMLResponse) # Определение маршрута для перехода на страницу добавления города
async def add_city_page(request: Request):
    return templates.TemplateResponse("add_city.html", {"request": request})

@app.get("/delete_highway_page", response_class=HTMLResponse) # Определение маршрута для перехода на страницу удаления трассы
async def delete_highway_page(request: Request):
    return templates.TemplateResponse("delete_highway.html", {"request": request})

@app.get("/add_highway_page", response_class=HTMLResponse) # Определение маршрута для перехода на страницу добавления трассы
async def add_highway_page(request: Request):
    return templates.TemplateResponse("add_highway.html", {"request": request})

# Добавление записи города
@app.post("/addcities")
async def add_city(
    request: Request, 
    name_city: str = Form(...), 
    region: str = Form(...), 
    population: int = Form(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()

    try:
        # Проверка существования города в указанном регионе
        city_exist = await conn.fetchval(
            "SELECT name_city FROM cities WHERE name_city = $1 AND region = $2", 
            name_city, region
        )

        if city_exist:
            message = f"Город '{name_city}' уже существует в регионе '{region}'!"
            status_code = 400
        else:
            # Добавление нового города
            await conn.execute(
                "INSERT INTO cities (name_city, region, population) VALUES ($1, $2, $3)", 
                name_city, region, population
            )
            message = f"Город '{name_city}' успешно добавлен в регион '{region}'!"
            status_code = 201

    except Exception as e:
        message = f"Ошибка: {str(e)}"
        status_code = 500
    finally:
        await conn.close()

    if response_format == "json":
        return JSONResponse(
            content={
                "message": message,
                "city_data": {
                    "name_city": name_city,
                    "region": region,
                    "population": population
                }
            }, 
            status_code=status_code
        )

    return templates.TemplateResponse(
        "add_city.html", {"request": request, "message": message}
    )


# Удаление записи города
@app.post("/delete_city_record")
async def delete_city_record(
    request: Request, 
    name_city: str = Form(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()

    # Проверка существования города
    city_exist = await conn.fetchval(
        "SELECT name_city FROM cities WHERE name_city = $1", name_city
    )

    if not city_exist:
        message = f"Город '{name_city}' не найден в базе данных!"
        status_code = 404
    else:
        await conn.execute("DELETE FROM cities WHERE name_city = $1", name_city)
        message = f"Город '{name_city}' успешно удалён!"
        status_code = 200

    await conn.close()

    if response_format == "json":
        return JSONResponse(
            content={"message": message, "deleted_city": name_city}, 
            status_code=status_code
        )

    return templates.TemplateResponse(
        "delete_city.html", {"request": request, "message": message}
    )


# Замена атрибута города
@app.post("/update_city_attribute")
async def update_city_attribute(
    request: Request, 
    name_city: str = Form(...), 
    attribute_name: str = Form(...), 
    new_value: str = Form(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()

    # Проверка существования города
    city_exist = await conn.fetchval(
        "SELECT name_city FROM cities WHERE name_city = $1", name_city
    )

    if not city_exist:
        message = f"Город '{name_city}' не найден в базе данных!"
        status_code = 404
    else:
        try:
            if attribute_name == "population":
                new_value = int(new_value)

            await conn.execute(
                f"UPDATE cities SET {attribute_name} = $1 WHERE name_city = $2", 
                new_value, name_city
            )
            message = f"Атрибут '{attribute_name}' успешно обновлён на '{new_value}' для города '{name_city}'!"
            status_code = 200

        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Ошибка: количество населения должно быть числом."
            )

    await conn.close()

    if response_format == "json":
        return JSONResponse(
            content={
                "message": message,
                "updated_city": name_city,
                "updated_attribute": {attribute_name: new_value}
            }, 
            status_code=status_code
        )

    return templates.TemplateResponse(
        "delete_city.html", {"request": request, "message": message}
    )



# добавление записи о автотрассе
@app.post("/addhighway")
async def add_highway(
    request: Request, 
    number_highways: int = Form(...), 
    city_a: str = Form(...), 
    city_b: str = Form(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()
    try:
        # Добавление новой автотрассы
        await conn.execute(
            "INSERT INTO highways (number_highways, city_a, city_b) VALUES ($1, $2, $3)", 
            number_highways, city_a, city_b
        )
        message = f"Автотрасса с номером {number_highways} успешно добавлена!"
        status_code = 201  # Код успешного создания

    except Exception as e:
        message = f"Ошибка: {str(e)}"
        status_code = 400  # Код ошибки

    finally:
        await conn.close()

    # Формирование JSON-ответа для Swagger
    if response_format == "json":
        return JSONResponse(
            content={
                "message": message,
                "highway_data": {
                    "number_highways": number_highways,
                    "city_a": city_a,
                    "city_b": city_b,
                }
            },
            status_code=status_code
        )

    # Формирование HTML-ответа для сайта
    return templates.TemplateResponse(
        "add_highway.html", 
        {"request": request, "message": message}
    )

# Удаление записи автотрассы
@app.post("/delete_highway_record", response_class=JSONResponse)
async def delete_highway_record(
    request: Request, 
    number_highways: int = Form(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()  # Подключение к базе данных

    # Проверка существования автотрассы
    highway_exist = await conn.fetchval(
        "SELECT number_highways FROM highways WHERE number_highways = $1", number_highways
    )

    # Формирование сообщения
    if not highway_exist:
        message = f"Автотрасса №{number_highways} не найдена в базе данных!"
        status_code = 404
    else:
        await conn.execute(
            "DELETE FROM highways WHERE number_highways = $1", number_highways
        )
        message = f"Автотрасса №{number_highways} успешно удалена!"
        status_code = 200

    await conn.close()

    # Возвращаем JSON-ответ для Swagger
    if response_format == "json":
        return JSONResponse(
            content={"message": message}, status_code=status_code
        )

    # Возвращаем HTML-ответ для сайта
    return templates.TemplateResponse(
        "delete_highway.html", 
        {"request": request, "message": message}
    )


# Замена атрибута автотрассы
@app.post("/update_highway_attribute", response_class=JSONResponse)
async def update_highway_attribute(
    request: Request, 
    number_highways: int = Form(...), 
    attribute_name: str = Form(...), 
    new_value: str = Form(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()  # Установка подключения к базе данных

    # Проверка существования автотрассы
    highway_exist = await conn.fetchval(
        "SELECT number_highways FROM highways WHERE number_highways = $1", number_highways
    )

    # Формирование ответа в зависимости от результата
    if not highway_exist:
        message = f"Автотрасса №{number_highways} не найдена в базе данных!"
        status_code = 404
    else:
        # Обновление указанного атрибута
        await conn.execute(
            f"UPDATE highways SET {attribute_name} = $1 WHERE number_highways = $2", 
            new_value, number_highways
        )
        message = f"Атрибут '{attribute_name}' успешно обновлён на '{new_value}' для автотрассы №{number_highways}!"
        status_code = 200

    await conn.close()

    # JSON-ответ для Swagger
    if response_format == "json":
        return JSONResponse(
            content={"message": message}, 
            status_code=status_code
        )

    # HTML-ответ для сайта
    return templates.TemplateResponse(
        "delete_highway.html", 
        {"request": request, "message": message}
    )



# Главная страница с данными базы данных
@app.get("/", response_class=HTMLResponse)
async def main(request: Request): # Определяется асинхронная функция main. Параметр request: Request содержит информацию о запросе от клиента
    conn = await get_db_connection()
    highways = await conn.fetch("SELECT * FROM highways") # Выполняется SQL-запрос на выбор всех записей из таблицы highways
    cities = await conn.fetch("SELECT * FROM cities") # Выполняется SQL-запрос на выбор всех записей из таблицы cities
    await conn.close() # Закрывается соединение с базой данных, чтобы освободить ресурсы

    return templates.TemplateResponse("mainpage.html", { # Возвращается HTML-шаблон mainpage.html
        "request": request, # объект запроса от клиента
        "highways": highways, # записи из таблицы highways
        "cities": cities, # записи из таблицы cities
        "search_highways": [], # пустые списки, поскольку на главной странице нет результатов поиска
        "search_cities": []
    })

# функция поиска
@app.get("/search", response_class=JSONResponse)
async def search(
    request: Request, 
    text: str = Query(...), 
    search_attribute: str = Query(...), 
    response_format: str = Query("html", enum=["html", "json"])
):
    conn = await get_db_connection()

    try:
        # Инициализация данных по умолчанию
        search_cities = []
        search_highways = []
        message = None

        # Проверка ввода и выполнение запросов
        if search_attribute == "number_highways":
            if not text.isdigit():
                message = "Ошибка: Номер автотрассы должен быть числом."
            else:
                highway_value = int(text)
                search_highways = [dict(row) for row in await conn.fetch(   # Record из asyncpg не сериализуем в JSON напрямую, поэтому dict(row) преобразует его в стандартный словарь Python, который можно использовать в JSON-ответах
                    "SELECT * FROM highways WHERE number_highways = $1", highway_value
                )]

                if search_highways:
                    highway = search_highways[0]
                    search_cities = [dict(row) for row in await conn.fetch(
                        """
                        SELECT * FROM cities
                        WHERE name_city = $1 OR name_city = $2
                        """,
                        highway["city_a"], highway["city_b"]
                    )]
                else:
                    message = "Автотрасса с таким номером не найдена."

        elif search_attribute == "name_city":
            search_cities = [dict(row) for row in await conn.fetch(
                "SELECT * FROM cities WHERE name_city = $1", text
            )]

            if search_cities:
                search_highways = [dict(row) for row in await conn.fetch(
                    "SELECT * FROM highways WHERE city_a = $1 OR city_b = $1", text
                )]
            else:
                message = "Город с таким названием не найден."

        elif search_attribute == "region":
            search_cities = [dict(row) for row in await conn.fetch(
                "SELECT * FROM cities WHERE region = $1", text
            )]
            if not search_cities:
                message = "Города с таким регионом не найдены."

        elif search_attribute == "population":
            if not text.isdigit():
                message = "Ошибка: Население должно быть числом."
            else:
                population_value = int(text)
                search_cities = [dict(row) for row in await conn.fetch(
                    "SELECT * FROM cities WHERE population = $1", population_value
                )]
                if not search_cities:
                    message = "Города с таким населением не найдены."

        # Данные текущего состояния базы
        highways = [dict(row) for row in await conn.fetch("SELECT * FROM highways")]
        cities = [dict(row) for row in await conn.fetch("SELECT * FROM cities")]

    finally:
        await conn.close()

    # Формирование JSON-ответа для Swagger
    if response_format == "json":
        return JSONResponse(
            content={
                "message": message or "Результаты поиска успешно получены",
                "search_highways": search_highways,
                "search_cities": search_cities,
                "highways": highways,
                "cities": cities,
            },
            status_code=200 if search_cities or search_highways else 404
        )

    # Формирование HTML-ответа для сайта
    return templates.TemplateResponse(
        "mainpage.html", {
            "request": request,
            "highways": highways,
            "cities": cities,
            "search_highways": search_highways,
            "search_cities": search_cities,
            "message": message
        }
    )




# Запуск приложения
if __name__ == "__main__": # Проверка, запущен ли скрипт напрямую
    import uvicorn # Импортируется uvicorn, асинхронный сервер приложений, совместимый с FastAPI. uvicorn запускает приложение на сервере и обрабатывает входящие HTTP-запросы
    uvicorn.run(app, host="0.0.0.0", port=8088) # Запускается сервер uvicorn. app — это экземпляр FastAPI, содержащий определенные маршруты и логику. 
                                                # host="0.0.0.0" — приложение будет доступно из любой сети (включая Docker-контейнеры). port=8088 — указывает порт, на котором будет работать сервер



