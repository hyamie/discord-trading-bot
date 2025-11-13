"""
Database Manager Module
Handles all database operations for the trading bot
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
from loguru import logger


class DatabaseManager:
    """Manages database operations for the trading bot"""

    def __init__(self, db_path: str):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Read schema file
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'schema.sql'
        )

        with open(schema_path, 'r') as f:
            schema = f.read()

        # Execute schema
        with self.get_connection() as conn:
            conn.executescript(schema)
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    # ========== Trade Ideas Operations ==========

    def insert_trade_idea(self, trade_data: Dict[str, Any]) -> str:
        """
        Insert a new trade idea

        Args:
            trade_data: Dictionary containing trade information

        Returns:
            trade_id: The ID of the inserted trade
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO trade_ideas (
                    id, ticker, trade_type, direction, entry, stop, target,
                    target2, confidence, rationale, edges_applied, risk_notes,
                    spy_bias, atr_value, market_volatility,
                    session_id, discord_user_id, discord_message_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['id'],
                trade_data['ticker'],
                trade_data['trade_type'],
                trade_data['direction'],
                trade_data['entry'],
                trade_data['stop'],
                trade_data['target'],
                trade_data.get('target2'),
                trade_data['confidence'],
                trade_data.get('rationale'),
                json.dumps(trade_data.get('edges_applied', [])),
                trade_data.get('risk_notes'),
                trade_data.get('spy_bias'),
                trade_data.get('atr_value'),
                trade_data.get('market_volatility'),
                trade_data.get('session_id'),
                trade_data.get('discord_user_id'),
                trade_data.get('discord_message_id')
            ))

            logger.info(f"Inserted trade idea: {trade_data['id']}")
            return trade_data['id']

    def update_trade_status(self, trade_id: str, status: str):
        """Update the status of a trade"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE trade_ideas
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, trade_id))
            logger.info(f"Updated trade {trade_id} status to {status}")

    def get_trade_idea(self, trade_id: str) -> Optional[Dict]:
        """Get a trade idea by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM trade_ideas WHERE id = ?",
                (trade_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_pending_trades(self) -> List[Dict]:
        """Get all pending trades"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM trade_ideas WHERE status = 'pending' ORDER BY timestamp DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    # ========== Outcomes Operations ==========

    def insert_outcome(self, outcome_data: Dict[str, Any]) -> int:
        """
        Insert a trade outcome

        Args:
            outcome_data: Dictionary containing outcome information

        Returns:
            outcome_id: The ID of the inserted outcome
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO outcomes (
                    trade_id, actual_outcome, profit_loss_pct, profit_loss_r,
                    close_price, close_timestamp, exit_reason, notes,
                    hold_duration_minutes, slippage_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome_data['trade_id'],
                outcome_data['actual_outcome'],
                outcome_data.get('profit_loss_pct'),
                outcome_data.get('profit_loss_r'),
                outcome_data.get('close_price'),
                outcome_data.get('close_timestamp'),
                outcome_data.get('exit_reason'),
                outcome_data.get('notes'),
                outcome_data.get('hold_duration_minutes'),
                outcome_data.get('slippage_pct')
            ))

            # Update trade status to closed
            self.update_trade_status(outcome_data['trade_id'], 'closed')

            logger.info(f"Inserted outcome for trade: {outcome_data['trade_id']}")
            return cursor.lastrowid

    def get_outcomes_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get all outcomes within a date range"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT o.*, t.ticker, t.trade_type, t.direction, t.confidence,
                       t.edges_applied, t.rationale
                FROM outcomes o
                JOIN trade_ideas t ON o.trade_id = t.id
                WHERE o.close_timestamp BETWEEN ? AND ?
                ORDER BY o.close_timestamp DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]

    # ========== Modifications Operations ==========

    def insert_modification(self, modification_data: Dict[str, Any]) -> int:
        """Insert a weekly modification record"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO modifications (
                    week, start_date, end_date, metrics, suggested_changes,
                    patterns_identified, strengths, weaknesses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                modification_data['week'],
                modification_data['start_date'],
                modification_data['end_date'],
                json.dumps(modification_data['metrics']),
                json.dumps(modification_data['suggested_changes']),
                modification_data.get('patterns_identified'),
                modification_data.get('strengths'),
                modification_data.get('weaknesses')
            ))

            logger.info(f"Inserted modification for week: {modification_data['week']}")
            return cursor.lastrowid

    # ========== Cache Operations ==========

    def get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get cached market data if not expired"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT data FROM market_data_cache
                WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
            """, (cache_key,))
            row = cursor.fetchone()

            if row:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(row['data'])

            logger.debug(f"Cache miss: {cache_key}")
            return None

    def set_cached_data(
        self,
        cache_key: str,
        ticker: str,
        timeframe: str,
        data: Dict,
        ttl_seconds: int = 60
    ):
        """Store data in cache"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_data_cache
                (cache_key, ticker, timeframe, data, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, ticker, timeframe, json.dumps(data), expires_at))

            logger.debug(f"Cached data: {cache_key} (expires in {ttl_seconds}s)")

    def clear_expired_cache(self):
        """Remove expired cache entries"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM market_data_cache
                WHERE expires_at <= CURRENT_TIMESTAMP
            """)
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"Cleared {deleted} expired cache entries")

    # ========== API Logging ==========

    def log_api_call(self, api_data: Dict[str, Any]):
        """Log an API call"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO api_calls (
                    api_name, endpoint, ticker, status_code, success,
                    error_message, response_time_ms, rate_limit_remaining
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                api_data['api_name'],
                api_data.get('endpoint'),
                api_data.get('ticker'),
                api_data.get('status_code'),
                api_data.get('success', True),
                api_data.get('error_message'),
                api_data.get('response_time_ms'),
                api_data.get('rate_limit_remaining')
            ))

    # ========== System Events ==========

    def log_system_event(
        self,
        event_type: str,
        message: str,
        component: str = None,
        details: Dict = None,
        severity: str = 'info'
    ):
        """Log a system event"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_events (
                    event_type, component, message, details, severity
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                event_type,
                component,
                message,
                json.dumps(details) if details else None,
                severity
            ))

    # ========== Analytics ==========

    def get_performance_metrics(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a date range"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        with self.get_connection() as conn:
            # Get outcomes in range
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN actual_outcome = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN actual_outcome = 'loss' THEN 1 ELSE 0 END) as losses,
                    AVG(profit_loss_r) as avg_r,
                    MAX(profit_loss_r) as max_r,
                    MIN(profit_loss_r) as min_r
                FROM outcomes
                WHERE close_timestamp BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))

            row = cursor.fetchone()

            total = row['total_trades'] or 0
            wins = row['wins'] or 0
            losses = row['losses'] or 0

            return {
                'total_trades': total,
                'wins': wins,
                'losses': losses,
                'win_rate': round(wins / total * 100, 2) if total > 0 else 0,
                'avg_r_multiple': round(row['avg_r'], 2) if row['avg_r'] else 0,
                'max_r_multiple': round(row['max_r'], 2) if row['max_r'] else 0,
                'min_r_multiple': round(row['min_r'], 2) if row['min_r'] else 0,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
