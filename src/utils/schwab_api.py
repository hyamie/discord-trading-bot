"""
Schwab API Integration Module
Handles authentication and data fetching from Schwab API with OAuth 2.0
"""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode
from loguru import logger
import pandas as pd


class SchwabAPIClient:
    """Client for Schwab API with OAuth 2.0 authentication and rate limiting"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        redirect_uri: str,
        base_url: str = "https://api.schwabapi.com"
    ):
        """
        Initialize Schwab API client

        Args:
            api_key: Schwab API key
            api_secret: Schwab API secret
            redirect_uri: OAuth redirect URI
            base_url: Schwab API base URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url

        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        # Rate limiting (120 calls/min)
        self.rate_limit = 120
        self.rate_window = 60  # seconds
        self.call_timestamps = []

    def _wait_for_rate_limit(self):
        """Implement rate limiting by waiting if necessary"""
        now = time.time()

        # Remove timestamps older than the window
        self.call_timestamps = [
            ts for ts in self.call_timestamps
            if now - ts < self.rate_window
        ]

        # If at limit, wait
        if len(self.call_timestamps) >= self.rate_limit:
            oldest = self.call_timestamps[0]
            wait_time = self.rate_window - (now - oldest) + 0.1
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                self.call_timestamps = []

        # Record this call
        self.call_timestamps.append(time.time())

    def authenticate(self, auth_code: Optional[str] = None) -> bool:
        """
        Authenticate with Schwab API using OAuth 2.0

        Args:
            auth_code: Authorization code (for initial auth)

        Returns:
            True if authentication successful
        """
        if self.refresh_token:
            return self._refresh_access_token()
        elif auth_code:
            return self._get_initial_token(auth_code)
        else:
            logger.error("No auth code or refresh token available")
            return False

    def _get_initial_token(self, auth_code: str) -> bool:
        """
        Get initial access token using authorization code

        Args:
            auth_code: OAuth authorization code

        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/v1/oauth/token"
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.api_key,
                'client_secret': self.api_secret
            }

            # Use Basic Auth for client credentials
            auth = (self.api_key, self.api_secret)
            response = requests.post(url, data=data, auth=auth)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 1800)  # 30 min default
            self.token_expires_at = time.time() + expires_in

            logger.info("Successfully obtained initial access token")
            return True

        except Exception as e:
            logger.error(f"Failed to get initial token: {e}")
            return False

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token

        Returns:
            True if successful
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        try:
            url = f"{self.base_url}/v1/oauth/token"
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }

            # Use Basic Auth for client credentials
            auth = (self.api_key, self.api_secret)
            response = requests.post(url, data=data, auth=auth)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 1800)
            self.token_expires_at = time.time() + expires_in

            logger.info("Successfully refreshed access token")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token:
            logger.error("Not authenticated")
            return False

        # Refresh if token expires in less than 5 minutes
        if self.token_expires_at and time.time() > (self.token_expires_at - 300):
            logger.info("Token expiring soon, refreshing...")
            return self._refresh_access_token()

        return True

    def _make_request(
        self,
        endpoint: str,
        params: Dict = None,
        method: str = 'GET'
    ) -> Optional[Dict]:
        """
        Make an authenticated request to Schwab API

        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method

        Returns:
            Response data or None
        """
        if not self._ensure_authenticated():
            return None

        self._wait_for_rate_limit()

        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'X-API-Key': self.api_key,
                'Accept': 'application/json'
            }

            # Only add Content-Type for POST requests
            if method != 'GET':
                headers['Content-Type'] = 'application/json'

            start_time = time.time()

            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.post(url, headers=headers, json=params)

            response_time = int((time.time() - start_time) * 1000)

            # Log the API call
            logger.debug(
                f"Schwab API {method} {endpoint}: "
                f"{response.status_code} ({response_time}ms)"
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"Schwab API HTTP error: {e}")
            # Log response body for debugging
            try:
                error_body = e.response.text
                logger.error(f"Schwab API error response: {error_body}")
            except:
                pass

            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded, backing off...")
                time.sleep(60)
            return None

        except Exception as e:
            logger.error(f"Schwab API request failed: {e}")
            return None

    def get_price_history(
        self,
        ticker: str,
        period_type: str = 'day',
        period: int = 10,
        frequency_type: str = 'minute',
        frequency: int = 5,
        extended_hours: bool = True,
        start_datetime: datetime = None,
        end_datetime: datetime = None
    ) -> Optional[pd.DataFrame]:
        """
        Get price history for a ticker

        Args:
            ticker: Stock ticker symbol
            period_type: 'day', 'month', 'year', 'ytd' (ignored if using datetime range)
            period: Number of periods (ignored if using datetime range)
            frequency_type: 'minute', 'daily', 'weekly', 'monthly'
            frequency: Frequency value (1, 5, 10, 15, 30 for minute)
            extended_hours: Include extended hours data
            start_datetime: Start datetime for range (preferred over period)
            end_datetime: End datetime for range (defaults to now)

        Returns:
            DataFrame with OHLCV data or None
        """
        endpoint = "/marketdata/v1/pricehistory"

        # Use datetime range if provided (recommended approach)
        if start_datetime is not None:
            import time
            if end_datetime is None:
                end_datetime = datetime.now()

            params = {
                'symbol': ticker.upper(),
                'frequencyType': frequency_type,
                'frequency': frequency,
                'startDate': int(start_datetime.timestamp() * 1000),  # milliseconds
                'endDate': int(end_datetime.timestamp() * 1000),
                'needExtendedHoursData': str(extended_hours).lower()
            }
        else:
            # Fallback to period-based (may have validation issues)
            params = {
                'symbol': ticker.upper(),
                'periodType': period_type,
                'period': period,
                'frequencyType': frequency_type,
                'frequency': frequency,
                'needExtendedHoursData': str(extended_hours).lower()
            }

        data = self._make_request(endpoint, params)

        if not data or 'candles' not in data:
            logger.warning(f"No price data for {ticker}")
            return None

        try:
            # Convert to DataFrame
            candles = data['candles']
            df = pd.DataFrame(candles)

            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df.set_index('datetime', inplace=True)

            # Rename columns to lowercase
            df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }, inplace=True)

            logger.info(
                f"Fetched {len(df)} candles for {ticker} "
                f"({frequency_type} {frequency})"
            )

            return df

        except Exception as e:
            logger.error(f"Error parsing price data for {ticker}: {e}")
            return None

    def get_quote(self, ticker: str) -> Optional[Dict]:
        """
        Get real-time quote for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Quote data or None
        """
        endpoint = f"/marketdata/v1/quotes"
        params = {'symbols': ticker.upper()}
        data = self._make_request(endpoint, params)

        if data and ticker.upper() in data:
            return data[ticker.upper()]

        return None

    def get_multiple_timeframes(
        self,
        ticker: str,
        timeframe_configs: List[Dict]
    ) -> Dict[str, pd.DataFrame]:
        """
        Get price data for multiple timeframes

        Args:
            ticker: Stock ticker symbol
            timeframe_configs: List of config dicts with timeframe parameters

        Returns:
            Dictionary mapping timeframe names to DataFrames

        Example:
            configs = [
                {'name': 'higher', 'frequency_type': 'minute', 'frequency': 60},
                {'name': 'middle', 'frequency_type': 'minute', 'frequency': 15},
                {'name': 'lower', 'frequency_type': 'minute', 'frequency': 5}
            ]
        """
        results = {}

        for config in timeframe_configs:
            name = config.pop('name', 'unknown')

            df = self.get_price_history(ticker, **config)

            if df is not None:
                results[name] = df
            else:
                logger.warning(f"Failed to fetch {name} timeframe for {ticker}")

        return results


class AlphaVantageClient:
    """Backup data source using Alpha Vantage API"""

    def __init__(self, api_key: str):
        """Initialize Alpha Vantage client"""
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.call_timestamps = []
        self.rate_limit = 5  # Free tier: 5 calls/min

    def _wait_for_rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 60]

        if len(self.call_timestamps) >= self.rate_limit:
            wait_time = 60 - (now - self.call_timestamps[0]) + 0.1
            if wait_time > 0:
                logger.warning(f"Alpha Vantage rate limit, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                self.call_timestamps = []

        self.call_timestamps.append(time.time())

    def get_intraday(
        self,
        ticker: str,
        interval: str = '5min',
        outputsize: str = 'compact'
    ) -> Optional[pd.DataFrame]:
        """
        Get intraday price data

        Args:
            ticker: Stock ticker
            interval: '1min', '5min', '15min', '30min', '60min'
            outputsize: 'compact' (100 points) or 'full' (all)

        Returns:
            DataFrame with OHLCV data
        """
        self._wait_for_rate_limit()

        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': ticker.upper(),
                'interval': interval,
                'apikey': self.api_key,
                'outputsize': outputsize
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                logger.warning(f"No data for {ticker} from Alpha Vantage")
                return None

            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)

            # Rename and convert columns
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            df['volume'] = df['volume'].astype(int)

            logger.info(f"Fetched {len(df)} bars for {ticker} from Alpha Vantage")
            return df

        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
            return None
