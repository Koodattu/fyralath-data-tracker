import requests
import base64
import os
import datetime
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
        """Fetches auction house data from a specific region."""
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

    def fetch_wow_token(self, region, access_token):
        """Fetches wow token data from a specific region."""
        url = f'https://{region}.api.blizzard.com/data/wow/token/index'
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

    def find_lowest_price(self, auction_data, item_id):
        lowest_price = None
        for auction in auction_data['auctions']:
            if auction['item']['id'] == item_id:
                if lowest_price is None or auction['unit_price'] < lowest_price:
                    lowest_price = auction['unit_price']
        return lowest_price
    
    def calculate_total_cost(self, auction_data, items):
        total_cost = 0
        item_details = []

        # Iterate through each item to calculate total cost and prepare details
        for item in items:
            # Skip Fyralath in the loop
            if item['id'] == 206448:
                continue

            # Find the lowest auction price for the item
            lowest_price = self.find_lowest_price(auction_data, item['id'])
            if lowest_price is None:
                print(f"Could not find auction data for item {item['name']}.")
                continue

            # Calculate cost based on amount needed, if applicable
            if 'amount_needed' in item:
                item_cost = lowest_price * item['amount_needed']
                total_cost += item_cost

                item_detail = {
                    'name': item['name'],
                    'id': item['id'],
                    'price': lowest_price,
                    'amount_needed': item['amount_needed']
                }

            item_details.append(item_detail)

        fyralath_detail = {
            "name": "Fyr'alath the Dreamrender", 
            "id": 206448,
            "price": total_cost
        }

        # Append Fyralath as the first item
        item_details.insert(0, fyralath_detail)

        return total_cost, item_details

    def run(self):
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        access_token = self.get_access_token(client_id, client_secret)

        if access_token is None:
            print("Failed to acquire access token. Exiting.")
            return None

        items = [
            {"name": "Fyr'alath the Dreamrender", "id": 206448},
            {"name": "Shadowflame Essence", "id": 204464, "amount_needed": 10},
            {"name": "Cosmic Ink", "id": 194755, "amount_needed": 250},
            {"name": "Runed Writhebark", "id": 194863, "amount_needed": 50},
            {"name": "Resonant Crystal", "id": 200113, "amount_needed": 200},
            {"name": "Awakened Fire", "id": 190321, "amount_needed": 150},
            {"name": "Awakened Earth", "id": 190316, "amount_needed": 100},
            {"name": "Awakened Order", "id": 190324, "amount_needed": 50},
            {"name": "Obsidian Cobraskin", "id": 205413, "amount_needed": 3},
            {"name": "Mireslush Hide", "id": 193230, "amount_needed": 50},
            {"name": "Zaralek Glowspores", "id": 204460, "amount_needed": 400},
            {"name": "Dreaming Essence", "id": 208212, "amount_needed": 5}
        ]

        aggregated_data = []
        regions = ['eu', 'us', 'tw', 'kr']
        for region in regions:
            print(f'Processing data for {region} region.')

            auction_data = self.fetch_data(region, access_token)
            if auction_data is None:
                print(f"Failed to obtain auction data for {region} region. Skipping.")
                continue

            total_cost, region_data = self.calculate_total_cost(auction_data, items)

            wow_token = self.fetch_wow_token(region, access_token)
            if wow_token is None:
                print(f"Failed to obtain wow token data for {region} region. Skipping.")

            wow_token_ratio = round(total_cost / wow_token['price'], 3)
            aggregated_data.append({"region": region, "wow_token_ratio": wow_token_ratio, "items": region_data})

        # Save the latest data for all regions if there's any data to save
        if aggregated_data:
            print("Data processing and saving completed for all regions.")
            timestamp = datetime.datetime.now()
            timestamp_dt = timestamp.replace(minute=0, second=0, microsecond=0)
            timestamp_adjusted = int(timestamp_dt.timestamp() * 1000)
            data_with_timestamp = {
                'timestamp': timestamp_adjusted,
                'data': aggregated_data
            }
            return data_with_timestamp
        else:
            print("No new data fetched. Exiting.")

        return None
    
if __name__ == "__main__":
    fetcher = AuctionDataFetcher()
    fetcher.run()