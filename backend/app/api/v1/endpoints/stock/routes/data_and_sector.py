"""
Stock data, sector, screener, and news endpoints.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.stock_financials_agent_modular import StockFinancialsAgent
from app.services.stock_service import StockService

from .schemas import (
    StockDetailResponse,
    clean_json_response,
    parse_llm_news_response,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")

DEFENCE_STOCK_UNIVERSE = [
    "HAL.NS",
    "BEL.NS",
    "BDL.NS",
    "MAZDOCK.NS",
    "COCHINSHIP.NS",
    "GRSE.NS",
    "PARAS.NS",
    "DATAPATTNS.NS",
    "MTARTECH.NS",
    "SOLARINDS.NS",
    "ASTRAMICRO.NS",
]


@router.get("/sectors/trending", response_model=dict)
async def get_trending_sectors(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        stock_service = StockService(db, context)
        sectors = await stock_service.get_trending_sectors()
        return {"success": True, "sectors": sectors, "count": len(sectors)}
    except Exception as e:
        logger.error(f"Error getting trending sectors: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get trending sectors: {str(e)}"
        )


@router.get("/sectors/{sector_id}/stocks", response_model=dict)
async def get_sector_stocks(
    sector_id: str,
    refresh: bool = Query(False, description="Force refresh from API"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        stock_service = StockService(db, context)
        result = await stock_service.get_stocks_for_sector(sector_id, refresh=refresh)
        if not result.get("sector"):
            raise HTTPException(status_code=404, detail=f"Sector {sector_id} not found")
        return {
            "success": True,
            "sector": result.get("sector"),
            "stocks": result.get("stocks", []),
            "count": len(result.get("stocks", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stocks for sector {sector_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sector stocks: {str(e)}"
        )


@router.get("/screen/defence", response_model=dict)
async def screen_defence_stocks(
    min_score: float = Query(
        55.0, ge=0.0, le=100.0, description="Minimum investment score (0-100)"
    ),
    price_band: Optional[str] = Query(
        None, description="Price band filter: low_price, mid_price, high_price"
    ),
    max_price: Optional[float] = Query(
        None, gt=0.0, description="Optional maximum current price filter"
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    refresh: bool = Query(False, description="Force refresh from API"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        if price_band and price_band not in {"low_price", "mid_price", "high_price"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid price_band. Use low_price, mid_price, or high_price.",
            )

        stock_service = StockService(db, context)
        financials_agent = StockFinancialsAgent(db, context)
        screened_results = []

        for symbol in DEFENCE_STOCK_UNIVERSE:
            stock_data = await stock_service.get_stock_by_symbol(
                symbol, force_refresh=refresh
            )
            if not stock_data:
                continue

            scorecard = financials_agent._build_investment_scorecard(stock_data)
            overall_score = float(scorecard.get("overall_score") or 0.0)
            price_position = scorecard.get("price_position") or {}
            current_price = price_position.get("current_price")
            stock_price_band = price_position.get("price_band")

            if overall_score < min_score:
                continue
            if price_band and stock_price_band != price_band:
                continue
            if (
                max_price is not None
                and current_price is not None
                and current_price > max_price
            ):
                continue

            screened_results.append(
                {
                    "symbol": stock_data.get("symbol") or symbol,
                    "company_name": stock_data.get("company_name"),
                    "sector": stock_data.get("sector"),
                    "industry": stock_data.get("industry"),
                    "exchange": stock_data.get("exchange"),
                    "scorecard": scorecard,
                }
            )

        screened_results.sort(
            key=lambda item: (
                float(item.get("scorecard", {}).get("overall_score") or 0.0),
                -float(
                    item.get("scorecard", {})
                    .get("price_position", {})
                    .get("current_price")
                    or 0.0
                ),
            ),
            reverse=True,
        )

        return {
            "success": True,
            "filters": {
                "min_score": min_score,
                "price_band": price_band,
                "max_price": max_price,
                "refresh": refresh,
            },
            "total_universe": len(DEFENCE_STOCK_UNIVERSE),
            "matched_count": len(screened_results),
            "stocks": screened_results[:limit],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error screening defence stocks: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to screen defence stocks: {str(e)}"
        )


@router.get("/{symbol}", response_model=StockDetailResponse)
async def get_stock(
    symbol: str,
    refresh: bool = Query(False, description="Force refresh from API (bypass cache)"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
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
    period: str = Query("1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, ..."),
    interval: str = Query("1d", description="Interval: 1m, 5m, 1h, 1d, 1wk, ..."),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
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


def _determine_model_type(model: Optional[str]):
    """Stock LLM routes use Anthropic only; query param model is ignored."""
    from app.services.multi_model_service import ModelType

    return ModelType.CLAUDE_OPUS_4_6


@router.get("/{symbol}/news", response_model=dict)
async def get_stock_news(
    symbol: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of news articles"),
    months_back: int = Query(6, ge=1, le=12, description="Months to look back"),
    model: Optional[str] = Query(None, description="Model option (ignored)"),
    include_llm_news: bool = Query(True, description="Include LLM-generated insights"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    try:
        stock_service = StockService(db, context)
        indian_news = await stock_service.get_stock_news(
            symbol, limit, months_back=months_back
        )
        llm_news_insights = []

        if include_llm_news:
            try:
                from app.services.multi_model_service import (
                    TaskComplexity,
                    multi_model_service,
                )

                stock_data = await stock_service.get_stock_by_symbol(symbol)
                if stock_data:
                    model_type = _determine_model_type(model)
                    company_name = stock_data.get("company_name", symbol)
                    llm_prompt = f"""
You are a financial news analyst. Based on stock information for {company_name} ({symbol}),
generate 3-5 recent news insights relevant to investors.
Provide only valid JSON array with fields: title, summary, category, impact, source.
"""
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
                        if response_text and response_text.strip():
                            response_clean = clean_json_response(response_text)
                            llm_news_insights.extend(
                                parse_llm_news_response(
                                    response_text, response_clean, symbol
                                )
                            )
            except Exception as e:
                logger.error(f"Error generating LLM news insights: {e}", exc_info=True)

        combined_news = llm_news_insights + indian_news
        return {
            "success": True,
            "symbol": symbol,
            "news": combined_news,
            "count": len(combined_news),
            "indian_news_count": len(indian_news),
            "llm_count": len(llm_news_insights),
            "generated_at": int(datetime.now().timestamp()),
        }
    except Exception as e:
        logger.error(f"Error getting stock news for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get stock news: {str(e)}"
        )
