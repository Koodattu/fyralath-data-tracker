# we shouldnt do more than 300 requests per minute to either api combined
# we need to save our data every outer loop
# we use two loops, first loop:
# loop through rio private base pages 0-249 for classes, use dps for paladin and all for death-knight and warrior
# parse response, get character id, name, region, server, class
# loop through parsed characters using public api and check if they have fyralath equipped
# save character id, name, region, server, class, true or false for legendary and current timestamp if lege or timestamp 0 if no legendary
# save classes to different files

# loop through the data we have, calculate how many have the legendary and how many dont

import sys
import time
import os
import json
import requests
from dotenv import load_dotenv
import base64

# Define constants
CLASSES = ["death-knight", "paladin", "warrior"]
ROLES = {"death-knight": "tank", "paladin": "dps", "warrior": "dps"}
DATA_DIR = "./rio_data"
RATE_LIMIT = 300  # max requests per minute
REQUEST_INTERVAL = 60 / RATE_LIMIT  # pause between requests to respect rate limit

# API Endpoints
RIO_PRIVATE_BASE = "https://raider.io/api/mythic-plus/rankings/characters?region=world&season=season-df-3&class={class_name}&role={role}&page={page}"
RIO_API_BASE = "https://raider.io/api/v1/characters/profile?region={region}&realm={realm}&name={name}&fields=gear"

BLIZZARD_EQ_API = "https://{region}.api.blizzard.com/profile/wow/character/{realm}/{name}/equipment"
BLIZZARD_ACH_API = "https://{region}.api.blizzard.com/profile/wow/character/{realm}/{name}/achievements"

PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")

def save_progress(class_name, page):
    """Saves the progress to a file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as file:
            progress = json.load(file)
    else:
        progress = {}
    progress[class_name] = page
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as file:
        json.dump(progress, file)

def load_progress():
    """Loads the progress from a file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def is_wearing_fyrath_by_item_id_rio(character_gear):
    # The known item ID for Fyr'alath the Dreamrender
    fyrath_item_id = 206448
    # Check if the 'mainhand' key exists in 'items'
    main_hand_item = character_gear.get('gear', {}).get('items', {}).get('mainhand', {})
    # Check if the 'item_id' key exists in 'mainhand' and if it matches the Fyr'alath item ID
    return main_hand_item.get('item_id') == fyrath_item_id

def is_wearing_fyrath_by_item_id_blizz(character_gear):
    """
    Checks if the character is wearing an item with the specified Fyr'alath item ID.

    :param character_gear: Dictionary containing the character's gear from the WoW API.
    :param fyrath_item_id: The item ID for Fyr'alath the Dreamrender.
    :return: True if the character is wearing Fyr'alath, False otherwise.
    """
    # The known item ID for Fyr'alath the Dreamrender
    fyrath_item_id = 206448
    for item in character_gear.get('equipped_items', []):
        if item.get('item', {}).get('id') == fyrath_item_id:
            return True
    return False

def log_failed_request(url, status_code):
    """Logs failed requests with their URL and status code to a file."""
    log_filename = os.path.join(DATA_DIR, "failed_requests.log")
    with open(log_filename, "a", encoding="utf-8") as log_file:
        log_entry = f"Failed request to {url} with status code {status_code}\n"
        log_file.write(log_entry)


def get_access_token():
    """Fetches an access token using client credentials."""
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
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

def make_blizz_request(access_token, api, region, realm, name):
    """Fetches auction house data from a specific region."""
    url = api.format(region=region, realm=realm, name=name)
    params = {
        'namespace': f'profile-{region}',
        'locale': 'en_US',
        'access_token': access_token
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data from {url}: {response.status_code}")
            log_failed_request(url, response.status_code)
            return None
    except Exception as e:
        print(f"Error making request to {url}: {e}")
        log_failed_request(url, "Exception")
        return None

def make_rio_request(url):
    """Make an HTTP GET request and return the JSON response. Logs failures."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data from {url}: {response.status_code}")
            log_failed_request(url, response.status_code)
            return None
    except Exception as e:
        print(f"Error making request to {url}: {e}")
        log_failed_request(url, "Exception")
        return None

def initialize_character_count():
    character_count = 0
    for class_name in CLASSES:
        file_path = os.path.join(DATA_DIR, f"{class_name}_data.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                character_count += len(data)
    print(f"Total characters already processed: {character_count}")
    return character_count

def fetch_and_process_characters():
    progress = load_progress()
    # Ensure the data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    request_count = 0
    character_count = initialize_character_count()
    start_time = time.time()
    
    for class_name in CLASSES:
        role = ROLES[class_name]
        start_page = progress.get(class_name, 0)  # Load progress for current class or start at 0
        for page in range(start_page, 250):
            current_time = time.time()
            if request_count >= RATE_LIMIT:
                time.sleep(max(0, 60 - (current_time - start_time)))
                start_time = time.time()
                request_count = 0
            
            url = RIO_PRIVATE_BASE.format(class_name=class_name, role=role, page=page)
            data = make_rio_request(url)
            if not data:
                continue  # Skip to next page if data fetching fails

            for character in data['rankings']['rankedCharacters']:
                request_count += 1
                character_count += 1  # Increment character count
                char_info = character['character']
                char_url = RIO_API_BASE.format(region=char_info['region']['slug'], realm=char_info['realm']['slug'], name=char_info['name'])
                gear_data = make_rio_request(char_url)
                
                if gear_data:
                    has_fyrath = is_wearing_fyrath_by_item_id_rio(gear_data)
                    requests_per_minute = request_count / ((time.time() - start_time) / 60) if time.time() - start_time > 0 else request_count
                    # Update the console line with the latest info, including character count
                    sys.stdout.write(f"\rProcessed: {character_count}/30000 ({(character_count/30000*100):.2f}%), Page: {page}/250, Req/Min: {requests_per_minute:.2f}, Approx time left: {((30000-character_count)/requests_per_minute):.2f} minutes, Latest: {char_info['name']} on {char_info['realm']['name']}            ")
                    sys.stdout.flush()
                    
                    save_data(DATA_DIR, class_name, {
                        "id": char_info['id'],
                        "name": char_info['name'],
                        "region": char_info['region']['slug'],
                        "realm": char_info['realm']['slug'],
                        "class": class_name,
                        "has_fyralath": has_fyrath,
                        "timestamp": int(time.time()) if has_fyrath else 0
                    })
            save_progress(class_name, page + 1)  # Save progress after each page is processed
            time.sleep(max(0, 60/RATE_LIMIT - (time.time() - current_time)))  # Ensure we respect the RATE_LIMIT

def save_data(dir, class_name, data):
    """Appends new data to a list stored in a JSON file efficiently."""
    filename = os.path.join(dir, f"{class_name}_data.json")
    if os.path.exists(filename):
        with open(filename, 'rb+') as file:
            file.seek(-1, os.SEEK_END)
            file.truncate()
            if file.tell() > 1:
                file.write(b',')
            # Ensure the data is encoded in UTF-8
            file.write(json.dumps(data, ensure_ascii=False).encode('utf8'))
            file.write(b']')
    else:
        with open(filename, 'w', encoding='utf-8') as file:
            # Write data as a list and ensure ASCII characters are not escaped
            file.write(json.dumps([data], ensure_ascii=False))

def save_data(file_name, data):
    """Appends new data to a list stored in a JSON file efficiently."""
    filename = os.path.join(f"{file_name}")
    if os.path.exists(filename):
        with open(filename, 'rb+') as file:
            file.seek(-1, os.SEEK_END)
            file.truncate()
            if file.tell() > 1:
                file.write(b',')
            # Ensure the data is encoded in UTF-8
            file.write(json.dumps(data, ensure_ascii=False).encode('utf8'))
            file.write(b']')
    else:
        with open(filename, 'w', encoding='utf-8') as file:
            # Write data as a list and ensure ASCII characters are not escaped
            file.write(json.dumps([data], ensure_ascii=False))

def get_processed_character_ids(updated_file_path):
    if os.path.exists(updated_file_path):
        with open(updated_file_path, 'r', encoding='utf-8') as file:
            characters = json.load(file)
            return {character['id'] for character in characters}
    return set()

def load_data_from_file(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

def update_and_save_all_characters():
    access_token = get_access_token()  # Ensure you have a valid access token
    achievement_id = 19450  # ID for Fyr'alath the Dreamrender achievement

    for class_name in CLASSES:
        #sorted_file_path = os.path.join(DATA_DIR, f"{class_name}_sorted_data.json")
        #updated_file_path = sorted_file_path.replace('_sorted_data.json', '_updated_data.json')
        sorted_file_path = os.path.join(DATA_DIR, f"{class_name}_updated_data.json")
        updated_file_path = sorted_file_path.replace('_updated_data.json', '_updated_2upd2ated2_data.json')
        
        # Get already processed character IDs to avoid reprocessing
        processed_ids = get_processed_character_ids(updated_file_path)

        characters = load_data_from_file(sorted_file_path)

        for character in characters:
            # Check if the character has already been processed
            #if character['id'] in processed_ids:
                #continue

            if character['has_fyralath'] and character['timestamp'] == 0:
                achievements_data = make_blizz_request(access_token, BLIZZARD_ACH_API, character['region'].lower(), character['realm'].lower(), character['name'].lower())
                if achievements_data:
                    for achievement in achievements_data.get('achievements', []):
                        if achievement.get('id') == achievement_id:
                            character['timestamp'] = achievement.get('completed_timestamp', 0) // 1000
                            break
            
            # Append character data to the updated file, whether it was updated or not
            save_data(updated_file_path, character)
            print(f"Updated character {character}.")

        print(f"Updated characters for {class_name} processed.")

if __name__ == "__main__":
    #fetch_and_process_characters()
    update_and_save_all_characters()
