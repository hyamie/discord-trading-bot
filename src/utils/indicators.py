"""
Technical Indicators Module
Calculates EMA, RSI, ATR, VWAP and other indicators for trading analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""

    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average

        Args:
            prices: Series of closing prices
            period: EMA period (e.g., 20, 50)

        Returns:
            Series of EMA values
        """
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average

        Args:
            prices: Series of closing prices
            period: SMA period

        Returns:
            Series of SMA values
        """
        return prices.rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index

        Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

        Args:
            prices: Series of closing prices
            period: RSI period (default 14)

        Returns:
            Series of RSI values (0-100)
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        # Calculate average gains and losses
        avg_gains = gains.ewm(span=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range

        True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        ATR = EMA of True Range

        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            period: ATR period (default 14)

        Returns:
            Series of ATR values
        """
        # Calculate True Range components
        high_low = high - low
        high_close = (high - close.shift(1)).abs()
        low_close = (low - close.shift(1)).abs()

        # True Range is the maximum of the three
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # ATR is the EMA of True Range
        atr = true_range.ewm(span=period, adjust=False).mean()

        return atr

    @staticmethod
    def calculate_vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        reset_daily: bool = True
    ) -> pd.Series:
        """
        Calculate Volume-Weighted Average Price

        VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
        Typical Price = (High + Low + Close) / 3

        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            volume: Series of volume
            reset_daily: Whether to reset VWAP daily (for intraday data)

        Returns:
            Series of VWAP values
        """
        typical_price = (high + low + close) / 3
        pv = typical_price * volume

        if reset_daily and hasattr(close.index, 'date'):
            # Group by date for intraday data
            vwap = (pv.groupby(close.index.date).cumsum() /
                    volume.groupby(close.index.date).cumsum())
        else:
            # Simple cumulative for daily+ data
            vwap = pv.cumsum() / volume.cumsum()

        return vwap

    @staticmethod
    def calculate_slope(prices: pd.Series, periods: int = 5) -> float:
        """
        Calculate the slope of price movement over N periods

        Args:
            prices: Series of prices
            periods: Number of periods to calculate slope over

        Returns:
            Slope as percentage change
        """
        if len(prices) < periods + 1:
            return 0.0

        current = prices.iloc[-1]
        previous = prices.iloc[-(periods + 1)]

        if previous == 0:
            return 0.0

        slope = ((current - previous) / previous) * 100
        return slope

    @staticmethod
    def detect_divergence(
        prices: pd.Series,
        indicator: pd.Series,
        lookback: int = 20
    ) -> Optional[str]:
        """
        Detect bullish or bearish divergence between price and indicator

        Args:
            prices: Series of prices
            indicator: Series of indicator values (e.g., RSI)
            lookback: Number of periods to look back

        Returns:
            'bullish', 'bearish', or None
        """
        if len(prices) < lookback or len(indicator) < lookback:
            return None

        recent_prices = prices.tail(lookback)
        recent_indicator = indicator.tail(lookback)

        # Find peaks and troughs
        price_high = recent_prices.max()
        price_low = recent_prices.min()
        indicator_high = recent_indicator.max()
        indicator_low = recent_indicator.min()

        # Bearish divergence: price making higher highs, indicator making lower highs
        if (recent_prices.iloc[-1] > price_high * 0.95 and
            recent_indicator.iloc[-1] < indicator_high * 0.95):
            return 'bearish'

        # Bullish divergence: price making lower lows, indicator making higher lows
        if (recent_prices.iloc[-1] < price_low * 1.05 and
            recent_indicator.iloc[-1] > indicator_low * 1.05):
            return 'bullish'

        return None

    @staticmethod
    def check_three_bar_breakout(
        prices: pd.Series,
        direction: str = 'long'
    ) -> bool:
        """
        Check if price broke above/below the prior 3-bar high/low

        Args:
            prices: Series of prices
            direction: 'long' or 'short'

        Returns:
            True if breakout occurred
        """
        if len(prices) < 4:
            return False

        current_price = prices.iloc[-1]
        three_bar_high = prices.iloc[-4:-1].max()
        three_bar_low = prices.iloc[-4:-1].min()

        if direction == 'long':
            return current_price > three_bar_high
        else:  # short
            return current_price < three_bar_low

    @staticmethod
    def calculate_all_indicators(
        df: pd.DataFrame,
        ema_periods: List[int] = [20, 50],
        rsi_period: int = 14,
        atr_period: int = 14,
        include_vwap: bool = True
    ) -> pd.DataFrame:
        """
        Calculate all indicators for a dataframe

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            ema_periods: List of EMA periods to calculate
            rsi_period: RSI period
            atr_period: ATR period
            include_vwap: Whether to include VWAP

        Returns:
            DataFrame with all indicators added
        """
        df = df.copy()

        try:
            # Calculate EMAs
            for period in ema_periods:
                df[f'EMA{period}'] = TechnicalIndicators.calculate_ema(
                    df['close'], period
                )

            # Calculate RSI
            df[f'RSI{rsi_period}'] = TechnicalIndicators.calculate_rsi(
                df['close'], rsi_period
            )

            # Calculate ATR
            df[f'ATR{atr_period}'] = TechnicalIndicators.calculate_atr(
                df['high'], df['low'], df['close'], atr_period
            )

            # Calculate VWAP if volume is available
            if include_vwap and 'volume' in df.columns:
                df['VWAP'] = TechnicalIndicators.calculate_vwap(
                    df['high'], df['low'], df['close'], df['volume']
                )

            logger.debug(f"Calculated indicators for {len(df)} bars")
            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise

    @staticmethod
    def get_signal_summary(
        df: pd.DataFrame,
        timeframe: str = "unknown"
    ) -> Dict[str, any]:
        """
        Generate a summary of current signals based on indicators

        Args:
            df: DataFrame with calculated indicators
            timeframe: Timeframe label (e.g., "1h", "15m")

        Returns:
            Dictionary with signal information
        """
        if df.empty or len(df) < 20:
            return {
                'timeframe': timeframe,
                'valid': False,
                'reason': 'Insufficient data'
            }

        latest = df.iloc[-1]

        # Trend bias (EMA20 vs EMA50)
        if 'EMA20' in df.columns and 'EMA50' in df.columns:
            if latest['EMA20'] > latest['EMA50']:
                trend_bias = 'bullish'
            elif latest['EMA20'] < latest['EMA50']:
                trend_bias = 'bearish'
            else:
                trend_bias = 'neutral'

            # Calculate slope
            ema20_slope = TechnicalIndicators.calculate_slope(df['EMA20'], 5)
        else:
            trend_bias = 'unknown'
            ema20_slope = 0.0

        # Momentum bias (RSI)
        if 'RSI14' in df.columns:
            rsi = latest['RSI14']
            if rsi > 55:
                momentum_bias = 'bullish'
            elif rsi < 45:
                momentum_bias = 'bearish'
            else:
                momentum_bias = 'neutral'
        else:
            rsi = None
            momentum_bias = 'unknown'

        # VWAP position
        if 'VWAP' in df.columns:
            price_vs_vwap = 'above' if latest['close'] > latest['VWAP'] else 'below'
        else:
            price_vs_vwap = 'unknown'

        # Entry triggers
        long_trigger = TechnicalIndicators.check_three_bar_breakout(df['close'], 'long')
        short_trigger = TechnicalIndicators.check_three_bar_breakout(df['close'], 'short')

        return {
            'timeframe': timeframe,
            'valid': True,
            'trend_bias': trend_bias,
            'momentum_bias': momentum_bias,
            'ema20': latest.get('EMA20'),
            'ema50': latest.get('EMA50'),
            'ema20_slope': round(ema20_slope, 4),
            'rsi': round(rsi, 2) if rsi else None,
            'atr': latest.get('ATR14'),
            'vwap': latest.get('VWAP'),
            'price_vs_vwap': price_vs_vwap,
            'close': latest['close'],
            'volume': latest.get('volume'),
            'long_trigger': long_trigger,
            'short_trigger': short_trigger
        }
