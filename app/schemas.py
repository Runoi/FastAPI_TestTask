
# fastapi_switchable_storage/app/schemas.py
#
# Определяет Pydantic-модели для валидации данных, сериализации и десериализации
# сущностей Item, используемых в API. Эти модели обеспечивают четкую структуру
# данных и автоматически генерируют документацию для Swagger UI, что улучшает
# взаимодействие с API и его понимание разработчиками.

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Модель для создания или обновления элемента (Item).
# Не включает поле 'id', так как оно генерируется хранилищем данных.
# Используется для входящих данных при POST и PUT запросах.
class ItemCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "name": "Laptop",
                "description": "Мощное вычислительное устройство",
                "price": 1200.50
            }
        ]
    })

    name: str = Field(
        min_length=3,
        max_length=50,
        description="Наименование предмета (минимум 3, максимум 50 символов)"
    )
    description: Optional[str] = Field(
        None,
        max_length=200,
        description="Описание предмета (опционально, максимум 200 символов)"
    )
    price: float = Field(
        gt=0,
        description="Цена предмета (должна быть больше нуля)"
    )


# Модель для чтения элемента (Item).
# Наследуется от ItemCreate и добавляет поле 'id',
# которое присваивается после сохранения в хранилище. Используется для исходящих данных.
# `from_attributes=True` позволяет создавать модель из произвольных объектов, например, из SQLAlchemy ORM-моделей.
class Item(ItemCreate):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "examples": [
            {
                "id": 1,
                "name": "Laptop",
                "description": "Мощное вычислительное устройство",
                "price": 1200.50
            }
        ]
    })

    id: int = Field(
        description="Уникальный идентификатор предмета, присвоенный хранилищем данных"
    )
