"""create llm usage tracking

Revision ID: 006_llm_usage_tracking
Revises: 005_session_comparison
Create Date: 2025-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

# revision identifiers, used by Alembic.
revision: str = '006_llm_usage_tracking'
down_revision: Union[str, None] = '005_session_comparison'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create LLM usage logs table
    op.create_table('llm_usage_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Context and identification
        sa.Column('client_account_id', sa.Integer, sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', sa.Integer, sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('user_id', sa.Integer, nullable=True),  # Reference to user system when implemented
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        
        # Request context
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('page_context', sa.String(255), nullable=True),
        sa.Column('feature_context', sa.String(255), nullable=True),  # e.g., 'asset-analysis', 'field-mapping'
        
        # LLM call details
        sa.Column('llm_provider', sa.String(100), nullable=False),  # 'openai', 'deepinfra', 'anthropic'
        sa.Column('model_name', sa.String(255), nullable=False),    # 'gpt-4', 'llama-2-70b', 'claude-3'
        sa.Column('model_version', sa.String(100), nullable=True),   # Model version if available
        
        # Token usage
        sa.Column('input_tokens', sa.Integer, nullable=True),
        sa.Column('output_tokens', sa.Integer, nullable=True),
        sa.Column('total_tokens', sa.Integer, nullable=True),
        
        # Cost calculation
        sa.Column('input_cost', sa.Numeric(10, 6), nullable=True),   # Cost for input tokens
        sa.Column('output_cost', sa.Numeric(10, 6), nullable=True),  # Cost for output tokens
        sa.Column('total_cost', sa.Numeric(10, 6), nullable=True),   # Total cost in USD
        sa.Column('cost_currency', sa.String(10), default='USD', nullable=False),
        
        # Performance metrics
        sa.Column('response_time_ms', sa.Integer, nullable=True),    # Response time in milliseconds
        sa.Column('success', sa.Boolean, default=True, nullable=False),
        sa.Column('error_type', sa.String(255), nullable=True),     # Error type if failed
        sa.Column('error_message', sa.Text, nullable=True),         # Error details
        
        # Request/response data (for debugging and analysis)
        sa.Column('request_data', JSONB, nullable=True),            # Truncated/sanitized request
        sa.Column('response_data', JSONB, nullable=True),           # Truncated/sanitized response
        sa.Column('metadata', JSONB, nullable=True),                # Additional metadata
        
        # Audit fields
        sa.Column('ip_address', sa.String(45), nullable=True),      # IPv6 support
        sa.Column('user_agent', sa.String(500), nullable=True),
        
        # Indexes for common queries
        sa.Index('idx_llm_usage_client_account', 'client_account_id'),
        sa.Index('idx_llm_usage_engagement', 'engagement_id'),
        sa.Index('idx_llm_usage_user', 'user_id'),
        sa.Index('idx_llm_usage_created_at', 'created_at'),
        sa.Index('idx_llm_usage_provider_model', 'llm_provider', 'model_name'),
        sa.Index('idx_llm_usage_success', 'success'),
        sa.Index('idx_llm_usage_page_context', 'page_context'),
        sa.Index('idx_llm_usage_feature_context', 'feature_context'),
        
        # Composite indexes for reporting
        sa.Index('idx_llm_usage_reporting', 'client_account_id', 'created_at', 'success'),
        sa.Index('idx_llm_usage_cost_analysis', 'client_account_id', 'llm_provider', 'model_name', 'created_at'),
    )
    
    # Create LLM model pricing table for cost calculations
    op.create_table('llm_model_pricing',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Model identification
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('model_version', sa.String(100), nullable=True),
        
        # Pricing (per 1K tokens)
        sa.Column('input_cost_per_1k_tokens', sa.Numeric(10, 6), nullable=False),
        sa.Column('output_cost_per_1k_tokens', sa.Numeric(10, 6), nullable=False),
        sa.Column('currency', sa.String(10), default='USD', nullable=False),
        
        # Validity period
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        
        # Metadata
        sa.Column('source', sa.String(255), nullable=True),         # Where pricing info came from
        sa.Column('notes', sa.Text, nullable=True),                 # Additional notes
        
        # Unique constraint for active pricing
        sa.UniqueConstraint('provider', 'model_name', 'model_version', 'effective_from', 
                           name='uq_model_pricing_version_date'),
                           
        # Indexes
        sa.Index('idx_model_pricing_provider_model', 'provider', 'model_name'),
        sa.Index('idx_model_pricing_active', 'is_active', 'effective_from', 'effective_to'),
    )
    
    # Create LLM usage summary table for quick reporting
    op.create_table('llm_usage_summary',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Aggregation period
        sa.Column('period_type', sa.String(20), nullable=False),    # 'daily', 'weekly', 'monthly'
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        
        # Context
        sa.Column('client_account_id', sa.Integer, sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', sa.Integer, sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('user_id', sa.Integer, nullable=True),
        sa.Column('llm_provider', sa.String(100), nullable=True),
        sa.Column('model_name', sa.String(255), nullable=True),
        sa.Column('page_context', sa.String(255), nullable=True),
        sa.Column('feature_context', sa.String(255), nullable=True),
        
        # Aggregated metrics
        sa.Column('total_requests', sa.Integer, default=0, nullable=False),
        sa.Column('successful_requests', sa.Integer, default=0, nullable=False),
        sa.Column('failed_requests', sa.Integer, default=0, nullable=False),
        sa.Column('total_input_tokens', sa.BigInteger, default=0, nullable=False),
        sa.Column('total_output_tokens', sa.BigInteger, default=0, nullable=False),
        sa.Column('total_tokens', sa.BigInteger, default=0, nullable=False),
        sa.Column('total_cost', sa.Numeric(12, 6), default=0, nullable=False),
        sa.Column('avg_response_time_ms', sa.Integer, nullable=True),
        sa.Column('min_response_time_ms', sa.Integer, nullable=True),
        sa.Column('max_response_time_ms', sa.Integer, nullable=True),
        
        # Indexes for reporting
        sa.Index('idx_usage_summary_period', 'period_type', 'period_start', 'period_end'),
        sa.Index('idx_usage_summary_client', 'client_account_id', 'period_start'),
        sa.Index('idx_usage_summary_model', 'llm_provider', 'model_name', 'period_start'),
        
        # Unique constraint for summary records
        sa.UniqueConstraint('period_type', 'period_start', 'client_account_id', 'engagement_id', 
                           'user_id', 'llm_provider', 'model_name', 'page_context', 'feature_context',
                           name='uq_usage_summary_period_context'),
    )


def downgrade() -> None:
    op.drop_table('llm_usage_summary')
    op.drop_table('llm_model_pricing') 
    op.drop_table('llm_usage_logs') 