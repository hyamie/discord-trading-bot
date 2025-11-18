#!/usr/bin/env python3
"""Test with known-good parameters from working GitHub example"""
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

# Try the exact parameters from the GitHub example
# symbol=AAPL&periodType=year&period=2&frequencyType=daily&frequency=1
print("Test 1: Year/daily (like GitHub example)")
df = client.get_price_history('AAPL', period_type='year', period=2, frequency_type='daily', frequency=1)
if df is not None:
    print(f"  [SUCCESS] Got {len(df)} bars")
else:
    print("  [FAILED]")

# Try simpler period/frequency combinations
tests = [
    ("1 day, 1min", {'period_type': 'day', 'period': 1, 'frequency_type': 'minute', 'frequency': 1}),
    ("1 day, 5min", {'period_type': 'day', 'period': 1, 'frequency_type': 'minute', 'frequency': 5}),
    ("10 days, daily", {'period_type': 'day', 'period': 10, 'frequency_type': 'daily', 'frequency': 1}),
]

for desc, params in tests:
    print(f"\nTest: {desc}")
    df = client.get_price_history('SPY', **params)
    if df is not None:
        print(f"  [SUCCESS] Got {len(df)} bars")
    else:
        print("  [FAILED]")
