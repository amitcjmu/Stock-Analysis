"""Add agentic memory architecture support

Revision ID: 20250712_agentic_memory_architecture
Revises: remove_session_id_final_cleanup
Create Date: 2025-07-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'agentic_memory_20250712'
down_revision = '4a69564e2679'
branch_labels = None
depends_on = None


def upgrade():
    """Add agent-enriched fields to assets table and create agent memory table"""
    
    # Add agent-enriched fields to assets table
    print("🔧 Adding agent-enriched fields to assets table...")
    
    # Business value and enrichment fields (populated by agents, not rules)
    op.add_column('assets', sa.Column('business_value_score', sa.Integer(), nullable=True))
    op.add_column('assets', sa.Column('enrichment_status', sa.String(20), nullable=True, default='basic'))
    op.add_column('assets', sa.Column('risk_assessment', sa.String(20), nullable=True))
    op.add_column('assets', sa.Column('modernization_potential', sa.String(20), nullable=True))
    op.add_column('assets', sa.Column('cloud_readiness_score', sa.Integer(), nullable=True))
    
    # Agent reasoning metadata  
    op.add_column('assets', sa.Column('enrichment_reasoning', sa.Text(), nullable=True))
    op.add_column('assets', sa.Column('last_enriched_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('assets', sa.Column('last_enriched_by_agent', sa.String(100), nullable=True))
    
    # Add constraints for score fields
    op.create_check_constraint(
        'check_business_value_score_range',
        'assets',
        'business_value_score >= 1 AND business_value_score <= 10'
    )
    
    op.create_check_constraint(
        'check_cloud_readiness_score_range', 
        'assets',
        'cloud_readiness_score >= 0 AND cloud_readiness_score <= 100'
    )
    
    # Create agent_discovered_patterns table (Tier 3 Memory)
    print("🧠 Creating agent_discovered_patterns table for Tier 3 memory...")
    
    op.create_table('agent_discovered_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Pattern identification
        sa.Column('pattern_type', sa.String(50), nullable=False),
        sa.Column('pattern_name', sa.String(200), nullable=False),
        sa.Column('pattern_description', sa.Text(), nullable=True),
        
        # Pattern content and confidence
        sa.Column('pattern_data', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('evidence_count', sa.Integer(), nullable=False, default=1),
        
        # Agent and discovery metadata
        sa.Column('discovered_by_agent', sa.String(100), nullable=False),
        sa.Column('discovery_context', sa.JSON(), nullable=True),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Usage and validation tracking
        sa.Column('times_referenced', sa.Integer(), nullable=False, default=0),
        sa.Column('last_referenced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_status', sa.String(20), nullable=False, default='pending'),
        sa.Column('validated_by_user', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['validated_by_user'], ['users.id'], ),
    )
    
    # Create indexes for performance
    op.create_index('ix_agent_patterns_client_account', 'agent_discovered_patterns', ['client_account_id'])
    op.create_index('ix_agent_patterns_engagement', 'agent_discovered_patterns', ['engagement_id'])
    op.create_index('ix_agent_patterns_type', 'agent_discovered_patterns', ['pattern_type'])
    op.create_index('ix_agent_patterns_confidence', 'agent_discovered_patterns', ['confidence_score'])
    op.create_index('ix_agent_patterns_discovery', 'agent_discovered_patterns', ['discovered_by_agent', 'created_at'])
    
    # Add constraint for confidence score
    op.create_check_constraint(
        'check_confidence_score_range',
        'agent_discovered_patterns', 
        'confidence_score >= 0.0 AND confidence_score <= 1.0'
    )
    
    print("✅ Agentic memory architecture tables created successfully")


def downgrade():
    """Remove agent-enriched fields and memory table"""
    
    print("🔄 Removing agentic memory architecture...")
    
    # Drop agent_discovered_patterns table
    op.drop_table('agent_discovered_patterns')
    
    # Remove agent-enriched columns from assets
    op.drop_column('assets', 'last_enriched_by_agent')
    op.drop_column('assets', 'last_enriched_at')
    op.drop_column('assets', 'enrichment_reasoning')
    op.drop_column('assets', 'cloud_readiness_score')
    op.drop_column('assets', 'modernization_potential')
    op.drop_column('assets', 'risk_assessment')
    op.drop_column('assets', 'enrichment_status')
    op.drop_column('assets', 'business_value_score')
    
    print("✅ Agentic memory architecture removed")