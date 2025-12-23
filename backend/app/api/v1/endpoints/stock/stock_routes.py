"""
Stock API Routes - Stock search and analysis endpoints
"""

import logging
import json
import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.stock_service import StockService
from app.services.stock_analysis_agent import StockAnalysisAgent
from app.services.stock_financials_agent import StockFinancialsAgent
from app.services.stock_statistics_agent import StockStatisticsAgent
from app.services.stock_history_agent import StockHistoryAgent
from app.services.stock_news_agent import StockNewsAgent
from app.models.watchlist import Watchlist
from sqlalchemy import select, and_, delete
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="")


# Helper functions for get_stock_news
def _determine_model_type(model: Optional[str]):
    """Determine ModelType from model string."""
    if not model:
        return None
    model_lower = model.lower()
    from app.services.multi_model_service import ModelType

    if model_lower == "gemini":
        return ModelType.GEMINI
    if model_lower in ("llama4_maverick", "llama"):
        return ModelType.LLAMA_4_MAVERICK
    if model_lower in ("gemma3_4b", "gemma"):
        return ModelType.GEMMA_3_4B
    return None


def _clean_json_response(response_text: str) -> str:
    """Extract and clean JSON from LLM response text."""
    response_clean = response_text.strip()

    # Remove markdown code blocks
    if "```json" in response_clean:
        json_match = re.search(r"```json\s*(.*?)\s*```", response_clean, re.DOTALL)
        if json_match:
            response_clean = json_match.group(1).strip()
    elif "```" in response_clean:
        json_match = re.search(r"```\s*(.*?)\s*```", response_clean, re.DOTALL)
        if json_match:
            response_clean = json_match.group(1).strip()

    # Try to find JSON array
    json_match = re.search(r"\[.*\]", response_clean, re.DOTALL)
    if json_match:
        response_clean = json_match.group(0)

    return response_clean


def _format_llm_insight(insight: dict, symbol: str, index: int) -> dict:
    """Format a single LLM insight to match Yahoo Finance format."""
    return {
        "title": insight.get("title", "AI News Insight"),
        "publisher": insight.get("source", "AI Analysis"),
        "link": "",
        "published_date": int(datetime.now().timestamp()),
        "uuid": f"llm-{symbol}-{index}",
        "summary": insight.get("summary", ""),
        "category": insight.get("category", "market_update"),
        "impact": insight.get("impact", "neutral"),
        "is_llm_generated": True,
    }


def _parse_llm_news_response(
    response_text: str, response_clean: str, symbol: str
) -> List[dict]:
    """Parse LLM news response and return formatted insights."""
    llm_news_insights = []

    try:
        llm_news_data = json.loads(response_clean)
        if isinstance(llm_news_data, list) and len(llm_news_data) > 0:
            # Format LLM news to match Yahoo Finance format
            for idx, insight in enumerate(llm_news_data[:5]):  # Limit to 5 insights
                if isinstance(insight, dict) and insight.get("title"):
                    llm_news_insights.append(_format_llm_insight(insight, symbol, idx))
            logger.info(
                f"Generated {len(llm_news_insights)} LLM news insights for {symbol}"
            )
        elif isinstance(llm_news_data, dict):
            # Handle case where LLM returns a single object instead of array
            logger.warning(
                "LLM returned a single object instead of array, converting to array"
            )
            if llm_news_data.get("title"):
                llm_news_insights.append(_format_llm_insight(llm_news_data, symbol, 0))
                logger.info(
                    f"Generated 1 LLM news insight from single object for {symbol}"
                )
        else:
            news_data_str = str(llm_news_data)[:200]
            logger.warning(
                f"LLM returned non-list news data: {type(llm_news_data)}, "
                f"value: {news_data_str}"
            )
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM news response as JSON: {e}")
        logger.warning(f"Response text that failed to parse: {response_clean[:500]}")
        # Try to create a fallback insight from the raw response
        if response_text and len(response_text) > 20:
            llm_news_insights.append(
                {
                    "title": f"Market Analysis for {symbol}",
                    "publisher": "AI Analysis",
                    "link": "",
                    "published_date": int(datetime.now().timestamp()),
                    "uuid": f"llm-{symbol}-fallback",
                    "summary": (
                        response_text[:300] + "..."
                        if len(response_text) > 300
                        else response_text
                    ),
                    "category": "market_update",
                    "impact": "neutral",
                    "is_llm_generated": True,
                }
            )
            logger.info(
                f"Created fallback LLM news insight from raw response for {symbol}"
            )

    return llm_news_insights


# Request/Response Models
class StockSearchResponse(BaseModel):
    """Response model for stock search"""

    success: bool
    stocks: List[dict]
    count: int
    query: str


class StockDetailResponse(BaseModel):
    """Response model for stock details"""

    success: bool
    stock: dict


class StockAnalysisRequest(BaseModel):
    """Request model for stock analysis"""

    symbol: str = Field(..., description="Stock symbol to analyze")
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use (gemini, llama4_maverick, gemma3_4b, auto). Defaults to auto selection.",
    )


class StockAnalysisResponse(BaseModel):
    """Response model for stock analysis"""

    success: bool
    stock: dict
    analysis: dict
    message: str


# IMPORTANT: Specific routes must come BEFORE parameterized routes
# to prevent route conflicts (e.g., /watchlist matching /{symbol})


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    q: str = Query(..., description="Search query (symbol or company name)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Search for stocks by symbol or company name.
    """
    try:
        stock_service = StockService(db, context)
        stocks = await stock_service.search_stocks(q, limit)

        return StockSearchResponse(
            success=True,
            stocks=stocks,
            count=len(stocks),
            query=q,
        )

    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search stocks: {str(e)}"
        )


@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Generate comprehensive stock analysis using LLM agent.
    """
    try:
        agent = StockAnalysisAgent(db, context)
        result = await agent.analyze_stock(request.symbol, model=request.model)

        return StockAnalysisResponse(
            success=True,
            stock=result["stock"],
            analysis=result["analysis"],
            message=f"Analysis completed for {request.symbol}",
        )

    except ValueError as e:
        logger.error(f"ValueError analyzing stock {request.symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing stock {request.symbol}: {e}", exc_info=True)
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze stock: {str(e)}"
        )


# Watchlist endpoints (must come before /{symbol} route)
@router.get("/watchlist", response_model=dict)
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get user's watchlist.
    """
    try:
        stmt = (
            select(Watchlist)
            .where(
                and_(
                    Watchlist.client_account_id == context.client_account_id,
                    Watchlist.engagement_id == context.engagement_id,
                    Watchlist.user_id == context.user_id,
                )
            )
            .order_by(Watchlist.created_at.desc())
        )
        result = await db.execute(stmt)
        watchlist_items = result.scalars().all()

        # Get stock data for each watchlist item
        stock_service = StockService(db, context)
        watchlist_with_data = []
        for item in watchlist_items:
            stock_data = await stock_service.get_stock_by_symbol(item.stock_symbol)
            watchlist_with_data.append(
                {
                    **item.to_dict(),
                    "stock_data": stock_data,
                }
            )

        return {"success": True, "watchlist": watchlist_with_data}

    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get watchlist: {str(e)}"
        )


@router.post("/watchlist", response_model=dict)
async def add_to_watchlist(
    symbol: str = Query(..., description="Stock symbol to add"),
    notes: Optional[str] = Query(None, description="Optional notes"),
    alert_price: Optional[str] = Query(None, description="Optional price alert"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Add a stock to user's watchlist.
    """
    try:
        # Check if already in watchlist
        stmt = select(Watchlist).where(
            and_(
                Watchlist.stock_symbol == symbol.upper(),
                Watchlist.client_account_id == context.client_account_id,
                Watchlist.engagement_id == context.engagement_id,
                Watchlist.user_id == context.user_id,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=400, detail=f"Stock {symbol} is already in watchlist"
            )

        # Get or create stock
        stock_service = StockService(db, context)
        stock_data = await stock_service.get_stock_by_symbol(symbol)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        # Save stock to database
        stock = await stock_service.save_stock(stock_data)
        await db.commit()

        # Create watchlist entry
        watchlist_item = Watchlist(
            stock_symbol=symbol.upper(),
            stock_id=UUID(str(stock.id)),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,
            notes=notes,
            alert_price=alert_price,
        )
        db.add(watchlist_item)
        await db.commit()

        return {
            "success": True,
            "message": f"Added {symbol} to watchlist",
            "watchlist_item": watchlist_item.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to add to watchlist: {str(e)}"
        )


@router.delete("/watchlist/{symbol}", response_model=dict)
async def remove_from_watchlist(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Remove a stock from user's watchlist.
    """
    try:
        stmt = delete(Watchlist).where(
            and_(
                Watchlist.stock_symbol == symbol.upper(),
                Watchlist.client_account_id == context.client_account_id,
                Watchlist.engagement_id == context.engagement_id,
                Watchlist.user_id == context.user_id,
            )
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404, detail=f"Stock {symbol} not found in watchlist"
            )

        return {"success": True, "message": f"Removed {symbol} from watchlist"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to remove from watchlist: {str(e)}"
        )


# Comparison endpoint (must come before /{symbol} route)
@router.get("/compare", response_model=dict)
async def compare_stocks(
    symbols: str = Query(
        ..., description="Comma-separated list of stock symbols to compare"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Compare multiple stocks side by side.
    """
    try:
        # Parse comma-separated symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        if len(symbol_list) < 2:
            raise HTTPException(
                status_code=400, detail="At least 2 stocks required for comparison"
            )
        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 stocks allowed for comparison"
            )

        stock_service = StockService(db, context)
        comparison_data = []

        for symbol in symbol_list:
            stock_data = await stock_service.get_stock_by_symbol(symbol)
            if stock_data:
                comparison_data.append(stock_data)

        if not comparison_data:
            raise HTTPException(
                status_code=404, detail="No valid stocks found for comparison"
            )

        return {
            "success": True,
            "symbols": symbol_list,
            "stocks": comparison_data,
            "count": len(comparison_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing stocks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to compare stocks: {str(e)}"
        )


# Parameterized routes (must come AFTER specific routes)
@router.get("/{symbol}", response_model=StockDetailResponse)
async def get_stock(
    symbol: str,
    refresh: bool = Query(False, description="Force refresh from API (bypass cache)"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get stock details by symbol.

    Args:
        symbol: Stock symbol
        refresh: If True, force refresh from API to get latest price data
    """
    try:
        stock_service = StockService(db, context)
        stock = await stock_service.get_stock_by_symbol(symbol, force_refresh=refresh)

        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        return StockDetailResponse(success=True, stock=stock)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stock: {str(e)}")


@router.get("/{symbol}/historical", response_model=dict)
async def get_historical_prices(
    symbol: str,
    period: str = Query(
        "1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    ),
    interval: str = Query(
        "1d",
        description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo",
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get historical price data for a stock.
    """
    try:
        stock_service = StockService(db, context)
        prices = await stock_service.get_historical_prices(symbol, period, interval)

        if not prices:
            raise HTTPException(
                status_code=404, detail=f"No historical data found for {symbol}"
            )

        return {
            "success": True,
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "prices": prices,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical prices: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get historical prices: {str(e)}"
        )


@router.get("/{stock_id}/analysis", response_model=dict)
async def get_stock_analysis(
    stock_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get latest stock analysis for a stock.
    """
    try:
        stock_service = StockService(db, context)
        analysis = await stock_service.get_stock_analysis(stock_id)

        if not analysis:
            raise HTTPException(
                status_code=404, detail=f"No analysis found for stock {stock_id}"
            )

        return {"success": True, "analysis": analysis}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get stock analysis: {str(e)}"
        )


@router.get("/{symbol}/news", response_model=dict)
async def get_stock_news(
    symbol: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of news articles"),
    model: Optional[str] = Query(
        None,
        description="LLM model to use for news generation (gemini, llama4_maverick, gemma3_4b, auto)",
    ),
    include_llm_news: bool = Query(
        True, description="Include LLM-generated news insights"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get news articles for a stock from Yahoo Finance and LLM-generated insights.
    """
    try:
        stock_service = StockService(db, context)

        # Get Yahoo Finance news
        yfinance_news = await stock_service.get_stock_news(symbol, limit)
        logger.info(
            f"Retrieved {len(yfinance_news)} news articles from Yahoo Finance for {symbol}"
        )

        # Get LLM-generated news insights if requested
        llm_news_insights = []
        if include_llm_news:
            try:
                from app.services.multi_model_service import (
                    multi_model_service,
                    TaskComplexity,
                )

                # Get stock data for context
                stock_data = await stock_service.get_stock_by_symbol(symbol)
                if stock_data:
                    # Determine model type
                    model_type = _determine_model_type(model)

                    # Generate LLM news insights
                    company_name = stock_data.get("company_name", symbol)
                    llm_prompt = f"""
You are a financial news analyst. Based on the current stock information for {company_name} ({symbol}),
generate 3-5 recent news insights that would be relevant to investors. These should be:
- Current market-relevant topics
- Industry trends affecting this stock
- Recent developments or events
- Market sentiment indicators

Stock Information:
- Symbol: {symbol}
- Company: {stock_data.get('company_name', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}
- Industry: {stock_data.get('industry', 'N/A')}
- Current Price: {f"${stock_data.get('current_price', 0):,.2f}" if stock_data.get('current_price') else "N/A"}

Provide the response as a JSON array of news insights, each with:
- title: A compelling news headline
- summary: A brief 2-3 sentence summary
- category: One of: market_update, industry_trend, company_news, analyst_insight, market_sentiment
- impact: positive, negative, or neutral
- source: "AI Analysis"

Format:
[
  {{
    "title": "News headline 1",
    "summary": "Brief summary...",
    "category": "market_update",
    "impact": "positive",
    "source": "AI Analysis"
  }},
  ...
]

Provide only valid JSON array, no additional text.
"""

                    logger.info(
                        f"Generating LLM news insights for {symbol} using model: {model or 'auto'}"
                    )
                    llm_response = await multi_model_service.generate_response(
                        prompt=llm_prompt,
                        task_type="analysis",
                        complexity=TaskComplexity.MEDIUM,
                        model_type=model_type,
                    )

                    if llm_response.get("status") != "error":
                        response_text = llm_response.get(
                            "response"
                        ) or llm_response.get("content", "")
                        logger.info(
                            f"LLM news response length: {len(response_text) if response_text else 0} characters"
                        )
                        logger.debug(
                            f"LLM news response preview: {response_text[:500] if response_text else 'Empty'}"
                        )

                        if response_text and response_text.strip():
                            response_clean = _clean_json_response(response_text)
                            logger.debug(
                                f"Cleaned response for parsing: {response_clean[:200]}..."
                            )
                            insights = _parse_llm_news_response(
                                response_text, response_clean, symbol
                            )
                            llm_news_insights.extend(insights)
                        else:
                            logger.warning(
                                "LLM returned empty response for news generation"
                            )
                    else:
                        error_msg = llm_response.get("error", "Unknown error")
                        logger.warning(f"LLM news generation failed: {error_msg}")
            except Exception as e:
                logger.error(f"Error generating LLM news insights: {e}", exc_info=True)
                # Continue without LLM news if it fails

        # Combine Yahoo Finance news and LLM insights
        # Put LLM insights first, then Yahoo Finance news
        combined_news = llm_news_insights + yfinance_news

        return {
            "success": True,
            "symbol": symbol,
            "news": combined_news,
            "count": len(combined_news),
            "yfinance_count": len(yfinance_news),
            "llm_count": len(llm_news_insights),
        }

    except Exception as e:
        logger.error(f"Error getting stock news for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get stock news: {str(e)}"
        )


@router.post("/analyze/financials", response_model=StockAnalysisResponse)
async def analyze_stock_financials(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Generate financial analysis using specialized Financials agent.
    """
    try:
        agent = StockFinancialsAgent(db, context)
        result = await agent.analyze_financials(request.symbol)

        return StockAnalysisResponse(
            success=True,
            stock=result["stock"],
            analysis=result["analysis"],
            message=f"Financials analysis completed for {request.symbol}",
        )

    except ValueError as e:
        logger.error(
            f"ValueError analyzing financials for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error analyzing financials for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze financials: {str(e)}"
        )


@router.post("/analyze/statistics", response_model=StockAnalysisResponse)
async def analyze_stock_statistics(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Generate statistical analysis using specialized Statistics agent.
    """
    try:
        agent = StockStatisticsAgent(db, context)
        result = await agent.analyze_statistics(request.symbol)

        return StockAnalysisResponse(
            success=True,
            stock=result["stock"],
            analysis=result["analysis"],
            message=f"Statistics analysis completed for {request.symbol}",
        )

    except ValueError as e:
        logger.error(
            f"ValueError analyzing statistics for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error analyzing statistics for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze statistics: {str(e)}"
        )


@router.post("/analyze/history", response_model=StockAnalysisResponse)
async def analyze_stock_history(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Generate historical price analysis using specialized History agent.
    """
    try:
        agent = StockHistoryAgent(db, context)
        result = await agent.analyze_history(request.symbol)

        return StockAnalysisResponse(
            success=True,
            stock=result["stock"],
            analysis=result["analysis"],
            message=f"History analysis completed for {request.symbol}",
        )

    except ValueError as e:
        logger.error(
            f"ValueError analyzing history for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error analyzing history for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze history: {str(e)}"
        )


@router.post("/analyze/news", response_model=StockAnalysisResponse)
async def analyze_stock_news(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Generate news sentiment analysis using specialized News agent.
    """
    try:
        stock_service = StockService(db, context)
        news_data = await stock_service.get_stock_news(request.symbol, limit=20)

        agent = StockNewsAgent(db, context)
        result = await agent.analyze_news(request.symbol, news_data or [])

        return StockAnalysisResponse(
            success=True,
            stock=result["stock"],
            analysis=result["analysis"],
            message=f"News analysis completed for {request.symbol}",
        )

    except ValueError as e:
        logger.error(
            f"ValueError analyzing news for {request.symbol}: {e}", exc_info=True
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing news for {request.symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze news: {str(e)}")


# Helper functions for analyze_stock_all_agents
async def _run_agent(
    agent_class,
    agent_name: str,
    symbol: str,
    model: Optional[str],
    db: AsyncSession,
    context: RequestContext,
) -> tuple:
    """Run a single agent and return its result."""
    try:
        logger.info(f"🚀 [ANALYZE ALL] Starting {agent_name} Agent for {symbol}")
        agent = agent_class(db, context)
        result = await agent.analyze(symbol, model=model)
        logger.info(f"🚀 [ANALYZE ALL] ✅ {agent_name} Agent completed for {symbol}")

        if "analysis" in result and result["analysis"] is not None:
            analysis = result["analysis"]
            analysis_keys = (
                list(analysis.keys()) if isinstance(analysis, dict) else "N/A"
            )
            logger.info(
                f"🚀 [ANALYZE ALL] {agent_name} Agent returned analysis "
                f"with keys: {analysis_keys}"
            )
            return (agent_name.lower(), analysis)
        else:
            logger.error(
                f"🚀 [ANALYZE ALL] {agent_name} Agent result missing 'analysis' key or is None"
            )
            result_keys = (
                list(result.keys()) if isinstance(result, dict) else "N/A"
            )
            logger.error(
                f"🚀 [ANALYZE ALL] {agent_name} Agent result keys: {result_keys}"
            )
            return (agent_name.lower(), None)
    except Exception as e:
        logger.error(
            f"🚀 [ANALYZE ALL] ❌ {agent_name} Agent failed: {e}", exc_info=True
        )
        return (agent_name.lower(), None)


def _process_agent_result(result: tuple, results: dict) -> None:
    """Process a single agent result and add it to results."""
    if isinstance(result, Exception):
        logger.error(f"🚀 [ANALYZE ALL] Agent task exception: {result}")
        results["errors"].append(str(result))
        return

    if not result:
        return

    agent_type, analysis_data = result
    logger.info(
        f"🚀 [ANALYZE ALL] Processing {agent_type} result: "
        f"type={type(analysis_data)}, is None={analysis_data is None}, "
        f"is dict={isinstance(analysis_data, dict)}"
    )

    if analysis_data is None:
        logger.warning(f"🚀 [ANALYZE ALL] ⚠️ {agent_type} returned None")
        results["errors"].append(f"{agent_type} agent returned no data")
        return

    if isinstance(analysis_data, dict) and len(analysis_data) > 0:
        results[agent_type] = analysis_data
        logger.info(f"🚀 [ANALYZE ALL] ✅ {agent_type} data added to results")
    elif isinstance(analysis_data, dict):
        logger.warning(f"🚀 [ANALYZE ALL] ⚠️ {agent_type} returned empty dict")
        results["errors"].append(f"{agent_type} agent returned empty data")
    else:
        logger.warning(
            f"🚀 [ANALYZE ALL] ⚠️ {agent_type} returned non-dict: {type(analysis_data)}"
        )
        results["errors"].append(f"{agent_type} agent returned invalid data type")


def _get_comprehensive_summary(results: dict) -> str:
    """Get summary from first available agent result."""
    if results.get("financials") and results["financials"].get("summary"):
        return results["financials"]["summary"]
    if results.get("statistics") and results["statistics"].get("summary"):
        return results["statistics"]["summary"]
    if results.get("history") and results["history"].get("summary"):
        return results["history"]["summary"]
    if results.get("news") and results["news"].get("summary"):
        return results["news"]["summary"]
    return "Analysis completed"


def _merge_key_insights(results: dict) -> List[str]:
    """Merge key insights from all agents."""
    key_insights = []
    for agent_type in ["financials", "statistics", "history", "news"]:
        if results.get(agent_type) and results[agent_type].get("key_insights"):
            key_insights.extend(results[agent_type]["key_insights"])
    return key_insights


def _merge_technical_analysis(results: dict) -> dict:
    """Merge technical analysis from statistics and history agents."""
    technical_analysis = {}

    # Merge from statistics
    if results.get("statistics"):
        stats_technical = results["statistics"].get("technical_analysis")
        if (
            stats_technical
            and isinstance(stats_technical, dict)
            and len(stats_technical) > 0
        ):
            technical_analysis.update(stats_technical)
            logger.info("🚀 [ANALYZE ALL] ✅ Merged statistics technical_analysis")
        elif results["statistics"].get("summary"):
            technical_analysis["statistics_summary"] = results["statistics"].get(
                "summary", ""
            )
            if results["statistics"].get("key_insights"):
                technical_analysis["statistical_insights"] = results["statistics"].get(
                    "key_insights", []
                )
            logger.info(
                "🚀 [ANALYZE ALL] ✅ Created technical_analysis from statistics summary (fallback)"
            )

    # Merge from history
    if results.get("history"):
        history_technical = results["history"].get("technical_analysis")
        if (
            history_technical
            and isinstance(history_technical, dict)
            and len(history_technical) > 0
        ):
            technical_analysis.update(history_technical)
            logger.info("🚀 [ANALYZE ALL] ✅ Merged history technical_analysis")
        elif results["history"].get("summary"):
            if "history_summary" not in technical_analysis:
                technical_analysis["history_summary"] = results["history"].get(
                    "summary", ""
                )
            if results["history"].get("key_insights"):
                if "technical_patterns" not in technical_analysis:
                    technical_analysis["technical_patterns"] = results["history"].get(
                        "key_insights", []
                    )
            logger.info(
                "🚀 [ANALYZE ALL] ✅ Created technical_analysis from history summary (fallback)"
            )

    return technical_analysis


def _merge_fundamental_analysis(results: dict) -> dict:
    """Merge fundamental analysis from financials agent."""
    fundamental_analysis = {}

    if not results.get("financials"):
        return fundamental_analysis

    financials_fundamental = results["financials"].get("fundamental_analysis")
    if (
        financials_fundamental
        and isinstance(financials_fundamental, dict)
        and len(financials_fundamental) > 0
    ):
        # Check if it has the expected structure
        has_structure = any(
            key in financials_fundamental
            for key in [
                "valuation_analysis",
                "financial_health",
                "key_financial_ratios",
                "growth_analysis",
            ]
        )
        if has_structure:
            fundamental_analysis.update(financials_fundamental)
            logger.info(
                "🚀 [ANALYZE ALL] ✅ Merged financials fundamental_analysis with proper structure"
            )
        else:
            fundamental_keys = list(financials_fundamental.keys())
            logger.warning(
                f"🚀 [ANALYZE ALL] ⚠️ Financials fundamental_analysis exists "
                f"but lacks expected structure. Keys: {fundamental_keys}"
            )
            fundamental_analysis.update(financials_fundamental)
    else:
        logger.warning(
            f"🚀 [ANALYZE ALL] ⚠️ Financials agent did not return fundamental_analysis. "
            f"Summary available: {bool(results['financials'].get('summary'))}"
        )

    return fundamental_analysis


def _merge_risk_assessment(results: dict) -> dict:
    """Merge risk assessment from all agents."""
    risk_assessment = {}
    for agent_type in ["financials", "statistics", "news"]:
        if results.get(agent_type) and results[agent_type].get("risk_assessment"):
            risk_assessment.update(results[agent_type]["risk_assessment"])
    return risk_assessment


def _get_recommendations(results: dict) -> tuple:
    """Get recommendations and confidence score from first available agent."""
    for agent_type in ["financials", "statistics", "history", "news"]:
        if results.get(agent_type) and results[agent_type].get("recommendations"):
            recommendations = results[agent_type]["recommendations"]
            confidence = (
                recommendations.get("confidence", 0.5)
                if isinstance(recommendations, dict)
                else 0.5
            )
            return recommendations, confidence
    return {}, 0.5


def _build_comprehensive_analysis(results: dict) -> Optional[dict]:
    """Build comprehensive analysis by merging all agent results."""
    if not (
        results.get("financials")
        or results.get("statistics")
        or results.get("history")
        or results.get("news")
    ):
        return None

    recommendations, confidence = _get_recommendations(results)

    comprehensive_analysis = {
        "summary": _get_comprehensive_summary(results),
        "key_insights": _merge_key_insights(results),
        "technical_analysis": _merge_technical_analysis(results),
        "fundamental_analysis": _merge_fundamental_analysis(results),
        "risk_assessment": _merge_risk_assessment(results),
        "recommendations": recommendations,
        "confidence_score": confidence,
    }

    # Log what's actually in the analysis for debugging
    has_technical = (
        comprehensive_analysis.get("technical_analysis")
        and isinstance(comprehensive_analysis["technical_analysis"], dict)
        and len(comprehensive_analysis["technical_analysis"]) > 0
    )
    has_fundamental = (
        comprehensive_analysis.get("fundamental_analysis")
        and isinstance(comprehensive_analysis["fundamental_analysis"], dict)
        and len(comprehensive_analysis["fundamental_analysis"]) > 0
    )
    has_risks = (
        comprehensive_analysis.get("risk_assessment")
        and isinstance(comprehensive_analysis["risk_assessment"], dict)
        and len(comprehensive_analysis["risk_assessment"]) > 0
    )
    has_recommendations = (
        comprehensive_analysis.get("recommendations")
        and isinstance(comprehensive_analysis["recommendations"], dict)
        and len(comprehensive_analysis["recommendations"]) > 0
    )

    logger.info(
        f"🚀 [ANALYZE ALL] Created comprehensive analysis with: "
        f"summary={bool(comprehensive_analysis.get('summary'))}, "
        f"technical={has_technical}, fundamental={has_fundamental}, "
        f"risks={has_risks}, recommendations={has_recommendations}"
    )

    return comprehensive_analysis


@router.post("/analyze/all", response_model=dict)
async def analyze_stock_all_agents(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Run all specialized agents concurrently and return comprehensive analysis.
    """
    logger.info(
        f"🚀 [ANALYZE ALL] Starting analysis for {request.symbol} with model: {request.model or 'auto'}"
    )

    results = {
        "success": True,
        "symbol": request.symbol,
        "stock": None,
        "financials": None,
        "statistics": None,
        "history": None,
        "news": None,
        "errors": [],
    }

    try:
        stock_service = StockService(db, context)
        stock_data = await stock_service.get_stock_by_symbol(request.symbol)
        if not stock_data:
            raise HTTPException(
                status_code=404, detail=f"Stock {request.symbol} not found"
            )

        stock = await stock_service.save_stock(stock_data)
        results["stock"] = stock.to_dict()

        async def run_financials():
            try:
                logger.info(
                    f"🚀 [ANALYZE ALL] Starting Financials Agent for {request.symbol}"
                )
                agent = StockFinancialsAgent(db, context)
                result = await agent.analyze_financials(
                    request.symbol, model=request.model
                )
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ Financials Agent completed for {request.symbol}"
                )
                if "analysis" in result and result["analysis"] is not None:
                    analysis = result["analysis"]
                    analysis_keys = (
                        list(analysis.keys()) if isinstance(analysis, dict) else "N/A"
                    )
                    logger.info(
                        f"🚀 [ANALYZE ALL] Financials Agent returned analysis "
                        f"with keys: {analysis_keys}"
                    )
                    return ("financials", analysis)
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] Financials Agent result missing 'analysis' key or is None"
                    )
                    result_keys = (
                        list(result.keys()) if isinstance(result, dict) else "N/A"
                    )
                    logger.error(
                        f"🚀 [ANALYZE ALL] Financials Agent result keys: {result_keys}"
                    )
                    return ("financials", None)
            except Exception as e:
                logger.error(
                    f"🚀 [ANALYZE ALL] ❌ Financials Agent failed: {e}", exc_info=True
                )
                return ("financials", None)

        async def run_statistics():
            try:
                logger.info(
                    f"🚀 [ANALYZE ALL] Starting Statistics Agent for {request.symbol}"
                )
                agent = StockStatisticsAgent(db, context)
                result = await agent.analyze_statistics(
                    request.symbol, model=request.model
                )
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ Statistics Agent completed for {request.symbol}"
                )
                if "analysis" in result and result["analysis"] is not None:
                    analysis = result["analysis"]
                    analysis_keys = (
                        list(analysis.keys()) if isinstance(analysis, dict) else "N/A"
                    )
                    logger.info(
                        f"🚀 [ANALYZE ALL] Statistics Agent returned analysis "
                        f"with keys: {analysis_keys}"
                    )
                    return ("statistics", analysis)
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] Statistics Agent result missing 'analysis' key or is None"
                    )
                    result_keys = (
                        list(result.keys()) if isinstance(result, dict) else "N/A"
                    )
                    logger.error(
                        f"🚀 [ANALYZE ALL] Statistics Agent result keys: {result_keys}"
                    )
                    return ("statistics", None)
            except Exception as e:
                logger.error(
                    f"🚀 [ANALYZE ALL] ❌ Statistics Agent failed: {e}", exc_info=True
                )
                return ("statistics", None)

        async def run_history():
            try:
                logger.info(
                    f"🚀 [ANALYZE ALL] Starting History Agent for {request.symbol}"
                )
                agent = StockHistoryAgent(db, context)
                result = await agent.analyze_history(
                    request.symbol, model=request.model
                )
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ History Agent completed for {request.symbol}"
                )
                if "analysis" in result and result["analysis"] is not None:
                    analysis = result["analysis"]
                    analysis_keys = (
                        list(analysis.keys()) if isinstance(analysis, dict) else "N/A"
                    )
                    logger.info(
                        f"🚀 [ANALYZE ALL] History Agent returned analysis "
                        f"with keys: {analysis_keys}"
                    )
                    return ("history", analysis)
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] History Agent result missing 'analysis' key or is None"
                    )
                    result_keys = (
                        list(result.keys()) if isinstance(result, dict) else "N/A"
                    )
                    logger.error(
                        f"🚀 [ANALYZE ALL] History Agent result keys: {result_keys}"
                    )
                    return ("history", None)
            except Exception as e:
                logger.error(
                    f"🚀 [ANALYZE ALL] ❌ History Agent failed: {e}", exc_info=True
                )
                return ("history", None)

        async def run_news():
            try:
                logger.info(
                    f"🚀 [ANALYZE ALL] Starting News Agent for {request.symbol}"
                )
                news_data = await stock_service.get_stock_news(request.symbol, limit=20)
                logger.info(
                    f"🚀 [ANALYZE ALL] Retrieved {len(news_data) if news_data else 0} news articles"
                )
                agent = StockNewsAgent(db, context)
                result = await agent.analyze_news(
                    request.symbol, news_data or [], model=request.model
                )
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ News Agent completed for {request.symbol}"
                )
                if "analysis" in result:
                    analysis_data = result["analysis"]
                    if isinstance(analysis_data, dict):
                        return ("news", analysis_data)
                    else:
                        return (
                            "news",
                            (
                                analysis_data.to_dict()
                                if hasattr(analysis_data, "to_dict")
                                else analysis_data
                            ),
                        )
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] News Agent result missing 'analysis' key"
                    )
                    return ("news", None)
            except Exception as e:
                logger.error(
                    f"🚀 [ANALYZE ALL] ❌ News Agent failed: {e}", exc_info=True
                )
                return ("news", None)

        # Run all agents concurrently
        logger.info(
            f"🚀 [ANALYZE ALL] Running all agents concurrently for {request.symbol}"
        )
        tasks = [run_financials(), run_statistics(), run_history(), run_news()]
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in agent_results:
            _process_agent_result(result, results)

        logger.info(f"🚀 [ANALYZE ALL] ✅ All agents completed for {request.symbol}")
        logger.info(
            f"🚀 [ANALYZE ALL] Results: Financials={results['financials'] is not None}, "
            f"Statistics={results['statistics'] is not None}, "
            f"History={results['history'] is not None}, "
            f"News={results['news'] is not None}"
        )

        # Log detailed results for debugging
        if results["financials"]:
            logger.info(
                f"🚀 [ANALYZE ALL] Financials summary: {results['financials'].get('summary', 'N/A')[:100]}"
            )
        if results["statistics"]:
            logger.info(
                f"🚀 [ANALYZE ALL] Statistics summary: {results['statistics'].get('summary', 'N/A')[:100]}"
            )
        if results["history"]:
            logger.info(
                f"🚀 [ANALYZE ALL] History summary: {results['history'].get('summary', 'N/A')[:100]}"
            )
        if results["news"]:
            logger.info(
                f"🚀 [ANALYZE ALL] News summary: {results['news'].get('summary', 'N/A')[:100]}"
            )

        # Create a comprehensive analysis by merging all agent results
        # This is used for the "Overview" tab in the frontend
        comprehensive_analysis = _build_comprehensive_analysis(results)
        results["analysis"] = comprehensive_analysis

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"🚀 [ANALYZE ALL] ❌ Error in analyze_all for {request.symbol}: {e}",
            exc_info=True,
        )
        results["success"] = False
        results["errors"].append(str(e))
        return results
