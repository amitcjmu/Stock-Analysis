# Decommission Flow - Phase 1: Decommission Planning

**Last Updated:** 2025-11-10
**Phase Name**: `decommission_planning` (per ADR-027 FlowTypeConfig)
**Estimated Duration**: 45 minutes
**Status**: Documentation updated to reflect November 2025 implementation reality

> **⚠️ IMPLEMENTATION STATUS**: This phase is **PARTIALLY IMPLEMENTED**. Core structure exists with **7 specialized CrewAI agents defined** in `agent_configs.py`. All agents use ADR-024 pattern (`memory_enabled=False` with TenantMemoryManager). Agent execution has basic child_flow_service implementation. Full AI-powered dependency analysis, risk assessment, and cost calculation are still in development. MFO transaction patterns fixed (November 2025). UI display bug ([Issue #960](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/960)) **RESOLVED Nov 2025**. See [Milestone #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952) for current status.
>
> **⚠️ HUMAN-IN-THE-LOOP WORKFLOW**: This phase REQUIRES manual user input, approvals, and artifact collection. The current implementation provides database structure and API endpoints, but does NOT include:
> - User input forms for manual data entry
> - Approval workflow UI
> - Artifact upload/storage
> - Progress tracking UI
>
> See [FUTURE_ENHANCEMENTS.md](./FUTURE_ENHANCEMENTS.md) for required additions.

## 📋 Phase Overview

The Decommission Planning phase analyzes systems selected for retirement, assesses risks, identifies dependencies, and generates comprehensive decommission plans. This phase uses AI agents to ensure safe, cost-effective system decommissioning.

**Phase Objectives:**
1. Analyze system dependencies and relationships
2. Assess decommission risks and mitigation strategies
3. Calculate potential cost savings
4. Generate approval workflows
5. Create per-system decommission plans
6. Pause for user review and approval

**Phase Output:**
- Dependency graph showing system relationships
- Risk assessment with mitigation strategies
- Cost savings estimates (annual and lifecycle)
- Decommission timeline and scheduling recommendations
- Approval requirements per system

## 👤 Manual Input Requirements

This phase REQUIRES user input and cannot be fully automated:

### User Must Provide:
1. **Dependency Confirmation**: Review AI-suggested dependencies, add missing ones, correct errors
2. **Risk Assessment**: Validate AI risk scores, add business-specific risks
3. **Cost Inputs**:
   - Actual decommission costs (vendors, contractors, labor)
   - Expected cost savings (hardware, licenses, maintenance)
   - Hidden costs (data migration, training, support)
4. **Timeline Inputs**:
   - Preferred shutdown date
   - Blackout periods (holidays, busy seasons)
   - Resource availability
5. **Stakeholder Approvals**:
   - Management sign-off on plan
   - Finance approval for budget
   - Compliance approval for regulatory requirements

### Artifacts to Collect:
- Dependency diagrams (if not auto-generated)
- Risk mitigation plans (documents)
- Financial justification (spreadsheets, emails)
- Approval emails/documents
- Stakeholder sign-off forms

### Current Implementation Status:
- ✅ AI agents provide recommendations (STUB)
- ❌ User input forms NOT implemented
- ❌ Artifact upload NOT implemented
- ❌ Approval workflow NOT implemented

## 🏗️ Architecture

### Agent-Based Execution (ADR-025 Pattern)

```python
# backend/app/services/child_flow_services/decommission.py
async def _execute_decommission_planning(
    self,
    child_flow,
    phase_input: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute decommission planning phase using TenantScopedAgentPool.

    Agents Used (STUB - Basic execution implemented, full AI analysis pending):
    1. Dependency Analyzer (STUB): Maps system dependencies
    2. Risk Assessor (STUB): Evaluates decommission risks
    3. Cost Analyst (STUB): Calculates potential savings

    Per ADR-025: Uses DecommissionAgentPool (NOT per-call Crew instantiation)
    """
    # Update phase status to running
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="decommission_planning",
        phase_status="running"
    )

    # Get agent pool (persistent, tenant-scoped)
    agent_pool = TenantScopedAgentPool(
        client_account_id=self.context.client_account_id,
        engagement_id=self.context.engagement_id
    )

    # Execute planning crew
    planning_crew = agent_pool.get_decommission_planning_crew()
    result = await planning_crew.execute(
        system_ids=child_flow.selected_system_ids,
        strategy=child_flow.decommission_strategy
    )

    # Store results in database
    await self._store_planning_results(child_flow, result)

    # Update phase status to completed
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="decommission_planning",
        phase_status="completed"
    )

    # Pause flow for user approval (ADR-012: child flow controls operational pauses)
    await self.repository.update_status(
        flow_id=child_flow.flow_id,
        status="paused_for_approval",
        current_phase="decommission_planning"
    )

    return {
        "status": "success",
        "phase": "decommission_planning",
        "paused_for_approval": True,
        "next_phase": "data_migration",
        "dependency_graph": result.dependency_graph,
        "risk_assessment": result.risk_assessment,
        "estimated_savings": result.estimated_savings
    }
```

### CrewAI Agent Configuration (November 2025 Reality)

**Implementation**: `backend/app/services/agents/decommission/agent_pool/agent_configs.py`

All agents use **ADR-024 pattern**: `memory_enabled=False`, with TenantMemoryManager for enterprise-grade learning.

**Agents Used in Planning Phase** (4 out of 7 total agents):

#### 1. System Analysis Agent
```python
{
    "role": "System Dependency Analysis Specialist",
    "goal": "Identify all system dependencies and impact zones to prevent downstream failures",
    "backstory": """Expert in enterprise architecture with 15+ years analyzing system dependencies.
        Creates comprehensive dependency maps to ensure safe decommissioning.""",
    "tools": ["cmdb_query", "network_discovery", "api_dependency_mapper"],
    "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager
    "llm_config": {
        "provider": "deepinfra",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    }
}
```

#### 2. Dependency Mapper Agent
```python
{
    "role": "System Relationship Mapping Specialist",
    "goal": "Map complex system relationships and integration points",
    "backstory": """20+ years in IT architecture, specialized in mapping complex integrations.
        Creates dependency maps used by Fortune 500 companies.""",
    "tools": [
        "dependency_graph_builder",
        "integration_analyzer",
        "critical_path_finder"
    ],
    "memory_enabled": False,  # Per ADR-024
    "llm_config": {
        "provider": "deepinfra",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    }
}
```

#### 3. Data Retention Agent
```python
{
    "role": "Data Retention and Archival Compliance Specialist",
    "goal": "Ensure data retention compliance and secure archival before decommissioning",
    "backstory": """Compliance expert with deep knowledge of GDPR, SOX, HIPAA, PCI-DSS.
        15+ years managing enterprise data archival for regulated industries.""",
    "tools": ["compliance_policy_lookup", "data_classifier", "archive_calculator"],
    "memory_enabled": False,  # Per ADR-024
    "llm_config": {
        "provider": "deepinfra",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    }
}
```

#### 4. Compliance Agent
```python
{
    "role": "Regulatory Compliance Validation Specialist",
    "goal": "Ensure all decommission activities meet regulatory compliance requirements",
    "backstory": """Regulatory compliance officer with expertise in multi-jurisdiction frameworks.
        Works closely with legal teams to ensure zero compliance gaps.""",
    "tools": [
        "compliance_checker",
        "regulatory_validator",
        "audit_trail_generator"
    ],
    "memory_enabled": False,  # Per ADR-024
    "llm_config": {
        "provider": "deepinfra",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    }
}
```

**Note**: Planning phase uses agents 1-4. Agents 5-7 (Shutdown Orchestrator, Validation, Rollback) are used in later phases.

### CrewAI Task Flow

```python
# Task 1: Dependency Analysis
dependency_task = Task(
    description="""
    Analyze dependencies for systems: {system_ids}

    For each system:
    1. Identify direct dependencies (what depends on this system)
    2. Identify upstream dependencies (what this system depends on)
    3. Map network connections and API integrations
    4. Flag critical dependencies that cannot be decommissioned

    Output dependency graph in JSON format.
    """,
    expected_output="JSON dependency graph with nodes and edges",
    agent=dependency_analyzer
)

# Task 2: Risk Assessment
risk_task = Task(
    description="""
    Assess decommission risks for systems: {system_ids}

    For each system evaluate:
    1. Data sensitivity and retention requirements
    2. Compliance obligations (GDPR, SOX, HIPAA)
    3. Business impact if decommissioned
    4. Rollback complexity

    Assign risk level: Low, Medium, High, Critical
    Provide mitigation strategies for Medium+ risks.
    """,
    expected_output="JSON risk assessment per system with mitigation strategies",
    agent=risk_assessor,
    context=[dependency_task]  # Needs dependency info
)

# Task 3: Cost Analysis
cost_task = Task(
    description="""
    Calculate cost savings from decommissioning systems: {system_ids}

    Calculate:
    1. Current annual costs (compute, storage, licensing, support)
    2. Projected annual savings after decommission
    3. One-time decommission costs (data migration, archival, labor)
    4. Net savings over 1, 3, 5 years
    5. ROI and payback period

    Consider strategy priority: {strategy_priority}
    """,
    expected_output="JSON cost analysis with annual savings and ROI",
    agent=cost_analyst,
    context=[dependency_task, risk_task]
)
```

## 📊 Data Flow

### Input to Phase

```python
phase_input = {
    "system_ids": ["uuid1", "uuid2", ...],  # From flow initialization
    "strategy": {
        "priority": "cost_savings",
        "execution_mode": "phased",
        "rollback_enabled": True
    }
}
```

### Agent Processing

1. **Dependency Analyzer** queries:
   - `asset_dependencies` table for known dependencies
   - CMDB for network connections
   - Application logs for API usage patterns
   - Configuration files for hardcoded references

2. **Risk Assessor** analyzes:
   - Data classification from Discovery flow
   - Compliance requirements from metadata
   - Business criticality scores from Assessment flow
   - Historical incident data

3. **Cost Analyst** calculates:
   - Current costs from asset inventory
   - Licensing costs from vendor databases
   - Support costs from ticketing systems
   - Projected savings based on strategy

### Phase Output (Stored in `decommission_plans` table)

```python
{
    "plan_id": "uuid",
    "flow_id": "decommission-flow-uuid",
    "system_id": "asset-uuid",
    "system_name": "Legacy CRM System",
    "system_type": "Application",

    # Dependency Analysis Results
    "dependencies": {
        "direct_dependencies": [
            {"asset_id": "uuid", "asset_name": "Customer Portal", "dependency_type": "API"}
        ],
        "upstream_dependencies": [
            {"asset_id": "uuid", "asset_name": "Customer Database", "dependency_type": "Database"}
        ],
        "network_connections": [
            {"ip_address": "10.0.1.50", "port": 443, "protocol": "HTTPS"}
        ]
    },

    # Risk Assessment Results
    "risk_level": "High",
    "risk_factors": [
        {
            "category": "Data Sensitivity",
            "severity": "High",
            "description": "Contains PII and financial records"
        },
        {
            "category": "Business Impact",
            "severity": "Medium",
            "description": "Used by 50 daily active users"
        }
    ],
    "mitigation_strategies": [
        {
            "risk": "Data Loss",
            "strategy": "Complete data migration to archive before decommission",
            "cost": 5000,
            "duration_days": 7
        },
        {
            "risk": "Service Disruption",
            "strategy": "Phased decommission with gradual user migration",
            "cost": 2000,
            "duration_days": 14
        }
    ],

    # Cost Analysis Results
    "cost_analysis": {
        "current_annual_cost": 45000,
        "projected_annual_savings": 42000,
        "one_time_decommission_cost": 7000,
        "net_savings_1_year": 35000,
        "net_savings_3_years": 119000,
        "net_savings_5_years": 203000,
        "roi_percentage": 500,
        "payback_period_months": 2
    },

    # Scheduling
    "scheduled_date": "2025-03-01T00:00:00Z",
    "estimated_duration_hours": 48,
    "priority": "High",

    # Approvals
    "requires_approvals": ["CIO", "Compliance Officer", "Finance Director"],
    "approval_status": "pending",
    "approved_by": None,
    "approved_at": None
}
```

## 🎨 Frontend UI

### Planning Results Page

**URL**: `/decommission/flow/{flow_id}/planning`

**Components**:

```typescript
<DecommissionPlanningView>
  <PlanSummary>
    <SystemCount>{plan_count} systems selected</SystemCount>
    <TotalSavings>${total_savings} annual savings</TotalSavings>
    <RiskDistribution>
      <High>{high_risk_count}</High>
      <Medium>{medium_risk_count}</Medium>
      <Low>{low_risk_count}</Low>
    </RiskDistribution>
  </PlanSummary>

  <DependencyVisualization>
    <DependencyGraph nodes={systems} edges={dependencies} />
    <Legend />
  </DependencyVisualization>

  <SystemPlansList>
    {plans.map(plan => (
      <SystemPlanCard key={plan.plan_id}>
        <SystemHeader>
          <SystemName>{plan.system_name}</SystemName>
          <RiskBadge level={plan.risk_level} />
          <SavingsBadge>${plan.cost_analysis.projected_annual_savings}</SavingsBadge>
        </SystemHeader>

        <DependenciesSection>
          <Title>Dependencies</Title>
          {plan.dependencies.direct_dependencies.length > 0 && (
            <WarningMessage>
              {plan.dependencies.direct_dependencies.length} systems depend on this
            </WarningMessage>
          )}
          <DependencyList dependencies={plan.dependencies} />
        </DependenciesSection>

        <RiskSection>
          <Title>Risks & Mitigation</Title>
          {plan.risk_factors.map(risk => (
            <RiskItem key={risk.category}>
              <RiskCategory>{risk.category}</RiskCategory>
              <RiskSeverity level={risk.severity}>{risk.severity}</RiskSeverity>
              <RiskDescription>{risk.description}</RiskDescription>
            </RiskItem>
          ))}
          <MitigationStrategies strategies={plan.mitigation_strategies} />
        </RiskSection>

        <CostAnalysisSection>
          <Title>Cost Analysis</Title>
          <CurrentCost>${plan.cost_analysis.current_annual_cost}/year</CurrentCost>
          <ProjectedSavings>${plan.cost_analysis.projected_annual_savings}/year</ProjectedSavings>
          <ROI>{plan.cost_analysis.roi_percentage}% ROI</ROI>
          <PaybackPeriod>{plan.cost_analysis.payback_period_months} months</PaybackPeriod>
        </CostAnalysisSection>

        <ApprovalSection>
          <RequiredApprovals>
            {plan.requires_approvals.map(role => (
              <ApprovalBadge key={role} status="pending">{role}</ApprovalBadge>
            ))}
          </RequiredApprovals>
        </ApprovalSection>
      </SystemPlanCard>
    ))}
  </SystemPlansList>

  <ActionButtons>
    <RejectButton onClick={handleReject}>
      Reject Plan
    </RejectButton>
    <ModifyButton onClick={handleModify}>
      Modify Selection
    </ModifyButton>
    <ApproveButton onClick={handleApprove}>
      Approve & Continue to Data Migration
    </ApproveButton>
  </ActionButtons>
</DecommissionPlanningView>
```

### API Calls During Planning Phase

```typescript
// 1. Get planning results
const { data: planningData } = useQuery({
  queryKey: ['decommission-planning', flowId],
  queryFn: () => apiCall(`/decommission-flow/${flowId}/planning-results`),
  enabled: !!flowId,
  staleTime: 60000,  // Planning results don't change frequently
});

// 2. Approve plan and proceed to data migration
const approvePlan = useMutation({
  mutationFn: async (flowId: string) => {
    return apiCall(`/decommission-flow/${flowId}/approve-planning`, {
      method: 'POST',
      body: JSON.stringify({
        approved_by: currentUser.email,
        approval_notes: approvalNotes
      })
    });
  },
  onSuccess: () => {
    toast.success('Decommission plan approved. Starting data migration phase.');
    queryClient.invalidateQueries(['decommission-flow-status', flowId]);
  }
});
```

## 🔧 Backend Implementation Details

### Approval Endpoint

```python
# backend/app/api/v1/endpoints/decommission_flow/approvals.py
@router.post("/{flow_id}/approve-planning")
async def approve_decommission_planning(
    flow_id: str,
    approval: PlanningApprovalRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    mfo: MasterFlowOrchestrator = Depends(get_mfo)
) -> DecommissionFlowResponse:
    """
    Approve decommission planning and proceed to data migration phase.

    Updates:
    1. Mark planning phase as completed
    2. Update all decommission plans approval_status
    3. Resume master flow to continue to data_migration phase
    """
    # Get child flow
    decom_repo = DecommissionFlowRepository(db, context.client_account_id, context.engagement_id)
    child_flow = await decom_repo.get_by_master_flow_id(uuid.UUID(flow_id))

    if not child_flow:
        raise HTTPException(status_code=404, detail="Decommission flow not found")

    if child_flow.decommission_planning_status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Planning phase must be completed before approval"
        )

    async with db.begin():
        # Update decommission plans approval status
        stmt = update(DecommissionPlan).where(
            DecommissionPlan.flow_id == child_flow.flow_id
        ).values(
            approval_status="approved",
            approved_by=approval.approved_by,
            approved_at=datetime.utcnow()
        )
        await db.execute(stmt)

        # Update child flow status to proceed to data_migration
        await decom_repo.update_status(
            flow_id=child_flow.flow_id,
            status="data_migration",
            current_phase="data_migration"
        )

        # Resume master flow via MFO
        await mfo.resume_flow(
            flow_id=flow_id,
            phase="data_migration"
        )

        await db.commit()

    return DecommissionFlowResponse(
        flow_id=flow_id,
        status="data_migration",
        current_phase="data_migration",
        next_phase="data_migration",
        selected_systems=[str(s) for s in child_flow.selected_system_ids],
        message="Planning approved. Starting data migration phase."
    )
```

## ⚠️ Error Handling

### Agent Execution Failures

```python
try:
    result = await planning_crew.execute(...)
except CrewExecutionError as e:
    logger.error(f"Planning crew execution failed: {e}", exc_info=True)

    # Mark phase as failed
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="decommission_planning",
        phase_status="failed"
    )

    # Store error details
    await self.repository.update(
        flow_id=child_flow.flow_id,
        runtime_state={
            "error": {
                "phase": "decommission_planning",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

    return {
        "status": "failed",
        "phase": "decommission_planning",
        "error": str(e),
        "retry_available": True
    }
```

### Dependency Analysis Failures

```python
if len(dependency_graph.nodes) == 0:
    logger.warning("Dependency analysis returned no results")

    # Return partial results with warning
    return {
        "status": "partial_success",
        "phase": "decommission_planning",
        "warning": "Could not analyze dependencies. Manual review required.",
        "dependency_graph": {"nodes": [], "edges": []},
        "risk_assessment": risk_result,
        "estimated_savings": cost_result
    }
```

## 🎓 Best Practices

### DO ✅
- Always analyze dependencies before approval
- Show clear risk mitigation strategies
- Calculate realistic cost savings (not overly optimistic)
- Require approval for high-risk decommissions
- Store complete planning results for audit trail
- Use persistent agent pools (not per-call Crew instantiation)
- Follow ADR-025 child_flow_service pattern

### DON'T ❌
- Don't skip dependency analysis (can cause cascade failures)
- Don't auto-approve high-risk systems
- Don't proceed without user approval
- Don't create new Crew instances per execution (94% performance loss)
- Don't use crew_class in FlowTypeConfig (deprecated pattern)
- Don't bypass multi-tenant scoping

## 📝 Testing Checklist

- [ ] Planning phase executes with valid system IDs
- [ ] Dependency analysis identifies known dependencies
- [ ] Risk assessment assigns appropriate risk levels
- [ ] Cost analysis calculates realistic savings
- [ ] UI displays planning results correctly
- [ ] Approval workflow functions properly
- [ ] Phase transitions to data_migration after approval
- [ ] Failed executions mark phase as failed (not flow)
- [ ] Multi-tenant scoping enforced on all queries
- [ ] Persistent agents reused across executions

---

**Next Phase**: After planning approval, the flow proceeds to [Data Migration](./03_Data_Migration.md) to archive critical data before system shutdown.
