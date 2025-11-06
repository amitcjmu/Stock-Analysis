# Decommission Flow - Architecture Summary

**Last Updated:** 2025-11-06
**Purpose:** Quick reference guide for understanding the Decommission flow architecture before making code changes

## 🚧 Implementation Status

**Current Version**: In Development for v2.5.0
**Target Release**: April 2025 (12-week implementation, January-April 2025)
**Milestone**: [GitHub Issue #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952)
**Overall Progress**: ~40% Complete (Foundation & Basic Flow)

### ✅ Completed Components
- Database schema and migrations (migration 120_create_decommission_tables.py)
- SQLAlchemy models and repository layer (DecommissionFlow, DecommissionPlan, etc.)
- Basic API endpoints (`/api/v1/decommission-flow/*`)
- MFO integration structure (two-table pattern with atomic transactions)
- Child flow service framework (DecommissionChildFlowService per ADR-025)
- FlowTypeConfig integration (3 phases: decommission_planning, data_migration, system_shutdown)
- Basic UI pages at `/decommission/*` routes
- Flow initialization and system selection UI

### ⚠️ In Progress (Partial Implementation)
- Agent integration with TenantScopedAgentPool (7 agents defined, execution partially implemented)
- UI refinements and bug fixes:
  - [Bug #960](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/960): Planning page not displaying selected systems (data in DB, display issue)
  - [Bug #961](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/961): Export page flow_id context handling
- Phase execution logic (stub implementations exist)
- Data retention and archival workflows (models exist, execution pending)

### ❌ Not Yet Implemented
- Complete agent crew execution (stub implementations with TODO comments)
- Assessment flow integration for 6R "Retire" strategy ([Issue #947](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/milestone/23))
- Wave execution integration for post-migration decommission ([Issue #948](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/milestone/23))
- E2E Playwright testing ([Issue #949](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/milestone/23))
- Full validation and safety checks for system shutdown phase
- Archive job execution with S3 integration
- Comprehensive API documentation and user guide
- Rollback mechanism implementation

**NOTE**: This documentation describes the INTENDED architecture and design. Not all features described here are fully implemented yet. Refer to the milestone issue #952 and sub-issues for current implementation status.

## 🤝 Human-in-the-Loop Architecture (CRITICAL)

**IMPORTANT**: The Decommission flow is **NOT a fully automated process**. It is designed as a **human-in-the-loop workflow** that guides users through a structured decommission process while requiring manual inputs, approvals, and decision-making at every phase.

### Why Not Fully Automated?

1. **Business Decisions Required**: Decommissioning systems involves strategic business decisions that cannot be automated:
   - Which systems to retire and when
   - Cost-benefit analysis and ROI justification
   - Risk tolerance and mitigation strategies
   - Timeline and resource allocation

2. **Approval Workflows Mandatory**: Enterprise decommissioning requires stakeholder approvals:
   - Management sign-off before proceeding
   - Compliance team reviews for regulatory requirements
   - Finance approvals for budget allocation
   - Legal reviews for contract terminations

3. **Manual Data Collection**: Critical information not available from automated sources:
   - Actual decommission costs (vendors, contractors, labor)
   - Business impact metrics (revenue, productivity)
   - ROI calculations (savings realized vs. projected)
   - External dependencies (third-party services, contracts)

4. **Artifact Management**: Documentation must be collected and stored:
   - Supporting documents (migration reports, test results)
   - Approval emails and sign-offs
   - Cost breakdowns and financial justifications
   - Compliance attestations
   - Post-decommission verification reports

5. **Execution Coordination**: Manual coordination with teams:
   - Infrastructure teams for shutdown execution
   - Application teams for testing and validation
   - Data teams for archival and migration
   - Vendor management for contract closure

### Current Implementation vs. Full Human-in-Loop

**What EXISTS Today (v2.5.0 Development):**
- ✅ Basic flow structure (phases, state tracking)
- ✅ Database models for plans, policies, jobs
- ✅ API endpoints for CRUD operations
- ✅ UI pages for viewing and basic interaction

**What's MISSING for Complete Human-in-Loop:**
- ❌ **Manual input forms** for progress updates at each phase
- ❌ **Approval workflow UI** (request, track, approve/reject)
- ❌ **Artifact upload & storage** (documents, files, links)
- ❌ **User input for cost calculations** (actual costs, ROI metrics)
- ❌ **Timeline adjustment UI** (delays, blockers, resource changes)
- ❌ **Risk assessment forms** (user-provided risk analysis)
- ❌ **Stakeholder notification system** (email, alerts)
- ❌ **Audit trail UI** (who did what, when, why)
- ❌ **Integration with external systems** (ticketing, finance, contracts)
- ❌ **Progress dashboard** (real-time status across all decommissions)

### Impact on Development

Developers working on Decommission flow MUST understand:

1. **AI Agents are ASSISTANTS, not executors**: Agents provide recommendations, analysis, and guidance - they DO NOT execute decommissions automatically.

2. **User input is REQUIRED, not optional**: Every phase requires user confirmation, input, and decision-making.

3. **State tracking is MANUAL**: Users must mark phases as complete, not the system.

4. **Artifact storage is ESSENTIAL**: Without document storage, the flow is incomplete.

5. **Approval workflows are MANDATORY**: Cannot proceed without explicit user approval at checkpoints.

### Future Enhancements Required

To make this a fully functional human-in-the-loop workflow, these features MUST be added:

**Phase 1 (High Priority):**
- Manual input forms for each phase
- Artifact upload/storage (S3 + metadata)
- Basic approval workflow (request → approve/reject)
- User input for cost/ROI calculations
- Progress tracking dashboard

**Phase 2 (Medium Priority):**
- Stakeholder notification system
- Timeline adjustment UI
- Risk assessment forms with scoring
- Integration with ticketing systems
- Audit trail visualization

**Phase 3 (Nice to Have):**
- Email integration for approvals
- Finance system integration for costs
- Contract management integration
- Automated reminders/escalations
- Reporting and analytics dashboard

**See**: `/docs/e2e-flows/05_Decommission/FUTURE_ENHANCEMENTS.md` (comprehensive enhancement roadmap)

## 🎯 Overview

The Decommission flow is a multi-phase, safety-focused process that safely retires IT systems while preserving critical data and maintaining compliance. It uses the Master Flow Orchestrator (MFO) pattern to coordinate decommissioning operations through three distinct phases: planning, data migration, and system shutdown.

**Key Objectives:**
- Safe system retirement with dependency analysis
- Compliance-driven data retention and archival
- Cost savings tracking and reporting
- Audit trail for all decommission operations
- Rollback capability during critical phases

## 🏗️ Core Architecture

### Master Flow Orchestrator (MFO) Integration (CRITICAL)

The Decommission flow is fully integrated with the **Master Flow Orchestrator** architecture per ADR-006:

1. **Master Flow Orchestrator (MFO)**
   - **Primary identifier**: `master_flow_id` is used for ALL operations
   - ALL flow operations (create, resume, pause, delete) go through MFO
   - **Unified API**: `/api/v1/master-flows/*` endpoints
   - Single source of truth for flow lifecycle management

2. **Master Flow Table** (`crewai_flow_state_extensions`)
   - Orchestration and coordination hub
   - Flow lifecycle status (running, paused, completed)
   - Stores comprehensive flow state and metadata
   - **Primary Key**: `flow_id` (this IS the master_flow_id)

3. **Child Flow Table** (`decommission_flows`)
   - Decommission-specific operational tracking (internal implementation detail)
   - Links to master via `master_flow_id` foreign key
   - Contains phase completion booleans for UI display
   - Stores decommission strategy, system selections, and metrics
   - **NOT exposed to API consumers** - internal state only

⚠️ **CRITICAL**: The `master_flow_id` is the **primary identifier** for all Decommission flow operations. Child flow IDs are internal implementation details and should never be used directly by API consumers or UI components.

### Key Components

- **MasterFlowOrchestrator**: Coordinates all flows, manages lifecycle
- **DecommissionChildFlowService**: Manages decommission-specific operations (per ADR-025)
- **DecommissionFlowRepository**: Data access layer with tenant scoping
- **FlowTypeConfig**: Phase definitions per ADR-027 (replaces crew_class pattern)
- **Background Execution**: Async phase execution via agent pools

## 📊 Flow Phases (Per ADR-027 FlowTypeConfig)

### 1. **Decommission Planning** (`decommission_planning`)
- Analyzes system dependencies and relationships
- Assesses decommission risks and mitigation strategies
- Calculates potential cost savings
- Requires approval workflows
- **Estimated Duration**: 45 minutes
- [Details →](./02_Decommission_Planning.md)

### 2. **Data Migration** (`data_migration`)
- Applies data retention policies
- Creates and executes archive jobs
- Verifies data integrity and accessibility
- Ensures compliance with retention requirements
- **Estimated Duration**: 120 minutes
- [Details →](./03_Data_Migration.md)

### 3. **System Shutdown** (`system_shutdown`)
- Performs pre-shutdown validation
- Executes graceful service shutdown
- Removes infrastructure resources
- Validates post-decommission state
- Creates audit trail
- **Estimated Duration**: 60 minutes
- [Details →](./04_System_Shutdown.md)

## 🔄 Data Flow Sequence (MFO-Aligned)

```
1. User selects systems for decommission → POST /api/v1/decommission-flow/initialize
2. Backend creates flow through MasterFlowOrchestrator (atomic transaction):
   - MFO.create_flow() → returns master_flow_id
   - DecommissionFlow record (references master_flow_id)
   - Master flow state (crewai_flow_state_extensions)
   - Child flow record (decommission_flows) - internal tracking only
3. MFO initiates BackgroundExecutionService with master_flow_id
4. DecommissionChildFlowService executes phases via persistent agents
5. ALL phase updates go through MFO using master_flow_id
6. UI polls MFO endpoints with master_flow_id for updates
```

## 💾 Database Schema

### Essential Tables

#### Primary Tables
- **`decommission_flows`** - Child flow table (operational state)
  - Links to master via `master_flow_id` foreign key
  - Tracks phase progress with dedicated status columns
  - Stores system selections and decommission strategy
  - Aggregates metrics (savings, compliance score)

- **`crewai_flow_state_extensions`** - Master flow orchestration
  - Lifecycle management (running, paused, completed)
  - Single source of truth for flow state
  - Tracks current phase and metadata

#### Supporting Tables
- **`decommission_plans`** - Per-system decommission plans
  - Dependencies, risk assessment, scheduling
  - Approval workflows and tracking

- **`data_retention_policies`** - Compliance-driven retention policies
  - Retention periods and compliance requirements
  - Data classification and storage locations

- **`archive_jobs`** - Data archival job tracking
  - Archive status and progress
  - Integrity verification and checksums

- **`decommission_execution_logs`** - Audit trail
  - Phase execution history
  - Safety checks and rollback points

- **`decommission_validation_checks`** - Post-decommission validation
  - Validation categories and results
  - Critical issue tracking

### Foreign Key Relationships (MFO-Aligned)

```sql
-- Primary relationships through master_flow_id
decommission_flows.master_flow_id → crewai_flow_state_extensions.flow_id (master_flow_id)
decommission_plans.flow_id → decommission_flows.flow_id
archive_jobs.flow_id → decommission_flows.flow_id
data_retention_policies (tenant-scoped, no FK to flows)

-- Key Point: crewai_flow_state_extensions.flow_id IS the master_flow_id
-- All external references use this as the primary identifier
```

### Phase Status Columns (ALIGNED WITH ADR-027)

```sql
-- Phase progress tracking (matches FlowTypeConfig phase names)
decommission_planning_status VARCHAR(50) DEFAULT 'pending'
decommission_planning_completed_at TIMESTAMP WITH TIME ZONE

data_migration_status VARCHAR(50) DEFAULT 'pending'
data_migration_completed_at TIMESTAMP WITH TIME ZONE

system_shutdown_status VARCHAR(50) DEFAULT 'pending'
system_shutdown_started_at TIMESTAMP WITH TIME ZONE
system_shutdown_completed_at TIMESTAMP WITH TIME ZONE
```

## 🛠️ Critical Code Patterns

### ✅ Correct Patterns

```python
# MFO Flow Creation (Primary Pattern)
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

async with db.begin():
    mfo = MasterFlowOrchestrator(db, context)
    master_flow_id = await mfo.create_flow(
        flow_type="decommission",
        configuration=config,
        atomic=True  # MUST be true for proper FK handling
    )
    await db.flush()  # Makes ID available for child flow

    # Create child flow with master reference
    child_flow_service = DecommissionChildFlowService(db, context)
    await child_flow_service.create_child_flow(
        master_flow_id=master_flow_id,
        selected_system_ids=system_ids
    )
    await db.commit()

# Always use master_flow_id for operations
await mfo.execute_phase(master_flow_id, phase_input)
await mfo.get_flow_status(master_flow_id)
await mfo.pause_flow(master_flow_id)

# UUID Serialization (prevents JSON errors)
configuration = convert_uuids_to_str({...})

# Phase Execution (ADR-025 Pattern)
child_flow_service = DecommissionChildFlowService(db, context)
result = await child_flow_service.execute_phase(
    flow_id=master_flow_id,
    phase_name="decommission_planning",
    phase_input={"system_ids": [...]}
)
```

### ❌ Incorrect Patterns

```python
# DON'T use child flow IDs for operations
decommission_flow_id = get_decommission_flow_id()  # WRONG!
await some_operation(decommission_flow_id)         # WRONG!

# DON'T bypass MFO for flow operations
await direct_database_update(flow_id)              # WRONG!

# DON'T reference child flow IDs in APIs/UI
return {"decommission_flow_id": child_id}          # WRONG!

# DON'T use old crew_class pattern (deprecated per ADR-025)
crew = Crew(agents=[...])                          # WRONG!
await crew.kickoff()                               # WRONG!

# Always use master_flow_id instead
return {"master_flow_id": master_flow_id}          # CORRECT!

# Always use child_flow_service
service = DecommissionChildFlowService(db, context)  # CORRECT!
await service.execute_phase(...)                     # CORRECT!
```

### ⚠️ Common Mistakes to Avoid

```python
# MISTAKE 1: Phase name mismatch
current_phase = "planning"  # ❌ WRONG - doesn't match FlowTypeConfig

current_phase = "decommission_planning"  # ✅ CORRECT

# MISTAKE 2: Bypassing tenant scoping
query = select(DecommissionFlow).where(flow_id == id)  # ❌ WRONG

repository = DecommissionFlowRepository(db, client_id, engagement_id)  # ✅ CORRECT
flow = await repository.get_by_flow_id(id)

# MISTAKE 3: Creating crew instances per call (94% performance loss)
crew = Crew(agents=[agent])  # ❌ WRONG - creates new crew each time

agent_pool = TenantScopedAgentPool(context)  # ✅ CORRECT - persistent agents
agent = await agent_pool.get_agent('decommission')

# MISTAKE 4: Missing atomic transaction for master+child creation
master_flow = create_master_flow()
await db.commit()  # ❌ WRONG - child creation may fail
child_flow = create_child_flow()

async with db.begin():  # ✅ CORRECT - atomic
    master_flow = create_master_flow()
    await db.flush()
    child_flow = create_child_flow(master_flow.id)
    await db.commit()
```

## 📋 Implementation Checklist

Before modifying Decommission flow code:

### MFO Integration
- [ ] **CRITICAL**: Use master_flow_id for ALL external operations
- [ ] Route all flow operations through MasterFlowOrchestrator
- [ ] Never expose child flow IDs to API consumers or UI
- [ ] Use `/api/v1/master-flows/*` endpoints for flow operations
- [ ] Ensure child flow records are created for internal tracking

### ADR Compliance
- [ ] Use DecommissionChildFlowService (ADR-025) - NO crew_class
- [ ] Phase names match FlowTypeConfig (ADR-027) exactly
- [ ] Follow two-table pattern (ADR-006, ADR-012)
- [ ] Use atomic transactions for data consistency
- [ ] Handle UUID serialization for JSON storage

### Testing & Verification
- [ ] Test full flow lifecycle using only master_flow_id
- [ ] Verify UI uses master_flow_id for all flow references
- [ ] Ensure multi-tenant scoping on all queries
- [ ] Test rollback capability during planning/migration phases
- [ ] Verify audit trail creation

## 🔗 Quick References

| Topic | Details | Key File |
|-------|---------|----------|
| Flow Overview | [01_Overview.md](./01_Overview.md) | `src/pages/Decommission.tsx` |
| Planning Phase | [02_Decommission_Planning.md](./02_Decommission_Planning.md) | `backend/app/services/child_flow_services/decommission.py` |
| Data Migration | [03_Data_Migration.md](./03_Data_Migration.md) | `backend/app/models/decommission_flow/policy_models.py` |
| System Shutdown | [04_System_Shutdown.md](./04_System_Shutdown.md) | `backend/app/models/decommission_flow/audit_models.py` |
| FlowTypeConfig | Phase definitions | `backend/app/services/flow_configs/decommission_flow_config.py` |
| Frontend API | Service methods | `src/lib/api/decommissionFlowService.ts` |
| Database Schema | Migration 120 | `backend/alembic/versions/120_create_decommission_tables.py` |

## 🚨 Critical Architectural Decisions

### ADR-006: Master Flow Orchestrator Pattern
- All flows MUST register with `crewai_flow_state_extensions` table
- Child flows (like `decommission_flows`) are internal implementation details
- master_flow_id is the primary identifier for all external operations

### ADR-025: Child Flow Service Pattern
- FlowTypeConfig MUST include `child_flow_service` field (not crew_class)
- DecommissionChildFlowService handles all phase execution
- Uses TenantScopedAgentPool for persistent agents (no Crew per call)

### ADR-027: Universal FlowTypeConfig Pattern
- Phase names MUST match FlowTypeConfig definitions exactly
- Database schema phase columns MUST align with FlowTypeConfig
- Frontend MUST query `/api/v1/flow-metadata/phases` for phase definitions

### ADR-012: Flow Status Management Separation
- **Master Flow**: High-level lifecycle (running, paused, completed)
- **Child Flow**: Operational decisions (phases, validations, UI state)
- Frontend and agents MUST use child flow status for operational decisions

## ⚡ Emergency Fixes

### If Decommission Flow is Stuck:
1. Check `crewai_flow_state_extensions` for master flow status
2. Verify `decommission_flows` record exists (if not, that's the problem)
3. Check DecommissionChildFlowService phase execution logs
4. Review background execution service status

### If Phase Transitions Fail:
1. Verify phase names match FlowTypeConfig exactly
2. Check that phase status columns exist in database
3. Ensure atomic transactions are being used
4. Review tenant scoping in all queries

### If Agent Execution Fails:
1. Verify TenantScopedAgentPool is being used (not Crew instantiation)
2. Check that DecommissionChildFlowService is registered in FlowTypeConfig
3. Review agent pool initialization with correct tenant context
4. Ensure crew_class is NOT specified (deprecated pattern)

## 🔐 Security & Compliance Notes

### Multi-Tenant Isolation
- ALL queries MUST include `client_account_id` and `engagement_id`
- Repository layer enforces tenant scoping automatically
- Never bypass ContextAwareRepository for queries

### Audit Trail
- All decommission operations logged in `decommission_execution_logs`
- Safety checks recorded with pass/fail status
- Rollback points tracked for recovery

### Data Retention Compliance
- Retention policies enforce regulatory requirements (GDPR, SOX, HIPAA)
- Archive jobs verify data integrity with checksums
- Encryption required for archived data

### Approval Workflows
- Decommission plans require stakeholder approval
- Point-of-no-return warning before system shutdown
- Rollback available until shutdown phase begins

## 📈 Performance Considerations

### Persistent Agent Pool Pattern
- Uses TenantScopedAgentPool to avoid 94% performance loss
- Agents initialized once per tenant, reused across phases
- NO per-call Crew instantiation (deprecated pattern)

### Atomic Transactions
- Master and child flows created in single transaction
- Phase updates use flush() before child flow creation
- Prevents orphaned records and FK constraint violations

### Efficient Queries
- Repository methods use tenant-scoped indexes
- Phase status queries filter at database level
- Array containment queries for system ID lookups

## 🎓 Learning from Other Flows

### Similarities with Assessment Flow
- Both use MFO two-table pattern
- Both have multi-phase progression
- Both require agent-based analysis
- Both generate reports and recommendations

### Key Differences
- Decommission is **irreversible after shutdown phase**
- Requires **approval workflows** for safety
- Generates **audit trail** for compliance
- Tracks **cost savings** and compliance metrics
- Supports **rollback** during planning and migration phases

---

**Remember**: The Decommission flow handles critical system retirement operations. Breaking it can result in data loss, compliance violations, or premature system shutdowns. Always test thoroughly and maintain audit trails.

**Before Making Changes**:
1. Read [ADR-006](../../adr/006-master-flow-orchestrator.md) (MFO Pattern)
2. Read [ADR-025](../../adr/025-child-flow-service-pattern.md) (Child Flow Service)
3. Read [ADR-027](../../adr/027-universal-flow-type-config-pattern.md) (FlowTypeConfig)
4. Review existing implementation in `backend/app/services/child_flow_services/decommission.py`
5. Test with docker containers (localhost:8081, NOT 3000)

---

## 📚 Additional References

### Planning & Design Documents
- [Solution Document v2.1](/docs/planning/DECOMMISSION_FLOW_SOLUTION.md) - Comprehensive solution (APPROVED with minor fixes)
- [Final Review](/docs/planning/DECOMMISSION_FLOW_FINAL_REVIEW.md) - v2.0 approval document with identified issues
- [Solution Review](/docs/planning/DECOMMISSION_FLOW_SOLUTION_REVIEW.md) - Initial architecture validation
- [Milestone Details](/docs/planning/DECOMMISSION_FLOW_MILESTONE.md) - 12-week implementation plan with 22 sub-issues

### GitHub Tracking
- [Milestone Issue #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952) - Parent milestone issue (185 story points)
- [Milestone v2.5.0](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/milestone/23) - All 22 sub-issues
- [Active Bugs](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues?q=is:issue+is:open+label:bug+decommission) - Current bug tracker
  - [Bug #960](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/960) - Planning page selected systems display
  - [Bug #961](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/961) - Export page flow context

### Architectural Decision Records (ADRs)
- [ADR-027](/docs/adr/027-universal-flow-type-config-pattern.md) - FlowTypeConfig pattern (MUST follow for phase names)
- [ADR-025](/docs/adr/025-child-flow-service-pattern.md) - Child flow service pattern (replaces crew_class)
- [ADR-006](/docs/adr/006-master-flow-orchestrator.md) - MFO two-table pattern (master_flow_id primary)
- [ADR-012](/docs/adr/012-flow-status-management-separation.md) - Status management separation
- [ADR-024](/docs/adr/024-tenant-memory-manager-architecture.md) - TenantMemoryManager for agent memory (memory=False)

### Implementation Progress Tracking

**Phase Breakdown (from Milestone)**:
- Phase 0 (Prep): Week 1 - 3 SP - ✅ COMPLETE
- Phase 1 (Database): Weeks 1-2 - 29 SP - ✅ COMPLETE
- Phase 2 (Backend API): Weeks 3-4 - 31 SP - ✅ MOSTLY COMPLETE
- Phase 3 (Agents): Weeks 5-6 - 39 SP - ⚠️ IN PROGRESS (stub implementations)
- Phase 4 (Frontend): Weeks 7-8 - 61 SP - ⚠️ IN PROGRESS (2 known bugs)
- Phase 5 (Integration): Weeks 9-10 - 29 SP - ❌ NOT STARTED
- Phase 6 (Documentation): Weeks 11-12 - 10 SP - ⚠️ IN PROGRESS (this doc)

### Key Implementation Files

**Backend**:
- FlowTypeConfig: `backend/app/services/flow_configs/additional_flow_configs.py:619-749`
- Child Flow Service: `backend/app/services/child_flows/decommission_child_flow_service.py`
- Repository: `backend/app/repositories/decommission_flow_repository.py`
- Models: `backend/app/models/decommission_flow/`
- API Endpoints: `backend/app/api/v1/endpoints/decommission_flow/`
- Database Migration: `backend/alembic/versions/120_create_decommission_tables.py`

**Frontend**:
- API Service: `src/lib/api/decommissionFlowService.ts`
- React Hooks: `src/hooks/decommission/useDecommissionFlow.ts`
- Pages: `src/pages/decommission/` (Overview, Planning, DataMigration, Shutdown, Export)
- Types: `src/types/api/decommission.ts`

### Related Documentation
- [Discovery Flow](../01_Discovery/) - Asset discovery and inventory
- [Collection Flow](../02_Collection/) - Detailed data collection
- [Assessment Flow](../03_Assess/) - 6R strategy recommendations (integrates with Decommission)
- [Planning Flow](../04_Plan/) - Migration wave planning
