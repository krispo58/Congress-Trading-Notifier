import requests
import time

while True:
    requests.get("https://localhost/backend/updaterecenttrades")
    time.sleep()