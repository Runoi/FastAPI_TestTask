import requests

BASE_URL = "http://localhost:8000"

def create_item(name: str, description: str, price: float):
    print(f"\n--- Создание элемента: {name} ---")
    data = {"name": name, "description": description, "price": price}
    response = requests.post(f"{BASE_URL}/items/", json=data)
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.json()}")
    return response.json()

def get_items(name_filter: str = None, min_price: float = None):
    print("\n--- Получение списка элементов ---")
    params = {}
    if name_filter:
        params["name_filter"] = name_filter
    if min_price:
        params["min_price"] = min_price

    
    response = requests.get(f"{BASE_URL}/items/", params=params)
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.json()}")
    return response.json()

def get_item_by_id(item_id: int):
    print(f"\n--- Получение элемента по ID: {item_id} ---")
    
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.json()}")
    return response.json()

def update_item(item_id: int, name: str, description: str, price: float):
    print(f"\n--- Обновление элемента ID: {item_id} ---")
    data = {"name": name, "description": description, "price": price}
    
    response = requests.put(f"{BASE_URL}/items/{item_id}", json=data)
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.json()}")
    return response.json()

def delete_item(item_id: int):
    print(f"\n--- Удаление элемента ID: {item_id} ---")
    
    response = requests.delete(f"{BASE_URL}/items/{item_id}")
    print(f"Статус: {response.status_code}")
    # Для 204 No Content тело ответа будет пустым
    print(f"Ответ: {response.text if response.text else 'Нет содержимого'}")
    return response.status_code == 204

def main():
    print("Запуск тестовых запросов к API...")

    # Создание элементов
    item1 = create_item("Ноутбук", "Мощный ноутбук для работы", 1200.0)
    item2 = create_item("Мышь", "Беспроводная мышь", 25.0)
    item3 = create_item("Клавиатура", "Механическая клавиатура", 100.0)

    # Получение всех элементов
    get_items()

    # Получение элемента по ID
    if item1:
        get_item_by_id(item1["id"])

    # Фильтрация по имени
    get_items(name_filter="ноут")

    # Фильтрация по минимальной цене
    get_items(min_price=50.0)

    # Обновление элемента
    if item2:
        update_item(item2["id"], "Игровая Мышь", "Эргономичная игровая мышь", 50.0)

    # Попытка получить обновленный элемент
    if item2:
        get_item_by_id(item2["id"])

    # Удаление элемента
    if item3:
        delete_item(item3["id"])
        print(f"Попытка получить удаленный элемент (ожидается 404):")
        get_item_by_id(item3["id"]) # Должно вернуть 404

    # Попытка удалить несуществующий элемент (ожидается 404)
    print(f"Попытка удалить несуществующий элемент (ожидается 404):")
    delete_item(9999)


if __name__ == "__main__":
    main()
