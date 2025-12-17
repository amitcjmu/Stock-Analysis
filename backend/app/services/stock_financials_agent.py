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
                # Merge financial metrics into stock_data
                stock_data.update(detailed_data)

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
                f"💰 [FINANCIALS AGENT] 🤖 Calling LLM for financials analysis of {stock_symbol} using model: {model or 'auto'}"
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
            analysis_data = self._parse_llm_response(response_text, stock_data, model_used=model_used)
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

        financial_metrics = f"""
Financial Metrics:
- Market Cap: {market_cap_str}
- P/E Ratio: {pe_ratio_str}
- EPS: {eps_str}
- Revenue: {revenue_str}
- Profit Margin: {profit_margin_str}
- ROE: {roe_str}
- Debt to Equity: {debt_to_equity_str}
- Current Ratio: {current_ratio_str}
- Dividend Yield: {dividend_yield_str}
- Book Value: {book_value_str}
- Price to Book: {price_to_book_str}
"""

        return f"""
You are a senior financial analyst specializing in fundamental analysis and financial statement evaluation.
Analyze the following stock's financial metrics and provide a comprehensive fundamental analysis.

Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Exchange: {stock_data.get('exchange', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {f"${stock_data.get('current_price', 0):,.2f}" if stock_data.get('current_price') else "N/A"}
{financial_metrics}

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
            if "```json" in response_clean:
                response_clean = re.sub(r"```json\s*", "", response_clean)
                response_clean = re.sub(r"```\s*$", "", response_clean)
            elif "```" in response_clean:
                response_clean = re.sub(r"```\s*", "", response_clean)

            # Try to find JSON object in the response (handle cases where there's extra text)
            json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(0)

            # Parse JSON
            analysis_json = json.loads(response_clean)

            # Structure the analysis data
            return {
                "analysis_type": "financials",
                "summary": analysis_json.get("summary", ""),
                "key_insights": analysis_json.get("risk_factors", []),
                "fundamental_analysis": {
                    "valuation_analysis": analysis_json.get("valuation_analysis", {}),
                    "financial_health": analysis_json.get("financial_health", {}),
                    "key_financial_ratios": analysis_json.get(
                        "key_financial_ratios", {}
                    ),
                    "growth_analysis": analysis_json.get("growth_analysis", {}),
                },
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
            # Fallback: create basic analysis from response text
            return {
                "analysis_type": "financials",
                "summary": response[:500] if len(response) > 500 else response,
                "key_insights": [
                    response[i : i + 200]
                    for i in range(0, min(600, len(response)), 200)
                ],
                "fundamental_analysis": {},
                "risk_assessment": {},
                "recommendations": {
                    "action": "hold",
                    "confidence": 0.5,
                    "reasoning": response,
                },
                "llm_model": model_used,
                "llm_prompt": self._create_financials_prompt(stock_data),
                "llm_response": {"raw_response": response},
                "confidence_score": 0.5,
            }
