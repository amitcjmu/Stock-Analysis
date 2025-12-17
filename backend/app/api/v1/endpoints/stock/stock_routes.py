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
from app.models.watchlist import Watchlist
from sqlalchemy import select, and_, delete

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
