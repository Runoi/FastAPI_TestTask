# fastapi_switchable_storage/app/config.py
#
# Модуль конфигурации приложения. Определяет настройки, такие как тип
# используемого хранилища данных (In-Memory, SQLite, Redis) и параметры
# подключения для каждого бэкенда. Использует библиотеку pydantic-settings
# для удобного и безопасного чтения настроек из переменных окружения
# или файла .env.

from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# Перечисление (Enum) для определения доступных типов хранилищ данных.
# Обеспечивает строгую типизацию и предотвращает ошибки при указании типа хранилища,
# делая код более надежным и читаемым.
class StorageType(str, Enum):
    IN_MEMORY = "in_memory"  # Хранилище в оперативной памяти (данные не персистентны)
    SQLITE = "sqlite"        # Хранилище в базе данных SQLite (данные персистентны в файле)
    REDIS = "redis"          # Хранилище в Redis (данные персистентны, если настроен Redis)


# Класс настроек приложения, наследуется от BaseSettings Pydantic.
# Автоматически загружает переменные окружения и настройки из .env файла,
# обеспечивая гибкую конфигурацию без изменения кода.
class Settings(BaseSettings):
    # Конфигурация Pydantic-Settings.
    # `env_file=".env"` указывает, что настройки следует искать в файле ".env".
    # `extra="ignore"` позволяет игнорировать неизвестные переменные в .env файле,
    # если они не определены явно в этом классе, предотвращая ошибки валидации.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Тип хранилища по умолчанию установлен в `in_memory`.
    # Может быть переопределен переменной окружения с именем `STORAGE_TYPE`.
    STORAGE_TYPE: StorageType = StorageType.IN_MEMORY

    # URL для подключения к серверу Redis.
    # По умолчанию указывает на локальный Redis или сервис 'redis_db' в Docker Compose.
    # Может быть `None`, если тип хранилища Redis не используется.
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # URL для файла базы данных SQLite.
    # По умолчанию указывает на файл `sqlite.db` в текущем каталоге (или относительно него).
    # Пример: `sqlite:///./data/sqlite.db` для файла в поддиректории `data`.
    SQLITE_DATABASE_URL: str = "sqlite:///./sqlite.db"


# Создание глобального экземпляра настроек, который будет использоваться во всем приложении.
# Это обеспечивает легкий доступ к конфигурации из любого места в коде.
settings = Settings()
