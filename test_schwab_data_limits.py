#!/usr/bin/env python3
"""Test Schwab API data availability limits"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

print("[SUCCESS] Authenticated!\n")

now = datetime.now()

# Test different frequency types
tests = [
    ("1-min, 7 days", 'minute', 1, 7),
    ("5-min, 7 days", 'minute', 5, 7),
    ("15-min, 7 days", 'minute', 15, 7),
    ("30-min, 7 days", 'minute', 30, 7),
    ("Daily, 60 days", 'daily', 1, 60),
    ("Daily, 180 days", 'daily', 1, 180),
    ("Weekly, 180 days", 'weekly', 1, 180),
]

for name, freq_type, freq, days in tests:
    start = now - timedelta(days=days)
    df = client.get_price_history(
        'SPY',
        frequency_type=freq_type,
        frequency=freq,
        start_datetime=start
    )

    if df is not None:
        date_range = f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}"
        print(f"{name:20s}: {len(df):4d} bars  ({date_range})")
    else:
        print(f"{name:20s}: None")
