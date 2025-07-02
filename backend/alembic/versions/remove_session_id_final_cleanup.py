"""Remove session_id final cleanup

Revision ID: remove_session_id_cleanup
Revises: 001_complete_schema_correct_order
Create Date: 2025-01-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'remove_session_id_cleanup'
down_revision = '001_complete_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Remove session_id columns from all tables"""
    
    # Drop column from discovery_flows table
    op.drop_column('discovery_flows', 'import_session_id')
    
    # Drop column from assets table
    op.drop_column('assets', 'session_id')
    
    # Drop column from access_audit_log table (RBAC)
    op.drop_column('access_audit_log', 'session_id')
    
    # Drop column from flow_deletion_audit table
    op.drop_column('flow_deletion_audit', 'session_id')
    
    # Drop column from llm_usage_logs table (renamed from session_id to flow_id)
    # Note: This column was already renamed in the model, so we're aligning the database
    op.execute("ALTER TABLE llm_usage_logs RENAME COLUMN session_id TO flow_id")
    
    # Drop any related indexes (if they exist)
    op.execute("DROP INDEX IF EXISTS idx_discovery_flows_import_session_id")
    op.execute("DROP INDEX IF EXISTS idx_assets_session_id")
    op.execute("DROP INDEX IF EXISTS idx_access_audit_log_session_id")
    
    # Note: Not dropping data_import_sessions table as it's still in use
    # The table tracks import operations and has been refactored to work with flow_id


def downgrade():
    """Not supporting downgrade - this is final cleanup"""
    raise NotImplementedError("Downgrade not supported for session_id cleanup")