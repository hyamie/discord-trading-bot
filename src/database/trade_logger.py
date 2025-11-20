"""
Trade Logger Module
Logs all trade signals to the trade_signals table for Phase II tracking
"""

import os
import asyncpg
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from dotenv import load_dotenv

# Load environment
load_dotenv()


class TradeLogger:
    """
    Handles logging trade signals to the database for performance tracking
    """

    def __init__(self, database_url: Optional[str] = None, schema: str = "discord_trading"):
        """
        Initialize Trade Logger

        Args:
            database_url: PostgreSQL connection string (defaults to env var)
            schema: Database schema (default: discord_trading)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.schema = schema
        self.pool = None

        if not self.database_url:
            logger.warning("DATABASE_URL not found - trade logging disabled")

    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection from pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)

        conn = await self.pool.acquire()
        # Set search path to use correct schema
        await conn.execute(f"SET search_path TO {self.schema}, public")
        return conn

    async def log_trade_signal(
        self,
        trade_id: str,
        ticker: str,
        trade_type: str,
        direction: str,
        entry: float,
        stop: float,
        target: float,
        confidence: int,
        edges: List[Dict],
        rationale: str,
        **kwargs
    ) -> bool:
        """
        Log a trade signal to the database

        Args:
            trade_id: Unique trade ID (e.g., AAPL-20251120-001)
            ticker: Stock ticker symbol
            trade_type: 'day' or 'swing'
            direction: 'long' or 'short'
            entry: Entry price
            stop: Stop loss price
            target: Target profit price
            confidence: Confidence score (0-5)
            edges: List of edge dictionaries
            rationale: Trade rationale text
            **kwargs: Additional optional fields (target2, atr_value, spy_bias, etc.)

        Returns:
            True if logged successfully, False otherwise
        """
        if not self.database_url:
            logger.debug("Trade logging skipped (no DATABASE_URL)")
            return False

        try:
            conn = await self.get_connection()

            try:
                # Prepare edges JSON (ensure it's a list of dicts)
                import json
                edges_json = json.dumps(edges) if edges else None

                # Calculate edges count
                edges_count = len([e for e in edges if e.get('applied', True)]) if edges else 0

                # Insert trade signal
                query = """
                    INSERT INTO trade_signals (
                        trade_id, ticker, trade_type, direction,
                        entry, stop, target, target2,
                        confidence, edges, edges_count, rationale,
                        timeframe_signals, atr_value, market_volatility, spy_bias,
                        news_summary, sent_to_discord
                    ) VALUES (
                        $1, $2, $3, $4,
                        $5, $6, $7, $8,
                        $9, $10, $11, $12,
                        $13, $14, $15, $16,
                        $17, $18
                    )
                    RETURNING id;
                """

                # Extract optional fields with defaults
                target2 = kwargs.get('target2')
                timeframe_signals = json.dumps(kwargs.get('timeframe_signals')) if kwargs.get('timeframe_signals') else None
                atr_value = kwargs.get('atr_value')
                market_volatility = kwargs.get('market_volatility')
                spy_bias = kwargs.get('spy_bias')
                news_summary = json.dumps(kwargs.get('news_summary')) if kwargs.get('news_summary') else None
                sent_to_discord = kwargs.get('sent_to_discord', True)

                result = await conn.fetchval(
                    query,
                    trade_id, ticker, trade_type, direction,
                    entry, stop, target, target2,
                    confidence, edges_json, edges_count, rationale,
                    timeframe_signals, atr_value, market_volatility, spy_bias,
                    news_summary, sent_to_discord
                )

                logger.info(f"Trade signal logged: {trade_id} ({ticker}) - Confidence {confidence}")
                return True

            finally:
                await self.pool.release(conn)

        except Exception as e:
            logger.error(f"Failed to log trade signal {trade_id}: {str(e)}")
            return False

    async def log_multiple_signals(self, signals: List[Dict]) -> int:
        """
        Log multiple trade signals at once

        Args:
            signals: List of signal dictionaries

        Returns:
            Number of signals logged successfully
        """
        success_count = 0

        for signal in signals:
            # Extract required fields
            trade_id = signal.get('trade_id')
            ticker = signal.get('ticker')
            trade_type = signal.get('trade_type')
            direction = signal.get('direction')
            entry = signal.get('entry')
            stop = signal.get('stop')
            target = signal.get('target')
            confidence = signal.get('confidence')
            edges = signal.get('edges_applied', [])
            rationale = signal.get('rationale', '')

            # Remove these from signal dict to pass as kwargs
            kwargs = {k: v for k, v in signal.items() if k not in [
                'trade_id', 'ticker', 'trade_type', 'direction',
                'entry', 'stop', 'target', 'confidence', 'edges_applied', 'rationale'
            ]}

            # Log signal
            success = await self.log_trade_signal(
                trade_id=trade_id,
                ticker=ticker,
                trade_type=trade_type,
                direction=direction,
                entry=entry,
                stop=stop,
                target=target,
                confidence=confidence,
                edges=edges,
                rationale=rationale,
                **kwargs
            )

            if success:
                success_count += 1

        logger.info(f"Logged {success_count}/{len(signals)} trade signals")
        return success_count

    async def update_trade_outcome(
        self,
        trade_id: str,
        status: str,
        r_achieved: Optional[float] = None,
        exit_price: Optional[float] = None,
        exit_reason: Optional[str] = None
    ) -> bool:
        """
        Update a trade signal with its outcome

        Args:
            trade_id: Trade ID to update
            status: New status ('WIN', 'LOSS', 'EXPIRED', 'CANCELLED')
            r_achieved: Actual R-multiple achieved
            exit_price: Price at exit (optional, for records)
            exit_reason: Reason for exit (optional)

        Returns:
            True if updated successfully
        """
        if not self.database_url:
            return False

        try:
            conn = await self.get_connection()

            try:
                # Determine triggered_at and closed_at
                now = datetime.utcnow()

                query = """
                    UPDATE trade_signals
                    SET status = $1,
                        r_achieved = $2,
                        triggered_at = COALESCE(triggered_at, $3),
                        closed_at = $4,
                        user_notes = COALESCE(user_notes, '') || $5
                    WHERE trade_id = $6
                    RETURNING id;
                """

                notes_addition = f"\n[Exit: {exit_reason} @ {exit_price}]" if exit_reason else ""

                result = await conn.fetchval(
                    query,
                    status, r_achieved, now, now, notes_addition, trade_id
                )

                if result:
                    logger.info(f"Trade outcome updated: {trade_id} -> {status} ({r_achieved}R)")
                    return True
                else:
                    logger.warning(f"Trade not found for outcome update: {trade_id}")
                    return False

            finally:
                await self.pool.release(conn)

        except Exception as e:
            logger.error(f"Failed to update trade outcome {trade_id}: {str(e)}")
            return False

    async def get_pending_trades(self) -> List[Dict]:
        """
        Get all pending trades for outcome tracking

        Returns:
            List of pending trade dictionaries
        """
        if not self.database_url:
            return []

        try:
            conn = await self.get_connection()

            try:
                query = """
                    SELECT trade_id, ticker, trade_type, direction,
                           entry, stop, target, target2,
                           created_at, expires_at
                    FROM trade_signals
                    WHERE status = 'PENDING'
                    ORDER BY created_at DESC;
                """

                rows = await conn.fetch(query)

                # Convert to list of dicts
                trades = []
                for row in rows:
                    trades.append({
                        'trade_id': row['trade_id'],
                        'ticker': row['ticker'],
                        'trade_type': row['trade_type'],
                        'direction': row['direction'],
                        'entry': float(row['entry']),
                        'stop': float(row['stop']),
                        'target': float(row['target']),
                        'target2': float(row['target2']) if row['target2'] else None,
                        'created_at': row['created_at'],
                        'expires_at': row['expires_at']
                    })

                return trades

            finally:
                await self.pool.release(conn)

        except Exception as e:
            logger.error(f"Failed to get pending trades: {str(e)}")
            return []

    async def mark_expired_trades(self) -> int:
        """
        Mark all expired pending trades as EXPIRED

        Returns:
            Number of trades marked as expired
        """
        if not self.database_url:
            return 0

        try:
            conn = await self.get_connection()

            try:
                query = "SELECT * FROM mark_expired_trades();"
                result = await conn.fetchval(query)
                expired_count = result or 0

                if expired_count > 0:
                    logger.info(f"Marked {expired_count} trades as expired")

                return expired_count

            finally:
                await self.pool.release(conn)

        except Exception as e:
            logger.error(f"Failed to mark expired trades: {str(e)}")
            return 0

    async def get_performance_summary(self) -> Dict:
        """
        Get overall performance summary

        Returns:
            Dictionary with performance metrics
        """
        if not self.database_url:
            return {}

        try:
            conn = await self.get_connection()

            try:
                query = "SELECT * FROM v_performance_summary;"
                row = await conn.fetchrow(query)

                if row:
                    return {
                        'total_signals': row['total_signals'],
                        'total_wins': row['total_wins'],
                        'total_losses': row['total_losses'],
                        'total_pending': row['total_pending'],
                        'total_expired': row['total_expired'],
                        'win_rate_pct': float(row['win_rate_pct']) if row['win_rate_pct'] else 0,
                        'avg_r_multiple': float(row['avg_r_multiple']) if row['avg_r_multiple'] else 0,
                        'total_r_achieved': float(row['total_r_achieved']) if row['total_r_achieved'] else 0,
                        'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0,
                        'first_signal_date': row['first_signal_date'],
                        'last_signal_date': row['last_signal_date']
                    }

                return {}

            finally:
                await self.pool.release(conn)

        except Exception as e:
            logger.error(f"Failed to get performance summary: {str(e)}")
            return {}

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.debug("Trade logger connection pool closed")


# Global instance
_trade_logger = None


def get_trade_logger() -> TradeLogger:
    """Get global trade logger instance"""
    global _trade_logger
    if _trade_logger is None:
        _trade_logger = TradeLogger()
    return _trade_logger
