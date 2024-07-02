from flask import Flask, request, Response, jsonify
import requests
import json
from pywebpush import webpush
import time

recent_trades = []
trades_updated = False

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
            

class CongressAPI:
    BASE_URL = "https://api.congress.gov/v3"

    def __init__(self, api_key) -> None:
        self.api_key = api_key
        self.members = []
        
        self.update_congress_members()

    def _make_request(self, endpoint, params: dict = {}):
        url = f"{self.BASE_URL}/{endpoint}?api_key={self.api_key}"
        for i in params.keys():
            url += f"&{i}={params[i]}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def congress_members(self, limit=250):
        """Gets a list of members in congress"""
        endpoint = "member"
        return self._make_request(endpoint, {"limit": limit})
    
    def member_image(self, name: str):
        try:
            member_id = self.bioguide_id(name)
            endpoint = f"member/{member_id}"
            response = self._make_request(endpoint)
            image = response["member"]["depiction"]["imageUrl"]
            return image
        except Exception as error:
            print(error)
            print(response, type(response))
            return None

    def bioguide_id(self, name: str):
        for member in self.members:
            if member["name"] == name:
                return member["bioguideId"]
        raise ValueError("Cannot find name in list of congressmen")

    def update_congress_members(self):
        self.members = []
        response = self.congress_members()
        m = response["members"]
        for member in m:
            self.members.append(member)
        for _ in range(2):
            next = response["pagination"]["next"]
            response = self.direct_request(next)
            m = response["members"]
            for member in m:
                self.members.append(member)
        #json.dump(members, open("backend/congress_members.json", "w"))

    def direct_request(self, url):
        return requests.get(url + f"&api_key={self.api_key}").json()

with open("vapid/vapid.json") as fd:
    data = json.load(fd)
    vapid_private_key = data["privateKey"]
    vapid_public_key = data["publicKey"]
    vapid_claims = data["subject"]

with open("backend/subscriptions.json") as fd:
    subscriptions = json.load(fd)
 
app = Flask(__name__)
quiver = QuiverQuantitativeAPI("abb7d18db8cb4533da6920daa12385bba6a6c5ad")
congress = CongressAPI("unr6zNM1GeAQ67kiHFlzYW72mQfHfZ8M5odCcCLa")

# Public files
@app.route("/")
def index():
    return open("frontend/index.html", "r").read()
    #return Response(files["index.html"], content_type="text/html")

@app.route("/main.js")
def mainjs():
    return open("frontend/main.js", "r").read()
    #return Response(files["main.js"], content_type="application/javascript")

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
        print(email)
        with open("emails.txt", "a") as fd:
            fd.write(email + "\n")
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
    global recent_trades, trades_updated, subscriptions, vapid_claims, vapid_private_key
    if len(recent_trades) < 1:
        with open("backend/recent_trades.json", "r") as fd:
            prev_trades = json.load(fd)
    else:
        prev_trades = recent_trades

    recent_trades = quiver.senate_trading()[:10]
    if recent_trades != prev_trades:
        # Send notifications to all subscribers
        new_trades = symmetric_difference(recent_trades, prev_trades)
        print(len(new_trades))
        print(len(subscriptions))

        for trade in new_trades:
            trade_data = json.dumps(trade)  # Serialize the trade object to JSON string
            for subscription in subscriptions:
                print(f"sending trade: {trade['Senator']} to subscription: {subscription}")
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
    subscription = json.loads(request.get_json()["subscription_json"])
    #if not is_valid_subscription(subscription):
    #    return "Stop hacking my server bro"

    if subscription in subscriptions:
        return "{'success' : 'true'}"

    subscriptions.append(subscription)
    
    with open("backend/subscriptions.json", "w") as fd:
        json.dump(subscriptions, fd)

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
app.run()