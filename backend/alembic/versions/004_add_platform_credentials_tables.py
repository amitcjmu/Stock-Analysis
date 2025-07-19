"""Add Platform Credentials tables for ADCS

Revision ID: 004_add_platform_credentials_tables
Revises: 003_add_collection_flow_tables
Create Date: 2025-07-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_add_platform_credentials_tables'
down_revision = '003_add_collection_flow_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credential status enum
    sa.Enum('active', 'expired', 'revoked', 'pending_rotation', name='credentialstatus').create(op.get_bind())
    
    # Create credential type enum
    sa.Enum('api_key', 'oauth2', 'basic_auth', 'service_account', 'certificate', 'ssh_key', 'custom', name='credentialtype').create(op.get_bind())
    
    # Create vault provider enum
    sa.Enum('local', 'aws_kms', 'azure_keyvault', 'gcp_kms', 'hashicorp_vault', name='vaultprovider').create(op.get_bind())
    
    # Create platform_credentials table (A4.1)
    op.create_table('platform_credentials',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_account_id', sa.UUID(), nullable=False),
        sa.Column('platform_adapter_id', sa.UUID(), nullable=False),
        sa.Column('credential_name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('credential_type', postgresql.ENUM('api_key', 'oauth2', 'basic_auth', 'service_account', 'certificate', 'ssh_key', 'custom', name='credentialtype', create_type=False), nullable=False),
        sa.Column('vault_provider', postgresql.ENUM('local', 'aws_kms', 'azure_keyvault', 'gcp_kms', 'hashicorp_vault', name='vaultprovider', create_type=False), server_default='local', nullable=False),
        sa.Column('vault_reference', sa.VARCHAR(length=500), nullable=True),
        sa.Column('encrypted_data', sa.TEXT(), nullable=False),
        sa.Column('encryption_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('credential_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'expired', 'revoked', 'pending_rotation', name='credentialstatus', create_type=False), server_default='active', nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_rotated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_validated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], name=op.f('fk_platform_credentials_client_account_id_client_accounts')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_platform_credentials_created_by_users')),
        sa.ForeignKeyConstraint(['platform_adapter_id'], ['platform_adapters.id'], name=op.f('fk_platform_credentials_platform_adapter_id_platform_adapters')),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name=op.f('fk_platform_credentials_updated_by_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_platform_credentials')),
        sa.UniqueConstraint('client_account_id', 'platform_adapter_id', 'credential_name', name='_client_platform_credential_uc')
    )
    op.create_index(op.f('ix_platform_credentials_client_account_id'), 'platform_credentials', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_platform_credentials_platform_adapter_id'), 'platform_credentials', ['platform_adapter_id'], unique=False)
    op.create_index(op.f('ix_platform_credentials_credential_type'), 'platform_credentials', ['credential_type'], unique=False)
    op.create_index(op.f('ix_platform_credentials_status'), 'platform_credentials', ['status'], unique=False)
    op.create_index(op.f('ix_platform_credentials_expires_at'), 'platform_credentials', ['expires_at'], unique=False)
    
    # Create credential_access_logs table (A4.5)
    op.create_table('credential_access_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('credential_id', sa.UUID(), nullable=False),
        sa.Column('accessed_by', sa.UUID(), nullable=False),
        sa.Column('access_type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('access_purpose', sa.TEXT(), nullable=True),
        sa.Column('collection_flow_id', sa.UUID(), nullable=True),
        sa.Column('ip_address', sa.VARCHAR(length=45), nullable=True),
        sa.Column('user_agent', sa.TEXT(), nullable=True),
        sa.Column('success', sa.BOOLEAN(), server_default=sa.text('true'), nullable=False),
        sa.Column('error_message', sa.TEXT(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('accessed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['accessed_by'], ['users.id'], name=op.f('fk_credential_access_logs_accessed_by_users')),
        sa.ForeignKeyConstraint(['collection_flow_id'], ['collection_flows.id'], name=op.f('fk_credential_access_logs_collection_flow_id_collection_flows'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['credential_id'], ['platform_credentials.id'], name=op.f('fk_credential_access_logs_credential_id_platform_credentials'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_credential_access_logs'))
    )
    op.create_index(op.f('ix_credential_access_logs_credential_id'), 'credential_access_logs', ['credential_id'], unique=False)
    op.create_index(op.f('ix_credential_access_logs_accessed_by'), 'credential_access_logs', ['accessed_by'], unique=False)
    op.create_index(op.f('ix_credential_access_logs_accessed_at'), 'credential_access_logs', ['accessed_at'], unique=False)
    op.create_index(op.f('ix_credential_access_logs_access_type'), 'credential_access_logs', ['access_type'], unique=False)
    op.create_index(op.f('ix_credential_access_logs_success'), 'credential_access_logs', ['success'], unique=False)
    
    # Create credential_rotation_history table (A4.6)
    op.create_table('credential_rotation_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('credential_id', sa.UUID(), nullable=False),
        sa.Column('rotation_type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('old_expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('new_expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('rotation_reason', sa.TEXT(), nullable=True),
        sa.Column('rotated_by', sa.UUID(), nullable=False),
        sa.Column('success', sa.BOOLEAN(), server_default=sa.text('true'), nullable=False),
        sa.Column('error_message', sa.TEXT(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('rotated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['credential_id'], ['platform_credentials.id'], name=op.f('fk_credential_rotation_history_credential_id_platform_credentials'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rotated_by'], ['users.id'], name=op.f('fk_credential_rotation_history_rotated_by_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_credential_rotation_history'))
    )
    op.create_index(op.f('ix_credential_rotation_history_credential_id'), 'credential_rotation_history', ['credential_id'], unique=False)
    op.create_index(op.f('ix_credential_rotation_history_rotated_at'), 'credential_rotation_history', ['rotated_at'], unique=False)
    op.create_index(op.f('ix_credential_rotation_history_rotation_type'), 'credential_rotation_history', ['rotation_type'], unique=False)
    
    # Create credential_permissions table (A4.4)
    op.create_table('credential_permissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('credential_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('role', sa.VARCHAR(length=50), nullable=True),
        sa.Column('permission_type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('granted_by', sa.UUID(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('revoked_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['credential_id'], ['platform_credentials.id'], name=op.f('fk_credential_permissions_credential_id_platform_credentials'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], name=op.f('fk_credential_permissions_granted_by_users')),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id'], name=op.f('fk_credential_permissions_revoked_by_users')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_credential_permissions_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_credential_permissions')),
        sa.CheckConstraint('(user_id IS NOT NULL) OR (role IS NOT NULL)', name=op.f('ck_credential_permissions_user_or_role'))
    )
    op.create_index(op.f('ix_credential_permissions_credential_id'), 'credential_permissions', ['credential_id'], unique=False)
    op.create_index(op.f('ix_credential_permissions_user_id'), 'credential_permissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_credential_permissions_role'), 'credential_permissions', ['role'], unique=False)
    op.create_index(op.f('ix_credential_permissions_permission_type'), 'credential_permissions', ['permission_type'], unique=False)
    
    # Add credential_id reference to collected_data_inventory table
    op.add_column('collected_data_inventory', 
        sa.Column('credential_id', sa.UUID(), nullable=True))
    
    # Add foreign key constraint for credential_id
    op.create_foreign_key(
        op.f('fk_collected_data_inventory_credential_id_platform_credentials'),
        'collected_data_inventory', 'platform_credentials',
        ['credential_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for credential_id
    op.create_index(op.f('ix_collected_data_inventory_credential_id'), 
                    'collected_data_inventory', ['credential_id'], unique=False)


def downgrade() -> None:
    # Drop index and foreign key from collected_data_inventory
    op.drop_index(op.f('ix_collected_data_inventory_credential_id'), table_name='collected_data_inventory')
    op.drop_constraint(op.f('fk_collected_data_inventory_credential_id_platform_credentials'), 
                      'collected_data_inventory', type_='foreignkey')
    op.drop_column('collected_data_inventory', 'credential_id')
    
    # Drop credential_permissions indexes and table
    op.drop_index(op.f('ix_credential_permissions_permission_type'), table_name='credential_permissions')
    op.drop_index(op.f('ix_credential_permissions_role'), table_name='credential_permissions')
    op.drop_index(op.f('ix_credential_permissions_user_id'), table_name='credential_permissions')
    op.drop_index(op.f('ix_credential_permissions_credential_id'), table_name='credential_permissions')
    op.drop_table('credential_permissions')
    
    # Drop credential_rotation_history indexes and table
    op.drop_index(op.f('ix_credential_rotation_history_rotation_type'), table_name='credential_rotation_history')
    op.drop_index(op.f('ix_credential_rotation_history_rotated_at'), table_name='credential_rotation_history')
    op.drop_index(op.f('ix_credential_rotation_history_credential_id'), table_name='credential_rotation_history')
    op.drop_table('credential_rotation_history')
    
    # Drop credential_access_logs indexes and table
    op.drop_index(op.f('ix_credential_access_logs_success'), table_name='credential_access_logs')
    op.drop_index(op.f('ix_credential_access_logs_access_type'), table_name='credential_access_logs')
    op.drop_index(op.f('ix_credential_access_logs_accessed_at'), table_name='credential_access_logs')
    op.drop_index(op.f('ix_credential_access_logs_accessed_by'), table_name='credential_access_logs')
    op.drop_index(op.f('ix_credential_access_logs_credential_id'), table_name='credential_access_logs')
    op.drop_table('credential_access_logs')
    
    # Drop platform_credentials indexes and table
    op.drop_index(op.f('ix_platform_credentials_expires_at'), table_name='platform_credentials')
    op.drop_index(op.f('ix_platform_credentials_status'), table_name='platform_credentials')
    op.drop_index(op.f('ix_platform_credentials_credential_type'), table_name='platform_credentials')
    op.drop_index(op.f('ix_platform_credentials_platform_adapter_id'), table_name='platform_credentials')
    op.drop_index(op.f('ix_platform_credentials_client_account_id'), table_name='platform_credentials')
    op.drop_table('platform_credentials')
    
    # Drop enums
    sa.Enum(name='vaultprovider').drop(op.get_bind())
    sa.Enum(name='credentialtype').drop(op.get_bind())
    sa.Enum(name='credentialstatus').drop(op.get_bind())