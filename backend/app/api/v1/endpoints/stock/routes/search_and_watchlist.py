"""
Search, history, watchlist, and compare stock endpoints.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.watchlist import Watchlist
from app.services.stock_analysis_agent import StockAnalysisAgent
from app.services.stock_service import StockService

from .schemas import (
    StockAnalysisRequest,
    StockAnalysisResponse,
    StockSearchResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    q: str = Query(..., description="Search query (symbol or company name)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        stock_service = StockService(db, context)
        stocks = await stock_service.search_stocks(q, limit)
        return StockSearchResponse(
            success=True, stocks=stocks, count=len(stocks), query=q
        )
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search stocks: {str(e)}"
        )


@router.get("/search/history", response_model=dict)
async def get_search_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        from app.services.cassandra_service import cassandra_service

        history = await cassandra_service.get_search_history(
            context.client_account_id,
            str(context.user_id or "system"),
            days=days,
            limit=limit,
        )
        return {
            "success": True,
            "history": history,
            "count": len(history),
            "days": days,
        }
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get search history: {str(e)}"
        )


@router.get("/search/analytics", response_model=dict)
async def get_search_analytics(
    year_month: Optional[str] = Query(
        None, description="Year-month (e.g., '2025-01'), defaults to current month"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        from app.services.cassandra_service import cassandra_service

        analytics = await cassandra_service.get_search_analytics(
            context.client_account_id,
            str(context.user_id or "system"),
            year_month=year_month,
        )
        if not analytics:
            return {
                "success": True,
                "analytics": None,
                "message": "No analytics data available for this period",
            }
        return {"success": True, "analytics": analytics}
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get search analytics: {str(e)}"
        )


@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
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
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze stock: {str(e)}"
        )


@router.get("/watchlist", response_model=dict)
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
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

        stock_service = StockService(db, context)
        watchlist_with_data = []
        for item in watchlist_items:
            stock_data = await stock_service.get_stock_by_symbol(item.stock_symbol)
            watchlist_with_data.append({**item.to_dict(), "stock_data": stock_data})
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
    try:
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

        stock_service = StockService(db, context)
        stock_data = await stock_service.get_stock_by_symbol(symbol)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        stock = await stock_service.save_stock(stock_data)
        await db.commit()

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


@router.get("/compare", response_model=dict)
async def compare_stocks(
    symbols: str = Query(
        ..., description="Comma-separated list of stock symbols to compare"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
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
