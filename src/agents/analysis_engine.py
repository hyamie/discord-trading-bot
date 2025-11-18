"""
Analysis Engine
Implements the 3-Tier Multi-Timeframe (MTF) trading logic with confidence scoring
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger

from src.utils.indicators import TechnicalIndicators
from src.utils.llm_client import get_llm_client


class AnalysisEngine:
    """
    Core trading analysis engine implementing 3-Tier MTF framework
    """

    def __init__(self):
        """Initialize analysis engine"""
        self.indicators = TechnicalIndicators()
        self.llm_client = get_llm_client()

        if self.llm_client:
            logger.info("✅ LLM client integrated for rationale generation")
        else:
            logger.warning("⚠️  LLM client unavailable - using template rationales")

    def analyze_ticker(
        self,
        ticker: str,
        price_data: Dict[str, pd.DataFrame],
        news_summary: Dict,
        trade_type: str = 'both'  # 'day', 'swing', or 'both'
    ) -> Dict[str, any]:
        """
        Complete analysis for a ticker

        Args:
            ticker: Stock ticker symbol
            price_data: Dictionary with timeframe data
                For day trading: {'higher': df_1h, 'middle': df_15m, 'lower': df_5m, 'spy': df_spy}
                For swing trading: {'higher': df_weekly, 'middle': df_daily, 'lower': df_4h, 'spy': df_spy}
            news_summary: News data from NewsAggregator
            trade_type: 'day', 'swing', or 'both'

        Returns:
            Dictionary with trade plans, signals, and rankings
        """
        logger.info(f"Analyzing {ticker} for {trade_type} trade(s)")

        plans = []

        # Day trade analysis
        if trade_type in ['day', 'both']:
            day_plan = self._analyze_day_trade(ticker, price_data, news_summary)
            if day_plan:
                plans.append(day_plan)

        # Swing trade analysis
        if trade_type in ['swing', 'both']:
            swing_plan = self._analyze_swing_trade(ticker, price_data, news_summary)
            if swing_plan:
                plans.append(swing_plan)

        # Rank plans by confidence
        plans.sort(key=lambda x: x['confidence'], reverse=True)

        return {
            'ticker': ticker,
            'plans': plans,
            'total_plans': len(plans),
            'highest_confidence': plans[0]['confidence'] if plans else 0,
            'analysis_timestamp': datetime.now().isoformat()
        }

    def _analyze_day_trade(
        self,
        ticker: str,
        price_data: Dict[str, pd.DataFrame],
        news_summary: Dict
    ) -> Optional[Dict]:
        """
        Analyze for day trade setup

        Timeframes:
        - Higher: 1h (macro trend)
        - Middle: 15m (confirmation)
        - Lower: 5m (entry trigger)
        """
        # Get required timeframes
        higher_tf = price_data.get('higher')  # 1h
        middle_tf = price_data.get('middle')  # 15m
        lower_tf = price_data.get('lower')   # 5m
        spy_data = price_data.get('spy')

        if higher_tf is None or middle_tf is None or lower_tf is None:
            logger.warning(f"Missing timeframe data for {ticker} day trade")
            return None

        # Calculate indicators for all timeframes
        higher_tf = self.indicators.calculate_all_indicators(higher_tf)
        middle_tf = self.indicators.calculate_all_indicators(middle_tf)
        lower_tf = self.indicators.calculate_all_indicators(lower_tf)

        # Get signal summaries
        higher_signals = self.indicators.get_signal_summary(higher_tf, "1h")
        middle_signals = self.indicators.get_signal_summary(middle_tf, "15m")
        lower_signals = self.indicators.get_signal_summary(lower_tf, "5m")

        # Determine direction (long or short)
        direction = self._determine_direction(higher_signals, middle_signals)

        if not direction:
            logger.debug(f"No clear direction for {ticker} day trade")
            return None

        # Calculate entry, stop, target
        entry_data = self._calculate_entry_levels(
            lower_tf,
            direction,
            lower_signals
        )

        # Apply refinement edges
        edges_applied = self._apply_edges(
            higher_signals,
            middle_signals,
            lower_signals,
            lower_tf,
            direction
        )

        # Calculate base confidence (0-3)
        confidence = self._calculate_base_confidence(
            higher_signals,
            middle_signals,
            lower_signals,
            direction
        )

        # Add edge bonuses
        confidence += min(len(edges_applied), 2)  # Max +2 from edges

        # Add news sentiment bonus/penalty
        news_adjustment = self._apply_news_sentiment(
            news_summary,
            direction
        )
        confidence += news_adjustment

        # Cap at 5
        confidence = min(confidence, 5)

        # Generate rationale
        rationale = self._generate_rationale(
            ticker,
            direction,
            higher_signals,
            middle_signals,
            lower_signals,
            edges_applied,
            news_summary,
            'day'
        )

        # Risk notes
        risk_notes = self._generate_risk_notes(
            entry_data,
            spy_data,
            higher_signals,
            'day'
        )

        return {
            'trade_type': 'day',
            'direction': direction,
            'entry': entry_data['entry'],
            'stop': entry_data['stop'],
            'target': entry_data['target'],
            'target2': entry_data.get('target2'),
            'risk_reward': entry_data['risk_reward'],
            'confidence': confidence,
            'edges_applied': edges_applied,
            'rationale': rationale,
            'risk_notes': risk_notes,
            'atr_value': lower_signals.get('atr'),
            'timeframes': {
                'higher': higher_signals,
                'middle': middle_signals,
                'lower': lower_signals
            }
        }

    def _analyze_swing_trade(
        self,
        ticker: str,
        price_data: Dict[str, pd.DataFrame],
        news_summary: Dict
    ) -> Optional[Dict]:
        """
        Analyze for swing trade setup

        Timeframes:
        - Higher: Weekly (macro trend)
        - Middle: Daily (confirmation)
        - Lower: 4h (entry trigger)
        """
        # Similar logic to day trade but with different timeframes
        higher_tf = price_data.get('higher_swing')  # Weekly
        middle_tf = price_data.get('middle_swing')  # Daily
        lower_tf = price_data.get('lower_swing')    # 4h
        spy_data = price_data.get('spy_swing')

        if higher_tf is None or middle_tf is None or lower_tf is None:
            logger.warning(f"Missing timeframe data for {ticker} swing trade")
            return None

        # Calculate indicators
        higher_tf = self.indicators.calculate_all_indicators(higher_tf, include_vwap=False)
        middle_tf = self.indicators.calculate_all_indicators(middle_tf, include_vwap=False)
        lower_tf = self.indicators.calculate_all_indicators(lower_tf, include_vwap=False)

        # Get signals
        higher_signals = self.indicators.get_signal_summary(higher_tf, "weekly")
        middle_signals = self.indicators.get_signal_summary(middle_tf, "daily")
        lower_signals = self.indicators.get_signal_summary(lower_tf, "4h")

        # Determine direction
        direction = self._determine_direction(higher_signals, middle_signals)

        if not direction:
            return None

        # Calculate levels
        entry_data = self._calculate_entry_levels(
            lower_tf,
            direction,
            lower_signals
        )

        # Apply edges
        edges_applied = self._apply_edges(
            higher_signals,
            middle_signals,
            lower_signals,
            lower_tf,
            direction,
            trade_type='swing'
        )

        # Calculate confidence
        confidence = self._calculate_base_confidence(
            higher_signals,
            middle_signals,
            lower_signals,
            direction
        )
        confidence += min(len(edges_applied), 2)
        confidence += self._apply_news_sentiment(news_summary, direction)
        confidence = min(confidence, 5)

        # Generate rationale and risk notes
        rationale = self._generate_rationale(
            ticker,
            direction,
            higher_signals,
            middle_signals,
            lower_signals,
            edges_applied,
            news_summary,
            'swing'
        )

        risk_notes = self._generate_risk_notes(
            entry_data,
            spy_data,
            higher_signals,
            'swing'
        )

        return {
            'trade_type': 'swing',
            'direction': direction,
            'entry': entry_data['entry'],
            'stop': entry_data['stop'],
            'target': entry_data['target'],
            'target2': entry_data.get('target2'),
            'risk_reward': entry_data['risk_reward'],
            'confidence': confidence,
            'edges_applied': edges_applied,
            'rationale': rationale,
            'risk_notes': risk_notes,
            'atr_value': lower_signals.get('atr'),
            'timeframes': {
                'higher': higher_signals,
                'middle': middle_signals,
                'lower': lower_signals
            }
        }

    def _determine_direction(
        self,
        higher_signals: Dict,
        middle_signals: Dict
    ) -> Optional[str]:
        """
        Determine trade direction based on trend and momentum alignment

        Returns:
            'long', 'short', or None
        """
        higher_trend = higher_signals.get('trend_bias')
        middle_trend = middle_signals.get('trend_bias')

        # Both must agree
        if higher_trend == 'bullish' and middle_trend == 'bullish':
            return 'long'
        elif higher_trend == 'bearish' and middle_trend == 'bearish':
            return 'short'

        return None

    def _calculate_entry_levels(
        self,
        lower_tf: pd.DataFrame,
        direction: str,
        lower_signals: Dict
    ) -> Dict:
        """
        Calculate entry, stop, and target levels

        Args:
            lower_tf: Lower timeframe DataFrame (with indicators)
            direction: 'long' or 'short'
            lower_signals: Signal summary for lower TF

        Returns:
            Dictionary with entry, stop, target levels
        """
        latest = lower_tf.iloc[-1]
        entry = float(latest['close'])
        atr = float(latest['ATR14'])

        # Calculate stop (1 ATR away)
        if direction == 'long':
            stop = entry - atr
        else:  # short
            stop = entry + atr

        # Calculate 1R
        r = abs(entry - stop)

        # Default target is 2R
        if direction == 'long':
            target = entry + (2 * r)
            target2 = entry + r  # 1R target
        else:
            target = entry - (2 * r)
            target2 = entry - r

        risk_reward = 2.0

        return {
            'entry': round(entry, 2),
            'stop': round(stop, 2),
            'target': round(target, 2),
            'target2': round(target2, 2),
            'risk_reward': risk_reward,
            'atr': round(atr, 2),
            'r_value': round(r, 2)
        }

    def _apply_edges(
        self,
        higher_signals: Dict,
        middle_signals: Dict,
        lower_signals: Dict,
        lower_tf: pd.DataFrame,
        direction: str,
        trade_type: str = 'day'
    ) -> List[str]:
        """
        Apply refinement edges and return list of met edges

        Edges:
        1. Slope Filter (EMA20 slope > 0.1%)
        2. Pullback Confirmation (Price vs VWAP + RSI range)
        3. Volatility Filter (Candle range > 1.25 * ATR)
        4. Volume Confirmation (Volume > 1.5x average)
        5. Divergence Filter

        Args:
            higher_signals: Higher TF signals
            middle_signals: Middle TF signals
            lower_signals: Lower TF signals
            lower_tf: Lower timeframe DataFrame
            direction: Trade direction
            trade_type: 'day' or 'swing'

        Returns:
            List of edge names that were met
        """
        edges = []

        # 1. Slope Filter (Higher TF)
        ema20_slope = higher_signals.get('ema20_slope', 0)
        if direction == 'long' and ema20_slope > 0.1:
            edges.append('Slope Filter (EMA20 rising strongly)')
        elif direction == 'short' and ema20_slope < -0.1:
            edges.append('Slope Filter (EMA20 falling strongly)')

        # 2. Pullback Confirmation (Middle TF) - only for day trades with VWAP
        if trade_type == 'day':
            rsi = middle_signals.get('rsi')
            price_vs_vwap = middle_signals.get('price_vs_vwap')

            if direction == 'long' and price_vs_vwap == 'above' and 45 < rsi < 65:
                edges.append('Pullback Confirmation (Above VWAP, RSI reset)')
            elif direction == 'short' and price_vs_vwap == 'below' and 35 < rsi < 55:
                edges.append('Pullback Confirmation (Below VWAP, RSI reset)')

        # 3. Volatility/Conviction Filter (Lower TF)
        latest = lower_tf.iloc[-1]
        candle_range = float(latest['high'] - latest['low'])
        atr = float(latest['ATR14'])

        if candle_range > 1.25 * atr:
            edges.append('Volatility Filter (Strong breakout candle)')

        # 4. Volume Confirmation (Lower TF)
        if 'volume' in lower_tf.columns:
            current_volume = float(latest['volume'])
            avg_volume = float(lower_tf['volume'].tail(10).mean())

            if current_volume > 1.5 * avg_volume:
                edges.append('Volume Confirmation (1.5x average)')

        # 5. Divergence Filter
        divergence = self.indicators.detect_divergence(
            lower_tf['close'],
            lower_tf['RSI14'],
            lookback=20
        )

        if divergence:
            if (divergence == 'bullish' and direction == 'long') or \
               (divergence == 'bearish' and direction == 'short'):
                edges.append(f'{divergence.capitalize()} Divergence')

        return edges

    def _calculate_base_confidence(
        self,
        higher_signals: Dict,
        middle_signals: Dict,
        lower_signals: Dict,
        direction: str
    ) -> int:
        """
        Calculate base confidence score (0-3)

        +1 for trend alignment
        +1 for momentum alignment
        +1 for entry trigger

        Args:
            higher_signals: Higher TF signals
            middle_signals: Middle TF signals
            lower_signals: Lower TF signals
            direction: Trade direction

        Returns:
            Base confidence score (0-3)
        """
        score = 0

        # +1 for trend alignment (already checked, so always +1 if we got here)
        if higher_signals.get('trend_bias') == middle_signals.get('trend_bias'):
            score += 1

        # +1 for momentum alignment
        expected_momentum = 'bullish' if direction == 'long' else 'bearish'
        if middle_signals.get('momentum_bias') == expected_momentum:
            score += 1

        # +1 for entry trigger on lower TF
        if direction == 'long' and lower_signals.get('long_trigger'):
            score += 1
        elif direction == 'short' and lower_signals.get('short_trigger'):
            score += 1

        return score

    def _apply_news_sentiment(
        self,
        news_summary: Dict,
        direction: str
    ) -> int:
        """
        Apply news sentiment adjustment to confidence

        Returns:
            +1 if news aligns, -1 if conflicts, 0 if neutral
        """
        if not news_summary or 'sentiment_summary' not in news_summary:
            return 0

        sentiment = news_summary['sentiment_summary'].get('overall', 'neutral')

        if direction == 'long' and sentiment == 'positive':
            return 1
        elif direction == 'short' and sentiment == 'negative':
            return 1
        elif (direction == 'long' and sentiment == 'negative') or \
             (direction == 'short' and sentiment == 'positive'):
            return -1

        return 0

    def _generate_rationale(
        self,
        ticker: str,
        direction: str,
        higher_signals: Dict,
        middle_signals: Dict,
        lower_signals: Dict,
        edges_applied: List[str],
        news_summary: Dict,
        trade_type: str
    ) -> str:
        """
        Generate human-readable rationale for the trade using LLM (or fallback template)

        Returns:
            2-3 sentence rationale
        """
        # Prepare signals dictionary for LLM
        signals = {
            'higher': higher_signals,
            'middle': middle_signals,
            'lower': lower_signals
        }

        # Prepare edges list for LLM
        edges = [{'name': edge, 'applied': True} for edge in edges_applied]

        # Try LLM generation first
        if self.llm_client:
            try:
                return self.llm_client.generate_trade_rationale(
                    ticker=ticker,
                    trade_type=trade_type,
                    direction=direction,
                    signals=signals,
                    edges=edges,
                    news_summary=news_summary
                )
            except Exception as e:
                logger.warning(f"LLM rationale generation failed, using template: {str(e)}")

        # Fallback to template-based rationale
        # Trend description
        trend_desc = (
            f"{direction.capitalize()} setup with "
            f"{higher_signals['timeframe']} {higher_signals['trend_bias']} trend "
            f"confirmed by {middle_signals['timeframe']} momentum"
        )

        # Edges description
        if edges_applied:
            edges_desc = f"Strong conviction with {len(edges_applied)} edge(s): {', '.join(edges_applied[:2])}"
        else:
            edges_desc = "Basic setup without additional edge confirmation"

        # News impact
        sentiment = news_summary.get('sentiment_summary', {}).get('overall', 'neutral')
        if sentiment != 'neutral':
            news_desc = f"News sentiment is {sentiment}, {'' if (direction == 'long' and sentiment == 'positive') or (direction == 'short' and sentiment == 'negative') else 'conflicting with'} the trade direction"
        else:
            news_desc = "News sentiment neutral"

        return f"{trend_desc}. {edges_desc}. {news_desc}."

    def _generate_risk_notes(
        self,
        entry_data: Dict,
        spy_data: Optional[pd.DataFrame],
        higher_signals: Dict,
        trade_type: str
    ) -> str:
        """
        Generate risk management notes

        Returns:
            Risk management guidance string
        """
        notes = []

        # R:R note
        rr = entry_data['risk_reward']
        notes.append(f"Risk {rr}R (Entry to stop = ${entry_data['r_value']:.2f})")

        # Position sizing
        notes.append("Risk 1-2% of capital per trade")

        # ATR context
        atr = entry_data['atr']
        notes.append(f"ATR: ${atr:.2f} (volatility measure)")

        # SPY bias check
        if spy_data is not None and len(spy_data) > 0:
            # Quick check if SPY contradicts
            notes.append("Monitor SPY for market context")

        # Time filter for day trades
        if trade_type == 'day':
            notes.append("Avoid 11:30 AM - 1:30 PM EST low-volume window")

        return "; ".join(notes)
