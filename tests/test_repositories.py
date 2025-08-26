# fastapi_switchable_storage/tests/test_repositories.py
#
# Модуль для юнит-тестирования реализации `InMemoryRepository`.
# Содержит асинхронные тесты для проверки всех CRUD-операций:
# создание, чтение, обновление, удаление и листинг элементов.
# Использует фикстуру `in_memory_repo` для предоставления изолированного
# экземпляра репозитория для каждого теста.

import pytest # Фреймворк для тестирования
import asyncio # Модуль для асинхронного программирования

from fastapi_switchable_storage.app.repositories.in_memory import InMemoryRepository # Тестируемый репозиторий
from fastapi_switchable_storage.app.schemas import Item, ItemCreate # Pydantic-модели для сущностей


# Фикстура pytest, которая предоставляет изолированный экземпляр InMemoryRepository
# для каждого асинхронного теста. Она сбрасывает состояние репозитория (очищает items)
# перед каждым тестом, чтобы обеспечить чистое и независимое выполнение тестов.
@pytest.fixture
async def in_memory_repo():
    repo = InMemoryRepository() # Создаем новый экземпляр репозитория
    repo.items = {}             # Очищаем словарь элементов, чтобы гарантировать чистое состояние
    yield repo                  # Предоставляем репозиторий тесту


# Тест для асинхронного метода `create_item`.
# Проверяет, что элемент успешно создается, ему присваивается ID,
# и он корректно сохраняется в репозитории.
async def test_create_item(in_memory_repo):
    # Создаем данные для нового элемента
    item_data = ItemCreate(name="Test Item", description="This is a test item.", price=10.0)
    # Вызываем метод создания элемента
    created_item = await in_memory_repo.create_item(item_data)

    # Проверяем, что созданный элемент соответствует ожидаемым данным
    assert created_item.name == "Test Item"
    assert created_item.description == "This is a test item."
    assert created_item.price == 10.0
    assert created_item.id is not None # Проверяем, что ID был присвоен
    # Проверяем, что элемент действительно добавлен в хранилище
    assert in_memory_repo.items[created_item.id] == created_item


# Тест для асинхронного метода `get_item`.
# Проверяет успешное получение существующего элемента по его ID.
async def test_get_item(in_memory_repo):
    # Создаем элемент, который затем будем получать
    item_data = ItemCreate(name="Test Item", description="This is a test item.", price=10.0)
    created_item = await in_memory_repo.create_item(item_data)
    # Пытаемся получить созданный элемент по его ID
    retrieved_item = await in_memory_repo.get_item(created_item.id)

    # Проверяем, что полученный элемент идентичен созданному
    assert retrieved_item == created_item


# Тест для асинхронного метода `get_item`, когда элемент не найден.
# Проверяет, что метод возвращает `None` для несуществующего ID.
async def test_get_item_not_found(in_memory_repo):
    # Пытаемся получить элемент с несуществующим ID
    retrieved_item = await in_memory_repo.get_item(999)
    # Проверяем, что результат равен None
    assert retrieved_item is None


# Тест для асинхронного метода `list_items`.
# Проверяет получение списка всех элементов и их количество.
async def test_list_items(in_memory_repo):
    # Создаем два элемента
    item1_data = ItemCreate(name="Item 1", description="Content 1", price=1.0)
    item2_data = ItemCreate(name="Item 2", description="Content 2", price=2.0)
    created_item1 = await in_memory_repo.create_item(item1_data)
    created_item2 = await in_memory_repo.create_item(item2_data)

    # Получаем список всех элементов
    all_items = await in_memory_repo.list_items()

    # Проверяем, что список содержит два элемента и что они соответствуют созданным
    assert len(all_items) == 2
    assert created_item1 in all_items
    assert created_item2 in all_items


# Тест для асинхронного метода `update_item`.
# Проверяет успешное обновление существующего элемента по его ID.
async def test_update_item(in_memory_repo):
    # Создаем исходный элемент
    item_data = ItemCreate(name="Original Name", description="Original Description", price=5.0)
    created_item = await in_memory_repo.create_item(item_data)
    # Создаем данные для обновления
    updated_data = ItemCreate(name="Updated Name", description="Updated Description", price=15.0)
    # Вызываем метод обновления
    updated_item = await in_memory_repo.update_item(created_item.id, updated_data)

    # Проверяем, что элемент был успешно обновлен и его поля изменились
    assert updated_item.name == "Updated Name"
    assert updated_item.description == "Updated Description"
    assert updated_item.price == 15.0
    # Проверяем, что обновленный элемент присутствует в хранилище по тому же ID
    assert in_memory_repo.items[created_item.id] == updated_item


# Тест для асинхронного метода `update_item`, когда элемент не найден.
# Проверяет, что метод возвращает `None` при попытке обновить несуществующий элемент.
async def test_update_item_not_found(in_memory_repo):
    # Создаем данные для обновления
    updated_data = ItemCreate(name="Updated Name", description="Updated Description", price=15.0)
    # Пытаемся обновить элемент с несуществующим ID
    updated_item = await in_memory_repo.update_item(999, updated_data)
    # Проверяем, что результат равен None
    assert updated_item is None


# Тест для асинхронного метода `delete_item`.
# Проверяет успешное удаление существующего элемента по его ID.
async def test_delete_item(in_memory_repo):
    # Создаем элемент, который затем будем удалять
    item_data = ItemCreate(name="Test Item", description="This is a test item.", price=10.0)
    created_item = await in_memory_repo.create_item(item_data)
    # Вызываем метод удаления
    deleted = await in_memory_repo.delete_item(created_item.id)

    # Проверяем, что удаление прошло успешно
    assert deleted is True
    # Проверяем, что элемент больше не присутствует в хранилище
    assert created_item.id not in in_memory_repo.items


# Тест для асинхронного метода `delete_item`, когда элемент не найден.
# Проверяет, что метод возвращает `False` при попытке удалить несуществующий элемент.
async def test_delete_item_not_found(in_memory_repo):
    # Пытаемся удалить элемент с несуществующим ID
    deleted = await in_memory_repo.delete_item(999)
    # Проверяем, что результат равен False
    assert deleted is False
