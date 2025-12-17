"""
Stock News Agent - Specialized AI agent for news analysis
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import (
    multi_model_service,
    TaskComplexity,
    ModelType,
)
from app.services.stock_service import StockService

logger = logging.getLogger(__name__)


class StockNewsAgent:
    """Specialized agent for generating news analysis using LLM"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_service = StockService(db, context)

    async def analyze_news(
        self,
        stock_symbol: str,
        news_data: List[Dict[str, Any]],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive news analysis using LLM.
        Returns structured news analysis data.
        
        Args:
            stock_symbol: Stock symbol to analyze
            news_data: List of news articles
            model: Optional model name (gemini, llama4_maverick, gemma3_4b, auto)
        """
        logger.info(f"📰 [NEWS AGENT] Starting analysis for {stock_symbol}")
        try:
            # Get stock data
            logger.info(f"📰 [NEWS AGENT] Fetching stock data for {stock_symbol}")
            stock_data = await self.stock_service.get_stock_by_symbol(stock_symbol)
            if not stock_data:
                logger.error(f"📰 [NEWS AGENT] Stock {stock_symbol} not found")
                raise ValueError(f"Stock {stock_symbol} not found")

            logger.info(
                f"📰 [NEWS AGENT] Stock data retrieved: {stock_data.get('company_name', 'N/A')}"
            )
            logger.info(f"📰 [NEWS AGENT] Processing {len(news_data)} news articles")

            # Save stock to database if not already saved
            stock = await self.stock_service.save_stock(stock_data)
            logger.info(f"📰 [NEWS AGENT] Stock saved to database with ID: {stock.id}")

            # Generate news analysis prompt
            prompt = self._create_news_prompt(stock_data, news_data)
            logger.info(
                f"📰 [NEWS AGENT] Prompt created, length: {len(prompt)} characters"
            )
            if news_data:
                logger.info(
                    f"📰 [NEWS AGENT] Sample news titles: {[n.get('title', 'N/A')[:50] for n in news_data[:3]]}"
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
                f"📰 [NEWS AGENT] 🤖 Calling LLM for news analysis of {stock_symbol} using model: {model or 'auto'}"
            )
            response_data = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="analysis",
                complexity=TaskComplexity.AGENTIC,
                model_type=model_type,  # Pass selected model or None for auto
            )
            logger.info("📰 [NEWS AGENT] LLM response received")
            logger.info(f"📰 [NEWS AGENT] Response keys: {list(response_data.keys())}")
            logger.info(
                f"📰 [NEWS AGENT] Response status: {response_data.get('status', 'N/A')}"
            )

            # Check for errors in response
            if response_data.get("status") == "error":
                error_msg = response_data.get("error", "Unknown error")
                logger.error(f"📰 [NEWS AGENT] LLM returned error: {error_msg}")
                raise ValueError(f"LLM error for {stock_symbol}: {error_msg}")

            # Extract the actual response text from the response dict
            response_text = response_data.get("response") or response_data.get(
                "content", ""
            )

            if not response_text:
                logger.error(
                    f"📰 [NEWS AGENT] Empty response from LLM for {stock_symbol}"
                )
                logger.error(f"📰 [NEWS AGENT] Full response_data: {response_data}")
                raise ValueError(
                    f"Empty response from LLM for {stock_symbol}. "
                    f"Response status: {response_data.get('status', 'unknown')}"
                )

            logger.info(
                f"📰 [NEWS AGENT] Response text length: {len(response_text)} characters"
            )
            logger.info(f"📰 [NEWS AGENT] Response preview: {response_text[:200]}...")

            # Parse LLM response into structured format
            logger.info("📰 [NEWS AGENT] Parsing LLM response")
            model_used = response_data.get("model_used", "auto")
            analysis_data = self._parse_llm_response(response_text, stock_data, model_used=model_used)
            logger.info("📰 [NEWS AGENT] Analysis data parsed successfully")
            logger.info(
                f"📰 [NEWS AGENT] Analysis summary: {analysis_data.get('summary', 'N/A')[:100]}..."
            )

            # Save analysis to database
            analysis = await self.stock_service.save_stock_analysis(
                UUID(str(stock.id)), analysis_data
            )
            logger.info(
                f"📰 [NEWS AGENT] Analysis saved to database with ID: {analysis.id}"
            )

            logger.info(
                f"📰 [NEWS AGENT] ✅ News analysis completed successfully for {stock_symbol}"
            )

            # Safely convert to dict - check if already a dict
            stock_dict = stock.to_dict() if hasattr(stock, "to_dict") else stock
            analysis_dict = (
                analysis.to_dict() if hasattr(analysis, "to_dict") else analysis
            )

            logger.info(
                f"📰 [NEWS AGENT] Stock type: {type(stock)}, Analysis type: {type(analysis)}"
            )
            logger.info(
                f"📰 [NEWS AGENT] Stock dict type: {type(stock_dict)}, Analysis dict type: {type(analysis_dict)}"
            )

            return {
                "stock": stock_dict,
                "analysis": analysis_dict,
            }

        except Exception as e:
            logger.error(
                f"📰 [NEWS AGENT] ❌ Error analyzing news for {stock_symbol}: {e}",
                exc_info=True,
            )
            raise

    def _create_news_prompt(
        self, stock_data: Dict[str, Any], news_data: List[Dict[str, Any]]
    ) -> str:
        """Create specialized prompt for news analysis"""
        # Format news articles
        news_summary = ""
        if news_data:
            news_summary = "\nRecent News Articles:\n"
            for i, article in enumerate(news_data[:10], 1):  # Limit to 10 most recent
                title = article.get("title", "N/A")
                publisher = article.get("publisher", "N/A")
                published_date = article.get("published_date", "N/A")
                news_summary += f"\n{i}. {title}\n   Publisher: {publisher}\n   Date: {published_date}\n"
        else:
            news_summary = "\nNo recent news articles available."

        return f"""
You are a senior financial news analyst specializing in market sentiment and news impact analysis.
Analyze the following stock's recent news and provide a comprehensive news-based analysis.

Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Exchange: {stock_data.get('exchange', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {f"${stock_data.get('current_price', 0):,.2f}" if stock_data.get('current_price') else "N/A"}
{news_summary}

Please provide a comprehensive news analysis in the following JSON format:

{{
    "summary": "Executive summary of the news sentiment and impact (2-3 sentences)",
    "news_sentiment": {{
        "overall_sentiment": "positive/negative/neutral",
        "sentiment_strength": "strong/moderate/weak",
        "news_volume": "high/moderate/low",
        "sentiment_trend": "improving/declining/stable"
    }},
    "key_news_themes": [
        "Main theme 1",
        "Main theme 2",
        "Main theme 3"
    ],
    "news_impact_analysis": {{
        "price_impact": "positive/negative/neutral",
        "short_term_outlook": "bullish/bearish/neutral",
        "long_term_outlook": "bullish/bearish/neutral",
        "risk_factors": ["risk factor 1", "risk factor 2"]
    }},
    "market_sentiment": {{
        "investor_sentiment": "optimistic/cautious/pessimistic",
        "analyst_sentiment": "positive/negative/neutral",
        "media_sentiment": "positive/negative/neutral"
    }},
    "news_insights": [
        "Key news insight 1",
        "Key news insight 2",
        "Key news insight 3"
    ],
    "recommendations": {{
        "action": "buy/hold/sell",
        "confidence": 0.0-1.0,
        "reasoning": "Detailed reasoning based on news analysis"
    }}
}}

Provide only valid JSON, no additional text.
"""

    def _parse_llm_response(
        self, response: str, stock_data: Dict[str, Any], model_used: str = "auto"
    ) -> Dict[str, Any]:
        """Parse LLM response into structured news analysis data"""
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
                "analysis_type": "news",
                "summary": analysis_json.get("summary", ""),
                "key_insights": analysis_json.get("news_insights", []),
                "risk_assessment": {
                    "news_sentiment": analysis_json.get("news_sentiment", {}),
                    "news_impact_analysis": analysis_json.get(
                        "news_impact_analysis", {}
                    ),
                    "market_sentiment": analysis_json.get("market_sentiment", {}),
                    "key_news_themes": analysis_json.get("key_news_themes", []),
                },
                "recommendations": analysis_json.get("recommendations", {}),
                "llm_model": model_used,
                "llm_prompt": self._create_news_prompt(stock_data, []),
                "llm_response": analysis_json,
                "confidence_score": analysis_json.get("recommendations", {}).get(
                    "confidence", 0.5
                ),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Fallback: create basic analysis from response text
            return {
                "analysis_type": "news",
                "summary": response[:500] if len(response) > 500 else response,
                "key_insights": [
                    response[i : i + 200]
                    for i in range(0, min(600, len(response)), 200)
                ],
                "risk_assessment": {},
                "recommendations": {
                    "action": "hold",
                    "confidence": 0.5,
                    "reasoning": response,
                },
                "llm_model": model_used,
                "llm_prompt": self._create_news_prompt(stock_data, []),
                "llm_response": {"raw_response": response},
                "confidence_score": 0.5,
            }
