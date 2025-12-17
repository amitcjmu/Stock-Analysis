"""
Stock History Agent - Specialized AI agent for historical price analysis
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import multi_model_service, TaskComplexity
from app.services.stock_service import StockService
from app.services.stock_data_api import StockDataAPIService

logger = logging.getLogger(__name__)


class StockHistoryAgent:
    """Specialized agent for generating historical price analysis using LLM"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_service = StockService(db, context)
        self.stock_data_api = StockDataAPIService()

    async def analyze_history(
        self, stock_symbol: str, period: str = "1y", interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive historical price analysis using LLM.
        Returns structured historical analysis data.
        """
        logger.info(f"📈 [HISTORY AGENT] Starting analysis for {stock_symbol}")
        try:
            # Get stock data
            logger.info(f"📈 [HISTORY AGENT] Fetching stock data for {stock_symbol}")
            stock_data = await self.stock_service.get_stock_by_symbol(stock_symbol)
            if not stock_data:
                logger.error(f"📈 [HISTORY AGENT] Stock {stock_symbol} not found")
                raise ValueError(f"Stock {stock_symbol} not found")

            logger.info(
                f"📈 [HISTORY AGENT] Stock data retrieved: {stock_data.get('company_name', 'N/A')}"
            )

            # Get historical price data
            logger.info(
                f"📈 [HISTORY AGENT] Fetching historical prices for period: {period}"
            )
            historical_data = await self.stock_data_api.get_historical_prices(
                stock_symbol, period, interval
            )
            if not historical_data:
                logger.warning(
                    f"📈 [HISTORY AGENT] No historical data available for {stock_symbol}"
                )
                historical_data = []

            logger.info(
                f"📈 [HISTORY AGENT] Retrieved {len(historical_data)} historical data points"
            )

            # Save stock to database if not already saved
            stock = await self.stock_service.save_stock(stock_data)
            logger.info(
                f"📈 [HISTORY AGENT] Stock saved to database with ID: {stock.id}"
            )

            # Generate history analysis prompt
            prompt = self._create_history_prompt(stock_data, historical_data, period)
            logger.info(
                f"📈 [HISTORY AGENT] Prompt created, length: {len(prompt)} characters"
            )

            # Call LLM for analysis
            logger.info(
                f"📈 [HISTORY AGENT] 🤖 Calling LLM for history analysis of {stock_symbol}"
            )
            response_data = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="analysis",
                complexity=TaskComplexity.AGENTIC,
            )
            logger.info("📈 [HISTORY AGENT] LLM response received")

            # Check for errors in response
            if response_data.get("status") == "error":
                error_msg = response_data.get("error", "Unknown error")
                logger.error(f"📈 [HISTORY AGENT] LLM returned error: {error_msg}")
                raise ValueError(f"LLM error for {stock_symbol}: {error_msg}")

            # Extract the actual response text from the response dict
            response_text = response_data.get("response") or response_data.get(
                "content", ""
            )

            if not response_text:
                logger.error(
                    f"📈 [HISTORY AGENT] Empty response from LLM for {stock_symbol}"
                )
                raise ValueError(f"Empty response from LLM for {stock_symbol}")

            logger.info(
                f"📈 [HISTORY AGENT] Response text length: {len(response_text)} characters"
            )

            # Parse LLM response into structured format
            logger.info("📈 [HISTORY AGENT] Parsing LLM response")
            analysis_data = self._parse_llm_response(
                response_text, stock_data, historical_data
            )
            logger.info("📈 [HISTORY AGENT] Analysis data parsed successfully")

            # Save analysis to database
            analysis = await self.stock_service.save_stock_analysis(
                UUID(str(stock.id)), analysis_data
            )
            logger.info(
                f"📈 [HISTORY AGENT] Analysis saved to database with ID: {analysis.id}"
            )

            logger.info(
                f"📈 [HISTORY AGENT] ✅ History analysis completed successfully for {stock_symbol}"
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
                f"📈 [HISTORY AGENT] ❌ Error analyzing history for {stock_symbol}: {e}",
                exc_info=True,
            )
            raise

    def _create_history_prompt(
        self,
        stock_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        period: str,
    ) -> str:
        """Create specialized prompt for historical price analysis"""
        # Calculate key statistics from historical data
        if historical_data:
            prices = [d.get("close", 0) for d in historical_data if d.get("close")]
            volumes = [d.get("volume", 0) for d in historical_data if d.get("volume")]

            if prices:
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                current_price = (
                    prices[-1] if prices else stock_data.get("current_price", 0)
                )
                price_change = current_price - prices[0] if len(prices) > 1 else 0
                price_change_pct = (
                    (price_change / prices[0] * 100) if prices[0] > 0 else 0
                )

                avg_volume = sum(volumes) / len(volumes) if volumes else 0
            else:
                min_price = max_price = avg_price = current_price = price_change = (
                    price_change_pct
                ) = avg_volume = 0
        else:
            min_price = max_price = avg_price = current_price = price_change = (
                price_change_pct
            ) = avg_volume = 0

        # Format historical summary
        history_summary = ""
        if historical_data:
            history_summary = f"\nHistorical Price Data ({period}):\n"
            history_summary += f"- Data Points: {len(historical_data)}\n"
            history_summary += f"- Price Range: ${min_price:.2f} - ${max_price:.2f}\n"
            history_summary += f"- Average Price: ${avg_price:.2f}\n"
            history_summary += f"- Current Price: ${current_price:.2f}\n"
            history_summary += (
                f"- Price Change: ${price_change:.2f} ({price_change_pct:.2f}%)\n"
            )
            history_summary += f"- Average Volume: {avg_volume:,.0f}\n"
            if len(historical_data) > 0:
                history_summary += (
                    f"- First Date: {historical_data[0].get('date', 'N/A')}\n"
                )
                history_summary += (
                    f"- Last Date: {historical_data[-1].get('date', 'N/A')}\n"
                )
        else:
            history_summary = "\nNo historical price data available."

        return f"""
You are a senior technical analyst specializing in historical price pattern analysis and trend identification.
Analyze the following stock's historical price data and provide a comprehensive technical analysis.

Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Exchange: {stock_data.get('exchange', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {f"${stock_data.get('current_price', 0):,.2f}" if stock_data.get('current_price') else "N/A"}
{history_summary}

Please provide a comprehensive historical price analysis in the following JSON format:

{{
    "summary": "Executive summary of the historical price trends and patterns (2-3 sentences)",
    "price_trends": {{
        "overall_trend": "bullish/bearish/sideways",
        "trend_strength": "strong/moderate/weak",
        "volatility": "high/moderate/low",
        "price_momentum": "accelerating/decelerating/stable"
    }},
    "key_price_levels": {{
        "support_levels": [price1, price2],
        "resistance_levels": [price1, price2],
        "current_position": "near_support/near_resistance/mid_range"
    }},
    "technical_patterns": [
        "Pattern 1 (e.g., ascending triangle, head and shoulders)",
        "Pattern 2",
        "Pattern 3"
    ],
    "volume_analysis": {{
        "volume_trend": "increasing/decreasing/stable",
        "volume_confirmation": "bullish/bearish/neutral",
        "average_volume": "above_average/below_average/normal"
    }},
    "time_period_analysis": {{
        "short_term_1m": "bullish/bearish/neutral",
        "medium_term_3m": "bullish/bearish/neutral",
        "long_term_12m": "bullish/bearish/neutral"
    }},
    "price_forecast": {{
        "short_term_target": price,
        "medium_term_target": price,
        "long_term_target": price,
        "forecast_basis": "Brief explanation of price targets"
    }},
    "recommendations": {{
        "action": "buy/hold/sell",
        "confidence": 0.0-1.0,
        "reasoning": "Detailed reasoning based on historical analysis"
    }}
}}

Provide only valid JSON, no additional text.
"""

    def _parse_llm_response(
        self,
        response: str,
        stock_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Parse LLM response into structured historical analysis data"""
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

            # Parse JSON
            analysis_json = json.loads(response_clean)

            # Structure the analysis data
            return {
                "analysis_type": "history",
                "summary": analysis_json.get("summary", ""),
                "key_insights": analysis_json.get("technical_patterns", []),
                "technical_analysis": {
                    "price_trends": analysis_json.get("price_trends", {}),
                    "key_price_levels": analysis_json.get("key_price_levels", {}),
                    "volume_analysis": analysis_json.get("volume_analysis", {}),
                    "time_period_analysis": analysis_json.get(
                        "time_period_analysis", {}
                    ),
                },
                "price_targets": analysis_json.get("price_forecast", {}),
                "recommendations": analysis_json.get("recommendations", {}),
                "llm_model": "llama4_maverick",
                "llm_prompt": self._create_history_prompt(
                    stock_data, historical_data, "1y"
                ),
                "llm_response": analysis_json,
                "confidence_score": analysis_json.get("recommendations", {}).get(
                    "confidence", 0.5
                ),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Fallback: create basic analysis from response text
            return {
                "analysis_type": "history",
                "summary": response[:500] if len(response) > 500 else response,
                "key_insights": [
                    response[i : i + 200]
                    for i in range(0, min(600, len(response)), 200)
                ],
                "technical_analysis": {},
                "price_targets": {},
                "recommendations": {
                    "action": "hold",
                    "confidence": 0.5,
                    "reasoning": response,
                },
                "llm_model": "llama4_maverick",
                "llm_prompt": self._create_history_prompt(
                    stock_data, historical_data, "1y"
                ),
                "llm_response": {"raw_response": response},
                "confidence_score": 0.5,
            }
