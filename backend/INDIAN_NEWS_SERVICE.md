# Indian News Service - Implementation Summary

## Overview

The stock news fetching system has been enhanced to fetch news from leading Indian economic newspapers (Times Group and Hindustan Times Group) instead of relying solely on Yahoo Finance. The new service supports fetching news from the past 6 months by default.

## Changes Made

### 1. New Service: `indian_news_service.py`

Created a new service that fetches news from:
- **Times Group**: The Economic Times (markets, companies, economy sections)
- **Hindustan Times Group**: Hindustan Times (business, market sections)
- **Additional Sources**: Business Standard, Mint (Livemint)

### 2. News Sources

The service uses two methods to fetch news:

#### a. NewsAPI.org (Optional)
- Requires `NEWSAPI_KEY` environment variable
- Provides structured news data from multiple Indian sources
- Better coverage and filtering capabilities

#### b. RSS Feeds (Primary)
- Fetches directly from RSS feeds of leading Indian newspapers
- No API key required
- Supports:
  - Economic Times RSS feeds (markets, companies, economy)
  - Hindustan Times RSS feeds (business, market)
  - Business Standard RSS feeds
  - Mint RSS feeds

### 3. Updated Services

#### `stock_data_api.py`
- Replaced yfinance news fetching with Indian News Service
- Now accepts `company_name` and `months_back` parameters
- Removed dependency on yfinance for news

#### `stock_service.py`
- Updated to pass company name to news service
- Supports `months_back` parameter (default: 6 months)

#### `stock_routes.py`
- Updated `/stock/stocks/{symbol}/news` endpoint
- Added `months_back` query parameter (default: 6)
- Changed response to show `indian_news_count` instead of `yfinance_count`
- Updated all news analysis endpoints to fetch 6 months of news

### 4. Dependencies

Added to `requirements.txt`:
- `feedparser==6.0.11` - For parsing RSS feeds

## Configuration

### Environment Variables

Optional (for enhanced news fetching):
```bash
NEWSAPI_KEY=your_newsapi_key_here
```

The service works without this key by using RSS feeds directly.

## API Usage

### Get Stock News

```http
GET /api/v1/stock/stocks/{symbol}/news?limit=50&months_back=6
```

**Parameters:**
- `symbol` (required): Stock symbol (e.g., RELIANCE, TCS)
- `limit` (optional, default: 20): Maximum number of articles
- `months_back` (optional, default: 6): Number of months to look back
- `include_llm_news` (optional, default: true): Include AI-generated insights

**Response:**
```json
{
  "success": true,
  "symbol": "RELIANCE",
  "news": [
    {
      "title": "Article Title",
      "publisher": "The Economic Times",
      "link": "https://...",
      "published_date": 1234567890,
      "summary": "Article summary...",
      "source": "rss"
    }
  ],
  "count": 25,
  "indian_news_count": 20,
  "llm_count": 5
}
```

## Features

### 1. Multi-Source Aggregation
- Fetches from multiple Indian news sources simultaneously
- Combines results from RSS feeds and NewsAPI (if configured)

### 2. Relevance Filtering
- Filters articles based on stock symbol and company name
- Calculates relevance scores
- Removes duplicate articles

### 3. Date Range Filtering
- Supports custom date ranges (default: 6 months)
- Filters articles by publication date
- Sorts by date (newest first)

### 4. Deduplication
- Removes duplicate articles based on title similarity
- Uses fuzzy matching to identify similar articles

## News Sources Included

1. **The Economic Times** (Times Group)
   - Markets section
   - Companies section
   - Economy section

2. **Hindustan Times** (Hindustan Times Group)
   - Business section
   - Market section

3. **Business Standard**
   - Markets section
   - Companies section

4. **Mint (Livemint)**
   - Markets section
   - Companies section

## Benefits

1. **Better Coverage**: Access to leading Indian economic newspapers
2. **Historical Data**: Fetch news from past 6 months (configurable)
3. **No API Limits**: RSS feeds don't have rate limits (unlike yfinance)
4. **Relevant Content**: Focused on Indian stocks and market news
5. **Multiple Sources**: Aggregates news from multiple reputable sources

## Migration Notes

- The system no longer uses yfinance for news fetching
- All existing endpoints continue to work with updated data sources
- News format remains compatible with existing code
- LLM-generated insights are still included (optional)

## Testing

To test the new service:

```python
from app.services.indian_news_service import IndianNewsService

service = IndianNewsService()
news = await service.get_stock_news(
    symbol="RELIANCE",
    company_name="Reliance Industries",
    limit=20,
    months_back=6
)
```

## Future Enhancements

Potential improvements:
1. Add more Indian news sources (Moneycontrol, Business Today, etc.)
2. Implement caching for RSS feeds
3. Add sentiment analysis for fetched articles
4. Support for more date range options
5. Add news category filtering
