#!/usr/bin/env python3
"""
Test Schwab API with live market data
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.schwab_api import SchwabAPIClient

load_dotenv()

def test_schwab():
    print("Testing Schwab API...")

    client = SchwabAPIClient(
        api_key=os.getenv('SCHWAB_API_KEY'),
        api_secret=os.getenv('SCHWAB_API_SECRET'),
        redirect_uri=os.getenv('SCHWAB_REDIRECT_URI')
    )

    client.refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')

    if not client.authenticate():
        print("[ERROR] Authentication failed")
        return

    print("[SUCCESS] Authenticated!")

    # Test get_multiple_timeframes with datetime ranges
    from datetime import datetime, timedelta
    now = datetime.now()

    configs = [
        {'name': 'higher', 'frequency_type': 'minute', 'frequency': 30, 'start_datetime': now - timedelta(days=5)},
        {'name': 'middle', 'frequency_type': 'minute', 'frequency': 15, 'start_datetime': now - timedelta(days=3)},
        {'name': 'lower', 'frequency_type': 'minute', 'frequency': 5, 'start_datetime': now - timedelta(days=1)},
    ]

    print("\nFetching SPY data with multiple timeframes...")
    result = client.get_multiple_timeframes('SPY', configs)

    if result:
        print(f"[SUCCESS] Got data for {len(result)} timeframes:")
        for name, df in result.items():
            if df is not None:
                print(f"  - {name}: {len(df)} bars")
                print(f"    Latest: {df.tail(1)[['close']].to_string()}")
            else:
                print(f"  - {name}: None")
    else:
        print("[ERROR] No data returned")

if __name__ == '__main__':
    test_schwab()
