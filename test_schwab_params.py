#!/usr/bin/env python3
"""
Test different Schwab API parameter combinations
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.schwab_api import SchwabAPIClient

load_dotenv()

def test_params():
    client = SchwabAPIClient(
        api_key=os.getenv('SCHWAB_API_KEY'),
        api_secret=os.getenv('SCHWAB_API_SECRET'),
        redirect_uri=os.getenv('SCHWAB_REDIRECT_URI')
    )
    client.refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')

    if not client.authenticate():
        print("[ERROR] Auth failed")
        return

    print("[SUCCESS] Authenticated!\n")

    # Test different parameter combinations
    tests = [
        {"desc": "1h bars, 5 days", "period_type": "day", "period": 5, "frequency_type": "minute", "frequency": 60},
        {"desc": "15m bars, 5 days", "period_type": "day", "period": 5, "frequency_type": "minute", "frequency": 15},
        {"desc": "5m bars, 1 day", "period_type": "day", "period": 1, "frequency_type": "minute", "frequency": 5},
        {"desc": "1m bars, 1 day", "period_type": "day", "period": 1, "frequency_type": "minute", "frequency": 1},
        {"desc": "5m bars, 10 days", "period_type": "day", "period": 10, "frequency_type": "minute", "frequency": 5},
    ]

    for test in tests:
        desc = test.pop("desc")
        print(f"Testing: {desc}")
        print(f"  Params: {test}")

        df = client.get_price_history('SPY', **test)

        if df is not None:
            print(f"  [SUCCESS] Got {len(df)} bars")
            print(f"  Latest: {df.tail(1)[['close']].values[0][0]:.2f}")
        else:
            print(f"  [FAILED]")
        print()

if __name__ == '__main__':
    test_params()
