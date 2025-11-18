#!/usr/bin/env python3
"""Detailed test to see why analysis returns no plans"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.schwab_api import SchwabAPIClient
from utils.indicators import TechnicalIndicators

load_dotenv()

# Initialize Schwab client
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

# Fetch price data
now = datetime.now()
day_configs = [
    {'name': 'higher', 'frequency_type': 'minute', 'frequency': 30, 'start_datetime': now - timedelta(days=5)},
    {'name': 'middle', 'frequency_type': 'minute', 'frequency': 15, 'start_datetime': now - timedelta(days=3)},
    {'name': 'lower', 'frequency_type': 'minute', 'frequency': 5, 'start_datetime': now - timedelta(days=1)},
]

print("Fetching SPY data...")
price_data = client.get_multiple_timeframes('SPY', day_configs)

if not price_data:
    print("[ERROR] No price data")
    sys.exit(1)

print(f"[SUCCESS] Got {len(price_data)} timeframes\n")

# Calculate indicators
indicators = TechnicalIndicators()

higher_tf = indicators.calculate_all_indicators(price_data['higher'])
middle_tf = indicators.calculate_all_indicators(price_data['middle'])
lower_tf = indicators.calculate_all_indicators(price_data['lower'])

# Get signals
higher_signals = indicators.get_signal_summary(higher_tf, "30m")
middle_signals = indicators.get_signal_summary(middle_tf, "15m")
lower_signals = indicators.get_signal_summary(lower_tf, "5m")

print("=== SIGNAL ANALYSIS ===\n")

print("HIGHER TIMEFRAME (30m):")
print(f"  Trend bias: {higher_signals.get('trend_bias')}")
print(f"  Momentum bias: {higher_signals.get('momentum_bias')}")
print(f"  RSI: {higher_signals.get('rsi'):.2f}")
print(f"  EMA20 slope: {higher_signals.get('ema20_slope'):.3f}%")
print(f"  MACD signal: {higher_signals.get('macd_signal')}")
print()

print("MIDDLE TIMEFRAME (15m):")
print(f"  Trend bias: {middle_signals.get('trend_bias')}")
print(f"  Momentum bias: {middle_signals.get('momentum_bias')}")
rsi = middle_signals.get('rsi')
print(f"  RSI: {f'{rsi:.2f}' if rsi is not None else 'None'}")
print(f"  Price vs VWAP: {middle_signals.get('price_vs_vwap')}")
print(f"  MACD signal: {middle_signals.get('macd_signal')}")
print()

print("LOWER TIMEFRAME (5m):")
print(f"  Trend bias: {lower_signals.get('trend_bias')}")
print(f"  Momentum bias: {lower_signals.get('momentum_bias')}")
print(f"  RSI: {lower_signals.get('rsi'):.2f}")
print(f"  Long trigger: {lower_signals.get('long_trigger')}")
print(f"  Short trigger: {lower_signals.get('short_trigger')}")
print()

print("=== DIRECTION DETERMINATION ===")
higher_trend = higher_signals.get('trend_bias')
middle_trend = middle_signals.get('trend_bias')

print(f"Higher trend: {higher_trend}")
print(f"Middle trend: {middle_trend}")
print(f"Agreement: {higher_trend == middle_trend}")

if higher_trend == 'bullish' and middle_trend == 'bullish':
    print("Direction: LONG")
elif higher_trend == 'bearish' and middle_trend == 'bearish':
    print("Direction: SHORT")
else:
    print("Direction: NONE (trends don't agree)")
    print("\nThis is why no trade plan was generated!")
