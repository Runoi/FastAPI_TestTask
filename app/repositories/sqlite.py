
# fastapi_switchable_storage/app/repositories/sqlite.py
#
# Реализация репозитория для работы с элементами (Item) в базе данных SQLite.
# Этот репозиторий использует асинхронный драйвер `aiosqlite` для выполнения
# CRUD-операций с таблицей 'items', обеспечивая персистентное хранение данных
# в файловой базе данных SQLite.

from typing import List, Optional
import aiosqlite
from app.schemas import Item, ItemCreate
from .base import BaseRepository
from app.database import get_db_connection


# Класс SQLiteRepository, реализующий интерфейс BaseRepository для работы с SQLite.
# Отвечает за взаимодействие с SQLite для хранения, извлечения, обновления
# и удаления сущностей Item, используя асинхронные операции.
class SQLiteRepository(BaseRepository):
    # Асинхронный метод для получения одного элемента по его уникальному ID.
    # Подключается к базе данных, выполняет параметризованный SELECT-запрос,
    # чтобы избежать SQL-инъекций, и возвращает объект `Item`, если запись найдена.
    # Возвращает `None`, если элемент с указанным ID не существует.
    async def get_item(self, item_id: int) -> Optional[Item]:
        # Используем асинхронный контекстный менеджер для управления соединением с БД.
        async for db in get_db_connection():  # Получаем асинхронное соединение с БД
            cursor = await db.execute(
                "SELECT id, name, description, price FROM items WHERE id = ?", # SQL запрос
                (item_id,) # Параметры запроса (кортеж)
            ) # Выполняем SELECT запрос
            row = await cursor.fetchone()      # Получаем одну запись (строку) из результата запроса
            if row:
                # Создаем объект Item из данных полученной строки по индексу
                return Item(id=row[0], name=row[1], description=row[2], price=row[3])
        return None # Элемент не найден или соединение с БД не установлено

    # Асинхронный метод для получения списка всех элементов.
    # Поддерживает опциональную фильтрацию элементов:
    #   - `name_filter`: фильтрация по имени (частичное совпадение, без учета регистра).
    #   - `min_price`: фильтрация по минимальной цене (элементы с ценой ниже будут исключены).
    # Возвращает список отфильтрованных объектов `Item`.
    async def list_items(self, name_filter: Optional[str] = None, min_price: Optional[float] = None) -> List[Item]:
        async for db in get_db_connection(): # Получаем асинхронное соединение с БД
            query = "SELECT id, name, description, price FROM items WHERE 1=1" # Базовый SQL запрос (1=1 для удобства добавления условий)
            params = [] # Список для хранения параметров SQL запроса

            # Если задан фильтр по имени, добавляем условие `LIKE` и параметр с подстановочными знаками.
            if name_filter:
                query += " AND LOWER(name) LIKE LOWER(?)"
                params.append(f"%{name_filter}%")
            # Если задан фильтр по минимальной цене, добавляем условие `>=` и параметр.
            if min_price:
                query += " AND price >= ?"
                params.append(min_price)
            
            # Добавляем сортировку для стабильного порядка элементов (например, по ID)
            query += " ORDER BY id"

            cursor = await db.execute(query, tuple(params)) # Выполняем запрос с параметрами
            rows = await cursor.fetchall()                  # Получаем все найденные записи (список кортежей)
            # Преобразуем каждую строку в объект Item и возвращаем список
            return [Item(id=row[0], name=row[1], description=row[2], price=row[3]) for row in rows]

    # Асинхронный метод для создания нового элемента.
    # Вставляет новую запись в таблицу 'items' с данными из `item_create`.
    # После успешной вставки возвращает созданный объект `Item` с автоматически
    # присвоенным SQLite ID (`cursor.lastrowid`).
    async def create_item(self, item_create: ItemCreate) -> Item:
        async for db in get_db_connection(): # Получаем асинхронное соединение с БД
            cursor = await db.execute(
                "INSERT INTO items (name, description, price) VALUES (?, ?, ?)", # SQL INSERT запрос
                (item_create.name, item_create.description, item_create.price) # Значения для вставки
            ) # Выполняем INSERT запрос
            await db.commit() # Применяем изменения к базе данных
            # Возвращаем созданный Item, используя `cursor.lastrowid` для получения ID
            return Item(id=cursor.lastrowid, **item_create.model_dump()) # Создаем и возвращаем Item

    # Асинхронный метод для обновления существующего элемента по его ID.
    # Обновляет поля записи в таблице 'items' по заданному `item_id` данными из `item_update`.
    # Возвращает обновленный объект `Item`, если запись была найдена и обновлена.
    # Возвращает `None`, если элемент с указанным ID не найден для обновления.
    async def update_item(self, item_id: int, item_update: ItemCreate) -> Optional[Item]:
        async for db in get_db_connection(): # Получаем асинхронное соединение с БД
            cursor = await db.execute(
                "UPDATE items SET name = ?, description = ?, price = ? WHERE id = ?", # SQL UPDATE запрос
                (item_update.name, item_update.description, item_update.price, item_id) # Значения и условие WHERE
            ) # Выполняем UPDATE запрос
            await db.commit() # Применяем изменения
            if cursor.rowcount > 0:
                # Если строка была обновлена (rowcount > 0), получаем и возвращаем обновленный элемент.
                return await self.get_item(item_id)
        return None # Элемент не найден для обновления или соединение с БД не установлено

    # Асинхронный метод для удаления элемента по его ID.
    # Удаляет запись из таблицы 'items' по заданному `item_id`.
    # Возвращает `True`, если элемент был успешно удален (то есть, `rowcount > 0`).
    # Возвращает `False`, если элемент с указанным ID не был найден для удаления.
    async def delete_item(self, item_id: int) -> bool:
        async for db in get_db_connection(): # Получаем асинхронное соединение с БД
            cursor = await db.execute("DELETE FROM items WHERE id = ?", (item_id,)) # Выполняем DELETE запрос
            await db.commit() # Применяем изменения
            # Возвращаем True, если была удалена хотя бы одна строка (cursor.rowcount > 0)
            return cursor.rowcount > 0 # Проверяем, была ли удалена хотя бы одна строка
