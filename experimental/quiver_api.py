import requests
import time

class QuiverQuantitativeAPI:
    BASE_URL = "https://api.quiverquant.com"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'Authorization': f'Token {self.api_key}'}

    def _make_request(self, endpoint):
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def congress_trading(self):
        endpoint = "beta/live/congresstrading"
        return self._make_request(endpoint)

    def senate_trading(self):
        while True:
            try:
                endpoint = "beta/live/senatetrading"
                return self._make_request(endpoint)
                break
            except requests.exceptions.HTTPError as error:
                print(error)
                print("Trying again in 5 seconds")
                time.sleep(5)
                print("Trying again...")
