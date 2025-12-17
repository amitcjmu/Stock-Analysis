"""
Stock Data API Service - Integrates with Yahoo Finance for real stock data
Supports both US stocks and Indian stocks (BSE/NSE)
"""

import logging
from typing import Any, Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)

# Try to import yfinance, fallback to mock if not available
try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available. Install with: pip install yfinance")


class StockDataAPIService:
    """Service for fetching real stock data from Yahoo Finance
    Supports:
    - US stocks (e.g., AAPL, MSFT)
    - Indian NSE stocks (e.g., RELIANCE.NS, TCS.NS)
    - Indian BSE stocks (e.g., RELIANCE.BO, TCS.BO)
    """

    def __init__(self):
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance not available - using mock data")

        # Indian company name to ticker mapping (BSE/NSE)
        self.indian_companies = {
            # Major Indian Companies - NSE
            "RELIANCE": "RELIANCE.NS",
            "RELIANCE INDUSTRIES": "RELIANCE.NS",
            "TCS": "TCS.NS",
            "TATA CONSULTANCY": "TCS.NS",
            "HDFC BANK": "HDFCBANK.NS",
            "HDFC": "HDFCBANK.NS",
            "INFOSYS": "INFY.NS",
            "ICICI BANK": "ICICIBANK.NS",
            "ICICI": "ICICIBANK.NS",
            "HINDUNILVR": "HINDUNILVR.NS",
            "HINDUSTAN UNILEVER": "HINDUNILVR.NS",
            "HUL": "HINDUNILVR.NS",
            "SBIN": "SBIN.NS",
            "STATE BANK": "SBIN.NS",
            "SBI": "SBIN.NS",
            "BHARTI AIRTEL": "BHARTIARTL.NS",
            "AIRTEL": "BHARTIARTL.NS",
            "BAJFINANCE": "BAJFINANCE.NS",
            "BAJAJ FINANCE": "BAJFINANCE.NS",
            "LIC": "LICI.NS",
            "LIFE INSURANCE": "LICI.NS",
            "ITC": "ITC.NS",
            "SUN PHARMA": "SUNPHARMA.NS",
            "SUN PHARMACEUTICAL": "SUNPHARMA.NS",
            "AXIS BANK": "AXISBANK.NS",
            "MARUTI": "MARUTI.NS",
            "MARUTI SUZUKI": "MARUTI.NS",
            "WIPRO": "WIPRO.NS",
            "NTPC": "NTPC.NS",
            "ONGC": "ONGC.NS",
            "OIL AND NATURAL GAS": "ONGC.NS",
            "POWERGRID": "POWERGRID.NS",
            "POWER GRID": "POWERGRID.NS",
            "NESTLE": "NESTLEIND.NS",
            "NESTLE INDIA": "NESTLEIND.NS",
            "ULTRACEMCO": "ULTRACEMCO.NS",
            "ULTRATECH CEMENT": "ULTRACEMCO.NS",
            "TITAN": "TITAN.NS",
            "TATA STEEL": "TATASTEEL.NS",
            "JSW STEEL": "JSWSTEEL.NS",
            "ASIAN PAINTS": "ASIANPAINT.NS",
            "HCL TECH": "HCLTECH.NS",
            "HCL TECHNOLOGIES": "HCLTECH.NS",
            "M&M": "M&M.NS",
            "MAHINDRA": "M&M.NS",
            "MAHINDRA AND MAHINDRA": "M&M.NS",
            "TECH MAHINDRA": "TECHM.NS",
            "ADANI PORTS": "ADANIPORTS.NS",
            "ADANI ENTERPRISES": "ADANIENT.NS",
            "TATA MOTORS": "TATAMOTORS.NS",
            "DIVIS LAB": "DIVISLAB.NS",
            "DIVIS LABORATORIES": "DIVISLAB.NS",
            "BAJAJ FINSERV": "BAJAJFINSV.NS",
            "GRASIM": "GRASIM.NS",
            "LT": "LT.NS",
            "LARSEN": "LT.NS",
            "LARSEN AND TOUBRO": "LT.NS",
            "L&T": "LT.NS",
            # Additional Indian Companies
            # Note: Apollo Micro Systems may not be available in Yahoo Finance
            "APOLLO TYRES": "APOLLOTYRE.NS",
            "APOLLO HOSPITALS": "APOLLOHOSP.NS",
            "APOLLO": "APOLLOHOSP.NS",  # Default to Apollo Hospitals if ambiguous
            "INDUSIND BANK": "INDUSINDBK.NS",
            "KOTAK MAHINDRA": "KOTAKBANK.NS",
            "KOTAK BANK": "KOTAKBANK.NS",
            "KOTAK": "KOTAKBANK.NS",
            "SHREECEM": "SHREECEM.NS",
            "SHREE CEMENT": "SHREECEM.NS",
            "CIPLA": "CIPLA.NS",
            "DR REDDYS": "DRREDDY.NS",
            "DR REDDY": "DRREDDY.NS",
            "EICHER MOTORS": "EICHERMOT.NS",
            "EICHER": "EICHERMOT.NS",
            "HERO MOTOCORP": "HEROMOTOCO.NS",
            "HERO": "HEROMOTOCO.NS",
            "BAJAJ AUTO": "BAJAJ-AUTO.NS",
            "BHARAT PETROLEUM": "BPCL.NS",
            "BPCL": "BPCL.NS",
            "INDIAN OIL": "IOC.NS",
            "IOC": "IOC.NS",
            "GAIL": "GAIL.NS",
            "COAL INDIA": "COALINDIA.NS",
            "HINDALCO": "HINDALCO.NS",
            "VEDANTA": "VEDL.NS",
            "JINDAL STEEL": "JINDALSTEL.NS",
            "SAIL": "SAIL.NS",
            "NATIONAL ALUMINIUM": "NATIONALUM.NS",
            "NMDC": "NMDC.NS",
            "PNB": "PNB.NS",
            "PUNJAB NATIONAL BANK": "PNB.NS",
            "BANK OF BARODA": "BANKBARODA.NS",
            "BOB": "BANKBARODA.NS",
            "CANARA BANK": "CANBK.NS",
            "UNION BANK": "UNIONBANK.NS",
            "IDBI BANK": "IDBI.NS",
            "YES BANK": "YESBANK.NS",
            "FEDERAL BANK": "FEDERALBNK.NS",
            "RBL BANK": "RBLBANK.NS",
            "BANDHAN BANK": "BANDHANBNK.NS",
            "AU SMALL FINANCE": "AUBANK.NS",
            "PERSISTENT": "PERSISTENT.NS",
            "PERSISTENT SYSTEMS": "PERSISTENT.NS",
            "LTI MINDTREE": "LTIM.NS",
            "LTIM": "LTIM.NS",
            "COFORGE": "COFORGE.NS",
            "MINDTREE": "MINDTREE.NS",
            "TATA POWER": "TATAPOWER.NS",
            "ADANI GREEN": "ADANIGREEN.NS",
            "ADANI TRANSMISSION": "ADANITRANS.NS",
        }

        # BSE Sensex and NSE Nifty indices
        self.indian_indices = {
            "SENSEX": "^BSESN",
            "BSE SENSEX": "^BSESN",
            "BSE": "^BSESN",
            "NIFTY": "^NSEI",
            "NIFTY 50": "^NSEI",
            "NSE NIFTY": "^NSEI",
            "NSE": "^NSEI",
            "NIFTY BANK": "^NSEBANK",
            "BANK NIFTY": "^NSEBANK",
        }

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to handle Indian stocks and company names"""
        symbol_upper = symbol.upper().strip()

        # Remove common suffixes like "LIMITED", "LTD", "INC", "CORPORATION", etc.
        cleaned_symbol = symbol_upper
        for suffix in [
            " LIMITED",
            " LTD",
            " INC",
            " CORPORATION",
            " CORP",
            " COMPANY",
            " CO",
        ]:
            if cleaned_symbol.endswith(suffix):
                cleaned_symbol = cleaned_symbol[: -len(suffix)].strip()

        # Check if already has exchange suffix
        if symbol_upper.endswith(".NS") or symbol_upper.endswith(".BO"):
            return symbol_upper

        # Check Indian indices
        if symbol_upper in self.indian_indices:
            return self.indian_indices[symbol_upper]
        if cleaned_symbol in self.indian_indices:
            return self.indian_indices[cleaned_symbol]

        # Check Indian companies (exact match first)
        if symbol_upper in self.indian_companies:
            return self.indian_companies[symbol_upper]
        if cleaned_symbol in self.indian_companies:
            return self.indian_companies[cleaned_symbol]

        # Check for partial matches (more flexible matching)
        # Try to find the best match by checking if query contains company name or vice versa
        best_match = None
        best_match_length = 0

        for company_name, ticker in self.indian_companies.items():
            # Check if query is contained in company name or company name is contained in query
            if cleaned_symbol in company_name or company_name in cleaned_symbol:
                # Prefer longer matches (more specific)
                if len(company_name) > best_match_length:
                    best_match = ticker
                    best_match_length = len(company_name)

        if best_match:
            logger.info(f"Matched '{symbol_upper}' to '{best_match}' via partial match")
            return best_match

        # Default: assume US stock or return as-is
        return symbol_upper

    async def search_stocks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for stocks by symbol or company name.
        Supports US stocks and Indian stocks (BSE/NSE).
        Uses Yahoo Finance ticker search.
        """
        if not YFINANCE_AVAILABLE:
            return await self._mock_search_stocks(query, limit)

        try:
            # Run synchronous yfinance calls in executor
            loop = asyncio.get_event_loop()
            stocks = await loop.run_in_executor(
                None, self._search_stocks_sync, query, limit
            )
            return stocks
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return await self._mock_search_stocks(query, limit)

    def _search_stocks_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Synchronous search implementation"""
        stocks = []
        query_upper = query.upper().strip()

        # Map common US company names to ticker symbols
        us_company_to_ticker = {
            "APPLE": "AAPL",
            "MICROSOFT": "MSFT",
            "GOOGLE": "GOOGL",
            "ALPHABET": "GOOGL",
            "AMAZON": "AMZN",
            "TESLA": "TSLA",
            "META": "META",
            "FACEBOOK": "META",
            "NVIDIA": "NVDA",
            "JPMORGAN": "JPM",
            "JPMORGAN CHASE": "JPM",
            "VISA": "V",
            "JOHNSON & JOHNSON": "JNJ",
            "JOHNSON AND JOHNSON": "JNJ",
            "WALMART": "WMT",
            "PROCTER & GAMBLE": "PG",
            "MASTERCARD": "MA",
            "UNITEDHEALTH": "UNH",
            "HOME DEPOT": "HD",
            "DISNEY": "DIS",
            "PAYPAL": "PYPL",
            "BANK OF AMERICA": "BAC",
            "VERIZON": "VZ",
            "ADOBE": "ADBE",
            "COMCAST": "CMCSA",
            "NETFLIX": "NFLX",
            "COCA COLA": "KO",
            "NIKE": "NKE",
            "MERCK": "MRK",
        }

        # Normalize symbol (handles both US and Indian stocks)
        search_symbol = self._normalize_symbol(query_upper)

        # If normalization didn't change it, check US companies
        if search_symbol == query_upper and query_upper in us_company_to_ticker:
            logger.info(
                f"Mapping US company name '{query_upper}' to ticker '{us_company_to_ticker[query_upper]}'"
            )
            search_symbol = us_company_to_ticker[query_upper]

        # Try direct ticker lookup first
        try:
            ticker = yf.Ticker(search_symbol)
            info = ticker.info
            if info and "symbol" in info and "error" not in info:
                stock_data = self._format_stock_data(info, ticker)
                if stock_data:
                    stocks.append(stock_data)
            elif info and "error" in info:
                error_desc = (
                    info.get("error", {}).get("description", "Unknown error")
                    if isinstance(info.get("error"), dict)
                    else str(info.get("error", "Unknown error"))
                )
                # Only log as warning if it's not a "Not Found" error (which is expected for some searches)
                if "not found" not in error_desc.lower() and "404" not in str(
                    error_desc
                ):
                    logger.warning(
                        f"Yahoo Finance error for '{search_symbol}': {error_desc}"
                    )
                else:
                    logger.debug(
                        f"Stock not found in Yahoo Finance for '{search_symbol}': {error_desc}"
                    )
        except Exception as e:
            # Suppress yfinance HTTP 404 errors as they're expected for unknown symbols
            if "404" not in str(e) and "not found" not in str(e).lower():
                logger.debug(f"Direct ticker lookup failed for {search_symbol}: {e}")

        # If we have results, return them
        if stocks:
            return stocks[:limit]

        # For broader search, try common tickers
        # Note: Yahoo Finance doesn't have a direct search API, so we try common patterns
        common_tickers = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "JPM",
            "V",
            "JNJ",
            "WMT",
            "PG",
            "MA",
            "UNH",
            "HD",
            "DIS",
            "PYPL",
            "BAC",
            "VZ",
            "ADBE",
            "CMCSA",
            "NFLX",
            "KO",
            "NKE",
            "MRK",
        ]

        for ticker_symbol in common_tickers:
            if query_upper in ticker_symbol or query_upper in ticker_symbol:
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    info = ticker.info
                    if info and "symbol" in info:
                        stock_data = self._format_stock_data(info, ticker)
                        if (
                            stock_data
                            and query_upper in stock_data.get("symbol", "").upper()
                        ):
                            stocks.append(stock_data)
                            if len(stocks) >= limit:
                                break
                except Exception as e:
                    logger.debug(f"Error fetching {ticker_symbol}: {e}")
                    continue

        return stocks[:limit]

    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock data by symbol"""
        if not YFINANCE_AVAILABLE:
            return await self._mock_get_stock_data(symbol)

        try:
            loop = asyncio.get_event_loop()
            stock_data = await loop.run_in_executor(
                None, self._get_stock_data_sync, symbol
            )
            return stock_data
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            return await self._mock_get_stock_data(symbol)

    def _get_stock_data_sync(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Synchronous stock data fetch - supports US and Indian stocks"""
        try:
            # Normalize symbol (handles both US and Indian stocks)
            symbol_normalized = self._normalize_symbol(symbol)

            logger.info(f"Fetching stock data for '{symbol}' -> '{symbol_normalized}'")

            ticker = yf.Ticker(symbol_normalized)
            info = ticker.info

            # Check if we got valid data
            if not info:
                logger.warning(f"No data returned for symbol {symbol_normalized}")
                return None

            # Check for error in response (yfinance sometimes returns error in info)
            if "error" in info or "symbol" not in info:
                error_msg = (
                    info.get("error", {}).get("description", "No symbol in response")
                    if isinstance(info.get("error"), dict)
                    else info.get("error", "No symbol in response")
                )
                logger.warning(
                    f"Invalid symbol or error for {symbol_normalized}: {error_msg}"
                )
                # Try to suggest alternative if it's a company name search
                if symbol != symbol_normalized:
                    logger.info(
                        f"Original search was '{symbol}', normalized to '{symbol_normalized}' but not found"
                    )
                return None

            return self._format_stock_data(info, ticker, symbol_normalized)
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None

    def _format_stock_data(
        self, info: Dict, ticker: Any, symbol: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Format Yahoo Finance data to our stock model format
        Supports both US and Indian stocks
        """
        try:
            # Get current price from history or info
            current_price = None
            previous_close = None

            try:
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
                    if len(hist) > 1:
                        previous_close = float(hist["Close"].iloc[-2])
            except Exception as e:
                logger.debug(f"Error fetching history: {e}")

            # Fallback to info if history not available
            if current_price is None:
                current_price = (
                    info.get("currentPrice")
                    or info.get("regularMarketPrice")
                    or info.get("regularMarketLastPrice")
                )
            if previous_close is None:
                previous_close = info.get("previousClose") or info.get(
                    "regularMarketPreviousClose"
                )

            # Calculate price change
            price_change = None
            price_change_percent = None
            if current_price and previous_close:
                price_change = current_price - previous_close
                price_change_percent = (
                    (price_change / previous_close) * 100 if previous_close else 0
                )

            # Extract symbol and determine exchange
            symbol_raw = info.get("symbol", symbol or "")
            exchange = info.get("exchange")

            # Determine if it's an Indian stock
            is_indian = False
            if symbol_raw.endswith(".NS"):
                exchange = exchange or "NSE"
                is_indian = True
                symbol_raw = symbol_raw.replace(".NS", "")
            elif symbol_raw.endswith(".BO"):
                exchange = exchange or "BSE"
                is_indian = True
                symbol_raw = symbol_raw.replace(".BO", "")

            # Get currency (INR for Indian stocks, USD for US)
            currency = info.get("currency", "INR" if is_indian else "USD")
            country = info.get("country", "India" if is_indian else "United States")

            return {
                "symbol": symbol_raw.upper(),
                "company_name": info.get("longName")
                or info.get("shortName")
                or info.get("symbol", symbol_raw),
                "exchange": exchange,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "current_price": float(current_price) if current_price else None,
                "previous_close": float(previous_close) if previous_close else None,
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "price_change": (
                    float(price_change) if price_change is not None else None
                ),
                "price_change_percent": (
                    float(price_change_percent)
                    if price_change_percent is not None
                    else None
                ),
                "currency": currency,
                "metadata": {
                    "currency": currency,
                    "country": country,
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary"),
                    "employees": info.get("fullTimeEmployees"),
                    "dividend_yield": info.get("dividendYield"),
                    "pe_ratio": info.get("trailingPE"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                    "is_indian_stock": is_indian,
                    "yfinance_symbol": info.get("symbol", symbol),
                },
            }
        except Exception as e:
            logger.error(f"Error formatting stock data: {e}")
            return None

    async def get_historical_prices(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical price data for a stock.

        Args:
            symbol: Stock symbol
            period: Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        """
        if not YFINANCE_AVAILABLE:
            return await self._mock_historical_prices(symbol, period)

        try:
            loop = asyncio.get_event_loop()
            prices = await loop.run_in_executor(
                None, self._get_historical_prices_sync, symbol, period, interval
            )
            return prices
        except Exception as e:
            logger.error(f"Error getting historical prices for {symbol}: {e}")
            return await self._mock_historical_prices(symbol, period)

    def _get_historical_prices_sync(
        self, symbol: str, period: str, interval: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Synchronous historical price fetch - supports US and Indian stocks"""
        try:
            # Normalize symbol to handle Indian stocks
            symbol_normalized = self._normalize_symbol(symbol)
            logger.info(
                f"Fetching historical prices for '{symbol}' -> '{symbol_normalized}'"
            )

            ticker = yf.Ticker(symbol_normalized)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"No historical data found for {symbol_normalized}")
                return None

            prices = []
            for date, row in hist.iterrows():
                prices.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "timestamp": int(date.timestamp()),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]) if "Volume" in row else None,
                    }
                )

            return prices
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return None

    # Mock data methods for fallback
    async def _mock_search_stocks(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mock search results"""
        mock_stocks = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "current_price": 175.50,
                "previous_close": 174.20,
                "market_cap": 2800000000000,
                "volume": 50000000,
                "price_change": 1.30,
                "price_change_percent": 0.75,
            },
            {
                "symbol": "MSFT",
                "company_name": "Microsoft Corporation",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Software",
                "current_price": 380.25,
                "previous_close": 378.90,
                "market_cap": 2800000000000,
                "volume": 25000000,
                "price_change": 1.35,
                "price_change_percent": 0.36,
            },
        ]
        query_upper = query.upper()
        filtered = [
            stock
            for stock in mock_stocks
            if query_upper in stock["symbol"]
            or query_upper in stock["company_name"].upper()
        ]
        return filtered[:limit]

    async def _mock_get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Mock stock data"""
        stocks = await self._mock_search_stocks(symbol, 1)
        return stocks[0] if stocks else None

    async def _mock_historical_prices(
        self, symbol: str, period: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Mock historical prices"""
        import random
        from datetime import datetime, timedelta

        days = 30 if period == "1mo" else 365 if period == "1y" else 90
        base_price = 100.0
        prices = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            change = random.uniform(-2, 2)
            base_price += change
            prices.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "timestamp": int(date.timestamp()),
                    "open": base_price,
                    "high": base_price + random.uniform(0, 2),
                    "low": base_price - random.uniform(0, 2),
                    "close": base_price + random.uniform(-0.5, 0.5),
                    "volume": random.randint(1000000, 10000000),
                }
            )

        return prices
