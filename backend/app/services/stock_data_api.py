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
            "HCLTECH": "HCLTECH.NS",
            "HCL": "HCLTECH.NS",
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
            "APOLLO TYRES": "APOLLOTYRE.NS",
            "APOLLO HOSPITALS": "APOLLOHOSP.NS",
            "APOLLO": "APOLLO.NS",  # Default to Apollo Micro Systems Ltd
            "APOLLO MICRO SYSTEMS": "APOLLO.NS",
            "APOLLO MICRO": "APOLLO.NS",
            "APOLLO MICRO SYSTEMS LTD": "APOLLO.NS",
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
            "VA TECH WABAG": "WABAG.NS",
            "VA TECH": "WABAG.NS",
            "WABAG": "WABAG.NS",
            "VA TECH WABAG LTD": "WABAG.NS",
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

    def _clean_symbol_suffixes(self, symbol: str) -> str:
        """Remove common company suffixes from symbol"""
        cleaned = symbol
        suffixes = [
            " LIMITED",
            " LTD",
            " INC",
            " CORPORATION",
            " CORP",
            " COMPANY",
            " CO",
        ]
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()
        return cleaned

    def _has_exchange_suffix(self, symbol: str) -> bool:
        """Check if symbol already has exchange suffix (.NS or .BO)"""
        return symbol.endswith(".NS") or symbol.endswith(".BO")

    def _check_indian_indices(self, symbol: str, cleaned: str) -> Optional[str]:
        """Check if symbol matches Indian indices"""
        if symbol in self.indian_indices:
            return self.indian_indices[symbol]
        if cleaned in self.indian_indices:
            return self.indian_indices[cleaned]
        return None

    def _check_exact_company_match(self, symbol: str, cleaned: str) -> Optional[str]:
        """Check for exact match in Indian companies mapping"""
        if symbol in self.indian_companies:
            return self.indian_companies[symbol]
        if cleaned in self.indian_companies:
            return self.indian_companies[cleaned]
        return None

    def _calculate_match_score(self, query: str, company_name: str) -> Optional[int]:
        """Calculate match score between query and company name"""
        # Skip very short company names to avoid false matches
        if len(company_name) < 3:
            return None

        # Check if there's any overlap
        if query not in company_name and company_name not in query:
            return None

        # Base score is length of company name (prefer longer matches)
        score = len(company_name)

        # Boost score for exact and word-boundary matches
        if query == company_name:
            score += 1000  # Exact match gets highest priority
        elif query.startswith(company_name) or query.endswith(company_name):
            score += 100  # Word boundary match
        elif company_name.startswith(query) or company_name.endswith(query):
            score += 50  # Partial word match

        return score

    def _find_partial_company_match(self, cleaned_symbol: str) -> Optional[str]:
        """Find best partial match in Indian companies"""
        best_match = None
        best_score = 0

        for company_name, ticker in self.indian_companies.items():
            score = self._calculate_match_score(cleaned_symbol, company_name)
            if score and score > best_score:
                best_match = ticker
                best_score = score

        if best_match:
            logger.info(
                f"Matched '{cleaned_symbol}' to '{best_match}' via partial match (score: {best_score})"
            )
        return best_match

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to handle Indian stocks and company names"""
        symbol_upper = symbol.upper().strip()
        cleaned_symbol = self._clean_symbol_suffixes(symbol_upper)

        # Check if already has exchange suffix
        if self._has_exchange_suffix(symbol_upper):
            return symbol_upper

        # Check Indian indices
        index_match = self._check_indian_indices(symbol_upper, cleaned_symbol)
        if index_match:
            return index_match

        # Check exact company match
        exact_match = self._check_exact_company_match(symbol_upper, cleaned_symbol)
        if exact_match:
            return exact_match

        # Check for partial matches
        partial_match = self._find_partial_company_match(cleaned_symbol)
        if partial_match:
            return partial_match

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

    def _get_us_company_to_ticker_map(self) -> Dict[str, str]:
        """Get mapping of US company names to ticker symbols."""
        return {
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

    def _try_direct_ticker_lookup(self, search_symbol: str) -> Optional[Dict[str, Any]]:
        """Try to get stock data by direct ticker lookup."""
        try:
            ticker = yf.Ticker(search_symbol)
            info = ticker.info
            if info and "symbol" in info and "error" not in info:
                stock_data = self._format_stock_data(info, ticker)
                if stock_data:
                    return stock_data
            elif info and "error" in info:
                error_desc = (
                    info.get("error", {}).get("description", "Unknown error")
                    if isinstance(info.get("error"), dict)
                    else str(info.get("error", "Unknown error"))
                )
                # Only log as warning if it's not a "Not Found" error
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
        return None

    def _search_common_tickers(
        self, query_upper: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search through common tickers for matches."""
        stocks = []
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
            if query_upper in ticker_symbol:
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

        return stocks

    def _search_stocks_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Synchronous search implementation"""
        query_upper = query.upper().strip()

        # Normalize symbol (handles both US and Indian stocks)
        search_symbol = self._normalize_symbol(query_upper)

        # If normalization didn't change it, check US companies
        us_company_to_ticker = self._get_us_company_to_ticker_map()
        if search_symbol == query_upper and query_upper in us_company_to_ticker:
            logger.info(
                f"Mapping US company name '{query_upper}' to ticker '{us_company_to_ticker[query_upper]}'"
            )
            search_symbol = us_company_to_ticker[query_upper]

        # Try direct ticker lookup first
        stock_data = self._try_direct_ticker_lookup(search_symbol)
        if stock_data:
            return [stock_data][:limit]

        # For broader search, try common tickers
        stocks = self._search_common_tickers(query_upper, limit)
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

    def _try_fast_info_price(self, ticker: Any) -> Optional[float]:
        """Try to get price from fast_info."""
        try:
            fast_info = ticker.fast_info
            if hasattr(fast_info, "lastPrice") and fast_info.lastPrice:
                price = float(fast_info.lastPrice)
                logger.debug(f"Got price from fast_info: {price}")
                return price
        except Exception as e:
            logger.debug(f"fast_info not available: {e}")
        return None

    def _try_intraday_price(self, ticker: Any, interval: str) -> Optional[float]:
        """Try to get price from intraday history."""
        try:
            hist_intraday = ticker.history(period="1d", interval=interval)
            if not hist_intraday.empty:
                price = float(hist_intraday["Close"].iloc[-1])
                if price:
                    logger.debug(f"Got price from {interval} intraday: {price}")
                    return price
        except Exception as e:
            logger.debug(f"Error fetching {interval} intraday history: {e}")
        return None

    def _get_info_price(self, info: Dict) -> Optional[float]:
        """Get price from info dict."""
        price = (
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or info.get("regularMarketLastPrice")
        )
        if price:
            logger.debug(f"Got price from regularMarketPrice: {price}")
            return float(price)
        return None

    def _get_indian_stock_price(self, ticker: Any, info: Dict) -> Optional[float]:
        """Get current price for Indian stocks using multiple fallback methods."""
        # Method 1: Try fast_info for real-time data
        price = self._try_fast_info_price(ticker)
        if price:
            return price

        # Method 2: Try 1-minute interval intraday data
        price = self._try_intraday_price(ticker, "1m")
        if price:
            return price

        # Method 3: Try 5-minute interval intraday data
        price = self._try_intraday_price(ticker, "5m")
        if price:
            return price

        # Method 4: Use regularMarketPrice
        price = self._get_info_price(info)
        if price:
            return price

        # Method 5: Fallback to daily history
        try:
            hist = ticker.history(period="2d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                logger.debug(f"Got price from daily history: {price}")
                return price
        except Exception as e:
            logger.debug(f"Error fetching daily history: {e}")

        return None

    def _get_us_stock_price(self, ticker: Any, info: Dict) -> tuple:
        """Get current price and previous close for US stocks."""
        current_price = None
        previous_close = None

        # Try history first (more reliable)
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
            if current_price:
                current_price = float(current_price)

        return current_price, previous_close

    def _get_previous_close(self, ticker: Any, info: Dict) -> Optional[float]:
        """Get previous close price with fallback methods."""
        previous_close = info.get("previousClose") or info.get(
            "regularMarketPreviousClose"
        )
        if previous_close:
            return float(previous_close)

        # Try to get from history if not in info
        try:
            hist = ticker.history(period="2d")
            if not hist.empty and len(hist) > 1:
                return float(hist["Close"].iloc[-2])
        except Exception as e:
            logger.debug(f"Error fetching previous close from history: {e}")

        return None

    def _format_stock_data(
        self, info: Dict, ticker: Any, symbol: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Format Yahoo Finance data to our stock model format
        Supports both US and Indian stocks
        """
        try:
            # Determine if it's an Indian stock early (needed for price fetching strategy)
            symbol_raw = info.get("symbol", symbol or "")
            is_indian = symbol_raw.endswith(".NS") or symbol_raw.endswith(".BO")

            # Get current price - prioritize most recent data
            if is_indian:
                current_price = self._get_indian_stock_price(ticker, info)
                previous_close = self._get_previous_close(ticker, info)
            else:
                current_price, previous_close = self._get_us_stock_price(ticker, info)
                if previous_close is None:
                    previous_close = self._get_previous_close(ticker, info)

            # Calculate price change
            price_change = None
            price_change_percent = None
            if current_price and previous_close:
                price_change = current_price - previous_close
                price_change_percent = (
                    (price_change / previous_close) * 100 if previous_close else 0
                )

            # Extract symbol and determine exchange
            exchange = info.get("exchange")

            # Clean up symbol (remove .NS or .BO suffix for display)
            if symbol_raw.endswith(".NS"):
                exchange = exchange or "NSE"
                symbol_raw = symbol_raw.replace(".NS", "")
            elif symbol_raw.endswith(".BO"):
                exchange = exchange or "BSE"
                symbol_raw = symbol_raw.replace(".BO", "")

            # Get currency (INR for Indian stocks, USD for US)
            currency = info.get("currency", "INR" if is_indian else "USD")
            country = info.get("country", "India" if is_indian else "United States")

            # Extract all financial metrics from Yahoo Finance info
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
                "marketCap": info.get(
                    "marketCap"
                ),  # Also include with different casing
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
                # Financial Ratios
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "trailingEps": info.get("trailingEps"),
                "forwardEps": info.get("forwardEps"),
                "priceToBook": info.get("priceToBook"),
                "priceToSalesTrailing12Months": info.get(
                    "priceToSalesTrailing12Months"
                ),
                # Revenue and Earnings
                "totalRevenue": info.get("totalRevenue"),
                "revenue": info.get("totalRevenue"),  # Alias
                "revenuePerShare": info.get("revenuePerShare"),
                # Profitability
                "profitMargins": info.get("profitMargins"),
                "grossMargins": info.get("grossMargins"),
                "operatingMargins": info.get("operatingMargins"),
                "netProfitMargin": info.get("netProfitMargin"),
                "ebitda": info.get("ebitda"),
                "ebitdaMargins": info.get("ebitdaMargins"),
                # Returns
                "returnOnEquity": info.get("returnOnEquity"),
                "returnOnAssets": info.get("returnOnAssets"),
                # Balance Sheet
                "bookValue": info.get("bookValue"),
                "totalCash": info.get("totalCash"),
                "totalCashPerShare": info.get("totalCashPerShare"),
                "totalDebt": info.get("totalDebt"),
                "debtToEquity": info.get("debtToEquity"),
                "debtToAssets": info.get("debtToAssets"),
                "currentRatio": info.get("currentRatio"),
                "quickRatio": info.get("quickRatio"),
                # Dividends
                "dividendYield": info.get("dividendYield"),
                "dividendRate": info.get("dividendRate"),
                "payoutRatio": info.get("payoutRatio"),
                # Growth
                "revenueGrowth": info.get("revenueGrowth"),
                "earningsGrowth": info.get("earningsGrowth"),
                "earningsQuarterlyGrowth": info.get("earningsQuarterlyGrowth"),
                # Additional metadata
                "metadata": {
                    "currency": currency,
                    "country": country,
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary"),
                    "employees": info.get("fullTimeEmployees"),
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

    async def get_stock_news(
        self,
        symbol: str,
        limit: int = 20,
        company_name: Optional[str] = None,
        months_back: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Get news articles for a stock from leading Indian economic newspapers.
        Uses Indian News Service instead of yfinance for better coverage of Indian stocks.

        Args:
            symbol: Stock symbol
            limit: Maximum number of news articles to return
            company_name: Company name for better search results
            months_back: Number of months to look back (default 6)
        """
        try:
            # Use Indian News Service for fetching news from Times Group and Hindustan Times Group
            from app.services.indian_news_service import IndianNewsService

            indian_news_service = IndianNewsService()
            news = await indian_news_service.get_stock_news(
                symbol=symbol,
                company_name=company_name,
                limit=limit,
                months_back=months_back,
            )

            logger.info(
                f"Retrieved {len(news)} news articles from Indian news sources for {symbol}"
            )

            return news
        except Exception as e:
            logger.error(
                f"Error getting stock news from Indian sources for {symbol}: {e}"
            )
            # Fallback to empty list instead of mock data
            return []

    def _get_stock_news_sync(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Synchronous news fetch - supports US and Indian stocks"""
        try:
            # Normalize symbol to handle Indian stocks
            symbol_normalized = self._normalize_symbol(symbol)
            logger.info(f"Fetching news for '{symbol}' -> '{symbol_normalized}'")

            ticker = yf.Ticker(symbol_normalized)
            news = ticker.news

            if not news:
                logger.warning(f"No news found for {symbol_normalized}")
                return []

            logger.info(
                f"Retrieved {len(news)} news articles from Yahoo Finance for {symbol_normalized}"
            )
            if len(news) > 0:
                logger.info(
                    f"Sample article keys: {list(news[0].keys()) if isinstance(news[0], dict) else 'N/A'}"
                )
                logger.info(f"Sample article: {str(news[0])[:200]}...")

            formatted_news = []
            for article in news:
                # Log article structure for debugging (first article only to avoid spam)
                if len(formatted_news) == 0:
                    article_keys = (
                        list(article.keys()) if isinstance(article, dict) else "N/A"
                    )
                    logger.info(f"Sample news article structure - Keys: {article_keys}")
                    logger.info(f"Sample news article: {str(article)[:500]}...")

                # Try multiple field names for title
                title = (
                    article.get("title")
                    or article.get("headline")
                    or article.get("summary")
                    or ""
                )

                # Try multiple field names for publisher
                publisher = (
                    article.get("publisher")
                    or article.get("source")
                    or article.get("provider")
                    or article.get("publisherName")
                    or "Unknown"
                )

                # Try multiple field names for link - Yahoo Finance uses various field names
                link = (
                    article.get("link")
                    or article.get("url")
                    or article.get("webUrl")
                    or article.get("canonicalUrl")
                    or article.get("clickThroughUrl")
                    or article.get("redirectUrl")
                    or ""
                )

                # Ensure link is a valid URL - if missing, try to construct from Yahoo Finance
                if not link and article.get("uuid"):
                    # Yahoo Finance news URL pattern
                    link = f"https://finance.yahoo.com/news/{article.get('uuid', '')}"

                # Validate link is a proper URL
                if link and not (
                    link.startswith("http://") or link.startswith("https://")
                ):
                    # If link doesn't start with http/https, prepend https://
                    link = f"https://{link}"

                # Try multiple field names for published date
                published_date = (
                    article.get("providerPublishTime")
                    or article.get("publishTime")
                    or article.get("publishedAt")
                    or article.get("timestamp")
                    or 0
                )

                # Only include articles with at least a title or summary
                if title or article.get("summary"):
                    formatted_news.append(
                        {
                            "title": title
                            or article.get("summary", "No title")[
                                :200
                            ],  # Limit title length
                            "publisher": publisher,
                            "link": link,
                            "published_date": published_date,
                            "uuid": article.get("uuid", ""),
                            "summary": article.get(
                                "summary", ""
                            ),  # Include summary if available
                        }
                    )
                else:
                    logger.warning(
                        f"Skipping article with no title or summary: {article}"
                    )

            logger.info(
                f"Formatted {len(formatted_news)} valid news articles out of {len(news[:limit])} total"
            )

            return formatted_news
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    async def _mock_get_stock_news(
        self, symbol: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Mock news articles"""
        return [
            {
                "title": f"Latest news about {symbol}",
                "publisher": "Financial News",
                "link": f"https://example.com/news/{symbol}",
                "published_date": 1700000000,
                "uuid": f"news-{symbol}-1",
            },
            {
                "title": f"Market analysis for {symbol}",
                "publisher": "Market Watch",
                "link": f"https://example.com/analysis/{symbol}",
                "published_date": 1699900000,
                "uuid": f"news-{symbol}-2",
            },
        ][:limit]
