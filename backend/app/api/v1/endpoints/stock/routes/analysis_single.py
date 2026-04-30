"""
Single-agent stock analysis endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.stock_financials_agent_modular import StockFinancialsAgent
from app.services.stock_history_agent import StockHistoryAgent
from app.services.stock_news_agent import StockNewsAgent
from app.services.stock_service import StockService
from app.services.stock_statistics_agent import StockStatisticsAgent

from .schemas import StockAnalysisRequest, StockAnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")


@router.post("/analyze/financials", response_model=StockAnalysisResponse)
async def analyze_stock_financials(
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
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
    try:
        stock_service = StockService(db, context)
        news_data = await stock_service.get_stock_news(
            request.symbol, limit=50, months_back=6
        )
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
