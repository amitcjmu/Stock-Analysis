"""
Stock API Routes - Stock search and analysis endpoints
"""

import logging
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
        result = await agent.analyze_stock(request.symbol)

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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get stock details by symbol.
    """
    try:
        stock_service = StockService(db, context)
        stock = await stock_service.get_stock_by_symbol(symbol)

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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get news articles for a stock.
    """
    try:
        stock_service = StockService(db, context)
        news = await stock_service.get_stock_news(symbol, limit)

        return {
            "success": True,
            "symbol": symbol,
            "news": news,
            "count": len(news),
        }

    except Exception as e:
        logger.error(f"Error getting stock news for {symbol}: {e}")
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


@router.post("/analyze/all", response_model=dict)
async def analyze_stock_all_agents(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Run all specialized agents concurrently and return comprehensive analysis.
    """
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
                result = await agent.analyze_financials(request.symbol)
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ Financials Agent completed for {request.symbol}"
                )
                if "analysis" in result and result["analysis"] is not None:
                    return ("financials", result["analysis"])
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] Financials Agent result missing 'analysis' key or is None"
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
                result = await agent.analyze_statistics(request.symbol)
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ Statistics Agent completed for {request.symbol}"
                )
                if "analysis" in result and result["analysis"] is not None:
                    return ("statistics", result["analysis"])
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] Statistics Agent result missing 'analysis' key or is None"
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
                result = await agent.analyze_history(request.symbol)
                logger.info(
                    f"🚀 [ANALYZE ALL] ✅ History Agent completed for {request.symbol}"
                )
                if "analysis" in result and result["analysis"] is not None:
                    return ("history", result["analysis"])
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] History Agent result missing 'analysis' key or is None"
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
                result = await agent.analyze_news(request.symbol, news_data or [])
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
            if isinstance(result, Exception):
                logger.error(f"🚀 [ANALYZE ALL] Agent task exception: {result}")
                results["errors"].append(str(result))
            elif result:
                agent_type, analysis_data = result
                logger.info(
                    f"🚀 [ANALYZE ALL] Processing {agent_type} result: "
                    f"type={type(analysis_data)}, is None={analysis_data is None}, "
                    f"is dict={isinstance(analysis_data, dict)}"
                )
                if analysis_data is not None:
                    if isinstance(analysis_data, dict) and len(analysis_data) > 0:
                        results[agent_type] = analysis_data
                        logger.info(
                            f"🚀 [ANALYZE ALL] ✅ {agent_type} data added to results"
                        )
                    elif isinstance(analysis_data, dict):
                        logger.warning(
                            f"🚀 [ANALYZE ALL] ⚠️ {agent_type} returned empty dict"
                        )
                        results["errors"].append(
                            f"{agent_type} agent returned empty data"
                        )
                    else:
                        logger.warning(
                            f"🚀 [ANALYZE ALL] ⚠️ {agent_type} returned non-dict: {type(analysis_data)}"
                        )
                        results["errors"].append(
                            f"{agent_type} agent returned invalid data type"
                        )
                else:
                    logger.warning(f"🚀 [ANALYZE ALL] ⚠️ {agent_type} returned None")
                    results["errors"].append(f"{agent_type} agent returned no data")

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
