# DecommissionAgentPool - Quick Start Guide

**🚀 5-Minute Integration Guide**

---

## TL;DR

```python
from app.services.agents.decommission import DecommissionAgentPool

# 1. Initialize pool
agent_pool = DecommissionAgentPool()

# 2. Get agents
agents = {
    "system_analysis_agent": await agent_pool.get_agent("system_analysis_agent", client_id, engagement_id),
    "dependency_mapper_agent": await agent_pool.get_agent("dependency_mapper_agent", client_id, engagement_id),
    "data_retention_agent": await agent_pool.get_agent("data_retention_agent", client_id, engagement_id),
}

# 3. Create crew
crew = agent_pool.create_decommission_planning_crew(
    agents=agents,
    system_ids=["sys1", "sys2"],
    decommission_strategy={"priority": "cost_savings"}
)

# 4. Execute
result = crew.kickoff()

# 5. Clean up
await agent_pool.release_agents(client_id, engagement_id)
```

---

## Agent Reference

| Agent Key | Role | Phase Used |
|-----------|------|------------|
| `system_analysis_agent` | System Dependency Analysis | Planning |
| `dependency_mapper_agent` | System Relationship Mapping | Planning |
| `data_retention_agent` | Data Retention & Compliance | Planning, Migration |
| `compliance_agent` | Regulatory Compliance | Migration |
| `shutdown_orchestrator_agent` | Safe System Shutdown | Shutdown |
| `validation_agent` | Post-Decommission Verification | Migration, Shutdown |
| `rollback_agent` | Rollback & Recovery | Shutdown |

---

## Crew Methods

### `create_decommission_planning_crew(agents, system_ids, decommission_strategy)`
**Agents Needed**: system_analysis_agent, dependency_mapper_agent, data_retention_agent
**Returns**: Planning crew ready for execution

### `create_data_migration_crew(agents, retention_policies, system_ids)`
**Agents Needed**: data_retention_agent, compliance_agent, validation_agent
**Returns**: Data migration crew ready for execution

### `create_system_shutdown_crew(agents, decommission_plan, system_ids)`
**Agents Needed**: shutdown_orchestrator_agent, validation_agent, rollback_agent
**Returns**: Shutdown crew ready for execution

---

## Common Patterns

### Pattern 1: Single Phase Execution
```python
# Execute just one phase
agent_pool = DecommissionAgentPool()
agents = {key: await agent_pool.get_agent(key, client_id, engagement_id) for key in required_agents}
crew = agent_pool.create_<phase>_crew(agents, **phase_args)
result = crew.kickoff()
await agent_pool.release_agents(client_id, engagement_id)
```

### Pattern 2: Full Workflow
```python
# Execute all 3 phases sequentially
from app.services.agents.decommission.example_usage import complete_decommission_workflow_example

result = await complete_decommission_workflow_example(
    client_account_id="uuid",
    engagement_id="uuid",
    system_ids=["sys1", "sys2"],
    decommission_strategy={"priority": "cost_savings"}
)
```

### Pattern 3: With TenantMemoryManager (ADR-024)
```python
from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager, LearningScope

# After crew execution
memory_manager = TenantMemoryManager(...)
await memory_manager.store_learning(
    client_account_id=UUID(client_id),
    engagement_id=UUID(engagement_id),
    scope=LearningScope.ENGAGEMENT,
    pattern_type="decommission_planning",
    pattern_data={"system_count": len(system_ids), "results": result}
)
```

---

## Critical: ADR-024 Compliance

⚠️ **ALL agents created with `memory=False`**
⚠️ **ALL crews created with `memory=False`**

✅ Use `TenantMemoryManager` for agent learning instead

---

## Error Handling

```python
try:
    crew = agent_pool.create_decommission_planning_crew(...)

    if not crew:
        # CrewAI unavailable - fallback mode
        return {"status": "failed", "error": "Crew creation failed"}

    result = crew.kickoff()

except ValueError as e:
    # Missing required agents
    logger.error(f"Agent creation failed: {e}")

except Exception as e:
    # General execution error
    logger.error(f"Crew execution failed: {e}")
```

---

## Testing

```bash
# Unit tests
docker exec migration_backend python -m pytest \
  tests/unit/services/agents/test_decommission_agent_pool.py -v

# Integration tests
docker exec migration_backend python -m pytest \
  tests/integration/test_decommission_agent_pool_integration.py -v

# All tests
docker exec migration_backend python -m pytest \
  tests/unit/services/agents/test_decommission_agent_pool.py \
  tests/integration/test_decommission_agent_pool_integration.py -v
```

**Expected**: 27/27 tests pass (100%)

---

## Files

- **Implementation**: `/backend/app/services/agents/decommission/agent_pool.py`
- **Examples**: `/backend/app/services/agents/decommission/example_usage.py`
- **Unit Tests**: `/backend/tests/unit/services/agents/test_decommission_agent_pool.py`
- **Integration Tests**: `/backend/tests/integration/test_decommission_agent_pool_integration.py`

---

## Next Steps for Integration

1. Create `DecommissionChildFlowService` in `/backend/app/services/child_flows/decommission.py`
2. Update `FlowTypeConfig` with `child_flow_service=DecommissionChildFlowService`
3. Implement phase handlers that use `agent_pool.create_<phase>_crew()`
4. Add TenantMemoryManager integration for learning storage

See `DECOMMISSION_AGENT_POOL_IMPLEMENTATION_SUMMARY.md` for detailed integration guide.

---

**🤖 Generated with Claude Code (CC)**
