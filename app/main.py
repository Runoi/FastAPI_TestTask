
# fastapi_switchable_storage/app/main.py
#
# Главный файл приложения FastAPI.
# Определяет создание экземпляра FastAPI, управление жизненным циклом приложения
# (инициализация БД, подключение/отключение к Redis) и все маршруты API (эндпоинты CRUD)
# для сущностей Item.

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query

from app.schemas import Item, ItemCreate
from app.repositories.base import BaseRepository
from app.dependencies import get_repository, connect_to_redis, close_redis_connection
from app.database import init_db
from app.config import settings, StorageType


# Контекстный менеджер lifespan для управления ресурсами приложения.
# Выполняет инициализацию при старте приложения (до yield) и очистку при завершении (после yield).
# Это гарантирует правильное подключение и отключение к базам данных (SQLite, Redis).
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация SQLite базы данных, если выбран соответствующий тип хранилища.
    if settings.STORAGE_TYPE == StorageType.SQLITE:
        print("Инициализация базы данных SQLite...")
        await init_db()  # Вызываем функцию инициализации БД
        print("База данных SQLite инициализирована.")
    # Подключение к Redis, если выбран соответствующий тип хранилища.
    elif settings.STORAGE_TYPE == StorageType.REDIS:
        await connect_to_redis() # Вызываем функцию подключения к Redis
    yield  # Здесь начинается жизненный цикл приложения (обработка HTTP-запросов)
    # Закрытие соединения с Redis при завершении работы приложения.
    if settings.STORAGE_TYPE == StorageType.REDIS:
        await close_redis_connection() # Вызываем функцию отключения от Redis


# Функция для создания и настройки экземпляра FastAPI приложения.
# Это позволяет создавать чистые экземпляры приложения для тестирования.
def create_fastapi_app() -> FastAPI:
    app_instance = FastAPI(
        title="FastAPI API с переключаемым хранилищем", # Название API для документации
        description="CRUD API для сущностей Item с возможностью переключения бэкендов хранения данных (In-Memory, SQLite, Redis)", # Описание API
        version="1.0.0", # Версия API
        lifespan=lifespan  # Применяем контекстный менеджер lifespan для управления ресурсами
    )

    # Эндпоинт для создания нового элемента (Item).
    # Принимает Pydantic-модель ItemCreate в теле запроса и возвращает созданный Item с присвоенным ID.
    # Использует систему Dependency Injection FastAPI для получения нужного репозитория (InMemory, SQLite, Redis).
    @app_instance.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED)
    async def create_item(item: ItemCreate, repository: BaseRepository = Depends(get_repository)):
        return await repository.create_item(item)

    # Эндпоинт для получения списка элементов (Item).
    # Поддерживает опциональную фильтрацию по имени (частичное совпадение, без учета регистра)
    # и по минимальной цене через Query-параметры. Возвращает список объектов Item.
    @app_instance.get("/items/", response_model=List[Item])
    async def list_items(
        repository: BaseRepository = Depends(get_repository),  # Получаем репозиторий через DI
        name_filter: Optional[str] = Query(
            None,
            description="Фильтрация элементов по имени (без учета регистра, частичное совпадение)"
        ),
        min_price: Optional[float] = Query(
            None,
            gt=0, # Значение должно быть больше нуля
            description="Фильтрация элементов по минимальной цене (должна быть больше нуля)"
        )
    ):
        return await repository.list_items(name_filter=name_filter, min_price=min_price)

    # Эндпоинт для получения одного элемента по его уникальному ID.
    # Если элемент с указанным ID не найден, возвращает HTTP 404 Not Found ошибку.
    @app_instance.get("/items/{item_id}", response_model=Item)
    async def get_item(item_id: int, repository: BaseRepository = Depends(get_repository)):
        item = await repository.get_item(item_id)  # Пытаемся получить элемент
        if item is None:
            # Если элемент не найден, выбрасываем исключение HTTPException
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        return item # Возвращаем найденный элемент

    # Эндпоинт для обновления существующего элемента по его ID.
    # Принимает ID элемента в пути и Pydantic-модель ItemCreate с обновленными данными в теле запроса.
    # Если элемент не найден, возвращает HTTP 404 Not Found ошибку.
    @app_instance.put("/items/{item_id}", response_model=Item)
    async def update_item(item_id: int, item: ItemCreate, repository: BaseRepository = Depends(get_repository)):
        updated_item = await repository.update_item(item_id, item)  # Пытаемся обновить элемент
        if updated_item is None:
            # Если элемент для обновления не найден, выбрасываем исключение HTTPException
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        return updated_item # Возвращаем обновленный элемент

    # Эндпоинт для удаления элемента по его ID.
    # Если элемент не найден, возвращает HTTP 404 Not Found ошибку.
    # При успешном удалении возвращает HTTP 204 No Content (без тела ответа).
    @app_instance.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(item_id: int, repository: BaseRepository = Depends(get_repository)):
        if not await repository.delete_item(item_id):
            # Если элемент для удаления не найден, выбрасываем исключение HTTPException
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент не найден")
        return  # При успешном удалении ничего не возвращаем (FastAPI автоматически установит 204 No Content)
    
    return app_instance # Возвращаем настроенный экземпляр приложения

# Создание экземпляра FastAPI приложения для запуска.
# Эта глобальная переменная используется Uvicorn для запуска приложения.
app = create_fastapi_app()
