# fastapi_switchable_storage/tests/test_api.py
#
# Модуль для юнит-тестирования API-эндпоинтов приложения FastAPI.
# Использует `TestClient` из FastAPI для симуляции HTTP-запросов
# и `pytest` для организации тестов. Фикстура `client` настраивает
# изолированное тестовое окружение для каждого теста, используя
# In-Memory репозиторий.

from fastapi.testclient import TestClient # Инструмент для тестирования FastAPI приложений
import pytest                         # Фреймворк для тестирования
import asyncio                        # Модуль для асинхронного программирования (хотя здесь напрямую не используется)
from unittest.mock import AsyncMock   # Для мокирования асинхронных объектов

from fastapi_switchable_storage.app.main import create_fastapi_app # Импортируем функцию для создания экземпляра FastAPI
from fastapi_switchable_storage.app.dependencies import get_repository # Импортируем функцию получения репозитория
from fastapi_switchable_storage.app.repositories.in_memory import InMemoryRepository # Конкретная реализация In-Memory репозитория
from fastapi_switchable_storage.app.schemas import Item, ItemCreate # Pydantic-модели для сущностей
from fastapi_switchable_storage.app.config import settings, StorageType # Настройки приложения


# Фикстура pytest для настройки тестового клиента FastAPI.
# Обеспечивает изолированное тестовое окружение для каждого теста API:
# 1. Временно устанавливает STORAGE_TYPE в IN_MEMORY, чтобы использовать InMemoryRepository.
# 2. Мокирует функцию `get_repository`, чтобы она всегда возвращала новый экземпляр
#    InMemoryRepository, предотвращая утечки состояния между тестами.
# 3. Создает новый экземпляр FastAPI приложения для каждого теста.
# 4. После выполнения теста отменяет все изменения и очищает глобальные переменные репозиториев.
@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    # Сохраняем оригинальное значение STORAGE_TYPE, чтобы восстановить его после тестов.
    original_storage_type = settings.STORAGE_TYPE
    monkeypatch.setattr(settings, "STORAGE_TYPE", StorageType.IN_MEMORY) # Принудительно устанавливаем In-Memory хранилище

    # Мокируем функцию get_repository, чтобы она всегда предоставляла новый InMemoryRepository.
    # Это гарантирует, что каждый тест работает с чистым состоянием.
    async def mock_get_repository():
        yield InMemoryRepository()
    monkeypatch.setattr(
        "fastapi_switchable_storage.app.dependencies.get_repository",
        mock_get_repository
    )

    # Создаем новый экземпляр FastAPI приложения для текущего теста.
    test_app = create_fastapi_app()

    # Используем TestClient для отправки HTTP-запросов к тестовому приложению.
    with TestClient(test_app) as c:
        yield c # Предоставляем тестовый клиент тестам

    # Очистка после выполнения всех тестов:
    # 1. Восстанавливаем оригинальное значение STORAGE_TYPE.
    # 2. Сбрасываем глобальные переменные репозиториев в None, чтобы избежать влияния на другие тесты.
    monkeypatch.undo() # Отменяем все изменения monkeypatch
    monkeypatch.setattr("fastapi_switchable_storage.app.dependencies._in_memory_repo", None)
    monkeypatch.setattr("fastapi_switchable_storage.app.dependencies._redis_client", None)


# Тест для эндпоинта создания нового элемента (/items/).
# Проверяет, что POST-запрос с корректными данными возвращает HTTP 201 Created
# и что созданный элемент соответствует отправленным данным, включая сгенерированный ID.
def test_create_item(client):
    # Отправляем POST-запрос для создания элемента.
    response = client.post(
        "/items/",
        json={"name": "Test Item", "description": "This is a test item.", "price": 10.0}
    )
    # Проверяем, что статус код ответа 201 Created.
    assert response.status_code == 201
    data = response.json() # Получаем JSON-ответ
    # Проверяем, что поля созданного элемента соответствуют отправленным.
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item."
    assert data["price"] == 10.0
    assert "id" in data # Проверяем, что ID был сгенерирован и присутствует в ответе
