#!/usr/bin/env python
"""Quick test of yfinance client"""

from src.utils.yfinance_client import YFinanceClient

client = YFinanceClient()
print('Testing AAPL day trade data...')
data = client.get_day_trade_data('AAPL')

print(f'Got {len(data)} timeframes')
for k, v in data.items():
    if v is not None and hasattr(v, '__len__'):
        print(f'{k}: {len(v)} bars')
    else:
        print(f'{k}: {v}')

print('\nSample of latest data:')
if 'higher' in data and data['higher'] is not None:
    print(data['higher'].tail())
