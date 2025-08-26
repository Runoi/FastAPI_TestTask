# fastapi_switchable_storage/tests/test_redis_repo.py
#
# Модуль для юнит-тестирования реализации `RedisRepository`.
# Содержит асинхронные тесты для проверки всех CRUD-операций
# (создание, чтение, обновление, удаление, листинг) для элементов Item в Redis.
# Для изоляции и контроля поведения Redis используется мокирование клиента Redis.

import pytest # Фреймворк для тестирования
from unittest.mock import AsyncMock, MagicMock # Инструменты для мокирования асинхронных и обычных объектов
import json # Для работы с JSON-данными

from fastapi_switchable_storage.app.repositories.redis_repo import RedisRepository # Тестируемый репозиторий
from fastapi_switchable_storage.app.schemas import Item, ItemCreate # Pydantic-модели для сущностей
from redis.asyncio import Redis # Асинхронный клиент Redis


# Фикстура pytest для создания и настройки мок-объекта клиента Redis.
# Имитирует поведение настоящего клиента Redis, храня данные во внутреннем словаре.
# Переопределяет асинхронные методы `set`, `get`, `delete`, `incr`, `scan_iter`, `mget`,
# чтобы они работали с внутренним состоянием мока и возвращали ожидаемые значения.
@pytest.fixture
def mock_redis_client():
    # Создаем AsyncMock на основе Redis, чтобы имитировать асинхронные методы.
    mock = AsyncMock(spec=Redis)
    # Внутреннее хранилище для имитации данных Redis.
    mock.mock_data = {}
    # Счетчик для имитации команды INCR.
    mock.next_id_counter = 0

    # Имитация асинхронного метода `set`.
    async def mock_set(key, value):
        str_key = key.decode('utf-8') if isinstance(key, bytes) else key
        mock.mock_data[str_key] = value.decode('utf-8') if isinstance(value, bytes) else value # Сохраняем как строку

    # Имитация асинхронного метода `get`.
    async def mock_get(key):
        str_key = key.decode('utf-8') if isinstance(key, bytes) else key
        val = mock.mock_data.get(str_key)
        return val.encode('utf-8') if isinstance(val, str) else val # Возвращаем как байты

    # Имитация асинхронного метода `delete`.
    async def mock_delete(key):
        str_key = key.decode('utf-8') if isinstance(key, bytes) else key
        if str_key in mock.mock_data:
            del mock.mock_data[str_key]
            return 1 # Возвращаем 1, если ключ был удален
        return 0 # Возвращаем 0, если ключ не был найден
    
    # Синхронная вспомогательная функция для имитации `scan_iter`.
    def mock_keys_sync(pattern):
        str_pattern = pattern.decode('utf-8') if isinstance(pattern, bytes) else pattern
        # Возвращаем ключи, которые начинаются с "item:", имитируя сканирование.
        if str_pattern == "*" or str_pattern == "item:*":
            return [k.encode('utf-8') for k in mock.mock_data.keys() if k.startswith("item:")]
        return []

    # Имитация асинхронного метода `incr`.
    async def mock_incr(key):
        str_key = key.decode('utf-8') if isinstance(key, bytes) else key
        if str_key == "next_item_id":
            mock.next_id_counter += 1
            return mock.next_id_counter
        return 0

    # Присваиваем имитируемые функции соответствующим методам мок-объекта.
    mock.set.side_effect = mock_set
    mock.get.side_effect = mock_get
    mock.delete.side_effect = mock_delete
    # Имитируем `scan_iter` с помощью AsyncIterator для асинхронного итерирования.
    mock.scan_iter.side_effect = lambda pattern: AsyncIterator(mock_keys_sync(pattern))
    
    # Имитация асинхронного метода `mget`.
    async def mock_mget(keys):
        results = []
        for key in keys:
            str_key = key.decode('utf-8') # Декодируем ключ для доступа к mock_data
            val = mock.mock_data.get(str_key)
            results.append(val.encode('utf-8') if isinstance(val, str) else val) # Возвращаем как байты
        return results
    mock.mget.side_effect = mock_mget
    mock.incr.side_effect = mock_incr
    
    return mock # Возвращаем настроенный мок-объект Redis клиента


# Вспомогательный класс для имитации асинхронного итератора.
# Необходим для корректной работы `mock.scan_iter`.
class AsyncIterator:
    def __init__(self, seq):
        self.seq = seq # Последовательность элементов для итерации
        self.i = 0     # Текущий индекс

    # Асинхронный метод для получения следующего элемента.
    async def __anext__(self):
        if self.i >= len(self.seq):
            raise StopAsyncIteration # Останавливаем итерацию, если достигнут конец последовательности
        result = self.seq[self.i]
        self.i += 1
        return result

    # Асинхронный метод для возврата самого себя как итератора.
    def __aiter__(self):
        return self


# Фикстура pytest для создания экземпляра RedisRepository с мокированным клиентом Redis.
# Очищает данные мок-клиента перед каждым тестом, обеспечивая изоляцию.
@pytest.fixture
async def redis_repo(mock_redis_client):
    repo = RedisRepository(redis_client=mock_redis_client) # Создаем репозиторий с мокированным клиентом
    # Очистка внутреннего состояния мок-клиента перед каждым тестом.
    mock_redis_client.mock_data = {}
    mock_redis_client.next_id_counter = 0
    return repo # Возвращаем настроенный RedisRepository


# Тест для асинхронного метода `create_item` в RedisRepository.
# Проверяет, что элемент успешно создается, ему присваивается ID,
# и он корректно сохраняется в имитируемом Redis.
async def test_create_item(redis_repo: RedisRepository, mock_redis_client: MagicMock):
    item_create = ItemCreate(name="Test Item", description="A test item", price=100.0)
    created_item = await redis_repo.create_item(item_create)

    # Проверяем, что ID был присвоен и данные соответствуют.
    assert created_item.id is not None
    assert created_item.name == item_create.name
    assert created_item.description == item_create.description
    assert created_item.price == item_create.price

    # Проверяем, что элемент был сохранен в имитируемом Redis, и данные верны.
    stored_data = await mock_redis_client.get(f"item:{created_item.id}".encode('utf-8'))
    assert stored_data is not None
    stored_item = Item.model_validate_json(stored_data)
    assert stored_item.model_dump() == created_item.model_dump()


# Тест для асинхронного метода `get_item` в RedisRepository.
# Проверяет успешное получение существующего элемента по его ID.
async def test_get_item(redis_repo: RedisRepository, mock_redis_client: MagicMock):
    item_create = ItemCreate(name="Test Item", description="A test item", price=100.0)
    created_item = await redis_repo.create_item(item_create)

    retrieved_item = await redis_repo.get_item(created_item.id)
    assert retrieved_item == created_item


# Тест для асинхронного метода `get_item`, когда элемент не найден.
# Проверяет, что метод возвращает `None` для несуществующего ID.
async def test_get_item_not_found(redis_repo: RedisRepository):
    retrieved_item = await redis_repo.get_item(999)
    assert retrieved_item is None


# Тест для асинхронного метода `list_items` в RedisRepository.
# Проверяет получение списка всех элементов и их количество.
async def test_list_items(redis_repo: RedisRepository, mock_redis_client: MagicMock):
    item1 = await redis_repo.create_item(ItemCreate(name="Item 1", price=10.0))
    item2 = await redis_repo.create_item(ItemCreate(name="Item 2", price=20.0))

    items = await redis_repo.list_items()
    assert len(items) == 2
    assert item1 in items
    assert item2 in items


# Тест для асинхронного метода `list_items` с фильтрами в RedisRepository.
# Проверяет корректность фильтрации по имени и минимальной цене.
async def test_list_items_with_filters(redis_repo: RedisRepository, mock_redis_client: MagicMock):
    await redis_repo.create_item(ItemCreate(name="Apple", price=10.0))
    await redis_repo.create_item(ItemCreate(name="Orange", price=20.0))
    await redis_repo.create_item(ItemCreate(name="Pineapple", price=30.0))

    # Фильтр по имени (частичное совпадение, без учета регистра)
    filtered_by_name = await redis_repo.list_items(name_filter="apple")
    assert len(filtered_by_name) == 2 # Ожидаем "Apple" и "Pineapple"
    assert any(item.name == "Apple" for item in filtered_by_name)
    assert any(item.name == "Pineapple" for item in filtered_by_name)

    # Фильтр по минимальной цене
    filtered_by_price = await redis_repo.list_items(min_price=25.0)
    assert len(filtered_by_price) == 1
    assert filtered_by_price[0].name == "Pineapple"

    # Комбинированный фильтр
    filtered_combined = await redis_repo.list_items(name_filter="apple", min_price=15.0)
    assert len(filtered_combined) == 1
    assert filtered_combined[0].name == "Pineapple"


# Тест для асинхронного метода `update_item` в RedisRepository.
# Проверяет успешное обновление существующего элемента по его ID.
async def test_update_item(redis_repo: RedisRepository, mock_redis_client: MagicMock):
    item_create = ItemCreate(name="Original", description="Old desc", price=50.0)
    created_item = await redis_repo.create_item(item_create)

    updated_data = ItemCreate(name="Updated", description="New desc", price=150.0)
    updated_item = await redis_repo.update_item(created_item.id, updated_data)

    # Проверяем, что элемент был обновлен корректно
    assert updated_item.id == created_item.id
    assert updated_item.name == updated_data.name
    assert updated_item.description == updated_data.description
    assert updated_item.price == updated_data.price

    # Проверяем, что элемент был обновлен в имитируемом Redis, и данные верны.
    stored_data = await mock_redis_client.get(f"item:{created_item.id}".encode('utf-8'))
    assert stored_data is not None
    stored_item = Item.model_validate_json(stored_data)
    assert stored_item.model_dump() == updated_item.model_dump()


# Тест для асинхронного метода `update_item`, когда элемент не найден.
# Проверяет, что метод возвращает `None` при попытке обновить несуществующий элемент.
async def test_update_item_not_found(redis_repo: RedisRepository):
    updated_data = ItemCreate(name="Updated", description="New desc", price=150.0)
    updated_item = await redis_repo.update_item(999, updated_data)
    assert updated_item is None


# Тест для асинхронного метода `delete_item` в RedisRepository.
# Проверяет успешное удаление существующего элемента по его ID.
async def test_delete_item(redis_repo: RedisRepository, mock_redis_client: MagicMock):
    item_create = ItemCreate(name="To Delete", price=1.0)
    created_item = await redis_repo.create_item(item_create)

    deleted = await redis_repo.delete_item(created_item.id)
    assert deleted is True

    # Проверяем, что элемент был удален из имитируемого Redis.
    stored_data = await mock_redis_client.get(f"item:{created_item.id}".encode('utf-8'))
    assert stored_data is None


# Тест для асинхронного метода `delete_item`, когда элемент не найден.
# Проверяет, что метод возвращает `False` при попытке удалить несуществующий элемент.
async def test_delete_item_not_found(redis_repo: RedisRepository):
    deleted = await redis_repo.delete_item(999)
    assert deleted is False
