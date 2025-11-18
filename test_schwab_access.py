#!/usr/bin/env python3
"""Test what Schwab API endpoints we can actually access"""
import os
import sys
import requests
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

if not client.authenticate():
    print("[ERROR] Auth failed")
    sys.exit(1)

print("[SUCCESS] Authenticated\n")

# Test various endpoints to see what we can access
headers = {
    'Authorization': f'Bearer {client.access_token}',
    'X-API-Key': client.api_key,
    'Accept': 'application/json'
}

test_endpoints = [
    # Market data endpoints
    ('GET', '/marketdata/v1/markets', {'markets': 'equity'}),
    ('GET', '/marketdata/v1/quotes', {'symbols': 'SPY'}),
    ('GET', '/marketdata/v1/$SPX/quotes', {}),
    ('GET', '/marketdata/v1/SPY/quotes', {}),
    ('GET', '/marketdata/v1/pricehistory', {'symbol': 'SPY', 'periodType': 'day', 'period': 1, 'frequencyType': 'minute', 'frequency': 1}),

    # Trader endpoints
    ('GET', '/trader/v1/accounts', {}),
]

for method, endpoint, params in test_endpoints:
    url = f"{client.base_url}{endpoint}"
    print(f"\n{method} {endpoint}")
    print(f"  Params: {params}")

    resp = requests.get(url, headers=headers, params=params)
    print(f"  Status: {resp.status_code}")

    if resp.status_code == 200:
        print(f"  [SUCCESS]")
        data = resp.json()
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())}")
    else:
        print(f"  [FAILED]")
        if resp.text:
            print(f"  Error: {resp.text[:200]}")
