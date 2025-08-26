
# app/dependencies.py
#
# Этот модуль отвечает за логику Dependency Injection в FastAPI.
# Он определяет, какой репозиторий должен быть предоставлен эндпоинтам
# в зависимости от конфигурации STORAGE_TYPE.

from typing import AsyncGenerator, Optional
from redis.asyncio import Redis

from app.config import settings, StorageType
from app.repositories.base import BaseRepository
from app.repositories.in_memory import InMemoryRepository
from app.repositories.sqlite import SQLiteRepository
from app.repositories.redis_repo import RedisRepository


# Глобальный экземпляр клиента Redis для обеспечения синглтона
# (чтобы не создавать новые подключения при каждом запросе).
# In-Memory репозиторий будет создаваться по запросу для каждого вызова get_repository, чтобы избежать утечек состояния.
_redis_client: Optional[Redis] = None


# Асинхронный генератор, который предоставляет экземпляр BaseRepository.
# FastAPI использует эту функцию как зависимость для эндпоинтов,
# автоматически выбирая нужную реализацию репозитория в зависимости от STORAGE_TYPE.
async def get_repository() -> AsyncGenerator[BaseRepository, None]:
    global _redis_client # Объявляем использование глобальной переменной Redis

    # Выбор репозитория в зависимости от значения STORAGE_TYPE из настроек.
    if settings.STORAGE_TYPE == StorageType.IN_MEMORY:
        # Для In-Memory репозитория всегда создаем новый экземпляр,
        # чтобы обеспечить изоляцию состояния между запросами/тестами.
        yield InMemoryRepository()
    elif settings.STORAGE_TYPE == StorageType.SQLITE:
        # Для SQLite создаем новый экземпляр репозитория при каждом запросе.
        # Соединение с БД управляется функцией get_db_connection через lifespan (в main.py).
        yield SQLiteRepository()
    elif settings.STORAGE_TYPE == StorageType.REDIS:
        # Если Redis клиент еще не создан, создаем его на основе REDIS_URL.
        # Используем синглтон для клиента Redis, чтобы не открывать много соединений.
        if _redis_client is None:
            _redis_client = Redis.from_url(settings.REDIS_URL)
        yield RedisRepository(redis_client=_redis_client) # Передаем клиент Redis в репозиторий
    else:
        # В случае неизвестного типа хранилища вызываем исключение.
        raise ValueError(f"Неизвестный тип хранилища: {settings.STORAGE_TYPE}")


# Асинхронная функция для подключения к Redis при старте приложения.
# Вызывается в рамках контекстного менеджера lifespan в main.py.
# Устанавливает глобальный клиент Redis и проверяет соединение.
async def connect_to_redis():
    global _redis_client
    # Подключаемся к Redis только если выбран тип хранилища REDIS.
    if settings.STORAGE_TYPE == StorageType.REDIS:
        print("Подключение к Redis...")
        _redis_client = Redis.from_url(settings.REDIS_URL)
        try:
            await _redis_client.ping() # Проверяем соединение с Redis
            print("Подключение к Redis установлено!")
        except Exception as e:
            print(f"Не удалось подключиться к Redis: {e}")
            _redis_client = None # Сбрасываем клиент, если подключение не удалось


# Асинхронная функция для закрытия соединения с Redis при завершении работы приложения.
# Вызывается в рамках контекстного менеджера lifespan в main.py.
# Корректно закрывает активное соединение с Redis, если оно существует.
async def close_redis_connection():
    global _redis_client
    # Закрываем соединение только если клиент Redis существует и активен.
    if _redis_client:
        print("Закрытие соединения с Redis...")
        await _redis_client.close() # Закрываем соединение
        print("Соединение с Redis закрыто.")
