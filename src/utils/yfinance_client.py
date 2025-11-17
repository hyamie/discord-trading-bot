"""
YFinance Data Client
Fallback data source when Schwab API is unavailable
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger


class YFinanceClient:
    """Client for fetching market data using yfinance"""

    def __init__(self):
        """Initialize yfinance client"""
        logger.info("✅ YFinance client initialized (free data source)")

    def get_price_history(
        self,
        ticker: str,
        period: str = "5d",
        interval: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch price history for a ticker

        Args:
            ticker: Stock ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"📊 Fetching {ticker} data: period={period}, interval={interval}")

            # Create ticker with timeout and headers to avoid rate limiting
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval, timeout=30)

            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return None

            # Standardize column names to match Schwab format
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in {ticker} data")
                return None

            logger.info(f"✅ Got {len(df)} bars for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {ticker} from yfinance: {str(e)}")
            return None

    def get_multiple_timeframes(
        self,
        ticker: str,
        configs: list
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch multiple timeframes for a ticker

        Args:
            ticker: Stock ticker symbol
            configs: List of config dicts with 'period' and 'interval'

        Returns:
            Dictionary with timeframe DataFrames
        """
        result = {}

        # Map config to yfinance parameters
        timeframe_map = {
            0: {'key': 'higher', 'period': '1mo', 'interval': '1h'},   # Higher TF
            1: {'key': 'middle', 'period': '5d', 'interval': '15m'},   # Middle TF
            2: {'key': 'lower', 'period': '1d', 'interval': '5m'},     # Lower TF
        }

        for idx, config in enumerate(configs[:3]):  # Only process first 3 configs
            if idx not in timeframe_map:
                continue

            tf_info = timeframe_map[idx]
            df = self.get_price_history(
                ticker=ticker,
                period=tf_info['period'],
                interval=tf_info['interval']
            )

            if df is not None:
                result[tf_info['key']] = df

        return result

    def get_day_trade_data(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Get data optimized for day trading

        Timeframes:
        - Higher: 1h bars (1 month)
        - Middle: 15m bars (5 days)
        - Lower: 5m bars (1 day)

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with 'higher', 'middle', 'lower' DataFrames
        """
        result = {}

        # Higher timeframe: 1h
        df_1h = self.get_price_history(ticker, period="1mo", interval="1h")
        if df_1h is not None:
            result['higher'] = df_1h

        # Middle timeframe: 15m
        df_15m = self.get_price_history(ticker, period="5d", interval="15m")
        if df_15m is not None:
            result['middle'] = df_15m

        # Lower timeframe: 5m
        df_5m = self.get_price_history(ticker, period="1d", interval="5m")
        if df_5m is not None:
            result['lower'] = df_5m

        return result

    def get_swing_trade_data(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Get data optimized for swing trading

        Timeframes:
        - Higher: Weekly bars (1 year)
        - Middle: Daily bars (6 months)
        - Lower: 4h bars (3 months)

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with 'higher', 'middle', 'lower' DataFrames
        """
        result = {}

        # Higher timeframe: Weekly
        df_weekly = self.get_price_history(ticker, period="1y", interval="1wk")
        if df_weekly is not None:
            result['higher'] = df_weekly

        # Middle timeframe: Daily
        df_daily = self.get_price_history(ticker, period="6mo", interval="1d")
        if df_daily is not None:
            result['middle'] = df_daily

        # Lower timeframe: 4h (using 1h as 4h not available)
        df_4h = self.get_price_history(ticker, period="3mo", interval="1h")
        if df_4h is not None:
            result['lower'] = df_4h

        return result


def get_yfinance_client() -> YFinanceClient:
    """
    Factory function to get YFinance client

    Returns:
        YFinanceClient instance
    """
    return YFinanceClient()
