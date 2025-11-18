#!/usr/bin/env python3
"""Test with the NEW period-based configuration"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.schwab_api import SchwabAPIClient
from utils.indicators import TechnicalIndicators

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

# NEW configuration from main.py
day_configs = [
    {'name': 'higher', 'period_type': 'day', 'period': 10, 'frequency_type': 'minute', 'frequency': 30},  # 30m bars, 10 days
    {'name': 'middle', 'period_type': 'month', 'period': 1, 'frequency_type': 'daily', 'frequency': 1},   # Daily bars, 1 month
    {'name': 'lower', 'period_type': 'day', 'period': 5, 'frequency_type': 'minute', 'frequency': 1},     # 1-min bars, 5 days
]

print("Fetching SPY data with NEW config...")
price_data = client.get_multiple_timeframes('SPY', day_configs)

if not price_data:
    print("[ERROR] No price data")
    sys.exit(1)

print(f"[SUCCESS] Got {len(price_data)} timeframes\n")

# Calculate indicators
indicators = TechnicalIndicators()

higher_tf = indicators.calculate_all_indicators(price_data['higher'])
middle_tf = indicators.calculate_all_indicators(price_data['middle'], include_vwap=False)  # Daily doesn't have VWAP
lower_tf = indicators.calculate_all_indicators(price_data['lower'])

# Get signals
higher_signals = indicators.get_signal_summary(higher_tf, "30m")
middle_signals = indicators.get_signal_summary(middle_tf, "daily")
lower_signals = indicators.get_signal_summary(lower_tf, "5m")

print("=== DATA SUMMARY ===\n")
print(f"Higher (30m): {len(price_data['higher'])} bars")
print(f"Middle (daily): {len(price_data['middle'])} bars")
print(f"Lower (1m): {len(price_data['lower'])} bars")
print()

print("=== SIGNAL ANALYSIS ===\n")

print("HIGHER TIMEFRAME (30m):")
print(f"  Trend bias: {higher_signals.get('trend_bias')}")
print(f"  Momentum bias: {higher_signals.get('momentum_bias')}")
print(f"  RSI: {higher_signals.get('rsi'):.2f}")
print()

print("MIDDLE TIMEFRAME (DAILY):")
print(f"  Trend bias: {middle_signals.get('trend_bias')}")
print(f"  Momentum bias: {middle_signals.get('momentum_bias')}")
rsi = middle_signals.get('rsi')
print(f"  RSI: {f'{rsi:.2f}' if rsi is not None else 'None'}")
print()

print("LOWER TIMEFRAME (1m):")
print(f"  Trend bias: {lower_signals.get('trend_bias')}")
print(f"  Momentum bias: {lower_signals.get('momentum_bias')}")
print(f"  RSI: {lower_signals.get('rsi'):.2f}")
print()

print("=== DIRECTION DETERMINATION ===")
higher_trend = higher_signals.get('trend_bias')
middle_trend = middle_signals.get('trend_bias')

print(f"Higher trend: {higher_trend}")
print(f"Middle trend: {middle_trend}")
print(f"Agreement: {higher_trend == middle_trend}")

if higher_trend == 'bullish' and middle_trend == 'bullish':
    print("Direction: LONG ✅")
elif higher_trend == 'bearish' and middle_trend == 'bearish':
    print("Direction: SHORT ✅")
else:
    print("Direction: NONE (trends don't agree)")
