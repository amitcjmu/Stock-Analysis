# HCLTech Cloud Assessment Framework – Capability Coverage and Gap Analysis

Date: 2025-08-25
Owner: AI Modernize Migration Platform Team

## Executive Summary

This report maps the HCLTech Cloud Assessment Framework (Kickoff → Planning/Tool Discovery → Workshops → Analysis → Craft → Transform) against current capabilities of the AI Modernize Migration Platform. After verifying actual code paths, we found that while the building blocks exist (agents, executors, models), some orchestrated execution paths currently route through placeholder implementations. Planning and Craft are partially addressed (6R strategy is implemented with fallbacks; wave planning is registered but lacks public endpoints). Workshop depth, performance/TCO, instance sizing, and execution/decommission remain partial or planned.

- Overall status (post code verification):
  - Discovery (Import → Mapping → Cleansing → Inventory → Dependencies): Partial/Conditional – functional executors exist, but the Crew execution engine maps several phases to placeholders
  - Workshops (Application owner questionnaires): Partial; adaptive forms are implemented with active fixes
  - Analysis (Dependencies, architecture, technical debt, risk): Partial-to-strong in places; performance/backup gaps
  - Craft (Go/No-Go, treatment, move groups, sizing, TCO, target architecture): Partial; 6R and wave planning covered, sizing/TCO pending
  - Transform (Migration execution): Planned; decommission planned

## Methodology and Evidence

Triangulated across `README.md`, `CHANGELOG.md`, discovery/assessment docs, and backend services. Representative evidence excerpts:

```23:63:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/flow_configs/discovery_flow_config.py
def get_discovery_flow_config() -> FlowTypeConfig:
    """
    Get the Discovery flow configuration with all 6 phases

    Phases:
    1. Data Import - Import and validate data from various sources
    2. Field Mapping - Map imported fields to standard schema
    3. Data Cleansing - Clean and normalize data
    4. Asset Creation - Create asset records from cleansed data
    5. Asset Inventory - Build comprehensive asset inventory
    6. Dependency Analysis - Analyze asset dependencies
    """
```

```112:156:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/assessment_flow/analysis_models.py
class SixRDecision(Base):
    """
    6R migration strategy decisions for applications and components.
    """
    __tablename__ = "sixr_decisions"
    sixr_strategy = Column(String(50), nullable=False)
    decision_rationale = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    risk_assessment = Column(JSONB, default=lambda: {}, nullable=False)
```

```206:245:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/core/database.py
async def get_db() -> AsyncSession:
    """Optimized async DB session with health checks (multi-tenant ready)."""
    session = AsyncSessionLocal()
    await session.execute(text("SELECT 1"))
    yield session
```

```85:132:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/repositories/context_aware_repository.py
class ContextAwareRepository(Generic[ModelType]):
    """Base repository that applies client_account_id/engagement_id scoping."""
    def _apply_context_filter(self, query: Select) -> Select:
        if self.has_client_account:
            filters.append(self.model_class.client_account_id == self.client_account_id)
        if self.has_engagement and self.engagement_id:
            filters.append(self.model_class.engagement_id == self.engagement_id)
```

## Code Reality Check: Implementations vs Placeholders

The following section validates whether capabilities are wired and executing real logic or are currently placeholder/stub paths.

- Discovery – Crew Execution Path uses placeholders for multiple phases
  - The Crew execution engine delegates discovery phases to a handler with placeholder methods for key phases:
  ```140:166:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/flow_orchestration/execution_engine_crew_discovery.py
  async def _execute_discovery_field_mapping(...):
      # Placeholder implementation for field mapping
      return {
          "phase": "field_mapping",
          "status": "completed",
          "mappings": {},
          "agent": "field_mapping_agent",
      }
  ```
  - Because `FlowExecutionCore` prefers Crew execution when `crew_config` is present, these placeholders can be hit instead of the richer executors:
  ```190:203:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/flow_orchestration/execution_engine_core.py
  if has_crew_config:
      from app.services.flow_orchestration.execution_engine_crew import FlowExecutionCrew
      crew_executor = FlowExecutionCrew(self.db, self.context, self.master_repo)
      phase_result = await crew_executor.execute_crew_phase(master_flow, phase_config, phase_input)
  ```
  - Functional implementations exist (not placeholders) for field mapping and other phases, but are not consistently used by the Crew engine:
  ```60:135:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/field_mapping_executor/base.py
  class FieldMappingExecutor:
      async def execute_phase(self, state: UnifiedDiscoveryFlowState, db_session: Any) -> Dict[str, Any]:
          # Validates state, executes agent, parses, validates, applies rules, persists, formats
  ```
  ```60:106:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/crewai_flows/handlers/phase_executors/field_mapping_executor.py
  class FieldMappingExecutor(BasePhaseExecutor):
      ...
  ```
  - Unified discovery flow references real executor classes, but execution path alignment is incomplete:
  ```221:244:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py
  self._phase_executor_classes = {
      "data_validation_phase": DataImportValidationExecutor,
      "field_mapping_phase": FieldMappingExecutor,
      "data_cleansing_phase": DataCleansingExecutor,
      "asset_inventory_phase": AssetInventoryExecutor,
      "dependency_analysis_phase": DependencyAnalysisExecutor,
      "tech_debt_assessment_phase": TechDebtExecutor,
  }
  ```

- Adaptive Workshops (Questionnaires) – real generation, partial wiring
  - Real questionnaire generation and adaptive form services exist and accept `collection_flow_id`; persistence is present, but some parts are still stabilizing:
  ```37:69:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/questionnaire_generation_handler.py
  questionnaires = await self.services.questionnaire_generator.generate_questionnaires(..., collection_flow_id=state.flow_id)
  ```
  ```479:500:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/manual_collection/adaptive_form_service.py
  def generate_adaptive_form(...):
      # Generates sections and metadata based on gap analysis and context
  ```
  - Quality service in `AdaptiveFormService` is intentionally uninitialized without request context, indicating partial integration:
  ```462:471:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/manual_collection/adaptive_form_service.py
  if self._quality_service is None:
      self.logger.warning("QualityAssessmentService not initialized - requires proper context setup")
      return None
  ```

- 6R Analysis – implemented with fallback
  - API endpoints create analyses and run background tasks; decision engine integrates a CrewAI technical debt crew with robust fallback:
  ```68:83:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/sixr_analysis.py
  @router.post("/analyze")
  async def create_sixr_analysis(...):
      background_tasks.add_task(analysis_service.run_initial_analysis, ...)
  ```
  ```166:190:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/sixr_engine_modular.py
  crew = tech_debt_crew.create_crew(asset_inventory, dependencies)
  crew_result = crew.kickoff()
  return self._parse_crew_results(crew_result, param_dict)
  ```

- Wave Planning – registered, but no public API endpoints
  - Planning agent manager registers a planner agent, but no `/api/v1/planning/waves|timeline` endpoints were found during search. This indicates functionality is not yet exposed:
  ```16:54:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/agent_registry/managers/planning.py
  class PlanningAgentManager(...):
      capabilities=["Automated wave generation", "Critical path analysis", ...]
  ```
  (No matching routes found for `/api/v1/planning/waves|timeline`.)

Conclusion: Discovery’s Crew executor path needs to be aligned with the real executors to move from placeholder to functional in production execution. Adaptive workshops are implemented but require final wiring and context initialization. 6R is functional with fallbacks. Wave planning lacks public endpoints.

## Coverage by HCL Framework Stages

Legend: Full, Partial, Planned, Missing

### 1) Kick‑off & Resource Onboarding
- Access to Existing CMDB: **Full** – Discovery CMDB import and processing with learning, dedupe, and asset creation
  - Evidence: `CHANGELOG` entries 2025-05-26..27; Discovery endpoints; Data import validation and processing
- Questionnaire finalization & walkthrough: **Partial** – Adaptive Forms implemented; fallback/bootstrap questionnaire fixes in progress
  - Evidence: `docs/planning/collection-flow-issues/2025-08-23_collection-flow-issues.md` and fixes reflected in `CHANGELOG` 2025-08-23
- Server(s) to Application mapping: **Partial** – Dependency analysis and application inventory supported; server-to-app mapping present in dependency phases
- Project templates, risk mgmt, workshop planning: **Partial** – Risk analysis present in assessment; project plan templates not formalized in UI
- Stakeholder participation & onboarding: **Partial** – RBAC and multi-tenant context implemented; stakeholder workflows TBD

### 2) Planning & Tool-Based Discovery
- Tool procurement/deployment: **Out of scope** for in-app (assumes platform usage)
- Baseline inventory: **Full** – Asset inventory phase with classification/deduplication
- Initial discovery: **Full** – Orchestrated via Unified Discovery Flow (6 phases)
- Workshop planning: **Partial** – Data collection via Adaptive Forms; scheduling/collab not native

### 3) Workshops with Application Owners (Data Collection)
Requested data: application details, business drivers, inter-dependencies, deployment architecture, complexity, DB/middleware, supportability, DR, security/compliance.
- Adaptive questionnaires: **Partial** – Implemented; ongoing fixes to ensure bootstrap form without preselected apps and reliable persistence
  - Evidence: collection flow report and `CHANGELOG` 2025-08-23
- Coverage of all workshop dimensions:
  - Application details, dependencies, architecture, complexity, database/middleware: **Partial** – covered through forms + discovery/assessment derived data
  - Supportability, DR requirements, security & compliance: **Planned/Partial** – data model/UI forms not fully explicit; agents can infer some but first-class workflows are limited

### 4) Analysis
- Infrastructure details & inter-dependencies: **Full/Partial** – Asset inventory + dependency analysis agents and crews; technical debt analysis available
  - Evidence: discovery flow config phases; tech debt crews; dependency analysis docs
- Authentication/Shared services analysis: **Partial** – basic modeling; not a dedicated analysis module
- Application component analysis (architecture, complexity, business criticality, DB & middleware): **Partial** – 6R/tech-debt agents consume and produce this; UI views vary by page
- Performance data, backup & storage: **Missing/Planned** – no dedicated performance telemetry or backup/storage analytics integrated

### 5) Craft (Recommendations and Planning)
- Go/No-Go recommendation: **Partial** – derivable from quality gates and 6R readiness; not formalized as a single artifact
- Treatment recommendation (6R): **Full** – 6R analysis agents, models, and endpoints
- Finalized move group / wave planning: **Partial/Full** – Wave Planning Coordinator agent exists; grouping logic and UI present in parts
- Target instance sizing: **Missing/Planned** – not yet implemented
- Migration parameters: **Partial** – parameters surfaced in assessments; not an end-to-end parameter registry
- TCO calculation: **Missing/Planned** – FinOps agent planned; LLM cost management exists (for AI), but cloud TCO not yet
- TO‑BE architecture: **Partial** – agents provide architecture/rationale narratives; formal architecture model/UI pending

### 6) Transform (Migration Execution)
- Migration execution orchestration: **Planned** – Execution Coordinator agent planned; no live executors integrated
- Decommission plan: **Planned** – agent planned; models and flows not yet finalized

## Detailed Capability Map

### Discovery Capabilities (Conditional)
- Functional executors and crews exist for field mapping, cleansing, inventory, and dependencies; however, the Crew execution path currently maps several phases to placeholders. Until the Crew engine delegates to the real executors, runtime coverage is partial.
- Learning-enabled field mapping and data cleansing exist; ensure execution uses `FieldMappingExecutor` rather than placeholder methods.

Key references:
```49:66:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/crewai_flows/unified_discovery_flow/phase_controller.py
class PhaseController:
    """Controls phase-by-phase execution with pauses for user input."""
```

### Assessment Capabilities (Solid foundation)
- Technical debt analysis crew, 6R strategy crew, and risk assessment handlers with persistent models (`sixr_decisions`).

Key references:
```66:92:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/crewai_flows/crews/sixr_strategy_crew.py
class SixRStrategyCrew:
    """Determines component-level 6R strategies with validation"""
```

### Planning/Wave Coordination (Emerging)
- Wave Planning Coordinator agent is registered, but no public planning endpoints were found; consider this not yet exposed (partial/blocked on API).

### FinOps/Cost/TCO (Gap)
- Robust LLM cost management exists (admin endpoints, dashboards) but cloud TCO for migration planning is not implemented. Opportunity for a Cost Optimization agent tied to cloud pricing APIs.

### Execution/Decommission (Planned)
- Agents planned; execution connectors and runbooks not yet integrated.

## Workshop Data Capture – Depth Check

Required dimensions vs status:
- Application details, deployment architecture, databases/middleware: **Partial** – captured via forms and discovery artifacts, needs consolidation into a single “Application Profile” view
- Complexity, business criticality: **Partial** – present in assessment/6R inputs, needs consistent scoring UI
- DR, security & compliance: **Gap** – add schemas, forms, and agents for policy alignment and DR objectives (RTO/RPO)

## Cross‑Cutting Architecture Strengths

- Multi‑tenant enforcement via context‑aware repositories and async DB sessions
- Agentic‑first design: 17 agents (13 active, 4 planned) with learning and agent‑UI bridge
- Master Flow Orchestrator with child flow pattern for lifecycle vs operational data

Key references:
```117:131:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/flow_configs/discovery_flow_config.py
# crew_class registration and child flow service integration
```

```62:101:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/core/context_aware.py
class ContextAwareRepository(ABC):
    def apply_context_filter(self, query):
        if hasattr(self.model_class, "client_account_id"):
            query = query.where(self.model_class.client_account_id == self.context.client_account_id)
```

## Gaps and Recommendations

Prioritized, high‑impact initiatives:

1) Adaptive Workshops Completion (High)
   - Finish bootstrap questionnaire path and persistence fixes for Adaptive Forms
   - Add sections for Supportability, DR (RTO/RPO), Security & Compliance
   - Outcome: Full coverage of HCL workshop scope; improved data quality feeding assessment

2) Performance, Backup & Storage Analysis (High)
   - Create an Analysis submodule and agent tools to ingest performance telemetry, backup/DR metadata
   - Outcome: Completes HCL “Performance Data” and “Backup & Storage” expectations

3) Craft Enhancements: Go/No‑Go, Sizing, TCO (High)
   - Formalize Go/No‑Go artifact based on quality gates and agent findings
   - Implement target instance sizing heuristics via agent tools with cloud provider catalogs
   - Implement TCO models (inputs: instance sizing, storage, network, licensing). Distinct from existing LLM cost analytics

4) Target Architecture Modeling (Medium)
   - Provide a structured TO‑BE architecture model and UI (components, services, integrations) with agent‑assisted recommendations

5) Execution Alignment for Discovery (High)
   - Align `FlowExecutionCrew` → `ExecutionEngineDiscoveryCrews` to call real phase executors (e.g., `FieldMappingExecutor`) instead of placeholders.
   - Add integration tests to assert that phase results contain real persisted artifacts (mappings, cleansed data, inventory rows).

6) Execution & Decommission (Medium)
   - Define execution connectors (e.g., runbooks, IaC hooks) and Decommission workflows, instrumented via agents

7) Shared Services & Authentication Deep Dive (Medium)
   - Add explicit assessment and visualization of shared services, auth/SSO integration dependencies

## Roadmap Alignment (Next 4–8 weeks)

- Weeks 1–2: Complete Adaptive Workshops (backend fallback, UI bootstrap, persistence shape); introduce DR/Security sections
- Weeks 2–3: Add Analysis: Performance + Backup/Storage agents and UI panels
- Weeks 3–4: Craft: Go/No‑Go artifact, Sizing (v1 with provider catalogs), TCO (v1 formula + export)
- Weeks 5–6: TO‑BE Architecture modeling and views; begin Execution connector design
- Weeks 7–8: Execution/Decommission agent stubs with health metrics; refine shared services/auth analysis

## Risks and Mitigations

- Data completeness from workshops may lag: mitigate with bootstrap forms, progressive disclosure, and defaults
- Complexity of sizing/TCO accuracy: start with conservative baselines; iterate with provider APIs and user feedback
- Execution connector scope creep: use modular handler pattern with feature flags per connector

## Acceptance Criteria for “Strong Coverage” of HCL Framework

- Workshops: End‑to‑end questionnaire flow works without preselected apps; includes DR/Security; persists reliably
- Analysis: Dedicated panels for performance and backup/storage with agent outputs and confidence scores
- Craft: Visible Go/No‑Go artifact, 6R recommendations linked to wave groups, v1 sizing and TCO summaries, TO‑BE architecture structured view
- Transform: Execution and Decommission agents stubbed with basic runbook integration and status tracking

## Appendix: Additional Evidence

Discovery flow sequence and status interactions:
```96:116:/Users/chocka/CursorProjects/migrate-ui-orchestrator/docs/architecture/discovery-flow-sequence-diagram.md
UI->>API: POST /api/v1/flows/{flow_id}/execute
API->>MFO: execute_phase(flow_id, "asset_inventory")
MFO->>UDF: Build inventory
UDF->>DB: Insert into assets table
```

Field Mapping learning system validated (backend fixed and health checked):
```55:75:/Users/chocka/CursorProjects/migrate-ui-orchestrator/docs/development/discovery-flow/FIELD_MAPPING_COMPREHENSIVE_VALIDATION_REPORT.md
Endpoint Status:
- /api/v1/data-import/field-mappings/learned - 200 OK
- /api/v1/data-import/field-mappings/health - 200 OK
```

---

This document will be maintained as features progress from Partial/Planned to Full coverage.


