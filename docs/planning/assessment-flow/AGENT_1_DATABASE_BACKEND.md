# AI Coding Agent 1: Database & Backend Infrastructure

## Agent Overview
You are responsible for creating the database schema, core backend models, and foundational infrastructure for the Assessment Flow feature. Your work will enable other agents to build upon a solid data foundation.

## Context

### Project Overview
The AI Force Migration Platform is implementing an Assessment Flow as the second major CrewAI flow after Discovery Flow. The Assessment Flow takes selected applications from the inventory and determines optimal 6R migration strategies (Rehost, Replatform, Refactor, Repurchase, Retire, Retain).

### Technical Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL (async with asyncpg)
- **Framework**: CrewAI Flow with @start/@listen decorators
- **Development**: Docker-only (no local services)

### Key Architecture Patterns
- Multi-tenant architecture with `client_account_id` scoping
- Async-first database operations using `AsyncSessionLocal`
- Repository pattern with `ContextAwareRepository`
- PostgreSQL-only persistence (no SQLite)

## Your Assigned Tasks

### 🗄️ Database Tasks

#### DB-001: Create Assessment Flow Schema Migration
**Priority**: P0 - Critical  
**Effort**: 4 hours  
**Location**: `backend/alembic/versions/`

Create an Alembic migration with the following schema:

```sql
-- Assessment flow tracking
CREATE TABLE assessment_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_flow_id UUID REFERENCES discovery_flows(id) NOT NULL,
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    selected_application_ids JSONB NOT NULL,
    architecture_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    progress INTEGER DEFAULT 0,
    current_phase VARCHAR(100),
    phase_results JSONB DEFAULT '{}',
    agent_insights JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Architecture requirements and verification
CREATE TABLE architecture_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    requirement_type VARCHAR(100) NOT NULL,
    description TEXT,
    mandatory BOOLEAN DEFAULT TRUE,
    requirement_details JSONB,
    verification_status VARCHAR(50) DEFAULT 'pending',
    verification_notes TEXT,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tech debt analysis results
CREATE TABLE tech_debt_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    debt_category VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    description TEXT NOT NULL,
    remediation_effort_hours INTEGER,
    impact_on_migration TEXT,
    detected_by_agent VARCHAR(100),
    agent_confidence FLOAT CHECK (agent_confidence >= 0 AND agent_confidence <= 1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6R strategy decisions
CREATE TABLE sixr_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_flow_id UUID REFERENCES assessment_flows(id) ON DELETE CASCADE,
    application_id UUID NOT NULL,
    application_name VARCHAR(255) NOT NULL,
    recommended_strategy VARCHAR(20) NOT NULL CHECK (recommended_strategy IN ('rehost', 'replatform', 'refactor', 'repurchase', 'retire', 'retain')),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    rationale TEXT,
    risk_factors JSONB DEFAULT '[]',
    estimated_effort_hours INTEGER,
    estimated_cost DECIMAL(12, 2),
    user_override_strategy VARCHAR(20) CHECK (user_override_strategy IN ('rehost', 'replatform', 'refactor', 'repurchase', 'retire', 'retain')),
    override_reason TEXT,
    override_by VARCHAR(100),
    override_at TIMESTAMP,
    decision_factors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_app_decision UNIQUE (assessment_flow_id, application_id)
);

-- Learning feedback table
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

-- Create indexes
CREATE INDEX idx_assessment_flows_discovery_flow ON assessment_flows(discovery_flow_id);
CREATE INDEX idx_assessment_flows_status ON assessment_flows(status);
CREATE INDEX idx_assessment_flows_client ON assessment_flows(client_account_id, engagement_id);
CREATE INDEX idx_sixr_decisions_app ON sixr_decisions(application_id);
CREATE INDEX idx_tech_debt_severity ON tech_debt_analysis(severity);
CREATE INDEX idx_arch_req_status ON architecture_requirements(verification_status);
```

**Testing**: 
```bash
docker exec -it migration_backend alembic upgrade head
docker exec -it migration_backend alembic downgrade -1
```

#### DB-002: Add Assessment Flow Seed Data
**Priority**: P2 - Medium  
**Effort**: 2 hours  
**Location**: `backend/app/db/seed_assessment.py`

Create seed data script for testing.

---

### 🐍 Backend Tasks

#### BE-001: Create AssessmentFlowState Model
**Priority**: P0 - Critical  
**Effort**: 3 hours  
**Location**: `backend/app/models/assessment_flow_state.py`

```python
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class SixRStrategy(str, Enum):
    REHOST = "rehost"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    REPURCHASE = "repurchase"
    RETIRE = "retire"
    RETAIN = "retain"

class ArchitectureRequirement(BaseModel):
    requirement_type: str
    description: str
    mandatory: bool
    verification_status: Optional[str] = "pending"
    verified_at: Optional[datetime] = None

class TechDebtItem(BaseModel):
    category: str  # security, performance, maintainability
    severity: str  # critical, high, medium, low
    description: str
    remediation_effort_hours: int
    impact_on_migration: str

class SixRDecision(BaseModel):
    application_id: str
    application_name: str
    recommended_strategy: SixRStrategy
    confidence_score: float
    rationale: str
    risk_factors: List[str]
    estimated_effort_hours: int
    estimated_cost: float
    user_override: Optional[SixRStrategy] = None
    override_reason: Optional[str] = None
    override_by: Optional[str] = None
    override_at: Optional[datetime] = None

class AssessmentFlowState(BaseModel):
    flow_id: str
    discovery_flow_id: str
    client_account_id: int
    engagement_id: int
    selected_application_ids: List[str]
    
    # Architecture verification
    architecture_requirements: List[ArchitectureRequirement] = []
    architecture_verified: bool = False
    architecture_issues: List[str] = []
    
    # Tech debt analysis
    tech_debt_analysis: Dict[str, List[TechDebtItem]] = {}
    overall_tech_debt_score: Optional[float] = None
    
    # 6R decisions
    sixr_decisions: Dict[str, SixRDecision] = {}
    
    # Flow metadata
    status: str = "initialized"
    progress: int = 0
    current_phase: str = "initialization"
    phase_results: Dict[str, Any] = {}
    agent_insights: List[Dict[str, Any]] = []
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
```

#### BE-002: Create Assessment SQLAlchemy Models
**Priority**: P0 - Critical  
**Effort**: 4 hours  
**Location**: `backend/app/models/assessment.py`

Create SQLAlchemy ORM models matching the database schema. Follow the pattern from existing models in the codebase.

```python
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, DECIMAL, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid

class AssessmentFlow(Base):
    __tablename__ = "assessment_flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discovery_flow_id = Column(UUID(as_uuid=True), ForeignKey("discovery_flows.id"), nullable=False)
    client_account_id = Column(Integer, nullable=False)
    engagement_id = Column(Integer, nullable=False)
    selected_application_ids = Column(JSON, nullable=False)
    architecture_verified = Column(Boolean, default=False)
    status = Column(String(50), nullable=False, default="initialized")
    progress = Column(Integer, default=0)
    current_phase = Column(String(100))
    phase_results = Column(JSON, default={})
    agent_insights = Column(JSON, default=[])
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
    completed_at = Column(DateTime)
    
    # Relationships
    architecture_requirements = relationship("ArchitectureRequirement", back_populates="assessment_flow", cascade="all, delete-orphan")
    tech_debt_items = relationship("TechDebtAnalysis", back_populates="assessment_flow", cascade="all, delete-orphan")
    sixr_decisions = relationship("SixRDecision", back_populates="assessment_flow", cascade="all, delete-orphan")
    learning_feedback = relationship("AssessmentLearningFeedback", back_populates="assessment_flow", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='valid_progress'),
    )

# Create similar models for other tables...
```

#### BE-005: Implement Assessment Repository
**Priority**: P1 - High  
**Effort**: 6 hours  
**Location**: `backend/app/repositories/assessment_repository.py`

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.repositories.base import ContextAwareRepository
from app.models.assessment import AssessmentFlow, SixRDecision, TechDebtAnalysis

class AssessmentRepository(ContextAwareRepository):
    """Repository for assessment flow data access"""
    
    async def create_assessment_flow(
        self, 
        discovery_flow_id: str,
        selected_application_ids: List[str],
        engagement_id: int
    ) -> AssessmentFlow:
        """Create a new assessment flow"""
        # Implementation
        
    async def get_assessment_flow(self, flow_id: str) -> Optional[AssessmentFlow]:
        """Get assessment flow by ID with multi-tenant filtering"""
        # Implementation
        
    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        progress: int,
        current_phase: str
    ) -> None:
        """Update flow status and progress"""
        # Implementation
        
    async def save_tech_debt_analysis(
        self,
        flow_id: str,
        application_id: str,
        debt_items: List[Dict[str, Any]]
    ) -> None:
        """Save tech debt analysis results"""
        # Implementation
        
    async def save_sixr_decision(
        self,
        flow_id: str,
        decision: Dict[str, Any]
    ) -> SixRDecision:
        """Save or update 6R decision"""
        # Implementation
```

## Development Guidelines

### Docker Commands
```bash
# Run your development
docker-compose up -d --build

# Test your migrations
docker exec -it migration_backend alembic upgrade head
docker exec -it migration_backend alembic downgrade -1

# Run tests
docker exec -it migration_backend python -m pytest tests/models/test_assessment_models.py -v

# Check your code
docker exec -it migration_backend python -c "from app.models.assessment import AssessmentFlow; print('Models loaded successfully')"
```

### Testing Requirements
- Write unit tests for all models
- Test multi-tenant data isolation
- Verify async operations work correctly
- Test migration rollback scenarios

### Code Standards
- Follow existing patterns in the codebase
- Use type hints for all functions
- Include docstrings for classes and methods
- Handle errors gracefully with proper logging

### Integration Points
- Your models will be used by Agent 2 for the CrewAI flow
- Your repository will be used by Agent 3 for API endpoints
- Ensure all UUID fields handle serialization properly
- Follow the multi-tenant patterns from existing repositories

### Critical Reminders
- **NEVER** run PostgreSQL locally - always use Docker
- **ALWAYS** use async database operations
- **ALWAYS** include client_account_id in queries
- **NEVER** use sync SessionLocal in async context
- Test your migrations both up and down

## Completion Checklist
- [ ] DB-001: Migration created and tested
- [ ] DB-002: Seed data script created
- [ ] BE-001: AssessmentFlowState model with all validations
- [ ] BE-002: All SQLAlchemy models created
- [ ] BE-005: Repository with all CRUD operations
- [ ] Unit tests for all components
- [ ] Integration tests for repository
- [ ] Documentation updated

## Dependencies You're Providing
Other agents depend on your work:
- Agent 2 needs your models for CrewAI flow implementation
- Agent 3 needs your repository for API endpoints
- Agent 4 needs your models for TypeScript type generation

Start with DB-001 and BE-001 as they are P0 critical tasks that unblock others.