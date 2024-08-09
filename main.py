from flask import Flask, request, Response, jsonify, send_file
import requests
import json
from pywebpush import webpush
import time

recent_trades = []

files = {}
emails = []

class QuiverQuantitativeAPI:
    BASE_URL = "https://api.quiverquant.com"  # Base URL for the API

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Token {self.api_key}'
        }

    def _make_request(self, endpoint):
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()

    def congress_trading(self):
        """Fetches data about trading by members of Congress."""
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
    
    def specific_trading(self, congressperson: str):
        endpoint = f"beta/bulk/congresstrading?representative={congressperson}"
        return self._make_request(endpoint)
            
class BeehiivAPI:
    BASE_URL = "https://api.beehiiv.com/v2"

    def __init__(self, api_key, publication_id):
        self.api_key = api_key
        self.publication_id = publication_id
        self.headers = {
            'Authorization': f'{self.api_key}'
        }

    def _make_request(self, endpoint, data):
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers, data=data)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    
    def _make_post_request(self, endpoint, data):
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    
    def subscribe_email(self, email):
        endpoint = f"/publications/{self.publication_id}/subscriptions"
        return self._make_post_request(endpoint, {"email": email, "reactivate_existing": True, "send_welcome_email" : True})




with open("vapid/vapid.json") as fd:
    data = json.load(fd)
    vapid_private_key = data["privateKey"]
    vapid_public_key = data["publicKey"]
    vapid_claims = data["subject"]

with open("backend/subscriptions.json") as fd:
    subscriptions = json.load(fd)
 
app = Flask(__name__)
quiver = QuiverQuantitativeAPI("abb7d18db8cb4533da6920daa12385bba6a6c5ad")
bh = BeehiivAPI("6Sr4h6r6Aj0WoXXJXVWSqN1xhHWNSJ99B0VdnmeIzKUZ2csCeAgqVVCRIcMwGBZG", "pub_c7d875ca-9f4f-4ea0-a1b2-2dfd3faf5815")
#congress = CongressAPI("unr6zNM1GeAQ67kiHFlzYW72mQfHfZ8M5odCcCLa")

# Public files
@app.route("/")
def index():
    return Response(files["index.html"], content_type="text/html")

@app.route("/main.js")
def mainjs():
    return Response(files["main.js"], content_type="application/javascript")

@app.route("/DollarFinanceLogo.png")
def logo():
    return send_file("frontend/DollarFinanceLogo.png")

@app.route("/NancyPelosi.png")
def nancy_pelosi_img():
    return send_file("frontend/NancyPelosi.png")

@app.route("/service_worker.js")
def service_worker():
    return Response(files["service_worker.js"], content_type="application/javascript")

# End public files

# Backend

@app.route("/backend/subscribeemail", methods=["POST"])
def subscribe_email():
    global emails
    try:
        email = request.get_json()["email"]
        # Send api request to beehiiv
        response = bh.subscribe_email(email)
        print(response)
        return json.dumps({"success": True})
    except Exception as error:
        print(error)
        return json.dumps({"success": False})

@app.route("/backend/recenttrades")
def get_recent_trades():
    global recent_trades
    return recent_trades

@app.route("/backend/congressmembers")
def get_congressmen():
    with open("congress_members.json", "r") as fd:
        return json.load(fd)

@app.route("/backend/updaterecenttrades")
def update_recent_trades():
    global recent_trades, subscriptions, vapid_claims, vapid_private_key
    if len(recent_trades) < 1:
        with open("backend/recent_trades.json", "r") as fd:
            prev_trades = json.load(fd)
    else:
        prev_trades = recent_trades

    recent_trades = quiver.specific_trading("Nancy Pelosi")[:10]
    if recent_trades != prev_trades:
        # Send notifications to all subscribers
        new_trades = symmetric_difference(recent_trades, prev_trades)

        for trade in new_trades:
            trade_data = json.dumps(trade)  # Serialize the trade object to JSON string
            for subscription in subscriptions:
                print(f"sending trade: {trade['Representative']} to subscription: {subscription}")
                try:
                    webpush(
                        subscription,
                        trade_data,
                        vapid_private_key,
                        {"sub": vapid_claims}
                    )
                except Exception as e:
                    print(f"Error while sending webpush: {e}")

    with open("backend/recent_trades.json", "w") as fd:
        json.dump(recent_trades, fd)

    return "success"


@app.route("/backend/pushsubscriptions", methods=["POST"])
def push_subscriptions():
    return "{'success' : 'true'}"

# End backend

# Utils

def is_valid_subscription(subscription):
    required_keys = {'endpoint', 'keys'}
    keys_sub_keys = {'p256dh', 'auth'}

    if not isinstance(subscription, dict):
        return False

    if not required_keys.issubset(subscription.keys()):
        return False

    if not isinstance(subscription['keys'], dict):
        return False

    if not keys_sub_keys.issubset(subscription['keys'].keys()):
        return False

    return True

def cache_files():
    with open("frontend/index.html", "r") as fd:
        files["index.html"] = fd.read()
    with open("frontend/main.js", "r") as fd:
        files["main.js"] = fd.read()
    with open("frontend/service_worker.js", "r") as fd:
        files["service_worker.js"] = fd.read()

def symmetric_difference(a: list, b: list):
    difference = []
    for item in a:
        if item not in b:
            difference.append(item)
    return difference

update_recent_trades()
cache_files()

if __name__ == "__main__":
    app.run()