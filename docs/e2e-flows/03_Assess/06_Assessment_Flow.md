
# Assessment Flow: Complete Architecture and Data Flow Analysis

**Analysis Date:** November 10, 2025
**Last Updated:** November 10, 2025 (Post-6R Migration Complete)
**MFO Integration Status:** Complete (ADR-006)
**Status:** ✅ PRODUCTION READY - COMPREHENSIVE NOVEMBER 2025 UPDATE

## Executive Summary

The Assessment Flow is the enterprise-grade cloud migration assessment engine, providing:
- **Three-Phase Workflow**: Architecture Standards → Tech Debt → 6R Recommendations
- **CrewAI Agent Orchestration**: 4 specialized agents via TenantScopedAgentPool
- **MFO Integration**: All operations via Master Flow Orchestrator (ADR-006)
- **6R Strategy Authority**: Single source of truth for migration recommendations
- **Export Capabilities**: PDF/Excel/JSON assessment reports

**Critical Architecture Changes (October 2025)**:
- Deprecated standalone 6R Analysis (`/api/v1/6r/*` → HTTP 410 Gone)
- `SixRStrategyCrew` renamed to `AssessmentStrategyCrew`
- Deleted `sixr_tools` module (Issue #840)
- Assessment Flow is now the only path for 6R recommendations

---

## 1. Three-Phase Workflow Architecture

### Flow Overview
```
┌─────────────────────────────────────────────────────────────────────┐
│                   Master Flow Orchestrator (MFO)                    │
│                 Single Source of Truth for All Flows                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   ▼                ▼                ▼
         Phase 1:              Phase 2:         Phase 3:
    Architecture Standards    Tech Debt       6R Strategy
    readiness_assessor     complexity_analyst  risk_assessor +
                                               recommendation_generator
```

### Phase 1: Architecture Standards
**Purpose**: Establish cloud architecture baseline and compliance requirements

**Endpoint**: `PUT /api/v1/assessment-flow/{master_flow_id}/architecture-standards`

**CrewAI Agent**: `readiness_assessor`
- **Role**: Migration Readiness Assessment Agent
- **Tools**: `asset_intelligence`, `data_validation`, `critical_attributes`
- **Frameworks**: AWS Well-Architected Framework, Azure Cloud Adoption Framework (CAF)
- **Memory**: `False` (uses TenantMemoryManager per ADR-024)

**Agent Execution** (`execution_engine_crew_assessment/readiness_executor.py`):
```python
async def execute_readiness_assessment(
    context: AssessmentContext
) -> Dict[str, Any]:
    """
    Execute readiness assessment phase using TenantScopedAgentPool.

    Returns:
        - readiness_scores: Per-application readiness (0.0-1.0)
        - architecture_standards: Standards documentation
        - compliance_gaps: List of compliance issues
        - confidence: Agent confidence (0.0-1.0)
    """
    # Get persistent agent from pool
    agent_pool = TenantScopedAgentPool
    agent = await agent_pool.get_or_create_agent(
        agent_type="readiness_assessor",
        client_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Execute with tenant-scoped inputs
    result = await agent.execute(inputs={
        "applications": context.selected_applications,
        "critical_attributes": context.critical_attributes,
        "compliance_requirements": context.compliance_requirements
    })

    # Store learning patterns
    await tenant_memory.store_learning(
        pattern_type="readiness_assessment",
        pattern_data=result["key_patterns"]
    )

    return result
```

**Inputs**:
- Selected canonical applications
- 22 critical attributes (infrastructure, application, business, tech debt)
- Architecture standards templates
- Compliance requirements (PCI-DSS, HIPAA, SOC2, etc.)

**Outputs**:
```json
{
  "readiness_scores": {
    "ERP System": 0.85,
    "Customer Portal": 0.72
  },
  "architecture_standards": {
    "compute_patterns": ["serverless", "containers"],
    "data_patterns": ["managed_db", "object_storage"],
    "security_patterns": ["iam", "encryption_at_rest"]
  },
  "compliance_gaps": [
    {
      "application": "ERP System",
      "gap": "Missing encryption for data at rest",
      "severity": "high"
    }
  ],
  "confidence": 0.88
}
```

**Database Persistence**:
- Stored in `assessment_flows.phase_results` JSONB: `{"architecture_standards": {...}}`
- Master flow status updated in `crewai_flow_state_extensions.flow_status`

---

### Phase 2: Tech Debt Assessment
**Purpose**: Identify technical debt and modernization priorities

**Endpoint**: `PUT /api/v1/assessment-flow/{master_flow_id}/tech-debt-analysis`

**CrewAI Agent**: `complexity_analyst`
- **Role**: Migration Complexity Analysis Agent
- **Tools**: `dependency_analysis`, `asset_intelligence`, `data_validation`
- **Focus**: Code quality, last updates, test coverage, security scans
- **Memory**: `False` (ADR-024)

**Agent Execution** (`execution_engine_crew_assessment/complexity_executor.py`):
```python
async def execute_complexity_analysis(
    context: AssessmentContext
) -> Dict[str, Any]:
    """
    Execute complexity and tech debt analysis.

    Returns:
        - complexity_scores: Per-component complexity (0.0-1.0)
        - tech_debt_items: Catalog of technical debt
        - modernization_opportunities: Ranked list of improvements
        - effort_estimates: Time/cost estimates for modernization
    """
    agent = await agent_pool.get_or_create_agent(
        agent_type="complexity_analyst",
        client_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Reuse inputs from Phase 1
    architecture_standards = context.phase_results["architecture_standards"]

    result = await agent.execute(inputs={
        "applications": context.selected_applications,
        "architecture_standards": architecture_standards,
        "dependency_map": context.dependency_map,
        "code_metrics": context.code_metrics
    })

    return result
```

**Inputs** (Includes Phase 1 outputs):
- Architecture standards (from Phase 1)
- Asset technical attributes (`code_quality_score`, `test_coverage`, `last_major_update`)
- Dependency analysis results
- Security scan data (`security_scan_date`, `vulnerability_count`)

**Outputs**:
```json
{
  "complexity_scores": {
    "ERP System/Database": 0.65,
    "ERP System/API Layer": 0.82,
    "ERP System/Frontend": 0.45
  },
  "tech_debt_items": [
    {
      "component": "ERP System/Database",
      "category": "architecture",
      "issue": "Monolithic database schema",
      "impact": "high",
      "effort_days": 45
    },
    {
      "component": "ERP System/API Layer",
      "category": "code_quality",
      "issue": "Low test coverage (35%)",
      "impact": "medium",
      "effort_days": 15
    }
  ],
  "modernization_opportunities": [
    {
      "component": "ERP System/Frontend",
      "opportunity": "Migrate to React from legacy AngularJS",
      "priority": 1,
      "effort_days": 60,
      "risk": "medium"
    }
  ],
  "confidence": 0.91
}
```

**Database Persistence**:
- Appended to `assessment_flows.phase_results`: `{"tech_debt_analysis": {...}}`
- Current phase updated to `sixr_decisions`

---

### Phase 3: 6R Strategy Recommendations
**Purpose**: Determine optimal migration strategy for each application component

**Endpoint**: `PUT /api/v1/assessment-flow/{master_flow_id}/sixr-decisions`

**CrewAI Crew**: `AssessmentStrategyCrew` (formerly `SixRStrategyCrew`)
- **Agents**: `risk_assessor` + `recommendation_generator`
- **Tools**: `dependency_analysis`, `critical_attributes`, `asset_intelligence`
- **Memory**: `False` (ADR-024)

**Agent 1: risk_assessor**:
```python
async def execute_risk_assessment(
    context: AssessmentContext
) -> Dict[str, Any]:
    """
    Assess migration risks and identify mitigation strategies.

    Returns:
        - risk_assessments: Per-component risk (low/medium/high)
        - mitigation_strategies: Risk mitigation plans
        - blockers: Critical blockers preventing migration
        - dependencies: Integration complexity risks
    """
    agent = await agent_pool.get_or_create_agent(
        agent_type="risk_assessor",
        client_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Synthesize all previous phase results
    architecture = context.phase_results["architecture_standards"]
    tech_debt = context.phase_results["tech_debt_analysis"]

    result = await agent.execute(inputs={
        "applications": context.selected_applications,
        "architecture_standards": architecture,
        "tech_debt_analysis": tech_debt,
        "business_constraints": context.business_constraints,
        "resource_availability": context.resource_availability
    })

    return result
```

**Agent 2: recommendation_generator**:
```python
async def execute_recommendation_generation(
    context: AssessmentContext
) -> Dict[str, Any]:
    """
    Generate component-level 6R strategy recommendations.

    Returns:
        - component_treatments: 6R strategy per component
        - overall_strategy: Recommended application-level strategy
        - wave_hints: Move group suggestions for Planning Flow
        - rationale: Detailed decision rationale
    """
    agent = await agent_pool.get_or_create_agent(
        agent_type="recommendation_generator",
        client_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Include risk assessment results
    risk_results = context.risk_assessment_results

    result = await agent.execute(inputs={
        "applications": context.selected_applications,
        "architecture_standards": context.phase_results["architecture_standards"],
        "tech_debt_analysis": context.phase_results["tech_debt_analysis"],
        "risk_assessment": risk_results,
        "business_priorities": context.business_priorities
    })

    # Store 6R strategy to Asset model
    await update_asset_sixr_strategy(
        asset_id=component.asset_id,
        sixr_strategy=result["component_treatments"][component.id]["strategy"]
    )

    return result
```

**6R Strategies**:
1. **Rehost** (Lift-and-Shift)
   - Minimal changes, fastest time to cloud
   - Best for: Stable applications with no immediate modernization need

2. **Replatform** (Lift-Tinker-Shift)
   - Minor optimizations (managed DB, PaaS services)
   - Best for: Applications needing cloud benefits without rearchitecting

3. **Refactor** (Re-architect)
   - Redesign for cloud-native (microservices, serverless)
   - Best for: Applications with high technical debt or scalability needs

4. **Repurchase** (Replace)
   - Switch to SaaS alternative
   - Best for: Commodity applications with mature SaaS options

5. **Retire**
   - Decommission unused applications
   - Best for: Low usage, redundant, or obsolete applications

6. **Retain** (Keep On-Premises)
   - Not ready for migration
   - Best for: Compliance blockers, legacy dependencies, low cloud ROI

**Outputs**:
```json
{
  "component_treatments": [
    {
      "component_id": "erp-database",
      "component_name": "ERP System / Database",
      "sixr_strategy": "replatform",
      "rationale": "Migrate to AWS RDS PostgreSQL for managed service benefits",
      "confidence": 0.87,
      "effort_days": 30,
      "risk": "medium",
      "dependencies": ["erp-api-layer"]
    },
    {
      "component_id": "erp-api-layer",
      "component_name": "ERP System / API Layer",
      "sixr_strategy": "refactor",
      "rationale": "High tech debt (low test coverage) justifies containerization",
      "confidence": 0.82,
      "effort_days": 60,
      "risk": "high",
      "dependencies": ["erp-database", "erp-frontend"]
    }
  ],
  "overall_strategy": "replatform",
  "wave_hints": {
    "wave_1": ["erp-database"],
    "wave_2": ["erp-api-layer", "erp-frontend"]
  },
  "confidence": 0.85,
  "rationale": "Phased migration minimizes risk while achieving cloud benefits"
}
```

**Database Persistence**:
- Completed in `assessment_flows.phase_results`: `{"sixr_decisions": {...}}`
- Master flow status: `completed`
- Asset.six_r_strategy updated for each component

---

## 2. MFO Integration Architecture (ADR-006)

### Two-Table Pattern (ADR-012)

**Master Table**: `crewai_flow_state_extensions`
- **Purpose**: Lifecycle management (running, paused, completed)
- **Scope**: All flow types (discovery, assessment, collection, planning, etc.)
- **Primary Key**: `flow_id` (UUID)

**Child Table**: `assessment_flows`
- **Purpose**: Operational state (phases, UI data, agent results)
- **Scope**: Assessment flow only
- **Foreign Key**: `master_flow_id` references `crewai_flow_state_extensions.flow_id`

**Why Two Tables?**:
- Master flow: High-level coordination across all flows
- Child flow: Domain-specific details for UI and agent execution
- Atomic transactions: Both created in single transaction
- Frontend uses **child flow** status for decisions

### Flow Creation Pattern

**Endpoint**: `POST /api/v1/master-flows`

**Request**:
```json
{
  "flow_type": "assessment",
  "client_account_id": "00000000-0000-0000-0000-000000000001",
  "engagement_id": "00000000-0000-0000-0000-000000000002",
  "user_id": "user-123",
  "configuration": {
    "selected_application_ids": ["app-uuid-1", "app-uuid-2"]
  }
}
```

**Backend** (`mfo_integration/create.py`):
```python
async def create_assessment_flow(
    flow_config: FlowCreateRequest,
    db: AsyncSession
) -> AssessmentFlowResponse:
    """Create assessment flow via MFO atomic transaction."""
    flow_id = uuid4()

    async with db.begin():  # Atomic transaction
        # Step 1: Create master flow (MFO registry)
        master_flow = CrewAIFlowStateExtensions(
            flow_id=flow_id,
            flow_type="assessment",
            flow_status="running",  # High-level lifecycle
            client_account_id=flow_config.client_account_id,
            engagement_id=flow_config.engagement_id,
            user_id=flow_config.user_id,
            flow_configuration=flow_config.configuration,
            flow_persistence_data={}
        )
        db.add(master_flow)
        await db.flush()  # Make flow_id available for FK

        # Step 2: Create child flow (operational state)
        child_flow = AssessmentFlow(
            flow_id=flow_id,  # Same UUID, not FK
            master_flow_id=master_flow.flow_id,  # FK relationship
            client_account_id=flow_config.client_account_id,
            engagement_id=flow_config.engagement_id,
            status="initialized",  # Operational status
            current_phase="architecture_standards",
            progress=0.0,
            phase_results={},
            configuration=flow_config.configuration
        )
        db.add(child_flow)

        # Step 3: Pre-compute readiness data (PR #600)
        resolver = AssessmentApplicationResolver(db, context)
        child_flow.application_asset_groups = await resolver.resolve_assets_to_applications()
        child_flow.readiness_summary = await resolver.calculate_readiness_summary()

        await db.commit()  # Single atomic commit

    return AssessmentFlowResponse.from_orm(child_flow)
```

### Phase Execution Pattern

**Endpoint**: `POST /api/v1/master-flows/{flow_id}/resume`

**Request**:
```json
{
  "phase": "tech_debt_analysis",
  "inputs": {
    "architecture_standards": { ... }
  }
}
```

**Backend** (`mfo_integration/lifecycle.py`):
```python
async def resume_assessment_flow(
    flow_id: UUID,
    phase_input: PhaseInput,
    db: AsyncSession
) -> AssessmentFlowResponse:
    """Resume assessment flow and execute next phase."""

    # Get child flow by master_flow_id
    child_flow = await assessment_repo.get_by_master_flow_id(flow_id)
    if not child_flow:
        raise ValueError(f"Assessment flow not found for master {flow_id}")

    # Route to phase executor via TenantScopedAgentPool
    executor = AssessmentFlowExecutor(db, context)
    result = await executor.execute_phase(
        phase_name=phase_input.phase,
        phase_input=phase_input.inputs,
        assessment_flow=child_flow
    )

    # Update child flow state
    child_flow.phase_results[phase_input.phase] = result
    child_flow.current_phase = _get_next_phase(phase_input.phase)
    child_flow.progress = _calculate_progress(child_flow.current_phase)

    # Update master flow status
    if child_flow.current_phase == "completed":
        master_flow = await master_repo.get_by_id(flow_id)
        master_flow.flow_status = "completed"

    await db.commit()
    return AssessmentFlowResponse.from_orm(child_flow)
```

---

## 3. CrewAI Agent Architecture

### TenantScopedAgentPool (ADR-015)

**Purpose**: Singleton agent pool per tenant, eliminating 94% performance overhead of per-call crew instantiation

**Implementation** (`tenant_scoped_agent_pool.py`):
```python
class TenantScopedAgentPool:
    """Persistent agent pool scoped by tenant."""
    _pools: Dict[str, Dict[str, Agent]] = {}  # {tenant_key: {agent_type: agent}}

    @classmethod
    async def initialize_tenant_pool(
        cls,
        client_id: str,
        engagement_id: str
    ) -> None:
        """Initialize agent pool for tenant."""
        tenant_key = f"{client_id}:{engagement_id}"

        if tenant_key not in cls._pools:
            cls._pools[tenant_key] = {}
            logger.info(f"Initialized agent pool for tenant {tenant_key}")

    @classmethod
    async def get_or_create_agent(
        cls,
        agent_type: str,
        client_id: str,
        engagement_id: str
    ) -> Agent:
        """Get existing agent or create new one."""
        tenant_key = f"{client_id}:{engagement_id}"
        await cls.initialize_tenant_pool(client_id, engagement_id)

        if agent_type not in cls._pools[tenant_key]:
            # Create agent from AGENT_TYPE_CONFIGS
            config = AGENT_TYPE_CONFIGS[agent_type]
            agent = Agent(
                role=config["role"],
                goal=config["goal"],
                backstory=config["backstory"],
                tools=_load_tools(config["tools"]),
                memory=False  # Per ADR-024
            )
            cls._pools[tenant_key][agent_type] = agent
            logger.info(f"Created {agent_type} agent for tenant {tenant_key}")

        return cls._pools[tenant_key][agent_type]
```

**Agent Pool Constants** (`agent_pool_constants.py`):
```python
AGENT_TYPE_CONFIGS = {
    "readiness_assessor": {
        "role": "Migration Readiness Assessment Agent",
        "goal": "Assess application readiness for cloud migration using AWS Well-Architected Framework and Azure CAF",
        "backstory": "Expert in cloud architecture patterns with 15+ years experience...",
        "tools": ["asset_intelligence", "data_validation", "critical_attributes"],
        "memory": False  # Per ADR-024: Use TenantMemoryManager
    },
    "complexity_analyst": {
        "role": "Migration Complexity Analysis Agent",
        "goal": "Identify technical debt and modernization opportunities",
        "backstory": "Software architect specializing in legacy system modernization...",
        "tools": ["dependency_analysis", "asset_intelligence", "data_validation"],
        "memory": False
    },
    "risk_assessor": {
        "role": "Migration Risk Assessment Agent",
        "goal": "Evaluate migration risks and develop mitigation strategies",
        "backstory": "Risk management specialist with expertise in cloud migrations...",
        "tools": ["dependency_analysis", "critical_attributes", "asset_intelligence"],
        "memory": False
    },
    "recommendation_generator": {
        "role": "Migration Recommendation Generation Agent",
        "goal": "Synthesize assessments into actionable 6R migration recommendations",
        "backstory": "Cloud strategy consultant with track record of successful migrations...",
        "tools": ["asset_intelligence", "dependency_analysis", "critical_attributes"],
        "memory": False
    }
}
```

### Memory Management (ADR-024)

**CrewAI Memory: DISABLED**
```python
# ❌ NEVER use CrewAI built-in memory
crew = Crew(
    agents=[agent],
    tasks=[task],
    memory=True  # BANNED - Causes 401 errors with DeepInfra
)

# ✅ ALWAYS use TenantMemoryManager
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)

await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,  # or CLIENT, GLOBAL
    pattern_type="readiness_assessment",
    pattern_data={
        "common_gaps": ["security_compliance", "network_documentation"],
        "typical_readiness_score": 0.78,
        "architecture_patterns": ["microservices", "event_driven"]
    }
)
```

**Why TenantMemoryManager?**:
- Multi-tenant isolation (engagement/client/global scopes)
- PostgreSQL + pgvector (native to our stack)
- Enterprise features: data classification, audit trails, encryption
- No DeepInfra/OpenAI embedding conflicts

---

## 4. Frontend Integration

### Assessment Flow Hook (`useAssessmentFlow.ts`)

```typescript
export const useAssessmentFlow = (masterFlowId: string) => {
  const { data: flowStatus } = useQuery({
    queryKey: ['assessment-flow-status', masterFlowId],
    queryFn: () => assessmentFlowApi.getStatus(masterFlowId),
    enabled: !!masterFlowId,
    refetchInterval: (data) => {
      if (!data) return false;
      if (data.flow_status === 'completed') return false;
      return data.flow_status === 'running' ? 5000 : 15000;  // Polling
    }
  });

  const resumeFlow = useMutation({
    mutationFn: (phaseInput: PhaseInput) =>
      assessmentFlowApi.resumeFlow(masterFlowId, phaseInput),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-flow-status']);
    }
  });

  const acceptRecommendations = useMutation({
    mutationFn: (recommendations: SixRRecommendations) =>
      assessmentFlowApi.acceptRecommendations(masterFlowId, recommendations),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-flow-status']);
      navigate(`/planning/wave-planning?flowId=${masterFlowId}`);
    }
  });

  return { flowStatus, resumeFlow, acceptRecommendations };
};
```

### API Client (`assessmentFlowApi.ts`)

```typescript
class AssessmentFlowApiClient {
  async createFlow(config: AssessmentFlowConfig): Promise<AssessmentFlowResponse> {
    return await apiCall('/api/v1/master-flows', {
      method: 'POST',
      body: JSON.stringify({
        flow_type: 'assessment',
        ...config
      })
    });
  }

  async getStatus(masterFlowId: string): Promise<FlowStatusResponse> {
    return await apiCall(`/api/v1/master-flows/${masterFlowId}/status`, {
      method: 'GET'
    });
  }

  async resumeFlow(
    masterFlowId: string,
    phaseInput: PhaseInput
  ): Promise<AssessmentFlowResponse> {
    return await apiCall(`/api/v1/master-flows/${masterFlowId}/resume`, {
      method: 'POST',
      body: JSON.stringify(phaseInput)
    });
  }

  async acceptRecommendations(
    masterFlowId: string,
    recommendations: SixRRecommendations
  ): Promise<void> {
    return await apiCall(
      `/api/v1/assessment-flow/${masterFlowId}/sixr-decisions/accept`,
      {
        method: 'POST',
        body: JSON.stringify(recommendations)
      }
    );
  }

  async exportReport(
    masterFlowId: string,
    format: 'pdf' | 'excel' | 'json'
  ): Promise<Blob> {
    return await apiCall(
      `/api/v1/assessment-flow/${masterFlowId}/export?format=${format}`,
      { method: 'GET' }
    );
  }
}
```

---

## 5. Export Functionality

### Endpoint: `GET /api/v1/assessment-flow/{flow_id}/export`

**Query Parameters**:
- `format`: `pdf` | `excel` | `json`

**Implementation** (`assessment_flow/export.py`):
```python
@router.get("/{flow_id}/export")
async def export_assessment_report(
    flow_id: UUID,
    format: str = Query(..., enum=["pdf", "excel", "json"]),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
) -> Response:
    """Export complete assessment report."""

    # Get assessment flow with all phase results
    flow = await assessment_repo.get_by_flow_id(flow_id)
    if not flow:
        raise HTTPException(404, "Assessment flow not found")

    # Generate report based on format
    if format == "pdf":
        report_bytes = await generate_pdf_report(flow)
        return Response(
            content=report_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=assessment-{flow_id}.pdf"}
        )
    elif format == "excel":
        report_bytes = await generate_excel_report(flow)
        return Response(
            content=report_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=assessment-{flow_id}.xlsx"}
        )
    else:  # json
        return JSONResponse(content={
            "flow_id": str(flow.flow_id),
            "architecture_standards": flow.phase_results.get("architecture_standards"),
            "tech_debt_analysis": flow.phase_results.get("tech_debt_analysis"),
            "sixr_decisions": flow.phase_results.get("sixr_decisions"),
            "readiness_summary": flow.readiness_summary,
            "application_groups": flow.application_asset_groups
        })
```

**PDF Report Sections**:
1. Executive Summary
2. Readiness Dashboard (from Phase 1)
3. Architecture Standards (from Phase 1)
4. Technical Debt Analysis (from Phase 2)
5. 6R Recommendations (from Phase 3)
6. Wave Planning Hints
7. Risk Assessment and Mitigation

---

## 6. Troubleshooting Guide

| Issue | Diagnostic | Fix |
|-------|-----------|-----|
| **Flow Creation Fails** | Check `POST /api/v1/master-flows` response | Verify `selected_application_ids` exist in Collection flow |
| **Agent Execution Hangs** | Check backend logs: `docker logs migration_backend --tail 100` | Verify TenantScopedAgentPool initialization; check DeepInfra API keys |
| **Phase Results Not Saving** | Check `assessment_flows.phase_results` JSONB field | Ensure atomic transaction completed; check DB connection pool |
| **6R Recommendations Wrong** | Review `iteration_history` in agent logs | Check if architecture standards + tech debt inputs are complete |
| **Export Fails** | Check file format parameter | PDF/Excel generation requires `reportlab` and `openpyxl` packages |
| **Frontend 404 Errors** | Check browser Network tab for endpoint | Verify using `/api/v1/master-flows/*` not deprecated `/api/v1/6r/*` |

---

## 7. Key Architectural References

**ADRs**:
- ADR-006: Master Flow Orchestrator (MFO integration)
- ADR-012: Flow Status Management Separation (two-table pattern)
- ADR-015: Persistent Multi-Tenant Agent Architecture (TenantScopedAgentPool)
- ADR-024: TenantMemoryManager Architecture (CrewAI memory disabled)

**Serena Memories**:
- `assessment-flow-mfo-migration-patterns` - MFO integration patterns
- `assessment_flow_agent_execution_implementation_2025_10` - CrewAI agent implementation
- `assessment-collection-flow-linking` - Collection → Assessment transition
- `architectural_patterns` - Two-table pattern and seven-layer architecture

**Backend Files**:
- `backend/app/api/v1/endpoints/assessment_flow_router.py` - Main router
- `backend/app/api/v1/endpoints/assessment_flow/mfo_integration/` - MFO integration
- `backend/app/services/flow_orchestration/execution_engine_crew_assessment/` - Agent executors
- `backend/app/services/crewai_flows/crews/assessment_strategy_crew/` - AssessmentStrategyCrew
- `backend/app/services/persistent_agents/agent_pool_constants.py` - Agent configurations
- `backend/app/models/assessment_flow/core_models.py` - Assessment flow model

**Database Migrations**:
- `111_remove_sixr_analysis_tables.py` - Archived 6R Analysis tables (October 2025)
- `094_assessment_data_model_refactor.py` - Assessment Flow enhancement (October 2025)

---

## 8. Success Metrics

**Performance**:
- Agent pool initialization: < 500ms (first time per tenant)
- Phase execution: 2-5 minutes per phase (depends on application count)
- Total assessment: 10-20 minutes for typical engagement (5-10 applications)

**Accuracy**:
- 6R recommendation confidence: > 85% (per agent self-assessment)
- Tech debt identification: > 90% coverage of critical issues
- Architecture compliance: 100% of standards validated

**Integration**:
- MFO registration: 100% of flows registered in `crewai_flow_state_extensions`
- Multi-tenant isolation: 100% queries scoped by client_account_id + engagement_id
- Export success rate: > 99% for all formats (PDF/Excel/JSON)
