# Field Mapping Agent Pool Configuration

## Insight 1: FieldMappingExecutor Requires Agent Pool
**Problem**: Field mappings falling back to mock responses instead of using AI
**Solution**: Pass TenantScopedAgentPool to FieldMappingExecutor
**Code**:
```python
# ❌ WRONG - Causes fallback to mock
executor = FieldMappingExecutor(
    flow_state, None, None  # No agent pool = fallback
)

# ✅ CORRECT - Uses AI agent
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from app.services.field_mapping_executor import FieldMappingExecutor as ModularFieldMappingExecutor

executor = ModularFieldMappingExecutor(
    storage_manager=None,
    agent_pool=TenantScopedAgentPool,  # Pass the class
    client_account_id=str(client_id),
    engagement_id=str(engagement_id)
)

# Call execute_phase not execute_field_mapping
result = await executor.execute_phase(flow_state, db_session)
```
**Usage**: When initializing field mapping executor for AI-powered mappings

## File Fixed:
- `backend/app/services/flow_orchestration/field_mapping_logic.py`
