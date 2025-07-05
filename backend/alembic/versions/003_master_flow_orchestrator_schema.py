"""Master Flow Orchestrator Schema Updates
Add new columns to crewai_flow_state_extensions table for unified flow management

Revision ID: master_flow_orchestrator_001
Revises: 002_add_assessment_flow_tables
Create Date: 2025-01-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'master_flow_orchestrator_001'
down_revision = '002_add_assessment_flow_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns and indexes to crewai_flow_state_extensions table"""
    
    # Add new columns to crewai_flow_state_extensions
    op.add_column('crewai_flow_state_extensions', 
        sa.Column('phase_transitions', postgresql.JSONB, nullable=True, 
                  server_default=text("'[]'::jsonb"),
                  comment='History of phase transitions with timestamps'))
    
    op.add_column('crewai_flow_state_extensions', 
        sa.Column('error_history', postgresql.JSONB, nullable=True,
                  server_default=text("'[]'::jsonb"),
                  comment='History of errors with recovery attempts'))
    
    op.add_column('crewai_flow_state_extensions', 
        sa.Column('retry_count', sa.Integer, nullable=False,
                  server_default='0',
                  comment='Number of retry attempts for current phase'))
    
    op.add_column('crewai_flow_state_extensions', 
        sa.Column('parent_flow_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='Reference to parent flow for hierarchical flows'))
    
    op.add_column('crewai_flow_state_extensions', 
        sa.Column('child_flow_ids', postgresql.JSONB, nullable=True,
                  server_default=text("'[]'::jsonb"),
                  comment='List of child flow IDs for hierarchical flows'))
    
    op.add_column('crewai_flow_state_extensions', 
        sa.Column('flow_metadata', postgresql.JSONB, nullable=True,
                  server_default=text("'{}'::jsonb"),
                  comment='Additional flow-specific metadata'))
    
    # Create performance indexes
    op.create_index('idx_crewai_flow_state_flow_type_status', 
                    'crewai_flow_state_extensions', 
                    ['flow_type', 'flow_status'])
    
    op.create_index('idx_crewai_flow_state_client_status', 
                    'crewai_flow_state_extensions', 
                    ['client_account_id', 'flow_status'])
    
    op.create_index('idx_crewai_flow_state_created_desc', 
                    'crewai_flow_state_extensions', 
                    [sa.text('created_at DESC')])
    
    # Add foreign key for parent_flow_id
    op.create_foreign_key('fk_crewai_flow_state_parent',
                          'crewai_flow_state_extensions', 
                          'crewai_flow_state_extensions',
                          ['parent_flow_id'], ['flow_id'],
                          ondelete='SET NULL')
    
    # Add CHECK constraints for data integrity
    op.create_check_constraint('chk_valid_flow_type',
                               'crewai_flow_state_extensions',
                               "flow_type IN ('discovery', 'assessment', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission')")
    
    op.create_check_constraint('chk_valid_flow_status',
                               'crewai_flow_state_extensions',
                               "flow_status IN ('initialized', 'active', 'processing', 'paused', 'completed', 'failed', 'cancelled')")
    
    op.create_check_constraint('chk_retry_count_positive',
                               'crewai_flow_state_extensions',
                               'retry_count >= 0')
    
    # Migrate existing discovery_flows data
    migrate_discovery_flows()
    
    # Migrate existing assessment_flows data
    migrate_assessment_flows()


def migrate_discovery_flows():
    """Migrate existing discovery_flows to master flow orchestrator"""
    connection = op.get_bind()
    
    # Get all discovery flows that don't have corresponding master flow entries
    result = connection.execute(text("""
        SELECT df.flow_id, df.client_account_id, df.engagement_id, df.user_id,
               df.flow_name, df.status, df.current_phase, df.created_at, df.updated_at,
               df.crewai_state_data, df.error_message, df.error_details
        FROM discovery_flows df
        LEFT JOIN crewai_flow_state_extensions cfs ON df.flow_id = cfs.flow_id
        WHERE cfs.flow_id IS NULL
    """))
    
    for row in result:
        # Map discovery flow status to master flow status
        status_mapping = {
            'active': 'active',
            'completed': 'completed',
            'failed': 'failed',
            'paused': 'paused',
            'initialized': 'initialized'
        }
        master_status = status_mapping.get(row.status, 'active')
        
        # Build phase transitions from discovery flow state
        phase_transitions = []
        if row.current_phase:
            phase_transitions.append({
                'phase': row.current_phase,
                'status': 'active',
                'timestamp': row.updated_at.isoformat() if row.updated_at else datetime.utcnow().isoformat()
            })
        
        # Build error history if errors exist
        error_history = []
        if row.error_message:
            error_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'phase': row.current_phase or 'unknown',
                'error': row.error_message,
                'details': row.error_details or {}
            })
        
        # Build flow metadata
        flow_metadata = {
            'source': 'discovery_flow_migration',
            'migrated_at': datetime.utcnow().isoformat(),
            'original_status': row.status
        }
        
        # Insert into master flow table
        connection.execute(text("""
            INSERT INTO crewai_flow_state_extensions (
                id, flow_id, client_account_id, engagement_id, user_id,
                flow_type, flow_name, flow_status, created_at, updated_at,
                flow_persistence_data, phase_transitions, error_history,
                retry_count, flow_metadata
            ) VALUES (
                :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                :flow_type, :flow_name, :flow_status, :created_at, :updated_at,
                :flow_persistence_data, :phase_transitions, :error_history,
                :retry_count, :flow_metadata
            )
        """), {
            'id': str(uuid.uuid4()),
            'flow_id': str(row.flow_id),
            'client_account_id': str(row.client_account_id),
            'engagement_id': str(row.engagement_id),
            'user_id': row.user_id,
            'flow_type': 'discovery',
            'flow_name': row.flow_name,
            'flow_status': master_status,
            'created_at': row.created_at,
            'updated_at': row.updated_at or row.created_at,
            'flow_persistence_data': row.crewai_state_data or {},
            'phase_transitions': phase_transitions,
            'error_history': error_history,
            'retry_count': 0,
            'flow_metadata': flow_metadata
        })
        
        # Update discovery_flows with master_flow_id
        connection.execute(text("""
            UPDATE discovery_flows 
            SET master_flow_id = :flow_id 
            WHERE flow_id = :flow_id
        """), {'flow_id': str(row.flow_id)})


def migrate_assessment_flows():
    """Migrate existing assessment_flows to master flow orchestrator"""
    connection = op.get_bind()
    
    # Get all assessment flows
    result = connection.execute(text("""
        SELECT id, client_account_id, engagement_id, status, current_phase,
               created_at, updated_at, completed_at, phase_results, agent_insights
        FROM assessment_flows
    """))
    
    for row in result:
        # Generate flow_id for assessment flows (they don't have one yet)
        flow_id = str(uuid.uuid4())
        
        # Map assessment flow status to master flow status
        status_mapping = {
            'initialized': 'initialized',
            'processing': 'processing',
            'paused_for_user_input': 'paused',
            'completed': 'completed',
            'error': 'failed'
        }
        master_status = status_mapping.get(row.status, 'active')
        
        # Build phase transitions from assessment flow state
        phase_transitions = []
        if row.current_phase:
            phase_transitions.append({
                'phase': row.current_phase,
                'status': 'active' if row.status == 'processing' else row.status,
                'timestamp': row.updated_at.isoformat() if row.updated_at else datetime.utcnow().isoformat()
            })
        
        # Build flow metadata
        flow_metadata = {
            'source': 'assessment_flow_migration',
            'migrated_at': datetime.utcnow().isoformat(),
            'original_id': str(row.id),
            'original_status': row.status
        }
        
        # Extract user_id from engagement (we'll use a default for now)
        user_id = 'system_migration'
        
        # Insert into master flow table
        connection.execute(text("""
            INSERT INTO crewai_flow_state_extensions (
                id, flow_id, client_account_id, engagement_id, user_id,
                flow_type, flow_name, flow_status, created_at, updated_at,
                flow_persistence_data, phase_transitions, error_history,
                retry_count, flow_metadata
            ) VALUES (
                :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                :flow_type, :flow_name, :flow_status, :created_at, :updated_at,
                :flow_persistence_data, :phase_transitions, :error_history,
                :retry_count, :flow_metadata
            )
        """), {
            'id': str(uuid.uuid4()),
            'flow_id': flow_id,
            'client_account_id': str(row.client_account_id),
            'engagement_id': str(row.engagement_id),
            'user_id': user_id,
            'flow_type': 'assessment',
            'flow_name': f'Assessment Flow - {row.id}',
            'flow_status': master_status,
            'created_at': row.created_at,
            'updated_at': row.updated_at or row.created_at,
            'flow_persistence_data': {
                'phase_results': row.phase_results or {},
                'agent_insights': row.agent_insights or []
            },
            'phase_transitions': phase_transitions,
            'error_history': [],
            'retry_count': 0,
            'flow_metadata': flow_metadata
        })
        
        # Add flow_id column to assessment_flows if it doesn't exist
        try:
            op.add_column('assessment_flows', 
                sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=True))
        except Exception:
            pass  # Column might already exist
        
        # Update assessment_flows with the generated flow_id
        connection.execute(text("""
            UPDATE assessment_flows 
            SET flow_id = :flow_id 
            WHERE id = :id
        """), {'flow_id': flow_id, 'id': str(row.id)})


def downgrade():
    """Remove added columns and indexes from crewai_flow_state_extensions table"""
    
    # Drop CHECK constraints
    op.drop_constraint('chk_retry_count_positive', 'crewai_flow_state_extensions')
    op.drop_constraint('chk_valid_flow_status', 'crewai_flow_state_extensions')
    op.drop_constraint('chk_valid_flow_type', 'crewai_flow_state_extensions')
    
    # Drop foreign key
    op.drop_constraint('fk_crewai_flow_state_parent', 'crewai_flow_state_extensions')
    
    # Drop indexes
    op.drop_index('idx_crewai_flow_state_created_desc', 'crewai_flow_state_extensions')
    op.drop_index('idx_crewai_flow_state_client_status', 'crewai_flow_state_extensions')
    op.drop_index('idx_crewai_flow_state_flow_type_status', 'crewai_flow_state_extensions')
    
    # Drop columns
    op.drop_column('crewai_flow_state_extensions', 'flow_metadata')
    op.drop_column('crewai_flow_state_extensions', 'child_flow_ids')
    op.drop_column('crewai_flow_state_extensions', 'parent_flow_id')
    op.drop_column('crewai_flow_state_extensions', 'retry_count')
    op.drop_column('crewai_flow_state_extensions', 'error_history')
    op.drop_column('crewai_flow_state_extensions', 'phase_transitions')
    
    # Remove flow_id from assessment_flows if we added it
    try:
        op.drop_column('assessment_flows', 'flow_id')
    except Exception:
        pass