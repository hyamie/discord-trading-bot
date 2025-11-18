#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from utils.schwab_api import SchwabAPIClient

load_dotenv()

client = SchwabAPIClient(
    api_key=os.getenv('SCHWAB_API_KEY'),
    api_secret=os.getenv('SCHWAB_API_SECRET'),
    redirect_uri=os.getenv('SCHWAB_REDIRECT_URI')
)
client.refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')

print(f"Refresh token set: {bool(client.refresh_token)}")
print(f"Refresh token (first 50 chars): {client.refresh_token[:50] if client.refresh_token else 'None'}...")

if client.authenticate():
    print("\n[SUCCESS] Authenticated")
    print(f"Access token set: {bool(client.access_token)}")
    print(f"Access token (first 50 chars): {client.access_token[:50] if client.access_token else 'None'}...")
    print(f"Token expires at: {client.token_expires_at}")

    # Try a simple GET to the base API
    import requests
    headers = {
        'Authorization': f'Bearer {client.access_token}',
        'Accept': 'application/json'
    }

    # Try different endpoints
    endpoints = [
        '/trader/v1/accounts',
        '/marketdata/v1/markets',
        '/marketdata/v1/$SPX/quotes',
    ]

    for endpoint in endpoints:
        url = f"{client.base_url}{endpoint}"
        print(f"\nTrying: {url}")
        resp = requests.get(url, headers=headers)
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  Error: {resp.text[:200]}")
else:
    print("[ERROR] Auth failed")
