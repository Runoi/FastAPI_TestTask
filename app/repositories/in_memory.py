# fastapi_switchable_storage/app/repositories/in_memory.py
#
# Реализация репозитория для хранения данных в оперативной памяти (in-memory).
# Этот репозиторий подходит для разработки, тестирования и демонстраций,
# где не требуется сохранение данных между запусками приложения,
# так как все данные хранятся в словаре Python и не являются персистентными.

from typing import Dict, List, Optional
from app.schemas import Item, ItemCreate
from .base import BaseRepository


# Репозиторий для хранения элементов (Item) в оперативной памяти.
# Наследуется от BaseRepository и реализует все его абстрактные методы
# для выполнения CRUD-операций.
class InMemoryRepository(BaseRepository):
    # Инициализация репозитория.
    # Создает пустой словарь `self.items` для хранения объектов Item по их ID
    # и устанавливает начальное значение `self.next_id` для генерации уникальных ID.
    def __init__(self):
        self.items: Dict[int, Item] = {}  # Словарь: ключ - ID элемента, значение - объект Item
        self.next_id = 1                  # Счетчик для генерации следующего уникального ID

    # Асинхронный метод для получения одного элемента по его уникальному ID.
    # Возвращает объект `Item` или `None`, если элемент с указанным ID не найден.
    async def get_item(self, item_id: int) -> Optional[Item]:
        return self.items.get(item_id)

    # Асинхронный метод для получения списка всех элементов.
    # Поддерживает опциональную фильтрацию элементов:
    #   - `name_filter`: фильтрация по имени (частичное совпадение, без учета регистра).
    #   - `min_price`: фильтрация по минимальной цене (элементы с ценой ниже будут исключены).
    # Возвращает список отфильтрованных объектов `Item`.
    async def list_items(self, name_filter: Optional[str] = None, min_price: Optional[float] = None) -> List[Item]:
        filtered_items = []
        for item in self.items.values():
            match_name = True  # Флаг соответствия фильтру по имени
            match_price = True # Флаг соответствия фильтру по цене

            # Применяем фильтр по имени, если он задан.
            if name_filter and name_filter.lower() not in item.name.lower():
                match_name = False
            # Применяем фильтр по минимальной цене, если он задан.
            if min_price and item.price < min_price:
                match_price = False

            # Если элемент соответствует всем активным фильтрам, добавляем его в результат.
            if match_name and match_price:
                filtered_items.append(item)
        return filtered_items

    # Асинхронный метод для создания нового элемента.
    # Генерирует новый уникальный ID, создает объект `Item` на основе
    # входящей Pydantic-модели `ItemCreate` и сохраняет его в словаре `self.items`.
    # После создания ID увеличивается для следующего элемента.
    # Возвращает созданный объект `Item`.
    async def create_item(self, item_create: ItemCreate) -> Item:
        item = Item(id=self.next_id, **item_create.model_dump()) # Создаем Item с новым ID и данными
        self.items[self.next_id] = item                          # Сохраняем Item в словаре по ID
        self.next_id += 1                                        # Увеличиваем счетчик ID для следующего элемента
        return item

    # Асинхронный метод для обновления существующего элемента по его ID.
    # Если элемент с `item_id` найден, обновляет его поля на основе данных
    # из `item_update`. Использует `model_copy(update=...)` для частичного обновления.
    # Возвращает обновленный объект `Item` или `None`, если элемент не найден.
    async def update_item(self, item_id: int, item_update: ItemCreate) -> Optional[Item]:
        if item_id in self.items:
            current_item = self.items[item_id]                          # Получаем текущий элемент
            updated_data = item_update.model_dump(exclude_unset=True) # Получаем только измененные поля (не None)
            updated_item = current_item.model_copy(update=updated_data) # Создаем копию с обновленными данными
            self.items[item_id] = updated_item                          # Сохраняем обновленный элемент в словаре
            return updated_item
        return None # Элемент не найден

    # Асинхронный метод для удаления элемента по его ID.
    # Если элемент с `item_id` найден, удаляет его из словаря `self.items`.
    # Возвращает `True`, если элемент был успешно удален, и `False`, если
    # элемент с таким ID не был найден.
    async def delete_item(self, item_id: int) -> bool:
        if item_id in self.items:
            del self.items[item_id] # Удаляем элемент из словаря
            return True
        return False # Элемент не найден
