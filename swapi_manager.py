import argparse
import json
import pandas as pd
import requests
import logging

# Налаштування логера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Клас для завантаження даних з SWAPI API
class SWAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_json(self, endpoint: str) -> list:
        all_data = []
        url = f"{self.base_url}{endpoint}/"

        while url:
            logger.info(f"Запит до URL: {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            all_data.extend(data['results'])
            url = data.get('next')

        return all_data

# Базовий клас для обробки даних
class EntityProcessor:
    def process(self, json_data: list) -> pd.DataFrame:
        """Метод для обробки даних, реалізується в дочірніх класах."""
        pass

# Процесор для людей
class PeopleProcessor(EntityProcessor):
    def process(self, json_data: list) -> pd.DataFrame:
        df = pd.DataFrame(json_data)
        df['full_name'] = df['name']  # Наприклад, додавання нового поля
        return df

# Процесор для планет
class PlanetsProcessor(EntityProcessor):
    def process(self, json_data: list) -> pd.DataFrame:
        df = pd.DataFrame(json_data)
        df['population'] = pd.to_numeric(df['population'], errors='coerce')
        return df

# Процесор для фільмів
class FilmsProcessor(EntityProcessor):
    def process(self, json_data: list) -> pd.DataFrame:
        df = pd.DataFrame(json_data)
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        return df

# Клас для управління даними SWAPI
class SWAPIDataManager:
    def __init__(self, client):
        self.client = client
        self.processors = {}
        self.data = {}

    def register_processor(self, endpoint: str, processor: EntityProcessor):
        self.processors[endpoint] = processor

    def fetch_entity(self, endpoint: str):
        json_data = self.client.fetch_json(endpoint)
        if endpoint in self.processors:
            processor = self.processors[endpoint]
            processed_data = processor.process(json_data)
            self.data[endpoint] = processed_data
        else:
            raise ValueError(f"Процесор для {endpoint} не знайдено.")

    def apply_filter(self, endpoint: str, columns_to_drop: list):
        if endpoint in self.data:
            self.data[endpoint].drop(columns=columns_to_drop, inplace=True)

    def save_to_excel(self, filename: str):
        with pd.ExcelWriter(filename) as writer:
            for endpoint, df in self.data.items():
                df.to_excel(writer, sheet_name=endpoint, index=False)

# Головна функція
def main():
    # Парсинг аргументів командного рядка
    parser = argparse.ArgumentParser(description="Завантаження та обробка даних з SWAPI.")
    parser.add_argument("--endpoint", required=True, help="Список сутностей через кому (наприклад, people,planets)")
    parser.add_argument("--output", required=True, help="Ім'я вихідного Excel-файлу")
    parser.add_argument("--filters", required=True, help="Шлях до JSON-файлу з фільтрами (наприклад, filters.json)")

    args = parser.parse_args()

    # Зчитуємо фільтри з JSON-файлу
    with open(args.filters, "r") as f:
        filters = json.load(f)

    # Ініціалізація клієнта та менеджера даних
    client = SWAPIClient(base_url="https://swapi.dev/api/")
    manager = SWAPIDataManager(client)

    # Реєстрація процесорів
    manager.register_processor("people", PeopleProcessor())
    manager.register_processor("planets", PlanetsProcessor())
    manager.register_processor("films", FilmsProcessor())

    # Завантаження та обробка даних для зазначених сутностей
    for endpoint in args.endpoint.split(","):
        manager.fetch_entity(endpoint)

    # Застосування фільтрів
    for endpoint, columns in filters.items():
        manager.apply_filter(endpoint, columns)

    # Збереження результату в файл
    manager.save_to_excel(args.output)

if __name__ == "__main__":
    main()

