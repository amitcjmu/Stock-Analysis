# Decommission Flow Documentation

**Last Updated:** 2025-11-06
**Flow Version:** 2.0.0 (In Development)
**Target Release:** v2.5.0 (April 2025)

## 🚧 Implementation Status

**IMPORTANT**: This flow is currently **IN DEVELOPMENT** (v2.5.0 milestone). Documentation describes the intended architecture - not all features are fully implemented yet.

**Progress**: ~40% Complete (Foundation & Basic Flow)
**Milestone**: [GitHub Issue #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952) (185 SP, 22 sub-issues)
**Timeline**: 12 weeks (January-April 2025)

### Current Status:
- ✅ Database schema, models, basic API endpoints
- ⚠️ Agent execution partially implemented (stubs exist)
- ⚠️ UI has known bugs ([#960](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/960), [#961](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/961))
- ❌ Assessment/Wave integration not yet implemented
- ❌ E2E testing pending

**For detailed status**, see [Implementation Status section](./00_Decommission_Flow_Summary.md#-implementation-status) in the Summary document.

## 🤝 Understanding the Human-in-the-Loop Architecture

**CRITICAL**: The Decommission flow is designed as a **human-in-the-loop workflow**, NOT a fully automated process. This means:

- ✅ AI agents provide **recommendations and analysis**
- ✅ System provides **structure and guidance**
- ❌ System CANNOT **execute decommissions automatically**
- ❌ System CANNOT **make business decisions for you**

### What This Means for Users

1. **Manual Input Required**: You must provide information at each phase (costs, risks, timelines)
2. **Approvals Mandatory**: Stakeholders must approve before proceeding
3. **Documents Required**: You must upload supporting artifacts
4. **Progress Tracking Manual**: You must mark phases complete after real-world execution

### What This Means for Developers

1. **Build for User Input**: Every phase needs forms for user-provided data
2. **Implement Approval Workflows**: Cannot proceed without explicit approvals
3. **Add Artifact Storage**: Must store supporting documents
4. **No Auto-Execution**: System guides, users execute

### Missing Features for Complete Human-in-Loop

See [FUTURE_ENHANCEMENTS.md](./FUTURE_ENHANCEMENTS.md) for the 285 story points of work required to make this a fully functional human-in-the-loop workflow.

**Critical Missing Features:**
- Manual input forms (40 SP)
- Approval workflow system (35 SP)
- Artifact upload/storage (25 SP)
- Cost/ROI input system (15 SP)
- Progress tracking UI (20 SP)

**Estimated Time to Completion**: 14 additional months beyond current milestone

## 📚 Quick Start

This directory contains comprehensive end-to-end documentation for the Decommission Flow, which safely retires IT systems while preserving critical data and maintaining compliance.

### New to Decommission Flow?

1. **Start here**: [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md) - Architecture overview and critical patterns
2. **Then read**: [01_Overview.md](./01_Overview.md) - Dashboard and flow initiation
3. **Review phases**: Phase documents (02, 03, 04) for detailed implementation

### Making Code Changes?

1. **MUST READ FIRST**: [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md) - Architectural decisions
2. **Check phase docs**: Find the phase you're modifying
3. **Follow patterns**: Use ✅ Correct and ❌ Incorrect code examples
4. **Reference ADRs**:
   - [ADR-006](../../adr/006-master-flow-orchestrator.md) - MFO Pattern
   - [ADR-025](../../adr/025-child-flow-service-pattern.md) - Child Flow Service
   - [ADR-027](../../adr/027-universal-flow-type-config-pattern.md) - FlowTypeConfig

## 📖 Document Structure

### [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md)
**Architecture overview and quick reference guide**

- MFO integration architecture (master_flow_id patterns)
- Two-table pattern (master + child flows)
- Flow phases overview
- Database schema
- Critical code patterns (✅ Correct vs ❌ Incorrect)
- Implementation checklist
- Emergency fixes

**Read this BEFORE making any code changes!**

### [01_Overview.md](./01_Overview.md)
**Dashboard, system selection, and flow initiation**

- Decommission dashboard components
- Eligible systems query and display
- System selection with dependency warnings
- Strategy configuration (cost savings, risk reduction, compliance)
- Flow initialization via MFO
- API endpoints and data flow
- UI components breakdown
- Polling strategy (NO WebSockets)

**Topics**: Dashboard, System Selection, Initialization, Metrics

### [02_Decommission_Planning.md](./02_Decommission_Planning.md)
**Phase 1: Decommission Planning (45 minutes)**

- Agent-based execution (Dependency Analyzer, Risk Assessor, Cost Analyst)
- CrewAI task flow and agent configuration
- Dependency analysis and risk assessment
- Cost savings calculation
- Approval workflows
- Planning results UI
- Phase output and database storage
- Approval endpoint implementation

**Topics**: Dependencies, Risk Assessment, Cost Analysis, Approvals

### [03_Data_Migration.md](./03_Data_Migration.md)
**Phase 2: Data Migration (120 minutes)**

- Data retention policies (GDPR, SOX, HIPAA compliance)
- Archive job creation and execution
- Encryption and data security
- Integrity verification with checksums
- Archive job status tracking
- Policy assignment logic
- Migration progress UI
- Error handling and retry logic

**Topics**: Retention Policies, Archive Jobs, Compliance, Data Security

### [04_System_Shutdown.md](./04_System_Shutdown.md)
**Phase 3: System Shutdown (60 minutes) - IRREVERSIBLE**

- Pre-validation checks (critical gates)
- Graceful shutdown sequence
- Infrastructure cleanup
- Post-validation verification
- Execution logs and audit trail
- Final metrics and cost savings
- Completion UI and audit reports

**Topics**: Validation, Shutdown Sequence, Cleanup, Audit Trail

## 🔄 Flow Progression

```
User Action                    Phase                           Duration
───────────────────────────────────────────────────────────────────────

Select Systems                 ┌──────────────────┐
Configure Strategy       ───▶  │   Initialization │
Initialize Flow                └──────────────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
Agent Analysis             ──▶ │ Decommission     │          45 min
User Approval                  │ Planning         │
                               └──────────────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
Apply Retention Policies   ──▶ │ Data             │         120 min
Execute Archive Jobs           │ Migration        │
Verify Integrity               └──────────────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
Pre-Validation             ──▶ │ System           │          60 min
Graceful Shutdown              │ Shutdown         │
Infrastructure Cleanup         │ ⚠️ IRREVERSIBLE  │
Post-Validation                └──────────────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │   Completed      │
                               │   Audit Report   │
                               └──────────────────┘
```

## 🏗️ Key Architectural Patterns

### Master Flow Orchestrator (MFO) Pattern

```
                    ┌─────────────────────────────┐
                    │  MasterFlowOrchestrator     │
                    │  (Single Entry Point)       │
                    └─────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
        ┌───────────▼──────────┐  ┌──────────▼──────────┐
        │ crewai_flow_state_   │  │ decommission_flows  │
        │ extensions           │  │ (child flow)        │
        │ (master flow)        │  │                     │
        │                      │  │ - operational state │
        │ - lifecycle status   │  │ - phase tracking    │
        │ - master_flow_id     │◀─│ - master_flow_id FK │
        └──────────────────────┘  └─────────────────────┘
                 │
                 │ References
                 ▼
        ┌─────────────────────┐
        │ decommission_plans  │
        │ archive_jobs        │
        │ execution_logs      │
        │ validation_checks   │
        └─────────────────────┘
```

**CRITICAL**: Always use `master_flow_id` for external operations, never child flow IDs.

### Three-Phase Execution Model

```python
# Per ADR-027 FlowTypeConfig
phases = [
    {
        "name": "decommission_planning",
        "duration_minutes": 45,
        "can_rollback": True,
        "requires_approval": True
    },
    {
        "name": "data_migration",
        "duration_minutes": 120,
        "can_rollback": True,
        "requires_approval": False
    },
    {
        "name": "system_shutdown",
        "duration_minutes": 60,
        "can_rollback": False,  # ⚠️ IRREVERSIBLE
        "requires_approval": False
    }
]
```

### Child Flow Service Pattern (ADR-025)

```python
# ✅ CORRECT: Use DecommissionChildFlowService
service = DecommissionChildFlowService(db, context)
result = await service.execute_phase(
    flow_id=master_flow_id,
    phase_name="decommission_planning",
    phase_input={"system_ids": [...]}
)

# ❌ WRONG: Don't use crew_class (deprecated)
crew = Crew(agents=[...])  # 94% performance loss
await crew.kickoff()
```

## 🗂️ File Structure

```
05_Decommission/
├── README.md                           # This file
├── 00_Decommission_Flow_Summary.md     # Architecture overview ⭐ START HERE
├── 01_Overview.md                      # Dashboard and initiation
├── 02_Decommission_Planning.md         # Phase 1: Planning (45 min)
├── 03_Data_Migration.md                # Phase 2: Data Migration (120 min)
└── 04_System_Shutdown.md               # Phase 3: Shutdown (60 min) ⚠️ IRREVERSIBLE
```

## 🔗 Related Documentation

### Architecture Decision Records (ADRs)
- [ADR-006](../../adr/006-master-flow-orchestrator.md) - Master Flow Orchestrator Pattern
- [ADR-012](../../adr/012-flow-status-management-separation.md) - Flow Status Separation
- [ADR-025](../../adr/025-child-flow-service-pattern.md) - Child Flow Service Pattern
- [ADR-027](../../adr/027-universal-flow-type-config-pattern.md) - Universal FlowTypeConfig

### Planning Documents
- [Decommission Flow Solution](../../planning/DECOMMISSION_FLOW_SOLUTION.md) - Original design
- [Decommission Flow Milestone](../../planning/DECOMMISSION_FLOW_MILESTONE.md) - Implementation phases
- [Solution Review](../../planning/DECOMMISSION_FLOW_SOLUTION_REVIEW.md) - Architecture validation

### Code References
- **Backend Service**: `backend/app/services/child_flow_services/decommission.py`
- **Repository**: `backend/app/repositories/decommission_flow_repository.py`
- **Models**: `backend/app/models/decommission_flow/`
- **FlowTypeConfig**: `backend/app/services/flow_configs/decommission_flow_config.py`
- **API Endpoints**: `backend/app/api/v1/endpoints/decommission_flow/`
- **Frontend Service**: `src/lib/api/decommissionFlowService.ts`
- **Frontend Types**: `src/types/api/decommission.ts`
- **Database Migration**: `backend/alembic/versions/120_create_decommission_tables.py`

### Other Flow Documentation
- [Discovery Flow](../01_Discovery/) - Asset discovery and inventory
- [Collection Flow](../02_Collection/) - Detailed data collection
- [Assessment Flow](../03_Assess/) - 6R strategy recommendations
- [Planning Flow](../04_Plan/) - Migration wave planning

## ⚠️ Critical Warnings

### 🚨 MUST READ Before Coding

1. **master_flow_id is PRIMARY identifier** - Never use child flow IDs in APIs/UI
2. **Phase names MUST match FlowTypeConfig** - `decommission_planning`, `data_migration`, `system_shutdown`
3. **NO WebSockets** - Use HTTP polling (Railway deployment requirement)
4. **snake_case ONLY** - All fields must use snake_case (NOT camelCase)
5. **Multi-tenant scoping REQUIRED** - Every query needs client_account_id + engagement_id
6. **System Shutdown is IRREVERSIBLE** - No rollback after shutdown phase begins
7. **Use child_flow_service, NOT crew_class** - Per ADR-025 (94% performance improvement)
8. **Atomic transactions for master+child creation** - Use flush() before child flow creation

### Common Mistakes

```python
# ❌ WRONG: Phase name doesn't match FlowTypeConfig
current_phase = "planning"  # Should be "decommission_planning"

# ❌ WRONG: Using child flow ID
return {"decommission_flow_id": child_flow.id}

# ❌ WRONG: Creating Crew per call
crew = Crew(agents=[...])  # 94% performance loss

# ❌ WRONG: Bypassing tenant scoping
query = select(DecommissionFlow).where(flow_id == id)

# ✅ CORRECT: Match FlowTypeConfig
current_phase = "decommission_planning"

# ✅ CORRECT: Use master_flow_id
return {"master_flow_id": master_flow_id}

# ✅ CORRECT: Persistent agent pool
service = DecommissionChildFlowService(db, context)

# ✅ CORRECT: Tenant-scoped repository
repo = DecommissionFlowRepository(db, client_id, engagement_id)
```

## 🎓 Learning Path

### For New Developers
1. Read [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md) - Understand architecture
2. Review [ADR-006](../../adr/006-master-flow-orchestrator.md) - Learn MFO pattern
3. Study [01_Overview.md](./01_Overview.md) - See flow initiation
4. Walk through phase docs (02, 03, 04) - Understand phase execution
5. Review code in `backend/app/services/child_flow_services/decommission.py`

### For Experienced Developers
1. Skim [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md) - Refresh on patterns
2. Jump to relevant phase doc - Find implementation details
3. Check code patterns section - See correct examples
4. Reference ADRs as needed - Understand architectural decisions

### For QA/Testing
1. Read [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md) - Understand flow
2. Review each phase doc - Learn expected behavior
3. Check "Testing Checklist" sections - Create test cases
4. Test error scenarios - Verify error handling
5. Validate multi-tenant isolation - Security testing

## 📊 Documentation Metrics

- **Total Pages**: 5 (Summary + Overview + 3 Phase Docs)
- **Total Lines**: ~3,500 lines
- **Code Examples**: 50+ examples
- **API Endpoints**: 15+ documented
- **Database Tables**: 6 tables
- **Phase Duration**: 225 minutes (45 + 120 + 60)
- **Agents Used**: 10 CrewAI agents
- **Last Updated**: 2025-11-06

## 🔍 Finding Information

### By Topic

| Topic | Document | Section |
|-------|----------|---------|
| MFO Integration | Summary | Core Architecture |
| System Selection | Overview | System Selection |
| Dependency Analysis | Planning Phase | Agent-Based Execution |
| Risk Assessment | Planning Phase | Risk Assessor Agent |
| Cost Analysis | Planning Phase | Cost Analyst Agent |
| Retention Policies | Data Migration | Data Retention Policies |
| Archive Jobs | Data Migration | Archive Jobs |
| Validation Checks | System Shutdown | Pre/Post-Validation |
| Shutdown Sequence | System Shutdown | Graceful Service Shutdown |
| Audit Trail | System Shutdown | Execution Logs |
| Error Handling | All Phase Docs | Error Handling sections |
| API Endpoints | Overview + Phase Docs | API Calls sections |
| Database Schema | Summary | Database Schema |
| Frontend UI | All Docs | Frontend UI sections |

### By Role

| Role | Key Documents |
|------|---------------|
| Backend Developer | Summary, Phase Docs (Backend sections) |
| Frontend Developer | Summary, Overview, Phase Docs (UI sections) |
| DevOps/SRE | Summary (Database Schema, Emergency Fixes) |
| QA/Testing | All Docs (Testing Checklist sections) |
| Product Manager | Summary, Overview (Phase progression) |
| Compliance Officer | Data Migration, System Shutdown (Audit sections) |

## 📊 Tracking Implementation Progress

### Milestone & Issues
- **Parent Issue**: [#952 - Decommission Flow Implementation](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952)
- **Milestone View**: [v2.5.0 Milestone](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/milestone/23)
- **All Sub-Issues**: View in milestone to see 22 implementation tasks
- **Active Bugs**: [Decommission bugs](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues?q=is:issue+is:open+label:bug+decommission)

### Contributing Guidelines
When working on Decommission flow features:

1. **Check Current Status**: Review [Implementation Status](#-implementation-status) above
2. **Find Your Issue**: Look in [milestone #23](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/milestone/23)
3. **Read Architecture First**: Start with [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md)
4. **Follow ADRs**: Comply with ADR-027 (FlowTypeConfig), ADR-025 (Child Flow Service), ADR-006 (MFO)
5. **Test Thoroughly**: Use Docker environment (localhost:8081), run pre-commit hooks
6. **Update Documentation**: Mark features as implemented, update status sections
7. **Link PRs to Issues**: Reference sub-issue numbers in PR descriptions

### Implementation Phases (from Milestone)
| Phase | Weeks | Story Points | Status |
|-------|-------|--------------|--------|
| 0: Preparation | Week 1 | 3 | ✅ Complete |
| 1: Database Foundation | Weeks 1-2 | 29 | ✅ Complete |
| 2: Backend API & MFO | Weeks 3-4 | 31 | ✅ Mostly Complete |
| 3: Child Flow Service & Agents | Weeks 5-6 | 39 | ⚠️ In Progress |
| 4: Frontend Implementation | Weeks 7-8 | 61 | ⚠️ In Progress |
| 5: Integration & Testing | Weeks 9-10 | 29 | ❌ Not Started |
| 6: Documentation & Launch | Weeks 11-12 | 10 | ⚠️ In Progress |

## 💬 Support

- **Questions?** Check [00_Decommission_Flow_Summary.md](./00_Decommission_Flow_Summary.md) first
- **Code issues?** Review code pattern examples in each doc
- **Architecture questions?** Read referenced ADRs
- **Emergency?** See "Emergency Fixes" in Summary doc
- **Implementation questions?** Check [milestone issue #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952)

---

**Remember**: Decommission flow handles IRREVERSIBLE system retirement. This feature is still in development - not production-ready. Always test thoroughly and follow established patterns to prevent data loss or premature shutdowns.
