"""
Stock Analysis Agent - Uses CrewAI and LLM to analyze stocks
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.multi_model_service import multi_model_service, TaskComplexity
from app.services.stock_service import StockService

logger = logging.getLogger(__name__)


class StockAnalysisAgent:
    """Agent for generating comprehensive stock analysis using LLM"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_service = StockService(db, context)

    async def analyze_stock(self, stock_symbol: str) -> Dict[str, Any]:
        """
        Generate comprehensive stock analysis using LLM.
        Returns structured analysis data.
        """
        try:
            # Get stock data
            stock_data = await self.stock_service.get_stock_by_symbol(stock_symbol)
            if not stock_data:
                raise ValueError(f"Stock {stock_symbol} not found")

            # Save stock to database if not already saved
            stock = await self.stock_service.save_stock(stock_data)

            # Generate analysis prompt
            prompt = self._create_analysis_prompt(stock_data)

            # Call LLM for analysis
            logger.info(f"🤖 Generating stock analysis for {stock_symbol} using LLM")
            response_data = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="analysis",
                complexity=TaskComplexity.AGENTIC,  # Use agentic complexity for comprehensive analysis
            )

            # Extract the actual response text from the response dict
            # multi_model_service returns {"response": "...", "status": "...", ...}
            response_text = response_data.get("response") or response_data.get("content", "")
            
            if not response_text:
                raise ValueError(f"Empty response from LLM for {stock_symbol}")

            # Parse LLM response into structured format
            analysis_data = self._parse_llm_response(response_text, stock_data)

            # Save analysis to database
            analysis = await self.stock_service.save_stock_analysis(
                UUID(str(stock.id)), analysis_data
            )

            logger.info(f"✅ Stock analysis completed for {stock_symbol}")

            return {
                "stock": stock.to_dict(),
                "analysis": analysis.to_dict(),
            }

        except Exception as e:
            logger.error(f"Error analyzing stock {stock_symbol}: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _create_analysis_prompt(self, stock_data: Dict[str, Any]) -> str:
        """Create comprehensive prompt for stock analysis"""
        # Safely format numeric values that might be None
        current_price = stock_data.get('current_price')
        previous_close = stock_data.get('previous_close')
        price_change_percent = stock_data.get('price_change_percent')
        market_cap = stock_data.get('market_cap')
        volume = stock_data.get('volume')
        
        current_price_str = f"${current_price:,.2f}" if current_price is not None else "N/A"
        previous_close_str = f"${previous_close:,.2f}" if previous_close is not None else "N/A"
        price_change_str = f"{price_change_percent:.2f}%" if price_change_percent is not None else "N/A"
        market_cap_str = f"${market_cap:,.0f}" if market_cap is not None else "N/A"
        volume_str = f"{volume:,.0f}" if volume is not None else "N/A"
        
        return f"""
You are a senior financial analyst with expertise in stock market analysis. 
Analyze the following stock and provide a comprehensive analysis.

Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Exchange: {stock_data.get('exchange', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {current_price_str}
- Previous Close: {previous_close_str}
- Price Change: {price_change_str}
- Market Cap: {market_cap_str}
- Volume: {volume_str}

Please provide a comprehensive analysis in the following JSON format:

{{
    "summary": "Executive summary of the stock (2-3 sentences)",
    "key_insights": [
        "Key insight 1",
        "Key insight 2",
        "Key insight 3"
    ],
    "technical_analysis": {{
        "trend": "bullish/bearish/neutral",
        "support_levels": [price1, price2],
        "resistance_levels": [price1, price2],
        "indicators": {{
            "rsi": "overbought/oversold/neutral",
            "macd": "bullish/bearish/neutral",
            "moving_averages": "above/below/neutral"
        }}
    }},
    "fundamental_analysis": {{
        "valuation": "overvalued/undervalued/fair",
        "financial_health": "strong/moderate/weak",
        "growth_prospects": "positive/neutral/negative",
        "competitive_position": "strong/moderate/weak"
    }},
    "risk_assessment": {{
        "overall_risk": "low/medium/high",
        "key_risks": [
            "Risk factor 1",
            "Risk factor 2"
        ],
        "volatility": "low/medium/high"
    }},
    "recommendations": {{
        "action": "buy/hold/sell",
        "confidence": 0.0-1.0,
        "reasoning": "Detailed reasoning for the recommendation"
    }},
    "price_targets": {{
        "short_term_1m": price,
        "medium_term_3m": price,
        "long_term_12m": price,
        "target_basis": "Brief explanation of price targets"
    }}
}}

Provide only valid JSON, no additional text.
"""

    def _parse_llm_response(
        self, response: str, stock_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM response into structured analysis data"""
        import json
        import re

        try:
            # Try to extract JSON from response
            # Remove markdown code blocks if present
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
                "analysis_type": "comprehensive",
                "summary": analysis_json.get("summary", ""),
                "key_insights": analysis_json.get("key_insights", []),
                "technical_analysis": analysis_json.get("technical_analysis", {}),
                "fundamental_analysis": analysis_json.get("fundamental_analysis", {}),
                "risk_assessment": analysis_json.get("risk_assessment", {}),
                "recommendations": analysis_json.get("recommendations", {}),
                "price_targets": analysis_json.get("price_targets", {}),
                "llm_model": "llama4_maverick",  # Model used
                "llm_prompt": self._create_analysis_prompt(stock_data),
                "llm_response": analysis_json,
                "confidence_score": analysis_json.get("recommendations", {}).get(
                    "confidence", 0.5
                ),
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Fallback: create basic analysis from response text
            return {
                "analysis_type": "comprehensive",
                "summary": response[:500] if len(response) > 500 else response,
                "key_insights": [response[i : i + 200] for i in range(0, min(600, len(response)), 200)],
                "technical_analysis": {},
                "fundamental_analysis": {},
                "risk_assessment": {},
                "recommendations": {"action": "hold", "confidence": 0.5, "reasoning": response},
                "price_targets": {},
                "llm_model": "llama4_maverick",
                "llm_prompt": self._create_analysis_prompt(stock_data),
                "llm_response": {"raw_response": response},
                "confidence_score": 0.5,
            }

