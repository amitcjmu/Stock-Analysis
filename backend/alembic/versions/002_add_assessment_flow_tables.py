"""Add assessment flow tables

Revision ID: 002_add_assessment_flow_tables
Revises: 001_complete_schema
Create Date: 2025-07-02 00:00:00.000000

This migration creates all Assessment Flow tables with:
- PostgreSQL-only architecture (no SQLite compatibility)
- UUID primary keys following platform patterns
- Multi-tenant constraints on all tables
- JSONB fields for complex state data with GIN indexes
- Proper foreign key constraints with CASCADE cleanup
- Performance optimization for flow navigation and component queries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '002_add_assessment_flow_tables'
down_revision = '001_complete_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === ASSESSMENT FLOW CORE TABLES ===
    
    # 1. Main assessment_flows table - Flow tracking with pause points and navigation state
    op.create_table(
        'assessment_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('selected_application_ids', postgresql.JSONB(), nullable=False),
        sa.Column('architecture_captured', sa.Boolean(), default=False, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='initialized', index=True),
        sa.Column('progress', sa.Integer(), default=0, nullable=False),
        sa.Column('current_phase', sa.String(100), nullable=True, index=True),
        sa.Column('next_phase', sa.String(100), nullable=True, index=True),
        sa.Column('pause_points', postgresql.JSONB(), default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('user_inputs', postgresql.JSONB(), default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('phase_results', postgresql.JSONB(), default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('agent_insights', postgresql.JSONB(), default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('apps_ready_for_planning', postgresql.JSONB(), default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('last_user_interaction', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Constraints
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='valid_progress'),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
    )
    
    # 2. engagement_architecture_standards - Engagement-level minimums with version management
    op.create_table(
        'engagement_architecture_standards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('requirement_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mandatory', sa.Boolean(), default=True, nullable=False),
        sa.Column('supported_versions', postgresql.JSONB(), nullable=True),
        sa.Column('requirement_details', postgresql.JSONB(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('engagement_id', 'requirement_type', name='unique_engagement_requirement'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
    )
    
    # 3. application_architecture_overrides - App-specific exceptions with business rationale
    op.create_table(
        'application_architecture_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('standard_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('override_type', sa.String(100), nullable=False),
        sa.Column('override_details', postgresql.JSONB(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        # Constraints
        sa.CheckConstraint("override_type IN ('exception', 'modification', 'addition')", name='valid_override_type'),
        sa.ForeignKeyConstraint(['assessment_flow_id'], ['assessment_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['standard_id'], ['engagement_architecture_standards.id'], ondelete='SET NULL'),
    )
    
    # 4. application_components - Flexible component identification beyond 3-tier
    op.create_table(
        'application_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('component_name', sa.String(255), nullable=False),
        sa.Column('component_type', sa.String(100), nullable=False),
        sa.Column('technology_stack', postgresql.JSONB(), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        # Constraints
        sa.UniqueConstraint('assessment_flow_id', 'application_id', 'component_name', name='unique_app_component'),
        sa.ForeignKeyConstraint(['assessment_flow_id'], ['assessment_flows.id'], ondelete='CASCADE'),
    )
    
    # 5. tech_debt_analysis - Component-level tech debt with severity and remediation tracking
    op.create_table(
        'tech_debt_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('debt_category', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('remediation_effort_hours', sa.Integer(), nullable=True),
        sa.Column('impact_on_migration', sa.Text(), nullable=True),
        sa.Column('tech_debt_score', sa.Float(), nullable=True),
        sa.Column('detected_by_agent', sa.String(100), nullable=True),
        sa.Column('agent_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        # Constraints
        sa.CheckConstraint("severity IN ('critical', 'high', 'medium', 'low')", name='valid_severity'),
        sa.CheckConstraint('agent_confidence >= 0 AND agent_confidence <= 1', name='valid_agent_confidence'),
        sa.ForeignKeyConstraint(['assessment_flow_id'], ['assessment_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['component_id'], ['application_components.id'], ondelete='SET NULL'),
    )
    
    # 6. component_treatments - Individual component 6R decisions with compatibility validation
    op.create_table(
        'component_treatments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommended_strategy', sa.String(20), nullable=False, index=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('compatibility_validated', sa.Boolean(), default=False, nullable=False),
        sa.Column('compatibility_issues', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        # Constraints
        sa.CheckConstraint("recommended_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_recommended_strategy'),
        sa.UniqueConstraint('assessment_flow_id', 'component_id', name='unique_component_treatment'),
        sa.ForeignKeyConstraint(['assessment_flow_id'], ['assessment_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['component_id'], ['application_components.id'], ondelete='CASCADE'),
    )
    
    # 7. sixr_decisions - Application-level 6R decisions with component rollup
    op.create_table(
        'sixr_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('application_name', sa.String(255), nullable=False),
        sa.Column('overall_strategy', sa.String(20), nullable=False, index=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('architecture_exceptions', postgresql.JSONB(), default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('tech_debt_score', sa.Float(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('move_group_hints', postgresql.JSONB(), default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('estimated_effort_hours', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('user_modifications', postgresql.JSONB(), nullable=True),
        sa.Column('modified_by', sa.String(100), nullable=True),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('app_on_page_data', postgresql.JSONB(), nullable=True),
        sa.Column('decision_factors', postgresql.JSONB(), nullable=True),
        sa.Column('ready_for_planning', sa.Boolean(), default=False, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        # Constraints
        sa.CheckConstraint("overall_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_overall_strategy'),
        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='valid_confidence_score'),
        sa.UniqueConstraint('assessment_flow_id', 'application_id', name='unique_app_decision'),
        sa.ForeignKeyConstraint(['assessment_flow_id'], ['assessment_flows.id'], ondelete='CASCADE'),
    )
    
    # 8. assessment_learning_feedback - Learning feedback for agent improvement
    op.create_table(
        'assessment_learning_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('original_strategy', sa.String(20), nullable=False),
        sa.Column('override_strategy', sa.String(20), nullable=False),
        sa.Column('feedback_reason', sa.Text(), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('learned_pattern', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        # Constraints
        sa.CheckConstraint("original_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_original_strategy'),
        sa.CheckConstraint("override_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_override_strategy'),
        sa.ForeignKeyConstraint(['assessment_flow_id'], ['assessment_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decision_id'], ['sixr_decisions.id'], ondelete='CASCADE'),
    )
    
    # === CREATE PERFORMANCE INDEXES ===
    
    # Core performance indexes
    op.create_index('idx_assessment_flows_status', 'assessment_flows', ['status'])
    op.create_index('idx_assessment_flows_client', 'assessment_flows', ['client_account_id', 'engagement_id'])
    op.create_index('idx_assessment_flows_phase', 'assessment_flows', ['current_phase', 'next_phase'])
    op.create_index('idx_eng_arch_standards', 'engagement_architecture_standards', ['engagement_id'])
    op.create_index('idx_app_components', 'application_components', ['application_id'])
    op.create_index('idx_component_treatments', 'component_treatments', ['application_id', 'recommended_strategy'])
    op.create_index('idx_sixr_decisions_app', 'sixr_decisions', ['application_id'])
    op.create_index('idx_sixr_ready_planning', 'sixr_decisions', ['ready_for_planning'])
    op.create_index('idx_tech_debt_severity', 'tech_debt_analysis', ['severity'])
    op.create_index('idx_tech_debt_component', 'tech_debt_analysis', ['component_id'])
    
    # JSONB GIN indexes for complex queries
    op.execute("CREATE INDEX idx_assessment_flows_selected_apps_gin ON assessment_flows USING GIN(selected_application_ids)")
    op.execute("CREATE INDEX idx_assessment_flows_pause_points_gin ON assessment_flows USING GIN(pause_points)")
    op.execute("CREATE INDEX idx_assessment_flows_user_inputs_gin ON assessment_flows USING GIN(user_inputs)")
    op.execute("CREATE INDEX idx_component_tech_stack_gin ON application_components USING GIN(technology_stack)")
    op.execute("CREATE INDEX idx_component_dependencies_gin ON application_components USING GIN(dependencies)")
    op.execute("CREATE INDEX idx_sixr_app_on_page_gin ON sixr_decisions USING GIN(app_on_page_data)")
    
    # === RUN MIGRATION HOOKS ===
    
    # Run assessment-specific migration hooks
    from app.core.migration_hooks import MigrationHooks
    MigrationHooks.run_assessment_migration_hooks(op)


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key dependencies
    op.drop_table('assessment_learning_feedback')
    op.drop_table('sixr_decisions')
    op.drop_table('component_treatments')
    op.drop_table('tech_debt_analysis')
    op.drop_table('application_components')
    op.drop_table('application_architecture_overrides')
    op.drop_table('engagement_architecture_standards')
    op.drop_table('assessment_flows')