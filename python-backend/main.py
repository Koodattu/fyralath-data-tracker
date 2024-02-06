import requests
import base64
import json
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_access_token(client_id, client_secret):
    """Fetches an access token using client credentials."""
    credentials = f'{client_id}:{client_secret}'
    base64_encoded_credentials = base64.b64encode(credentials.encode()).decode()
    token_url = 'https://us.battle.net/oauth/token'
    data = {'grant_type': 'client_credentials'}
    headers = {'Authorization': f'Basic {base64_encoded_credentials}'}
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f'Error acquiring access token: Status Code {response.status_code}')

def fetch_data(region, access_token):
    """Fetches data from a specific region."""
    url = f'https://{region}.api.blizzard.com/data/wow/auctions/commodities'
    params = {
        'namespace': f'dynamic-{region}',
        'locale': 'en_US',
        'access_token': access_token
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Error fetching data: Status Code {response.status_code}')

def save_data_as_json(filename, data):
    """Saves the fetched data as a JSON file."""
    with open(filename, 'w') as file:
        json.dump(data, file)

def read_data_from_json(filename):
    """Reads data from a saved JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return None

def update_total_cost_file(region, total_cost):
    """Updates the total cost file for the region with a new data entry."""
    filename = f'total_cost_{region}.json'
    now = datetime.datetime.now().isoformat()
    entry = {'timestamp': now, 'total_cost': total_cost}
    
    if os.path.exists(filename):
        with open(filename, 'r+') as file:
            data = json.load(file)
            data.append(entry)
            file.seek(0)
            json.dump(data, file)
    else:
        with open(filename, 'w') as file:
            json.dump([entry], file)

def calculate_total_cost(auction_data, parts_data):
    """Calculates the total cost based on the lowest prices and amounts needed."""
    item_id_to_name = {item['item_id']: item['item_name'] for part_data in parts_data.values() for item in part_data}
    lowest_prices = {}
    for auction in auction_data['auctions']:
        item_id = auction['item']['id']
        unit_price = auction['unit_price']
        if item_id in item_id_to_name and (item_id not in lowest_prices or unit_price < lowest_prices[item_id]):
            lowest_prices[item_id] = unit_price
    total_costs = {part: sum(lowest_prices.get(item['item_id'], 0) * item['amount_needed'] for item in items) for part, items in parts_data.items()}
    overall_total_cost = sum(total_costs.values())
    return overall_total_cost, total_costs

def main():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    access_token = get_access_token(client_id, client_secret)
    
    regions = ['us', 'eu', 'tw', 'kr']
    for region in regions:
        print(f'Fetching and processing data for {region} region.')
        
        # Fetch auction data for the region
        auction_data = fetch_data(region, access_token)
        
        # Save the fetched auction data into a region-specific file
        auction_data_filename = f'auction_data_{region}.json'
        save_data_as_json(auction_data_filename, auction_data)
        print(f'Auction data for {region} region saved to {auction_data_filename}.')

        # Define the parts data with item IDs and amounts needed
        parts_data = {
            'grip': [
                {'item_id': 205413, 'item_name': 'obsidian cobraskin', 'amount_needed': 3},
                {'item_id': 208212, 'item_name': 'dreaming essence', 'amount_needed': 5},
                {'item_id': 193230, 'item_name': 'mireslush hide', 'amount_needed': 50},
                {'item_id': 204460, 'item_name': 'zaralek glowspores', 'amount_needed': 400},
            ],
            'vellum': [
                {'item_id': 190324, 'item_name': 'awakened order', 'amount_needed': 50},
                {'item_id': 190316, 'item_name': 'awakened earth', 'amount_needed': 100},
                {'item_id': 190321, 'item_name': 'awakened fire', 'amount_needed': 150},
                {'item_id': 200113, 'item_name': 'resonant crystal', 'amount_needed': 200},
            ],
            'rune': [
                {'item_id': 204464, 'item_name': 'shadowflame essence', 'amount_needed': 10},
                {'item_id': 194863, 'item_name': 'runed writhebark', 'amount_needed': 50},
                {'item_id': 194755, 'item_name': 'cosmic ink', 'amount_needed': 250},
            ],
        }
    
        # Calculate the total cost for the region based on the auction data and parts_data
        # Note: You need to implement calculate_total_cost function to use it here.
        overall_total_cost, _ = calculate_total_cost(auction_data, parts_data)
        
        # Update the total cost file for the region with a new entry
        update_total_cost_file(region, overall_total_cost)
        print(f'Total cost for {region} region updated.')

if __name__ == '__main__':
    main()



