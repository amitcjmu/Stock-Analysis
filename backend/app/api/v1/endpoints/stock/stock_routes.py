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
    model: Optional[str] = Query(None, description="LLM model to use for news generation (gemini, llama4_maverick, gemma3_4b, auto)"),
    include_llm_news: bool = Query(True, description="Include LLM-generated news insights"),
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
        logger.info(f"Retrieved {len(yfinance_news)} news articles from Yahoo Finance for {symbol}")
        
        # Get LLM-generated news insights if requested
        llm_news_insights = []
        if include_llm_news:
            try:
                from app.services.multi_model_service import multi_model_service, ModelType, TaskComplexity
                
                # Get stock data for context
                stock_data = await stock_service.get_stock_by_symbol(symbol)
                if stock_data:
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
                    
                    # Generate LLM news insights
                    llm_prompt = f"""
You are a financial news analyst. Based on the current stock information for {stock_data.get('company_name', symbol)} ({symbol}), 
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
                    
                    logger.info(f"Generating LLM news insights for {symbol} using model: {model or 'auto'}")
                    llm_response = await multi_model_service.generate_response(
                        prompt=llm_prompt,
                        task_type="analysis",
                        complexity=TaskComplexity.MEDIUM,
                        model_type=model_type,
                    )
                    
                    if llm_response.get("status") != "error":
                        response_text = llm_response.get("response") or llm_response.get("content", "")
                        logger.info(f"LLM news response length: {len(response_text) if response_text else 0} characters")
                        logger.debug(f"LLM news response preview: {response_text[:500] if response_text else 'Empty'}")
                        
                        if response_text and response_text.strip():
                            # Extract JSON from response
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
                            json_match = re.search(r'\[.*\]', response_clean, re.DOTALL)
                            if json_match:
                                response_clean = json_match.group(0)
                            
                            logger.debug(f"Cleaned response for parsing: {response_clean[:200]}...")
                            
                            try:
                                llm_news_data = json.loads(response_clean)
                                if isinstance(llm_news_data, list) and len(llm_news_data) > 0:
                                    # Format LLM news to match Yahoo Finance format
                                    for insight in llm_news_data[:5]:  # Limit to 5 insights
                                        if isinstance(insight, dict) and insight.get("title"):
                                            llm_news_insights.append({
                                                "title": insight.get("title", "AI News Insight"),
                                                "publisher": insight.get("source", "AI Analysis"),
                                                "link": "",
                                                "published_date": int(datetime.now().timestamp()),
                                                "uuid": f"llm-{symbol}-{len(llm_news_insights)}",
                                                "summary": insight.get("summary", ""),
                                                "category": insight.get("category", "market_update"),
                                                "impact": insight.get("impact", "neutral"),
                                                "is_llm_generated": True,
                                            })
                                    logger.info(f"Generated {len(llm_news_insights)} LLM news insights for {symbol}")
                                elif isinstance(llm_news_data, dict):
                                    # Handle case where LLM returns a single object instead of array
                                    logger.warning("LLM returned a single object instead of array, converting to array")
                                    if llm_news_data.get("title"):
                                        llm_news_insights.append({
                                            "title": llm_news_data.get("title", "AI News Insight"),
                                            "publisher": llm_news_data.get("source", "AI Analysis"),
                                            "link": "",
                                            "published_date": int(datetime.now().timestamp()),
                                            "uuid": f"llm-{symbol}-0",
                                            "summary": llm_news_data.get("summary", ""),
                                            "category": llm_news_data.get("category", "market_update"),
                                            "impact": llm_news_data.get("impact", "neutral"),
                                            "is_llm_generated": True,
                                        })
                                        logger.info(f"Generated 1 LLM news insight from single object for {symbol}")
                                else:
                                    logger.warning(f"LLM returned non-list news data: {type(llm_news_data)}, value: {str(llm_news_data)[:200]}")
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse LLM news response as JSON: {e}")
                                logger.warning(f"Response text that failed to parse: {response_clean[:500]}")
                                # Try to create a fallback insight from the raw response
                                if response_text and len(response_text) > 20:
                                    llm_news_insights.append({
                                        "title": f"Market Analysis for {symbol}",
                                        "publisher": "AI Analysis",
                                        "link": "",
                                        "published_date": int(datetime.now().timestamp()),
                                        "uuid": f"llm-{symbol}-fallback",
                                        "summary": response_text[:300] + "..." if len(response_text) > 300 else response_text,
                                        "category": "market_update",
                                        "impact": "neutral",
                                        "is_llm_generated": True,
                                    })
                                    logger.info(f"Created fallback LLM news insight from raw response for {symbol}")
                        else:
                            logger.warning(f"LLM returned empty response for news generation")
                    else:
                        error_msg = llm_response.get('error', 'Unknown error')
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
                    logger.info(
                        f"🚀 [ANALYZE ALL] Financials Agent returned analysis with keys: {list(analysis.keys()) if isinstance(analysis, dict) else 'N/A'}"
                    )
                    return ("financials", analysis)
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] Financials Agent result missing 'analysis' key or is None"
                    )
                    logger.error(
                        f"🚀 [ANALYZE ALL] Financials Agent result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
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
                    logger.info(
                        f"🚀 [ANALYZE ALL] Statistics Agent returned analysis with keys: {list(analysis.keys()) if isinstance(analysis, dict) else 'N/A'}"
                    )
                    return ("statistics", analysis)
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] Statistics Agent result missing 'analysis' key or is None"
                    )
                    logger.error(
                        f"🚀 [ANALYZE ALL] Statistics Agent result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
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
                    logger.info(
                        f"🚀 [ANALYZE ALL] History Agent returned analysis with keys: {list(analysis.keys()) if isinstance(analysis, dict) else 'N/A'}"
                    )
                    return ("history", analysis)
                else:
                    logger.error(
                        "🚀 [ANALYZE ALL] History Agent result missing 'analysis' key or is None"
                    )
                    logger.error(
                        f"🚀 [ANALYZE ALL] History Agent result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
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

        # Create a comprehensive analysis by merging all agent results
        # This is used for the "Overview" tab in the frontend
        comprehensive_analysis = None
        if results["financials"] or results["statistics"] or results["history"] or results["news"]:
            comprehensive_analysis = {
                "summary": (
                    results["financials"].get("summary", "")
                    if results["financials"]
                    else results["statistics"].get("summary", "")
                    if results["statistics"]
                    else results["history"].get("summary", "")
                    if results["history"]
                    else results["news"].get("summary", "")
                    if results["news"]
                    else "Analysis completed"
                ),
                "key_insights": [],
                "technical_analysis": {},
                "fundamental_analysis": {},
                "risk_assessment": {},
                "recommendations": {},
                "confidence_score": 0.5,
            }

            # Merge key insights from all agents
            if results["financials"] and results["financials"].get("key_insights"):
                comprehensive_analysis["key_insights"].extend(
                    results["financials"]["key_insights"]
                )
            if results["statistics"] and results["statistics"].get("key_insights"):
                comprehensive_analysis["key_insights"].extend(
                    results["statistics"]["key_insights"]
                )
            if results["history"] and results["history"].get("key_insights"):
                comprehensive_analysis["key_insights"].extend(
                    results["history"]["key_insights"]
                )
            if results["news"] and results["news"].get("key_insights"):
                comprehensive_analysis["key_insights"].extend(
                    results["news"]["key_insights"]
                )

            # Merge technical analysis (from statistics and history)
            if results["statistics"]:
                stats_technical = results["statistics"].get("technical_analysis")
                logger.info(
                    f"🚀 [ANALYZE ALL] Statistics technical_analysis: "
                    f"exists={stats_technical is not None}, "
                    f"type={type(stats_technical)}, "
                    f"len={len(stats_technical) if isinstance(stats_technical, dict) else 'N/A'}, "
                    f"keys={list(stats_technical.keys()) if isinstance(stats_technical, dict) else 'N/A'}"
                )
                if (
                    stats_technical
                    and isinstance(stats_technical, dict)
                    and len(stats_technical) > 0
                ):
                    comprehensive_analysis["technical_analysis"].update(stats_technical)
                    logger.info(
                        f"🚀 [ANALYZE ALL] ✅ Merged statistics technical_analysis"
                    )
                elif results["statistics"].get("summary"):
                    # Fallback: create technical analysis from statistics summary
                    comprehensive_analysis["technical_analysis"]["statistics_summary"] = results["statistics"].get("summary", "")
                    if results["statistics"].get("key_insights"):
                        comprehensive_analysis["technical_analysis"]["statistical_insights"] = results["statistics"].get("key_insights", [])
                    logger.info(
                        f"🚀 [ANALYZE ALL] ✅ Created technical_analysis from statistics summary (fallback)"
                    )

            if results["history"]:
                history_technical = results["history"].get("technical_analysis")
                logger.info(
                    f"🚀 [ANALYZE ALL] History technical_analysis: "
                    f"exists={history_technical is not None}, "
                    f"type={type(history_technical)}, "
                    f"len={len(history_technical) if isinstance(history_technical, dict) else 'N/A'}, "
                    f"keys={list(history_technical.keys()) if isinstance(history_technical, dict) else 'N/A'}"
                )
                if (
                    history_technical
                    and isinstance(history_technical, dict)
                    and len(history_technical) > 0
                ):
                    comprehensive_analysis["technical_analysis"].update(history_technical)
                    logger.info(
                        f"🚀 [ANALYZE ALL] ✅ Merged history technical_analysis"
                    )
                elif results["history"].get("summary"):
                    # Fallback: create technical analysis from history summary
                    if "history_summary" not in comprehensive_analysis["technical_analysis"]:
                        comprehensive_analysis["technical_analysis"]["history_summary"] = results["history"].get("summary", "")
                    if results["history"].get("key_insights"):
                        if "technical_patterns" not in comprehensive_analysis["technical_analysis"]:
                            comprehensive_analysis["technical_analysis"]["technical_patterns"] = results["history"].get("key_insights", [])
                    logger.info(
                        f"🚀 [ANALYZE ALL] ✅ Created technical_analysis from history summary (fallback)"
                    )

            # Merge fundamental analysis (from financials)
            if results["financials"]:
                financials_fundamental = results["financials"].get("fundamental_analysis")
                logger.info(
                    f"🚀 [ANALYZE ALL] Financials fundamental_analysis: "
                    f"exists={financials_fundamental is not None}, "
                    f"type={type(financials_fundamental)}, "
                    f"len={len(financials_fundamental) if isinstance(financials_fundamental, dict) else 'N/A'}, "
                    f"keys={list(financials_fundamental.keys()) if isinstance(financials_fundamental, dict) else 'N/A'}"
                )
                if (
                    financials_fundamental
                    and isinstance(financials_fundamental, dict)
                    and len(financials_fundamental) > 0
                ):
                    # Check if it has the expected structure (valuation_analysis, financial_health, etc.)
                    has_structure = any(
                        key in financials_fundamental
                        for key in ["valuation_analysis", "financial_health", "key_financial_ratios", "growth_analysis"]
                    )
                    if has_structure:
                        comprehensive_analysis["fundamental_analysis"].update(
                            financials_fundamental
                        )
                        logger.info(
                            f"🚀 [ANALYZE ALL] ✅ Merged financials fundamental_analysis with proper structure"
                        )
                    else:
                        # Has data but wrong structure - try to restructure it
                        logger.warning(
                            f"🚀 [ANALYZE ALL] ⚠️ Financials fundamental_analysis exists but lacks expected structure. Keys: {list(financials_fundamental.keys())}"
                        )
                        # Still merge it, but log a warning
                        comprehensive_analysis["fundamental_analysis"].update(
                            financials_fundamental
                        )
                else:
                    # No fundamental_analysis from financials agent - this shouldn't happen if agent is working correctly
                    logger.warning(
                        f"🚀 [ANALYZE ALL] ⚠️ Financials agent did not return fundamental_analysis. "
                        f"Summary available: {bool(results['financials'].get('summary'))}"
                    )
                    # Don't create fallback fields - let the frontend handle empty state

            # Merge risk assessment (from all agents)
            if results["financials"] and results["financials"].get("risk_assessment"):
                comprehensive_analysis["risk_assessment"].update(
                    results["financials"]["risk_assessment"]
                )
            if results["statistics"] and results["statistics"].get("risk_assessment"):
                comprehensive_analysis["risk_assessment"].update(
                    results["statistics"]["risk_assessment"]
                )
            if results["news"] and results["news"].get("risk_assessment"):
                comprehensive_analysis["risk_assessment"].update(
                    results["news"]["risk_assessment"]
                )

            # Use recommendations from financials (most comprehensive) or first available
            if results["financials"] and results["financials"].get("recommendations"):
                comprehensive_analysis["recommendations"] = results["financials"][
                    "recommendations"
                ]
                comprehensive_analysis["confidence_score"] = results["financials"][
                    "recommendations"
                ].get("confidence", 0.5)
            elif results["statistics"] and results["statistics"].get("recommendations"):
                comprehensive_analysis["recommendations"] = results["statistics"][
                    "recommendations"
                ]
                comprehensive_analysis["confidence_score"] = results["statistics"][
                    "recommendations"
                ].get("confidence", 0.5)
            elif results["history"] and results["history"].get("recommendations"):
                comprehensive_analysis["recommendations"] = results["history"][
                    "recommendations"
                ]
                comprehensive_analysis["confidence_score"] = results["history"][
                    "recommendations"
                ].get("confidence", 0.5)
            elif results["news"] and results["news"].get("recommendations"):
                comprehensive_analysis["recommendations"] = results["news"][
                    "recommendations"
                ]
                comprehensive_analysis["confidence_score"] = results["news"][
                    "recommendations"
                ].get("confidence", 0.5)

            # Check if sections have actual content (not just empty dicts)
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
                f"technical={has_technical}, "
                f"fundamental={has_fundamental}, "
                f"risks={has_risks}, "
                f"recommendations={has_recommendations}"
            )
            
            # Log what's actually in technical_analysis and fundamental_analysis for debugging
            if comprehensive_analysis.get("technical_analysis"):
                logger.info(
                    f"🚀 [ANALYZE ALL] Technical analysis keys: {list(comprehensive_analysis['technical_analysis'].keys())}"
                )
            if comprehensive_analysis.get("fundamental_analysis"):
                logger.info(
                    f"🚀 [ANALYZE ALL] Fundamental analysis keys: {list(comprehensive_analysis['fundamental_analysis'].keys())}"
                )

        # Add comprehensive analysis to results
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
