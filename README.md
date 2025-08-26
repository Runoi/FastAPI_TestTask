
# FastAPI Switchable Storage API

Этот проект представляет собой CRUD API для управления сущностями `Item` с возможностью переключения бэкендов хранения данных. Он разработан с использованием FastAPI и следует принципам чистой архитектуры, модульности и расширяемости.

## Ключевые архитектурные особенности

- **Паттерн "Репозиторий"**: Абстрагированный слой доступа к данным, который отделяет бизнес-логику от деталей конкретного хранилища.
- **Переключаемые бэкенды хранения**: Поддержка трех типов хранилищ:
    - **In-memory**: Данные хранятся в оперативной памяти (словарь Python).
    - **SQLite**: Легковесная файловая база данных.
    - **Redis**: Быстрое хранилище данных ключ-значение.
- **Конфигурация через переменные окружения**: Тип используемого хранилища определяется через переменную окружения `STORAGE_TYPE` без необходимости изменения кода.
- **Dependency Injection**: Использование системы внедрения зависимостей FastAPI для предоставления соответствующего экземпляра репозитория эндпоинтам.

## Технологии

- [**FastAPI**](https://fastapi.tiangolo.com/): Современный, быстрый (высокопроизводительный) веб-фреймворк для создания API на Python 3.7+.
- [**Pydantic**](https://pydantic.dev/): Библиотека для валидации данных и управления настройками с использованием Python type hints.
- [**Pydantic-Settings**](https://pydantic-docs.helpmanual.io/blog/pydantic-settings/): Расширение Pydantic для управления настройками из различных источников (переменные окружения, `.env` файлы).
- [**Uvicorn**](https://www.uvicorn.org/): Молниеносный ASGI-сервер, на котором работает FastAPI.
- [**aiosqlite**](https://pypi.org/project/aiosqlite/): Асинхронный адаптер SQLite для `asyncio`.
- [**redis-py**](https://redis.readthedocs.io/en/stable/)
- [**pytest**](https://docs.pytest.org/): Фреймворк для тестирования Python-кода.
- [**pytest-asyncio**](https://pytest-asyncio.readthedocs.io/en/latest/): Плагин Pytest для поддержки асинхронного кода.
- [**Docker**](https://www.docker.com/): Платформа для контейнеризации приложений.
- [**Docker Compose**](https://docs.docker.com/compose/): Инструмент для определения и запуска многоконтейнерных Docker-приложений.

## Как запустить проект

Для запуска проекта вам потребуется установленный Docker и Docker Compose (для запуска с Docker) или Python и pip (для локального запуска).

1.  **Склонируйте репозиторий** (если еще не сделали это):

    ```bash
    git clone <URL_РЕПОЗИТОРИЯ>

    ```

2.  **Установите зависимости (для локального запуска)**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Создайте файл `.env`**: Создайте файл с именем `.env` в корневой директории проекта (`fastapi_switchable_storage/`) и скопируйте в него следующее содержимое:

    ```ini
    # STORAGE_TYPE может быть: in_memory, sqlite, redis
    STORAGE_TYPE=in_memory
    REDIS_URL=redis://redis_db:6379/0
    # SQLITE_DATABASE_URL опционально, по-умолчанию:///./sqlite.db
    # SQLITE_DATABASE_URL=sqlite:///./data/sqlite.db
    ```

4.  **Настройте `.env` файл**: Откройте созданный `.env` файл и укажите желаемый тип хранилища. Например:

    ```ini
    STORAGE_TYPE=in_memory
    REDIS_URL=redis://redis_db:6379/0
    ```

    -   `STORAGE_TYPE`: `in_memory`, `sqlite` или `redis`. 
        -   Для `in_memory` и `sqlite` Redis не требуется, но сервис `redis_db` все равно запустится. 
        -   Для `sqlite` данные будут храниться в файле `./data/sqlite.db`.

5.  **Запустите приложение с Docker Compose**:

    ```bash
    docker-compose up --build
    ```

    Это команда соберет Docker-образ, запустит контейнеры `app` и `redis_db` (если `STORAGE_TYPE` установлен в `redis`).

6.  **Доступ к API**: После запуска API будет доступно по адресу `http://localhost:8000`.
    Документация Swagger UI будет доступна по `http://localhost:8000/docs`.
    Документация ReDoc будет доступна по `http://localhost:8000/redoc`.

## Запуск тестов

Для запуска тестов используйте `pytest`.

1.  **Запустите все тесты**:

    ```bash
    python -m pytest fastapi_switchable_storage/tests
    ```

2.  **Запустите отдельные тесты** (например, только тесты API):

    ```bash
    python -m pytest fastapi_switchable_storage/tests/test_api.py
    ```

3.  **Захват вывода тестов**: Для захвата полного вывода тестов в файл `test_results.txt` можно использовать вспомогательный скрипт:

    ```bash
    python run_tests_and_capture.py
    ```

    Этот скрипт запускает `pytest` и сохраняет `stdout` и `stderr` в `test_results.txt`.

**Важное замечание для тестов API**: Для тестов API (`fastapi_switchable_storage/tests/test_api.py`) тип хранилища автоматически устанавливается в `in_memory`, а репозиторий изолируется для каждого теста, чтобы предотвратить утечки состояния.

## Конфигурация хранилища

Тип хранилища определяется переменной окружения `STORAGE_TYPE` в файле `.env`. Возможные значения:

-   `in_memory`: Данные хранятся только в оперативной памяти приложения. При перезапуске контейнера все данные будут утеряны. Подходит для тестирования или демонстрации.
-   `sqlite`: Данные сохраняются в файле `sqlite.db` внутри тома `./data`. Данные будут персистентными между перезапусками контейнера.
-   `redis`: Данные хранятся в Redis. Требует запущенного Redis-сервиса (который запускается `docker-compose.yml`). Данные будут персистентными, если Redis настроен на сохранение данных.

Пример конфигурации для Redis:

```ini
STORAGE_TYPE=redis
REDIS_URL=redis://redis_db:6379/0
```

Убедитесь, что `REDIS_URL` указывает на правильный хост и порт, если вы не используете `docker-compose` или если Redis запущен на другом адресе.

Пример выполнения запросов/работы API(run_api_requsets.py):
<img width="972" height="927" alt="image" src="https://github.com/user-attachments/assets/efbb2acf-e5c2-4133-a4e3-662710db0a6b" />

