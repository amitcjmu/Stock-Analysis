# Agent Pattern Examples (ADR-024)

**Purpose**: Educational examples demonstrating ADR-024 patterns
**Status**: NOT used in production - reference only

## Overview

These are example agent implementations that demonstrate various agent patterns used in the migration orchestrator platform. They are **NOT** used in production code - the actual production implementation uses `TenantScopedAgentPool` (see ADR-015 and ADR-024).

## Files (9 examples)

### Data Collection & Validation Agents
- `asset_inventory_agent_crewai_example.py` - Pattern for discovering and cataloging application assets
- `collection_orchestrator_agent_crewai_example.py` - Pattern for orchestrating multi-phase data collection workflows
- `data_validation_agent_crewai_example.py` - Pattern for validating data quality and completeness
- `credential_validation_agent_crewai_example.py` - Pattern for validating credentials and access permissions

### Data Processing Agents
- `data_cleansing_agent_crewai_example.py` - Pattern for cleaning and normalizing raw data
- `critical_attribute_assessor_crewai_example.py` - Pattern for identifying and assessing critical data attributes

### Workflow Management Agents
- `validation_workflow_agent_crewai_example.py` - Pattern for managing validation workflows
- `progress_tracking_agent_crewai_example.py` - Pattern for tracking task progress across multi-phase operations
- `tier_recommendation_agent_crewai_example.py` - Pattern for analyzing complexity and recommending migration tiers

## Production Usage

**DO NOT import these files in production code.** For production agent usage, use:

```python
from app.services.persistent_agents import TenantScopedAgentPool

# Get or create persistent agent
agent = await TenantScopedAgentPool.get_agent(
    context=request_context,
    agent_type="data_validation",  # or other type
    service_registry=service_registry
)

# Process data
result = await agent.process(input_data, **kwargs)
```

## Architecture References

### ADR-015: Persistent Multi-Tenant Agent Architecture
- Singleton pattern: One agent instance per (tenant, agent_type)
- Lazy initialization: Agents created on first use
- Memory persistence: Agent learning stored in tenant-scoped memory

### ADR-024: TenantMemoryManager Architecture
- **CrewAI memory DISABLED** (`memory=False` for all crews)
- Enterprise memory: PostgreSQL + pgvector
- Multi-tenant isolation: client_account_id + engagement_id scoping
- Learning scopes: ENGAGEMENT, CLIENT, GLOBAL

## Example Pattern Structure

```python
# Example agent pattern (DO NOT use in production)
from crewai import Agent, Task, Crew

def create_example_agent(context):
    \"\"\"Example: Creating an agent for a specific task\"\"\"
    agent = Agent(
        role="Data Validator",
        goal="Validate data quality and completeness",
        backstory="...",
        memory=False  # Per ADR-024
    )

    task = Task(
        description="Validate the provided data",
        agent=agent,
        expected_output="Validation report"
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        memory=False,  # Required per ADR-024
        verbose=False
    )

    return crew

# Production equivalent:
async def validate_data_production(context, service_registry, data):
    \"\"\"Production: Using persistent agent\"\"\"
    agent = await TenantScopedAgentPool.get_agent(
        context=context,
        agent_type="data_validation",
        service_registry=service_registry
    )
    return await agent.process(data)
```

## Learning from These Examples

Study these patterns to understand:
1. **Agent Role Definition**: How to define clear agent responsibilities
2. **Task Structure**: How to structure tasks for agents
3. **Crew Composition**: How multiple agents can work together
4. **Expected Outputs**: How to specify and validate outputs

Then apply these patterns using `TenantScopedAgentPool` in production.

## Migration Context

These files were moved from `backend/app/services/agents/` as part of the backend cleanup (Task A3):
- **Original Location**: `backend/app/services/agents/*_crewai.py`
- **New Location**: `docs/examples/agent_patterns/*_crewai_example.py`
- **Reason**: Clarify that these are examples, not production code
- **Date**: 2025-10-11

## Related Documentation

- `/docs/adr/015-persistent-multi-tenant-agent-architecture.md` - Persistent agent pattern
- `/docs/adr/024-tenant-memory-manager-architecture.md` - Memory management
- `/docs/analysis/backend_cleanup/FINAL-PARALLEL-EXECUTION-PLAN.md` - Cleanup plan (Task A3)
- `/docs/guidelines/coding-agent-guide.md` - Production coding patterns

## Restoration

If these files need to be moved back (NOT recommended):

```bash
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator
for file in docs/examples/agent_patterns/*_crewai_example.py; do
    basename=$(basename "$file" _example.py)
    cp "$file" "backend/app/services/agents/${basename}.py"
done
```

**Warning**: Moving these back would require:
1. Removing the `_example` suffix
2. Updating any imports in production code (violates ADR-015/024)
3. Re-enabling direct Crew() usage (not recommended)
