# Decommission Flow - Complete Solution Design

**Document Version**: 2.1
**Created**: 2025-01-05
**Updated**: 2025-01-14 (Post-Final-Review)
**Status**: ✅ APPROVED - Ready for Implementation
**ADR Alignment**:
- **ADR-027** (Universal FlowTypeConfig Pattern) - **CRITICAL**
- **ADR-025** (Child Flow Service Pattern) - **REQUIRED**
- ADR-006 (MFO Two-Table Pattern)
- ADR-012 (Status Management Separation)
- ADR-024 (TenantMemoryManager)

## Executive Summary

The Decommission Flow enables safe retirement of legacy systems identified for decommissioning during cloud migration assessments. This flow follows the proven MFO two-table pattern used in Collection and Assessment flows, integrating with TenantScopedAgentPool for AI-powered automation of planning, data retention, execution, and validation phases.

**Key Features**:
- AI-driven decommission planning with dependency analysis
- Automated compliance and data retention policies
- Safe execution with rollback capabilities
- Comprehensive validation and cleanup automation
- Integration with 6R recommendations (Retire strategy)

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Flow Orchestrator                  │
│              (crewai_flow_state_extensions)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Two-Table Pattern (ADR-006)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Decommission Flow                         │
│                   (decommission_flows)                       │
│                                                              │
│  Phases (per FlowTypeConfig - ADR-027):                     │
│  1. decommission_planning  (Planning & Risk Assessment)      │
│  2. data_migration         (Data Retention & Archival)       │
│  3. system_shutdown        (Execution, Validation, Cleanup)  │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │ TenantScopedAgentPool│  │  TenantMemoryManager │
    │   (7 Decom Agents)   │  │  (Learning Patterns) │
    └──────────────────────┘  └──────────────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
    Assets Table    Discovery/Assessment
    (Retire Strategy)  Flow Integration
```

### 1.2 Asset Eligibility Criteria

Systems eligible for decommissioning must meet ONE of these criteria:

1. **Pre-Migration Retirement** (from Discovery/Assessment):
   - 6R Strategy = "Retire" (on-prem systems deemed obsolete)
   - Identified as redundant during discovery phase
   - Zero business value identified by assessment agents

2. **Post-Migration Decommission** (from successful cloud migration):
   - Cloud migration completed (wave execution successful)
   - On-prem/virtual source system ready for retirement
   - Grace period expired (e.g., 90 days post-migration)

**Data Model Reference**:
```python
# Assets eligible for decommission
eligible_assets = db.query(Asset).filter(
    or_(
        # Pre-migration retirement
        Asset.six_r_strategy == "Retire",
        # Post-migration decommission
        and_(
            Asset.migration_status == "completed",
            Asset.decommission_eligible == True,
            Asset.grace_period_end < datetime.utcnow()
        )
    ),
    Asset.client_account_id == client_account_id,
    Asset.engagement_id == engagement_id
).all()
```

---

## 2. FlowTypeConfig Integration (ADR-027)

### 2.0 Universal FlowTypeConfig Pattern

**Per ADR-027, ALL flows MUST use FlowTypeConfig pattern exclusively.**

The decommission flow configuration is already implemented in:
**`backend/app/services/flow_configs/additional_flow_configs.py::get_decommission_flow_config()`**

#### Phase Definitions from FlowTypeConfig

**CANONICAL PHASES** (lines 619-749 of `additional_flow_configs.py`):

```python
phases = [
    PhaseConfig(
        name="decommission_planning",  # ← CRITICAL: Use this exact name
        display_name="Decommission Planning",
        description="Plan safe system decommissioning approach",
        required_inputs=["decommission_targets", "business_requirements"],
        can_pause=True,
        timeout_seconds=2700,  # 45 minutes
        metadata={
            "planning_aspects": ["data", "dependencies", "compliance", "communication"],
            "approval_required": True,
            "rollback_planning": True
        }
    ),
    PhaseConfig(
        name="data_migration",  # ← CRITICAL: Use this exact name
        display_name="Data Migration",
        description="Migrate and archive critical data before decommission",
        required_inputs=["decommission_plan", "data_requirements"],
        can_pause=True,
        timeout_seconds=7200,  # 120 minutes
        metadata={
            "migration_methods": ["backup", "archive", "transfer", "export"],
            "encryption_required": True
        }
    ),
    PhaseConfig(
        name="system_shutdown",  # ← CRITICAL: Use this exact name
        display_name="System Shutdown",
        description="Safely shutdown and decommission systems",
        required_inputs=["migrated_data", "shutdown_procedures"],
        completion_handler="decommission_completion",
        can_pause=True,
        timeout_seconds=3600,  # 60 minutes
        metadata={
            "shutdown_sequence": ["connections", "applications", "databases", "infrastructure"],
            "verification_required": True,
            "audit_trail": True
        }
    )
]
```

#### Phase Consolidation Strategy

The FlowTypeConfig uses a **3-phase structure** that consolidates the original 4-phase design:

1. **decommission_planning** (Phase 1)
   - System identification and selection
   - Dependency analysis and mapping
   - Risk assessment and mitigation
   - Cost analysis and ROI projections
   - Stakeholder approval workflows

2. **data_migration** (Phase 2)
   - Data retention policy assignment
   - Archive job creation and execution
   - Data migration with integrity verification
   - Compliance validation
   - Encryption and secure storage

3. **system_shutdown** (Phase 3 - Consolidates execution + validation)
   - Pre-execution safety checks
   - Graceful service shutdown
   - Infrastructure removal
   - **Post-decommission validation** (embedded)
   - **Resource cleanup** (embedded)
   - Audit trail completion

**Rationale for Consolidation:**
- Validation and cleanup are tightly coupled with shutdown execution
- Reduces unnecessary phase transitions
- Matches operational workflow (shutdown → verify → cleanup is atomic)
- Consistent with FlowTypeConfig already in production

#### FlowTypeConfig Capabilities

```python
capabilities = FlowCapabilities(
    supports_pause_resume=True,      # Can pause at any phase
    supports_rollback=True,          # Can rollback on failure
    supports_branching=False,        # Linear flow
    supports_iterations=False,       # Single-pass execution
    supports_scheduling=True,        # Schedule decommission
    supports_checkpointing=True,     # Save state between phases
    required_permissions=[
        "decommission.read",
        "decommission.write",
        "decommission.execute",
        "decommission.approve"
    ]
)
```

#### Retrieving Phase Definitions Programmatically

```python
from app.services.flow_type_registry import get_flow_config

# Get phase list at runtime (ADR-027 mandate)
async def get_decommission_phases():
    """Retrieve phase definitions from FlowTypeConfig."""
    config = get_flow_config("decommission")
    return [
        {
            "name": phase.name,
            "display_name": phase.display_name,
            "description": phase.description,
            "timeout_seconds": phase.timeout_seconds,
            "can_pause": phase.can_pause
        }
        for phase in config.phases
    ]
    # Returns: [
    #   {"name": "decommission_planning", "display_name": "Decommission Planning", ...},
    #   {"name": "data_migration", "display_name": "Data Migration", ...},
    #   {"name": "system_shutdown", "display_name": "System Shutdown", ...}
    # ]
```

#### Database Schema Alignment Mandate

**CRITICAL**: Database phase column names MUST match FlowTypeConfig phase names exactly:
- ❌ `planning_status` → ✅ `decommission_planning_status`
- ❌ `data_retention_status` → ✅ `data_migration_status`
- ❌ `execution_status` → ✅ `system_shutdown_status`
- ❌ `validation_status` → ❌ REMOVED (consolidated into `system_shutdown`)

---

## 3. Database Schema Design

### 2.1 Master Flow Table (Existing - Enhanced)

**Table**: `migration.crewai_flow_state_extensions`

```sql
-- No schema changes needed - uses existing master flow table
-- Flow type: "decommission"
-- Status values: initialized, running, paused, completed, failed, deleted
```

### 3.2 Child Flow Table (New)

**Table**: `migration.decommission_flows`

**CRITICAL**: Phase column names MUST match FlowTypeConfig phases per ADR-027

```sql
CREATE TABLE migration.decommission_flows (
    -- Identity
    flow_id UUID PRIMARY KEY,
    master_flow_id UUID NOT NULL REFERENCES migration.crewai_flow_state_extensions(flow_id),

    -- Multi-tenant scoping
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    -- Flow metadata
    flow_name VARCHAR(255),
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Operational status (child flow - operational decisions per ADR-012)
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    -- Values: initialized, decommission_planning, data_migration, system_shutdown, completed, failed

    current_phase VARCHAR(50) NOT NULL DEFAULT 'decommission_planning',
    -- Values: decommission_planning, data_migration, system_shutdown, completed
    -- ⚠️ MUST match FlowTypeConfig phase names exactly (ADR-027)

    -- Selected systems for decommission
    selected_system_ids UUID[] NOT NULL,  -- Array of Asset IDs
    system_count INTEGER NOT NULL,

    -- Phase progress tracking (ALIGNED WITH FLOWTYPECONFIG)
    decommission_planning_status VARCHAR(50) DEFAULT 'pending',
    decommission_planning_completed_at TIMESTAMP WITH TIME ZONE,

    data_migration_status VARCHAR(50) DEFAULT 'pending',
    data_migration_completed_at TIMESTAMP WITH TIME ZONE,

    system_shutdown_status VARCHAR(50) DEFAULT 'pending',
    system_shutdown_started_at TIMESTAMP WITH TIME ZONE,
    system_shutdown_completed_at TIMESTAMP WITH TIME ZONE,
    -- NOTE: Validation/cleanup now embedded in system_shutdown phase

    -- Configuration and runtime state
    decommission_strategy JSONB NOT NULL DEFAULT '{}',
    -- {
    --   "priority": "cost_savings" | "risk_reduction" | "compliance",
    --   "execution_mode": "immediate" | "scheduled" | "phased",
    --   "rollback_enabled": true,
    --   "stakeholder_approvals": []
    -- }

    runtime_state JSONB NOT NULL DEFAULT '{}',
    -- {
    --   "current_agent": "dependency_analyzer",
    --   "phase_metrics": {},
    --   "pending_approvals": [],
    --   "warnings": [],
    --   "errors": []
    -- }

    -- Aggregated metrics
    total_systems_decommissioned INTEGER DEFAULT 0,
    estimated_annual_savings DECIMAL(15, 2),
    actual_annual_savings DECIMAL(15, 2),
    compliance_score DECIMAL(5, 2),  -- 0-100

    -- Constraints
    CONSTRAINT fk_client_account FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(client_account_id),
    CONSTRAINT fk_engagement FOREIGN KEY (engagement_id)
        REFERENCES migration.engagements(engagement_id),
    CONSTRAINT valid_status CHECK (status IN (
        'initialized', 'decommission_planning', 'data_migration',
        'system_shutdown', 'completed', 'failed'
    )),
    CONSTRAINT valid_phase CHECK (current_phase IN (
        'decommission_planning', 'data_migration', 'system_shutdown', 'completed'
    ))
    -- ⚠️ Phase values match FlowTypeConfig exactly (ADR-027)
);

-- Indexes for performance
CREATE INDEX idx_decom_flows_tenant ON migration.decommission_flows(client_account_id, engagement_id);
CREATE INDEX idx_decom_flows_status ON migration.decommission_flows(status);
CREATE INDEX idx_decom_flows_master ON migration.decommission_flows(master_flow_id);
CREATE INDEX idx_decom_flows_created ON migration.decommission_flows(created_at DESC);
```

### 2.3 Supporting Tables (New)

#### Decommission Plans

```sql
CREATE TABLE migration.decommission_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    system_id UUID NOT NULL REFERENCES migration.assets(id),
    system_name VARCHAR(255) NOT NULL,
    system_type VARCHAR(100),

    -- Dependencies
    dependencies JSONB NOT NULL DEFAULT '[]',
    -- [{"system_id": "uuid", "name": "Dependent System", "impact": "high"}]

    -- Risk assessment
    risk_level VARCHAR(50) NOT NULL,  -- low, medium, high, very_high
    risk_factors JSONB NOT NULL DEFAULT '[]',
    mitigation_strategies JSONB NOT NULL DEFAULT '[]',

    -- Scheduling
    scheduled_date TIMESTAMP WITH TIME ZONE,
    estimated_duration_hours INTEGER,
    priority VARCHAR(50),  -- high, medium, low

    -- Approvals
    requires_approvals JSONB NOT NULL DEFAULT '[]',
    -- [{"approver": "user_id", "role": "IT Manager", "status": "pending"}]

    approval_status VARCHAR(50) DEFAULT 'pending',
    approved_by VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_decom_plan_flow FOREIGN KEY (flow_id)
        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE
);

CREATE INDEX idx_decom_plans_flow ON migration.decommission_plans(flow_id);
CREATE INDEX idx_decom_plans_system ON migration.decommission_plans(system_id);
```

#### Data Retention Policies

```sql
CREATE TABLE migration.data_retention_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    policy_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Retention requirements
    retention_period_days INTEGER NOT NULL,
    compliance_requirements VARCHAR[] NOT NULL,  -- ['GDPR', 'SOX', 'HIPAA']

    -- Data classification
    data_types VARCHAR[] NOT NULL,
    storage_location VARCHAR(255) NOT NULL,
    encryption_required BOOLEAN DEFAULT true,

    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, under_review

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_retention_client FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(client_account_id)
);

CREATE INDEX idx_retention_policies_tenant ON migration.data_retention_policies(client_account_id, engagement_id);
```

#### Archive Jobs

```sql
CREATE TABLE migration.archive_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
    policy_id UUID NOT NULL REFERENCES migration.data_retention_policies(policy_id),

    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    system_id UUID NOT NULL REFERENCES migration.assets(id),
    system_name VARCHAR(255) NOT NULL,

    -- Job details
    data_size_gb DECIMAL(15, 2),
    archive_location VARCHAR(500),

    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    -- Values: queued, in_progress, completed, failed, cancelled

    progress_percentage INTEGER DEFAULT 0,

    -- Timing
    scheduled_start TIMESTAMP WITH TIME ZONE,
    actual_start TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    actual_completion TIMESTAMP WITH TIME ZONE,

    -- Verification
    integrity_verified BOOLEAN DEFAULT false,
    verification_checksum VARCHAR(255),

    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_archive_job_flow FOREIGN KEY (flow_id)
        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE,
    CONSTRAINT valid_archive_status CHECK (status IN (
        'queued', 'in_progress', 'completed', 'failed', 'cancelled'
    ))
);

CREATE INDEX idx_archive_jobs_flow ON migration.archive_jobs(flow_id);
CREATE INDEX idx_archive_jobs_status ON migration.archive_jobs(status);
CREATE INDEX idx_archive_jobs_system ON migration.archive_jobs(system_id);
```

#### Decommission Execution Logs

```sql
CREATE TABLE migration.decommission_execution_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
    plan_id UUID NOT NULL REFERENCES migration.decommission_plans(plan_id),

    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    system_id UUID NOT NULL REFERENCES migration.assets(id),

    -- Execution details
    execution_phase VARCHAR(100) NOT NULL,
    -- Values: pre_validation, service_shutdown, data_migration,
    --         infrastructure_removal, verification

    status VARCHAR(50) NOT NULL,
    -- Values: pending, in_progress, completed, failed, rolled_back

    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    executed_by VARCHAR(255),  -- Agent or user ID

    -- Safety checks
    safety_checks_passed JSONB NOT NULL DEFAULT '[]',
    safety_checks_failed JSONB NOT NULL DEFAULT '[]',
    rollback_available BOOLEAN DEFAULT true,

    -- Logging
    execution_log JSONB NOT NULL DEFAULT '[]',
    -- [{"timestamp": "ISO", "action": "shutdown_service", "result": "success"}]

    error_details TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_execution_flow FOREIGN KEY (flow_id)
        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE
);

CREATE INDEX idx_execution_logs_flow ON migration.decommission_execution_logs(flow_id);
CREATE INDEX idx_execution_logs_plan ON migration.decommission_execution_logs(plan_id);
CREATE INDEX idx_execution_logs_status ON migration.decommission_execution_logs(status);
```

#### Validation Checks

```sql
CREATE TABLE migration.decommission_validation_checks (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
    system_id UUID NOT NULL REFERENCES migration.assets(id),

    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    -- Check details
    validation_category VARCHAR(100) NOT NULL,
    -- Values: data_integrity, access_removal, service_termination,
    --         dependency_verification, compliance

    check_name VARCHAR(255) NOT NULL,
    check_description TEXT,
    is_critical BOOLEAN DEFAULT false,

    -- Results
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Values: pending, passed, warning, failed

    result_details JSONB,
    issues_found INTEGER DEFAULT 0,

    validated_by VARCHAR(255),
    validated_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_validation_flow FOREIGN KEY (flow_id)
        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE,
    CONSTRAINT valid_validation_status CHECK (status IN (
        'pending', 'passed', 'warning', 'failed'
    ))
);

CREATE INDEX idx_validation_checks_flow ON migration.decommission_validation_checks(flow_id);
CREATE INDEX idx_validation_checks_system ON migration.decommission_validation_checks(system_id);
CREATE INDEX idx_validation_checks_status ON migration.decommission_validation_checks(status);
```

---

## 4. Child Flow Service Pattern (ADR-025)

### 4.0 Child Flow Service Requirement

**Per ADR-025, FlowTypeConfig MUST include `child_flow_service` field.**

The decommission flow requires a dedicated child flow service class to handle:
- Child flow CRUD operations
- Phase transitions and state management
- Integration with MFO for master flow sync
- Phase execution routing to appropriate agents

#### Child Flow Service Implementation

**File**: `backend/app/services/child_flows/decommission_child_flow_service.py`

```python
"""
Decommission Child Flow Service
Per ADR-025: Single execution path via child_flow_service
"""

from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.child_flows.base_child_flow_service import BaseChildFlowService
from app.repositories.decommission_flow_repository import DecommissionFlowRepository
from app.services.persistent_agents.decommission_agent_pool import DecommissionAgentPool
from app.models.decommission_flow import DecommissionFlow


class DecommissionChildFlowService(BaseChildFlowService):
    """
    Handles all decommission flow child operations.
    Follows Discovery/Collection pattern per ADR-025.
    """

    def __init__(self, db: AsyncSession, context: Dict[str, Any]):
        super().__init__(db, context)
        self.repository = DecommissionFlowRepository(db)
        self.agent_pool = DecommissionAgentPool()

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute phase by routing to appropriate handler.
        Per ADR-027: phase_name matches FlowTypeConfig phase name.
        """
        child_flow = await self.repository.get_by_flow_id(
            UUID(flow_id),
            UUID(self.context["client_account_id"]),
            UUID(self.context["engagement_id"])
        )

        if not child_flow:
            raise ValueError(f"Decommission flow {flow_id} not found")

        # Route to phase-specific handler
        if phase_name == "decommission_planning":
            return await self._execute_decommission_planning(child_flow, phase_input)
        elif phase_name == "data_migration":
            return await self._execute_data_migration(child_flow, phase_input)
        elif phase_name == "system_shutdown":
            return await self._execute_system_shutdown(child_flow, phase_input)
        else:
            raise ValueError(f"Unknown phase: {phase_name}")

    async def _execute_decommission_planning(
        self,
        child_flow: DecommissionFlow,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 1: Decommission Planning
        - Dependency analysis
        - Risk assessment
        - Cost analysis
        """
        # Get agents from pool
        dependency_analyzer = await self.agent_pool.get_agent(
            "dependency_analyzer",
            str(child_flow.client_account_id),
            str(child_flow.engagement_id)
        )
        risk_assessor = await self.agent_pool.get_agent(
            "risk_assessor",
            str(child_flow.client_account_id),
            str(child_flow.engagement_id)
        )
        cost_analyst = await self.agent_pool.get_agent(
            "cost_optimization_analyst",
            str(child_flow.client_account_id),
            str(child_flow.engagement_id)
        )

        # Execute planning crew (implementation in section 5)
        result = await execute_decommission_planning_crew(
            child_flow, dependency_analyzer, risk_assessor, cost_analyst
        )

        # Update phase status
        await self.repository.update_phase_status(
            child_flow.flow_id,
            "decommission_planning",
            "completed",
            child_flow.client_account_id,
            child_flow.engagement_id
        )

        return result

    async def _execute_data_migration(
        self,
        child_flow: DecommissionFlow,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 2: Data Migration
        - Data retention policy assignment
        - Archive job creation
        - Data migration execution
        """
        # Implementation follows same pattern as planning
        pass

    async def _execute_system_shutdown(
        self,
        child_flow: DecommissionFlow,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 3: System Shutdown (includes validation/cleanup)
        - Pre-execution safety checks
        - Service shutdown
        - Post-shutdown validation
        - Resource cleanup
        """
        # Implementation follows same pattern
        pass

    async def get_flow_by_master_id(self, master_flow_id: UUID) -> Optional[DecommissionFlow]:
        """Get child flow by master flow ID."""
        return await self.repository.get_by_master_flow_id(
            master_flow_id,
            UUID(self.context["client_account_id"]),
            UUID(self.context["engagement_id"])
        )

    async def update_flow_status(
        self,
        flow_id: UUID,
        status: str,
        runtime_state: Optional[Dict] = None
    ) -> None:
        """Update child flow status and optionally runtime state."""
        await self.repository.update_status(
            flow_id,
            status,
            runtime_state,
            UUID(self.context["client_account_id"]),
            UUID(self.context["engagement_id"])
        )
```

#### FlowTypeConfig Registration

**Update**: `backend/app/services/flow_configs/additional_flow_configs.py`

```python
def get_decommission_flow_config() -> FlowTypeConfig:
    """
    MFO-054: Decommission Flow Configuration
    Per ADR-025: MUST include child_flow_service
    """
    # ... existing phases definition ...

    return FlowTypeConfig(
        name="decommission",
        display_name="Decommission Flow",
        description="Safe system decommissioning with data preservation",
        version="2.0.0",
        phases=phases,
        child_flow_service=DecommissionChildFlowService,  # ← REQUIRED per ADR-025
        capabilities=capabilities,
        # ... rest of config ...
    )
```

#### Single Execution Path (No crew_class)

Per ADR-025, decommission flow uses **ONLY** `child_flow_service` for execution:
- ❌ No `crew_class` field (deprecated pattern)
- ✅ All execution routes through `child_flow_service.execute_phase()`
- ✅ Agents accessed via `TenantScopedAgentPool`
- ✅ Phase routing handled in service class

---

## 5. Backend API Architecture

### 3.1 API Endpoint Structure

**Base Path**: `/api/v1/decommission-flow/`

Following the Assessment Flow pattern with MFO integration:

```
/api/v1/decommission-flow/
├── flow-management.py         # Initialize, status, resume, cancel
├── mfo_integration.py         # MFO two-table pattern helpers
├── planning.py                # Planning & assessment phase
├── data_retention.py          # Data retention & archival phase
├── execution.py               # Safe execution phase
├── validation.py              # Validation & cleanup phase
├── export.py                  # Export reports (PDF, Excel, JSON)
└── __init__.py                # Router aggregation
```

### 3.2 MFO Integration Layer

**File**: `backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py`

```python
"""
Decommission Flow MFO Integration
Per ADR-006: Two-table pattern for master + child flows
"""

from uuid import UUID, uuid4
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.decommission_flow import DecommissionFlow
from app.repositories.decommission_flow_repository import DecommissionFlowRepository

logger = logging.getLogger(__name__)

async def create_decommission_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    system_ids: List[UUID],
    user_id: str,
    flow_name: str | None,
    decommission_strategy: Dict[str, Any],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Create decommission flow through MFO using two-table pattern.

    Returns:
        {
            "flow_id": "uuid",
            "status": "initialized",
            "current_phase": "decommission_planning",
            "selected_systems": [...],
            "message": "Decommission flow created successfully"
        }
    """
    flow_id = uuid4()

    try:
        async with db.begin():  # Atomic transaction
            # Step 1: Create master flow (lifecycle management)
            master_flow = CrewAIFlowStateExtensions(
                flow_id=flow_id,
                flow_type="decommission",
                flow_status="running",  # High-level lifecycle
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                flow_configuration={
                    "created_via": "decommission_api",
                    "flow_name": flow_name,
                    "system_count": len(system_ids)
                },
                flow_persistence_data={}
            )
            db.add(master_flow)
            await db.flush()

            # Step 2: Create child flow (operational state)
            child_flow = DecommissionFlow(
                flow_id=flow_id,
                master_flow_id=master_flow.flow_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                created_by=user_id,
                flow_name=flow_name or f"Decommission_{flow_id.hex[:8]}",
                status="initialized",  # Operational status
                current_phase="decommission_planning",
                selected_system_ids=system_ids,
                system_count=len(system_ids),
                decommission_strategy=decommission_strategy,
                runtime_state={
                    "initialized_at": datetime.utcnow().isoformat(),
                    "pending_approvals": [],
                    "current_agent": None
                }
            )
            db.add(child_flow)

            await db.commit()

        logger.info(f"Created decommission flow {flow_id} with {len(system_ids)} systems")

        return {
            "flow_id": str(flow_id),
            "status": child_flow.status,
            "current_phase": child_flow.current_phase,
            "selected_systems": [str(sid) for sid in system_ids],
            "message": f"Decommission flow initialized for {len(system_ids)} systems"
        }

    except Exception as e:
        logger.error(f"Failed to create decommission flow: {e}")
        raise


async def get_decommission_status_via_mfo(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Get decommission flow status (child flow operational state).
    Per ADR-012: Use child flow status for UI and agent decisions.
    """
    repo = DecommissionFlowRepository(db)

    # Get child flow (operational state)
    child_flow = await repo.get_by_flow_id(
        flow_id, client_account_id, engagement_id
    )

    if not child_flow:
        raise ValueError(f"Decommission flow {flow_id} not found")

    return {
        "flow_id": str(child_flow.flow_id),
        "master_flow_id": str(child_flow.master_flow_id),
        "status": child_flow.status,
        "current_phase": child_flow.current_phase,
        "system_count": child_flow.system_count,
        "phase_progress": {
            "decommission_planning": child_flow.decommission_planning_status,
            "data_migration": child_flow.data_migration_status,
            "system_shutdown": child_flow.system_shutdown_status
        },
        # ⚠️ Phase names match FlowTypeConfig (ADR-027)
        "metrics": {
            "systems_decommissioned": child_flow.total_systems_decommissioned,
            "estimated_savings": float(child_flow.estimated_annual_savings or 0),
            "compliance_score": float(child_flow.compliance_score or 0)
        },
        "runtime_state": child_flow.runtime_state,
        "created_at": child_flow.created_at.isoformat(),
        "updated_at": child_flow.updated_at.isoformat()
    }


async def update_decommission_phase_via_mfo(
    flow_id: UUID,
    new_phase: str,
    new_status: str,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> None:
    """
    Update decommission flow phase and status.
    Syncs master and child flows atomically per ADR-012.
    """
    async with db.begin():
        # Update child flow (operational state)
        repo = DecommissionFlowRepository(db)
        await repo.update_phase_status(
            flow_id, new_phase, new_status,
            client_account_id, engagement_id
        )

        # Sync master flow if terminal state
        if new_status in ["completed", "failed"]:
            master_repo = MasterFlowRepository(db)
            master_status = "completed" if new_status == "completed" else "failed"
            await master_repo.update_status(flow_id, master_status)

        await db.commit()
```

### 3.3 Flow Management Endpoints

**File**: `backend/app/api/v1/endpoints/decommission_flow/flow_management.py`

```python
"""
Decommission flow management endpoints.
Handles initialization, status, resume, and cancellation.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.core.context_helpers import verify_client_access, verify_engagement_access
from app.schemas.decommission_flow import (
    DecommissionFlowCreateRequest,
    DecommissionFlowResponse,
    DecommissionFlowStatusResponse
)

from .mfo_integration import (
    create_decommission_via_mfo,
    get_decommission_status_via_mfo
)

router = APIRouter()


@router.post("/initialize", response_model=DecommissionFlowResponse)
async def initialize_decommission_flow(
    request: DecommissionFlowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """
    Initialize decommission flow for selected systems.

    Eligible systems:
    - Pre-migration: 6R strategy = "Retire"
    - Post-migration: Successfully migrated assets past grace period

    Request body:
    {
        "selected_system_ids": ["uuid1", "uuid2"],
        "flow_name": "Q1 2025 Decommission",
        "decommission_strategy": {
            "priority": "cost_savings",
            "execution_mode": "phased",
            "rollback_enabled": true
        }
    }
    """
    try:
        await verify_engagement_access(db, engagement_id, client_account_id)

        # Verify systems are eligible for decommission
        await verify_systems_eligible_for_decommission(
            db, request.selected_system_ids, client_account_id, engagement_id
        )

        # Create flow via MFO
        system_ids_uuid = [UUID(sid) for sid in request.selected_system_ids]

        result = await create_decommission_via_mfo(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            system_ids=system_ids_uuid,
            user_id=current_user.id,
            flow_name=request.flow_name,
            decommission_strategy=request.decommission_strategy,
            db=db
        )

        flow_id = result["flow_id"]

        # Start planning phase in background
        background_tasks.add_task(
            execute_decommission_planning_phase,
            flow_id, client_account_id, engagement_id, current_user.id
        )

        return DecommissionFlowResponse(
            flow_id=flow_id,
            status=result["status"],
            current_phase=result["current_phase"],
            next_phase="data_migration",
            selected_systems=result["selected_systems"],
            message=result["message"]
        )

    except Exception as e:
        logger.error(f"Decommission flow initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{flow_id}/status", response_model=DecommissionFlowStatusResponse)
async def get_decommission_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """Get current status of decommission flow (child flow operational state)."""
    try:
        status = await get_decommission_status_via_mfo(
            UUID(flow_id), UUID(client_account_id), UUID(engagement_id), db
        )
        return DecommissionFlowStatusResponse(**status)

    except Exception as e:
        logger.error(f"Failed to get decommission flow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 4. CrewAI Agent Architecture

### 4.1 Decommission Agent Pool

Using `TenantScopedAgentPool` for multi-tenant agent management:

**File**: `backend/app/services/persistent_agents/decommission_agent_pool.py`

```python
"""
Decommission-specific agent pool configuration.
Integrates with TenantScopedAgentPool for lifecycle management.
"""

from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool, AgentConfig
)

# Decommission agent definitions
DECOMMISSION_AGENTS = {
    "dependency_analyzer": AgentConfig(
        name="Dependency Analyzer",
        role="System Dependency Mapping Specialist",
        goal="Identify all system dependencies to prevent downstream failures",
        backstory="""Expert in enterprise architecture with 15+ years analyzing
        system dependencies. Creates comprehensive dependency maps to ensure safe
        decommissioning without impacting dependent systems.""",
        tools=["cmdb_query", "network_discovery", "api_dependency_mapper"],
        memory=False  # Per ADR-024
    ),

    "risk_assessor": AgentConfig(
        name="Decommission Risk Assessor",
        role="Risk Analysis and Mitigation Specialist",
        goal="Assess decommission risks and create mitigation strategies",
        backstory="""20+ years in IT risk management, specialized in system
        retirement risks. Evaluates business impact, technical risks, and
        regulatory compliance to ensure safe decommissioning.""",
        tools=["risk_matrix_calculator", "compliance_checker", "impact_analyzer"],
        memory=False
    ),

    "data_retention_specialist": AgentConfig(
        name="Data Retention Specialist",
        role="Compliance and Data Archival Expert",
        goal="Ensure data retention compliance and secure archival",
        backstory="""Compliance expert with deep knowledge of GDPR, SOX, HIPAA,
        and PCI-DSS. Creates retention policies that balance legal requirements
        with storage optimization.""",
        tools=["compliance_policy_lookup", "data_classifier", "archive_calculator"],
        memory=False
    ),

    "archive_orchestrator": AgentConfig(
        name="Archive Orchestrator",
        role="Data Migration and Archive Automation Specialist",
        goal="Execute data archival with integrity verification",
        backstory="""Data migration expert with 10+ years managing petabyte-scale
        archives. Ensures data integrity, encryption, and accessibility while
        optimizing storage costs.""",
        tools=["data_migrator", "integrity_verifier", "encryption_service"],
        memory=False
    ),

    "execution_safety_agent": AgentConfig(
        name="Execution Safety Guardian",
        role="Safe Decommission Execution Specialist",
        goal="Execute decommissions safely with rollback capabilities",
        backstory="""Infrastructure automation expert with zero-downtime deployment
        expertise. Implements safety checks, gradual shutdowns, and automated
        rollback for risk-free decommissioning.""",
        tools=["service_controller", "health_monitor", "rollback_orchestrator"],
        memory=False
    ),

    "validation_engineer": AgentConfig(
        name="Validation Engineer",
        role="Post-Decommission Verification Specialist",
        goal="Verify successful decommission and complete cleanup",
        backstory="""Quality assurance engineer specialized in infrastructure
        validation. Performs comprehensive checks to ensure complete system
        removal and resource cleanup.""",
        tools=["access_verifier", "resource_scanner", "compliance_auditor"],
        memory=False
    ),

    "cost_optimization_analyst": AgentConfig(
        name="Cost Optimization Analyst",
        role="Decommission ROI and Savings Analyst",
        goal="Calculate and verify cost savings from decommissioning",
        backstory="""FinOps specialist with expertise in TCO analysis. Tracks
        infrastructure costs, calculates savings, and provides ROI metrics for
        decommission initiatives.""",
        tools=["cost_calculator", "roi_analyzer", "savings_tracker"],
        memory=False
    )
}


class DecommissionAgentPool:
    """
    Manages decommission-specific agent pool using TenantScopedAgentPool.
    """

    def __init__(self):
        self.agent_pool = TenantScopedAgentPool(
            agent_configs=DECOMMISSION_AGENTS,
            pool_name="decommission_agents"
        )

    async def get_agent(
        self,
        agent_key: str,
        client_account_id: str,
        engagement_id: str
    ):
        """Get agent instance scoped to tenant."""
        return await self.agent_pool.get_agent(
            agent_key, client_account_id, engagement_id
        )

    async def release_agents(
        self,
        client_account_id: str,
        engagement_id: str
    ):
        """Release all agents for tenant when flow completes."""
        await self.agent_pool.release_tenant_agents(
            client_account_id, engagement_id
        )
```

### 4.2 Phase-Specific Crews

Each decommission phase uses a specialized crew:

```python
"""
Decommission phase execution crews.
Each phase orchestrates multiple agents for comprehensive automation.
"""

from crewai import Crew, Task
from app.services.crewai_flows.config.crew_factory import create_crew

async def execute_decommission_planning_crew(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    selected_systems: List[Dict]
):
    """
    Decommission Planning Phase Crew (per FlowTypeConfig ADR-027):
    - Dependency Analyzer: Map system dependencies
    - Risk Assessor: Evaluate decommission risks
    - Cost Analyst: Calculate potential savings

    Phase name: "decommission_planning" per FlowTypeConfig
    This consolidates planning, dependency analysis, and risk assessment.
    """
    agent_pool = DecommissionAgentPool()

    dependency_analyzer = await agent_pool.get_agent(
        "dependency_analyzer", client_account_id, engagement_id
    )
    risk_assessor = await agent_pool.get_agent(
        "risk_assessor", client_account_id, engagement_id
    )
    cost_analyst = await agent_pool.get_agent(
        "cost_optimization_analyst", client_account_id, engagement_id
    )

    # Define tasks
    dependency_task = Task(
        description=f"Analyze dependencies for {len(selected_systems)} systems",
        expected_output="Dependency map with impact analysis",
        agent=dependency_analyzer
    )

    risk_task = Task(
        description="Assess decommission risks and create mitigation plan",
        expected_output="Risk assessment with mitigation strategies",
        agent=risk_assessor,
        context=[dependency_task]  # Depends on dependency analysis
    )

    cost_task = Task(
        description="Calculate estimated cost savings from decommissioning",
        expected_output="Financial impact analysis with ROI projections",
        agent=cost_analyst
    )

    # Create crew
    planning_crew = create_crew(
        agents=[dependency_analyzer, risk_assessor, cost_analyst],
        tasks=[dependency_task, risk_task, cost_task],
        memory=False,  # Per ADR-024
        verbose=False
    )

    # Execute crew
    result = await planning_crew.kickoff_async()

    # Store results in flow runtime_state
    await update_flow_planning_results(flow_id, result)

    return result
```

---

## 5. Frontend Integration

### 5.1 API Service Layer

**File**: `src/lib/api/decommissionFlowApi.ts`

```typescript
/**
 * Decommission Flow API Service
 * Follows snake_case convention per API field naming standards
 */

import { apiCall } from './apiClient';

export interface DecommissionFlowCreateRequest {
  selected_system_ids: string[];
  flow_name?: string;
  decommission_strategy: {
    priority: 'cost_savings' | 'risk_reduction' | 'compliance';
    execution_mode: 'immediate' | 'scheduled' | 'phased';
    rollback_enabled: boolean;
  };
}

export interface DecommissionFlowResponse {
  flow_id: string;
  status: string;
  current_phase: string;
  next_phase: string;
  selected_systems: string[];
  message: string;
}

export interface DecommissionFlowStatus {
  flow_id: string;
  master_flow_id: string;
  status: string;
  current_phase: string;
  system_count: number;
  phase_progress: {
    decommission_planning: string;
    data_migration: string;
    system_shutdown: string;
  };
  // ⚠️ Phase names match FlowTypeConfig (ADR-027)
  metrics: {
    systems_decommissioned: number;
    estimated_savings: number;
    compliance_score: number;
  };
  runtime_state: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export const decommissionFlowApi = {
  /**
   * Initialize new decommission flow
   */
  async initialize(
    request: DecommissionFlowCreateRequest
  ): Promise<DecommissionFlowResponse> {
    return apiCall('/api/v1/decommission-flow/initialize', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Get flow status (child flow operational state per ADR-012)
   */
  async getStatus(flow_id: string): Promise<DecommissionFlowStatus> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/status`);
  },

  /**
   * Get phase definitions from FlowTypeConfig (ADR-027)
   * Frontend MUST retrieve phases from API, not hardcode
   */
  async getPhases(): Promise<PhaseDetail[]> {
    return apiCall('/api/v1/flow-metadata/phases/decommission');
    // Returns: [
    //   {name: "decommission_planning", display_name: "Decommission Planning", ...},
    //   {name: "data_migration", display_name: "Data Migration", ...},
    //   {name: "system_shutdown", display_name: "System Shutdown", ...}
    // ]
  },

  /**
   * Get eligible systems for decommission
   */
  async getEligibleSystems(engagement_id: string): Promise<any[]> {
    return apiCall(`/api/v1/decommission-flow/eligible-systems`, {
      method: 'GET',
      headers: { 'X-Engagement-ID': engagement_id },
    });
  },

  /**
   * Approve decommission plan
   */
  async approvePlan(flow_id: string, plan_id: string): Promise<void> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/planning/approve`, {
      method: 'POST',
      body: JSON.stringify({ plan_id }),
    });
  },

  /**
   * Start execution phase
   */
  async startExecution(flow_id: string): Promise<void> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/execution/start`, {
      method: 'POST',
    });
  },

  /**
   * Export decommission report
   */
  async exportReport(
    flow_id: string,
    format: 'pdf' | 'excel' | 'json'
  ): Promise<Blob> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
      responseType: 'blob',
    });
  },
};
```

### 5.2 React Query Hooks

**File**: `src/hooks/decommission/useDecommissionFlow.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { decommissionFlowApi } from '@/lib/api/decommissionFlowApi';

/**
 * Hook for decommission flow status with polling
 * Per ADR-012: Uses child flow status for UI decisions
 */
export function useDecommissionFlowStatus(flow_id: string | null) {
  return useQuery({
    queryKey: ['decommission-flow-status', flow_id],
    queryFn: () => decommissionFlowApi.getStatus(flow_id!),
    enabled: !!flow_id,
    refetchInterval: (data) => {
      // Poll every 5s if in active phase, 15s if idle, stop if completed/failed
      const status = data?.status;
      const currentPhase = data?.current_phase;

      // Check both status and current_phase for active states (ADR-027 phase names)
      if (
        status === 'decommission_planning' ||
        status === 'data_migration' ||
        status === 'system_shutdown' ||
        currentPhase === 'decommission_planning' ||
        currentPhase === 'data_migration' ||
        currentPhase === 'system_shutdown'
      ) {
        return 5000;
      }

      if (status === 'completed' || status === 'failed') {
        return false; // Stop polling
      }

      return 15000; // Idle state polling
    },
  });
}

/**
 * Initialize decommission flow mutation
 */
export function useInitializeDecommissionFlow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: decommissionFlowApi.initialize,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['decommission-flows'] });
      queryClient.setQueryData(['decommission-flow-status', data.flow_id], data);
    },
  });
}

/**
 * Get eligible systems for decommission
 */
export function useEligibleSystems(engagement_id: string) {
  return useQuery({
    queryKey: ['eligible-systems', engagement_id],
    queryFn: () => decommissionFlowApi.getEligibleSystems(engagement_id),
    enabled: !!engagement_id,
  });
}
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Deliverables**:
- Database schema creation (Alembic migration)
- SQLAlchemy models for all tables
- Repository layer for data access
- MFO integration layer (`mfo_integration.py`)

**Files**:
```
backend/alembic/versions/120_create_decommission_tables.py
backend/app/models/decommission_flow.py
backend/app/repositories/decommission_flow_repository.py
backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py
```

### Phase 2: Backend API (Weeks 3-4)
**Deliverables**:
- Flow management endpoints (initialize, status, cancel)
- Planning phase endpoints and logic
- Data retention endpoints and policies
- Execution phase endpoints with safety checks
- Validation endpoints and reporting

**Files**:
```
backend/app/api/v1/endpoints/decommission_flow/
├── __init__.py
├── flow_management.py
├── planning.py
├── data_retention.py
├── execution.py
├── validation.py
└── export.py
```

### Phase 3: Agent Architecture (Weeks 5-6)
**Deliverables**:
- Decommission agent pool configuration
- Phase-specific crew implementations
- Agent tool integrations (CMDB, compliance, cost)
- TenantMemoryManager integration for learning

**Files**:
```
backend/app/services/persistent_agents/decommission_agent_pool.py
backend/app/services/crewai_flows/decommission/
├── planning_crew.py
├── data_retention_crew.py
├── execution_crew.py
└── validation_crew.py
```

### Phase 4: Frontend Integration (Weeks 7-8)
**Deliverables**:
- API service layer (`decommissionFlowApi.ts`)
- React Query hooks for state management
- Convert mock pages to live data-driven components
- Integration with existing asset inventory

**Files**:
```
src/lib/api/decommissionFlowApi.ts
src/hooks/decommission/
├── useDecommissionFlow.ts
├── useDecommissionPlanning.ts
├── useDataRetention.ts
└── useExecution.ts
src/pages/decommission/
├── Index.tsx (update with live data)
├── Planning.tsx (update)
├── DataRetention.tsx (update)
├── Execution.tsx (update)
└── Validation.tsx (update)
```

### Phase 5: Testing & Validation (Weeks 9-10)
**Deliverables**:
- Unit tests for repositories and services
- Integration tests for API endpoints
- E2E tests with Playwright (qa-playwright-tester agent)
- Load testing for multi-tenant scenarios

**Files**:
```
backend/tests/integration/test_decommission_flow.py
tests/e2e/decommission/
├── planning.spec.ts
├── data_retention.spec.ts
├── execution.spec.ts
└── validation.spec.ts
```

### Phase 6: Documentation & Launch (Week 11-12)
**Deliverables**:
- API documentation (OpenAPI specs)
- User guide for decommission workflows
- Admin guide for policy configuration
- Runbook for operations team

**Files**:
```
docs/user-guide/DECOMMISSION_FLOW.md
docs/api/DECOMMISSION_ENDPOINTS.md
docs/runbooks/DECOMMISSION_OPERATIONS.md
```

---

## 7. Integration Points

### 7.1 Assessment Flow Integration

**Trigger**: Assets with 6R strategy = "Retire"

```python
# In assessment flow completion handler
async def on_assessment_complete(assessment_flow_id: str):
    """Auto-create decommission recommendations for Retire assets."""

    # Get assets marked for retirement
    retire_assets = await get_assets_by_sixr_strategy(
        assessment_flow_id, "Retire"
    )

    if retire_assets:
        # Create decommission recommendation
        await create_decommission_recommendation(
            engagement_id=assessment_flow.engagement_id,
            system_ids=[asset.id for asset in retire_assets],
            reason="6R Assessment Recommendation",
            estimated_savings=calculate_retirement_savings(retire_assets)
        )
```

### 7.2 Wave Execution Integration

**Trigger**: Successful cloud migration completion

```python
# In wave execution completion handler
async def on_wave_migration_complete(wave_id: str):
    """Mark source systems eligible for decommission post-migration."""

    migrated_assets = await get_wave_assets(wave_id, status="completed")

    for asset in migrated_assets:
        await mark_system_decommission_eligible(
            system_id=asset.source_system_id,
            grace_period_days=90,  # Configurable per client
            reason="Successful cloud migration completed"
        )
```

### 7.3 FinOps Integration

**Data Flow**: Cost savings tracking

```python
# Real-time cost tracking for decommissioned systems
async def track_decommission_savings(decommission_flow_id: str):
    """Send cost savings to FinOps dashboard."""

    flow = await get_decommission_flow(decommission_flow_id)

    for system in flow.decommissioned_systems:
        await finops_service.record_cost_avoidance(
            system_id=system.id,
            monthly_savings=system.infrastructure_cost,
            category="decommission",
            effective_date=system.decommission_completed_at
        )
```

---

## 8. Security & Compliance

### 8.1 Multi-Tenant Isolation

All queries MUST include:
```python
# Always scope by tenant
.filter(
    DecommissionFlow.client_account_id == client_account_id,
    DecommissionFlow.engagement_id == engagement_id
)
```

### 8.2 Approval Workflows

Critical operations require multi-level approvals:
```python
APPROVAL_REQUIRED_OPERATIONS = {
    "start_execution": ["IT Manager", "Security Officer"],
    "data_deletion": ["Compliance Officer", "Legal"],
    "emergency_rollback": ["VP Engineering", "CTO"]
}
```

### 8.3 Audit Logging

All decommission actions logged per OWASP requirements:
```python
await audit_logger.log_decommission_action(
    flow_id=flow_id,
    action="system_shutdown",
    system_id=system_id,
    user_id=current_user.id,
    timestamp=datetime.utcnow(),
    result="success",
    ip_address=request.client.host
)
```

---

## 9. Monitoring & Observability

### 9.1 Key Metrics

Track via Grafana dashboards:
- **Flow Metrics**: Active flows, completion rate, avg duration
- **System Metrics**: Systems decommissioned, pending approvals
- **Cost Metrics**: Monthly savings, ROI, cost avoidance
- **Compliance Metrics**: Policy adherence, audit pass rate
- **Agent Metrics**: Task success rate, avg response time

### 9.2 Alerts

Configure Grafana/Prometheus alerts:
- Decommission execution failures
- Data retention policy violations
- Safety check failures
- Approval SLA breaches
- Agent execution timeouts

---

## 10. Success Criteria

### 10.1 Functional Requirements
✅ Initialize decommission flow for eligible systems
✅ AI-driven dependency analysis and risk assessment
✅ Automated data retention policy assignment
✅ Safe execution with rollback capabilities
✅ Comprehensive validation and cleanup
✅ Export reports (PDF, Excel, JSON)

### 10.2 Non-Functional Requirements
✅ **Performance**: Flow initialization < 2s
✅ **Scalability**: Support 100+ systems per flow
✅ **Availability**: 99.9% uptime (Railway deployment)
✅ **Security**: Zero cross-tenant data leakage
✅ **Compliance**: 100% audit trail coverage

### 10.3 Integration Requirements
✅ Assessment flow integration (Retire strategy)
✅ Wave execution integration (post-migration)
✅ FinOps cost tracking integration
✅ Asset inventory bidirectional sync

---

## 11. References

### ADRs
- **ADR-006**: Master Flow Orchestrator (two-table pattern)
- **ADR-012**: Flow Status Management Separation
- **ADR-024**: TenantMemoryManager Architecture

### Code References
- **Assessment Flow**: `backend/app/api/v1/endpoints/assessment_flow/`
- **Collection Flow**: `backend/app/api/v1/endpoints/collection/`
- **TenantScopedAgentPool**: `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`

### Documentation
- `/docs/analysis/Notes/000-lessons.md`: Architectural lessons
- `/docs/analysis/Notes/coding-agent-guide.md`: Implementation patterns
- `/docs/guidelines/API_REQUEST_PATTERNS.md`: API conventions

---

## 12. Appendix

### A. Sample Decommission Flow

```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "flow_name": "Q1 2025 Legacy Mainframe Retirement",
  "selected_systems": [
    {
      "id": "asset-001",
      "name": "Legacy Billing System",
      "type": "Application",
      "six_r_strategy": "Retire",
      "annual_cost": 120000
    }
  ],
  "phases": {
    "decommission_planning": {
      "status": "completed",
      "dependency_count": 3,
      "risk_level": "medium",
      "estimated_savings": 120000
    },
    "data_migration": {
      "status": "in_progress",
      "policies_assigned": 2,
      "archive_jobs": [
        {
          "data_size_gb": 847,
          "status": "in_progress",
          "progress": 75
        }
      ]
    },
    "system_shutdown": {
      "status": "pending",
      "scheduled_date": "2025-02-15T08:00:00Z",
      "includes_validation": true,
      "includes_cleanup": true
    }
  }
}
```

### B. Agent Collaboration Example

```
Planning Phase Crew Execution:

1. Dependency Analyzer Agent:
   - Query CMDB for system relationships
   - Map API dependencies via network discovery
   - Output: 3 dependent systems identified

2. Risk Assessor Agent (uses Dependency Analyzer output):
   - Evaluate impact on dependent systems
   - Check compliance requirements
   - Output: Medium risk, mitigation plan created

3. Cost Optimization Analyst:
   - Calculate infrastructure costs (servers, licenses, support)
   - Project annual savings: $120,000
   - ROI timeline: Immediate (no migration costs)
```

---

## 13. Document Change Log

### v2.1 (2025-01-14) - Final Review Corrections

**Per Final Review**: Fixed 5 remaining phase name inconsistencies in code examples.

**Status**: ✅ **APPROVED FOR IMPLEMENTATION**

#### Fixes Applied:

1. **Line 829** (Issue #1): Docstring example `"planning"` → `"decommission_planning"`
2. **Line 865** (Issue #2 - CRITICAL): Code assignment `current_phase="planning"` → `current_phase="decommission_planning"`
3. **Line 1058** (Issue #3 - CRITICAL): Next phase reference `"data_retention"` → `"data_migration"`
4. **Line 1454** (Issue #4): Frontend polling logic updated to check FlowTypeConfig phase names
5. **Lines 1796-1819** (Issue #5): Appendix JSON example updated to use correct phase names

**Impact**: Prevents runtime errors (database constraint violations, API errors, UI polling failures)

---

### v2.0 (2025-01-14) - ADR Alignment Updates

**Per Initial Review**: Aligned with ADR-027 and ADR-025 requirements.

**Version 2.0 brings the document into full compliance with:**
- **ADR-027** (Universal FlowTypeConfig Pattern)
- **ADR-025** (Child Flow Service Pattern)
- Existing FlowTypeConfig implementation (`get_decommission_flow_config()`)

### Major Changes

#### 1. Phase Naming Alignment (CRITICAL)

**Before (v1.0 - INCORRECT)**:
- `planning` → `data_retention` → `execution` → `validation` (4 phases)

**After (v2.0 - CORRECT)**:
- `decommission_planning` → `data_migration` → `system_shutdown` (3 phases)

**Rationale**: MUST match FlowTypeConfig implementation exactly per ADR-027.

#### 2. Added ADR-027 Compliance Section

New Section 2.0: "FlowTypeConfig Integration"
- Documents existing `get_decommission_flow_config()` implementation
- Explains 3-phase consolidation strategy
- Provides programmatic phase retrieval examples
- Mandates database schema alignment

#### 3. Added Child Flow Service Pattern (ADR-025)

New Section 4.0: "Child Flow Service Pattern"
- Complete `DecommissionChildFlowService` implementation
- Phase routing via `execute_phase()` method
- Integration with `TenantScopedAgentPool`
- No `crew_class` usage (deprecated pattern)

#### 4. Database Schema Updates

**Updated Column Names**:
- ❌ `planning_status` → ✅ `decommission_planning_status`
- ❌ `data_retention_status` → ✅ `data_migration_status`
- ❌ `execution_status` → ✅ `system_shutdown_status`
- ❌ `validation_status` → ❌ REMOVED (consolidated into `system_shutdown`)

**Updated CHECK Constraints**:
```sql
-- Now matches FlowTypeConfig phases exactly
CONSTRAINT valid_phase CHECK (current_phase IN (
    'decommission_planning', 'data_migration', 'system_shutdown', 'completed'
))
```

#### 5. API Code Examples

**Updated All API Responses**:
```python
# Before
"phase_progress": {
    "planning": ...,
    "data_retention": ...,
    "execution": ...,
    "validation": ...
}

# After (v2.0)
"phase_progress": {
    "decommission_planning": ...,
    "data_migration": ...,
    "system_shutdown": ...
}
```

#### 6. Frontend TypeScript Updates

**Updated Interfaces**:
```typescript
// Before
interface DecommissionFlowStatus {
  phase_progress: {
    planning: string;
    data_retention: string;
    execution: string;
    validation: string;
  };
}

// After (v2.0)
interface DecommissionFlowStatus {
  phase_progress: {
    decommission_planning: string;
    data_migration: string;
    system_shutdown: string;
  };
}
```

**Added FlowTypeConfig API Integration**:
```typescript
async getPhases(): Promise<PhaseDetail[]> {
  return apiCall('/api/v1/flow-metadata/phases/decommission');
}
```

#### 7. Agent Crew Function Names

**Updated Function Names**:
- ❌ `execute_planning_phase()` → ✅ `execute_decommission_planning_crew()`
- Added clarification comments referencing FlowTypeConfig phases

### Implementation Status

**v1.0 Status**: ⚠️ Would have caused runtime errors
- Database phase columns wouldn't match FlowTypeConfig
- API endpoints would reference non-existent phases
- Frontend would display wrong phase names
- No child_flow_service (ADR-025 violation)

**v2.0 Status**: ✅ Ready for Implementation
- Fully aligned with FlowTypeConfig
- ADR-025 compliant with child_flow_service
- ADR-027 compliant with Universal FlowTypeConfig Pattern
- Database schema matches phase definitions
- API examples use correct phase names
- Frontend correctly integrates with FlowTypeConfig API

### Verification Checklist

Before implementation, verify:
- [ ] `get_decommission_flow_config()` exists in `additional_flow_configs.py` (✅ Confirmed lines 619-749)
- [ ] Database migration uses phase names from Section 3.2
- [ ] API responses match examples in Section 5.2
- [ ] Frontend types match Section 6.1
- [ ] Child flow service implements ADR-025 pattern
- [ ] No hardcoded phase names in frontend (use `getPhases()` API)

### References

- **ADR-027**: `/docs/adr/027-universal-flow-type-config-pattern.md`
- **ADR-025**: `/docs/adr/025-collection-flow-child-service-migration.md`
- **FlowTypeConfig**: `backend/app/services/flow_configs/additional_flow_configs.py:619-749`
- **Review Document**: `/docs/planning/DECOMMISSION_FLOW_SOLUTION_REVIEW.md`

---

**END OF DOCUMENT v2.1**

**Approval Status**: ✅ Ready for Implementation

**Next Steps**:
1. Create GitHub milestone from `/docs/planning/DECOMMISSION_FLOW_MILESTONE.md`
2. Create 22 sub-issues with detailed acceptance criteria
3. Begin Phase 0: Rename existing Decommission → "Decom" (Issue #1)
4. Begin Phase 1: Database schema implementation (Issues #2-4)
3. Ensure all phase references match FlowTypeConfig throughout

For implementation questions, consult:
- `/docs/analysis/Notes/coding-agent-guide.md`
- Assessment Flow MFO migration patterns (`assessment-flow-mfo-migration-patterns` memory)
- Collection Flow reference implementation
