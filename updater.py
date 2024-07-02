import requests
import time

while True:
    try:
        requests.get("https://localhost/backend/updaterecenttrades")
        time.sleep(21600000)
    except Exception as error:
        print(error)
        time.sleep(5000)