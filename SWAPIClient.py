import requests
import logging

class SWAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        logging.basicConfig(level=logging.INFO)

    def fetch_json(self, endpoint: str) -> list:
        url = f"{self.base_url}{endpoint}/"
        results = []
        while url:
            logging.info(f"Отримання даних з: {url}")
            response = requests.get(url)
            response.raise_for_status()  # викликає помилку, якщо відповідь не 2xx
            data = response.json()
            results.extend(data['results'])
            url = data.get('next')  # якщо є наступна сторінка, додається до url
        return results
