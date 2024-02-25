import sys
import time
import os
import json
import requests
from dotenv import load_dotenv
import base64

from mongodb_manager import MongoDBManager

# Define constants
CLASSES = ["death-knight", "paladin", "warrior"]
ROLES = {"death-knight": "all", "paladin": "dps", "warrior": "dps"}
RATE_LIMIT = 300
REQUEST_INTERVAL = 60 / RATE_LIMIT

# API Endpoints
RIO_PRIVATE_BASE = "https://raider.io/api/mythic-plus/rankings/characters?region=world&season=season-df-3&class={class_name}&role={role}&page={page}"
RIO_API_BASE = "https://raider.io/api/v1/characters/profile?region={region}&realm={realm}&name={name}&fields=gear"

BLIZZARD_EQ_API = "https://{region}.api.blizzard.com/profile/wow/character/{realm}/{name}/equipment"
BLIZZARD_ACH_API = "https://{region}.api.blizzard.com/profile/wow/character/{realm}/{name}/achievements"
BLIZZARD_RAIDS_API = "https://{region}.api.blizzard.com/profile/wow/character/{realm}/{name}/encounters/raids"

def is_wearing_fyrath_by_item_id_rio(character_gear):
    fyralath_item_id = 206448
    main_hand_item = character_gear.get('gear', {}).get('items', {}).get('mainhand', {})
    return main_hand_item.get('item_id') == fyralath_item_id
def is_wearing_fyrath_by_item_id_blizz(character_gear):
    fyrath_item_id = 206448
    for item in character_gear.get('equipped_items', []):
        if item.get('item', {}).get('id') == fyrath_item_id:
            return True
    return False

def log_failed_request(url, status_code):
    """Logs failed requests with their URL and status code to a file."""
    DATA_DIR = "./rio_data"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
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
    url = api.format(region=region, realm=realm.lower(), name=name.lower())
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

class AcquisitionDataFetcher:
    def fetch_and_process_characters():
        mongo_db_manager = MongoDBManager()
        saved_character_ids, saved_characters_per_class = mongo_db_manager.get_saved_character_ids_with_class()
        request_count = 0
        character_count = sum(len(ids) for ids in saved_character_ids.values())
        start_time = time.time()
        access_token = get_access_token()

        for class_name in CLASSES:
            role = ROLES[class_name]
            for page in range(0, 500):
                if saved_characters_per_class[class_name] >= 10000:
                    break

                current_time = time.time()
                if request_count >= RATE_LIMIT:
                    time.sleep(max(0, 60 - (current_time - start_time)))
                    start_time = time.time()
                    request_count = 0

                url = RIO_PRIVATE_BASE.format(class_name=class_name, role=role, page=page)
                data = make_rio_request(url)
                request_count += 1
                if not data:
                    continue

                for character in data['rankings']['rankedCharacters']:
                    char_info = character['character']
                    char_name = char_info['name']
                    char_id = char_info['id']

                    if char_id in saved_character_ids[class_name]:
                        continue

                    char_url = RIO_API_BASE.format(region=char_info['region']['slug'], realm=char_info['realm']['slug'], name=char_name)
                    gear_data = make_rio_request(char_url)
                    fyralath_acquired_date = 0

                    if gear_data and is_wearing_fyrath_by_item_id_rio(gear_data):
                        achievements_data = make_blizz_request(access_token, BLIZZARD_ACH_API, char_info['region']['slug'], char_info['realm']['slug'], char_name)
                        if achievements_data:
                            for achievement in achievements_data.get('achievements', []):
                                if achievement.get('id') == 19450:
                                    fyralath_acquired_date = achievement.get('completed_timestamp', 0) // 1000
                                    break

                    raids_data = make_blizz_request(access_token, BLIZZARD_RAIDS_API, char_info['region']['slug'], char_info['realm']['slug'], char_name)
                    fyrakk_kills_hc = 0
                    fyrakk_kills_m = 0
                    if raids_data:
                        for expansion in raids_data.get('expansions', []):
                            for instance in expansion.get('instances', []):
                                for mode in instance.get('modes', []):
                                    if mode.get('difficulty', {}).get('name') == "Heroic":
                                        for encounter in mode.get('progress', {}).get('encounters', []):
                                            if encounter.get('encounter', {}).get('id') == 2519:
                                                fyrakk_kills_hc = encounter.get('completed_count', 0)
                                    elif mode.get('difficulty', {}).get('name') == "Mythic":
                                        for encounter in mode.get('progress', {}).get('encounters', []):
                                            if encounter.get('encounter', {}).get('id') == 2519:
                                                fyrakk_kills_m = encounter.get('completed_count', 0)
                    save_character = fyrakk_kills_hc > 0 or fyrakk_kills_m > 0
                    if fyrakk_kills_hc > 0 or fyrakk_kills_m > 0:
                        character_data = {
                            "name": char_name,
                            "char_id": char_id,
                            "region": char_info['region']['slug'],
                            "realm": char_info['realm']['slug'],
                            "class": class_name,
                            "fyralath_acquired_date": fyralath_acquired_date,
                            "fyrakk_kills_hc": fyrakk_kills_hc,
                            "fyrakk_kills_m": fyrakk_kills_m
                        }
                        mongo_db_manager.save_character_data_by_class(class_name, character_data)
                        saved_characters_per_class[class_name] += 1
                        character_count += 1
                        if saved_characters_per_class[class_name] >= 10000:
                            break

                    requests_per_minute = request_count / ((time.time() - start_time) / 60) if time.time() - start_time > 0 else request_count
                    sys.stdout.write(f"\rProcessed: {character_count}/30000 ({(character_count/30000*100):.2f}%), Page: {page}, Req/Min: {requests_per_minute:.2f}, Approx time left: {((30000-character_count)/requests_per_minute):.2f} minutes, Latest: {char_name} on {char_info['realm']['slug']}, Saved: {save_character}           ")
                    sys.stdout.flush()

                time.sleep(max(0, 60/RATE_LIMIT - (time.time() - current_time)))
                if saved_characters_per_class[class_name] >= 10000:
                    print(f"Reached 10,000 saved characters for class {class_name}. Moving to next class.")
                    break  # Ensure breaking out of the page loop as well

            # Check if the loop was exited due to reaching the limit
            if saved_characters_per_class[class_name] < 10000:
                print(f"Processed all available pages for class {class_name} but did not reach 10,000 characters. Total saved: {saved_characters_per_class[class_name]}")

    def update_characters_data(self):
        mongo_db_manager = MongoDBManager()
        characters_to_update = mongo_db_manager.get_characters_without_fyralath()
        for class_name, characters in characters_to_update.items():
            for char in characters:
                char_id = char['char_id']
                region = char['region']
                realm = char['realm']
                name = char['name']

                char_url = RIO_API_BASE.format(region=region, realm=realm, name=name)
                gear_data = make_rio_request(char_url)
                
                fyralath_acquired_date = 0
                fyrakk_kills_hc, fyrakk_kills_m = 0, 0

                if gear_data and is_wearing_fyrath_by_item_id_rio(gear_data):
                    achievements_data = make_blizz_request(self.access_token, BLIZZARD_ACH_API, region, realm, name)
                    if achievements_data:
                        for achievement in achievements_data.get('achievements', []):
                            if achievement.get('id') == 19450:  # ID for Fyralath acquisition
                                fyralath_acquired_date = achievement.get('completed_timestamp', 0) // 1000
                                break

                    raids_data = make_blizz_request(self.access_token, BLIZZARD_RAIDS_API, region, realm, name)
                    if raids_data:
                        for expansion in raids_data.get('expansions', []):
                            for instance in expansion.get('instances', []):
                                for mode in instance.get('modes', []):
                                    if mode.get('difficulty', {}).get('name') == "Heroic":
                                        for encounter in mode.get('progress', {}).get('encounters', []):
                                            if encounter.get('encounter', {}).get('id') == 2519:
                                                fyrakk_kills_hc = encounter.get('completed_count', 0)
                                    elif mode.get('difficulty', {}).get('name') == "Mythic":
                                        for encounter in mode.get('progress', {}).get('encounters', []):
                                            if encounter.get('encounter', {}).get('id') == 2519:
                                                fyrakk_kills_m = encounter.get('completed_count', 0)

                # Update MongoDB document
                if fyralath_acquired_date > 0 or fyrakk_kills_hc > 0 or fyrakk_kills_m > 0:
                    updates = {
                        "fyralath_acquired_date": fyralath_acquired_date,
                        "fyrakk_kills_hc": fyrakk_kills_hc,
                        "fyrakk_kills_m": fyrakk_kills_m
                    }
                    mongo_db_manager.update_character(class_name, char_id, updates)

if __name__ == "__main__":
    fetcher = AcquisitionDataFetcher()
    fetcher.fetch_and_process_characters()
    fetcher.update_characters_data()
