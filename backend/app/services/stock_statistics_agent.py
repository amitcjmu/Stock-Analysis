"""
Stock Statistics Agent - Specialized AI agent for statistical analysis
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


class StockStatisticsAgent:
    """Specialized agent for generating statistical analysis using LLM"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_service = StockService(db, context)
        self.stock_data_api = StockDataAPIService()

    async def analyze_statistics(
        self, stock_symbol: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistical analysis using LLM.
        Returns structured statistical analysis data.

        Args:
            stock_symbol: Stock symbol to analyze
            model: Optional model name (gemini, llama4_maverick, gemma3_4b, auto)
        """
        logger.info(f"📊 [STATISTICS AGENT] Starting analysis for {stock_symbol}")
        try:
            # Get stock data
            logger.info(f"📊 [STATISTICS AGENT] Fetching stock data for {stock_symbol}")
            stock_data = await self.stock_service.get_stock_by_symbol(stock_symbol)
            if not stock_data:
                logger.error(f"📊 [STATISTICS AGENT] Stock {stock_symbol} not found")
                raise ValueError(f"Stock {stock_symbol} not found")

            logger.info(
                f"📊 [STATISTICS AGENT] Stock data retrieved: {stock_data.get('company_name', 'N/A')}"
            )

            # Get historical data for statistical calculations
            logger.info(
                "📊 [STATISTICS AGENT] Fetching historical data for statistical analysis"
            )
            historical_data = await self.stock_data_api.get_historical_prices(
                stock_symbol, "1y", "1d"
            )

            # Calculate statistics
            statistics = self._calculate_statistics(stock_data, historical_data or [])

            # Save stock to database if not already saved
            stock = await self.stock_service.save_stock(stock_data)
            logger.info(
                f"📊 [STATISTICS AGENT] Stock saved to database with ID: {stock.id}"
            )

            # Generate statistics analysis prompt
            prompt = self._create_statistics_prompt(stock_data, statistics)
            logger.info(
                f"📊 [STATISTICS AGENT] Prompt created, length: {len(prompt)} characters"
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
                f"📊 [STATISTICS AGENT] 🤖 Calling LLM for statistics analysis "
                f"of {stock_symbol} using model: {model or 'auto'}"
            )
            response_data = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="analysis",
                complexity=TaskComplexity.AGENTIC,
                model_type=model_type,  # Pass selected model or None for auto
            )
            logger.info("📊 [STATISTICS AGENT] LLM response received")

            # Check for errors in response
            if response_data.get("status") == "error":
                error_msg = response_data.get("error", "Unknown error")
                logger.error(f"📊 [STATISTICS AGENT] LLM returned error: {error_msg}")
                raise ValueError(f"LLM error for {stock_symbol}: {error_msg}")

            # Extract the actual response text from the response dict
            response_text = response_data.get("response") or response_data.get(
                "content", ""
            )

            if not response_text:
                logger.error(
                    f"📊 [STATISTICS AGENT] Empty response from LLM for {stock_symbol}"
                )
                raise ValueError(f"Empty response from LLM for {stock_symbol}")

            logger.info(
                f"📊 [STATISTICS AGENT] Response text length: {len(response_text)} characters"
            )

            # Parse LLM response into structured format
            logger.info("📊 [STATISTICS AGENT] Parsing LLM response")
            model_used = response_data.get("model_used", "auto")
            analysis_data = self._parse_llm_response(
                response_text, stock_data, statistics, model_used=model_used
            )
            logger.info("📊 [STATISTICS AGENT] Analysis data parsed successfully")

            # Save analysis to database
            analysis = await self.stock_service.save_stock_analysis(
                UUID(str(stock.id)), analysis_data
            )
            logger.info(
                f"📊 [STATISTICS AGENT] Analysis saved to database with ID: {analysis.id}"
            )

            logger.info(
                f"📊 [STATISTICS AGENT] ✅ Statistics analysis completed successfully for {stock_symbol}"
            )

            # Safely convert to dict
            stock_dict = stock.to_dict() if hasattr(stock, "to_dict") else stock
            analysis_dict = (
                analysis.to_dict() if hasattr(analysis, "to_dict") else analysis
            )

            # Log return structure details
            logger.info(
                f"📊 [STATISTICS AGENT] Returning result with keys: {list({'stock': stock_dict, 'analysis': analysis_dict}.keys())}"
            )
            if isinstance(analysis_dict, dict):
                logger.info(
                    f"📊 [STATISTICS AGENT] Analysis keys: {list(analysis_dict.keys())}"
                )
                logger.info(
                    f"📊 [STATISTICS AGENT] Analysis summary: {analysis_dict.get('summary', 'N/A')[:200]}..."
                )
                logger.info(
                    f"📊 [STATISTICS AGENT] Analysis type: {analysis_dict.get('analysis_type', 'N/A')}"
                )
                logger.info(
                    f"📊 [STATISTICS AGENT] Model used: {analysis_dict.get('llm_model', 'N/A')}"
                )
                logger.info(
                    f"📊 [STATISTICS AGENT] Confidence score: {analysis_dict.get('confidence_score', 'N/A')}"
                )

            return {
                "stock": stock_dict,
                "analysis": analysis_dict,
            }

        except Exception as e:
            logger.error(
                f"📊 [STATISTICS AGENT] ❌ Error analyzing statistics for {stock_symbol}: {e}",
                exc_info=True,
            )
            raise

    def _calculate_statistics(
        self, stock_data: Dict[str, Any], historical_data: list
    ) -> Dict[str, Any]:
        """Calculate statistical metrics from stock data"""
        stats = {
            "price_statistics": {},
            "volume_statistics": {},
            "volatility_metrics": {},
            "performance_metrics": {},
        }

        if historical_data:
            prices = [d.get("close", 0) for d in historical_data if d.get("close")]
            volumes = [d.get("volume", 0) for d in historical_data if d.get("volume")]

            if prices:
                import statistics

                stats["price_statistics"] = {
                    "mean": statistics.mean(prices),
                    "median": statistics.median(prices),
                    "min": min(prices),
                    "max": max(prices),
                    "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
                }

                # Calculate returns
                returns = []
                for i in range(1, len(prices)):
                    if prices[i - 1] > 0:
                        returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

                if returns:
                    stats["performance_metrics"] = {
                        "average_return": statistics.mean(returns),
                        "volatility": (
                            statistics.stdev(returns) if len(returns) > 1 else 0
                        ),
                        "total_return": (
                            (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
                        ),
                    }

            if volumes:
                import statistics

                stats["volume_statistics"] = {
                    "mean": statistics.mean(volumes),
                    "median": statistics.median(volumes),
                    "min": min(volumes),
                    "max": max(volumes),
                }

        return stats

    def _create_statistics_prompt(
        self, stock_data: Dict[str, Any], statistics: Dict[str, Any]
    ) -> str:
        """Create specialized prompt for statistical analysis"""
        # Format statistics
        stats_summary = f"""
Statistical Metrics:
Price Statistics:
- Mean: ${statistics.get('price_statistics', {}).get('mean', 0):.2f}
- Median: ${statistics.get('price_statistics', {}).get('median', 0):.2f}
- Min: ${statistics.get('price_statistics', {}).get('min', 0):.2f}
- Max: ${statistics.get('price_statistics', {}).get('max', 0):.2f}
- Std Dev: ${statistics.get('price_statistics', {}).get('std_dev', 0):.2f}

Performance Metrics:
- Average Return: {statistics.get('performance_metrics', {}).get('average_return', 0):.2%}
- Volatility: {statistics.get('performance_metrics', {}).get('volatility', 0):.2%}
- Total Return: {statistics.get('performance_metrics', {}).get('total_return', 0):.2%}

Volume Statistics:
- Mean Volume: {statistics.get('volume_statistics', {}).get('mean', 0):,.0f}
- Median Volume: {statistics.get('volume_statistics', {}).get('median', 0):,.0f}
"""

        return f"""
You are a senior quantitative analyst specializing in statistical analysis and risk modeling.
Analyze the following stock's statistical metrics and provide a comprehensive statistical analysis.

Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Exchange: {stock_data.get('exchange', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {f"${stock_data.get('current_price', 0):,.2f}" if stock_data.get('current_price') else "N/A"}
{stats_summary}

Please provide a comprehensive statistical analysis in the following JSON format:

{{
    "summary": "Executive summary of the statistical analysis and risk profile (2-3 sentences)",
    "volatility_analysis": {{
        "volatility_level": "high/moderate/low",
        "risk_level": "high/moderate/low",
        "price_stability": "stable/volatile/highly_volatile"
    }},
    "distribution_analysis": {{
        "price_distribution": "normal/skewed/fat_tailed",
        "outliers": "present/absent",
        "distribution_characteristics": "Brief description"
    }},
    "performance_statistics": {{
        "expected_return": value,
        "risk_adjusted_return": value,
        "sharpe_ratio": value,
        "max_drawdown": value
    }},
    "statistical_signals": [
        "Statistical signal 1",
        "Statistical signal 2",
        "Statistical signal 3"
    ],
    "risk_metrics": {{
        "value_at_risk": value,
        "expected_shortfall": value,
        "beta": value,
        "correlation": value
    }},
    "recommendations": {{
        "action": "buy/hold/sell",
        "confidence": 0.0-1.0,
        "reasoning": "Detailed reasoning based on statistical analysis"
    }}
}}

Provide only valid JSON, no additional text.
"""

    def _parse_llm_response(
        self,
        response: str,
        stock_data: Dict[str, Any],
        statistics: Dict[str, Any],
        model_used: str = "auto",
    ) -> Dict[str, Any]:
        """Parse LLM response into structured statistical analysis data"""
        import json
        import re

        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            
            # Remove markdown code blocks more thoroughly
            if "```json" in response_clean:
                # Extract content between ```json and ```
                json_match = re.search(r"```json\s*(.*?)\s*```", response_clean, re.DOTALL)
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

            # Structure the analysis data
            return {
                "analysis_type": "statistics",
                "summary": analysis_json.get("summary", ""),
                "key_insights": analysis_json.get("statistical_signals", []),
                "risk_assessment": {
                    "volatility_analysis": analysis_json.get("volatility_analysis", {}),
                    "risk_metrics": analysis_json.get("risk_metrics", {}),
                    "distribution_analysis": analysis_json.get(
                        "distribution_analysis", {}
                    ),
                },
                "technical_analysis": {
                    "performance_statistics": analysis_json.get(
                        "performance_statistics", {}
                    ),
                },
                "recommendations": analysis_json.get("recommendations", {}),
                "llm_model": model_used,
                "llm_prompt": self._create_statistics_prompt(stock_data, statistics),
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
                summary_match = re.search(r'summary["\']?\s*:\s*["\']?([^"\']+)', clean_text, re.IGNORECASE)
                if summary_match:
                    summary_text = summary_match.group(1).strip()[:500]
                else:
                    # Last resort: use first 500 chars of cleaned text
                    summary_text = clean_text.strip()[:500]
            
            # Fallback: create basic analysis from response text
            return {
                "analysis_type": "statistics",
                "summary": summary_text if summary_text else "Analysis completed but response format was invalid.",
                "key_insights": [
                    response[i : i + 200]
                    for i in range(0, min(600, len(response)), 200)
                ],
                "risk_assessment": {},
                "technical_analysis": {},
                "recommendations": {
                    "action": "hold",
                    "confidence": 0.5,
                    "reasoning": "Unable to parse full analysis due to response format issues.",
                },
                "llm_model": model_used,
                "llm_prompt": self._create_statistics_prompt(stock_data, statistics),
                "llm_response": {"raw_response": response},
                "confidence_score": 0.5,
            }
