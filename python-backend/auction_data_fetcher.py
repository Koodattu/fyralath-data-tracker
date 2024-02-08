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

    def get_or_fetch_auction_data(self, region, access_token):
        """Attempts to read auction data from a local file, and fetches it if not found."""
        auction_data_filename = f'./data/auction_data/auction_data_{region}.json'

        # Check if the auction data file exists and has content
        try:
            if os.path.exists(auction_data_filename) and os.path.getsize(auction_data_filename) > 0:
                print(f'Using existing auction data for {region} region.')
                with open(auction_data_filename, 'r') as file:
                    auction_data = json.load(file)
                return auction_data
        except Exception as e:
            print(f"Error reading existing auction data for {region} region: {e}")

        # If file doesn't exist or is empty, fetch new data
        print(f'Fetching new auction data for {region} region.')
        auction_data = self.fetch_data(region, access_token)
        if auction_data is not None:
            self.save_data_as_json(auction_data_filename, auction_data)
        return auction_data

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

    def calculate_total_cost(self, auction_data, base_json, item_ids):

        # Helper function to update item prices in the JSON structure
        def update_item_prices(parts, auction_prices):
            for part in parts:
                if part['id'] in auction_prices:
                    part['price'] = auction_prices[part['id']]
                if 'parts' in part:
                    update_item_prices(part['parts'], auction_prices)

        # Extract auction prices for relevant item IDs
        auction_prices = {}
        for auction in auction_data['auctions']:
            item_id = auction['item']['id']
            unit_price = auction.get('unit_price', auction.get('buyout'))
            if item_id in item_ids:
                # Update the price if it's lower than an existing price or if it hasn't been set
                if item_id not in auction_prices or unit_price < auction_prices[item_id]:
                    auction_prices[item_id] = unit_price

        # Update item prices in the base JSON structure
        if 'parts' in base_json:
            update_item_prices(base_json['parts'], auction_prices)

        # Recalculate prices for composite items
        def recalculate_composite_item_prices(parts):
            for part in parts:
                if 'parts' in part:
                    part['price'] = sum(p.get('price', 0) * p.get('amount_needed', 1) for p in part['parts'] if p.get('price') is not None)
                    recalculate_composite_item_prices(part['parts'])

        def update_composite_items_price(base_json):
            base_json['price'] = sum(part.get('price', 0) * part.get('amount_needed', 1) for part in base_json['parts'])

        # After updating all item prices based on auction data and recalculating component prices
        recalculate_composite_item_prices(base_json['parts'])
        update_composite_items_price(base_json)  # Ensures composite item prices are correctly summed up

        return base_json

    def save_latest_data(self, aggregated_data):
        filename = './data/latest_item_prices.json'
        timestamp = datetime.datetime.now().isoformat()
        data_with_timestamp = {
            'timestamp': timestamp,
            'data': aggregated_data
        }

        try:
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            with open(filename, 'w') as file:
                json.dump(data_with_timestamp, file)
            print(f"Latest item prices saved to {filename}.")
        except Exception as e:
            print(f"Error saving latest item prices: {e}")

    def read_base_json(self):
        try:
            with open('base.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error reading base JSON: {e}")
            return None

    def extract_item_ids(self, base_json):
        item_ids = set()
    
        def traverse_parts(parts):
            for part in parts:
                item_ids.add(part['id'])
                if 'parts' in part:
                    traverse_parts(part['parts'])
    
        if 'parts' in base_json:
            traverse_parts(base_json['parts'])
    
        return list(item_ids)

    def run(self):
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        access_token = self.get_access_token(client_id, client_secret)

        if access_token is None:
            print("Failed to acquire access token. Exiting.")
            return False

        base_json = self.read_base_json()
        if not base_json:
            print("Failed to read base JSON structure. Exiting.")
            return False

        aggregated_data = []
        regions = ['us', 'eu', 'tw', 'kr']
        for region in regions:
            print(f'Processing data for {region} region.')

            if self.entry_exists_for_current_hour(region):
                print(f'Entry for the current hour already exists for {region} region. Skipping.')
                continue

            auction_data = self.get_or_fetch_auction_data(region, access_token)
            if auction_data is None:
                print(f"Failed to obtain auction data for {region} region. Skipping.")
                continue

            item_ids = self.extract_item_ids(base_json)

            # Now, instead of using a reversed list, update prices in base_json directly using extracted item_ids
            # Then, recalculate composite item prices based on updated auction prices
            region_data = self.calculate_total_cost(auction_data, base_json, item_ids)
            aggregated_data.append({"region": region, "data": region_data})

        # Save the latest data for all regions if there's any data to save
        if aggregated_data:
            self.save_latest_data(aggregated_data)
            print("Data processing and saving completed for all regions.")
        else:
            print("No new data fetched. Exiting.")

        return True

if __name__ == '__main__':
    auction_fetcher = AuctionDataFetcher()
    auction_fetcher.run()
