"""
Parallel multi-agent stock analysis endpoint and merge helpers.
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.stock_financials_agent_modular import StockFinancialsAgent
from app.services.stock_history_agent import StockHistoryAgent
from app.services.stock_news_agent import StockNewsAgent
from app.services.stock_service import StockService
from app.services.stock_statistics_agent import StockStatisticsAgent

from .schemas import StockAnalysisRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="")


def _process_agent_result(result: tuple, results: dict) -> None:
    if isinstance(result, Exception):
        results["errors"].append(str(result))
        return
    if not result:
        return
    agent_type, analysis_data = result
    if analysis_data is None:
        results["errors"].append(f"{agent_type} agent returned no data")
        return
    if isinstance(analysis_data, dict) and analysis_data:
        results[agent_type] = analysis_data
        return
    results["errors"].append(f"{agent_type} agent returned invalid data")


def _get_comprehensive_summary(results: dict) -> str:
    for agent_type in ["financials", "statistics", "history", "news"]:
        if results.get(agent_type) and results[agent_type].get("summary"):
            return results[agent_type]["summary"]
    return "Analysis completed"


def _merge_key_insights(results: dict) -> List[str]:
    key_insights = []
    for agent_type in ["financials", "statistics", "history", "news"]:
        if results.get(agent_type) and results[agent_type].get("key_insights"):
            key_insights.extend(results[agent_type]["key_insights"])
    return key_insights


def _merge_technical_analysis(results: dict) -> dict:
    technical_analysis = {}
    if results.get("statistics"):
        stats_technical = results["statistics"].get("technical_analysis")
        if stats_technical and isinstance(stats_technical, dict):
            technical_analysis.update(stats_technical)
    if results.get("history"):
        history_technical = results["history"].get("technical_analysis")
        if history_technical and isinstance(history_technical, dict):
            technical_analysis.update(history_technical)
    return technical_analysis


def _merge_fundamental_analysis(results: dict) -> dict:
    if not results.get("financials"):
        return {}
    financials_fundamental = results["financials"].get("fundamental_analysis")
    if financials_fundamental and isinstance(financials_fundamental, dict):
        return financials_fundamental
    return {}


def _merge_risk_assessment(results: dict) -> dict:
    risk_assessment = {}
    for agent_type in ["financials", "statistics", "news"]:
        if results.get(agent_type) and results[agent_type].get("risk_assessment"):
            risk_assessment.update(results[agent_type]["risk_assessment"])
    return risk_assessment


def _get_recommendations(results: dict) -> tuple:
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
    if not (
        results.get("financials")
        or results.get("statistics")
        or results.get("history")
        or results.get("news")
    ):
        return None

    recommendations, confidence = _get_recommendations(results)
    return {
        "summary": _get_comprehensive_summary(results),
        "key_insights": _merge_key_insights(results),
        "technical_analysis": _merge_technical_analysis(results),
        "fundamental_analysis": _merge_fundamental_analysis(results),
        "risk_assessment": _merge_risk_assessment(results),
        "recommendations": recommendations,
        "confidence_score": confidence,
    }


@router.post("/analyze/all", response_model=dict)
async def analyze_stock_all_agents(  # noqa: C901
    request: StockAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
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
                agent = StockFinancialsAgent(db, context)
                result = await agent.analyze_financials(
                    request.symbol, model=request.model
                )
                return ("financials", result.get("analysis"))
            except Exception:
                return ("financials", None)

        async def run_statistics():
            try:
                agent = StockStatisticsAgent(db, context)
                result = await agent.analyze_statistics(
                    request.symbol, model=request.model
                )
                return ("statistics", result.get("analysis"))
            except Exception:
                return ("statistics", None)

        async def run_history():
            try:
                agent = StockHistoryAgent(db, context)
                result = await agent.analyze_history(
                    request.symbol, model=request.model
                )
                return ("history", result.get("analysis"))
            except Exception:
                return ("history", None)

        async def run_news():
            try:
                news_data = await stock_service.get_stock_news(
                    request.symbol, limit=50, months_back=6
                )
                agent = StockNewsAgent(db, context)
                result = await agent.analyze_news(
                    request.symbol, news_data or [], model=request.model
                )
                return ("news", result.get("analysis"))
            except Exception:
                return ("news", None)

        agent_results = await asyncio.gather(
            run_financials(),
            run_statistics(),
            run_history(),
            run_news(),
            return_exceptions=True,
        )
        for result in agent_results:
            _process_agent_result(result, results)

        results["analysis"] = _build_comprehensive_analysis(results)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in analyze_all for {request.symbol}: {e}",
            exc_info=True,
        )
        results["success"] = False
        results["errors"].append(str(e))
        return results
