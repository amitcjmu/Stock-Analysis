"""Enhanced RBAC system with hierarchical roles and soft delete management

Revision ID: 004_enhanced_rbac_system
Revises: 003_session_management  
Create Date: 2025-01-28 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_enhanced_rbac_system'
down_revision = '002_add_session_support'
branch_labels = None
depends_on = None


def upgrade():
    # Create enhanced_user_profiles table
    op.create_table('enhanced_user_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_level', sa.String(length=30), nullable=False, index=True),
        sa.Column('data_scope', sa.String(length=20), nullable=False),
        sa.Column('scope_client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, index=True, server_default='pending_approval'),
        sa.Column('approval_requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('registration_reason', sa.Text(), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('role_description', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('manager_email', sa.String(length=255), nullable=True),
        sa.Column('linkedin_profile', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('delete_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['scope_client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['scope_engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_enhanced_user_profiles_role_level'), 'enhanced_user_profiles', ['role_level'], unique=False)
    op.create_index(op.f('ix_enhanced_user_profiles_status'), 'enhanced_user_profiles', ['status'], unique=False)
    op.create_index(op.f('ix_enhanced_user_profiles_user_id'), 'enhanced_user_profiles', ['user_id'], unique=False)
    
    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_level', sa.String(length=30), nullable=False, index=True),
        sa.Column('can_manage_platform_settings', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_all_clients', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_all_users', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_purge_deleted_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_view_system_logs', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_create_clients', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_modify_client_settings', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_client_users', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete_client_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_create_engagements', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_modify_engagement_settings', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_engagement_users', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete_engagement_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_import_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_export_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_view_analytics', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_modify_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_configure_agents', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_view_agent_insights', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_approve_agent_decisions', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_permissions_role_level'), 'role_permissions', ['role_level'], unique=False)
    
    # Create soft_deleted_items table
    op.create_table('soft_deleted_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('item_id', sa.String(length=255), nullable=False, index=True),
        sa.Column('item_name', sa.String(length=255), nullable=True),
        sa.Column('item_data', sa.JSON(), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('delete_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending_review', index=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_decision', sa.String(length=20), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('purged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('restored_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_soft_deleted_items_item_id'), 'soft_deleted_items', ['item_id'], unique=False)
    op.create_index(op.f('ix_soft_deleted_items_item_type'), 'soft_deleted_items', ['item_type'], unique=False)
    op.create_index(op.f('ix_soft_deleted_items_status'), 'soft_deleted_items', ['status'], unique=False)
    
    # Create enhanced_access_audit_log table
    op.create_table('enhanced_access_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('user_role_level', sa.String(length=30), nullable=True),
        sa.Column('user_data_scope', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enhanced_access_audit_log_action_type'), 'enhanced_access_audit_log', ['action_type'], unique=False)
    op.create_index(op.f('ix_enhanced_access_audit_log_created_at'), 'enhanced_access_audit_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_enhanced_access_audit_log_user_id'), 'enhanced_access_audit_log', ['user_id'], unique=False)
    
    # Insert default role permissions
    op.execute("""
        INSERT INTO role_permissions (id, role_level, can_manage_platform_settings, can_manage_all_clients, 
                                     can_manage_all_users, can_purge_deleted_data, can_view_system_logs,
                                     can_create_clients, can_modify_client_settings, can_manage_client_users,
                                     can_delete_client_data, can_create_engagements, can_modify_engagement_settings,
                                     can_manage_engagement_users, can_delete_engagement_data, can_import_data,
                                     can_export_data, can_view_analytics, can_modify_data, can_configure_agents,
                                     can_view_agent_insights, can_approve_agent_decisions)
        VALUES 
        (gen_random_uuid(), 'platform_admin', true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true),
        (gen_random_uuid(), 'client_admin', false, false, false, false, false, false, true, true, true, true, true, true, true, true, true, true, true, true, true, true),
        (gen_random_uuid(), 'engagement_manager', false, false, false, false, false, false, false, false, false, false, true, true, true, true, true, true, true, false, true, true),
        (gen_random_uuid(), 'analyst', false, false, false, false, false, false, false, false, false, false, false, false, false, true, true, true, true, false, true, false),
        (gen_random_uuid(), 'viewer', false, false, false, false, false, false, false, false, false, false, false, false, false, false, true, true, false, false, true, false),
        (gen_random_uuid(), 'anonymous', false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, true, false, false, false, false)
    """)
    
    # Create demo platform admin user profile
    op.execute("""
        INSERT INTO enhanced_user_profiles (user_id, role_level, data_scope, status, approved_at, 
                                           organization, role_description, notification_preferences)
        SELECT id, 'platform_admin', 'platform', 'active', now(), 
               'AI Force Platform', 'Platform Administrator',
               '{"email_notifications": true, "system_alerts": true, "learning_updates": true, "weekly_reports": true}'::json
        FROM users 
        WHERE email = 'admin@aiforce.com'
        ON CONFLICT (user_id) DO NOTHING
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('enhanced_access_audit_log')
    op.drop_table('soft_deleted_items')
    op.drop_table('role_permissions')
    op.drop_table('enhanced_user_profiles') 