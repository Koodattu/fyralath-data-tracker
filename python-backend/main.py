from flask import Flask, request
from flask_caching import Cache
from flask_cors import CORS
import json
from auction_data_fetcher import AuctionDataFetcher
from mongodb_manager import MongoDBManager
import schedule
import threading
import time
import socket
from waitress import serve

app = Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
auction_fetcher = AuctionDataFetcher()
db_manager = MongoDBManager()

def fetch_auction_data():
    print("Fetching auction data...")
    result = auction_fetcher.run()
    cache.clear()
    print("Auction data fetched successfully")

# Schedule the task to run every hour
schedule.every().hour.do(fetch_auction_data)

# Create a separate thread to execute the scheduled tasks
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    print("Fetching current data...")
    cache_key = 'current_data'
    data = cache.get(cache_key)
    if data is None:
        print("Cache missing. Getting data from db.")
        data = db_manager.get_latest_item_prices()
        data = json.dumps(data, default=str)
        cache.set(cache_key, data, timeout=None)
    else:
        print("Returning cached current data")
    return data


@app.route('/api/data/history', methods=['GET'])
def get_history_data():
    print("Fetching history data...")
    cache_key = 'history_data'
    data = cache.get(cache_key)
    if data is None:
        print("Cache missing. Getting data from db.")
        data = db_manager.get_all_daily_averages()
        data = json.dumps(data, default=str)
        cache.set(cache_key, data, timeout=None)
    else:
        print("Returning cached current data.")
    return data

def get_local_ip():
    """Function to get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '0.0.0.0'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    print("Starting Flask app")
    # Start the scheduler thread
    print("Fetching auction data...")
    #result = auction_fetcher.run()
    print("Auction data fetched successfully")
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    # Start the Flask app using the local IP address
    local_ip = get_local_ip()
    port = 5000
    print("Flask app starting")
    print(f"http://{local_ip}:{port}/api/data/current")
    print(f"http://{local_ip}:{port}/api/data/history")
    #app.run(host=local_ip)
    serve(app, host=local_ip, port=port)
