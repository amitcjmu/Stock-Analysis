"""Add multi-tenant models and pgvector support

Revision ID: 001_multi_tenant
Revises: 
Create Date: 2025-01-28 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Import pgvector with fallback
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = sa.Text

# revision identifiers
revision = '001_multi_tenant'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    if PGVECTOR_AVAILABLE:
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create client_accounts table
    op.create_table('client_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('subscription_tier', sa.String(length=50), nullable=True),
        sa.Column('billing_contact_email', sa.String(length=255), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('branding', sa.JSON(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_accounts_id'), 'client_accounts', ['id'], unique=False)
    op.create_index(op.f('ix_client_accounts_slug'), 'client_accounts', ['slug'], unique=True)
    op.create_index(op.f('ix_client_accounts_is_mock'), 'client_accounts', ['is_mock'], unique=False)
    op.create_index(op.f('ix_client_accounts_is_active'), 'client_accounts', ['is_active'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_is_mock'), 'users', ['is_mock'], unique=False)

    # Add foreign key constraint to client_accounts
    op.create_foreign_key(None, 'client_accounts', 'users', ['created_by'], ['id'])

    # Create engagements table
    op.create_table('engagements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('engagement_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('engagement_lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_contact_name', sa.String(length=255), nullable=True),
        sa.Column('client_contact_email', sa.String(length=255), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_lead_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_account_id', 'slug')
    )
    op.create_index(op.f('ix_engagements_id'), 'engagements', ['id'], unique=False)
    op.create_index(op.f('ix_engagements_client_account_id'), 'engagements', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_engagements_status'), 'engagements', ['status'], unique=False)
    op.create_index(op.f('ix_engagements_is_mock'), 'engagements', ['is_mock'], unique=False)
    op.create_index(op.f('ix_engagements_is_active'), 'engagements', ['is_active'], unique=False)

    # Create user_account_associations table
    op.create_table('user_account_associations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_account_associations_user_id'), 'user_account_associations', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_account_associations_client_account_id'), 'user_account_associations', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_user_account_associations_is_mock'), 'user_account_associations', ['is_mock'], unique=False)

    # Create cmdb_assets table
    op.create_table('cmdb_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('asset_type', sa.Enum('server', 'database', 'application', 'network_device', 'router', 'switch', 'firewall', 'load_balancer', 'storage_device', 'san', 'nas', 'security_device', 'virtual_machine', 'virtualization_platform', 'container', 'cloud_service', 'infrastructure_device', 'unknown', name='assettype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('fqdn', sa.String(length=255), nullable=True),
        sa.Column('mac_address', sa.String(length=17), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('datacenter', sa.String(length=100), nullable=True),
        sa.Column('rack_location', sa.String(length=50), nullable=True),
        sa.Column('availability_zone', sa.String(length=50), nullable=True),
        sa.Column('operating_system', sa.String(length=100), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.Column('cpu_cores', sa.Integer(), nullable=True),
        sa.Column('memory_gb', sa.Float(), nullable=True),
        sa.Column('storage_gb', sa.Float(), nullable=True),
        sa.Column('business_owner', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('application_name', sa.String(length=255), nullable=True),
        sa.Column('technology_stack', sa.String(length=255), nullable=True),
        sa.Column('criticality', sa.String(length=20), nullable=True),
        sa.Column('status', sa.Enum('discovered', 'pending', 'analyzed', 'ready_for_migration', 'migrated', 'failed', 'excluded', name='assetstatus'), nullable=True),
        sa.Column('six_r_strategy', sa.Enum('rehost', 'replatform', 'refactor', 'rearchitect', 'retire', 'retain', name='sixrstrategy'), nullable=True),
        sa.Column('migration_priority', sa.Integer(), nullable=True),
        sa.Column('migration_complexity', sa.String(length=20), nullable=True),
        sa.Column('migration_wave', sa.Integer(), nullable=True),
        sa.Column('sixr_ready', sa.String(length=50), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('related_assets', sa.JSON(), nullable=True),
        sa.Column('discovery_method', sa.String(length=50), nullable=True),
        sa.Column('discovery_source', sa.String(length=100), nullable=True),
        sa.Column('discovery_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cpu_utilization_percent', sa.Float(), nullable=True),
        sa.Column('memory_utilization_percent', sa.Float(), nullable=True),
        sa.Column('disk_iops', sa.Float(), nullable=True),
        sa.Column('network_throughput_mbps', sa.Float(), nullable=True),
        sa.Column('current_monthly_cost', sa.Float(), nullable=True),
        sa.Column('estimated_cloud_cost', sa.Float(), nullable=True),
        sa.Column('imported_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_filename', sa.String(length=255), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('field_mappings_used', sa.JSON(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['imported_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cmdb_assets_id'), 'cmdb_assets', ['id'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_client_account_id'), 'cmdb_assets', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_engagement_id'), 'cmdb_assets', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_name'), 'cmdb_assets', ['name'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_hostname'), 'cmdb_assets', ['hostname'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_asset_type'), 'cmdb_assets', ['asset_type'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_environment'), 'cmdb_assets', ['environment'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_status'), 'cmdb_assets', ['status'], unique=False)
    op.create_index(op.f('ix_cmdb_assets_is_mock'), 'cmdb_assets', ['is_mock'], unique=False)

    # Create tags table
    op.create_table('tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference_embedding', Vector(1536) if PGVECTOR_AVAILABLE else sa.Text(), nullable=True),
        sa.Column('confidence_threshold', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    op.create_index(op.f('ix_tags_category'), 'tags', ['category'], unique=False)
    op.create_index(op.f('ix_tags_is_active'), 'tags', ['is_active'], unique=False)

    # Create cmdb_asset_embeddings table
    op.create_table('cmdb_asset_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cmdb_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding', Vector(1536) if PGVECTOR_AVAILABLE else sa.Text(), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cmdb_asset_id'], ['cmdb_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cmdb_asset_id', 'client_account_id', 'engagement_id', name='unique_asset_embedding')
    )
    op.create_index(op.f('ix_cmdb_asset_embeddings_id'), 'cmdb_asset_embeddings', ['id'], unique=False)
    op.create_index(op.f('ix_cmdb_asset_embeddings_cmdb_asset_id'), 'cmdb_asset_embeddings', ['cmdb_asset_id'], unique=False)
    op.create_index(op.f('ix_cmdb_asset_embeddings_client_account_id'), 'cmdb_asset_embeddings', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_cmdb_asset_embeddings_engagement_id'), 'cmdb_asset_embeddings', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_cmdb_asset_embeddings_is_mock'), 'cmdb_asset_embeddings', ['is_mock'], unique=False)
    
    # Create HNSW index for vector similarity search if pgvector is available
    if PGVECTOR_AVAILABLE:
        op.create_index('ix_cmdb_asset_embeddings_hnsw', 'cmdb_asset_embeddings', ['embedding'], 
                       postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})

    # Create cmdb_sixr_analyses table (renamed to avoid conflict)
    op.create_table('cmdb_sixr_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('total_assets', sa.Integer(), nullable=True),
        sa.Column('rehost_count', sa.Integer(), nullable=True),
        sa.Column('replatform_count', sa.Integer(), nullable=True),
        sa.Column('refactor_count', sa.Integer(), nullable=True),
        sa.Column('rearchitect_count', sa.Integer(), nullable=True),
        sa.Column('retire_count', sa.Integer(), nullable=True),
        sa.Column('retain_count', sa.Integer(), nullable=True),
        sa.Column('total_current_cost', sa.Float(), nullable=True),
        sa.Column('total_estimated_cost', sa.Float(), nullable=True),
        sa.Column('potential_savings', sa.Float(), nullable=True),
        sa.Column('analysis_results', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cmdb_sixr_analyses_id'), 'cmdb_sixr_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_cmdb_sixr_analyses_client_account_id'), 'cmdb_sixr_analyses', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_cmdb_sixr_analyses_engagement_id'), 'cmdb_sixr_analyses', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_cmdb_sixr_analyses_status'), 'cmdb_sixr_analyses', ['status'], unique=False)
    op.create_index(op.f('ix_cmdb_sixr_analyses_is_mock'), 'cmdb_sixr_analyses', ['is_mock'], unique=False)

    # Create migration_waves table
    op.create_table('migration_waves',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wave_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('planned_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_assets', sa.Integer(), nullable=True),
        sa.Column('completed_assets', sa.Integer(), nullable=True),
        sa.Column('failed_assets', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),
        sa.Column('estimated_effort_hours', sa.Float(), nullable=True),
        sa.Column('actual_effort_hours', sa.Float(), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_migration_waves_id'), 'migration_waves', ['id'], unique=False)
    op.create_index(op.f('ix_migration_waves_client_account_id'), 'migration_waves', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_migration_waves_engagement_id'), 'migration_waves', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_migration_waves_wave_number'), 'migration_waves', ['wave_number'], unique=False)
    op.create_index(op.f('ix_migration_waves_status'), 'migration_waves', ['status'], unique=False)
    op.create_index(op.f('ix_migration_waves_is_mock'), 'migration_waves', ['is_mock'], unique=False)

    # Create asset_tags table
    op.create_table('asset_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cmdb_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('assigned_method', sa.String(length=50), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cmdb_asset_id'], ['cmdb_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id']),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_tags_cmdb_asset_id'), 'asset_tags', ['cmdb_asset_id'], unique=False)
    op.create_index(op.f('ix_asset_tags_tag_id'), 'asset_tags', ['tag_id'], unique=False)
    op.create_index(op.f('ix_asset_tags_is_mock'), 'asset_tags', ['is_mock'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('asset_tags')
    op.drop_table('migration_waves')
    op.drop_table('cmdb_sixr_analyses')
    
    if PGVECTOR_AVAILABLE:
        op.drop_index('ix_cmdb_asset_embeddings_hnsw', table_name='cmdb_asset_embeddings')
    op.drop_table('cmdb_asset_embeddings')
    op.drop_table('tags')
    op.drop_table('cmdb_assets')
    op.drop_table('user_account_associations')
    op.drop_table('engagements')
    op.drop_table('users')
    op.drop_table('client_accounts')
    
    # Drop pgvector extension (optional, might be used by other apps)
    # op.execute('DROP EXTENSION IF EXISTS vector') 