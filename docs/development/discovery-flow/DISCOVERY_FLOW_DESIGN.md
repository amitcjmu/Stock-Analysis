# Discovery Flow Design Document

## Executive Summary

The Discovery Flow is the foundational CrewAI flow in the AI Modernize Migration Platform, designed to solve the critical challenge of creating an accurate, comprehensive IT asset inventory from disparate, often conflicting data sources. It employs intelligent agents to consolidate information from CMDBs, assessment tools, monitoring systems, and documentation into a unified view of applications, servers, and their dependencies.

This flow operates on a continuous refinement model where each data import enhances existing asset records rather than creating discrete sessions. The system prioritizes agent-driven intelligence with human-in-the-loop validation, ensuring accuracy while minimizing manual effort.

## Business Context and Problem Statement

### Current Enterprise Challenges
- **Fragmented Data Sources**: Infrastructure split between on-premise and cloud, managed by multiple vendors
- **Inaccurate CMDBs**: Less than 50% accuracy, outdated since initial setup years ago
- **Varying Maturity Levels**: Advanced DevOps coexists with legacy systems lacking observability
- **Tool Limitations**: Assessment tools (Dr.Migrate, Cloudamize) require extended network access and miss orphaned resources
- **Siloed Monitoring**: Enterprise tools (DataDog, AppScan) cover specific applications only
- **No Holistic View**: Missing consolidated view of applications, dependencies, and infrastructure

### Solution Approach
Create an intelligent data integration system that:
- Ingests data from all available sources (CMDB dumps, scan reports, monitoring data, documentation)
- Reconciles conflicting information using confidence scoring and pattern recognition
- Builds comprehensive application inventory with dependency mapping
- Provides continuous refinement capabilities
- Prepares assets for downstream assessment and planning flows

## Core Design Principles

### 1. Agent-First Architecture
- **True CrewAI Agents**: Not pseudo-agents or simple automation
- **Pattern Learning**: Agents identify and learn from data patterns globally and locally
- **Intelligent Reconciliation**: Confidence-based conflict resolution
- **Anomaly Detection**: Proactive identification of data quality issues

### 2. Continuous Refinement Model
- **Not Session-Based**: Each import refines existing records
- **Iterative Enhancement**: Data quality improves over time
- **Raw Data Preservation**: All original data retained for reference
- **No Rollback Complexity**: Current state + raw data model

### 3. Human-in-the-Loop Validation
- **Configurable Autonomy**: Users control agent decision-making levels
- **Confidence Thresholds**: 70%+ for automatic actions
- **Override Capability**: Users can always override agent recommendations
- **Audit Trail**: All human decisions tracked for learning

### 4. Flexible Authority Model
- **Authoritative Sources**: Designate trusted sources for specific attributes
- **Newer Wins Default**: Recent data typically overrides older data
- **Anomaly Alerts**: System flags suspicious overwrites
- **User Ownership**: Users own final decisions

## Functional Requirements

### Data Ingestion Capabilities

#### Supported Data Sources
1. **CMDB Exports**
   - CSV, XML, JSON formats
   - Custom field mapping support
   - Bulk upload with size restrictions (configurable)

2. **Assessment Tool Reports**
   - CloudAmize exports
   - Dr.Migrate scan results
   - Custom assessment tool outputs

3. **Monitoring System Data**
   - DataDog metrics and topology
   - AppScan application insights
   - APM tool exports

4. **Documentation**
   - Application guides (PDF, Word)
   - Architecture diagrams
   - Runbooks and operational docs

#### Ingestion Process
1. **Security Scanning**
   - Malware detection
   - Sensitive data identification
   - File format validation

2. **Size Management**
   - Initial restrictions (configurable)
   - Batch processing for large files
   - Progress tracking and estimation

3. **Error Handling**
   - Partial import support
   - User choice on failed records
   - Detailed error reporting

### Field Mapping Intelligence

#### Mapping Process
1. **Initial Mapping**
   - User-guided field alignment
   - Visual mapping interface
   - Preview of mapped data

2. **Pattern Learning**
   - Global pattern repository (default)
   - Engagement-specific learning (opt-in)
   - Industry-specific patterns

3. **Auto-Mapping**
   - Confidence-based suggestions
   - 70%+ threshold for auto-accept
   - User review interface

#### Critical Attributes for Migration
- Application identification (name, ID, aliases)
- Infrastructure details (hostname, IP, specs)
- Technology stack (languages, frameworks, versions)
- Ownership (department, contact, criticality)
- Operational details (environment, SLA, compliance)
- Dependencies (upstream, downstream, integration points)

### Data Reconciliation Engine

#### Confidence Scoring Model
```python
confidence_factors = {
    "data_recency": 0.3,        # Newer data weighted higher
    "source_reliability": 0.3,   # User-configured per source
    "pattern_consistency": 0.2,  # Matches known patterns
    "data_completeness": 0.2     # Percentage of fields populated
}
```

#### Conflict Resolution
1. **Automatic Resolution** (confidence > 70%)
   - Apply highest confidence value
   - Log decision rationale
   - Flag for optional review

2. **Manual Resolution** (confidence < 70%)
   - Present all options to user
   - Show confidence scores
   - Allow custom input

3. **Anomaly Detection**
   - Flag suspicious overwrites
   - Identify data quality drops
   - Alert on breaking changes

### Asset Inventory Management

#### Supported Asset Types
1. **Applications**
   - Business applications
   - Technical services
   - Middleware components
   - Custom/COTS designation

2. **Infrastructure**
   - Physical servers
   - Virtual machines
   - Containers and hosts
   - Network devices
   - Storage systems

3. **Relationships**
   - One-to-many (shared hosting)
   - Many-to-one (clustering)
   - Multi-tier architectures
   - Container orchestration

#### Asset States
- **Active**: Currently operational
- **Migrated**: Already moved to cloud
- **Retired**: Decommissioned
- **Planned**: Future state
- **Unknown**: Insufficient data

### Dependency Discovery

#### Discovery Depth Levels
1. **Level 1 - Direct Dependencies**
   - Immediate connections
   - API integrations
   - Database connections

2. **Level 2 - Transitive Dependencies**
   - Second-degree relationships
   - Shared service dependencies
   - Infrastructure dependencies

3. **Level 3+ - Deep Analysis**
   - Full dependency chains
   - Circular dependency detection
   - Critical path analysis

#### Dependency Types
- **Runtime**: Application calls, API dependencies
- **Data**: Database connections, file shares
- **Infrastructure**: Shared load balancers, networks
- **Temporal**: Startup sequences, batch dependencies

#### Dependency Attributes
- **Coupling Strength**: Tight, loose, optional
- **Criticality**: Required, recommended, optional
- **Latency Sensitivity**: Real-time, near-time, batch
- **Data Volume**: High, medium, low

### Readiness Assessment

#### Readiness Scoring Algorithm
```python
readiness_components = {
    "critical_attributes_complete": 0.4,
    "dependency_mapping_complete": 0.3,
    "ownership_defined": 0.2,
    "technical_details_available": 0.1
}
```

#### Readiness Indicators
- **Green (80%+)**: Ready for assessment
- **Yellow (60-79%)**: May need additional data
- **Red (<60%)**: Insufficient data for accurate assessment

### Agent Intelligence Capabilities

#### Pattern Recognition
1. **Naming Conventions**
   - Environment indicators (PROD, DEV, TEST)
   - Application groupings
   - Version patterns

2. **Technology Patterns**
   - Common stack combinations
   - Framework indicators
   - Platform associations

3. **Organizational Patterns**
   - Department prefixes
   - Cost center mappings
   - Team ownership

4. **Infrastructure Patterns**
   - Cluster configurations
   - Network segments
   - Shared services

#### Anomaly Detection
- Orphaned servers with no application
- Circular dependency loops
- Duplicate applications
- Inconsistent naming
- Missing critical attributes
- Unusual technology combinations

## Technical Architecture

### CrewAI Flow Implementation

```python
class UnifiedDiscoveryFlow(Flow[DiscoveryFlowState]):
    """
    Main discovery flow orchestrating multi-source data ingestion,
    intelligent reconciliation, and inventory building.
    """
    
    def __init__(self, crewai_service: CrewAIService, context: FlowContext):
        super().__init__()
        self.crewai_service = crewai_service
        self.context = context
        self.state_manager = FlowStateManager(context.flow_id)
        self.postgres_store = PostgresStore(context.flow_id)
    
    @start()
    def initialize_discovery(self):
        """Initialize discovery flow with engagement context"""
        
    @listen(initialize_discovery)
    def ingest_data_sources(self, init_result):
        """Process uploaded data files with security scanning"""
        
    @listen(ingest_data_sources)
    def map_fields_intelligently(self, ingestion_result):
        """Apply intelligent field mapping with pattern learning"""
        
    @listen(map_fields_intelligently)
    def reconcile_conflicts(self, mapping_result):
        """Resolve data conflicts using confidence scoring"""
        
    @listen(reconcile_conflicts)
    def discover_applications(self, reconciliation_result):
        """Identify and consolidate applications from assets"""
        
    @listen(discover_applications)
    def map_dependencies(self, discovery_result):
        """Discover and map application dependencies"""
        
    @listen(map_dependencies)
    def assess_readiness(self, dependency_result):
        """Calculate readiness scores for assessment flow"""
```

### CrewAI Crews and Agents

#### 1. Data Ingestion Crew
```python
class DataIngestionCrew:
    """Handles multi-source data ingestion with security validation"""
    
    agents = [
        {
            "role": "Security Scanner Agent",
            "goal": "Detect malware and sensitive data in uploads",
            "backstory": "Expert in file security analysis and data protection"
        },
        {
            "role": "Format Parser Agent", 
            "goal": "Parse various file formats and extract structured data",
            "backstory": "Specialist in data formats and extraction techniques"
        },
        {
            "role": "Data Quality Assessor",
            "goal": "Evaluate data quality and completeness",
            "backstory": "Expert in data quality metrics and validation"
        }
    ]
    
    tasks = [
        "Scan uploaded files for security threats",
        "Extract data from various formats (CSV, JSON, XML, PDF)",
        "Assess data quality and report issues",
        "Prepare data for field mapping phase",
        "Track ingestion metrics and errors"
    ]
```

#### 2. Field Mapping Intelligence Crew
```python
class FieldMappingCrew:
    """Provides intelligent field mapping with pattern learning"""
    
    agents = [
        {
            "role": "Pattern Recognition Agent",
            "goal": "Identify field naming patterns across sources",
            "backstory": "Machine learning expert in pattern identification"
        },
        {
            "role": "Mapping Recommendation Agent",
            "goal": "Suggest optimal field mappings based on patterns",
            "backstory": "Expert in data integration and schema matching"
        },
        {
            "role": "Learning Optimization Agent",
            "goal": "Continuously improve mapping accuracy through feedback",
            "backstory": "Specialist in reinforcement learning and optimization"
        }
    ]
    
    tasks = [
        "Analyze field names and data patterns",
        "Match source fields to standard attributes",
        "Calculate confidence scores for mappings",
        "Learn from user corrections and feedback",
        "Build reusable mapping templates"
    ]
```

#### 3. Data Reconciliation Crew
```python
class DataReconciliationCrew:
    """Resolves conflicts between data sources intelligently"""
    
    agents = [
        {
            "role": "Conflict Detection Agent",
            "goal": "Identify conflicting data across sources",
            "backstory": "Expert in data anomaly detection and analysis"
        },
        {
            "role": "Authority Resolution Agent",
            "goal": "Apply authoritative source rules and confidence scoring",
            "backstory": "Specialist in data governance and quality"
        },
        {
            "role": "Anomaly Alert Agent",
            "goal": "Flag suspicious data changes for user review",
            "backstory": "Expert in identifying data quality issues"
        }
    ]
    
    tasks = [
        "Compare data values across sources",
        "Calculate confidence scores for each value",
        "Apply authoritative source preferences",
        "Flag anomalies and quality degradation",
        "Generate reconciliation recommendations"
    ]
```

#### 4. Application Discovery Crew
```python
class ApplicationDiscoveryCrew:
    """Identifies applications from infrastructure assets"""
    
    agents = [
        {
            "role": "Application Pattern Agent",
            "goal": "Recognize application patterns in asset data",
            "backstory": "Expert in application architectures and patterns"
        },
        {
            "role": "Component Grouping Agent",
            "goal": "Group related assets into logical applications",
            "backstory": "Specialist in system architecture and design"
        },
        {
            "role": "Metadata Enrichment Agent",
            "goal": "Enhance application data with additional context",
            "backstory": "Expert in metadata management and enrichment"
        }
    ]
    
    tasks = [
        "Identify application patterns in naming and configuration",
        "Group servers and components by application",
        "Detect multi-tier application architectures",
        "Identify shared services and platforms",
        "Enrich applications with business context"
    ]
```

#### 5. Dependency Mapping Crew
```python
class DependencyMappingCrew:
    """Discovers and maps dependencies between applications"""
    
    agents = [
        {
            "role": "Connection Discovery Agent",
            "goal": "Identify connections between applications and services",
            "backstory": "Network and integration specialist"
        },
        {
            "role": "Dependency Classification Agent",
            "goal": "Classify dependency types and characteristics",
            "backstory": "Expert in system integration patterns"
        },
        {
            "role": "Impact Analysis Agent",
            "goal": "Analyze dependency impact and criticality",
            "backstory": "Specialist in risk and impact assessment"
        }
    ]
    
    tasks = [
        "Discover runtime dependencies from connection data",
        "Identify data dependencies from database connections",
        "Map infrastructure dependencies",
        "Classify dependency strength and criticality",
        "Detect circular dependencies and anomalies"
    ]
```

### Data Models

#### DiscoveryFlowState
```python
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class DataSourceType(str, Enum):
    CMDB = "cmdb"
    ASSESSMENT_TOOL = "assessment_tool"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"
    MANUAL = "manual"

class ConfidenceLevel(str, Enum):
    HIGH = "high"          # 80-100%
    MEDIUM = "medium"      # 60-79%
    LOW = "low"           # 40-59%
    INSUFFICIENT = "insufficient"  # <40%

class AssetState(str, Enum):
    ACTIVE = "active"
    MIGRATED = "migrated"
    RETIRED = "retired"
    PLANNED = "planned"
    UNKNOWN = "unknown"

class DiscoveryFlowState(BaseModel):
    flow_id: str
    client_account_id: int
    engagement_id: int
    
    # Data sources tracking
    data_sources: List[Dict[str, Any]]  # Source metadata
    ingestion_history: List[Dict[str, Any]]  # Import records
    
    # Field mapping state
    field_mappings: Dict[str, Dict[str, Any]]  # Source -> standard mappings
    mapping_patterns: List[Dict[str, Any]]  # Learned patterns
    mapping_confidence: Dict[str, float]  # Confidence per mapping
    
    # Asset inventory
    raw_assets: Dict[str, Any]  # Original data preserved
    assets: Dict[str, Any]  # Current curated state
    asset_confidence: Dict[str, Dict[str, float]]  # Per-attribute confidence
    
    # Application discovery
    applications: Dict[str, Any]
    application_components: Dict[str, List[str]]  # App -> asset mapping
    
    # Dependency mapping
    dependencies: List[Dict[str, Any]]
    dependency_depth: int  # Current analysis depth
    
    # Readiness assessment
    readiness_scores: Dict[str, float]
    critical_attributes: List[str]
    assessment_ready_apps: List[str]
    
    # Authority configuration
    authoritative_sources: Dict[str, str]  # Attribute -> source
    source_reliability: Dict[str, float]  # Source -> reliability score
    
    # User preferences
    agent_autonomy_level: str  # "high", "medium", "low"
    auto_resolve_threshold: float  # Default 0.7
    global_learning_enabled: bool  # Default True
    
    # Flow metadata
    status: str
    progress: int
    current_phase: str
    phase_results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
```

### Database Schema

```sql
-- Main discovery flow tracking
CREATE TABLE discovery_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    progress INTEGER DEFAULT 0,
    current_phase VARCHAR(100),
    agent_autonomy_level VARCHAR(20) DEFAULT 'medium',
    auto_resolve_threshold FLOAT DEFAULT 0.7,
    global_learning_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_client_account FOREIGN KEY (client_account_id) 
        REFERENCES client_accounts(id) ON DELETE CASCADE,
    CONSTRAINT fk_engagement FOREIGN KEY (engagement_id) 
        REFERENCES engagements(id) ON DELETE CASCADE
);

-- Data source tracking
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255),
    file_size BIGINT,
    upload_user_id INTEGER,
    reliability_score FLOAT DEFAULT 0.5,
    is_authoritative_for JSONB,  -- List of attributes
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE
);

-- Raw data preservation
CREATE TABLE raw_data_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    data_source_id UUID NOT NULL,
    record_type VARCHAR(50),  -- 'application', 'server', 'device'
    raw_data JSONB NOT NULL,
    import_timestamp TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE,
    CONSTRAINT fk_data_source FOREIGN KEY (data_source_id) 
        REFERENCES data_sources(id) ON DELETE CASCADE
);

-- Field mapping configurations
CREATE TABLE field_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    data_source_id UUID NOT NULL,
    source_field VARCHAR(255) NOT NULL,
    target_attribute VARCHAR(255) NOT NULL,
    mapping_confidence FLOAT NOT NULL,
    is_auto_mapped BOOLEAN DEFAULT FALSE,
    user_override BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE,
    CONSTRAINT fk_data_source FOREIGN KEY (data_source_id) 
        REFERENCES data_sources(id) ON DELETE CASCADE
);

-- Learned mapping patterns (global knowledge base)
CREATE TABLE mapping_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_key VARCHAR(255) NOT NULL,  -- Hash of source characteristics
    source_field_pattern VARCHAR(255),
    target_attribute VARCHAR(255),
    confidence_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(pattern_key)
);

-- Main asset inventory
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    asset_type VARCHAR(50) NOT NULL,  -- 'application', 'server', 'device'
    asset_identifier VARCHAR(255) NOT NULL,  -- Primary identifier
    asset_name VARCHAR(255),
    asset_state VARCHAR(50) DEFAULT 'active',
    
    -- Core attributes (curated current state)
    attributes JSONB NOT NULL DEFAULT '{}',
    
    -- Confidence tracking per attribute
    attribute_confidence JSONB DEFAULT '{}',
    
    -- Source tracking per attribute
    attribute_sources JSONB DEFAULT '{}',
    
    -- Metadata
    readiness_score FLOAT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE,
    UNIQUE(discovery_flow_id, asset_type, asset_identifier)
);

-- Application groupings
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    application_name VARCHAR(255) NOT NULL,
    business_unit VARCHAR(255),
    technical_owner VARCHAR(255),
    business_owner VARCHAR(255),
    criticality VARCHAR(50),
    environment VARCHAR(50),
    
    -- Application metadata
    metadata JSONB DEFAULT '{}',
    
    -- Readiness for assessment
    ready_for_assessment BOOLEAN DEFAULT FALSE,
    readiness_score FLOAT,
    missing_critical_attributes JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE
);

-- Application to asset mapping
CREATE TABLE application_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL,
    asset_id UUID NOT NULL,
    relationship_type VARCHAR(50),  -- 'hosts', 'uses', 'depends_on'
    relationship_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_application FOREIGN KEY (application_id) 
        REFERENCES applications(id) ON DELETE CASCADE,
    CONSTRAINT fk_asset FOREIGN KEY (asset_id) 
        REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE(application_id, asset_id, relationship_type)
);

-- Dependencies between assets/applications
CREATE TABLE dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'application' or 'asset'
    source_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    dependency_type VARCHAR(50) NOT NULL,  -- 'runtime', 'data', 'infrastructure', 'temporal'
    
    -- Dependency characteristics
    coupling_strength VARCHAR(20),  -- 'tight', 'loose', 'optional'
    criticality VARCHAR(20),  -- 'required', 'recommended', 'optional'
    latency_sensitivity VARCHAR(20),  -- 'real-time', 'near-time', 'batch'
    data_volume VARCHAR(20),  -- 'high', 'medium', 'low'
    
    -- Discovery metadata
    discovery_method VARCHAR(50),  -- How it was discovered
    confidence_score FLOAT,
    verified_by_user BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE
);

-- Conflict resolution history
CREATE TABLE data_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    asset_id UUID NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    conflicting_values JSONB NOT NULL,  -- Array of {value, source, confidence}
    resolution_method VARCHAR(50),  -- 'auto', 'manual', 'anomaly_flag'
    selected_value TEXT,
    selected_source UUID,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE,
    CONSTRAINT fk_asset FOREIGN KEY (asset_id) 
        REFERENCES assets(id) ON DELETE CASCADE
);

-- Agent insights and learning
CREATE TABLE discovery_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    insight_type VARCHAR(50) NOT NULL,  -- 'pattern', 'anomaly', 'recommendation'
    agent_name VARCHAR(100) NOT NULL,
    insight_data JSONB NOT NULL,
    confidence_score FLOAT,
    user_feedback VARCHAR(20),  -- 'accepted', 'rejected', 'modified'
    feedback_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE
);

-- Audit trail
CREATE TABLE discovery_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID NOT NULL,
    user_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    action_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_discovery_flow FOREIGN KEY (discovery_flow_id) 
        REFERENCES discovery_flows(id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX idx_discovery_flows_client ON discovery_flows(client_account_id, engagement_id);
CREATE INDEX idx_assets_readiness ON assets(discovery_flow_id, readiness_score);
CREATE INDEX idx_applications_ready ON applications(discovery_flow_id, ready_for_assessment);
CREATE INDEX idx_dependencies_source ON dependencies(source_type, source_id);
CREATE INDEX idx_dependencies_target ON dependencies(target_type, target_id);
CREATE INDEX idx_conflicts_unresolved ON data_conflicts(discovery_flow_id) WHERE resolved_at IS NULL;

-- JSONB indexes for performance
CREATE INDEX idx_assets_attributes_gin ON assets USING GIN(attributes);
CREATE INDEX idx_assets_confidence_gin ON assets USING GIN(attribute_confidence);
```

## API Endpoints

### Discovery Flow Management

```yaml
# Initialize Discovery Flow
POST /api/v1/discovery-flow/initialize
Request:
  {
    "engagement_config": {
      "max_applications": 500,
      "max_servers": 5000,
      "agent_autonomy_level": "medium",
      "auto_resolve_threshold": 0.7,
      "global_learning_enabled": true
    }
  }
Response:
  {
    "flow_id": "uuid",
    "status": "initialized",
    "current_phase": "awaiting_data"
  }

# Get Flow Status
GET /api/v1/discovery-flow/{flow_id}/status
Response:
  {
    "flow_id": "uuid",
    "status": "processing",
    "progress": 45,
    "current_phase": "field_mapping",
    "stats": {
      "total_assets": 1250,
      "applications_discovered": 45,
      "dependencies_mapped": 156,
      "conflicts_pending": 23
    }
  }
```

### Data Ingestion

```yaml
# Upload Data Source
POST /api/v1/discovery-flow/{flow_id}/upload
Headers:
  Content-Type: multipart/form-data
Form Data:
  file: <file>
  source_type: "cmdb"
  source_name: "ServiceNow CMDB Export"
  reliability_score: 0.8
Response:
  {
    "data_source_id": "uuid",
    "status": "scanning",
    "estimated_processing_time": "15 minutes"
  }

# Get Upload Status
GET /api/v1/discovery-flow/{flow_id}/upload/{source_id}/status
Response:
  {
    "status": "completed",
    "records_processed": 5000,
    "records_failed": 12,
    "security_scan": "passed",
    "ready_for_mapping": true
  }
```

### Field Mapping

```yaml
# Get Mapping Suggestions
GET /api/v1/discovery-flow/{flow_id}/mappings/suggestions/{source_id}
Response:
  {
    "mappings": [
      {
        "source_field": "ServerName",
        "suggested_target": "hostname",
        "confidence": 0.95,
        "based_on_pattern": true
      },
      {
        "source_field": "AppID",
        "suggested_target": "application_id",
        "confidence": 0.82,
        "based_on_pattern": true
      }
    ],
    "unmapped_fields": ["CustomField1", "LegacyCode"]
  }

# Save Field Mappings
POST /api/v1/discovery-flow/{flow_id}/mappings/{source_id}
Request:
  {
    "mappings": [
      {
        "source_field": "ServerName",
        "target_attribute": "hostname",
        "accept_suggestion": true
      },
      {
        "source_field": "AppID",
        "target_attribute": "application_identifier",
        "accept_suggestion": false
      }
    ]
  }
```

### Conflict Resolution

```yaml
# Get Pending Conflicts
GET /api/v1/discovery-flow/{flow_id}/conflicts?status=pending
Response:
  {
    "conflicts": [
      {
        "conflict_id": "uuid",
        "asset_id": "uuid",
        "asset_name": "CRM-PROD-01",
        "attribute": "memory_gb",
        "values": [
          {"value": "16", "source": "CMDB", "confidence": 0.6},
          {"value": "32", "source": "CloudAmize", "confidence": 0.9}
        ],
        "recommendation": {
          "value": "32",
          "reason": "CloudAmize scan is more recent and reliable"
        }
      }
    ]
  }

# Resolve Conflicts
POST /api/v1/discovery-flow/{flow_id}/conflicts/resolve
Request:
  {
    "resolutions": [
      {
        "conflict_id": "uuid",
        "selected_value": "32",
        "selected_source": "CloudAmize",
        "notes": "Confirmed with infrastructure team"
      }
    ]
  }
```

### Asset Management

```yaml
# Get Asset Inventory
GET /api/v1/discovery-flow/{flow_id}/assets?type=application&ready_for_assessment=true
Response:
  {
    "assets": [
      {
        "asset_id": "uuid",
        "asset_name": "Customer Portal",
        "readiness_score": 0.85,
        "missing_attributes": [],
        "components": ["web-server-01", "app-server-01", "db-server-01"],
        "dependencies": 5
      }
    ],
    "total": 45,
    "ready_count": 38
  }

# Update Asset
PUT /api/v1/discovery-flow/{flow_id}/assets/{asset_id}
Request:
  {
    "updates": {
      "business_owner": "John Smith",
      "criticality": "high",
      "notes": "Manually verified with application team"
    }
  }

# Add Manual Asset
POST /api/v1/discovery-flow/{flow_id}/assets
Request:
  {
    "asset_type": "application",
    "asset_name": "Legacy Billing System",
    "attributes": {
      "technology_stack": ["COBOL", "DB2"],
      "environment": "production",
      "business_unit": "Finance"
    }
  }
```

### Dependency Management

```yaml
# Get Dependency Map
GET /api/v1/discovery-flow/{flow_id}/dependencies?source_id={app_id}&depth=2
Response:
  {
    "dependencies": [
      {
        "source": {"id": "uuid", "name": "Customer Portal"},
        "target": {"id": "uuid", "name": "Payment Service"},
        "type": "runtime",
        "characteristics": {
          "coupling": "loose",
          "criticality": "required",
          "latency": "real-time"
        }
      }
    ],
    "total_dependencies": 12
  }

# Add Manual Dependency
POST /api/v1/discovery-flow/{flow_id}/dependencies
Request:
  {
    "source_id": "uuid",
    "source_type": "application",
    "target_id": "uuid", 
    "target_type": "application",
    "dependency_type": "data",
    "characteristics": {
      "coupling": "tight",
      "criticality": "required"
    },
    "notes": "Shares customer database"
  }
```

### Readiness Assessment

```yaml
# Get Readiness Report
GET /api/v1/discovery-flow/{flow_id}/readiness
Response:
  {
    "summary": {
      "total_applications": 145,
      "ready_for_assessment": 125,
      "needs_more_data": 15,
      "insufficient_data": 5
    },
    "by_readiness_score": {
      "high": 125,    # 80%+
      "medium": 15,   # 60-79%
      "low": 5        # <60%
    },
    "missing_critical_attributes": {
      "business_owner": 8,
      "technology_stack": 3,
      "dependencies": 12
    }
  }

# Mark Applications Ready
POST /api/v1/discovery-flow/{flow_id}/mark-ready
Request:
  {
    "application_ids": ["uuid1", "uuid2", "uuid3"],
    "override_readiness": true,
    "reason": "Proceeding with available data"
  }
```

## Frontend Integration

### Key UI Components

1. **Data Upload Wizard**
   - Drag-and-drop file upload
   - Source type selection
   - Reliability score configuration
   - Progress tracking with time estimates

2. **Field Mapping Interface**
   - Split-screen source/target view
   - Auto-mapping suggestions with confidence
   - Bulk accept/reject capabilities
   - Pattern learning feedback

3. **Conflict Resolution Dashboard**
   - Conflict queue with filters
   - Side-by-side value comparison
   - Bulk resolution tools
   - Anomaly highlighting

4. **Asset Inventory Browser**
   - Filterable/sortable grid
   - Readiness score indicators
   - Quick edit capabilities
   - Bulk selection tools

5. **Dependency Visualizer**
   - Interactive network diagram
   - Depth control (1-3 levels)
   - Relationship details on hover
   - Manual connection drawing

6. **Readiness Dashboard**
   - Summary statistics
   - Readiness distribution charts
   - Missing attribute analysis
   - Application selection for assessment

### Navigation Structure
```
/discovery/
├── upload/              # Data source upload
├── field-mapping/       # Field mapping configuration
├── conflicts/          # Conflict resolution
├── inventory/          # Asset inventory browser
│   ├── applications/   # Application view
│   ├── infrastructure/ # Server/device view
│   └── components/     # Component view
├── dependencies/       # Dependency mapping
├── readiness/         # Assessment readiness
└── insights/          # Agent insights and patterns
```

## Integration Points

### With Assessment Flow
- Exposes full asset inventory via async DB
- Applications marked "ready_for_assessment" are available
- Provides readiness scores and missing attribute lists
- Supplies dependency maps for assessment analysis

### With Planning Flow
- Continuous updates to asset inventory
- New discoveries don't affect finalized plans
- Planning can query latest dependency information
- Supports re-assessment requests for specific apps

### With Other Systems
- Event-driven updates for inventory changes
- API access for external system queries
- Webhook notifications for major discoveries
- Export capabilities for reporting

## Performance Considerations

### Scalability Limits
- 500 applications per engagement (initial)
- 5,000 servers/devices per engagement (initial)
- 10MB file upload limit (configurable)
- 100 concurrent users per engagement

### Processing Strategies
- Batch processing for large imports
- Async agent processing with progress tracking
- Incremental dependency discovery
- Cached pattern matching for performance

### Data Retention
- Raw data retained indefinitely
- Audit logs retained per compliance requirements
- Pattern learning data aggregated monthly
- Conflict history retained for analysis

## Security and Compliance

### Data Security
- File scanning for malware
- Sensitive data detection and masking
- Encryption at rest and in transit
- Secure file storage with access controls

### Access Control
- RBAC with Analyst/Manager write permissions
- Read-only access for other roles
- Engagement-level data isolation
- Audit trail for all modifications

### Compliance Features
- Complete audit logging
- Data lineage tracking
- User consent for global learning
- Right to deletion support

## Success Metrics

### Operational Metrics
- Average time to first discovery: < 2 hours
- Auto-mapping accuracy: > 85%
- Conflict resolution time: < 5 minutes per conflict
- Readiness score accuracy: > 90%

### Quality Metrics
- Data completeness: > 80% of critical attributes
- Dependency discovery coverage: > 90%
- False positive rate: < 10%
- User override rate: < 15%

### Business Metrics
- Time to assessment readiness: 50% reduction
- Manual effort reduction: 70%
- Data quality improvement: 2x
- Discovery cycle time: 75% reduction

## Risk Mitigation

### Technical Risks
1. **Large Data Volumes**
   - Mitigation: Batch processing, size limits, async operations

2. **Poor Data Quality**
   - Mitigation: Multi-source reconciliation, confidence scoring

3. **Pattern Learning Accuracy**
   - Mitigation: Human validation, confidence thresholds

### Business Risks
1. **Incomplete Discovery**
   - Mitigation: Readiness scoring, user overrides

2. **Incorrect Mappings**
   - Mitigation: Review UI, audit trail, rollback capability

3. **Privacy Concerns**
   - Mitigation: Opt-out for global learning, data masking

## Future Enhancements

### Phase 2
- Real-time discovery agent deployment
- Network scanning capabilities
- API-based CMDB integration
- Advanced ML for pattern recognition

### Phase 3
- Code repository analysis
- Documentation parsing with NLP
- Automated dependency validation
- Predictive readiness scoring

## Appendix

### Critical Attributes List
1. **Application Identity**
   - Application name
   - Application ID/code
   - Aliases/alternate names

2. **Ownership**
   - Business owner
   - Technical owner
   - Support contact
   - Business unit

3. **Technology**
   - Programming languages
   - Frameworks and versions
   - Database platforms
   - Operating systems

4. **Infrastructure**
   - Server hostnames
   - IP addresses
   - CPU/memory specs
   - Storage details

5. **Operations**
   - Environment (prod/dev/test)
   - Criticality rating
   - SLA requirements
   - Compliance needs

6. **Integration**
   - API endpoints
   - Data sources
   - External dependencies
   - Integration methods

### Confidence Scoring Formula
```python
def calculate_confidence(data_point, context):
    base_score = 0.0
    
    # Factor 1: Data recency (30%)
    age_days = (datetime.now() - data_point.timestamp).days
    recency_score = max(0, 1 - (age_days / 365)) * 0.3
    
    # Factor 2: Source reliability (30%)
    source_score = context.source_reliability.get(
        data_point.source, 0.5) * 0.3
    
    # Factor 3: Pattern match (20%)
    pattern_score = pattern_matcher.score(data_point) * 0.2
    
    # Factor 4: Data completeness (20%)
    completeness = len(data_point.attributes) / len(required_attributes)
    completeness_score = min(1, completeness) * 0.2
    
    return base_score + recency_score + source_score + 
           pattern_score + completeness_score
```

### Sample Field Mapping Patterns
```json
{
  "common_patterns": [
    {
      "source_patterns": ["hostname", "host_name", "server_name", "computer_name"],
      "target_attribute": "hostname",
      "confidence": 0.95
    },
    {
      "source_patterns": ["app_id", "application_id", "app_code", "appl_id"],
      "target_attribute": "application_id",
      "confidence": 0.90
    },
    {
      "source_patterns": ["ip_address", "ip_addr", "ip", "network_address"],
      "target_attribute": "ip_address",
      "confidence": 0.95
    }
  ]
}
```