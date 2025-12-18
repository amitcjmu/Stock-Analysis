"""
Stock Financials Agent - Specialized AI agent for financial analysis
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import (
    multi_model_service,
    TaskComplexity,
    ModelType,
)
from app.services.stock_service import StockService
from app.services.stock_data_api import StockDataAPIService

logger = logging.getLogger(__name__)


class StockFinancialsAgent:
    """Specialized agent for generating financial analysis using LLM"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_service = StockService(db, context)
        self.stock_data_api = StockDataAPIService()

    async def analyze_financials(
        self, stock_symbol: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive financial analysis using LLM.
        Returns structured financial analysis data.

        Args:
            stock_symbol: Stock symbol to analyze
            model: Optional model name (gemini, llama4_maverick, gemma3_4b, auto)
        """
        logger.info(f"💰 [FINANCIALS AGENT] Starting analysis for {stock_symbol}")
        try:
            # Get stock data (includes financial metrics from Yahoo Finance)
            logger.info(f"💰 [FINANCIALS AGENT] Fetching stock data for {stock_symbol}")
            stock_data = await self.stock_service.get_stock_by_symbol(stock_symbol)
            if not stock_data:
                logger.error(f"💰 [FINANCIALS AGENT] Stock {stock_symbol} not found")
                raise ValueError(f"Stock {stock_symbol} not found")

            logger.info(
                f"💰 [FINANCIALS AGENT] Stock data retrieved: {stock_data.get('company_name', 'N/A')}"
            )

            # Get detailed financial data
            logger.info("💰 [FINANCIALS AGENT] Fetching detailed financial data")
            detailed_data = await self.stock_data_api.get_stock_data(stock_symbol)
            if detailed_data:
                # Log what data we received
                logger.info(
                    f"💰 [FINANCIALS AGENT] Received detailed data with keys: {list(detailed_data.keys())}"
                )
                # Log key financial metrics
                financial_keys = [
                    "market_cap",
                    "trailingPE",
                    "forwardPE",
                    "trailingEps",
                    "totalRevenue",
                    "profitMargins",
                    "returnOnEquity",
                    "debtToEquity",
                    "currentRatio",
                    "bookValue",
                    "priceToBook",
                ]
                for key in financial_keys:
                    if key in detailed_data:
                        logger.info(
                            f"💰 [FINANCIALS AGENT] {key}: {detailed_data.get(key)}"
                        )
                # Merge financial metrics into stock_data
                stock_data.update(detailed_data)
            else:
                logger.warning(
                    f"💰 [FINANCIALS AGENT] No detailed financial data returned for {stock_symbol}"
                )

            # Save stock to database if not already saved
            stock = await self.stock_service.save_stock(stock_data)
            logger.info(
                f"💰 [FINANCIALS AGENT] Stock saved to database with ID: {stock.id}"
            )

            # Generate financials analysis prompt
            prompt = self._create_financials_prompt(stock_data)
            logger.info(
                f"💰 [FINANCIALS AGENT] Prompt created, length: {len(prompt)} characters"
            )

            # Determine model type
            model_type = None
            if model:
                model_lower = model.lower()
                if model_lower == "gemini":
                    model_type = ModelType.GEMINI
                elif model_lower == "llama4_maverick" or model_lower == "llama":
                    model_type = ModelType.LLAMA_4_MAVERICK
                elif model_lower == "gemma3_4b" or model_lower == "gemma":
                    model_type = ModelType.GEMMA_3_4B
                # If model is "auto" or None, model_type stays None and auto-selection will be used

            # Call LLM for analysis
            logger.info(
                f"💰 [FINANCIALS AGENT] 🤖 Calling LLM for financials analysis "
                f"of {stock_symbol} using model: {model or 'auto'}"
            )
            response_data = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="analysis",
                complexity=TaskComplexity.AGENTIC,
                model_type=model_type,  # Pass selected model or None for auto
            )
            logger.info("💰 [FINANCIALS AGENT] LLM response received")

            # Check for errors in response
            if response_data.get("status") == "error":
                error_msg = response_data.get("error", "Unknown error")
                logger.error(f"💰 [FINANCIALS AGENT] LLM returned error: {error_msg}")
                raise ValueError(f"LLM error for {stock_symbol}: {error_msg}")

            # Extract the actual response text from the response dict
            response_text = response_data.get("response") or response_data.get(
                "content", ""
            )

            if not response_text:
                logger.error(
                    f"💰 [FINANCIALS AGENT] Empty response from LLM for {stock_symbol}"
                )
                raise ValueError(f"Empty response from LLM for {stock_symbol}")

            logger.info(
                f"💰 [FINANCIALS AGENT] Response text length: {len(response_text)} characters"
            )

            # Parse LLM response into structured format
            logger.info("💰 [FINANCIALS AGENT] Parsing LLM response")
            model_used = response_data.get("model_used", "auto")
            analysis_data = self._parse_llm_response(
                response_text, stock_data, model_used=model_used
            )
            logger.info("💰 [FINANCIALS AGENT] Analysis data parsed successfully")

            # Save analysis to database
            analysis = await self.stock_service.save_stock_analysis(
                UUID(str(stock.id)), analysis_data
            )
            logger.info(
                f"💰 [FINANCIALS AGENT] Analysis saved to database with ID: {analysis.id}"
            )

            logger.info(
                f"💰 [FINANCIALS AGENT] ✅ Financials analysis completed successfully for {stock_symbol}"
            )

            # Safely convert to dict
            stock_dict = stock.to_dict() if hasattr(stock, "to_dict") else stock
            analysis_dict = (
                analysis.to_dict() if hasattr(analysis, "to_dict") else analysis
            )

            # Log return structure details
            logger.info(
                f"💰 [FINANCIALS AGENT] Returning result with keys: {list({'stock': stock_dict, 'analysis': analysis_dict}.keys())}"
            )
            if isinstance(analysis_dict, dict):
                logger.info(
                    f"💰 [FINANCIALS AGENT] Analysis keys: {list(analysis_dict.keys())}"
                )
                logger.info(
                    f"💰 [FINANCIALS AGENT] Analysis summary: {analysis_dict.get('summary', 'N/A')[:200]}..."
                )
                logger.info(
                    f"💰 [FINANCIALS AGENT] Analysis type: {analysis_dict.get('analysis_type', 'N/A')}"
                )
                logger.info(
                    f"💰 [FINANCIALS AGENT] Model used: {analysis_dict.get('llm_model', 'N/A')}"
                )
                logger.info(
                    f"💰 [FINANCIALS AGENT] Confidence score: {analysis_dict.get('confidence_score', 'N/A')}"
                )

            return {
                "stock": stock_dict,
                "analysis": analysis_dict,
            }

        except Exception as e:
            logger.error(
                f"💰 [FINANCIALS AGENT] ❌ Error analyzing financials for {stock_symbol}: {e}",
                exc_info=True,
            )
            raise

    def _create_financials_prompt(self, stock_data: Dict[str, Any]) -> str:
        """Create specialized prompt for financial analysis"""
        # Extract key financial metrics
        market_cap = stock_data.get("market_cap", 0)
        pe_ratio = (
            stock_data.get("trailingPE")
            or stock_data.get("forwardPE")
            or stock_data.get("pe_ratio")
        )
        eps = stock_data.get("trailingEps") or stock_data.get("eps")
        revenue = stock_data.get("totalRevenue") or stock_data.get("revenue")
        profit_margin = stock_data.get("profitMargins") or stock_data.get(
            "profit_margin"
        )
        roe = stock_data.get("returnOnEquity") or stock_data.get("roe")
        debt_to_equity = stock_data.get("debtToEquity") or stock_data.get(
            "debt_to_equity"
        )
        current_ratio = stock_data.get("currentRatio") or stock_data.get(
            "current_ratio"
        )
        dividend_yield = stock_data.get("dividendYield") or stock_data.get(
            "dividend_yield"
        )
        book_value = stock_data.get("bookValue") or stock_data.get("book_value")
        price_to_book = stock_data.get("priceToBook") or stock_data.get("price_to_book")

        # Additional metrics
        roa = stock_data.get("returnOnAssets") or stock_data.get("roa")
        quick_ratio = stock_data.get("quickRatio") or stock_data.get("quick_ratio")
        debt_to_assets = stock_data.get("debtToAssets") or stock_data.get(
            "debt_to_assets"
        )
        price_to_sales = (
            stock_data.get("priceToSalesTrailing12Months")
            or stock_data.get("priceToSales")
            or stock_data.get("price_to_sales")
        )
        net_margin = (
            stock_data.get("netProfitMargin")
            or stock_data.get("net_margin")
            or profit_margin
        )

        # Format financial metrics
        market_cap_str = f"${market_cap:,.0f}" if market_cap else "N/A"
        pe_ratio_str = f"{pe_ratio:.2f}" if pe_ratio else "N/A"
        eps_str = f"${eps:.2f}" if eps else "N/A"
        revenue_str = f"${revenue:,.0f}" if revenue else "N/A"
        profit_margin_str = f"{profit_margin:.2%}" if profit_margin else "N/A"
        roe_str = f"{roe:.2%}" if roe else "N/A"
        debt_to_equity_str = f"{debt_to_equity:.2f}" if debt_to_equity else "N/A"
        current_ratio_str = f"{current_ratio:.2f}" if current_ratio else "N/A"
        dividend_yield_str = f"{dividend_yield:.2%}" if dividend_yield else "N/A"
        book_value_str = f"${book_value:.2f}" if book_value else "N/A"
        price_to_book_str = f"{price_to_book:.2f}" if price_to_book else "N/A"

        # Format additional metrics
        roa_str = f"{roa:.2%}" if roa else "N/A"
        quick_ratio_str = f"{quick_ratio:.2f}" if quick_ratio else "N/A"
        debt_to_assets_str = f"{debt_to_assets:.2f}" if debt_to_assets else "N/A"
        price_to_sales_str = f"{price_to_sales:.2f}" if price_to_sales else "N/A"
        net_margin_str = f"{net_margin:.2%}" if net_margin else "N/A"

        financial_metrics = f"""
Financial Metrics:
- Market Cap: {market_cap_str}
- P/E Ratio: {pe_ratio_str}
- EPS: {eps_str}
- Revenue: {revenue_str}
- Profit Margin: {profit_margin_str}
- Net Margin: {net_margin_str}
- ROE: {roe_str}
- ROA: {roa_str}
- Debt to Equity: {debt_to_equity_str}
- Debt to Assets: {debt_to_assets_str}
- Current Ratio: {current_ratio_str}
- Quick Ratio: {quick_ratio_str}
- Dividend Yield: {dividend_yield_str}
- Book Value: {book_value_str}
- Price to Book: {price_to_book_str}
- Price to Sales: {price_to_sales_str}
"""

        # Include ALL available financial data in the prompt for better analysis
        # Filter out None values and format for readability
        all_financial_data = {
            k: v
            for k, v in stock_data.items()
            if v is not None
            and k.lower()
            not in [
                "symbol",
                "company_name",
                "exchange",
                "sector",
                "industry",
                "current_price",
                "id",
                "created_at",
                "updated_at",
            ]
            and (
                "revenue" in k.lower()
                or "earnings" in k.lower()
                or "profit" in k.lower()
                or "margin" in k.lower()
                or "ratio" in k.lower()
                or "debt" in k.lower()
                or "equity" in k.lower()
                or "assets" in k.lower()
                or "return" in k.lower()
                or "book" in k.lower()
                or "price" in k.lower()
                or "market" in k.lower()
                or "cap" in k.lower()
                or "eps" in k.lower()
                or "pe" in k.lower()
                or "dividend" in k.lower()
            )
        }

        additional_data = ""
        if all_financial_data:
            additional_data = "\n\nAdditional Financial Data Available:\n"
            for key, value in sorted(all_financial_data.items())[
                :30
            ]:  # Limit to 30 fields
                if value is not None:
                    if isinstance(value, (int, float)):
                        if value > 1000000:
                            additional_data += f"- {key}: ${value:,.0f}\n"
                        elif value < 1 and value > 0:
                            additional_data += f"- {key}: {value:.4f}\n"
                        else:
                            additional_data += f"- {key}: {value:,.2f}\n"
                    else:
                        additional_data += f"- {key}: {value}\n"

        return f"""
You are a senior financial analyst specializing in fundamental analysis and financial statement evaluation.
Analyze the following stock's financial metrics and provide a comprehensive fundamental analysis.

CRITICAL INSTRUCTIONS:
1. You MUST use the actual values provided in the financial metrics below. Do NOT mark them as "undeterminable" or "null" if values are provided.
2. For each field in the JSON response, you MUST provide a value. Use the actual numbers from the data provided.
3. If a metric is "N/A", calculate it from available data or provide a reasonable estimate based on industry standards.
4. For valuation ratios, use the actual P/E, Price-to-Book, and Price-to-Sales values provided.
5. For profitability ratios, use the actual ROE, ROA, and net margin values provided.
6. For liquidity ratios, use the actual current ratio and quick ratio values provided.
7. For leverage ratios, use the actual debt-to-equity and debt-to-assets values provided.
8. NEVER return "undeterminable" or "null" for any field - always provide a value based on the data.

Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Exchange: {stock_data.get('exchange', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {f"${stock_data.get('current_price', 0):,.2f}" if stock_data.get('current_price') else "N/A"}
{financial_metrics}
{additional_data}

Please provide a comprehensive financial analysis in the following JSON format:

{{
    "summary": "Executive summary of the financial health and valuation (2-3 sentences)",
    "valuation_analysis": {{
        "valuation": "overvalued/undervalued/fair",
        "valuation_basis": "Brief explanation",
        "price_target": price,
        "upside_potential": percentage
    }},
    "financial_health": {{
        "overall_health": "strong/moderate/weak",
        "liquidity": "strong/moderate/weak",
        "solvency": "strong/moderate/weak",
        "profitability": "strong/moderate/weak",
        "efficiency": "strong/moderate/weak"
    }},
    "key_financial_ratios": {{
        "profitability_ratios": {{
            "net_margin": value,
            "roe": value,
            "roa": value
        }},
        "liquidity_ratios": {{
            "current_ratio": value,
            "quick_ratio": value
        }},
        "leverage_ratios": {{
            "debt_to_equity": value,
            "debt_to_assets": value
        }},
        "valuation_ratios": {{
            "pe_ratio": value,
            "price_to_book": value,
            "price_to_sales": value
        }}
    }},
    "growth_analysis": {{
        "revenue_growth": "positive/negative/stable",
        "earnings_growth": "positive/negative/stable",
        "growth_prospects": "strong/moderate/weak"
    }},
    "risk_factors": [
        "Financial risk factor 1",
        "Financial risk factor 2",
        "Financial risk factor 3"
    ],
    "recommendations": {{
        "action": "buy/hold/sell",
        "confidence": 0.0-1.0,
        "reasoning": "Detailed reasoning based on financial analysis"
    }}
}}

Provide only valid JSON, no additional text.
"""

    def _parse_llm_response(
        self, response: str, stock_data: Dict[str, Any], model_used: str = "auto"
    ) -> Dict[str, Any]:
        """Parse LLM response into structured financial analysis data"""
        import json
        import re

        try:
            # Try to extract JSON from response
            response_clean = response.strip()

            # Remove markdown code blocks more thoroughly
            if "```json" in response_clean:
                # Extract content between ```json and ```
                json_match = re.search(
                    r"```json\s*(.*?)\s*```", response_clean, re.DOTALL
                )
                if json_match:
                    response_clean = json_match.group(1).strip()
                else:
                    # Fallback: remove markers
                    response_clean = re.sub(r"```json\s*", "", response_clean)
                    response_clean = re.sub(r"```\s*$", "", response_clean)
            elif "```" in response_clean:
                # Extract content between ``` and ```
                json_match = re.search(r"```\s*(.*?)\s*```", response_clean, re.DOTALL)
                if json_match:
                    response_clean = json_match.group(1).strip()
                else:
                    response_clean = re.sub(r"```\s*", "", response_clean)

            # Try to find JSON object in the response (handle cases where there's extra text)
            json_match = re.search(r"\{.*\}", response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(0)

            # Log cleaned response for debugging
            logger.debug(f"Cleaned response (first 200 chars): {response_clean[:200]}")

            # Parse JSON
            analysis_json = json.loads(response_clean)

            # Extract financial ratios from LLM response or fallback to stock_data
            llm_ratios = analysis_json.get("key_financial_ratios", {})
            profitability = llm_ratios.get("profitability_ratios", {})
            liquidity = llm_ratios.get("liquidity_ratios", {})
            leverage = llm_ratios.get("leverage_ratios", {})
            valuation = llm_ratios.get("valuation_ratios", {})

            # Fallback: populate ratios from stock_data if LLM didn't provide them
            if not profitability.get("net_margin") or profitability.get(
                "net_margin"
            ) in ["null", "N/A", "undeterminable"]:
                net_margin = stock_data.get("netProfitMargin") or stock_data.get(
                    "profitMargins"
                )
                if net_margin:
                    profitability["net_margin"] = (
                        f"{net_margin:.2%}"
                        if isinstance(net_margin, float)
                        else net_margin
                    )

            if not profitability.get("roe") or profitability.get("roe") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                roe = stock_data.get("returnOnEquity")
                if roe:
                    profitability["roe"] = (
                        f"{roe:.2%}" if isinstance(roe, float) else roe
                    )

            if not profitability.get("roa") or profitability.get("roa") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                roa = stock_data.get("returnOnAssets")
                if roa:
                    profitability["roa"] = (
                        f"{roa:.2%}" if isinstance(roa, float) else roa
                    )

            if not liquidity.get("current_ratio") or liquidity.get("current_ratio") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                current_ratio = stock_data.get("currentRatio")
                if current_ratio:
                    liquidity["current_ratio"] = (
                        f"{current_ratio:.2f}"
                        if isinstance(current_ratio, float)
                        else current_ratio
                    )

            if not liquidity.get("quick_ratio") or liquidity.get("quick_ratio") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                quick_ratio = stock_data.get("quickRatio")
                if quick_ratio:
                    liquidity["quick_ratio"] = (
                        f"{quick_ratio:.2f}"
                        if isinstance(quick_ratio, float)
                        else quick_ratio
                    )

            if not leverage.get("debt_to_equity") or leverage.get("debt_to_equity") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                debt_to_equity = stock_data.get("debtToEquity")
                if debt_to_equity:
                    leverage["debt_to_equity"] = (
                        f"{debt_to_equity:.2f}"
                        if isinstance(debt_to_equity, float)
                        else debt_to_equity
                    )

            if not leverage.get("debt_to_assets") or leverage.get("debt_to_assets") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                debt_to_assets = stock_data.get("debtToAssets")
                if debt_to_assets:
                    leverage["debt_to_assets"] = (
                        f"{debt_to_assets:.2f}"
                        if isinstance(debt_to_assets, float)
                        else debt_to_assets
                    )

            if not valuation.get("pe_ratio") or valuation.get("pe_ratio") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                pe_ratio = stock_data.get("trailingPE") or stock_data.get("forwardPE")
                if pe_ratio:
                    valuation["pe_ratio"] = (
                        f"{pe_ratio:.2f}" if isinstance(pe_ratio, float) else pe_ratio
                    )

            if not valuation.get("price_to_book") or valuation.get("price_to_book") in [
                "null",
                "N/A",
                "undeterminable",
            ]:
                price_to_book = stock_data.get("priceToBook")
                if price_to_book:
                    valuation["price_to_book"] = (
                        f"{price_to_book:.2f}"
                        if isinstance(price_to_book, float)
                        else price_to_book
                    )

            if not valuation.get("price_to_sales") or valuation.get(
                "price_to_sales"
            ) in ["null", "N/A", "undeterminable"]:
                price_to_sales = stock_data.get(
                    "priceToSalesTrailing12Months"
                ) or stock_data.get("priceToSales")
                if price_to_sales:
                    valuation["price_to_sales"] = (
                        f"{price_to_sales:.2f}"
                        if isinstance(price_to_sales, float)
                        else price_to_sales
                    )

            # Update the ratios in the analysis_json
            analysis_json["key_financial_ratios"] = {
                "profitability_ratios": profitability,
                "liquidity_ratios": liquidity,
                "leverage_ratios": leverage,
                "valuation_ratios": valuation,
            }

            # Ensure valuation_analysis exists and has required fields
            valuation_analysis = analysis_json.get("valuation_analysis", {})
            if not valuation_analysis or len(valuation_analysis) == 0:
                valuation_analysis = {}

            # Fallback for valuation_analysis fields
            if not valuation_analysis.get("valuation") or valuation_analysis.get(
                "valuation"
            ) in [None, "null", "N/A", "undeterminable"]:
                # Determine valuation based on P/E ratio
                pe_ratio_val = stock_data.get("trailingPE") or stock_data.get(
                    "forwardPE"
                )
                if pe_ratio_val:
                    if pe_ratio_val > 25:
                        valuation_analysis["valuation"] = "overvalued"
                    elif pe_ratio_val < 15:
                        valuation_analysis["valuation"] = "undervalued"
                    else:
                        valuation_analysis["valuation"] = "fair"
                else:
                    valuation_analysis["valuation"] = "fair"

            if not valuation_analysis.get("valuation_basis") or valuation_analysis.get(
                "valuation_basis"
            ) in [None, "null", "N/A"]:
                pe_ratio_val = stock_data.get("trailingPE") or stock_data.get(
                    "forwardPE"
                )
                if pe_ratio_val:
                    valuation_analysis["valuation_basis"] = (
                        f"Based on P/E ratio of {pe_ratio_val:.2f}"
                    )
                else:
                    valuation_analysis["valuation_basis"] = (
                        "Analysis based on available financial metrics"
                    )

            if not valuation_analysis.get("price_target") or valuation_analysis.get(
                "price_target"
            ) in [None, "null", "N/A"]:
                # Calculate a simple price target based on P/E and EPS
                current_price = stock_data.get("current_price")
                pe_ratio_val = stock_data.get("trailingPE") or stock_data.get(
                    "forwardPE"
                )
                eps_val = stock_data.get("trailingEps") or stock_data.get("forwardEps")
                if current_price and pe_ratio_val and eps_val:
                    # Simple price target: current P/E * EPS (fair value estimate)
                    valuation_analysis["price_target"] = round(
                        pe_ratio_val * eps_val, 2
                    )
                    if current_price:
                        upside = (
                            (valuation_analysis["price_target"] - current_price)
                            / current_price
                        ) * 100
                        valuation_analysis["upside_potential"] = round(upside, 2)
                elif current_price:
                    # Fallback: use current price as target
                    valuation_analysis["price_target"] = current_price
                    valuation_analysis["upside_potential"] = 0

            # Ensure financial_health exists
            financial_health = analysis_json.get("financial_health", {})
            if not financial_health or len(financial_health) == 0:
                financial_health = {}
                # Populate from available metrics
                roe = stock_data.get("returnOnEquity")
                current_ratio = stock_data.get("currentRatio")
                debt_to_equity = stock_data.get("debtToEquity")

                if roe:
                    financial_health["profitability"] = (
                        "strong" if roe > 0.15 else "moderate" if roe > 0.10 else "weak"
                    )
                else:
                    financial_health["profitability"] = "moderate"

                if current_ratio:
                    financial_health["liquidity"] = (
                        "strong"
                        if current_ratio > 1.5
                        else "moderate" if current_ratio > 1.0 else "weak"
                    )
                else:
                    financial_health["liquidity"] = "moderate"

                if debt_to_equity:
                    financial_health["solvency"] = (
                        "strong"
                        if debt_to_equity < 50
                        else "moderate" if debt_to_equity < 100 else "weak"
                    )
                else:
                    financial_health["solvency"] = "moderate"

                financial_health["overall_health"] = "moderate"
                financial_health["efficiency"] = "moderate"

            # Ensure growth_analysis exists
            growth_analysis = analysis_json.get("growth_analysis", {})
            if not growth_analysis or len(growth_analysis) == 0:
                growth_analysis = {}

            if not growth_analysis.get("revenue_growth") or growth_analysis.get(
                "revenue_growth"
            ) in ["null", "N/A", "undeterminable"]:
                revenue_growth = stock_data.get("revenueGrowth")
                if revenue_growth is not None:
                    growth_analysis["revenue_growth"] = (
                        "positive"
                        if revenue_growth > 0
                        else "negative" if revenue_growth < 0 else "stable"
                    )
                else:
                    growth_analysis["revenue_growth"] = "stable"

            if not growth_analysis.get("earnings_growth") or growth_analysis.get(
                "earnings_growth"
            ) in ["null", "N/A", "undeterminable"]:
                earnings_growth = stock_data.get("earningsGrowth") or stock_data.get(
                    "earningsQuarterlyGrowth"
                )
                if earnings_growth is not None:
                    growth_analysis["earnings_growth"] = (
                        "positive"
                        if earnings_growth > 0
                        else "negative" if earnings_growth < 0 else "stable"
                    )
                else:
                    growth_analysis["earnings_growth"] = "stable"

            if not growth_analysis.get("growth_prospects") or growth_analysis.get(
                "growth_prospects"
            ) in ["null", "N/A", "undeterminable"]:
                revenue_growth = stock_data.get("revenueGrowth")
                earnings_growth = stock_data.get("earningsGrowth") or stock_data.get(
                    "earningsQuarterlyGrowth"
                )
                if (revenue_growth and revenue_growth > 0.1) or (
                    earnings_growth and earnings_growth > 0.1
                ):
                    growth_analysis["growth_prospects"] = "strong"
                elif (revenue_growth and revenue_growth > 0) or (
                    earnings_growth and earnings_growth > 0
                ):
                    growth_analysis["growth_prospects"] = "moderate"
                else:
                    growth_analysis["growth_prospects"] = "weak"

            # Update analysis_json with populated structures
            analysis_json["valuation_analysis"] = valuation_analysis
            analysis_json["financial_health"] = financial_health
            analysis_json["growth_analysis"] = growth_analysis

            # Log what we're returning
            logger.info(
                f"💰 [FINANCIALS AGENT] fundamental_analysis structure: "
                f"valuation_analysis={bool(valuation_analysis) and len(valuation_analysis) > 0}, "
                f"financial_health={bool(financial_health) and len(financial_health) > 0}, "
                f"key_financial_ratios={bool(analysis_json.get('key_financial_ratios'))}, "
                f"growth_analysis={bool(growth_analysis) and len(growth_analysis) > 0}"
            )

            # Structure the analysis data - use the populated variables, not analysis_json.get()
            fundamental_analysis = {
                "valuation_analysis": valuation_analysis,
                "financial_health": financial_health,
                "key_financial_ratios": analysis_json.get("key_financial_ratios", {}),
                "growth_analysis": growth_analysis,
            }

            logger.info(
                f"💰 [FINANCIALS AGENT] fundamental_analysis keys: {list(fundamental_analysis.keys())}, "
                f"total length: {len(fundamental_analysis)}"
            )

            return {
                "analysis_type": "financials",
                "summary": analysis_json.get("summary", ""),
                "key_insights": analysis_json.get("risk_factors", []),
                "fundamental_analysis": fundamental_analysis,
                "risk_assessment": {
                    "risk_factors": analysis_json.get("risk_factors", []),
                },
                "recommendations": analysis_json.get("recommendations", {}),
                "llm_model": model_used,
                "llm_prompt": self._create_financials_prompt(stock_data),
                "llm_response": analysis_json,
                "confidence_score": analysis_json.get("recommendations", {}).get(
                    "confidence", 0.5
                ),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.warning(f"Response text (first 500 chars): {response[:500]}")

            # Try to extract summary from raw response even if JSON parsing fails
            summary_text = ""
            # Try to find summary in the response text
            summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', response, re.DOTALL)
            if summary_match:
                summary_text = summary_match.group(1)
            else:
                # If no JSON summary found, try to extract first meaningful sentence
                # Remove markdown code blocks
                clean_text = re.sub(r"```json\s*", "", response)
                clean_text = re.sub(r"```\s*", "", clean_text)
                # Try to find text after "summary"
                summary_match = re.search(
                    r'summary["\']?\s*:\s*["\']?([^"\']+)', clean_text, re.IGNORECASE
                )
                if summary_match:
                    summary_text = summary_match.group(1).strip()[:500]
                else:
                    # Last resort: use first 500 chars of cleaned text
                    summary_text = clean_text.strip()[:500]

            # Fallback: create basic analysis from response text
            return {
                "analysis_type": "financials",
                "summary": (
                    summary_text
                    if summary_text
                    else "Analysis completed but response format was invalid."
                ),
                "key_insights": [
                    response[i : i + 200]
                    for i in range(0, min(600, len(response)), 200)
                ],
                "fundamental_analysis": {},
                "risk_assessment": {},
                "recommendations": {
                    "action": "hold",
                    "confidence": 0.5,
                    "reasoning": "Unable to parse full analysis due to response format issues.",
                },
                "llm_model": model_used,
                "llm_prompt": self._create_financials_prompt(stock_data),
                "llm_response": {"raw_response": response},
                "confidence_score": 0.5,
            }
