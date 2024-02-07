from flask import Flask, request
from flask_caching import Cache
from flask_cors import CORS
import json
from auction_data_fetcher import AuctionDataFetcher
import schedule
import threading
import time
import socket

app = Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
auction_fetcher = AuctionDataFetcher()

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

@app.route('/api/data', methods=['GET'])
@cache.cached(timeout=None)  # Cache the response indefinitely
def get_data():
    print("Get data called")
    with open('latest_total_costs.json') as file:
        data = json.load(file)
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
    result = auction_fetcher.run()
    print("Auction data fetched successfully")
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    # Start the Flask app using the local IP address
    local_ip = get_local_ip()
    print(f"Flask app starting on http://{local_ip}:5000")
    app.run(host=local_ip)

    print("Flask app started")
