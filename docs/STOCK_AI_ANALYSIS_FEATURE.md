# Stock AI Analysis Feature - File Documentation

## Overview
The Stock AI Analysis feature provides comprehensive stock market analysis using AI/LLM agents. It integrates with Yahoo Finance for real-time stock data and uses LLM models (Llama 4 Maverick) to generate detailed stock analysis including technical analysis, fundamental analysis, risk assessment, and investment recommendations.

## Architecture

### Flow Diagram
```
User Request → API Endpoint → Stock Service → Stock Data API (Yahoo Finance)
                                              ↓
                                    Stock Analysis Agent → Multi Model Service (LLM)
                                              ↓
                                    Stock Analysis Model (Database)
```

## Files Added/Modified

### 1. Backend Models

#### `backend/app/models/stock.py`
**Purpose**: Database models for stocks and stock analysis

**Key Components**:
- **`Stock` Model**: Stores stock information
  - Fields: symbol, company_name, exchange, sector, industry, current_price, previous_close, market_cap, volume, price_change, price_change_percent, currency, stock_metadata
  - Multi-tenant support: client_account_id, engagement_id, user_id
  - Relationships: One-to-many with StockAnalysis

- **`StockAnalysis` Model**: Stores LLM-generated analysis
  - Fields:
    - Analysis content: summary, key_insights, technical_analysis, fundamental_analysis, risk_assessment, recommendations, price_targets
    - LLM metadata: llm_model, llm_prompt, llm_response, confidence_score
    - Analysis metadata: analysis_type, analysis_date, is_latest
  - Multi-tenant support: client_account_id, engagement_id, user_id
  - Relationships: Many-to-one with Stock

**Key Features**:
- JSONB fields for flexible data storage
- Timestamps for tracking creation and updates
- Multi-tenant isolation

#### `backend/app/models/watchlist.py`
**Purpose**: Model for user watchlists

**Key Components**:
- **`Watchlist` Model**: Tracks stocks in user watchlists
  - Fields: stock_symbol, notes, added_at
  - Multi-tenant support: client_account_id, engagement_id, user_id
  - Relationships: Many-to-one with Stock

### 2. Backend Services

#### `backend/app/services/stock_data_api.py`
**Purpose**: Integration with Yahoo Finance API for real-time stock data

**Key Features**:
- Supports US stocks (NASDAQ, NYSE)
- Supports Indian stocks (NSE, BSE)
- Company name to ticker mapping for both US and Indian markets
- Historical price data fetching
- Error handling and fallback mechanisms

**Key Methods**:
- `search_stocks(query, limit)`: Search stocks by symbol or company name
- `get_stock_data(symbol)`: Get detailed stock information
- `get_historical_prices(symbol, period, interval)`: Get historical price data
- `_normalize_symbol(symbol)`: Normalize company names to ticker symbols

**Company Mappings**:
- US companies: Apple (AAPL), Microsoft (MSFT), Google (GOOGL), etc.
- Indian companies: Reliance (RELIANCE.NS), TCS (TCS.NS), Infosys (INFY.NS), etc.
- Indian indices: Sensex (^BSESN), Nifty (^NSEI), Bank Nifty (^NSEBANK)

#### `backend/app/services/stock_service.py`
**Purpose**: Business logic layer for stock operations

**Key Methods**:
- `search_stocks(query, limit)`: Search stocks (checks DB first, then API)
- `get_stock_by_symbol(symbol)`: Get stock by symbol
- `save_stock(stock_data)`: Save or update stock in database
- `save_stock_analysis(stock_id, analysis_data)`: Save LLM analysis
- `get_stock_analysis(stock_id)`: Get latest analysis for a stock
- `get_historical_prices(symbol, period, interval)`: Get historical prices
- `add_to_watchlist(symbol, notes)`: Add stock to watchlist
- `remove_from_watchlist(symbol)`: Remove stock from watchlist
- `get_watchlist()`: Get user's watchlist
- `compare_stocks(symbols)`: Compare multiple stocks

**Key Features**:
- Database-first approach with API fallback
- Multi-tenant data isolation
- Automatic stock data updates

#### `backend/app/services/stock_analysis_agent.py`
**Purpose**: AI/LLM agent for generating comprehensive stock analysis

**Key Components**:
- **`StockAnalysisAgent` Class**: Main agent class

**Key Methods**:
- `analyze_stock(stock_symbol)`: Main method to generate analysis
  1. Fetches stock data
  2. Creates comprehensive analysis prompt
  3. Calls LLM via multi_model_service
  4. Parses LLM response into structured format
  5. Saves analysis to database

- `_create_analysis_prompt(stock_data)`: Creates detailed prompt for LLM
  - Includes: symbol, company name, exchange, sector, industry, current price, previous close, price change, market cap, volume
  - Requests: summary, key insights, technical analysis, fundamental analysis, risk assessment, recommendations, price targets

- `_parse_llm_response(response, stock_data)`: Parses LLM JSON response
  - Extracts structured analysis data
  - Handles JSON parsing errors with fallback
  - Structures data for database storage

**LLM Integration**:
- Uses `multi_model_service` with `TaskComplexity.AGENTIC`
- Model: Llama 4 Maverick (for complex analysis tasks)
- Task type: "analysis"

**Analysis Structure**:
```json
{
  "summary": "Executive summary",
  "key_insights": ["insight1", "insight2", ...],
  "technical_analysis": {
    "trend": "bullish/bearish/neutral",
    "support_levels": [price1, price2],
    "resistance_levels": [price1, price2],
    "indicators": {...}
  },
  "fundamental_analysis": {
    "valuation": "overvalued/undervalued/fair",
    "financial_health": "strong/moderate/weak",
    "growth_prospects": "positive/neutral/negative",
    "competitive_position": "strong/moderate/weak"
  },
  "risk_assessment": {
    "overall_risk": "low/medium/high",
    "key_risks": ["risk1", "risk2"],
    "volatility": "low/medium/high"
  },
  "recommendations": {
    "action": "buy/hold/sell",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed reasoning"
  },
  "price_targets": {
    "short_term_1m": price,
    "medium_term_3m": price,
    "long_term_12m": price,
    "target_basis": "Explanation"
  }
}
```

### 3. Backend API Endpoints

#### `backend/app/api/v1/endpoints/stock/stock_routes.py`
**Purpose**: FastAPI routes for stock operations

**Endpoints**:

1. **`GET /api/v1/stock/stocks/search`**
   - Query params: `q` (search query), `limit` (max results)
   - Returns: List of matching stocks
   - Response: `StockSearchResponse`

2. **`GET /api/v1/stock/stocks/{symbol}`**
   - Path param: `symbol` (stock symbol)
   - Returns: Detailed stock information
   - Response: `StockDetailResponse`

3. **`POST /api/v1/stock/stocks/analyze`**
   - Body: `StockAnalysisRequest` (symbol)
   - Returns: Stock data + AI-generated analysis
   - Response: `StockAnalysisResponse`
   - **This is the main AI analysis endpoint**

4. **`GET /api/v1/stock/stocks/{symbol}/historical`**
   - Path param: `symbol`
   - Query params: `period` (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max), `interval` (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
   - Returns: Historical price data

5. **`GET /api/v1/stock/stocks/{stock_id}/analysis`**
   - Path param: `stock_id` (UUID)
   - Returns: Latest analysis for the stock

6. **`GET /api/v1/stock/stocks/watchlist`**
   - Returns: User's watchlist

7. **`POST /api/v1/stock/stocks/watchlist`**
   - Body: `symbol`, `notes` (optional)
   - Adds stock to watchlist

8. **`DELETE /api/v1/stock/stocks/watchlist/{symbol}`**
   - Path param: `symbol`
   - Removes stock from watchlist

9. **`GET /api/v1/stock/stocks/compare`**
   - Query params: `symbols` (comma-separated list)
   - Returns: Comparison of multiple stocks

**Request/Response Models**:
- `StockSearchResponse`: success, stocks[], count, query
- `StockDetailResponse`: success, stock{}
- `StockAnalysisRequest`: symbol
- `StockAnalysisResponse`: success, stock{}, analysis{}, message

### 4. Database Migrations

#### `backend/alembic/versions/XXX_create_stock_tables.py`
**Purpose**: Creates stock and stock_analyses tables

**Tables Created**:
- `migration.stocks`: Stock information table
- `migration.stock_analyses`: Stock analysis table

#### `backend/alembic/versions/157_create_watchlist_table.py`
**Purpose**: Creates watchlist table

**Tables Created**:
- `migration.watchlist`: User watchlist table

### 5. Router Registration

#### `backend/app/api/v1/router_registry/core_routers.py`
**Modified**: Added stock router registration
```python
from app.api.v1.endpoints.stock.stock_routes import router as stock_router
api_router.include_router(stock_router, prefix="/stock/stocks")
```

### 6. Model Registration

#### `backend/app/models/__init__.py`
**Modified**: Added Stock and StockAnalysis imports
```python
from app.models.stock import Stock, StockAnalysis
from app.models.watchlist import Watchlist
```

#### `backend/alembic/env.py`
**Modified**: Added Stock, StockAnalysis, and Watchlist imports for migrations

## AI/LLM Integration Details

### LLM Service Used
- **Service**: `multi_model_service`
- **Model**: Llama 4 Maverick (via CrewAI)
- **Task Complexity**: `TaskComplexity.AGENTIC`
- **Task Type**: "analysis"

### Analysis Prompt Structure
The prompt includes:
1. Stock information (symbol, company, exchange, sector, industry)
2. Current market data (price, change, market cap, volume)
3. Request for structured JSON analysis with:
   - Executive summary
   - Key insights
   - Technical analysis (trend, support/resistance, indicators)
   - Fundamental analysis (valuation, financial health, growth, competitive position)
   - Risk assessment (overall risk, key risks, volatility)
   - Recommendations (action, confidence, reasoning)
   - Price targets (short/medium/long term)

### Response Parsing
- Extracts JSON from LLM response
- Handles markdown code blocks
- Fallback to basic analysis if JSON parsing fails
- Stores full LLM response for audit trail

## Data Flow

1. **Stock Search**:
   ```
   User → API → StockService → StockDataAPIService → Yahoo Finance
   ```

2. **Stock Analysis**:
   ```
   User → API → StockAnalysisAgent → StockService → StockDataAPIService
                                              ↓
                                    MultiModelService → LLM (Llama 4 Maverick)
                                              ↓
                                    Parse Response → Save to Database
   ```

3. **Historical Data**:
   ```
   User → API → StockService → StockDataAPIService → Yahoo Finance
   ```

## Multi-Tenant Support

All models and services support multi-tenant isolation:
- `client_account_id`: Client account identifier
- `engagement_id`: Engagement identifier
- `user_id`: User identifier

All database queries are scoped to these identifiers.

## Error Handling

- Graceful fallbacks for API failures
- JSON parsing error handling with fallback analysis
- Comprehensive error logging
- User-friendly error messages

## Dependencies

- `yfinance`: Yahoo Finance API integration
- `sqlalchemy`: Database ORM
- `fastapi`: API framework
- `multi_model_service`: LLM service integration
- `pydantic`: Data validation

## Testing

To test the AI analysis:
```bash
# Search for a stock
curl -X GET "http://localhost:8000/api/v1/stock/stocks/search?q=TCS" \
  -H "X-Client-Account-ID: <uuid>" \
  -H "X-Engagement-ID: <uuid>" \
  -H "X-User-ID: <user_id>"

# Analyze a stock (AI analysis)
curl -X POST "http://localhost:8000/api/v1/stock/stocks/analyze" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: <uuid>" \
  -H "X-Engagement-ID: <uuid>" \
  -H "X-User-ID: <user_id>" \
  -d '{"symbol": "TCS"}'
```

## Future Enhancements

- Real-time price updates
- Portfolio management
- Alert system for price changes
- Advanced charting
- News sentiment analysis
- Earnings calendar integration
- Options chain analysis

