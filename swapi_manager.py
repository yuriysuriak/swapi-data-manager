import argparse
import json
import requests
import pandas as pd

class SWAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_json(self, endpoint: str) -> list:
        results = []
        url = f"{self.base_url}/{endpoint}/"
        while url:
            print(f"Fetching data from {url}")  # Логування URL
            response = requests.get(url)
            data = response.json()
            results.extend(data['results'])
            url = data.get('next')  # Пагінація
        return results

class SWAPIDataManager:
    def __init__(self, client: SWAPIClient):
        self.client = client
        self.data = {}

    def fetch_entity(self, endpoint: str):
        json_data = self.client.fetch_json(endpoint)
        self.data[endpoint] = pd.DataFrame(json_data)

    def apply_filter(self, endpoint: str, columns_to_drop: list):
        df = self.data.get(endpoint)
        if df is not None:
            self.data[endpoint] = df.drop(columns=columns_to_drop)

    def save_to_excel(self, filename: str):
        with pd.ExcelWriter(filename) as writer:
            for endpoint, df in self.data.items():
                df.to_excel(writer, sheet_name=endpoint)

def main():
    # Аргументи командного рядка
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', required=True, help="List of endpoints to fetch data from")
    parser.add_argument('--output', required=True, help="Output Excel file name")
    parser.add_argument('--filters', required=True, help="Path to the JSON file containing filters")
    args = parser.parse_args()

    # Завантаження фільтрів з файлу
    with open(args.filters, 'r') as file:
        filters = json.load(file)

    # Ініціалізація клієнта і менеджера даних
    client = SWAPIClient(base_url="https://swapi.dev/api/")
    manager = SWAPIDataManager(client)

    # Завантаження даних для всіх endpoint-ів
    for endpoint in args.endpoint.split(','):
        manager.fetch_entity(endpoint)

    # Застосування фільтрів
    for endpoint, columns_to_drop in filters.items():
        manager.apply_filter(endpoint, columns_to_drop)

    # Збереження даних у файл
    manager.save_to_excel(args.output)

if __name__ == "__main__":
    main()
