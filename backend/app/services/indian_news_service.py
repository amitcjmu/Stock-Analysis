"""
Indian News Service - Fetches news from leading Indian economic newspapers
Supports Times Group (Economic Times) and Hindustan Times Group
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
import feedparser
from urllib.parse import urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)


class IndianNewsService:
    """Service for fetching news from leading Indian economic newspapers"""

    def __init__(self):
        # NewsAPI.org configuration
        self.newsapi_key = getattr(settings, "NEWSAPI_KEY", None) or None
        self.newsapi_base_url = "https://newsapi.org/v2"

        # Indian news sources
        self.indian_sources = {
            "economic_times": {
                "name": "The Economic Times",
                "rss_feeds": [
                    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",  # Markets
                    "https://economictimes.indiatimes.com/companies/rssfeeds/13357270.cms",  # Companies
                    "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",  # Economy
                ],
                "newsapi_id": "the-economic-times",
            },
            "hindustan_times": {
                "name": "Hindustan Times",
                "rss_feeds": [
                    "https://www.hindustantimes.com/rss/business/rssfeed.xml",  # Business
                    "https://www.hindustantimes.com/rss/market/rssfeed.xml",  # Market
                ],
                "newsapi_id": "hindustan-times",
            },
            "business_standard": {
                "name": "Business Standard",
                "rss_feeds": [
                    "https://www.business-standard.com/rss/markets-106.rss",
                    "https://www.business-standard.com/rss/companies-102.rss",
                ],
                "newsapi_id": "business-standard",
            },
            "livemint": {
                "name": "Mint",
                "rss_feeds": [
                    "https://www.livemint.com/rss/markets",
                    "https://www.livemint.com/rss/companies",
                ],
                "newsapi_id": "mint",
            },
        }

    async def get_stock_news(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        limit: int = 50,
        months_back: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Get news articles for a stock from leading Indian economic newspapers.

        Args:
            symbol: Stock symbol (e.g., RELIANCE, TCS)
            company_name: Company name for better search results
            limit: Maximum number of articles to return
            months_back: Number of months to look back (default 6)

        Returns:
            List of news articles with title, publisher, link, published_date, summary
        """
        logger.info(
            f"📰 [INDIAN NEWS] Fetching news for {symbol} (company: {company_name}) "
            f"from past {months_back} months"
        )

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)

        # Build search query
        search_terms = [symbol]
        if company_name:
            # Extract main company name (remove common suffixes)
            clean_name = (
                company_name.replace(" Limited", "")
                .replace(" Ltd", "")
                .replace(" Inc", "")
            )
            search_terms.append(clean_name)

        all_news = []

        # Try NewsAPI first if available
        if self.newsapi_key:
            try:
                newsapi_news = await self._fetch_from_newsapi(
                    search_terms, start_date, end_date, limit
                )
                all_news.extend(newsapi_news)
                logger.info(
                    f"📰 [INDIAN NEWS] Fetched {len(newsapi_news)} articles from NewsAPI"
                )
            except Exception as e:
                logger.warning(f"📰 [INDIAN NEWS] NewsAPI fetch failed: {e}")

        # Fetch from RSS feeds
        try:
            rss_news = await self._fetch_from_rss_feeds(
                search_terms, start_date, end_date, limit
            )
            all_news.extend(rss_news)
            logger.info(
                f"📰 [INDIAN NEWS] Fetched {len(rss_news)} articles from RSS feeds"
            )
        except Exception as e:
            logger.warning(f"📰 [INDIAN NEWS] RSS fetch failed: {e}")

        # Remove duplicates based on title similarity
        unique_news = self._deduplicate_news(all_news)

        # Filter by date range and relevance
        filtered_news = self._filter_news_by_relevance(
            unique_news, search_terms, start_date, end_date
        )

        # Sort by date (newest first) and limit
        filtered_news.sort(key=lambda x: x.get("published_date", 0), reverse=True)
        result = filtered_news[:limit]

        logger.info(
            f"📰 [INDIAN NEWS] Returning {len(result)} unique news articles for {symbol}"
        )

        return result

    async def _fetch_from_newsapi(
        self,
        search_terms: List[str],
        start_date: datetime,
        end_date: datetime,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI.org"""
        if not self.newsapi_key:
            return []

        news_articles = []
        async with aiohttp.ClientSession() as session:
            for term in search_terms:
                try:
                    # Build query for Indian sources
                    sources = ",".join(
                        [
                            source["newsapi_id"]
                            for source in self.indian_sources.values()
                            if source.get("newsapi_id")
                        ]
                    )

                    params = {
                        "q": term,
                        "sources": sources,
                        "from": start_date.strftime("%Y-%m-%d"),
                        "to": end_date.strftime("%Y-%m-%d"),
                        "sortBy": "publishedAt",
                        "pageSize": min(limit, 100),
                        "apiKey": self.newsapi_key,
                    }

                    url = f"{self.newsapi_base_url}/everything?{urlencode(params)}"
                    logger.debug(
                        f"📰 [INDIAN NEWS] NewsAPI URL: {url.replace(self.newsapi_key, '***')}"
                    )

                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("status") == "ok":
                                articles = data.get("articles", [])
                                for article in articles:
                                    news_articles.append(
                                        {
                                            "title": article.get("title", ""),
                                            "publisher": article.get("source", {}).get(
                                                "name", "Unknown"
                                            ),
                                            "link": article.get("url", ""),
                                            "published_date": self._parse_date(
                                                article.get("publishedAt", "")
                                            ),
                                            "summary": article.get("description", ""),
                                            "source": "newsapi",
                                        }
                                    )
                        else:
                            logger.warning(
                                f"📰 [INDIAN NEWS] NewsAPI returned status {response.status}"
                            )
                except Exception as e:
                    logger.error(f"📰 [INDIAN NEWS] Error fetching from NewsAPI: {e}")
                    continue

        return news_articles

    async def _fetch_from_rss_feeds(
        self,
        search_terms: List[str],
        start_date: datetime,
        end_date: datetime,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fetch news from RSS feeds"""
        news_articles = []

        # Collect all RSS feeds
        all_feeds = []
        for source_name, source_info in self.indian_sources.items():
            for feed_url in source_info.get("rss_feeds", []):
                all_feeds.append((feed_url, source_info["name"]))

        # Fetch from all feeds concurrently
        tasks = [
            self._fetch_single_rss_feed(
                feed_url, publisher, search_terms, start_date, end_date
            )
            for feed_url, publisher in all_feeds
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                news_articles.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"📰 [INDIAN NEWS] RSS feed error: {result}")

        return news_articles

    async def _fetch_single_rss_feed(
        self,
        feed_url: str,
        publisher: str,
        search_terms: List[str],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch news from a single RSS feed"""
        news_articles = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    feed_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        feed = feedparser.parse(content)

                        for entry in feed.entries:
                            try:
                                # Parse published date - feedparser provides parsed dates
                                pub_date = None
                                if (
                                    hasattr(entry, "published_parsed")
                                    and entry.published_parsed
                                ):
                                    # Use feedparser's parsed date (tuple format)
                                    pub_date = int(
                                        datetime(
                                            *entry.published_parsed[:6]
                                        ).timestamp()
                                    )
                                elif (
                                    hasattr(entry, "updated_parsed")
                                    and entry.updated_parsed
                                ):
                                    pub_date = int(
                                        datetime(*entry.updated_parsed[:6]).timestamp()
                                    )
                                else:
                                    # Fallback to string parsing
                                    pub_date = self._parse_date(
                                        entry.get("published", "")
                                    )
                                    if not pub_date:
                                        pub_date = self._parse_date(
                                            entry.get("updated", "")
                                        )

                                # Check if article is within date range
                                if pub_date and (
                                    pub_date < start_date.timestamp()
                                    or pub_date > end_date.timestamp()
                                ):
                                    continue

                                # Check if article is relevant to search terms
                                title = entry.get("title", "").lower()
                                summary = entry.get("summary", "").lower()

                                is_relevant = any(
                                    term.lower() in title or term.lower() in summary
                                    for term in search_terms
                                )

                                if is_relevant:
                                    news_articles.append(
                                        {
                                            "title": entry.get("title", ""),
                                            "publisher": publisher,
                                            "link": entry.get("link", ""),
                                            "published_date": pub_date
                                            or int(datetime.now().timestamp()),
                                            "summary": entry.get("summary", "")
                                            or entry.get("description", ""),
                                            "source": "rss",
                                        }
                                    )
                            except Exception as e:
                                logger.debug(
                                    f"📰 [INDIAN NEWS] Error parsing RSS entry: {e}"
                                )
                                continue
                    else:
                        logger.debug(
                            f"📰 [INDIAN NEWS] RSS feed {feed_url} returned status {response.status}"
                        )
        except Exception as e:
            logger.debug(f"📰 [INDIAN NEWS] Error fetching RSS feed {feed_url}: {e}")

        return news_articles

    def _parse_date(self, date_str: str) -> Optional[int]:
        """Parse date string to timestamp"""
        if not date_str:
            return None

        try:
            # Try parsing ISO format
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                # Try common date formats
                for fmt in [
                    "%Y-%m-%d",
                    "%Y-%m-%d %H:%M:%S",
                    "%a, %d %b %Y %H:%M:%S %Z",
                ]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Fallback: try to parse using feedparser's date parsing
                    try:
                        # Use feedparser's date parsing utility
                        from feedparser import _parse_date as feedparser_parse_date

                        parsed = feedparser_parse_date(date_str)
                        if parsed:
                            dt = datetime(*parsed[:6])
                        else:
                            return None
                    except (ImportError, AttributeError, Exception):
                        # If feedparser parsing fails, return None
                        return None

            return int(dt.timestamp())
        except Exception as e:
            logger.debug(f"📰 [INDIAN NEWS] Error parsing date '{date_str}': {e}")
            return None

    def _deduplicate_news(
        self, news_articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate news articles based on title similarity"""
        seen_titles = set()
        unique_news = []

        for article in news_articles:
            title = article.get("title", "").lower().strip()
            # Normalize title (remove extra spaces, special chars)
            normalized = " ".join(title.split())

            # Check for similar titles (simple approach)
            is_duplicate = False
            for seen in seen_titles:
                # Check if titles are very similar (80% similarity)
                if self._title_similarity(normalized, seen) > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_titles.add(normalized)
                unique_news.append(article)

        return unique_news

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        words1 = set(title1.split())
        words2 = set(title2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _filter_news_by_relevance(
        self,
        news_articles: List[Dict[str, Any]],
        search_terms: List[str],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Filter news articles by relevance to search terms and date range"""
        filtered = []

        for article in news_articles:
            # Check date range
            pub_date = article.get("published_date", 0)
            if pub_date < start_date.timestamp() or pub_date > end_date.timestamp():
                continue

            # Check relevance
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            combined_text = f"{title} {summary}"

            # Count matches
            matches = sum(1 for term in search_terms if term.lower() in combined_text)

            if matches > 0:
                article["relevance_score"] = matches / len(search_terms)
                filtered.append(article)

        return filtered
