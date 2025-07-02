"""LLM Usage Tracking Models

Models for tracking LLM API usage, costs, and performance metrics.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, BigInteger, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
from datetime import datetime
from typing import Optional, Dict, Any


class LLMUsageLog(Base):
    """Log individual LLM API calls for tracking usage and costs."""
    
    __tablename__ = "llm_usage_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Context and identification
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    user_id = Column(Integer, nullable=True)  # Reference to user system when implemented
    username = Column(String(255), nullable=True)
    flow_id = Column(String(255), nullable=True)
    
    # Request context
    request_id = Column(String(255), nullable=True)
    endpoint = Column(String(500), nullable=True)
    page_context = Column(String(255), nullable=True)
    feature_context = Column(String(255), nullable=True)  # e.g., 'asset-analysis', 'field-mapping'
    
    # LLM call details
    llm_provider = Column(String(100), nullable=False)  # 'openai', 'deepinfra', 'anthropic'
    model_name = Column(String(255), nullable=False)    # 'gpt-4', 'llama-2-70b', 'claude-3'
    model_version = Column(String(100), nullable=True)   # Model version if available
    
    # Token usage
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Cost calculation
    input_cost = Column(Numeric(10, 6), nullable=True)   # Cost for input tokens
    output_cost = Column(Numeric(10, 6), nullable=True)  # Cost for output tokens
    total_cost = Column(Numeric(10, 6), nullable=True)   # Total cost in USD
    cost_currency = Column(String(10), default='USD', nullable=False)
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)    # Response time in milliseconds
    success = Column(Boolean, default=True, nullable=False)
    error_type = Column(String(255), nullable=True)     # Error type if failed
    error_message = Column(Text, nullable=True)         # Error details
    
    # Request/response data (for debugging and analysis)
    request_data = Column(JSONB, nullable=True)         # Truncated/sanitized request
    response_data = Column(JSONB, nullable=True)        # Truncated/sanitized response
    additional_metadata = Column(JSONB, nullable=True)  # Additional metadata
    
    # Audit fields
    ip_address = Column(String(45), nullable=True)      # IPv6 support
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="llm_usage_logs")
    engagement = relationship("Engagement", back_populates="llm_usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_llm_usage_client_account', 'client_account_id'),
        Index('idx_llm_usage_engagement', 'engagement_id'),
        Index('idx_llm_usage_user', 'user_id'),
        Index('idx_llm_usage_created_at', 'created_at'),
        Index('idx_llm_usage_provider_model', 'llm_provider', 'model_name'),
        Index('idx_llm_usage_success', 'success'),
        Index('idx_llm_usage_page_context', 'page_context'),
        Index('idx_llm_usage_feature_context', 'feature_context'),
        Index('idx_llm_usage_reporting', 'client_account_id', 'created_at', 'success'),
        Index('idx_llm_usage_cost_analysis', 'client_account_id', 'llm_provider', 'model_name', 'created_at'),
    )
    
    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, provider={self.llm_provider}, model={self.model_name}, cost={self.total_cost})>"


class LLMModelPricing(Base):
    """Store pricing information for different LLM models."""
    
    __tablename__ = "llm_model_pricing"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Model identification
    provider = Column(String(100), nullable=False)
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(100), nullable=True)
    
    # Pricing (per 1K tokens)
    input_cost_per_1k_tokens = Column(Numeric(10, 6), nullable=False)
    output_cost_per_1k_tokens = Column(Numeric(10, 6), nullable=False)
    currency = Column(String(10), default='USD', nullable=False)
    
    # Validity period
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    source = Column(String(255), nullable=True)         # Where pricing info came from
    notes = Column(Text, nullable=True)                 # Additional notes
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('provider', 'model_name', 'model_version', 'effective_from', 
                        name='uq_model_pricing_version_date'),
        Index('idx_model_pricing_provider_model', 'provider', 'model_name'),
        Index('idx_model_pricing_active', 'is_active', 'effective_from', 'effective_to'),
    )
    
    def __repr__(self):
        return f"<LLMModelPricing(provider={self.provider}, model={self.model_name}, input_cost={self.input_cost_per_1k_tokens})>"


class LLMUsageSummary(Base):
    """Aggregated LLM usage statistics for quick reporting."""
    
    __tablename__ = "llm_usage_summary"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Aggregation period
    period_type = Column(String(20), nullable=False)    # 'daily', 'weekly', 'monthly'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Context
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    user_id = Column(Integer, nullable=True)
    llm_provider = Column(String(100), nullable=True)
    model_name = Column(String(255), nullable=True)
    page_context = Column(String(255), nullable=True)
    feature_context = Column(String(255), nullable=True)
    
    # Aggregated metrics
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    total_input_tokens = Column(BigInteger, default=0, nullable=False)
    total_output_tokens = Column(BigInteger, default=0, nullable=False)
    total_tokens = Column(BigInteger, default=0, nullable=False)
    total_cost = Column(Numeric(12, 6), default=0, nullable=False)
    avg_response_time_ms = Column(Integer, nullable=True)
    min_response_time_ms = Column(Integer, nullable=True)
    max_response_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="llm_usage_summaries")
    engagement = relationship("Engagement", back_populates="llm_usage_summaries")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_usage_summary_period', 'period_type', 'period_start', 'period_end'),
        Index('idx_usage_summary_client', 'client_account_id', 'period_start'),
        Index('idx_usage_summary_model', 'llm_provider', 'model_name', 'period_start'),
        UniqueConstraint('period_type', 'period_start', 'client_account_id', 'engagement_id', 
                        'user_id', 'llm_provider', 'model_name', 'page_context', 'feature_context',
                        name='uq_usage_summary_period_context'),
    )
    
    def __repr__(self):
        return f"<LLMUsageSummary(period={self.period_type}, requests={self.total_requests}, cost={self.total_cost})>" 