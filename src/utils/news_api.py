"""
News API Integration Module
Fetches and aggregates news from Finnhub and NewsAPI
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger


class FinnhubClient:
    """Client for Finnhub news and market data"""

    def __init__(self, api_key: str):
        """Initialize Finnhub client"""
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.call_timestamps = []
        self.rate_limit = 60  # Free tier: 60 calls/min

    def _wait_for_rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 60]

        if len(self.call_timestamps) >= self.rate_limit:
            wait_time = 60 - (now - self.call_timestamps[0]) + 0.1
            if wait_time > 0:
                logger.warning(f"Finnhub rate limit, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                self.call_timestamps = []

        self.call_timestamps.append(time.time())

    def get_company_news(
        self,
        ticker: str,
        days_back: int = 1,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Get company news

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to look back
            max_results: Maximum number of results

        Returns:
            List of news articles
        """
        self._wait_for_rate_limit()

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            params = {
                'symbol': ticker.upper(),
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'token': self.api_key
            }

            response = requests.get(
                f"{self.base_url}/company-news",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            articles = response.json()

            # Limit results
            articles = articles[:max_results]

            # Standardize format
            standardized = []
            for article in articles:
                standardized.append({
                    'source': 'finnhub',
                    'headline': article.get('headline', ''),
                    'summary': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'published_at': datetime.fromtimestamp(
                        article.get('datetime', 0)
                    ).isoformat(),
                    'sentiment': self._infer_sentiment(
                        article.get('headline', ''),
                        article.get('summary', '')
                    ),
                    'category': article.get('category', 'general')
                })

            logger.info(f"Fetched {len(standardized)} articles for {ticker} from Finnhub")
            return standardized

        except Exception as e:
            logger.error(f"Finnhub API error: {e}")
            return []

    def get_market_news(
        self,
        category: str = 'general',
        max_results: int = 10
    ) -> List[Dict]:
        """
        Get general market news

        Args:
            category: News category (general, forex, crypto, merger)
            max_results: Maximum results

        Returns:
            List of news articles
        """
        self._wait_for_rate_limit()

        try:
            params = {
                'category': category,
                'token': self.api_key
            }

            response = requests.get(
                f"{self.base_url}/news",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            articles = response.json()[:max_results]

            standardized = []
            for article in articles:
                standardized.append({
                    'source': 'finnhub',
                    'headline': article.get('headline', ''),
                    'summary': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'published_at': datetime.fromtimestamp(
                        article.get('datetime', 0)
                    ).isoformat(),
                    'sentiment': 'neutral',
                    'category': category
                })

            logger.info(f"Fetched {len(standardized)} market news from Finnhub")
            return standardized

        except Exception as e:
            logger.error(f"Finnhub market news error: {e}")
            return []

    @staticmethod
    def _infer_sentiment(headline: str, summary: str) -> str:
        """
        Simple rule-based sentiment inference

        Args:
            headline: Article headline
            summary: Article summary

        Returns:
            'positive', 'negative', or 'neutral'
        """
        text = (headline + ' ' + summary).lower()

        positive_words = [
            'surge', 'gain', 'profit', 'growth', 'record', 'beat', 'exceed',
            'strong', 'rise', 'jump', 'rally', 'breakthrough', 'success',
            'upgrade', 'bullish', 'optimistic', 'outperform'
        ]

        negative_words = [
            'loss', 'decline', 'drop', 'fall', 'crash', 'plunge', 'miss',
            'weak', 'concern', 'risk', 'warning', 'downgrade', 'bearish',
            'pessimistic', 'underperform', 'layoff', 'cut', 'lawsuit'
        ]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'


class NewsAPIClient:
    """Client for NewsAPI"""

    def __init__(self, api_key: str):
        """Initialize NewsAPI client"""
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.call_timestamps = []
        self.rate_limit = 100  # Developer plan: 100 calls/day

    def _wait_for_rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        # Check daily limit
        self.call_timestamps = [
            ts for ts in self.call_timestamps
            if now - ts < 86400  # 24 hours
        ]

        if len(self.call_timestamps) >= self.rate_limit:
            logger.error("NewsAPI daily rate limit reached")
            return False

        self.call_timestamps.append(time.time())
        return True

    def search_news(
        self,
        query: str,
        days_back: int = 1,
        max_results: int = 10,
        language: str = 'en'
    ) -> List[Dict]:
        """
        Search for news articles

        Args:
            query: Search query (e.g., ticker symbol)
            days_back: Number of days to look back
            max_results: Maximum results
            language: Language code

        Returns:
            List of news articles
        """
        if not self._wait_for_rate_limit():
            return []

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            params = {
                'q': query,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'language': language,
                'sortBy': 'relevancy',
                'pageSize': max_results,
                'apiKey': self.api_key
            }

            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 'ok':
                logger.warning(f"NewsAPI error: {data.get('message')}")
                return []

            articles = data.get('articles', [])

            standardized = []
            for article in articles:
                standardized.append({
                    'source': f"newsapi:{article.get('source', {}).get('name', 'unknown')}",
                    'headline': article.get('title', ''),
                    'summary': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'sentiment': FinnhubClient._infer_sentiment(
                        article.get('title', ''),
                        article.get('description', '')
                    ),
                    'category': 'general'
                })

            logger.info(f"Fetched {len(standardized)} articles for '{query}' from NewsAPI")
            return standardized

        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []


class NewsAggregator:
    """Aggregates news from multiple sources"""

    def __init__(self, finnhub_key: str, newsapi_key: str):
        """
        Initialize news aggregator

        Args:
            finnhub_key: Finnhub API key
            newsapi_key: NewsAPI key
        """
        self.finnhub = FinnhubClient(finnhub_key) if finnhub_key else None
        self.newsapi = NewsAPIClient(newsapi_key) if newsapi_key else None

    def get_ticker_news(
        self,
        ticker: str,
        days_back: int = 1,
        max_per_source: int = 5
    ) -> Dict[str, any]:
        """
        Get aggregated news for a ticker from all sources

        Args:
            ticker: Stock ticker symbol
            days_back: Days to look back
            max_per_source: Max articles per source

        Returns:
            Dictionary with articles and summary
        """
        all_articles = []

        # Finnhub
        if self.finnhub:
            finnhub_articles = self.finnhub.get_company_news(
                ticker, days_back, max_per_source
            )
            all_articles.extend(finnhub_articles)

        # NewsAPI
        if self.newsapi:
            newsapi_articles = self.newsapi.search_news(
                ticker, days_back, max_per_source
            )
            all_articles.extend(newsapi_articles)

        # Remove duplicates based on headline similarity
        unique_articles = self._deduplicate(all_articles)

        # Sort by publish date (newest first)
        unique_articles.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )

        # Calculate sentiment summary
        sentiment_summary = self._summarize_sentiment(unique_articles)

        return {
            'ticker': ticker,
            'total_articles': len(unique_articles),
            'articles': unique_articles[:10],  # Top 10
            'sentiment_summary': sentiment_summary,
            'fetched_at': datetime.now().isoformat()
        }

    @staticmethod
    def _deduplicate(articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on headline similarity"""
        if not articles:
            return []

        unique = []
        seen_headlines = set()

        for article in articles:
            headline = article.get('headline', '').lower()
            # Simple deduplication: first 50 chars of headline
            key = headline[:50]

            if key not in seen_headlines:
                seen_headlines.add(key)
                unique.append(article)

        return unique

    @staticmethod
    def _summarize_sentiment(articles: List[Dict]) -> Dict[str, any]:
        """
        Calculate sentiment summary

        Args:
            articles: List of articles

        Returns:
            Summary with counts and overall sentiment
        """
        if not articles:
            return {
                'overall': 'neutral',
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_pct': 0,
                'negative_pct': 0
            }

        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }

        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            sentiment_counts[sentiment] += 1

        total = len(articles)
        positive_pct = round((sentiment_counts['positive'] / total) * 100, 1)
        negative_pct = round((sentiment_counts['negative'] / total) * 100, 1)

        # Overall sentiment
        if positive_pct > 60:
            overall = 'positive'
        elif negative_pct > 60:
            overall = 'negative'
        elif positive_pct > negative_pct + 20:
            overall = 'positive'
        elif negative_pct > positive_pct + 20:
            overall = 'negative'
        else:
            overall = 'neutral'

        return {
            'overall': overall,
            'positive': sentiment_counts['positive'],
            'negative': sentiment_counts['negative'],
            'neutral': sentiment_counts['neutral'],
            'positive_pct': positive_pct,
            'negative_pct': negative_pct,
            'description': f"{positive_pct}% positive, {negative_pct}% negative"
        }

    def format_news_for_discord(
        self,
        news_data: Dict,
        max_headlines: int = 3
    ) -> str:
        """
        Format news summary for Discord

        Args:
            news_data: News data from get_ticker_news()
            max_headlines: Number of headlines to show

        Returns:
            Formatted string for Discord
        """
        articles = news_data.get('articles', [])
        sentiment = news_data.get('sentiment_summary', {})

        if not articles:
            return "📰 **News**: No recent news found"

        lines = [
            f"📰 **Latest News** ({sentiment.get('description', 'N/A')})"
        ]

        for i, article in enumerate(articles[:max_headlines], 1):
            emoji = {
                'positive': '✅',
                'negative': '❌',
                'neutral': '➖'
            }.get(article.get('sentiment', 'neutral'), '➖')

            headline = article.get('headline', 'Untitled')
            # Truncate long headlines
            if len(headline) > 80:
                headline = headline[:77] + '...'

            lines.append(f"{i}. {emoji} {headline}")

        return '\n'.join(lines)
