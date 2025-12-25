# Cassandra Integration for Stock Search Data

## Overview

This document describes the integration of Apache Cassandra database for storing user stock search-related information. Cassandra is used to store high-volume, time-series search data with fast read performance.

## Architecture Diagrams

For visual architecture diagrams, see:
- [Cassandra Integration Sequence Diagram](../architecture/cassandra-integration-sequence.mmd)
- [Cassandra Architecture Overview](../architecture/cassandra-architecture.mmd)
- [Stock Search Flow Diagram](../architecture/stock-search-flow.mmd)

## Architecture

### Why Cassandra?

- **High Write Throughput**: Optimized for write-heavy workloads (search logging)
- **Time-Series Data**: Perfect for storing search history with time-based queries
- **Scalability**: Horizontal scaling for growing search volumes
- **Fast Reads**: Optimized for time-ordered queries
- **TTL Support**: Built-in expiration for cached search results

### Schema Design

#### Keyspace: `stock_analysis`

**Table 1: `user_stock_searches`** (Time-series search history)
- **Partition Key**: `(client_account_id, user_id, search_date)`
- **Clustering Keys**: `(search_timestamp DESC, search_id)`
- **Purpose**: Store individual search queries with metadata
- **Fields**:
  - `client_account_id`, `engagement_id`, `user_id` - Multi-tenant isolation
  - `search_date` - Date partition for efficient queries
  - `search_timestamp` - Exact timestamp of search
  - `search_id` - Unique identifier for each search
  - `search_query` - The search query string
  - `search_type` - Type: 'symbol', 'company_name', 'fuzzy'
  - `results_count` - Number of results returned
  - `execution_time_ms` - Query execution time
  - `source` - Data source: 'database', 'api', 'cache'

**Table 2: `user_search_results`** (Search results cache)
- **Partition Key**: `search_query_hash`
- **Clustering Keys**: `(client_account_id, user_id, search_id)`
- **Purpose**: Cache search results for quick lookup
- **TTL**: 24 hours (set per-row during INSERT)
- **Fields**:
  - `search_query_hash` - MD5 hash of search query
  - `results` - JSON string of search results
  - `created_at`, `expires_at` - Cache expiration tracking

**Table 3: `user_search_analytics`** (Aggregated analytics)
- **Partition Key**: `(client_account_id, user_id)`
- **Clustering Key**: `year_month`
- **Purpose**: Pre-aggregated monthly analytics
- **Fields**:
  - `year_month` - Format: 'YYYY-MM'
  - `total_searches` - Total number of searches
  - `unique_queries` - Number of unique queries
  - `avg_results_count` - Average results per search
  - `avg_execution_time_ms` - Average execution time
  - `most_searched_symbols` - Map of symbol -> count
  - `search_sources` - Map of source -> count

## Configuration

### Environment Variables

Add these to your `.env` file or environment:

```bash
# Cassandra Connection
CASSANDRA_CONTACT_POINTS=cassandra  # Comma-separated list: "host1,host2"
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=stock_analysis
CASSANDRA_USERNAME=  # Optional, leave empty for no auth
CASSANDRA_PASSWORD=  # Optional, leave empty for no auth
```

### Docker Setup

Cassandra is configured in `docker-compose.yml` and will start automatically:

```bash
docker-compose -f config/docker/docker-compose.yml up -d cassandra
```

## Usage

### Automatic Integration

The Cassandra service is automatically integrated with `StockService.search_stocks()`. Every search is logged to Cassandra:

1. **Cache Check**: First checks Cassandra cache for recent results
2. **Search Execution**: Performs the actual search (database or API)
3. **Logging**: Logs search to Cassandra (non-blocking)
4. **Caching**: Caches results for 24 hours
5. **Analytics**: Updates aggregated analytics

### Manual Usage

```python
from app.services.cassandra_service import cassandra_service

# Log a search
search_id = await cassandra_service.log_stock_search(
    client_account_id=uuid.UUID("..."),
    engagement_id=uuid.UUID("..."),
    user_id="user123",
    search_query="AAPL",
    search_type="symbol",
    results_count=10,
    execution_time_ms=150,
    source="api",
    results=[...]  # Optional: cache results
)

# Get search history
history = await cassandra_service.get_search_history(
    client_account_id=uuid.UUID("..."),
    user_id="user123",
    days=30,
    limit=100
)

# Get analytics
analytics = await cassandra_service.get_search_analytics(
    client_account_id=uuid.UUID("..."),
    user_id="user123",
    year_month="2025-01"  # Optional, defaults to current month
)

# Get cached results
cached = await cassandra_service.get_cached_results(
    client_account_id=uuid.UUID("..."),
    user_id="user123",
    search_query="AAPL"
)
```

## API Endpoints

### Get Search History

```http
GET /api/v1/stock/stocks/search/history?days=30&limit=100
```

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "search_id": "uuid",
      "search_query": "AAPL",
      "search_type": "symbol",
      "results_count": 10,
      "execution_time_ms": 150,
      "source": "api",
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 50,
  "days": 30
}
```

### Get Search Analytics

```http
GET /api/v1/stock/stocks/search/analytics?year_month=2025-01
```

**Response:**
```json
{
  "success": true,
  "analytics": {
    "year_month": "2025-01",
    "total_searches": 150,
    "unique_queries": 45,
    "avg_results_count": 8.5,
    "avg_execution_time_ms": 120.5,
    "most_searched_symbols": {
      "AAPL": 25,
      "MSFT": 20,
      "GOOGL": 15
    },
    "search_sources": {
      "api": 100,
      "database": 40,
      "cache": 10
    }
  }
}
```

## Frontend

### Search History View

Access the search history view at `/discovery/search-history` or via the sidebar navigation.

**Features:**
- View all search history with filters
- Statistics dashboard (total searches, avg execution time, cache hits)
- Filter by query, source, type, and time range
- Click to search again
- Real-time data from Cassandra

## Performance Considerations

### Write Performance

- **Non-blocking Logging**: Search logging uses `asyncio.create_task()` to avoid blocking the main request
- **Batch Writes**: Analytics updates are batched and executed asynchronously
- **Consistency Level**: Uses `ConsistencyLevel.ONE` for fast writes

### Read Performance

- **Partitioning**: Data is partitioned by date for efficient time-range queries
- **Caching**: Search results are cached with 24-hour TTL
- **Indexes**: Secondary indexes on `search_query` and `search_type` for flexible queries

### Scalability

- **Horizontal Scaling**: Add more Cassandra nodes as search volume grows
- **Replication**: Configure replication factor based on availability requirements
- **TTL**: Automatic expiration of cached results reduces storage growth

## Testing

Unit tests are available in `tests/backend/unit/services/test_cassandra_service.py`:

```bash
# Run all Cassandra service tests
docker exec migration_backend pytest tests/backend/unit/services/test_cassandra_service.py -v

# Run with coverage
docker exec migration_backend pytest tests/backend/unit/services/test_cassandra_service.py \
  --cov=app.services.cassandra_service \
  --cov-report=term-missing \
  -v
```

## Troubleshooting

### Connection Issues

1. **Check Cassandra is running**: `docker ps | grep cassandra`
2. **Verify connection string**: Check `CASSANDRA_CONTACT_POINTS` and `CASSANDRA_PORT`
3. **Check authentication**: Verify `CASSANDRA_USERNAME` and `CASSANDRA_PASSWORD` if enabled

### Schema Issues

1. **Keyspace not created**: The service auto-creates keyspace on first initialization
2. **Tables not created**: The service auto-creates tables on first initialization
3. **Index errors**: Check Cassandra logs for index creation issues

### Performance Issues

1. **Slow writes**: Check Cassandra node health and network latency
2. **Slow reads**: Verify partition key usage (queries should include partition key)
3. **High memory usage**: Monitor cache size and adjust TTL if needed

## Future Enhancements

- [ ] Real-time search suggestions based on history
- [ ] Anomaly detection for unusual search patterns
- [ ] Cross-user analytics (aggregated, anonymized)
- [ ] Search trend analysis
- [ ] Integration with recommendation engine

