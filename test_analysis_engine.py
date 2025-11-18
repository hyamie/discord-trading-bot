#!/usr/bin/env python3
"""Test the analysis engine with live Schwab data"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.schwab_api import SchwabAPIClient
from agents.analysis_engine import AnalysisEngine

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

# Run analysis
print("Running analysis engine...")
engine = AnalysisEngine()
result = engine.analyze_ticker(
    ticker='SPY',
    price_data=price_data,
    news_summary={},
    trade_type='day'
)

print(f"\n=== ANALYSIS RESULT ===")
print(f"Total plans: {result['total_plans']}")
print(f"Highest confidence: {result['highest_confidence']}")

if result['plans']:
    for i, plan in enumerate(result['plans'], 1):
        print(f"\nPlan {i}:")
        print(f"  Direction: {plan['direction']}")
        print(f"  Entry: ${plan['entry']:.2f}")
        print(f"  Stop: ${plan['stop']:.2f}")
        print(f"  Target: ${plan['target']:.2f}")
        print(f"  Confidence: {plan['confidence']}/5")
        print(f"  Edges: {', '.join(plan['edges_applied']) if plan['edges_applied'] else 'None'}")
        print(f"  Rationale: {plan['rationale']}")
else:
    print("\n[WARNING] No plans generated!")
    print("Checking what failed...")

    # Re-run analysis with more logging
    for key, df in price_data.items():
        if df is not None:
            print(f"\n{key} timeframe:")
            print(f"  Bars: {len(df)}")
            print(f"  Latest close: ${df['close'].iloc[-1]:.2f}")
        else:
            print(f"\n{key}: None")
