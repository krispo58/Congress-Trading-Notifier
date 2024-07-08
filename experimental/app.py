from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from py_vapid import Vapid
from quiver_api import QuiverQuantitativeAPI
from pywebpush import webpush, WebPushException

app = Flask(__name__)
CORS(app)

# Configuration
vapid_keys = {
    "subject": "mailto:kristofferkolderup@gmail.com",
    "publicKey": "BBy0JDW0WUs9SLC33fI2X7bny1AiP6swaBv6R-US2kYHyrrOs3PXSDfr9rqkPk39UVWJKJSjPXJcV6Ejw80KxAU",
    "privateKey": "3zbDWbAVup0SCT6R1MmNx9yQ4OnA0_7mq6yE4ZYXEUU"
}
API_KEY = 'abb7d18db8cb4533da6920daa12385bba6a6c5ad'  # Replace with your actual Quiver API key
quiver_api = QuiverQuantitativeAPI(API_KEY)
recent_trades = []
subscription_file = 'subscriptions.json'
email_file = 'emails.txt'

# Serve static files (index.html, styles.css, main.js, service-worker.js, logo)
@app.route('/')
def serve_index():
    return send_from_directory('', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.endswith('.css') or path.endswith('.js') or path.endswith('.png'):
        return send_from_directory('', path)
    else:
        return send_from_directory('', 'index.html')

# API endpoints
@app.route('/api/recenttrades', methods=['GET'])
def get_recent_trades():
    return jsonify(recent_trades[-10:])

@app.route('/api/updaterecenttrades', methods=['POST'])
def update_recent_trades():
    global recent_trades
    new_trades = quiver_api.senate_trading()
    if new_trades != recent_trades:
        new_only = [trade for trade in new_trades if trade not in recent_trades]
        recent_trades = new_trades
        notify_subscribers(new_only)
    return '', 204

@app.route('/api/pushsubscriptions', methods=['POST'])
def save_subscription():
    subscription = request.json
    if not os.path.exists(subscription_file):
        with open(subscription_file, 'w') as file:
            json.dump([], file)
    with open(subscription_file, 'r+') as file:
        subscriptions = json.load(file)
        subscriptions.append(subscription)
        file.seek(0)
        json.dump(subscriptions, file, indent=4)
    return '', 201

@app.route('/api/postemail', methods=['POST'])
def save_email():
    email = request.json.get('email')
    if email:
        with open(email_file, 'a') as file:
            file.write(email + '\n')
    return '', 201

def notify_subscribers(new_trades):
    if os.path.exists(subscription_file):
        with open(subscription_file, 'r') as file:
            subscriptions = json.load(file)
        for subscription in subscriptions:
            try:
                webpush(subscription, json.dumps(new_trades), vapid_private_key=vapid_keys['privateKey'], vapid_claims={"sub": vapid_keys["subject"]})
            except WebPushException as ex:
                print("Web push failed:", repr(ex))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
