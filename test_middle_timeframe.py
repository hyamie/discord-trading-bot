#!/usr/bin/env python3
"""Test why middle timeframe only returns 14-15 bars"""
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

# Test different day ranges for 15m bars
now = datetime.now()
tests = [
    ("3 days", 3),
    ("5 days", 5),
    ("7 days", 7),
    ("10 days", 10),
    ("14 days", 14),
]

for name, days in tests:
    start = now - timedelta(days=days)
    df = client.get_price_history(
        'SPY',
        frequency_type='minute',
        frequency=15,
        start_datetime=start
    )

    if df is not None:
        print(f"{name:10s}: {len(df):4d} bars  (from {df.index[0]} to {df.index[-1]})")
    else:
        print(f"{name:10s}: None")
