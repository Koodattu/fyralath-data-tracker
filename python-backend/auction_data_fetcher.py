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

    def calculate_total_cost(self, auction_data, components_data, items_data):
        # First, update auction item prices in items_data
        for auction in auction_data['auctions']:
            item_id = auction['item']['id']
            unit_price = auction.get('unit_price', auction.get('buyout'))
            if item_id in items_data and (items_data[item_id]['price'] is None or unit_price < items_data[item_id]['price']):
                items_data[item_id]['price'] = unit_price

        # Then, calculate component prices
        for component_id, component_info in components_data.items():
            component_total_cost = 0
            for part in component_info['parts']:
                item_id = part['item_id']
                amount_needed = part['amount_needed']
                if item_id in items_data and items_data[item_id]['price'] is not None:
                    component_total_cost += items_data[item_id]['price'] * amount_needed
            items_data[component_id]['price'] = component_total_cost  # Update component price in items_data

        # Finally, calculate prices for final items based on components
        for item_id, item_info in items_data.items():
            if 'components' in item_info:
                final_price = sum(items_data[comp_id]['price'] for comp_id in item_info['components'] if items_data[comp_id]['price'] is not None)
                items_data[item_id]['price'] = final_price

        # Prepare data for saving, only include items with non-null prices
        latest_data = []
        for item_id, item_info in items_data.items():
            if item_info['price'] is not None:
                latest_data.append({'item_id': item_id, 'name': item_info['name'], 'price': item_info['price']})
        return latest_data

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

    def run(self):
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        access_token = self.get_access_token(client_id, client_secret)

        if access_token is None:
            print("Failed to acquire access token. Exiting.")
            return False
    
        aggregated_data = {}
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

            components_data = {
                # Component for Erden's Dreamleaf Grip
                209351: {  
                    'parts': [
                        {'item_id': 205413, 'amount_needed': 3},  # Obsidian Cobraskin
                        {'item_id': 208212, 'amount_needed': 5},  # Dreaming Essence
                        {'item_id': 193230, 'amount_needed': 50},  # Mireslush Hide
                        {'item_id': 204460, 'amount_needed': 400},  # Zaralek Glowspores
                    ]
                },
                # Component for Shalasar's Sophic Vellum
                210003: {  
                    'parts': [
                        {'item_id': 190324, 'amount_needed': 50},  # Awakened Order
                        {'item_id': 190316, 'amount_needed': 100},  # Awakened Earth
                        {'item_id': 190321, 'amount_needed': 150},  # Awakened Fire
                        {'item_id': 200113, 'amount_needed': 200},  # Resonant Crystal
                    ]
                },
                # Component for Lydiara's Binding Rune
                209998: {  
                    'parts': [
                        {'item_id': 204464, 'amount_needed': 10},  # Shadowflame Essence
                        {'item_id': 194863, 'amount_needed': 50},  # Runed Writhebark
                        {'item_id': 194755, 'amount_needed': 250},  # Cosmic Ink
                    ]
                },
                # Component for Fyr'alath the Dreamrender
                207728: {  
                    'parts': [
                        {'item_id': 209351, 'amount_needed': 1},  # Erden's Dreamleaf Grip
                        {'item_id': 210003, 'amount_needed': 1},  # Shalasar's Sophic Vellum
                        {'item_id': 209998, 'amount_needed': 1}  # Lydiara's Binding Rune
                    ]
                }
            }

            items_data = {
                207728: {"name": "Fyr'alath the Dreamrender", "price": None},
                209351: {"name": "Erden's Dreamleaf Grip", "price": None},
                210003: {"name": "Shalasar's Sophic Vellum", "price": None},
                209998: {"name": "Lydiara's Binding Rune", "price": None},
                205413: {"name": "Obsidian Cobraskin", "price": None},
                208212: {"name": "Dreaming Essence", "price": None},
                193230: {"name": "Mireslush Hide", "price": None},
                204460: {"name": "Zaralek Glowspores", "price": None},
                190324: {"name": "Awakened Order", "price": None},
                190316: {"name": "Awakened Earth", "price": None},
                190321: {"name": "Awakened Fire", "price": None},
                200113: {"name": "Resonant Crystal", "price": None},
                204464: {"name": "Shadowflame Essence", "price": None},
                194863: {"name": "Runed Writhebark", "price": None},
                194755: {"name": "Cosmic Ink", "price": None}
            }

            region_data = self.calculate_total_cost(auction_data, components_data, items_data)

            # Store the data for the current region
            aggregated_data[region] = region_data

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
