"""
Stock Model - For Stock Analysis Application
"""

import uuid
from typing import Any, Dict, Optional
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Stock(Base):
    """
    Stock model for storing stock information and search results.
    """

    __tablename__ = "stocks"
    __table_args__ = {"schema": "migration"}

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Stock identification
    symbol = Column(String(20), nullable=False, index=True)  # e.g., "AAPL", "MSFT"
    company_name = Column(String(255), nullable=False)
    exchange = Column(String(50), nullable=True)  # e.g., "NASDAQ", "NYSE"
    sector = Column(String(100), nullable=True)
    industry = Column(String(200), nullable=True)

    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False)

    # Current stock data (snapshot)
    current_price = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    price_change = Column(Float, nullable=True)
    price_change_percent = Column(Float, nullable=True)

    # Additional metadata
    stock_metadata = Column(JSONB, nullable=False, default={})  # Store additional stock data (renamed from metadata to avoid SQLAlchemy conflict)
    search_keywords = Column(Text, nullable=True)  # Keywords used to find this stock

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    analyses = relationship("StockAnalysis", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock(symbol={self.symbol}, name='{self.company_name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "symbol": self.symbol,
            "company_name": self.company_name,
            "exchange": self.exchange,
            "sector": self.sector,
            "industry": self.industry,
            "current_price": self.current_price,
            "previous_close": self.previous_close,
            "currency": self.stock_metadata.get("currency") if self.stock_metadata else None,
            "market_cap": self.market_cap,
            "volume": self.volume,
            "price_change": self.price_change,
            "price_change_percent": self.price_change_percent,
            "metadata": self.stock_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StockAnalysis(Base):
    """
    Stock Analysis model for storing LLM-generated stock analysis.
    """

    __tablename__ = "stock_analyses"
    __table_args__ = {"schema": "migration"}

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to stock
    stock_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False)

    # Analysis content from LLM agent
    analysis_type = Column(String(50), nullable=False, default="comprehensive")  # comprehensive, technical, fundamental
    summary = Column(Text, nullable=False)  # Executive summary
    key_insights = Column(JSONB, nullable=False, default=[])  # List of key insights
    technical_analysis = Column(JSONB, nullable=True)  # Technical indicators, charts, etc.
    fundamental_analysis = Column(JSONB, nullable=True)  # Financial metrics, ratios, etc.
    risk_assessment = Column(JSONB, nullable=True)  # Risk factors and assessment
    recommendations = Column(JSONB, nullable=True)  # Buy/sell/hold recommendations
    price_targets = Column(JSONB, nullable=True)  # Price targets and forecasts

    # LLM metadata
    llm_model = Column(String(100), nullable=True)  # Model used for analysis
    llm_prompt = Column(Text, nullable=True)  # Prompt used
    llm_response = Column(JSONB, nullable=True)  # Full LLM response
    confidence_score = Column(Float, nullable=True)  # Confidence in analysis

    # Analysis metadata
    analysis_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_latest = Column(String(10), nullable=False, default="true")  # "true" or "false" as string for JSONB compatibility

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    stock = relationship("Stock", back_populates="analyses")

    def __repr__(self):
        return f"<StockAnalysis(stock_id={self.stock_id}, type='{self.analysis_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "stock_id": str(self.stock_id),
            "analysis_type": self.analysis_type,
            "summary": self.summary,
            "key_insights": self.key_insights or [],
            "technical_analysis": self.technical_analysis or {},
            "fundamental_analysis": self.fundamental_analysis or {},
            "risk_assessment": self.risk_assessment or {},
            "recommendations": self.recommendations or {},
            "price_targets": self.price_targets or {},
            "llm_model": self.llm_model,
            "confidence_score": self.confidence_score,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
            "is_latest": self.is_latest == "true",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

