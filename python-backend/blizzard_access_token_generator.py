import sys
import time
import os
import json
import requests
from dotenv import load_dotenv
import base64



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


if __name__ == "__main__":
    print(get_access_token())
