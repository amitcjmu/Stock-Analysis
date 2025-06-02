"""Add session support and RBAC models

Revision ID: 002_add_session_support
Revises: 001_initial_models
Create Date: 2025-01-28 10:00:00.000000

This migration adds:
- DataImportSession model for session-level tracking
- Enhanced ClientAccount model with business context
- Enhanced Engagement model with migration scope  
- RBAC models (UserProfile, UserRole, ClientAccess, EngagementAccess, AccessAuditLog)
- Session references in DataImport and CMDBAsset models
- Demo client "Pujyam Corp" with admin user

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '002_add_session_support'
down_revision = '83c1ba41e213'
branch_labels = None
depends_on = None


def upgrade():
    # Add enhanced fields to client_accounts table
    op.add_column('client_accounts', sa.Column('business_objectives', sa.JSON(), nullable=True))
    op.add_column('client_accounts', sa.Column('it_guidelines', sa.JSON(), nullable=True))
    op.add_column('client_accounts', sa.Column('decision_criteria', sa.JSON(), nullable=True))
    op.add_column('client_accounts', sa.Column('agent_preferences', sa.JSON(), nullable=True))
    
    # Create data_import_sessions table
    op.create_table('data_import_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_name', sa.String(length=255), nullable=False),
        sa.Column('session_display_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('auto_created', sa.Boolean(), nullable=False),
        sa.Column('source_filename', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('total_imports', sa.Integer(), nullable=True),
        sa.Column('total_assets_processed', sa.Integer(), nullable=True),
        sa.Column('total_records_imported', sa.Integer(), nullable=True),
        sa.Column('data_quality_score', sa.Integer(), nullable=True),
        sa.Column('session_config', sa.JSON(), nullable=True),
        sa.Column('business_context', sa.JSON(), nullable=True),
        sa.Column('agent_insights', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_import_sessions_id'), 'data_import_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_client_account_id'), 'data_import_sessions', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_engagement_id'), 'data_import_sessions', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_session_name'), 'data_import_sessions', ['session_name'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_status'), 'data_import_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_is_mock'), 'data_import_sessions', ['is_mock'], unique=False)
    
    # Add enhanced fields to engagements table
    op.add_column('engagements', sa.Column('migration_scope', sa.JSON(), nullable=True))
    op.add_column('engagements', sa.Column('team_preferences', sa.JSON(), nullable=True))
    op.add_column('engagements', sa.Column('current_session_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add session_id to data_imports table (handle existing data)
    # First add as nullable
    op.add_column('data_imports', sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create a default session for existing data_imports
    _create_default_sessions_for_existing_data(op)
    
    # Now make it NOT NULL
    op.alter_column('data_imports', 'session_id', nullable=False)
    op.create_index(op.f('ix_data_imports_session_id'), 'data_imports', ['session_id'], unique=False)
    op.create_foreign_key('fk_data_imports_session', 'data_imports', 'data_import_sessions', ['session_id'], ['id'], ondelete='CASCADE')
    
    # Add session_id to cmdb_assets table
    op.add_column('cmdb_assets', sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_cmdb_assets_session_id'), 'cmdb_assets', ['session_id'], unique=False)
    op.create_foreign_key('fk_cmdb_assets_session', 'cmdb_assets', 'data_import_sessions', ['session_id'], ['id'], ondelete='CASCADE')
    
    # Create RBAC tables
    
    # User profiles table
    op.create_table('user_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('approval_requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('registration_reason', sa.Text(), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('role_description', sa.String(length=255), nullable=True),
        sa.Column('requested_access_level', sa.String(length=20), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('manager_email', sa.String(length=255), nullable=True),
        sa.Column('linkedin_profile', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
        sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_status'), 'user_profiles', ['status'], unique=False)
    
    # User roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_type', sa.String(length=50), nullable=False),
        sa.Column('role_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('scope_type', sa.String(length=20), nullable=True),
        sa.Column('scope_client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['scope_client_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['scope_engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    op.create_index(op.f('ix_user_roles_user_id'), 'user_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_roles_is_active'), 'user_roles', ['is_active'], unique=False)
    
    # Client access table
    op.create_table('client_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('access_level', sa.String(length=20), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('restricted_environments', sa.JSON(), nullable=True),
        sa.Column('restricted_data_types', sa.JSON(), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_access_id'), 'client_access', ['id'], unique=False)
    op.create_index(op.f('ix_client_access_user_profile_id'), 'client_access', ['user_profile_id'], unique=False)
    op.create_index(op.f('ix_client_access_client_account_id'), 'client_access', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_client_access_is_active'), 'client_access', ['is_active'], unique=False)
    
    # Engagement access table
    op.create_table('engagement_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('access_level', sa.String(length=20), nullable=False),
        sa.Column('engagement_role', sa.String(length=100), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('restricted_sessions', sa.JSON(), nullable=True),
        sa.Column('allowed_session_types', sa.JSON(), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engagement_access_id'), 'engagement_access', ['id'], unique=False)
    op.create_index(op.f('ix_engagement_access_user_profile_id'), 'engagement_access', ['user_profile_id'], unique=False)
    op.create_index(op.f('ix_engagement_access_engagement_id'), 'engagement_access', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_engagement_access_is_active'), 'engagement_access', ['is_active'], unique=False)
    
    # Access audit log table
    op.create_table('access_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['data_import_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_access_audit_log_id'), 'access_audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_access_audit_log_user_id'), 'access_audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_access_audit_log_action_type'), 'access_audit_log', ['action_type'], unique=False)
    op.create_index(op.f('ix_access_audit_log_created_at'), 'access_audit_log', ['created_at'], unique=False)
    
    # Add foreign key for current_session_id in engagements
    op.create_foreign_key('fk_engagements_current_session', 'engagements', 'data_import_sessions', ['current_session_id'], ['id'])
    
    # Data seeding: Create demo client "Pujyam Corp" and admin user
    _seed_demo_data(op)


def downgrade():
    # Remove foreign keys first
    op.drop_constraint('fk_engagements_current_session', 'engagements', type_='foreignkey')
    op.drop_constraint('fk_cmdb_assets_session', 'cmdb_assets', type_='foreignkey')
    op.drop_constraint('fk_data_imports_session', 'data_imports', type_='foreignkey')
    
    # Drop RBAC tables
    op.drop_table('access_audit_log')
    op.drop_table('engagement_access')
    op.drop_table('client_access')
    op.drop_table('user_roles')
    op.drop_table('user_profiles')
    
    # Remove session columns
    op.drop_column('cmdb_assets', 'session_id')
    op.drop_column('data_imports', 'session_id')
    op.drop_column('engagements', 'current_session_id')
    op.drop_column('engagements', 'team_preferences')
    op.drop_column('engagements', 'migration_scope')
    
    # Drop sessions table
    op.drop_table('data_import_sessions')
    
    # Remove enhanced client account fields
    op.drop_column('client_accounts', 'agent_preferences')
    op.drop_column('client_accounts', 'decision_criteria')
    op.drop_column('client_accounts', 'it_guidelines')
    op.drop_column('client_accounts', 'business_objectives')


def _create_default_sessions_for_existing_data(op):
    """Create default sessions for existing data_imports that don't have sessions."""
    
    # Get existing data_imports
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT DISTINCT client_account_id, engagement_id, imported_by, created_at
        FROM data_imports 
        WHERE session_id IS NULL
        ORDER BY created_at
    """))
    
    existing_imports = result.fetchall()
    
    if not existing_imports:
        return
    
    print(f"Creating default sessions for {len(existing_imports)} existing data imports...")
    
    for import_record in existing_imports:
        client_account_id = import_record[0]
        engagement_id = import_record[1] 
        imported_by = import_record[2]
        created_at = import_record[3]
        
        # Generate session ID and name
        session_id = str(uuid.uuid4())
        session_name = f"legacy-import-{created_at.strftime('%Y%m%d-%H%M%S')}"
        
        # Create session
        connection.execute(sa.text(f"""
            INSERT INTO data_import_sessions (
                id, client_account_id, engagement_id, session_name, session_display_name,
                description, session_type, auto_created, status, progress_percentage,
                started_at, completed_at, last_activity_at, created_by, is_mock, created_at
            ) VALUES (
                '{session_id}',
                '{client_account_id}',
                '{engagement_id}',
                '{session_name}',
                'Legacy Import Session',
                'Auto-created session for existing data import',
                'legacy_import',
                true,
                'completed',
                100,
                '{created_at}',
                '{created_at}',
                '{created_at}',
                '{imported_by}',
                false,
                '{created_at}'
            )
        """))
        
        # Update data_imports to reference this session
        connection.execute(sa.text(f"""
            UPDATE data_imports 
            SET session_id = '{session_id}'
            WHERE client_account_id = '{client_account_id}' 
              AND engagement_id = '{engagement_id}'
              AND imported_by = '{imported_by}'
              AND session_id IS NULL
        """))
    
    print(f"✅ Created {len(existing_imports)} default sessions for existing data")


def _seed_demo_data(op):
    """Seed demo data for development and testing."""
    
    # Generate UUIDs for demo data
    admin_user_id = str(uuid.uuid4())
    pujyam_client_id = str(uuid.uuid4())
    demo_engagement_id = str(uuid.uuid4())
    
    # Create admin user
    op.execute(f"""
        INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, is_mock, created_at)
        VALUES (
            '{admin_user_id}',
            'admin@aiforce.com',
            '$2b$12$LQv3c1yqBwEHxPuNybpL.eO9wkQZlJ3Y1Z2KGV7gHhqbqJ8v5KXLS',  -- CNCoE2025
            'Admin',
            'User',
            true,
            true,
            false,
            now()
        );
    """)
    
    # Create admin user profile
    op.execute(f"""
        INSERT INTO user_profiles (user_id, status, approval_requested_at, approved_at, approved_by, 
                                 organization, role_description, requested_access_level, 
                                 notification_preferences, created_at)
        VALUES (
            '{admin_user_id}',
            'active',
            now(),
            now(),
            '{admin_user_id}',
            'AI Force Platform',
            'Platform Administrator',
            'super_admin',
            '{{"email_notifications": true, "system_alerts": true, "learning_updates": true, "weekly_reports": true}}',
            now()
        );
    """)
    
    # Create admin role
    admin_role_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO user_roles (id, user_id, role_type, role_name, description, permissions, 
                              scope_type, is_active, assigned_at, assigned_by, created_at)
        VALUES (
            '{admin_role_id}',
            '{admin_user_id}',
            'platform_admin',
            'Super Administrator',
            'Full platform access and user management',
            '{{"can_create_clients": true, "can_manage_engagements": true, "can_import_data": true, 
               "can_export_data": true, "can_view_analytics": true, "can_manage_users": true, 
               "can_configure_agents": true, "can_access_admin_console": true}}',
            'global',
            true,
            now(),
            '{admin_user_id}',
            now()
        );
    """)
    
    # Create Pujyam Corp demo client
    op.execute(f"""
        INSERT INTO client_accounts (id, name, slug, description, industry, company_size, 
                                   subscription_tier, business_objectives, it_guidelines, 
                                   decision_criteria, agent_preferences, is_mock, created_at, created_by)
        VALUES (
            '{pujyam_client_id}',
            'Pujyam Corp',
            'pujyam-corp',
            'Demo client for AI Force Migration Platform development and testing',
            'Technology Services',
            'enterprise',
            'enterprise',
            '{{"primary_goals": ["Cloud Migration", "Cost Optimization", "Modernization"], 
               "timeframe": "12 months", 
               "success_metrics": ["50% cost reduction", "Zero downtime migration", "Improved performance"],
               "budget_constraints": "5M USD",
               "compliance_requirements": ["SOC2", "ISO27001", "GDPR"]}}',
            '{{"architecture_patterns": ["Microservices", "API-first", "Cloud-native"],
               "security_requirements": ["Zero Trust", "End-to-end encryption", "Multi-factor auth"],
               "compliance_standards": ["SOC2", "ISO27001", "GDPR"],
               "technology_preferences": ["AWS", "Kubernetes", "Terraform"],
               "cloud_strategy": "Cloud-first with hybrid capabilities",
               "data_governance": {{"classification": "strict", "retention": "7 years", "privacy": "high"}}}}',
            '{{"risk_tolerance": "medium", "cost_sensitivity": "high", "innovation_appetite": "aggressive",
               "timeline_pressure": "medium", "quality_vs_speed": "quality", "technical_debt_tolerance": "low"}}',
            '{{"confidence_thresholds": {{"field_mapping": 0.85, "data_classification": 0.8, 
                                       "risk_assessment": 0.9, "migration_strategy": 0.95}},
               "learning_preferences": ["accuracy_focused", "conservative"],
               "custom_prompts": {{}},
               "notification_preferences": {{"confidence_alerts": true, "learning_updates": true, "error_notifications": true}}}}',
            false,
            now(),
            '{admin_user_id}'
        );
    """)
    
    # Create demo engagement
    op.execute(f"""
        INSERT INTO engagements (id, client_account_id, name, slug, description, engagement_type, 
                               status, priority, engagement_lead_id, client_contact_name, client_contact_email,
                               migration_scope, team_preferences, is_mock, created_at, created_by)
        VALUES (
            '{demo_engagement_id}',
            '{pujyam_client_id}',
            'Digital Transformation 2025',
            'digital-transformation-2025',
            'Comprehensive cloud migration and digital transformation initiative',
            'migration',
            'active',
            'high',
            '{admin_user_id}',
            'John Doe',
            'john.doe@pujyam.com',
            '{{"target_clouds": ["AWS"], 
               "migration_strategies": ["rehost", "replatform", "refactor"],
               "excluded_systems": [],
               "included_environments": ["Production", "Staging", "Development"],
               "business_units": ["IT", "Operations", "Finance"],
               "geographic_scope": ["North America", "Europe"],
               "timeline_constraints": {{"go_live_date": "2025-12-31", "freeze_periods": ["2025-11-15 to 2025-12-15"]}}}}',
            '{{"stakeholders": [{{"name": "John Doe", "role": "CTO", "email": "john.doe@pujyam.com", "decision_authority": "high"}}],
               "decision_makers": ["John Doe", "Jane Smith"],
               "technical_leads": ["Alice Johnson", "Bob Wilson"],
               "communication_style": "formal",
               "reporting_frequency": "weekly",
               "preferred_meeting_times": ["Tuesday 10 AM", "Friday 2 PM"],
               "escalation_contacts": ["john.doe@pujyam.com"],
               "project_methodology": "agile"}}',
            false,
            now(),
            '{admin_user_id}'
        );
    """)
    
    # Grant admin access to Pujyam Corp
    client_access_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO client_access (id, user_profile_id, client_account_id, access_level, 
                                 permissions, granted_at, granted_by, is_active, created_at)
        VALUES (
            '{client_access_id}',
            '{admin_user_id}',
            '{pujyam_client_id}',
            'admin',
            '{{"can_view_data": true, "can_import_data": true, "can_export_data": true, 
               "can_manage_engagements": true, "can_configure_client_settings": true, "can_manage_client_users": true}}',
            now(),
            '{admin_user_id}',
            true,
            now()
        );
    """)
    
    # Grant admin access to demo engagement
    engagement_access_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO engagement_access (id, user_profile_id, engagement_id, access_level, 
                                     engagement_role, permissions, granted_at, granted_by, is_active, created_at)
        VALUES (
            '{engagement_access_id}',
            '{admin_user_id}',
            '{demo_engagement_id}',
            'admin',
            'Platform Administrator',
            '{{"can_view_data": true, "can_import_data": true, "can_export_data": true, 
               "can_manage_sessions": true, "can_configure_agents": true, 
               "can_approve_migration_decisions": true, "can_access_sensitive_data": true}}',
            now(),
            '{admin_user_id}',
            true,
            now()
        );
    """)
    
    print("✅ Demo data seeded successfully:")
    print(f"   - Admin user: admin@aiforce.com / CNCoE2025")
    print(f"   - Demo client: Pujyam Corp ({pujyam_client_id})")
    print(f"   - Demo engagement: Digital Transformation 2025 ({demo_engagement_id})") 