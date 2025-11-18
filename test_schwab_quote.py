#!/usr/bin/env python3
"""
Quick test to verify Schwab API is pulling live data
"""
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.schwab_api import SchwabAPIClient

load_dotenv()

def test_schwab_quote():
    """Test Schwab API quote fetching"""
    print("=" * 70)
    print("SCHWAB API QUOTE TEST")
    print("=" * 70)
    print()

    # Initialize client
    api_key = os.getenv('SCHWAB_API_KEY')
    api_secret = os.getenv('SCHWAB_API_SECRET')
    redirect_uri = os.getenv('SCHWAB_REDIRECT_URI')
    refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')

    if not all([api_key, api_secret, refresh_token]):
        print("[ERROR] Missing Schwab credentials in .env")
        return

    print(f"API Key: {api_key[:10]}...")
    print(f"Refresh Token: {refresh_token[:20]}...")
    print()

    # Create client
    client = SchwabAPIClient(
        api_key=api_key,
        api_secret=api_secret,
        redirect_uri=redirect_uri
    )

    # Set refresh token
    client.refresh_token = refresh_token

    # Authenticate
    print("Authenticating with Schwab...")
    if not client.authenticate():
        print("[ERROR] Authentication failed")
        return

    print("[SUCCESS] Authenticated!")
    print()

    # Test ES quote
    print("Fetching ES quote...")
    quote = client.get_quote('ES')

    if quote:
        print("[SUCCESS] Got ES quote:")
        print()
        print(f"Symbol: {quote.get('symbol')}")
        print(f"Last Price: ${quote.get('lastPrice', 'N/A')}")
        print(f"Bid: ${quote.get('bidPrice', 'N/A')}")
        print(f"Ask: ${quote.get('askPrice', 'N/A')}")
        print(f"Volume: {quote.get('totalVolume', 'N/A')}")
        print(f"Quote Time: {quote.get('quoteTime', 'N/A')}")
        print()
        print("Full quote data:")
        import json
        print(json.dumps(quote, indent=2))
    else:
        print("[ERROR] No quote data returned")
        print()

        # Try SPY as fallback
        print("Trying SPY instead...")
        spy_quote = client.get_quote('SPY')
        if spy_quote:
            print("[SUCCESS] Got SPY quote:")
            print()
            print(f"Symbol: {spy_quote.get('symbol')}")
            print(f"Last Price: ${spy_quote.get('lastPrice', 'N/A')}")
            print(f"Bid: ${spy_quote.get('bidPrice', 'N/A')}")
            print(f"Ask: ${spy_quote.get('askPrice', 'N/A')}")
            print(f"Volume: {spy_quote.get('totalVolume', 'N/A')}")
        else:
            print("[ERROR] SPY quote also failed")

if __name__ == '__main__':
    test_schwab_quote()
