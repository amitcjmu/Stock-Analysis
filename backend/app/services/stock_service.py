"""
Stock Service - Handles stock search and data fetching
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.stock import Stock, StockAnalysis
from app.services.stock_data_api import StockDataAPIService

logger = logging.getLogger(__name__)


class StockService:
    """Service for stock search and management"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.stock_data_api = StockDataAPIService()

    async def search_stocks(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for stocks by symbol or company name.
        Uses Yahoo Finance API for real stock data.
        """
        try:
            # Search in database first
            search_pattern = f"%{query.upper()}%"
            stmt = (
                select(Stock)
                .where(
                    and_(
                        or_(
                            Stock.symbol.ilike(search_pattern),
                            Stock.company_name.ilike(search_pattern),
                        ),
                        Stock.client_account_id == self.context.client_account_id,
                        Stock.engagement_id == self.context.engagement_id,
                    )
                )
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            existing_stocks = result.scalars().all()

            # Convert to dict
            stocks = [stock.to_dict() for stock in existing_stocks]

            # If no results in DB, fetch from Yahoo Finance API
            if not stocks:
                stocks = await self.stock_data_api.search_stocks(query, limit)

            return stocks

        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            # Fallback to API on error
            return await self.stock_data_api.search_stocks(query, limit)

    async def get_historical_prices(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical price data for a stock"""
        try:
            return await self.stock_data_api.get_historical_prices(symbol, period, interval)
        except Exception as e:
            logger.error(f"Error getting historical prices: {e}")
            return None

    async def get_stock_by_symbol(
        self, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Get stock by symbol"""
        try:
            stmt = (
                select(Stock)
                .where(
                    and_(
                        Stock.symbol == symbol.upper(),
                        Stock.client_account_id == self.context.client_account_id,
                        Stock.engagement_id == self.context.engagement_id,
                    )
                )
            )
            result = await self.db.execute(stmt)
            stock = result.scalar_one_or_none()

            if stock:
                return stock.to_dict()

            # If not in DB, fetch from Yahoo Finance API
            stock_data = await self.stock_data_api.get_stock_data(symbol)
            return stock_data

        except Exception as e:
            logger.error(f"Error getting stock by symbol: {e}")
            return None

    async def save_stock(self, stock_data: Dict[str, Any]) -> Stock:
        """Save or update stock in database"""
        try:
            # Check if stock already exists
            stmt = (
                select(Stock)
                .where(
                    and_(
                        Stock.symbol == stock_data["symbol"].upper(),
                        Stock.client_account_id == self.context.client_account_id,
                        Stock.engagement_id == self.context.engagement_id,
                    )
                )
            )
            result = await self.db.execute(stmt)
            existing_stock = result.scalar_one_or_none()

            if existing_stock:
                # Update existing stock
                # Exclude fields that are auto-managed by SQLAlchemy or shouldn't be updated
                excluded_fields = ["id", "created_at", "updated_at", "client_account_id", "engagement_id", "user_id"]
                for key, value in stock_data.items():
                    if hasattr(existing_stock, key) and key not in excluded_fields:
                        setattr(existing_stock, key, value)
                # Manually set updated_at to current time (onupdate=func.now() doesn't work well with asyncpg)
                existing_stock.updated_at = datetime.now(timezone.utc)
                await self.db.flush()
                return existing_stock
            else:
                # Create new stock
                # Include currency in metadata if provided
                metadata = stock_data.get("metadata", {})
                if stock_data.get("currency"):
                    metadata["currency"] = stock_data.get("currency")
                
                new_stock = Stock(
                    symbol=stock_data["symbol"].upper(),
                    company_name=stock_data.get("company_name", ""),
                    exchange=stock_data.get("exchange"),
                    sector=stock_data.get("sector"),
                    industry=stock_data.get("industry"),
                    current_price=stock_data.get("current_price"),
                    previous_close=stock_data.get("previous_close"),
                    market_cap=stock_data.get("market_cap"),
                    volume=stock_data.get("volume"),
                    price_change=stock_data.get("price_change"),
                    price_change_percent=stock_data.get("price_change_percent"),
                    stock_metadata=metadata,
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    user_id=self.context.user_id or "system",
                )
                self.db.add(new_stock)
                await self.db.flush()
                return new_stock

        except Exception as e:
            logger.error(f"Error saving stock: {e}")
            await self.db.rollback()
            raise

    async def get_stock_analysis(
        self, stock_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get latest stock analysis for a stock"""
        try:
            stmt = (
                select(StockAnalysis)
                .where(
                    and_(
                        StockAnalysis.stock_id == stock_id,
                        StockAnalysis.client_account_id == self.context.client_account_id,
                        StockAnalysis.engagement_id == self.context.engagement_id,
                        StockAnalysis.is_latest == "true",
                    )
                )
                .order_by(StockAnalysis.created_at.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            analysis = result.scalar_one_or_none()

            if analysis:
                return analysis.to_dict()

            return None

        except Exception as e:
            logger.error(f"Error getting stock analysis: {e}")
            return None

    async def save_stock_analysis(
        self, stock_id: UUID, analysis_data: Dict[str, Any]
    ) -> StockAnalysis:
        """Save stock analysis from LLM agent"""
        try:
            # Mark previous analyses as not latest
            stmt = (
                select(StockAnalysis)
                .where(
                    and_(
                        StockAnalysis.stock_id == stock_id,
                        StockAnalysis.client_account_id == self.context.client_account_id,
                        StockAnalysis.engagement_id == self.context.engagement_id,
                        StockAnalysis.is_latest == "true",
                    )
                )
            )
            result = await self.db.execute(stmt)
            previous_analyses = result.scalars().all()
            for prev_analysis in previous_analyses:
                prev_analysis.is_latest = "false"

            # Create new analysis
            new_analysis = StockAnalysis(
                stock_id=stock_id,
                analysis_type=analysis_data.get("analysis_type", "comprehensive"),
                summary=analysis_data.get("summary", ""),
                key_insights=analysis_data.get("key_insights", []),
                technical_analysis=analysis_data.get("technical_analysis"),
                fundamental_analysis=analysis_data.get("fundamental_analysis"),
                risk_assessment=analysis_data.get("risk_assessment"),
                recommendations=analysis_data.get("recommendations"),
                price_targets=analysis_data.get("price_targets"),
                llm_model=analysis_data.get("llm_model"),
                llm_prompt=analysis_data.get("llm_prompt"),
                llm_response=analysis_data.get("llm_response"),
                confidence_score=analysis_data.get("confidence_score"),
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                user_id=self.context.user_id or "system",
                is_latest="true",
            )
            self.db.add(new_analysis)
            await self.db.flush()
            return new_analysis

        except Exception as e:
            logger.error(f"Error saving stock analysis: {e}")
            await self.db.rollback()
            raise

