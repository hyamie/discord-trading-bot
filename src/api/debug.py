"""
Quick debug script to test yfinance locally
"""

import sys
sys.path.insert(0, '/app')  # For Railway

from src.utils.yfinance_client import YFinanceClient

print("Creating YFinance client...")
client = YFinanceClient()

print("\nTesting AAPL day trade data...")
data = client.get_day_trade_data('AAPL')

print(f"\nGot {len(data)} timeframes:")
for key, df in data.items():
    if df is not None:
        print(f"  {key}: {len(df)} bars")
        print(f"    Columns: {list(df.columns)}")
        print(f"    Latest close: ${df['close'].iloc[-1]:.2f}")
    else:
        print(f"  {key}: None")

print("\nTesting SPY...")
spy = client.get_price_history('SPY', period='5d', interval='1h')
if spy is not None:
    print(f"SPY: {len(spy)} bars, latest: ${spy['close'].iloc[-1]:.2f}")
else:
    print("SPY: Failed")

print("\nDone!")
