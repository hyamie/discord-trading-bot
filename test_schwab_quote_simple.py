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

if client.authenticate():
    print("[SUCCESS] Authenticated")

    # Try quote endpoint
    quote = client.get_quote('SPY')
    if quote:
        print(f"[SUCCESS] Got quote: {quote.get('symbol')} = ${quote.get('lastPrice', 'N/A')}")
    else:
        print("[ERROR] Quote failed")
else:
    print("[ERROR] Auth failed")
