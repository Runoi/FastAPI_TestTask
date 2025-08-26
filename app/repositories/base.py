
# fastapi_switchable_storage/app/repositories/base.py
#
# Этот модуль определяет абстрактный базовый класс `BaseRepository`,
# который служит контрактом для всех конкретных реализаций репозиториев
# в приложении. Паттерн "Репозиторий" абстрагирует слой доступа к данным,
# позволяя бизнес-логике быть независимой от деталей хранения (например,
# In-Memory, SQLite, Redis). Все методы являются асинхронными.

from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas import ItemCreate, Item


# Абстрактный базовый класс BaseRepository (ABC - Abstract Base Class).
# Все конкретные реализации репозиториев (например, InMemoryRepository,
# SQLiteRepository, RedisRepository) должны наследовать от этого класса
# и реализовать все его абстрактные методы, помеченные `@abstractmethod`.
class BaseRepository(ABC):
    # Абстрактный асинхронный метод для получения одного элемента по его уникальному ID.
    # Возвращает объект `Item` или `None`, если элемент не найден.
    @abstractmethod
    async def get_item(self, item_id: int) -> Optional[Item]:
        pass # Дочерние классы должны реализовать эту логику

    # Абстрактный асинхронный метод для получения списка элементов.
    # Позволяет опционально фильтровать элементы по имени (частичное совпадение,
    # без учета регистра) и по минимальной цене.
    # Возвращает список объектов `Item`.
    @abstractmethod
    async def list_items(self, name_filter: Optional[str] = None, min_price: Optional[float] = None) -> List[Item]:
        pass # Дочерние классы должны реализовать эту логику

    # Абстрактный асинхронный метод для создания нового элемента.
    # Принимает Pydantic-модель `ItemCreate` (без ID) и возвращает
    # созданный объект `Item` с уже присвоенным уникальным ID.
    @abstractmethod
    async def create_item(self, item: ItemCreate) -> Item:
        pass # Дочерние классы должны реализовать эту логику

    # Абстрактный асинхронный метод для обновления существующего элемента по его ID.
    # Принимает уникальный `item_id` и Pydantic-модель `ItemCreate` с
    # обновленными данными. Возвращает обновленный объект `Item` или `None`,
    # если элемент с таким ID не найден.
    @abstractmethod
    async def update_item(self, item_id: int, item: ItemCreate) -> Optional[Item]:
        pass # Дочерние классы должны реализовать эту логику

    # Абстрактный асинхронный метод для удаления элемента по его ID.
    # Возвращает `True` в случае успешного удаления и `False`, если элемент
    # с указанным ID не был найден.
    @abstractmethod
    async def delete_item(self, item_id: int) -> bool:
        pass # Дочерние классы должны реализовать эту логику
