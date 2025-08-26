# fastapi_switchable_storage/app/repositories/redis_repo.py
#
# Реализация репозитория для работы с элементами (Item) в базе данных Redis.
# Этот репозиторий использует асинхронный клиент Redis для выполнения
# CRUD-операций и поддерживает персистентное хранение данных.

from typing import List, Optional
import json
from redis.asyncio import Redis
from app.schemas import Item, ItemCreate
from .base import BaseRepository


# Класс RedisRepository, реализующий интерфейс BaseRepository для работы с Redis.
# Отвечает за взаимодействие с Redis для хранения, извлечения, обновления
# и удаления сущностей Item.
class RedisRepository(BaseRepository):
    # Инициализация репозитория. Принимает асинхронный клиент Redis.
    # Устанавливает префикс для ключей Redis и ключ для счетчика ID.
    def __init__(self, redis_client: Redis):
        self.redis = redis_client          # Экземпляр асинхронного клиента Redis для выполнения операций
        self.key_prefix = "item:"         # Префикс, используемый для всех ключей элементов в Redis (например, "item:1", "item:2")
        self.next_id_key = "next_item_id" # Ключ в Redis, хранящий следующий доступный ID для новых элементов

    # Приватный асинхронный метод для получения следующего уникального ID элемента.
    # Использует команду Redis `INCR` для атомарного увеличения счетчика `self.next_id_key`.
    # Это гарантирует, что каждый новый элемент получит уникальный ID даже при параллельных запросах.
    async def _get_next_id(self) -> int:
        return await self.redis.incr(self.next_id_key)

    # Асинхронный метод для получения одного элемента по его ID.
    # Извлекает данные элемента из Redis по сформированному ключу. Если данные найдены,
    # они десериализуются из JSON в объект `Item` с помощью Pydantic и возвращаются.
    # Возвращает `None`, если элемент не найден.
    async def get_item(self, item_id: int) -> Optional[Item]:
        item_data = await self.redis.get(f"{self.key_prefix}{item_id}") # Получаем сырые данные по ключу из Redis
        if item_data:
            return Item.model_validate_json(item_data) # Десериализуем JSON-строку в объект Item
        return None # Элемент не найден

    # Асинхронный метод для получения списка элементов.
    # Сканирует Redis для получения всех ключей, начинающихся с `self.key_prefix`.
    # Затем извлекает данные для всех найденных ключей и десериализует их.
    # Поддерживает опциональную фильтрацию по имени и минимальной цене.
    # Возвращает список отфильтрованных объектов `Item`.
    async def list_items(self, name_filter: Optional[str] = None, min_price: Optional[float] = None) -> List[Item]:
        all_keys = []
        # Итерируемся по ключам в Redis, используя `scan_iter` для эффективного сканирования.
        async for key in self.redis.scan_iter(f"{self.key_prefix}*"):
            all_keys.append(key) # Добавляем каждый найденный ключ в список

        if not all_keys:
            return [] # Если ключей нет, возвращаем пустой список

        items_data = await self.redis.mget(all_keys) # Получаем данные для всех найденных ключей за один запрос
        items = []
        for item_data in items_data:
            if item_data:
                item = Item.model_validate_json(item_data) # Десериализуем данные в объект Item
                match_name = True  # Флаг соответствия фильтру по имени
                match_price = True # Флаг соответствия фильтру по цене

                # Применяем фильтр по имени, если он задан. Сравнение без учета регистра.
                if name_filter and name_filter.lower() not in item.name.lower():
                    match_name = False
                # Применяем фильтр по минимальной цене, если он задан.
                if min_price and item.price < min_price:
                    match_price = False

                if match_name and match_price:
                    items.append(item) # Добавляем элемент, если он соответствует всем фильтрам
        return items

    # Асинхронный метод для создания нового элемента.
    # Получает новый уникальный ID, создает объект `Item` на основе входящих данных,
    # сериализует его в JSON и сохраняет в Redis под ключом `self.key_prefix{item_id}`.
    # Возвращает созданный объект `Item`.
    async def create_item(self, item_create: ItemCreate) -> Item:
        item_id = await self._get_next_id() # Получаем следующий доступный ID
        item = Item(id=item_id, **item_create.model_dump()) # Создаем новый объект Item
        # Сохраняем Item в Redis, сериализуя его в JSON строку.
        await self.redis.set(f"{self.key_prefix}{item_id}", item.model_dump_json())
        return item # Возвращаем созданный элемент

    # Асинхронный метод для обновления существующего элемента по ID.
    # Сначала пытается получить существующий элемент. Если он найден,
    # обновляет его поля на основе данных из `item_update` (частичное обновление).
    # Затем сериализует и сохраняет обновленный объект обратно в Redis.
    # Возвращает обновленный объект `Item` или `None`, если элемент не найден.
    async def update_item(self, item_id: int, item_update: ItemCreate) -> Optional[Item]:
        existing_item = await self.get_item(item_id) # Получаем существующий элемент для обновления
        if existing_item:
            updated_data = item_update.model_dump(exclude_unset=True) # Получаем только те поля, которые были явно установлены в item_update
            updated_item = existing_item.model_copy(update=updated_data) # Создаем новую копию элемента с обновленными данными
            # Сохраняем обновленный Item в Redis, заменяя старую версию.
            await self.redis.set(f"{self.key_prefix}{item_id}", updated_item.model_dump_json())
            return updated_item # Возвращаем обновленный элемент
        return None # Элемент для обновления не найден

    # Асинхронный метод для удаления элемента по ID.
    # Удаляет ключ элемента из Redis, соответствующий заданному `item_id`.
    # Возвращает `True`, если ключ был успешно удален (т.е., элемент существовал),
    # и `False`, если ключ не был найден (элемент не существовал).
    async def delete_item(self, item_id: int) -> bool:
        # `delete` возвращает количество удаленных ключей. Если > 0, значит, элемент был удален.
        result = await self.redis.delete(f"{self.key_prefix}{item_id}") # Удаляем ключ элемента из Redis
        return result > 0 # Возвращаем True, если был удален хотя бы один ключ
