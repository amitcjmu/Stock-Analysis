# Assessment Flow - Database & Foundation Tasks

## Overview
This document tracks all database schema, migrations, and foundational infrastructure tasks for the Assessment Flow implementation based on the comprehensive design analysis.

## Key Implementation Context
- **PostgreSQL-only persistence** following Discovery Flow patterns
- **Component-level 6R treatments** with flexible architecture support
- **Architecture minimums** with engagement-level standards and app overrides
- **Multi-tenant data model** with proper RBAC and isolation
- **State recovery** and pause/resume capabilities throughout

---

## 🗄️ Database Schema Tasks

### DB-001: Create Assessment Flow Core Schema Migration
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 14 hours  
**Dependencies**: None  
**Sprint**: Foundation Week 1-2  

**Description**: Create comprehensive Alembic migration for PostgreSQL-only assessment flow tables with enhanced architecture minimums support

**Location**: `backend/app/alembic/versions/xxx_add_assessment_flow_tables.py`

**Technical Requirements**:
- PostgreSQL-only approach (no SQLite compatibility) - learned from Remediation Phase 1
- UUID primary keys following platform patterns  
- Multi-tenant constraints on all tables
- JSONB fields for complex state data with GIN indexes
- Proper foreign key constraints with CASCADE cleanup
- Performance optimization for flow navigation and component queries

**Core Tables Required**:
1. **assessment_flows** - Main flow tracking with pause points and navigation state
2. **engagement_architecture_standards** - Engagement-level minimums with version requirements
3. **application_architecture_overrides** - App-specific exceptions with business rationale
4. **application_components** - Flexible component discovery beyond 3-tier architecture
5. **tech_debt_analysis** - Component-level tech debt with severity and remediation tracking
6. **component_treatments** - Individual component 6R decisions with compatibility validation
7. **sixr_decisions** - Application-level rollup with app_on_page_data consolidation
8. **assessment_learning_feedback** - Agent learning from user modifications and overrides

**Detailed Schema Requirements**:

```sql
-- Main flow tracking with pause/resume support
CREATE TABLE assessment_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    selected_application_ids JSONB NOT NULL,
    architecture_captured BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    progress INTEGER DEFAULT 0,
    current_phase VARCHAR(100),
    next_phase VARCHAR(100),
    pause_points JSONB DEFAULT '[]',
    user_inputs JSONB DEFAULT '{}',
    phase_results JSONB DEFAULT '{}',
    agent_insights JSONB DEFAULT '[]',
    apps_ready_for_planning JSONB DEFAULT '[]',
    last_user_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Engagement-level architecture standards with version management
CREATE TABLE engagement_architecture_standards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id INTEGER NOT NULL,
    requirement_type VARCHAR(100) NOT NULL,
    description TEXT,
    mandatory BOOLEAN DEFAULT TRUE,
    supported_versions JSONB,  -- {"java": "11+", "python": "3.8+"}
    requirement_details JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_engagement_requirement UNIQUE (engagement_id, requirement_type)
);

-- Application-specific architecture overrides with rationale
CREATE TABLE application_architecture_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    standard_id UUID REFERENCES engagement_architecture_standards(id),
    override_type VARCHAR(100) NOT NULL,  -- exception, modification, addition
    override_details JSONB,
    rationale TEXT,
    approved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Flexible component identification beyond 3-tier
CREATE TABLE application_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(100) NOT NULL,  -- frontend, middleware, backend, service, etc.
    technology_stack JSONB,
    dependencies JSONB,  -- Other components this depends on
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_app_component UNIQUE (assessment_flow_id, application_id, component_name)
);

-- Component-aware tech debt analysis
CREATE TABLE tech_debt_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    component_id UUID REFERENCES application_components(id),
    debt_category VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    description TEXT NOT NULL,
    remediation_effort_hours INTEGER,
    impact_on_migration TEXT,
    tech_debt_score FLOAT,
    detected_by_agent VARCHAR(100),
    agent_confidence FLOAT CHECK (agent_confidence >= 0 AND agent_confidence <= 1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Component-level 6R treatments with compatibility validation
CREATE TABLE component_treatments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    component_id UUID REFERENCES application_components(id),
    recommended_strategy VARCHAR(20) NOT NULL CHECK (recommended_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')),
    rationale TEXT,
    compatibility_validated BOOLEAN DEFAULT FALSE,
    compatibility_issues JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_component_treatment UNIQUE (assessment_flow_id, component_id)
);

-- Application-level 6R decisions with component rollup
CREATE TABLE sixr_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    application_name VARCHAR(255) NOT NULL,
    overall_strategy VARCHAR(20) NOT NULL CHECK (overall_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    rationale TEXT,
    architecture_exceptions JSONB DEFAULT '[]',
    tech_debt_score FLOAT,
    risk_factors JSONB DEFAULT '[]',
    move_group_hints JSONB DEFAULT '[]',  -- Technology proximity, dependencies
    estimated_effort_hours INTEGER,
    estimated_cost DECIMAL(12, 2),
    user_modifications JSONB,
    modified_by VARCHAR(100),
    modified_at TIMESTAMP,
    app_on_page_data JSONB,  -- Complete consolidated view
    decision_factors JSONB,
    ready_for_planning BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_app_decision UNIQUE (assessment_flow_id, application_id)
);

-- Learning feedback for agent improvement
CREATE TABLE assessment_learning_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    decision_id UUID REFERENCES sixr_decisions(id) ON DELETE CASCADE,
    original_strategy VARCHAR(20) NOT NULL,
    override_strategy VARCHAR(20) NOT NULL,
    feedback_reason TEXT,
    agent_id VARCHAR(100),
    learned_pattern JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Performance Indexes Required**:
```sql
-- Core performance indexes
CREATE INDEX idx_assessment_flows_status ON assessment_flows(status);
CREATE INDEX idx_assessment_flows_client ON assessment_flows(client_account_id, engagement_id);
CREATE INDEX idx_assessment_flows_phase ON assessment_flows(current_phase, next_phase);
CREATE INDEX idx_eng_arch_standards ON engagement_architecture_standards(engagement_id);
CREATE INDEX idx_app_components ON application_components(application_id);
CREATE INDEX idx_component_treatments ON component_treatments(application_id, recommended_strategy);
CREATE INDEX idx_sixr_decisions_app ON sixr_decisions(application_id);
CREATE INDEX idx_sixr_ready_planning ON sixr_decisions(ready_for_planning);
CREATE INDEX idx_tech_debt_severity ON tech_debt_analysis(severity);
CREATE INDEX idx_tech_debt_component ON tech_debt_analysis(component_id);

-- JSONB GIN indexes for complex queries
CREATE INDEX idx_assessment_flows_selected_apps_gin ON assessment_flows USING GIN(selected_application_ids);
CREATE INDEX idx_assessment_flows_pause_points_gin ON assessment_flows USING GIN(pause_points);
CREATE INDEX idx_assessment_flows_user_inputs_gin ON assessment_flows USING GIN(user_inputs);
CREATE INDEX idx_component_tech_stack_gin ON application_components USING GIN(technology_stack);
CREATE INDEX idx_component_dependencies_gin ON application_components USING GIN(dependencies);
CREATE INDEX idx_sixr_app_on_page_gin ON sixr_decisions USING GIN(app_on_page_data);
```

**Acceptance Criteria**:
- [ ] All 8 core tables created with proper relationships
- [ ] JSONB fields for complex state data with GIN indexes
- [ ] Multi-tenant constraints and foreign key relationships
- [ ] Enum validation for strategy and severity fields
- [ ] Performance indexes for navigation and queries
- [ ] CASCADE delete relationships for data cleanup
- [ ] UUID primary keys following platform patterns
- [ ] Timestamp tracking for audit trail
- [ ] Proper CHECK constraints for data validation

---

### DB-002: Create Architecture Standards Seed Data
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 8 hours  
**Dependencies**: DB-001  
**Sprint**: Foundation Week 1-2  

**Description**: Create comprehensive seed data, templates, and initialization for engagement-level architecture standards with industry best practices

**Location**: `backend/app/core/seed_data/assessment_standards.py`

**Technical Requirements**:
- Industry-standard architecture templates for common technology stacks
- Technology lifecycle and supported version matrices
- Security and compliance requirement templates
- Cloud-native architecture patterns and minimums
- Integration with existing platform seed data patterns

**Seed Data Categories**:

1. **Technology Version Standards**:
```python
tech_version_standards = [
    {
        "requirement_type": "java_versions",
        "description": "Minimum supported Java versions for cloud migration",
        "mandatory": True,
        "supported_versions": {
            "java": "11+",
            "spring_boot": "2.5+",
            "spring_framework": "5.3+"
        },
        "requirement_details": {
            "rationale": "Java 8 end-of-life considerations",
            "migration_path": "Upgrade to Java 11 LTS or Java 17 LTS",
            "compatibility_notes": "Review deprecated APIs"
        }
    },
    {
        "requirement_type": "dotnet_versions", 
        "description": "Minimum supported .NET versions",
        "mandatory": True,
        "supported_versions": {
            "dotnet_core": "3.1+",
            "dotnet_framework": "4.8+",
            "asp_net_core": "3.1+"
        }
    },
    {
        "requirement_type": "python_versions",
        "description": "Minimum supported Python versions",
        "mandatory": True, 
        "supported_versions": {
            "python": "3.8+",
            "django": "3.2+",
            "flask": "2.0+"
        }
    }
]
```

2. **Security and Compliance Standards**:
```python
security_standards = [
    {
        "requirement_type": "authentication",
        "description": "Modern authentication and authorization patterns",
        "mandatory": True,
        "requirement_details": {
            "patterns": ["OAuth2", "OIDC", "SAML"],
            "deprecated": ["Basic Auth", "Custom Sessions"],
            "required_features": ["MFA", "SSO Integration"]
        }
    },
    {
        "requirement_type": "data_encryption",
        "description": "Data encryption at rest and in transit",
        "mandatory": True,
        "requirement_details": {
            "transit": ["TLS 1.2+", "Certificate Management"],
            "rest": ["AES-256", "Key Management"],
            "compliance": ["PCI-DSS", "SOC2", "GDPR"]
        }
    }
]
```

3. **Architecture Pattern Standards**:
```python
architecture_standards = [
    {
        "requirement_type": "containerization",
        "description": "Container readiness for cloud deployment",
        "mandatory": False,
        "requirement_details": {
            "container_runtime": ["Docker", "Containerd"],
            "orchestration": ["Kubernetes", "Docker Swarm"],
            "registry": ["Container Registry Integration"],
            "best_practices": ["Multi-stage builds", "Minimal base images"]
        }
    },
    {
        "requirement_type": "api_design",
        "description": "RESTful API design standards",
        "mandatory": True,
        "requirement_details": {
            "standards": ["OpenAPI 3.0+", "REST Maturity Level 2+"],
            "documentation": ["API Documentation", "SDK Generation"],
            "versioning": ["Semantic Versioning", "Backward Compatibility"]
        }
    }
]
```

4. **Cloud-Native Standards**:
```python
cloud_native_standards = [
    {
        "requirement_type": "observability",
        "description": "Monitoring, logging, and tracing capabilities", 
        "mandatory": True,
        "requirement_details": {
            "monitoring": ["Prometheus", "CloudWatch", "Application Insights"],
            "logging": ["Structured Logging", "Centralized Logging"],
            "tracing": ["OpenTelemetry", "Distributed Tracing"],
            "alerting": ["SLA Monitoring", "Error Rate Tracking"]
        }
    },
    {
        "requirement_type": "scalability",
        "description": "Horizontal and vertical scaling capabilities",
        "mandatory": False,
        "requirement_details": {
            "horizontal": ["Load Balancing", "Auto Scaling"],
            "vertical": ["Resource Optimization", "Performance Tuning"],
            "data": ["Database Scaling", "Caching Strategies"]
        }
    }
]
```

**Initialization Function**:
```python
async def initialize_assessment_standards(db: AsyncSession, engagement_id: int):
    """Initialize engagement with default architecture standards"""
    
    all_standards = (
        tech_version_standards + 
        security_standards + 
        architecture_standards + 
        cloud_native_standards
    )
    
    for standard in all_standards:
        standard_record = EngagementArchitectureStandard(
            engagement_id=engagement_id,
            requirement_type=standard["requirement_type"],
            description=standard["description"],
            mandatory=standard["mandatory"],
            supported_versions=standard.get("supported_versions"),
            requirement_details=standard["requirement_details"],
            created_by="system_init"
        )
        db.add(standard_record)
    
    await db.commit()
```

**Acceptance Criteria**:
- [ ] Technology version matrices for Java, .NET, Python, Node.js
- [ ] Security and compliance requirement templates  
- [ ] Architecture pattern standards and best practices
- [ ] Cloud-native capability requirements
- [ ] Initialization function for new engagements
- [ ] Integration with database initialization hooks
- [ ] RBAC compatibility for standard modification
- [ ] Support for custom engagement-specific standards

---

### DB-003: Update Database Initialization Hooks
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 4 hours  
**Dependencies**: DB-001, DB-002  
**Sprint**: Foundation Week 1-2  

**Description**: Update existing database initialization to include assessment flow tables and seed data integration

**Location**: `backend/app/core/database_initialization.py`

**Technical Requirements**:
- Integration with existing platform initialization
- Assessment flow table creation verification
- Architecture standards seed data initialization
- Multi-tenant context preservation during initialization
- Alembic migration hook integration

**Updates Required**:

1. **Add Assessment Tables to Initialization**:
```python
# In database_initialization.py
async def verify_assessment_tables(db: AsyncSession):
    """Verify assessment flow tables exist and are properly configured"""
    
    required_tables = [
        'assessment_flows',
        'engagement_architecture_standards', 
        'application_architecture_overrides',
        'application_components',
        'tech_debt_analysis',
        'component_treatments',
        'sixr_decisions',
        'assessment_learning_feedback'
    ]
    
    for table in required_tables:
        result = await db.execute(
            text("SELECT to_regclass(:table_name)"), 
            {"table_name": table}
        )
        if not result.scalar():
            raise DatabaseInitializationError(f"Missing table: {table}")
    
    logger.info("Assessment flow tables verified successfully")
```

2. **Integration with Engagement Creation**:
```python
async def initialize_engagement_assessment_standards(
    db: AsyncSession, 
    engagement_id: int,
    client_account_id: int
):
    """Initialize assessment standards for new engagement"""
    
    from app.core.seed_data.assessment_standards import initialize_assessment_standards
    
    try:
        await initialize_assessment_standards(db, engagement_id)
        logger.info(f"Assessment standards initialized for engagement {engagement_id}")
    except Exception as e:
        logger.error(f"Failed to initialize assessment standards: {str(e)}")
        raise
```

3. **Update Main Initialization Function**:
```python
async def initialize_database(db: AsyncSession):
    """Enhanced database initialization with assessment support"""
    
    # Existing initialization...
    await create_platform_admin()
    await setup_demo_data()
    
    # New assessment initialization
    await verify_assessment_tables(db)
    
    # Initialize assessment standards for existing engagements
    engagements = await db.execute(
        select(Engagement).where(Engagement.status == 'active')
    )
    
    for engagement in engagements.scalars():
        await initialize_engagement_assessment_standards(
            db, 
            engagement.id, 
            engagement.client_account_id
        )
    
    logger.info("Database initialization completed with assessment support")
```

**Alembic Integration**:
```python
# In migration_hooks.py
async def post_assessment_migration_hook(db: AsyncSession):
    """Post-migration hook for assessment flow setup"""
    
    await verify_assessment_tables(db)
    
    # Initialize standards for existing engagements
    engagements = await db.execute(select(Engagement))
    for engagement in engagements.scalars():
        existing_standards = await db.execute(
            select(EngagementArchitectureStandard)
            .where(EngagementArchitectureStandard.engagement_id == engagement.id)
        )
        
        if not existing_standards.first():
            await initialize_engagement_assessment_standards(
                db, engagement.id, engagement.client_account_id
            )
```

**Acceptance Criteria**:
- [ ] Assessment tables verification in initialization
- [ ] Architecture standards initialization for new engagements
- [ ] Backward compatibility for existing engagements
- [ ] Alembic migration hook integration
- [ ] Error handling and logging for initialization failures
- [ ] Multi-tenant context preservation
- [ ] Integration with existing platform admin setup

---

## 🏗️ Foundation Infrastructure Tasks

### FOUND-001: Create Assessment Flow State Models
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 10 hours  
**Dependencies**: DB-001  
**Sprint**: Foundation Week 1-2  

**Description**: Create comprehensive Pydantic models for assessment flow state management with proper typing and validation

**Location**: `backend/app/models/assessment_flow.py`

**Technical Requirements**:
- Pydantic v2 models with proper validation
- Enum definitions for 6R strategies and flow phases  
- Support for complex JSONB field structures
- Integration with existing platform model patterns
- Type safety for component treatments and architecture standards

**Model Definitions Required**:

1. **Core Enums**:
```python
from enum import Enum

class SixRStrategy(str, Enum):
    REWRITE = "rewrite"
    REARCHITECT = "rearchitect" 
    REFACTOR = "refactor"
    REPLATFORM = "replatform"
    REHOST = "rehost"
    REPURCHASE = "repurchase"
    RETIRE = "retire"
    RETAIN = "retain"

class AssessmentPhase(str, Enum):
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies" 
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
    FINALIZATION = "finalization"

class TechDebtSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ComponentType(str, Enum):
    FRONTEND = "frontend"
    MIDDLEWARE = "middleware"
    BACKEND = "backend"
    DATABASE = "database"
    SERVICE = "service"
    API = "api"
    UI = "ui"
    CUSTOM = "custom"
```

2. **Architecture Standards Models**:
```python
class ArchitectureRequirement(BaseModel):
    requirement_type: str
    description: str
    level: Literal["engagement", "application"]
    mandatory: bool = True
    supported_versions: Optional[Dict[str, str]] = None
    requirement_details: Optional[Dict[str, Any]] = None
    exceptions: Optional[List[str]] = None
    verification_status: Optional[str] = None
    verified_at: Optional[datetime] = None
    modified_by: Optional[str] = None

class ApplicationArchitectureOverride(BaseModel):
    application_id: str
    standard_id: str
    override_type: Literal["exception", "modification", "addition"]
    override_details: Optional[Dict[str, Any]] = None
    rationale: str
    approved_by: Optional[str] = None
```

3. **Component and Tech Debt Models**:
```python
class ApplicationComponent(BaseModel):
    component_name: str
    component_type: ComponentType
    technology_stack: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True

class TechDebtItem(BaseModel):
    category: str
    severity: TechDebtSeverity
    description: str
    remediation_effort_hours: Optional[int] = None
    impact_on_migration: Optional[str] = None
    tech_debt_score: Optional[float] = None
    detected_by_agent: Optional[str] = None
    agent_confidence: Optional[float] = Field(None, ge=0, le=1)
    
    class Config:
        use_enum_values = True

class ComponentTreatment(BaseModel):
    component_name: str
    component_type: ComponentType
    recommended_strategy: SixRStrategy
    rationale: str
    compatibility_validated: bool = False
    compatibility_issues: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True
```

4. **6R Decision Models**:
```python
class SixRDecision(BaseModel):
    application_id: str
    application_name: str
    component_treatments: List[ComponentTreatment]
    overall_strategy: SixRStrategy
    confidence_score: float = Field(ge=0, le=1)
    rationale: str
    architecture_exceptions: List[str] = []
    tech_debt_score: Optional[float] = None
    risk_factors: List[str] = []
    estimated_effort_hours: Optional[int] = None
    estimated_cost: Optional[float] = None
    move_group_hints: List[str] = []
    user_modifications: Optional[Dict[str, Any]] = None
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    app_on_page_data: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True

class AssessmentLearningFeedback(BaseModel):
    original_strategy: SixRStrategy
    override_strategy: SixRStrategy  
    feedback_reason: str
    agent_id: str
    learned_pattern: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
```

5. **Main Flow State Model**:
```python
class AssessmentFlowState(BaseModel):
    flow_id: str
    client_account_id: int
    engagement_id: int
    selected_application_ids: List[str]
    
    # Architecture requirements
    engagement_architecture_standards: List[ArchitectureRequirement] = []
    application_architecture_overrides: Dict[str, List[ApplicationArchitectureOverride]] = {}
    architecture_captured: bool = False
    
    # Component identification  
    application_components: Dict[str, List[ApplicationComponent]] = {}
    
    # Tech debt analysis
    tech_debt_analysis: Dict[str, List[TechDebtItem]] = {}
    component_tech_debt: Dict[str, Dict[str, float]] = {}  # app_id -> component -> score
    
    # 6R decisions
    sixr_decisions: Dict[str, SixRDecision] = {}
    
    # User interaction tracking
    pause_points: List[str] = []
    user_inputs: Dict[str, Any] = {}
    
    # Flow metadata
    status: str = "initialized"
    progress: int = Field(default=0, ge=0, le=100)
    current_phase: AssessmentPhase
    next_phase: Optional[AssessmentPhase] = None
    phase_results: Dict[str, Any] = {}
    agent_insights: List[Dict[str, Any]] = []
    
    # Readiness tracking
    apps_ready_for_planning: List[str] = []
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_user_interaction: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Validation and Helper Methods**:
```python
class AssessmentFlowState(BaseModel):
    # ... fields above ...
    
    def calculate_overall_strategy(self, app_id: str) -> SixRStrategy:
        """Calculate app-level strategy from component treatments"""
        if app_id not in self.sixr_decisions:
            raise ValueError(f"No decisions found for app {app_id}")
        
        decision = self.sixr_decisions[app_id]
        strategies = [ct.recommended_strategy for ct in decision.component_treatments]
        
        # Return highest modernization strategy
        strategy_order = [
            SixRStrategy.REWRITE,
            SixRStrategy.REARCHITECT, 
            SixRStrategy.REFACTOR,
            SixRStrategy.REPLATFORM,
            SixRStrategy.REHOST,
            SixRStrategy.REPURCHASE,
            SixRStrategy.RETIRE,
            SixRStrategy.RETAIN
        ]
        
        for strategy in strategy_order:
            if strategy in strategies:
                return strategy
                
        return SixRStrategy.RETAIN  # Default fallback
    
    def get_apps_needing_review(self) -> List[str]:
        """Get applications that need user review"""
        return [
            app_id for app_id, decision in self.sixr_decisions.items()
            if decision.confidence_score < 0.8
        ]
    
    def validate_component_compatibility(self, app_id: str) -> List[str]:
        """Validate compatibility between component treatments"""
        issues = []
        if app_id not in self.sixr_decisions:
            return issues
            
        decision = self.sixr_decisions[app_id]
        treatments = {ct.component_name: ct.recommended_strategy 
                     for ct in decision.component_treatments}
        
        # Check for incompatible combinations
        if (treatments.get("frontend") == SixRStrategy.REWRITE and 
            treatments.get("backend") == SixRStrategy.RETAIN):
            issues.append("Frontend rewrite with backend retain may cause integration issues")
            
        return issues
```

**Acceptance Criteria**:
- [ ] Complete enum definitions for strategies, phases, severities
- [ ] Pydantic models with proper validation and constraints
- [ ] Support for complex JSONB field structures
- [ ] Helper methods for strategy calculation and validation
- [ ] Type safety throughout model hierarchy
- [ ] Integration with existing platform model patterns
- [ ] JSON serialization support for API responses
- [ ] Validation for component compatibility logic

---

### FOUND-002: Create Assessment Flow Repository Pattern
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 12 hours  
**Dependencies**: DB-001, FOUND-001  
**Sprint**: Foundation Week 1-2  

**Description**: Create repository pattern for assessment flow data access with multi-tenant support and complex query capabilities

**Location**: `backend/app/repositories/assessment_flow_repository.py`

**Technical Requirements**:
- Multi-tenant data access with ContextAwareRepository pattern
- Complex JSONB queries for component and tech debt data
- Efficient state persistence and retrieval
- Support for partial updates and incremental saves
- Integration with existing repository patterns

**Repository Implementation**:
```python
from app.repositories.base import ContextAwareRepository
from app.models.assessment_flow import AssessmentFlowState, SixRDecision
from sqlalchemy import select, update, and_, or_
from sqlalchemy.dialects.postgresql import insert

class AssessmentFlowRepository(ContextAwareRepository):
    """Repository for assessment flow data access with multi-tenant support"""
    
    def __init__(self, db: AsyncSession, client_account_id: int):
        super().__init__(db, client_account_id)
    
    async def create_assessment_flow(
        self, 
        engagement_id: int,
        selected_application_ids: List[str],
        created_by: str
    ) -> str:
        """Create new assessment flow with initial state"""
        
        flow_record = AssessmentFlow(
            client_account_id=self.client_account_id,
            engagement_id=engagement_id,
            selected_application_ids=selected_application_ids,
            status="initialized",
            current_phase="architecture_minimums",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(flow_record)
        await self.db.commit()
        await self.db.refresh(flow_record)
        
        return str(flow_record.id)
    
    async def get_assessment_flow_state(self, flow_id: str) -> Optional[AssessmentFlowState]:
        """Get complete assessment flow state with all related data"""
        
        # Get main flow record
        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
        )
        flow = result.scalar_one_or_none()
        if not flow:
            return None
        
        # Get architecture standards
        arch_standards = await self._get_architecture_standards(flow.engagement_id)
        
        # Get application overrides
        app_overrides = await self._get_application_overrides(flow_id)
        
        # Get application components
        app_components = await self._get_application_components(flow_id)
        
        # Get tech debt analysis
        tech_debt = await self._get_tech_debt_analysis(flow_id)
        
        # Get 6R decisions
        sixr_decisions = await self._get_sixr_decisions(flow_id)
        
        return AssessmentFlowState(
            flow_id=str(flow.id),
            client_account_id=flow.client_account_id,
            engagement_id=flow.engagement_id,
            selected_application_ids=flow.selected_application_ids,
            engagement_architecture_standards=arch_standards,
            application_architecture_overrides=app_overrides,
            architecture_captured=flow.architecture_captured,
            application_components=app_components,
            tech_debt_analysis=tech_debt["analysis"],
            component_tech_debt=tech_debt["scores"],
            sixr_decisions=sixr_decisions,
            pause_points=flow.pause_points or [],
            user_inputs=flow.user_inputs or {},
            status=flow.status,
            progress=flow.progress,
            current_phase=AssessmentPhase(flow.current_phase),
            next_phase=AssessmentPhase(flow.next_phase) if flow.next_phase else None,
            phase_results=flow.phase_results or {},
            agent_insights=flow.agent_insights or [],
            apps_ready_for_planning=flow.apps_ready_for_planning or [],
            created_at=flow.created_at,
            updated_at=flow.updated_at,
            last_user_interaction=flow.last_user_interaction,
            completed_at=flow.completed_at
        )
    
    async def update_flow_phase(
        self, 
        flow_id: str, 
        current_phase: str,
        next_phase: Optional[str] = None,
        progress: Optional[int] = None
    ):
        """Update flow phase and progress"""
        
        update_data = {
            "current_phase": current_phase,
            "updated_at": datetime.utcnow()
        }
        
        if next_phase:
            update_data["next_phase"] = next_phase
        if progress is not None:
            update_data["progress"] = progress
            
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(**update_data)
        )
        await self.db.commit()
    
    async def save_user_input(
        self, 
        flow_id: str, 
        phase: str, 
        user_input: Dict[str, Any]
    ):
        """Save user input for specific phase"""
        
        # Get current user_inputs
        result = await self.db.execute(
            select(AssessmentFlow.user_inputs)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
        )
        current_inputs = result.scalar() or {}
        current_inputs[phase] = user_input
        
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(
                user_inputs=current_inputs,
                last_user_interaction=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
    
    async def save_architecture_standards(
        self,
        engagement_id: int,
        standards: List[ArchitectureRequirement]
    ):
        """Save or update engagement architecture standards"""
        
        for standard in standards:
            stmt = insert(EngagementArchitectureStandard).values(
                engagement_id=engagement_id,
                requirement_type=standard.requirement_type,
                description=standard.description,
                mandatory=standard.mandatory,
                supported_versions=standard.supported_versions,
                requirement_details=standard.requirement_details,
                created_by=standard.modified_by or "system",
                updated_at=datetime.utcnow()
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['engagement_id', 'requirement_type'],
                set_=dict(
                    description=stmt.excluded.description,
                    mandatory=stmt.excluded.mandatory,
                    supported_versions=stmt.excluded.supported_versions,
                    requirement_details=stmt.excluded.requirement_details,
                    updated_at=stmt.excluded.updated_at
                )
            )
            
            await self.db.execute(stmt)
        
        await self.db.commit()
    
    async def save_application_components(
        self,
        flow_id: str,
        app_id: str,
        components: List[ApplicationComponent]
    ):
        """Save application components for specific app"""
        
        # Delete existing components for this app in this flow
        await self.db.execute(
            delete(ApplicationComponent)
            .where(
                and_(
                    ApplicationComponent.assessment_flow_id == flow_id,
                    ApplicationComponent.application_id == app_id
                )
            )
        )
        
        # Insert new components
        for component in components:
            component_record = ApplicationComponent(
                assessment_flow_id=flow_id,
                application_id=app_id,
                component_name=component.component_name,
                component_type=component.component_type,
                technology_stack=component.technology_stack,
                dependencies=component.dependencies
            )
            self.db.add(component_record)
        
        await self.db.commit()
    
    async def save_sixr_decision(
        self,
        flow_id: str,
        decision: SixRDecision
    ):
        """Save or update 6R decision for application"""
        
        stmt = insert(SixRDecisionRecord).values(
            assessment_flow_id=flow_id,
            application_id=decision.application_id,
            application_name=decision.application_name,
            overall_strategy=decision.overall_strategy,
            confidence_score=decision.confidence_score,
            rationale=decision.rationale,
            architecture_exceptions=decision.architecture_exceptions,
            tech_debt_score=decision.tech_debt_score,
            risk_factors=decision.risk_factors,
            move_group_hints=decision.move_group_hints,
            estimated_effort_hours=decision.estimated_effort_hours,
            estimated_cost=decision.estimated_cost,
            user_modifications=decision.user_modifications,
            modified_by=decision.modified_by,
            modified_at=decision.modified_at,
            app_on_page_data=decision.app_on_page_data,
            ready_for_planning=False,
            updated_at=datetime.utcnow()
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['assessment_flow_id', 'application_id'],
            set_=dict(
                overall_strategy=stmt.excluded.overall_strategy,
                confidence_score=stmt.excluded.confidence_score,
                rationale=stmt.excluded.rationale,
                architecture_exceptions=stmt.excluded.architecture_exceptions,
                tech_debt_score=stmt.excluded.tech_debt_score,
                risk_factors=stmt.excluded.risk_factors,
                move_group_hints=stmt.excluded.move_group_hints,
                user_modifications=stmt.excluded.user_modifications,
                modified_by=stmt.excluded.modified_by,
                modified_at=stmt.excluded.modified_at,
                app_on_page_data=stmt.excluded.app_on_page_data,
                updated_at=stmt.excluded.updated_at
            )
        )
        
        await self.db.execute(stmt)
        
        # Save component treatments
        await self._save_component_treatments(flow_id, decision)
        
        await self.db.commit()
    
    async def mark_apps_ready_for_planning(
        self,
        flow_id: str,
        app_ids: List[str]
    ):
        """Mark applications as ready for planning flow"""
        
        await self.db.execute(
            update(SixRDecisionRecord)
            .where(
                and_(
                    SixRDecisionRecord.assessment_flow_id == flow_id,
                    SixRDecisionRecord.application_id.in_(app_ids)
                )
            )
            .values(ready_for_planning=True)
        )
        
        # Update flow apps_ready_for_planning list
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(apps_ready_for_planning=app_ids)
        )
        
        await self.db.commit()
    
    # Private helper methods for data retrieval
    async def _get_architecture_standards(self, engagement_id: int) -> List[ArchitectureRequirement]:
        """Get architecture standards for engagement"""
        # Implementation details...
        pass
    
    async def _get_application_overrides(self, flow_id: str) -> Dict[str, List]:
        """Get application architecture overrides"""
        # Implementation details...
        pass
    
    async def _get_application_components(self, flow_id: str) -> Dict[str, List]:
        """Get application components"""
        # Implementation details...
        pass
    
    async def _get_tech_debt_analysis(self, flow_id: str) -> Dict:
        """Get tech debt analysis and scores"""
        # Implementation details...
        pass
    
    async def _get_sixr_decisions(self, flow_id: str) -> Dict[str, SixRDecision]:
        """Get 6R decisions for all applications"""
        # Implementation details...
        pass
```

**Acceptance Criteria**:
- [ ] Multi-tenant repository with ContextAwareRepository inheritance
- [ ] Complete CRUD operations for assessment flow state
- [ ] Efficient JSONB query support for complex data structures
- [ ] Incremental save capabilities for large flows
- [ ] Support for partial updates and phase-based saves
- [ ] Component compatibility validation during saves
- [ ] Integration with existing platform repository patterns
- [ ] Proper error handling and transaction management

---

## Next Steps

After completing these foundation tasks, proceed to:
1. **Backend & CrewAI Tasks** (Document 02)
2. **API & Integration Tasks** (Document 03) 
3. **Frontend & UX Tasks** (Document 04)
4. **Testing & DevOps Tasks** (Document 05)

## Dependencies Map

- **DB-002** depends on **DB-001**
- **DB-003** depends on **DB-001, DB-002** 
- **FOUND-001** depends on **DB-001**
- **FOUND-002** depends on **DB-001, FOUND-001**

All subsequent development phases depend on completing these foundation tasks first.