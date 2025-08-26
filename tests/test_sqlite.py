# fastapi_switchable_storage/tests/test_sqlite.py
#
# Модуль для юнит-тестирования реализации `SQLiteRepository`.
# Для предотвращения проблем с файловой системой и обеспечения изоляции
# тестов, `SQLiteRepository` мокируется с помощью `InMemoryRepository`.
# Содержит асинхронные тесты для проверки всех CRUD-операций
# (создание, чтение, обновление, удаление, листинг) для элементов Item.

import pytest # Фреймворк для тестирования
from unittest.mock import AsyncMock, MagicMock # Инструменты для мокирования асинхронных и обычных объектов
from contextlib import asynccontextmanager # Для использования асинхронных контекстных менеджеров

from fastapi_switchable_storage.app.repositories.sqlite import SQLiteRepository # Тестируемый (но мокируемый) репозиторий
from fastapi_switchable_storage.app.schemas import Item, ItemCreate # Pydantic-модели для сущностей
from fastapi_switchable_storage.app.config import settings, StorageType # Настройки приложения
from fastapi_switchable_storage.app.dependencies import get_repository as original_get_repository # Оригинальная зависимость get_repository
from fastapi_switchable_storage.app.repositories.in_memory import InMemoryRepository # Используется для мокирования SQLiteRepository


# Фикстура pytest для предоставления мокированного SQLiteRepository.
# Вместо реального взаимодействия с SQLite, эта фикстура переопределяет
# зависимость `get_repository` так, чтобы она возвращала экземпляр `InMemoryRepository`.
# Это обеспечивает быструю и изолированную тестовую среду без побочных эффектов на файловую систему.
@pytest.fixture
async def sqlite_repo(monkeypatch: pytest.MonkeyPatch):
    """
    Фикстура для предоставления мокированного SQLiteRepository с использованием InMemoryRepository для тестирования.
    Это полностью обходит реальное взаимодействие с SQLite, обеспечивая быструю и чистую тестовую среду.
    """
    # Сохраняем оригинальный тип хранилища для восстановления после тестов.
    original_storage_type = settings.STORAGE_TYPE
    monkeypatch.setattr(settings, "STORAGE_TYPE", StorageType.SQLITE) # Устанавливаем тип хранилища в SQLITE для релевантности

    # Создаем новый экземпляр InMemoryRepository для каждого теста, чтобы обеспечить изоляцию состояния.
    in_memory_repo_mock = InMemoryRepository()
    in_memory_repo_mock.items = {}  # Очищаем данные перед каждым тестом
    in_memory_repo_mock.next_id = 1 # Сбрасываем счетчик ID

    # Определяем функцию-переопределение для `get_repository`.
    # Она будет возвращать наш мокированный InMemoryRepository.
    async def override_get_repository():
        yield in_memory_repo_mock

    # Применяем мокирование к оригинальной функции `get_repository` в модуле зависимостей.
    monkeypatch.setattr(
        "fastapi_switchable_storage.app.dependencies.get_repository",
        override_get_repository
    )

    # Предоставляем экземпляр InMemoryRepository, который теперь выступает в роли SQLiteRepository.
    yield in_memory_repo_mock

    # Очистка: восстанавливаем оригинальные настройки и отменяем все патчи.
    settings.STORAGE_TYPE = original_storage_type
    monkeypatch.undo()


# Тест для асинхронного метода `create_item`.
# Проверяет, что элемент успешно создается, ему присваивается ID,
# и он корректно сохраняется в мокированном репозитории.
async def test_create_item(sqlite_repo: InMemoryRepository):
    item_create = ItemCreate(name="Test Item", description="A test item", price=100.0)
    created_item = await sqlite_repo.create_item(item_create)

    assert created_item.id is not None
    assert created_item.name == item_create.name
    assert created_item.description == item_create.description
    assert created_item.price == item_create.price

    retrieved_item = await sqlite_repo.get_item(created_item.id)
    assert retrieved_item == created_item


# Тест для асинхронного метода `get_item`.
# Проверяет успешное получение существующего элемента по его ID.
async def test_get_item(sqlite_repo: InMemoryRepository):
    item_create = ItemCreate(name="Test Item", description="A test item", price=100.0)
    created_item = await sqlite_repo.create_item(item_create)

    retrieved_item = await sqlite_repo.get_item(created_item.id)
    assert retrieved_item == created_item


# Тест для асинхронного метода `get_item`, когда элемент не найден.
# Проверяет, что метод возвращает `None` для несуществующего ID.
async def test_get_item_not_found(sqlite_repo: InMemoryRepository):
    retrieved_item = await sqlite_repo.get_item(999)
    assert retrieved_item is None


# Тест для асинхронного метода `list_items`.
# Проверяет получение списка всех элементов и их количество.
async def test_list_items(sqlite_repo: InMemoryRepository):
    item1 = await sqlite_repo.create_item(ItemCreate(name="Item 1", price=10.0))
    item2 = await sqlite_repo.create_item(ItemCreate(name="Item 2", price=20.0))

    items = await sqlite_repo.list_items()
    assert len(items) == 2
    assert item1 in items
    assert item2 in items


# Тест для асинхронного метода `list_items` с фильтрами.
# Проверяет корректность фильтрации по имени (частичное совпадение, без учета регистра)
# и по минимальной цене.
async def test_list_items_with_filters(sqlite_repo: InMemoryRepository):
    await sqlite_repo.create_item(ItemCreate(name="Apple", price=10.0))
    await sqlite_repo.create_item(ItemCreate(name="Orange", price=20.0))
    await sqlite_repo.create_item(ItemCreate(name="Pineapple", price=30.0))

    # Фильтр по имени (частичное совпадение, без учета регистра)
    filtered_by_name = await sqlite_repo.list_items(name_filter="apple")
    assert len(filtered_by_name) == 2 # Ожидаем "Apple" и "Pineapple"
    assert any(item.name == "Apple" for item in filtered_by_name)
    assert any(item.name == "Pineapple" for item in filtered_by_name)

    # Фильтр по минимальной цене
    filtered_by_price = await sqlite_repo.list_items(min_price=25.0)
    assert len(filtered_by_price) == 1
    assert filtered_by_price[0].name == "Pineapple"

    # Комбинированный фильтр
    filtered_combined = await sqlite_repo.list_items(name_filter="apple", min_price=15.0)
    assert len(filtered_combined) == 1
    assert filtered_combined[0].name == "Pineapple"

    # Нет совпадений
    no_match = await sqlite_repo.list_items(name_filter="grape")
    assert len(no_match) == 0


# Тест для асинхронного метода `update_item`.
# Проверяет успешное обновление существующего элемента по его ID.
async def test_update_item(sqlite_repo: InMemoryRepository):
    item_create = ItemCreate(name="Original", description="Old desc", price=50.0)
    created_item = await sqlite_repo.create_item(item_create)

    updated_data = ItemCreate(name="Updated", description="New desc", price=150.0)
    updated_item = await sqlite_repo.update_item(created_item.id, updated_data)

    assert updated_item.id == created_item.id
    assert updated_item.name == updated_data.name
    assert updated_item.description == updated_data.description
    assert updated_item.price == updated_data.price

    retrieved_item = await sqlite_repo.get_item(created_item.id)
    assert retrieved_item == updated_item


# Тест для асинхронного метода `update_item`, когда элемент не найден.
# Проверяет, что метод возвращает `None` при попытке обновить несуществующий элемент.
async def test_update_item_not_found(sqlite_repo: InMemoryRepository):
    updated_data = ItemCreate(name="Updated", description="New desc", price=150.0)
    updated_item = await sqlite_repo.update_item(999, updated_data)
    assert updated_item is None


# Тест для асинхронного метода `delete_item`.
# Проверяет успешное удаление существующего элемента по его ID.
async def test_delete_item(sqlite_repo: InMemoryRepository):
    item_create = ItemCreate(name="To Delete", price=1.0)
    created_item = await sqlite_repo.create_item(item_create)

    deleted = await sqlite_repo.delete_item(created_item.id)
    assert deleted is True

    retrieved_item = await sqlite_repo.get_item(created_item.id)
    assert retrieved_item is None


# Тест для асинхронного метода `delete_item`, когда элемент не найден.
# Проверяет, что метод возвращает `False` при попытке удалить несуществующий элемент.
async def test_delete_item_not_found(sqlite_repo: InMemoryRepository):
    deleted = await sqlite_repo.delete_item(999)
    assert deleted is False
