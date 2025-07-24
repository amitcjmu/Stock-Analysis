# Database Architecture Decisions - AI Modernize Migration Platform

## Table of Contents
1. [Overview](#overview)
2. [Key Architecture Decisions](#key-architecture-decisions)
3. [Schema Design Rationale](#schema-design-rationale)
4. [Multi-Phase Orchestration](#multi-phase-orchestration)
5. [Multi-Tenancy Strategy](#multi-tenancy-strategy)
6. [Data Type Choices](#data-type-choices)
7. [Performance Optimizations](#performance-optimizations)
8. [Future Considerations](#future-considerations)

## Overview

This document captures the key architectural decisions made in designing the database schema for the AI Modernize Migration Platform. Each decision is documented with context, alternatives considered, and rationale for the chosen approach.

## Key Architecture Decisions

### ADR-001: Single Schema Isolation

**Decision**: Use a single PostgreSQL schema named `migration` for all tables.

**Context**: 
- Need clear namespace separation from other applications
- Future possibility of multi-database deployments
- Simplified backup and permission management

**Alternatives Considered**:
1. **Public schema** - Default PostgreSQL approach
2. **Schema per tenant** - Complete isolation per client
3. **Schema per module** - Separate schemas for discovery, assessment, etc.

**Chosen Approach**: Single `migration` schema

**Rationale**:
- Provides namespace isolation without complexity
- Easy to backup/restore entire schema
- Supports future multi-database scenarios
- Simplifies cross-module queries
- Reduces operational overhead

**Trade-offs**:
- Less isolation than schema-per-tenant
- All tables in one namespace (mitigated by naming conventions)

### ADR-002: UUID Primary Keys

**Decision**: Use PostgreSQL native UUID type with `gen_random_uuid()` for all primary keys.

**Context**:
- Distributed system with multiple services creating records
- Need globally unique identifiers
- Potential for data synchronization across environments

**Alternatives Considered**:
1. **Serial integers** - Traditional auto-incrementing IDs
2. **Snowflake IDs** - Twitter's distributed ID generation
3. **ULIDs** - Lexicographically sortable unique identifiers

**Chosen Approach**: PostgreSQL UUID v4

**Rationale**:
- Native PostgreSQL support (no custom functions)
- Globally unique without coordination
- Standard format recognized by all tools
- Good indexing performance with B-tree
- Prevents ID enumeration attacks

**Trade-offs**:
- 16 bytes vs 8 bytes for bigint
- Not sortable by creation time
- Slightly slower inserts than serial

### ADR-003: Master Flow Orchestration

**Decision**: Implement hierarchical flow orchestration with `master_flow_id` linking all phases.

**Context**:
- Multi-phase migration process (discovery → assessment → planning → execution)
- Need to track assets across all phases
- Requirement for cross-phase reporting

**Architecture**:
```
crewai_flow_state_extensions (Master)
    ├── discovery_flows
    ├── assessment_flows
    ├── planning_flows
    └── execution_flows

assets.master_flow_id → Links to master flow
assets.discovery_flow_id → Specific phase reference
```

**Alternatives Considered**:
1. **Flat structure** - Independent flows without hierarchy
2. **Foreign keys only** - Direct relationships between phases
3. **Event sourcing** - Complete event log of all changes

**Chosen Approach**: Hierarchical with master flow

**Rationale**:
- Clear ownership and lifecycle management
- Enables cross-phase asset tracking
- Supports future workflow orchestration
- Maintains referential integrity
- Allows phase-independent operations

**Trade-offs**:
- Additional join for cross-phase queries
- More complex than flat structure
- Requires careful null handling during initialization

### ADR-004: Hybrid State Management

**Decision**: Use both boolean flags and JSON for discovery flow state management.

**Context**:
- Existing code checks boolean flags (data_import_completed, etc.)
- Need for more flexible state management
- CrewAI integration requires JSON state storage

**Implementation**:
```sql
-- Boolean flags (backward compatibility)
data_import_completed BOOLEAN DEFAULT false,
attribute_mapping_completed BOOLEAN DEFAULT false,

-- JSON state (flexibility)
current_phase VARCHAR(100),
phases_completed JSONB DEFAULT '[]',
crew_ai_state JSONB DEFAULT '{}'
```

**Alternatives Considered**:
1. **Boolean only** - Simple but inflexible
2. **JSON only** - Flexible but requires migration
3. **State machine table** - Separate state tracking

**Chosen Approach**: Hybrid boolean + JSON

**Rationale**:
- Maintains backward compatibility
- Provides migration path to JSON
- Supports complex CrewAI states
- Allows gradual transition
- Best of both worlds

**Trade-offs**:
- Redundant state representation
- Synchronization complexity
- Eventually should migrate to JSON only

## Schema Design Rationale

### Asset Table Design

**Decision**: Keep all 60+ fields in the assets table despite many being NULL.

**Rationale**:
1. **Import Flexibility**: Different import sources provide different fields
2. **Field Mapping Target**: Acts as a schema for what can be mapped
3. **Future Proofing**: Ready for new data sources
4. **Query Performance**: Avoiding joins for common attributes
5. **Business Requirements**: Comprehensive asset inventory

**Key Field Groups**:
- **Identification**: Name, type, CMDB ID
- **Infrastructure**: Hostname, IP, OS, hardware specs
- **Business Context**: Owner, department, criticality
- **Migration Planning**: 6R strategy, wave, complexity
- **Performance Metrics**: Utilization, IOPS, throughput
- **Cost Data**: Current and projected costs

### Multi-Tenant Fields

**Decision**: Include `client_account_id` and `engagement_id` in every table.

**Rationale**:
1. **Row-Level Security**: Foundation for RLS policies
2. **Query Performance**: Partition pruning with indexes
3. **Data Isolation**: Guaranteed tenant separation
4. **Compliance**: Audit trail per tenant
5. **Flexibility**: Supports cross-engagement queries when needed

**Implementation Pattern**:
```sql
-- Every table includes
client_account_id UUID NOT NULL REFERENCES client_accounts(id),
engagement_id UUID NOT NULL REFERENCES engagements(id),

-- Composite index for performance
INDEX ix_table_client_engagement (client_account_id, engagement_id)
```

### Test Data Strategy

**Decision**: Use dedicated test tenant IDs instead of `is_mock` boolean flags.

**Original Approach**:
```sql
is_mock BOOLEAN DEFAULT false  -- Mixed with production data
```

**New Approach**:
```sql
-- Dedicated test tenants
TEST_TENANT_1 = "11111111-1111-1111-1111-111111111111"
TEST_TENANT_2 = "22222222-2222-2222-2222-222222222222"
```

**Rationale**:
1. **Clean Separation**: Test data in separate tenant
2. **Production Safety**: No risk of test data in production
3. **Realistic Testing**: Full multi-tenant behavior
4. **Easy Cleanup**: Delete by tenant ID
5. **No Schema Pollution**: Removes is_mock from 20+ tables

## Multi-Phase Orchestration

### Flow Hierarchy Design

**Decision**: Implement parent-child flow relationships with shared state.

**Structure**:
```
Master Flow (Orchestrator)
├── State: Overall progress, phase transitions
├── Config: Global settings, preferences
└── Children: {
    discovery: UUID,
    assessment: UUID,
    planning: UUID,
    execution: UUID
}
```

**Rationale**:
1. **Centralized Control**: Single point for workflow management
2. **Phase Independence**: Each phase can run separately
3. **State Persistence**: CrewAI state maintained across phases
4. **Progress Tracking**: Unified view of all phases
5. **Extensibility**: Easy to add new phases

### Asset Lifecycle Tracking

**Decision**: Assets maintain references to all phases they've been through.

**Fields**:
- `master_flow_id`: Overall workflow reference
- `discovery_flow_id`: When asset was discovered
- `assessment_flow_id`: When asset was assessed
- `planning_flow_id`: When migration was planned
- `execution_flow_id`: When migration was executed

**Rationale**:
1. **Full History**: Complete asset journey
2. **Phase Queries**: Find assets by phase
3. **Rollback Support**: Revert to previous phase
4. **Audit Trail**: Compliance requirements
5. **Analytics**: Phase duration and success rates

## Multi-Tenancy Strategy

### Tenant Hierarchy

**Decision**: Two-level tenant hierarchy: Client Account → Engagement

**Structure**:
```
Client Account (Organization)
├── Settings & Preferences
├── User Management
└── Engagements (Projects)
    ├── Isolated Data
    ├── Specific Timeline
    └── Resource Allocation
```

**Rationale**:
1. **Business Model**: Matches consulting engagement pattern
2. **Resource Management**: Limits per engagement
3. **Access Control**: Granular permissions
4. **Billing**: Track usage per project
5. **Data Lifecycle**: Archive completed engagements

### Isolation Guarantees

**Implementation**: PostgreSQL Row-Level Security (RLS) - Immediate Priority

Based on security best practices, we're implementing RLS as part of the initial migration rather than deferring it:

```sql
-- Enable RLS on all tables
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_imports ENABLE ROW LEVEL SECURITY;

-- Create policies for multi-tenant isolation
CREATE POLICY tenant_isolation ON assets
FOR ALL TO application_role
USING (client_account_id = current_setting('app.client_id')::uuid);

-- Application sets context in middleware
SET LOCAL app.client_id = '${client_account_id}';
SET LOCAL app.engagement_id = '${engagement_id}';
```

**Application Integration**:
```python
# FastAPI middleware
async def set_tenant_context(request: Request, call_next):
    async with db.connection() as conn:
        await conn.execute(
            "SET LOCAL app.client_id = %(client_id)s",
            {"client_id": request.state.client_account_id}
        )
    return await call_next(request)
```

## Data Type Choices

### JSONB vs Normalized Tables

**Decision**: Use JSONB for flexible, nested data structures.

**Use Cases**:
1. **Settings/Preferences**: Variable schema per client
2. **AI State**: Complex CrewAI agent states
3. **Metrics/Analytics**: Evolving data points
4. **Import Mappings**: Dynamic field structures
5. **Error Details**: Structured error information

**Guidelines**:
- Use JSONB for truly variable data
- Create GIN indexes for frequently queried paths
- Validate JSON schema in application layer
- Consider extracting to columns if queried often

### Enum Types vs CHECK Constraints

**Decision**: Use CHECK constraints instead of PostgreSQL ENUMs for better flexibility.

**Implementation**:
```sql
-- Instead of CREATE TYPE ... AS ENUM
-- Use VARCHAR with CHECK constraints
CREATE TABLE assets (
    six_r_strategy VARCHAR(20) CHECK (six_r_strategy IN ('rehost', 'replatform', 'refactor', 'repurchase', 'retire', 'retain')),
    asset_type VARCHAR(20) CHECK (asset_type IN ('server', 'application', 'database', 'network', 'storage')),
    -- ...
);

-- Easy to modify
ALTER TABLE assets DROP CONSTRAINT assets_six_r_strategy_check;
ALTER TABLE assets ADD CONSTRAINT assets_six_r_strategy_check 
    CHECK (six_r_strategy IN ('rehost', 'replatform', 'refactor', 'repurchase', 'retire', 'retain', 'rewrite'));
```

**Rationale**:
1. **Flexibility**: Adding new values doesn't require type alteration
2. **Portability**: Works across all SQL databases
3. **Simplicity**: No special type management
4. **Agility**: Better for evolving AI systems that may discover new categories

**Trade-offs**:
- Slightly less storage efficient (VARCHAR vs 4-byte enum)
- No automatic type documentation in schema
- Must maintain constraints in application code too

## Performance Optimizations

### Indexing Strategy

**Decision**: Comprehensive indexing based on query patterns.

**Index Categories**:
1. **Primary Keys**: Automatic B-tree indexes
2. **Foreign Keys**: Indexed for join performance
3. **Tenant Filters**: Composite (client_id, engagement_id)
4. **Search Fields**: Single column for WHERE clauses
5. **JSONB Paths**: GIN indexes for JSON queries

**Key Indexes**:
```sql
-- Multi-tenant performance
CREATE INDEX ix_assets_client_engagement ON assets(client_account_id, engagement_id);

-- Master flow queries
CREATE INDEX ix_assets_master_flow_id ON assets(master_flow_id) WHERE master_flow_id IS NOT NULL;

-- JSON search
CREATE INDEX ix_discovery_flows_phases ON discovery_flows USING GIN (phases);
```

### Partitioning Strategy

**Decision**: Prepare for partitioning high-volume tables.

**Candidates**:
- `llm_usage_log`: Partition by month
- `agent_task_history`: Partition by week
- `security_audit_logs`: Partition by month

**Implementation** (Future):
```sql
CREATE TABLE llm_usage_log_2025_01 PARTITION OF llm_usage_log
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Query Optimization Patterns

**Decision**: Establish query patterns for optimal performance.

**Patterns**:
1. **Always filter by tenant first**
2. **Use CTEs for complex queries**
3. **Avoid SELECT * in production**
4. **Paginate large result sets**
5. **Use EXPLAIN ANALYZE in development**

## Future Considerations

### Table Inheritance for Flow Evolution

**Future Pattern**: PostgreSQL table inheritance for flow tables

As the system evolves and new flow types are added, consider migrating to table inheritance:

```sql
-- Base flow table with common columns
CREATE TABLE base_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID UNIQUE NOT NULL,
    master_flow_id UUID REFERENCES crewai_flow_state_extensions(flow_id),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    
    -- Common flow fields
    status VARCHAR(50) DEFAULT 'initialized',
    progress_percentage FLOAT DEFAULT 0.0,
    crew_ai_state JSONB DEFAULT '{}',
    current_phase VARCHAR(100),
    phases_completed JSONB DEFAULT '[]',
    
    -- Common timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Child tables inherit all base columns and add specific ones
CREATE TABLE discovery_flows_v2 (
    -- Specific to discovery
    discovery_type VARCHAR(50),
    target_platforms JSONB DEFAULT '[]',
    discovered_assets_count INTEGER DEFAULT 0
) INHERITS (base_flows);

CREATE TABLE assessment_flows_v2 (
    -- Specific to assessment
    assessment_type VARCHAR(50),
    technical_debt_score FLOAT,
    risk_score FLOAT
) INHERITS (base_flows);
```

**Benefits**:
- New flow types require no migration to existing tables
- Queries against base_flows return all flow types
- Maintains single source of truth for common fields
- Aligns database structure with conceptual hierarchy

**Implementation Timeline**: Consider after initial consolidation is stable

### Scalability Path

**Horizontal Scaling Options**:
1. **Read Replicas**: For analytics queries
2. **Sharding**: By client_account_id
3. **Citus**: Distributed PostgreSQL
4. **Time-Series DB**: For metrics data

### Schema Evolution

**Migration Strategy**:
1. **Backward Compatible**: Add columns with defaults
2. **Feature Flags**: Control rollout
3. **Blue-Green**: For breaking changes
4. **Data Migrations**: Background jobs

### AI/ML Integration

**Prepared Features**:
1. **pgvector**: Embedding storage ready
2. **JSONB**: Flexible AI model outputs
3. **Task History**: Training data collection
4. **Performance Metrics**: Model evaluation
5. **Agent Learning Patterns**: Dedicated knowledge base

**Agent Learning Patterns Table**:
```sql
CREATE TABLE agent_learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Multi-tenant context
    client_account_id UUID NOT NULL REFERENCES client_accounts(id),
    engagement_id UUID REFERENCES engagements(id),
    master_flow_id UUID REFERENCES crewai_flow_state_extensions(flow_id),
    
    -- Learning metadata
    insight_type VARCHAR(50) NOT NULL CHECK (insight_type IN (
        'field_mapping_suggestion',
        'risk_pattern',
        'optimization_opportunity',
        'anomaly_detection',
        'workflow_improvement'
    )),
    
    -- AI content
    embedding vector(1536) NOT NULL,  -- For similarity search
    raw_evidence JSONB NOT NULL,      -- Original data/context
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Tracking
    discovered_by VARCHAR(100),       -- Which agent found this
    validated BOOLEAN DEFAULT false,
    applied_count INTEGER DEFAULT 0,  -- Times this pattern was used
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_applied_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for vector similarity
    INDEX ix_learning_embedding USING ivfflat (embedding vector_cosine_ops)
);
```

This enables agents to:
- Store discovered patterns with embeddings
- Query similar past experiences
- Build organizational knowledge over time
- Learn from successful migrations

### Compliance & Security

**Future Enhancements**:
1. **Encryption at Rest**: Transparent data encryption
2. **Audit Triggers**: Automatic change tracking
3. **Data Retention**: Automated archival
4. **GDPR Tools**: Right to be forgotten

## Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|---------|
| 2024-Q4 | Initial schema design | MVP launch | High |
| 2025-01 | V3 table consolidation | Reduce complexity | High |
| 2025-01 | Remove is_mock fields | Multi-tenant testing | Medium |
| 2025-01 | Add master_flow_id | Phase orchestration | High |
| 2025-02 | (Planned) Add RLS policies | Security hardening | High |

## Lessons Learned

### What Worked Well
1. **UUID Strategy**: No ID conflicts in distributed system
2. **JSONB Flexibility**: Adapted to changing requirements
3. **Schema Isolation**: Clean separation from other apps
4. **Enum Types**: Clear valid values, good performance

### Challenges Faced
1. **V3 Table Proliferation**: Parallel systems confusion
2. **Boolean State Flags**: Inflexible for complex workflows  
3. **Nullable Foreign Keys**: Complexity in joins
4. **Large JSON Fields**: Performance impact

### Recommendations
1. **Start with Master Flow**: Don't add orchestration later
2. **Plan for Multi-Tenancy**: Add tenant fields from day one
3. **Document Decisions**: This file should exist from start
4. **Test at Scale**: Performance test with realistic data
5. **Version Everything**: Including stored procedures

---

*Database Architecture Decisions for AI Modernize Migration Platform - January 2025*