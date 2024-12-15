from fastapi import FastAPI, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles # Подключение статических файлов (CSS, JS, изображения)
from fastapi.templating import Jinja2Templates
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

    return templates.TemplateResponse("mainpage.html", { # Возвращает HTML-шаблон mainpage.html с передачей данных о трассах и городах
        "request": request, "highways": highways, "cities": cities
    })

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


@app.post("/addcities") # Определение маршрута для обработки POST-запроса по URL-адресу в кавычках
async def add_city(
    request: Request, # Объект запроса, содержащий данные запроса от клиента
    name_city: str = Form(...), # Получение данных из формы
    region: str = Form(...), 
    population: int = Form(...)
):
    conn = await get_db_connection() # Устанавливается асинхронное подключение к базе данных
    try:
        # Добавление нового города в таблицу cities
        await conn.execute(
            "INSERT INTO cities (name_city, region, population) VALUES ($1, $2, $3)",
            name_city, region, population
        )
        message = f"Город {name_city} успешно добавлен!"
    except Exception as e: # Обработка ошибок, если что-то пошло не так
        message = f"Ошибка: {str(e)}" # Создание сообщения об ошибке с описанием проблемы
    finally:
        await conn.close()

    return templates.TemplateResponse("add_city.html", {"request": request, "message": message}) # Передаются объект request и сообщение message для отображения на странице

# Удаление записи города
@app.post("/delete_city_record") # Определение маршрута для обработки POST-запроса по URL-адресу в кавычках
async def delete_city_record(request: Request, name_city: str = Form(...)):
    conn = await get_db_connection() # Устанавливается подключение к базе данных PostgreSQL
    
    # Проверка существования города
    city_exist = await conn.fetchval(
        "SELECT name_city FROM cities WHERE name_city = $1", name_city # Выполняется SQL-запрос для проверки наличия записи с указанным name_city в таблице cities
    )

    if not city_exist:
        message = f"Город '{name_city}' не найден в базе данных!" # Если city_exist равно None,то есть запись не найдена в БД, формируется сообщение о том, что город не найден
    else: 
        await conn.execute("DELETE FROM cities WHERE name_city = $1", name_city) # Если запись найдена, выполняется SQL-запрос на удаление города
        message = f"Город '{name_city}' успешно удалён!"

    await conn.close()
    return templates.TemplateResponse("delete_city.html", {"request": request, "message": message}) # Передаются объект request и сообщение message, чтобы отобразить статус операции


# Замена атрибута города
@app.post("/update_city_attribute") # Определение маршрута для обработки POST-запроса по URL-адресу в кавычках
async def update_city_attribute(
    request: Request, name_city: str = Form(...), attribute_name: str = Form(...), new_value: str = Form(...) # Объект запроса, содержащий данные от клиента и получение данных из данных формы
):
    conn = await get_db_connection()

    # Проверка существования города
    city_exist = await conn.fetchval(
        "SELECT name_city FROM cities WHERE name_city = $1", name_city # SQL-запрос для проверки, существует ли город с указанным названием name_city
    )

    if not city_exist: # Если город не найден в базе данных
        message = f"Город '{name_city}' не найден в базе данных!"
    else: # Если город найден, продолжается обработка запроса
        if attribute_name == "population": # Проверка, является ли обновляемый атрибут числом
            try:
                new_value = int(new_value) # Попытка преобразовать `new_value` в целое число
            except ValueError:
                raise HTTPException(
                    status_code=400, # Генерация ошибки, если преобразование не удалось
                    detail="Ошибка: количество населения должен быть числом."
                )

        await conn.execute(
            f"UPDATE cities SET {attribute_name} = $1 WHERE name_city = $2", # SQL-запрос для обновления указанного атрибута attribute_name значением new_value
            new_value, name_city
        )
        message = f"Атрибут '{attribute_name}' успешно обновлён на '{new_value}' для города '{name_city}'!"

    await conn.close()
    return templates.TemplateResponse("delete_city.html", {"request": request, "message": message}) # Объект request и сообщение message передаются для отображения статуса операции




@app.post("/addhighway") # Определение маршрута для обработки POST-запроса по URL-адресу в кавычках
async def add_highway(
    request: Request, # Объект запроса, содержащий данные от клиента
    number_highways: int = Form(...), # Получение данных из формы
    city_a: str = Form(...),
    city_b: str = Form(...)
):
    conn = await get_db_connection()
    try:
        # Добавление новой автотрассы
        await conn.execute(
            "INSERT INTO highways (number_highways, city_a, city_b) VALUES ($1, $2, $3)", # Выполняется SQL-запрос на добавление новой записи в таблицу highways
            number_highways, city_a, city_b
        )
        message = f"Автотрасса с номером {number_highways} успешно добавлена!"
    except Exception as e:
        message = f"Ошибка: {str(e)}" # Если произошла ошибка при добавлении записи, формируется сообщение об ошибке с подробной информацией
    finally:
        await conn.close()

    return templates.TemplateResponse("add_highway.html", {"request": request, "message": message})

# Удаление записи автотрассы
@app.post("/delete_highway_record") # Определение маршрута для обработки POST-запроса по URL-адресу в кавычках
async def delete_highway_record(request: Request, number_highways: int = Form(...)):
    conn = await get_db_connection() # Устанавливается подключение к базе данных PostgreSQL

    # Проверка существования автотрассы
    highway_exist = await conn.fetchval(
        "SELECT number_highways FROM highways WHERE number_highways = $1", number_highways # Выполняется SQL-запрос для проверки наличия автотрассы с указанным номером в базе данных
    ) # fetchval() возвращает значение первого столбца первой строки, если запись найдена; иначе возвращает None

    if not highway_exist:
        message = f"Автотрасса №{number_highways} не найдена в базе данных!" # Проверяется результат предыдущего запроса: если трасса не найдена, создается сообщение об ошибке
    else:
        await conn.execute(
            "DELETE FROM highways WHERE number_highways = $1", number_highways # Если трасса найдена, выполняется SQL-запрос DELETE, удаляющий запись с заданным номером автотрассы
        )
        message = f"Автотрасса №{number_highways} успешно удалена!"

    await conn.close()
    return templates.TemplateResponse("delete_highway.html", {"request": request, "message": message})


# Замена атрибута автотрассы
@app.post("/update_highway_attribute") # Определение маршрута для обработки POST-запроса по URL-адресу в кавычках
async def update_highway_attribute(
    request: Request, number_highways: int = Form(...), attribute_name: str = Form(...), new_value: str = Form(...)
):
    conn = await get_db_connection() # Устанавливается подключение к базе данных PostgreSQL

    # Проверка существования автотрассы
    highway_exist = await conn.fetchval(
        "SELECT number_highways FROM highways WHERE number_highways = $1", number_highways # Выполняется SQL-запрос, проверяющий наличие автотрассы с указанным номером
    ) # fetchval() возвращает номер автотрассы, если запись найдена, иначе возвращает None

    if not highway_exist:
        message = f"Автотрасса №{number_highways} не найдена в базе данных!" # Проверяется результат запроса: если трасса отсутствует, создается сообщение об ошибке
    else: # Если трасса найдена
        await conn.execute(
            f"UPDATE highways SET {attribute_name} = $1 WHERE number_highways = $2", # SQL-запрос UPDATE, обновляющий указанное поле attribute_name в таблице highways
            new_value, number_highways # качестве значений подставляются new_value и number_highways
        )
        message = f"Атрибут '{attribute_name}' успешно обновлён на '{new_value}' для автотрассы №{number_highways}!"

    await conn.close()
    return templates.TemplateResponse("delete_highway.html", {"request": request, "message": message})



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


@app.get("/search", response_class=HTMLResponse)
async def search( # Определяется асинхронная функция search
    request: Request, # Cодержит информацию о запросе от клиента
    text: str = Query(...), # Параметр, введенный пользователем
    search_attribute: str = Query(...) # Атрибут, по которому будет выполнен поиск
):
    conn = await get_db_connection()

    try: # Блок обработки исключений для безопасного выполнения операций
        # Данные по умолчанию
        search_cities = [] # Инициализация пустых списков search_cities, search_highways для хранения результатов поиска
        search_highways = []
        message = None # message хранит диагностическое сообщение

        # Поиск по номеру автотрассы
        if search_attribute == "number_highways": # Проверяется, выбран ли атрибут number_highways
            if not text.isdigit():
                message = "Ошибка: Номер автотрассы должен быть числом."
            else:
                highway_value = int(text) # Проверка, что введенное значение text является числом
                # Поиск автотрассы
                search_highways = await conn.fetch(
                    "SELECT * FROM highways WHERE number_highways = $1", highway_value # Выполняется SQL-запрос на поиск автотрассы по number_highways
                )

                # Поиск городов, связанных с найденной трассой
                if search_highways: # Если найдены автотрассы, продолжается поиск городов
                    highway = search_highways[0]
                    search_cities = await conn.fetch(
                        """
                        SELECT * FROM cities
                        WHERE name_city = $1 OR name_city = $2
                        """,
                        highway["city_a"], highway["city_b"]
                    ) # Извлекаются города, которые связаны с найденной трассой
                else:
                    message = "Автотрасса с таким номером не найдена." # Если автотрасса не найдена, устанавливается соответствующее сообщение

        # Поиск по названию города
        elif search_attribute == "name_city": # Проверяется, выбран ли атрибут name_city
            search_cities = await conn.fetch(
                "SELECT * FROM cities WHERE name_city = $1", text # Выполняется SQL-запрос на поиск города по названию
            )

            if search_cities: # Если город найден, ищутся автотрассы, связанные с этим городом
                search_highways = await conn.fetch(
                    "SELECT * FROM highways WHERE city_a = $1 OR city_b = $1", text # Запрашиваются трассы, проходящие через указанный город
                )
            else:
                message = "Город с таким названием не найден." # Если город не найден, формируется диагностическое сообщение

        # Поиск по региону
        elif search_attribute == "region": # Проверяется, выбран ли атрибут region
            search_cities = await conn.fetch(
                "SELECT * FROM cities WHERE region = $1", text # Выполняется поиск городов по региону
            )
            if not search_cities:
                message = "Города с таким регионом не найдены." # Если города не найдены, устанавливается сообщение

        # Поиск по населению
        elif search_attribute == "population": # Проверяется, выбран ли атрибут population
            if not text.isdigit():
                message = "Ошибка: Население должно быть числом." # Проверка, что введенное значение является числом
            else:
                population_value = int(text) # Преобразование text в целое число
                search_cities = await conn.fetch(
                    "SELECT * FROM cities WHERE population = $1", population_value # Выполняется поиск городов с указанным населением
                )
                if not search_cities:
                    message = "Города с таким населением не найдены." # Если города не найдены, выводится сообщение

        # Данные текущего состояния базы
        highways = await conn.fetch("SELECT * FROM highways")
        cities = await conn.fetch("SELECT * FROM cities")

    finally:
        await conn.close()

    return templates.TemplateResponse("mainpage.html", { # Возвращается HTML-шаблон mainpage.html с результатами поиска. Передаются данные об автотрассах, городах, результатах поиска и диагностическом сообщении
        "request": request,
        "highways": highways,
        "cities": cities,
        "search_highways": search_highways,
        "search_cities": search_cities,
        "message": message
    })




# Запуск приложения
if __name__ == "__main__": # Проверка, запущен ли скрипт напрямую
    import uvicorn # Импортируется uvicorn, асинхронный сервер приложений, совместимый с FastAPI. uvicorn запускает приложение на сервере и обрабатывает входящие HTTP-запросы
    uvicorn.run(app, host="0.0.0.0", port=8088) # Запускается сервер uvicorn. app — это экземпляр FastAPI, содержащий определенные маршруты и логику. 
                                                # host="0.0.0.0" — приложение будет доступно из любой сети (включая Docker-контейнеры). port=8088 — указывает порт, на котором будет работать сервер



