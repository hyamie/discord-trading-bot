#!/usr/bin/env python3
"""Test Schwab API with period/frequency approach"""
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

if not client.authenticate():
    print("[ERROR] Auth failed")
    sys.exit(1)

print("[SUCCESS] Authenticated!\n")

# Test different period/frequency combinations
tests = [
    ("5-min, 10 days", 'day', 10, 'minute', 5),
    ("15-min, 10 days", 'day', 10, 'minute', 15),
    ("30-min, 10 days", 'day', 10, 'minute', 30),
    ("1-hour (60min), 10 days", 'day', 10, 'minute', 60),  # This will fail
    ("Daily, 3 months", 'month', 3, 'daily', 1),
    ("Daily, 6 months", 'month', 6, 'daily', 1),
]

for name, period_type, period, freq_type, freq in tests:
    df = client.get_price_history(
        'SPY',
        period_type=period_type,
        period=period,
        frequency_type=freq_type,
        frequency=freq
    )

    if df is not None:
        date_range = f"{df.index[0].strftime('%Y-%m-%d %H:%M')} to {df.index[-1].strftime('%Y-%m-%d %H:%M')}"
        print(f"{name:25s}: {len(df):4d} bars  ({date_range})")
    else:
        print(f"{name:25s}: None")
