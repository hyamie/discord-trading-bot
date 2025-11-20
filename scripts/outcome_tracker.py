#!/usr/bin/env python3
"""
Outcome Tracker Script
Monitors pending trades and updates their status based on current market prices

This script runs hourly to:
1. Fetch all PENDING trades from database
2. Check current price for each ticker
3. Determine if target hit, stop hit, or still pending
4. Update trade status and calculate R-multiple
5. Mark expired trades

Designed to run as a GitHub Actions cron job or Railway scheduled task
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.trade_logger import get_trade_logger
from src.utils.schwab_api import SchwabAPIClient

# Load environment
env_file = project_root / '.env.supabase'
if env_file.exists():
    load_dotenv(env_file)

# Also load main .env
main_env = project_root / '.env'
if main_env.exists():
    load_dotenv(main_env)


class OutcomeTracker:
    """Tracks trade outcomes by monitoring price movements"""

    def __init__(self):
        self.trade_logger = get_trade_logger()
        self.schwab_client = None

        # Initialize Schwab client if credentials available
        schwab_api_key = os.getenv('SCHWAB_API_KEY')
        schwab_api_secret = os.getenv('SCHWAB_API_SECRET')
        schwab_refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')

        if schwab_api_key and schwab_api_secret and schwab_refresh_token:
            self.schwab_client = SchwabAPIClient(
                api_key=schwab_api_key,
                api_secret=schwab_api_secret,
                redirect_uri=os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8080/callback')
            )
            self.schwab_client.refresh_token = schwab_refresh_token
            if self.schwab_client.authenticate():
                logger.info("Schwab API authenticated successfully")
            else:
                logger.warning("Schwab authentication failed - using fallback methods")
                self.schwab_client = None
        else:
            logger.warning("Schwab credentials not found - outcome tracking limited")

    def get_current_price(self, ticker: str) -> float:
        """
        Get current price for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Current price or None if unavailable
        """
        if self.schwab_client:
            try:
                # Use Schwab quote API
                quote = self.schwab_client.get_quote(ticker)
                if quote and 'lastPrice' in quote:
                    return float(quote['lastPrice'])
            except Exception as e:
                logger.warning(f"Schwab quote failed for {ticker}: {str(e)}")

        # Fallback: Use yfinance
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            data = stock.history(period='1d', interval='1m')
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            logger.warning(f"YFinance quote failed for {ticker}: {str(e)}")

        return None

    def calculate_r_multiple(
        self,
        direction: str,
        entry: float,
        stop: float,
        exit_price: float
    ) -> float:
        """
        Calculate R-multiple for a trade

        Args:
            direction: 'long' or 'short'
            entry: Entry price
            stop: Stop loss price
            exit_price: Exit price (current or actual)

        Returns:
            R-multiple achieved
        """
        if direction == 'long':
            risk = entry - stop
            reward = exit_price - entry
        else:  # short
            risk = stop - entry
            reward = entry - exit_price

        if risk == 0:
            return 0

        return round(reward / risk, 2)

    def check_trade_outcome(self, trade: Dict) -> Dict:
        """
        Check if a pending trade has hit target or stop

        Args:
            trade: Trade dictionary with entry/stop/target

        Returns:
            Dictionary with status update or None if still pending
        """
        ticker = trade['ticker']
        direction = trade['direction']
        entry = trade['entry']
        stop = trade['stop']
        target = trade['target']

        # Get current price
        current_price = self.get_current_price(ticker)
        if current_price is None:
            logger.warning(f"Could not get price for {ticker}, skipping")
            return None

        logger.debug(f"{ticker}: Current={current_price}, Entry={entry}, Stop={stop}, Target={target}")

        # Check if target or stop hit
        if direction == 'long':
            if current_price >= target:
                r_achieved = self.calculate_r_multiple(direction, entry, stop, current_price)
                return {
                    'status': 'WIN',
                    'r_achieved': r_achieved,
                    'exit_price': current_price,
                    'exit_reason': 'target_hit'
                }
            elif current_price <= stop:
                r_achieved = self.calculate_r_multiple(direction, entry, stop, current_price)
                return {
                    'status': 'LOSS',
                    'r_achieved': r_achieved,
                    'exit_price': current_price,
                    'exit_reason': 'stop_hit'
                }
        else:  # short
            if current_price <= target:
                r_achieved = self.calculate_r_multiple(direction, entry, stop, current_price)
                return {
                    'status': 'WIN',
                    'r_achieved': r_achieved,
                    'exit_price': current_price,
                    'exit_reason': 'target_hit'
                }
            elif current_price >= stop:
                r_achieved = self.calculate_r_multiple(direction, entry, stop, current_price)
                return {
                    'status': 'LOSS',
                    'r_achieved': r_achieved,
                    'exit_price': current_price,
                    'exit_reason': 'stop_hit'
                }

        # Still pending
        return None

    async def run(self):
        """Main outcome tracking routine"""
        logger.info("=" * 60)
        logger.info("Outcome Tracker - Starting")
        logger.info("=" * 60)

        try:
            # 1. Get all pending trades
            pending_trades = await self.trade_logger.get_pending_trades()
            logger.info(f"Found {len(pending_trades)} pending trades")

            if not pending_trades:
                logger.info("No pending trades to check")
                return

            # 2. Mark expired trades first
            expired_count = await self.trade_logger.mark_expired_trades()
            if expired_count > 0:
                logger.info(f"Marked {expired_count} trades as expired")

            # 3. Check each pending trade
            updates_made = 0
            for trade in pending_trades:
                trade_id = trade['trade_id']
                ticker = trade['ticker']

                # Skip if expired
                if trade['expires_at'] < datetime.now(trade['expires_at'].tzinfo):
                    logger.debug(f"Skipping expired trade: {trade_id}")
                    continue

                logger.debug(f"Checking trade: {trade_id} ({ticker})")

                # Check outcome
                outcome = self.check_trade_outcome(trade)

                if outcome:
                    # Update trade in database
                    success = await self.trade_logger.update_trade_outcome(
                        trade_id=trade_id,
                        status=outcome['status'],
                        r_achieved=outcome['r_achieved'],
                        exit_price=outcome.get('exit_price'),
                        exit_reason=outcome.get('exit_reason')
                    )

                    if success:
                        updates_made += 1
                        logger.info(
                            f"Trade outcome updated: {trade_id} -> {outcome['status']} "
                            f"({outcome['r_achieved']}R)"
                        )

            logger.info(f"Updated {updates_made} trade outcomes")

            # 4. Log summary stats
            summary = await self.trade_logger.get_performance_summary()
            if summary:
                logger.info("\nPerformance Summary:")
                logger.info(f"  Total Signals: {summary.get('total_signals', 0)}")
                logger.info(f"  Wins: {summary.get('total_wins', 0)}")
                logger.info(f"  Losses: {summary.get('total_losses', 0)}")
                logger.info(f"  Pending: {summary.get('total_pending', 0)}")
                logger.info(f"  Win Rate: {summary.get('win_rate_pct', 0)}%")
                logger.info(f"  Avg R-Multiple: {summary.get('avg_r_multiple', 0)}R")

        except Exception as e:
            logger.error(f"Outcome tracker failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            await self.trade_logger.close()

        logger.info("=" * 60)
        logger.info("Outcome Tracker - Complete")
        logger.info("=" * 60)


async def main():
    """Main entry point"""
    tracker = OutcomeTracker()
    await tracker.run()


if __name__ == '__main__':
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        project_root / "logs" / "outcome_tracker_{time}.log",
        rotation="1 week",
        retention="4 weeks",
        level="DEBUG"
    )

    # Run async main
    asyncio.run(main())
