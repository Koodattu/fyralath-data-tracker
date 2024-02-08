import requests
import base64
import json
import os
import datetime
import shutil
from dotenv import load_dotenv

class AuctionDataFetcher:
    def __init__(self):
        load_dotenv()

    def get_access_token(self, client_id, client_secret):
        """Fetches an access token using client credentials."""
        credentials = f'{client_id}:{client_secret}'
        base64_encoded_credentials = base64.b64encode(credentials.encode()).decode()
        token_url = 'https://us.battle.net/oauth/token'
        data = {'grant_type': 'client_credentials'}
        headers = {'Authorization': f'Basic {base64_encoded_credentials}'}
        try:
            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            print(f"Error acquiring access token: {e}")
            return None

    def fetch_data(self, region, access_token):
        """Fetches data from a specific region."""
        url = f'https://{region}.api.blizzard.com/data/wow/auctions/commodities'
        params = {
            'namespace': f'dynamic-{region}',
            'locale': 'en_US',
            'access_token': access_token
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching data for {region} region: {e}")
            return None

    def save_data_as_json(self, filename, data):
        """Saves the fetched data as a JSON file."""
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            with open(filename, 'w') as file:
                json.dump(data, file)
        except Exception as e:
            print(f"Error saving data as JSON to {filename}: {e}")

    def entry_exists_for_current_hour(self, region):
        """Checks if an entry for the current year, month, day, and hour exists in the file."""
        filename = f'./data/total_cost_{region}.json'
        now = datetime.datetime.now().isoformat()
        current_date_hour = now[:13]

        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    data = json.load(file)
                    for entry in data:
                        entry_date_hour = entry['timestamp'][:13]
                        if entry_date_hour == current_date_hour:
                            return True
            return False
        except Exception as e:
            print(f"Error checking entry existence for {region} region: {e}")
            return False

    def update_total_cost_file(self, region, total_cost):
        """Updates the total cost file for the region with a new data entry."""
        filename = f'./data/total_cost_{region}.json'
        now = datetime.datetime.now().isoformat()
        entry = {'timestamp': now, 'total_cost': total_cost}
        
        try:
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            if os.path.exists(filename):
                with open(filename, 'r+') as file:
                    data = json.load(file)
                    data.append(entry)
                    file.seek(0)
                    json.dump(data, file)
            else:
                with open(filename, 'w') as file:
                    json.dump([entry], file)

            backup_folder = './data/backup'
            os.makedirs(backup_folder, exist_ok=True)
            backup_path = os.path.join(backup_folder, f'total_cost_{region}.json')
            shutil.copy(filename, backup_path)
        except Exception as e:
            print(f"Error updating total cost file for {region} region: {e}")

    def save_latest_data(self, latest_data):
        """Saves the latest data for all regions into a single JSON file."""
        filename = './data/latest_total_costs.json'
        try:
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            
            with open(filename, 'w') as file:
                json.dump(latest_data, file)
            print(f"Latest data saved to {filename}.")
        except Exception as e:
            print(f"Error saving latest data: {e}")

    def calculate_total_cost(self, auction_data, parts_data):
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

    def run(self):
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        access_token = self.get_access_token(client_id, client_secret)
        
        if access_token is None:
            print("Failed to acquire access token. Exiting.")
            return False

        latest_data = []
        regions = ['us', 'eu', 'tw', 'kr']
        for region in regions:
            print(f'Fetching and processing data for {region} region.')
            
            if self.entry_exists_for_current_hour(region):
                print(f'Entry for the current hour already exists for {region} region. Skipping.')
                continue

            auction_data = self.fetch_data(region, access_token)
            
            if auction_data is None:
                print(f"Failed to fetch auction data for {region} region. Skipping.")
                continue

            auction_data_filename = f'./data/auction_data/auction_data_{region}.json'
            self.save_data_as_json(auction_data_filename, auction_data)
            print(f'Auction data for {region} region saved to {auction_data_filename}.')

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

            overall_total_cost, _ = self.calculate_total_cost(auction_data, parts_data)
            print(f'Total cost for {region} region: {overall_total_cost}')

            latest_data.append({
                'region': region,
                'total_cost': overall_total_cost,
                'timestamp': datetime.datetime.now().isoformat()
            })

            self.update_total_cost_file(region, overall_total_cost)
            print(f'Total cost for {region} region updated.')

        if not latest_data:
            print("No new data fetched. Exiting.")
            return False
        
        self.save_latest_data(latest_data)
        return True

if __name__ == '__main__':
    auction_fetcher = AuctionDataFetcher()
    auction_fetcher.run()
