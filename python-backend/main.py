import requests
import base64
import json
from dotenv import load_dotenv
import os

# Replace 'YOUR_CLIENT_ID' and 'YOUR_CLIENT_SECRET' with your actual client credentials
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Combine the client ID and client secret with a colon (:) separator
credentials = f'{client_id}:{client_secret}'

# Encode the credentials as a Base64-encoded string
base64_encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Define the token URL
token_url = 'https://us.battle.net/oauth/token'

# Define the grant type as 'client_credentials'
data = {
    'grant_type': 'client_credentials'
}

# Encode the client credentials in the request headers
headers = {
    'Authorization': f'Basic {base64_encoded_credentials}'
}

# Send the POST request to obtain the access token
response = requests.post(token_url, data=data, headers=headers)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']
    print(f'Acquired access token. Expires in {token_data["expires_in"]} seconds.')
else:
    print(f'Error: Status Code {response.status_code}')


# Replace 'YOUR_API_KEY' with your actual Blizzard API key
api_key = access_token

# Define the base URL for the Blizzard API
url = 'https://us.api.blizzard.com/data/wow/auctions/commodities'

# Define any additional parameters you want to include in the request
params = {
    ':region': 'us',
    'namespace': 'dynamic-us',
    'locale': 'en_US',
    'access_token': api_key  # Include your API key here
}

if os.path.exists('auction_data.json'):
    with open('auction_data.json', 'r') as file:
        auction_data = json.load(file)
    print('Auction data loaded from existing file.')
else:
    # Send a GET request to the Auction House API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        auction_data = response.json()

        with open('auction_data.json', 'w') as file:
            json.dump(auction_data, file)
            
        print('Auction data has been saved to auction_data.json')
    else:
        print(f'Error: Status Code {response.status_code}')

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

item_id_to_name = {}
for part_data in parts_data.values():
    for item in part_data:
        item_id_to_name[item['item_id']] = item['item_name']

# Process the auction data once to find the lowest prices for items in parts_data
# Create a dictionary to store the lowest prices for each item ID
lowest_prices = {}

for auction in auction_data['auctions']:
    item_id = auction['item']['id']
    unit_price = auction['unit_price']

    # Check if the item_id is in parts_data
    if item_id in item_id_to_name:
        # Update lowest_prices if the price is lower or if item_id is not in lowest_prices
        if item_id not in lowest_prices or unit_price < lowest_prices[item_id]:
            lowest_prices[item_id] = unit_price

# Print individual items and their lowest prices
print('Individual Items and Lowest Prices:')
for item_id, lowest_price in lowest_prices.items():
    item_name = item_id_to_name[item_id]  # Get item name from the dictionary
    print(f'Item ID: {item_id}, Item Name: {item_name}, Lowest Price: {lowest_price}')

# Calculate the total cost for each part based on the lowest prices and amounts needed
total_costs = {}
for part, items in parts_data.items():
    total_cost = sum(lowest_prices.get(item['item_id'], 0) * item['amount_needed'] for item in items)
    total_costs[part] = total_cost

# Calculate the overall total cost by summing up the costs of all parts
overall_total_cost = sum(total_costs.values())

# Print the results
print('Total Costs for Each Part:')
for part, cost in total_costs.items():
    print(f'{part}: {cost}')

# Function to convert coppers to gold, silver, and copper values
def convert_coppers_to_gold_silver_copper(coppers):
    gold = coppers // 10000
    silver = (coppers % 10000) // 100
    copper = coppers % 100
    return gold, silver, copper

# Calculate the overall total cost in coppers
overall_total_cost_copper = overall_total_cost

# Convert the overall total cost to gold, silver, and copper
overall_total_cost_gold, overall_total_cost_silver, overall_total_cost_copper = convert_coppers_to_gold_silver_copper(overall_total_cost_copper)

# Format the overall total cost in gold with commas
formatted_overall_total_cost_gold = '{:,}'.format(overall_total_cost_gold)

# Print the overall total cost in the desired format
print(f'Overall Total Cost: {formatted_overall_total_cost_gold} gold, {overall_total_cost_silver} silver, {overall_total_cost_copper} copper')
