# CrewAI Agent ServiceRegistry Fixes - September 2025

## Error Pattern
`TenantScopedAgentPool.get_or_create_agent() got an unexpected keyword argument 'service_registry'`

## Root Cause
ServiceRegistry.get_agent_tools() method doesn't exist but was being called without checking.

## Solution Applied

### 1. Add Method Existence Check in tool_manager.py
```python
@classmethod
def add_registry_tools(
    cls,
    tools: List,
    context_info: Dict[str, Any],
    service_registry: Optional["ServiceRegistry"] = None,
) -> int:
    if not service_registry:
        return 0

    tools_added = 0
    try:
        # Check if service_registry has get_agent_tools method
        if hasattr(service_registry, "get_agent_tools"):
            registry_tools = service_registry.get_agent_tools(context_info)
            if registry_tools:
                tools.extend(registry_tools)
                tools_added += len(registry_tools)
        else:
            logger.debug("ServiceRegistry does not have get_agent_tools method")
    except Exception as e:
        logger.warning(f"Failed to add registry tools: {e}")

    return tools_added
```

### 2. Fix Missing context_info Parameter
```python
# In agent_executor.py
agent = await TenantScopedAgentPool.get_or_create_agent(
    client_id=str(self.context.client_account_id),
    engagement_id=str(self.context.engagement_id),
    agent_type="field_mapper",
    context_info={  # This was missing!
        "service_registry": getattr(self, "service_registry", None),
        "flow_id": getattr(self.context, "flow_id", None),
    }
)
```

## Related Pattern from Memory
From flowtypeconfig_parameter_debugging_patterns_2025_09:
- ServiceRegistry dependency injection requires parameter detection
- Use inspect.signature() to check function parameters
- Pass registry only to functions that expect it

## Files Modified
- `backend/app/services/persistent_agents/tool_manager.py`
- `backend/app/services/field_mapping_executor/agent_executor.py`

## Important Note
Don't remove service_registry setup entirely (as was done in commit 1ac9c3cf). Instead, add proper checks and handle missing methods gracefully. The registry pattern is needed for enterprise features.
