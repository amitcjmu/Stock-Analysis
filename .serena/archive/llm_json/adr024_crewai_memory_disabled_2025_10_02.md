# ADR-024: CrewAI Memory Disabled - Use TenantMemoryManager

**Date Created**: October 2, 2025
**Session Context**: Railway deployment error triage - OpenAI embeddings 422 validation error

## Critical Decision (October 2025)

CrewAI's built-in memory system was **DISABLED** and replaced with `TenantMemoryManager` per ADR-024.

## Why This Matters for All Code Changes

### The Rule
- **NEVER set `memory=True`** when creating agents or crews
- **ALWAYS use `memory=False`** (default in CrewConfig since October 2025)
- **Use `TenantMemoryManager`** for all agent learning and pattern storage

### Why Memory Was Disabled

1. **401/422 Authentication Errors**: CrewAI memory tried to use OpenAI embeddings with DeepInfra API keys, causing validation failures
2. **No Multi-Tenant Isolation**: CrewAI's ChromaDB doesn't support per-tenant data scoping
3. **External Dependency**: ChromaDB file-based storage vs native PostgreSQL+pgvector
4. **Architectural Violation**: Global monkey patches contradict explicit configuration principle from factory pattern migration

### What Replaced It

**TenantMemoryManager** - Enterprise-grade memory system:
- Multi-tenant isolation (client_account_id, engagement_id scoping)
- Native PostgreSQL + pgvector (already in stack)
- Data classification and audit trails
- Learning scopes: ENGAGEMENT, CLIENT, GLOBAL
- Pattern storage and retrieval with similarity search

## Common Mistakes to Avoid

### ❌ **WRONG** - Re-enabling CrewAI Memory
```python
# DO NOT DO THIS
agent = create_agent(
    role="Field Mapper",
    memory=True,  # ❌ WRONG - Legacy pattern
    ...
)

crew = create_crew(
    agents=[agent],
    memory=True,  # ❌ WRONG - Will cause 422 errors
)
```

### ❌ **WRONG** - Enabling Memory in Agent Pool
```python
# DO NOT DO THIS in agent_pool_constants.py
AGENT_POOL_CONFIG = {
    "field_mapper": {
        "memory_enabled": True,  # ❌ WRONG - Legacy setting
    }
}
```

### ❌ **WRONG** - Applying Memory Patches at Startup
```python
# DO NOT DO THIS in lifecycle.py
from app.services.crewai_memory_patch import apply_memory_patch

apply_memory_patch()  # ❌ WRONG - Violates ADR-024
```

### ❌ **WRONG** - Using EmbedderConfig for CrewAI Memory
```python
# DO NOT DO THIS
from app.services.crewai_flows.config.embedder_config import EmbedderConfig

embedder = EmbedderConfig.get_embedder_for_crew(memory_enabled=True)
# ❌ WRONG - Superseded by TenantMemoryManager
```

## ✅ **CORRECT** - Using TenantMemoryManager

### Disable Memory in Agent Creation
```python
# CORRECT - Memory disabled by default
agent = create_agent(
    role="Field Mapper",
    # memory=False is the default, no need to specify
    ...
)

crew = create_crew(
    agents=[agent],
    # memory=False is the default
)
```

### Use TenantMemoryManager for Learning
```python
# CORRECT - Store agent learning
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

# After agent completes task
memory_manager = TenantMemoryManager(
    crewai_service=crewai_service,
    database_session=db
)

await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    pattern_data={
        "source_field": "cust_name",
        "target_field": "customer_name",
        "confidence": 0.95,
        "transformation_rule": "lowercase + underscore"
    }
)

# Before agent execution - retrieve similar patterns
patterns = await memory_manager.retrieve_similar_patterns(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    query_context={"source_field": "customer"}
)
```

## If You See Memory Errors in Production

### Symptoms
- `Error code: 422 - encoding_format should be 'float' but received 'base64'`
- `Error code: 401 - Incorrect API key provided`
- `Failed to initialize embedder`
- `Warning: Using heuristic field mapping approach (CrewAI not available or disabled)`

### Root Cause
Legacy `memory=True` settings in code that haven't been migrated to ADR-024 standards.

### Fix Strategy
1. **Find all `memory=True` settings**:
   ```bash
   grep -r "memory=True\|memory.*:.*True" backend/app/services/
   ```

2. **Change to `memory=False`** with comment:
   ```python
   memory=False,  # Per ADR-024: Use TenantMemoryManager for enterprise memory
   ```

3. **Update agent_pool_constants.py**:
   ```python
   "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
   ```

4. **Fix incorrect comments** in agent_wrapper.py:
   ```python
   # OLD COMMENT (WRONG):
   # Factory applies defaults: max_iterations=1, timeout=600s, memory=True

   # NEW COMMENT (CORRECT):
   # Factory applies defaults: max_iterations=1, timeout=600s, memory=False (ADR-024)
   ```

5. **Do NOT**:
   - Re-enable global memory patches
   - Use EmbedderConfig to configure CrewAI memory
   - Propose "fixing" CrewAI memory instead of using TenantMemoryManager

## Files to Check When Making Changes

### Configuration Files
- `backend/app/services/crewai_flows/config/crew_factory/config.py` (lines 100, 147)
  - Should have `memory=False` defaults
- `backend/app/services/persistent_agents/agent_pool_constants.py`
  - All agents should have `memory_enabled: False`

### Agent Files (Legacy `memory=True` locations)
- `backend/app/services/agentic_intelligence/modernization_agent.py:135, 257`
- `backend/app/services/agentic_intelligence/business_value_agent.py:121, 212`
- `backend/app/services/agentic_intelligence/risk_assessment_agent.py:133, 250`
- `backend/app/services/agents/credential_validation_agent_crewai.py:71`
- `backend/app/services/agents/gap_prioritization_agent_crewai.py:66, 93`
- `backend/app/services/agents/tier_recommendation_agent_crewai.py:75`
- `backend/app/services/agents/validation_workflow_agent_crewai.py:72`
- And 8+ more agent files (see grep results)

### Comments to Fix
- `backend/app/services/persistent_agents/config/agent_wrapper.py:71`
  - Comment incorrectly says "memory=True" but defaults are "memory=False"

## Key References

- **ADR Document**: `/docs/adr/024-tenant-memory-manager-architecture.md`
- **Strategy Document**: `/docs/development/TENANT_MEMORY_STRATEGY.md`
- **Implementation**: `backend/app/services/crewai_flows/memory/tenant_memory_manager/`
- **Factory Defaults**: `backend/app/services/crewai_flows/config/crew_factory/config.py`

## Learning for Future Sessions

When you see errors related to:
- OpenAI embeddings validation
- DeepInfra API authentication
- CrewAI memory initialization
- Encoding format mismatches

**First check**: Are there any `memory=True` settings in the code?
**Then fix**: Change to `memory=False` and use TenantMemoryManager

**Do NOT propose**:
- Re-enabling memory patches
- "Fixing" the embedder configuration
- Using EmbedderConfig for CrewAI memory

**The correct solution is ALWAYS**: Disable CrewAI memory, use TenantMemoryManager.

## Historical Context

### Timeline
- **Pre-October 2025**: CrewAI memory enabled with global monkey patches
- **October 2025**: Factory pattern migration removed global patches (ADR-019)
- **October 2, 2025**: ADR-024 formalized complete CrewAI memory disablement
- **Current**: All new code must use `memory=False` + TenantMemoryManager

### Why This Decision Was Made
After comprehensive research (Context7 MCP evaluation), no viable alternatives existed for integrating DeepInfra embeddings with CrewAI memory. The TenantMemoryManager provides superior enterprise features and eliminates all integration issues.

---

**Status**: Active and Enforced
**Last Updated**: October 2, 2025
**Related PRs**: #486 (TenantMemoryManager implementation), Current PR (memory=True removal)
