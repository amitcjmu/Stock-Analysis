## Agent Integration for Collection Gaps

Agents Involved (persistent via TenantScopedAgentPool)
- Pattern Recognition Agent: field mapping and normalization (vendor/product/version).
- Asset Intelligence Agent: lifecycle enrichment, asset-product linking, confidence scoring.
- Migration Strategy Expert: consumes resilience/compliance/ops/licensing to refine 6R.
- Risk Assessment Specialist: compliance/data-classification and vulnerability overlays.
- Wave Planning Coordinator: uses blackout/maintenance and dependencies for scheduling.
- Learning Specialist: feedback capture and memory updates (per tenant).

Initialization Pattern
```python
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

async def get_agent(context, agent_name: str):
    pool = TenantScopedAgentPool(context.client_account_id)
    # Note: use class references configured in the pool; do not instantiate Crew() per call
    return await pool.get_agent(agent_name)
```

Memory Enablement
- DeepInfra embeddings patch is enabled (ADR-019). Reference: `backend/app/core/memory/crewai_deepinfra_patch.py`.
- Agents persist learning per-tenant (episodic + semantic memory) via `TenantMemoryManager`.

Tools & Tasks
- GapAnalysisTool
  - Input: `{subject, existing_data_snapshot}`
  - Output: `{missing_fields_by_category, priorities}`

- QuestionnaireGenerationTool
  - Guarantees `question_id == field_name` for resolvable persistence.
  - Adapts sections per stakeholder role; sections ≤15 questions; with validation rules.

- VendorLifecycleTool
  - Normalizes vendor→product→version; finds lifecycle milestones; emits provenance & confidence.

- DependencyGraphTool
  - Suggests likely dependencies; UI confirms; agent updates critical path hints.

Memory & Learning
- Store user corrections for product/version normalization and mapping in tenant memory.
- Confidence drift metrics published; retrain thresholds learned (no hard-coded limits).

Failure Handling
- Return structured `pending/not_ready` with retry hints; never fabricate data.

Agent Tool Registry (to be implemented)
```python
class AgentToolRegistry:
    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, name: str, tool: BaseTool):
        if name in cls._tools:
            raise ValueError(f"Tool {name} already registered")
        cls._tools[name] = tool

    @classmethod
    def get(cls, name: str) -> BaseTool:
        return cls._tools[name]
```


