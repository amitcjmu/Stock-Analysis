# Database Design Architecture

## Overview

The AI Modernize Migration Platform uses PostgreSQL as its primary database with a sophisticated multi-tenant architecture designed to support enterprise-scale cloud migration projects. The database design emphasizes data isolation, scalability, and comprehensive audit trails.

## Database Technology Stack

### Core Technologies
- **PostgreSQL 14+**: Primary relational database with JSON/JSONB support
- **SQLAlchemy 2.0**: ORM with async support and modern patterns
- **Alembic**: Database migration management
- **asyncpg**: High-performance async PostgreSQL driver
- **UUID**: Primary key generation for distributed systems
- **pgvector**: Vector storage for AI embeddings (future)

### Connection Configuration

```python
# High-performance async connection pool
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)
```

## Multi-Tenant Architecture

### Tenant Isolation Strategy

The platform implements **Row-Level Security (RLS)** with client account and engagement scoping:

```sql
-- Every data query includes tenant context
SELECT * FROM assets 
WHERE client_account_id = ? 
AND engagement_id = ?
AND user_has_access(?, client_account_id, engagement_id);
```

### Tenant Hierarchy

```
Platform
├── Client Accounts (Organizations)
│   ├── Users (with roles: admin, member, viewer)
│   ├── Engagements (Projects/Migrations)
│   │   ├── Discovery Flows
│   │   ├── Collection Flows  
│   │   ├── Assessment Flows
│   │   ├── Assets
│   │   └── Data Imports
│   └── Settings & Preferences
└── Platform Administration
```

## Core Domain Models

### 1. Multi-Tenancy Foundation

#### Client Accounts
```sql
CREATE TABLE client_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    
    -- Subscription & Billing
    subscription_tier VARCHAR(50) DEFAULT 'standard',
    max_users INTEGER,
    max_engagements INTEGER,
    storage_quota_gb INTEGER,
    api_quota_monthly INTEGER,
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    features_enabled JSONB DEFAULT '{}',
    agent_configuration JSONB DEFAULT '{}',
    branding JSONB DEFAULT '{}',
    
    -- Business Context
    business_objectives JSONB DEFAULT '{
        "primary_goals": [],
        "timeframe": "",
        "success_metrics": [],
        "constraints": []
    }',
    
    -- AI Agent Preferences
    agent_preferences JSONB DEFAULT '{
        "discovery_depth": "comprehensive",
        "automation_level": "assisted", 
        "risk_tolerance": "moderate",
        "preferred_clouds": [],
        "compliance_requirements": []
    }',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT client_accounts_pkey PRIMARY KEY (id),
    CONSTRAINT client_accounts_slug_unique UNIQUE (slug)
);

CREATE INDEX idx_client_accounts_active ON client_accounts(is_active);
CREATE INDEX idx_client_accounts_subscription ON client_accounts(subscription_tier);
```

#### Engagements
```sql
CREATE TABLE engagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    engagement_type VARCHAR(50) DEFAULT 'migration',
    status VARCHAR(50) DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'medium',
    
    -- Timeline
    start_date TIMESTAMPTZ,
    target_completion_date TIMESTAMPTZ,
    actual_completion_date TIMESTAMPTZ,
    
    -- Team
    engagement_lead_id UUID REFERENCES users(id),
    client_contact_name VARCHAR(255),
    client_contact_email VARCHAR(255),
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    migration_scope JSONB DEFAULT '{
        "target_clouds": [],
        "migration_strategies": [],
        "excluded_systems": [],
        "included_environments": [],
        "business_units": [],
        "geographic_scope": []
    }',
    
    -- Audit fields  
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT engagements_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_engagements_client ON engagements(client_account_id);
CREATE INDEX idx_engagements_status ON engagements(status);
CREATE INDEX idx_engagements_active ON engagements(is_active);
```

#### Users and Authentication
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    
    -- Status flags
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Default context for faster login
    default_client_id UUID REFERENCES client_accounts(id),
    default_engagement_id UUID REFERENCES engagements(id),
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_unique UNIQUE (email)
);

-- User-Client associations with roles
CREATE TABLE user_account_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    CONSTRAINT user_account_associations_pkey PRIMARY KEY (id),
    CONSTRAINT user_client_unique UNIQUE (user_id, client_account_id)
);

CREATE INDEX idx_user_associations_user ON user_account_associations(user_id);
CREATE INDEX idx_user_associations_client ON user_account_associations(client_account_id);
```

### 2. Flow Orchestration Architecture

The platform uses a **dual-table pattern** for flow management, providing both orchestration control and workflow-specific data:

#### Master Flow Coordination
```sql
CREATE TABLE crewai_flow_state_extensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID UNIQUE NOT NULL,  -- CrewAI Flow ID (single source of truth)
    
    -- Multi-tenant isolation
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    user_id VARCHAR NOT NULL,
    
    -- Flow metadata
    flow_type VARCHAR(50) NOT NULL, -- 'discovery', 'collection', 'assessment'
    flow_name VARCHAR(255) NOT NULL,
    flow_version VARCHAR(20) DEFAULT '1.0',
    
    -- State management
    flow_status VARCHAR(50) DEFAULT 'initialized', -- 'initialized', 'running', 'paused', 'completed', 'failed'
    current_phase VARCHAR(100),
    progress_percentage INTEGER DEFAULT 0,
    
    -- Configuration
    flow_config JSONB DEFAULT '{}',
    agent_config JSONB DEFAULT '{}',
    
    -- Performance tracking
    performance_metrics JSONB DEFAULT '{}',
    execution_stats JSONB DEFAULT '{}',
    error_details JSONB DEFAULT '{}',
    
    -- State persistence
    flow_persistence_data JSONB DEFAULT '{}',
    checkpoint_data JSONB DEFAULT '{}',
    phase_transitions JSONB DEFAULT '[]',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT crewai_flow_state_extensions_pkey PRIMARY KEY (id),
    CONSTRAINT flow_id_unique UNIQUE (flow_id)
);

CREATE INDEX idx_flow_extensions_client ON crewai_flow_state_extensions(client_account_id);
CREATE INDEX idx_flow_extensions_engagement ON crewai_flow_state_extensions(engagement_id);
CREATE INDEX idx_flow_extensions_type ON crewai_flow_state_extensions(flow_type);
CREATE INDEX idx_flow_extensions_status ON crewai_flow_state_extensions(flow_status);
```

#### Discovery Flow Specifics
```sql
CREATE TABLE discovery_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID UNIQUE NOT NULL,  -- References crewai_flow_state_extensions.flow_id
    
    -- Links to master flow
    master_flow_id UUID REFERENCES crewai_flow_state_extensions(flow_id) ON DELETE CASCADE,
    
    -- Multi-tenant isolation (denormalized for performance)
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    user_id VARCHAR NOT NULL,
    
    -- Data source
    data_import_id UUID REFERENCES data_imports(id),
    
    -- Discovery-specific state
    flow_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- UI-facing status
    current_phase VARCHAR(100) DEFAULT 'data_import',
    progress_percentage INTEGER DEFAULT 0,
    
    -- Phase completion flags  
    data_import_completed BOOLEAN DEFAULT FALSE,
    field_mapping_completed BOOLEAN DEFAULT FALSE,
    data_cleansing_completed BOOLEAN DEFAULT FALSE,
    asset_inventory_completed BOOLEAN DEFAULT FALSE,
    dependency_analysis_completed BOOLEAN DEFAULT FALSE,
    tech_debt_completed BOOLEAN DEFAULT FALSE,
    
    -- Analysis results
    analysis_results JSONB DEFAULT '{}',
    field_mappings JSONB DEFAULT '{}',
    data_quality_metrics JSONB DEFAULT '{}',
    
    -- CrewAI state data
    crewai_state_data JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_phase_update TIMESTAMPTZ,
    
    CONSTRAINT discovery_flows_pkey PRIMARY KEY (id),
    CONSTRAINT discovery_flows_flow_id_unique UNIQUE (flow_id)
);

CREATE INDEX idx_discovery_flows_master ON discovery_flows(master_flow_id);
CREATE INDEX idx_discovery_flows_client ON discovery_flows(client_account_id);
CREATE INDEX idx_discovery_flows_engagement ON discovery_flows(engagement_id);
CREATE INDEX idx_discovery_flows_status ON discovery_flows(status);
CREATE INDEX idx_discovery_flows_phase ON discovery_flows(current_phase);
```

### 3. Data Import and Asset Management

#### Data Imports
```sql
CREATE TABLE data_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    
    filename VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    file_type VARCHAR(50),
    upload_status VARCHAR(50) DEFAULT 'pending',
    
    -- Processing results
    total_rows INTEGER,
    valid_rows INTEGER,
    invalid_rows INTEGER,
    columns_detected JSONB DEFAULT '[]',
    
    -- Data storage
    file_path TEXT,
    processed_data JSONB,
    validation_errors JSONB DEFAULT '[]',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    uploaded_by UUID REFERENCES users(id),
    
    CONSTRAINT data_imports_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_data_imports_client ON data_imports(client_account_id);
CREATE INDEX idx_data_imports_engagement ON data_imports(engagement_id);
CREATE INDEX idx_data_imports_status ON data_imports(upload_status);
```

#### Assets
```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    
    -- Asset identification
    asset_name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(100), -- 'server', 'application', 'database', 'network'
    environment VARCHAR(100), -- 'production', 'staging', 'development'
    
    -- Technical details
    specifications JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '[]',
    configurations JSONB DEFAULT '{}',
    
    -- Migration analysis
    migration_readiness JSONB DEFAULT '{}',
    sixr_recommendation VARCHAR(50), -- 'rehost', 'replatform', 'refactor', etc.
    complexity_score INTEGER,
    risk_score INTEGER,
    
    -- Discovery metadata
    discovered_from_import_id UUID REFERENCES data_imports(id),
    discovery_flow_id UUID REFERENCES discovery_flows(flow_id),
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_analyzed TIMESTAMPTZ,
    
    CONSTRAINT assets_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_assets_client ON assets(client_account_id);
CREATE INDEX idx_assets_engagement ON assets(engagement_id);
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_environment ON assets(environment);
CREATE INDEX idx_assets_sixr ON assets(sixr_recommendation);
CREATE INDEX idx_assets_discovery ON assets(discovery_flow_id);
```

### 4. AI Agent and Learning Systems

#### Agent Memory and Learning
```sql
CREATE TABLE agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL,
    engagement_id UUID,
    
    agent_type VARCHAR(100) NOT NULL,
    memory_type VARCHAR(50), -- 'pattern', 'decision', 'feedback'
    
    memory_content JSONB NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    
    -- Context
    context_tags JSONB DEFAULT '[]',
    related_flows JSONB DEFAULT '[]',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ,
    
    CONSTRAINT agent_memory_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_agent_memory_client ON agent_memory(client_account_id);
CREATE INDEX idx_agent_memory_type ON agent_memory(agent_type, memory_type);
CREATE INDEX idx_agent_memory_confidence ON agent_memory(confidence_score);
```

#### Agent Performance Tracking
```sql
CREATE TABLE agent_task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL,
    engagement_id UUID,
    flow_id UUID,
    
    agent_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    task_description TEXT,
    
    -- Performance metrics
    duration_seconds INTEGER,
    tokens_used INTEGER,
    success_rate FLOAT,
    
    -- Results
    task_result JSONB,
    error_details JSONB,
    
    -- Audit fields
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT agent_task_history_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_agent_tasks_client ON agent_task_history(client_account_id);
CREATE INDEX idx_agent_tasks_flow ON agent_task_history(flow_id);
CREATE INDEX idx_agent_tasks_agent ON agent_task_history(agent_name);
CREATE INDEX idx_agent_tasks_type ON agent_task_history(task_type);
CREATE INDEX idx_agent_tasks_started ON agent_task_history(started_at);
```

### 5. Collection Flow (Adaptive Data Collection)

#### Collection Flows
```sql
CREATE TABLE collection_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    flow_name VARCHAR(255) NOT NULL,
    flow_type VARCHAR(50) DEFAULT 'adaptive', -- 'adaptive', 'bulk', 'integration'
    status VARCHAR(50) DEFAULT 'active',
    
    -- Collection configuration
    target_application_count INTEGER,
    collection_method VARCHAR(50), -- 'forms', 'bulk_upload', 'api_integration'
    
    -- Progress tracking
    applications_identified INTEGER DEFAULT 0,
    applications_completed INTEGER DEFAULT 0,
    data_quality_score FLOAT DEFAULT 0.0,
    
    -- Collection data
    application_catalog JSONB DEFAULT '[]',
    collection_metadata JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT collection_flows_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_collection_flows_client ON collection_flows(client_account_id);
CREATE INDEX idx_collection_flows_engagement ON collection_flows(engagement_id);
CREATE INDEX idx_collection_flows_status ON collection_flows(status);
```

### 6. Assessment and Analysis

#### Assessment Flows
```sql
CREATE TABLE assessment_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID UNIQUE NOT NULL,
    
    -- Links to master flow
    master_flow_id UUID REFERENCES crewai_flow_state_extensions(flow_id) ON DELETE CASCADE,
    
    -- Multi-tenant isolation
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    user_id VARCHAR NOT NULL,
    
    flow_name VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(50) DEFAULT 'comprehensive', -- 'quick', 'comprehensive', 'targeted'
    status VARCHAR(50) DEFAULT 'active',
    
    -- Assessment scope
    asset_scope JSONB DEFAULT '{}',
    assessment_criteria JSONB DEFAULT '{}',
    
    -- Results
    assessment_results JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT assessment_flows_pkey PRIMARY KEY (id)
);
```

#### 6R Analysis Results
```sql
CREATE TABLE sixr_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    
    -- 6R Recommendation
    primary_recommendation VARCHAR(50) NOT NULL, -- 'rehost', 'replatform', 'refactor', 'rearchitect', 'rebuild', 'retire'
    confidence_score FLOAT NOT NULL,
    
    -- Alternative recommendations
    alternative_options JSONB DEFAULT '[]',
    
    -- Analysis details
    analysis_criteria JSONB DEFAULT '{}',
    cost_estimation JSONB DEFAULT '{}',
    effort_estimation JSONB DEFAULT '{}',
    risk_factors JSONB DEFAULT '[]',
    
    -- Decision rationale
    rationale TEXT,
    business_impact JSONB DEFAULT '{}',
    technical_considerations JSONB DEFAULT '{}',
    
    -- Audit fields
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    analyzed_by VARCHAR(255), -- Agent or user identifier
    
    CONSTRAINT sixr_analysis_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_sixr_analysis_asset ON sixr_analysis(asset_id);
CREATE INDEX idx_sixr_analysis_recommendation ON sixr_analysis(primary_recommendation);
CREATE INDEX idx_sixr_analysis_confidence ON sixr_analysis(confidence_score);
```

## Data Consistency and Integrity

### 1. Referential Integrity

```sql
-- Foreign key constraints ensure data consistency
ALTER TABLE discovery_flows 
ADD CONSTRAINT fk_discovery_master_flow 
FOREIGN KEY (master_flow_id) 
REFERENCES crewai_flow_state_extensions(flow_id) 
ON DELETE CASCADE;

-- Cascading deletes for tenant cleanup
ALTER TABLE assets 
ADD CONSTRAINT fk_assets_client 
FOREIGN KEY (client_account_id) 
REFERENCES client_accounts(id) 
ON DELETE CASCADE;
```

### 2. Data Validation Constraints

```sql
-- Ensure valid status values
ALTER TABLE discovery_flows 
ADD CONSTRAINT check_discovery_status 
CHECK (status IN ('active', 'paused', 'completed', 'failed', 'cancelled'));

-- Ensure valid percentages
ALTER TABLE discovery_flows 
ADD CONSTRAINT check_progress_percentage 
CHECK (progress_percentage >= 0 AND progress_percentage <= 100);

-- Ensure valid confidence scores
ALTER TABLE sixr_analysis 
ADD CONSTRAINT check_confidence_score 
CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0);
```

### 3. Data Triggers for Consistency

```sql
-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_discovery_flows_updated_at
    BEFORE UPDATE ON discovery_flows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

## Performance Optimization

### 1. Indexing Strategy

```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_discovery_flows_tenant_status 
ON discovery_flows(client_account_id, engagement_id, status);

CREATE INDEX idx_assets_tenant_type 
ON assets(client_account_id, engagement_id, asset_type);

-- Partial indexes for active records
CREATE INDEX idx_active_discovery_flows 
ON discovery_flows(client_account_id, engagement_id) 
WHERE status = 'active';

-- GIN indexes for JSONB queries
CREATE INDEX idx_assets_specifications_gin 
ON assets USING GIN (specifications);

CREATE INDEX idx_flow_config_gin 
ON crewai_flow_state_extensions USING GIN (flow_config);
```

### 2. Query Optimization

```sql
-- Materialized view for dashboard aggregations
CREATE MATERIALIZED VIEW engagement_summary AS
SELECT 
    e.id AS engagement_id,
    e.client_account_id,
    e.name AS engagement_name,
    COUNT(DISTINCT df.id) AS discovery_flows_count,
    COUNT(DISTINCT a.id) AS assets_count,
    AVG(df.progress_percentage) AS avg_progress,
    COUNT(DISTINCT CASE WHEN df.status = 'completed' THEN df.id END) AS completed_flows
FROM engagements e
LEFT JOIN discovery_flows df ON e.id = df.engagement_id
LEFT JOIN assets a ON e.id = a.engagement_id
WHERE e.is_active = TRUE
GROUP BY e.id, e.client_account_id, e.name;

-- Refresh strategy
CREATE INDEX idx_engagement_summary_client 
ON engagement_summary(client_account_id);
```

### 3. Connection Pooling

```python
# Production database configuration
DATABASE_CONFIG = {
    "pool_size": 20,              # Base connections
    "max_overflow": 30,           # Additional connections
    "pool_timeout": 30,           # Wait time for connection
    "pool_recycle": 3600,         # Recycle connections hourly
    "pool_pre_ping": True,        # Validate connections
    "echo": False,                # Disable SQL logging in production
}
```

## Security Implementation

### 1. Row-Level Security (RLS)

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_flows ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY tenant_isolation_assets ON assets
    FOR ALL TO application_user
    USING (client_account_id = current_setting('app.current_client_id')::UUID);

CREATE POLICY tenant_isolation_discovery ON discovery_flows
    FOR ALL TO application_user  
    USING (client_account_id = current_setting('app.current_client_id')::UUID);
```

### 2. Data Encryption

```sql
-- Encrypt sensitive fields
ALTER TABLE users 
ALTER COLUMN email 
SET DATA TYPE TEXT USING pgp_sym_encrypt(email, current_setting('app.encryption_key'));

-- Create secure views for sensitive data
CREATE VIEW users_secure AS
SELECT 
    id,
    pgp_sym_decrypt(email::BYTEA, current_setting('app.encryption_key')) AS email,
    first_name,
    last_name,
    is_active,
    created_at
FROM users;
```

### 3. Audit Logging

```sql
-- Audit table for all data changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    client_account_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, client_account_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW), 
                COALESCE(current_setting('app.current_user_id', true)::UUID, NULL),
                COALESCE(current_setting('app.current_client_id', true)::UUID, NULL));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, client_account_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW),
                COALESCE(current_setting('app.current_user_id', true)::UUID, NULL),
                COALESCE(current_setting('app.current_client_id', true)::UUID, NULL));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, operation, old_values, user_id, client_account_id)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD),
                COALESCE(current_setting('app.current_user_id', true)::UUID, NULL),
                COALESCE(current_setting('app.current_client_id', true)::UUID, NULL));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

## Data Migration and Schema Evolution

### 1. Alembic Migration Strategy

```python
# alembic/env.py - Multi-tenant migration setup
def run_migrations_online():
    """Run migrations in 'online' mode with tenant awareness."""
    
    # Create engine with proper configuration
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        **DATABASE_CONFIG
    )

    with connectable.connect() as connection:
        # Set application-level settings for migrations
        connection.execute(text("SET app.migration_mode = 'true'"))
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()
```

### 2. Version Management

```python
# Migration version naming convention
# Format: YYYY_MM_DD_HHMM_description
# Example: 2025_01_18_1200_add_agent_memory_table.py

"""Add agent memory table for persistent learning

Revision ID: abc123def456
Revises: def456ghi789
Create Date: 2025-01-18 12:00:00.000000

"""

def upgrade():
    # Forward migration
    op.create_table(
        'agent_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('memory_content', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Backward migration with data preservation
    op.execute("CREATE BACKUP TABLE agent_memory_backup AS SELECT * FROM agent_memory")
    op.drop_table('agent_memory')
```

## Backup and Recovery

### 1. Backup Strategy

```bash
#!/bin/bash
# Automated backup script with encryption

# Full database backup
pg_dump \
  --host=$DB_HOST \
  --port=$DB_PORT \
  --username=$DB_USER \
  --format=custom \
  --compress=9 \
  --verbose \
  --file="backup_$(date +%Y%m%d_%H%M%S).dump" \
  $DB_NAME

# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup_*.dump

# Upload to S3 with retention policy
aws s3 cp backup_*.dump.gpg s3://migration-platform-backups/daily/ \
  --storage-class STANDARD_IA
```

### 2. Point-in-Time Recovery

```sql
-- Enable WAL archiving for point-in-time recovery
archive_mode = on
archive_command = 'cp %p /backup/archive/%f'
wal_level = replica
max_wal_senders = 3
```

## Monitoring and Observability

### 1. Performance Monitoring

```sql
-- Query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Monitor slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE mean_time > 1000  -- Queries taking > 1 second
ORDER BY mean_time DESC;
```

### 2. Health Checks

```python
async def database_health_check():
    """Comprehensive database health check."""
    try:
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            result = await session.execute(text("SELECT 1"))
            
            # Test tenant isolation
            await session.execute(text("""
                SELECT COUNT(*) FROM client_accounts 
                WHERE is_active = TRUE
            """))
            
            # Test flow state consistency
            await session.execute(text("""
                SELECT COUNT(*) FROM discovery_flows df
                JOIN crewai_flow_state_extensions cse ON df.master_flow_id = cse.flow_id
                WHERE df.status != cse.flow_status
            """))
            
            return {"status": "healthy", "timestamp": datetime.utcnow()}
            
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow()}
```

## Best Practices

### 1. Schema Design Principles
- Use UUIDs for all primary keys to support distributed systems
- Implement soft deletes with `is_active` flags
- Include comprehensive audit fields on all tables
- Use JSONB for flexible configuration and metadata storage
- Design for multi-tenancy from the start

### 2. Query Optimization
- Always include tenant filters in queries
- Use appropriate indexes for common query patterns
- Leverage JSONB GIN indexes for configuration queries
- Implement query result caching for expensive operations
- Monitor and optimize slow queries regularly

### 3. Security Guidelines
- Enable row-level security on all tenant-scoped tables
- Encrypt sensitive PII data at rest
- Implement comprehensive audit logging
- Use parameterized queries to prevent SQL injection
- Regular security audits and penetration testing

### 4. Migration Guidelines
- Test all migrations in staging environment first
- Implement rollback procedures for all schema changes
- Use feature flags for gradual rollout of new features
- Maintain backward compatibility during transitions
- Document all schema changes and their business impact

Last Updated: 2025-01-18