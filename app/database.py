
# fastapi_switchable_storage/app/database.py
#
# Модуль для работы с базой данных SQLite.
# Предоставляет функции для получения асинхронного соединения с базой данных
# и инициализации ее схемы (создания таблиц).

import aiosqlite
from app.config import settings


# Асинхронный генератор, который предоставляет соединение с базой данных SQLite.
# Используется в Dependency Injection FastAPI для управления жизненным циклом соединения:
# соединение открывается в начале запроса и закрывается после его завершения.
async def get_db_connection():
    # Открываем асинхронное соединение с базой данных SQLite.
    # Путь к базе данных берется из настроек приложения (settings.SQLITE_DATABASE_URL).
    async with aiosqlite.connect(settings.SQLITE_DATABASE_URL) as db:
        yield db  # Передаем объект соединения потребителю (например, репозиторию)


# Асинхронная функция для инициализации схемы базы данных SQLite.
# Создает таблицу 'items' с необходимыми полями, если она еще не существует.
# Эта функция вызывается при старте приложения через механизм lifespan в main.py.
async def init_db():
    # Открываем соединение для выполнения инициализационных запросов.
    async with aiosqlite.connect(settings.SQLITE_DATABASE_URL) as db:
        # Выполняем SQL-запрос для создания таблицы items.
        # Таблица включает поля:
        #   - id: INTEGER PRIMARY KEY AUTOINCREMENT (уникальный ID, автоматически увеличивается)
        #   - name: TEXT NOT NULL (наименование предмета, обязательное поле)
        #   - description: TEXT (описание предмета, опциональное поле)
        #   - price: REAL NOT NULL (цена предмета, вещественное число, обязательное поле)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)
        await db.commit()  # Применяем изменения (создание таблицы) к базе данных
