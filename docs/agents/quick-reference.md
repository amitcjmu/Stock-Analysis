# Agent Service Layer Quick Reference

## Setup

```python
from app.services.agents.agent_service_layer import get_agent_service

# Get service instance
service = get_agent_service(
    client_account_id="your-client-id",
    engagement_id="your-engagement-id",
    user_id="optional-user-id"
)
```

## Common Operations

### Check if Flow Exists
```python
result = service.get_flow_status(flow_id)
if result["status"] == "not_found":
    print("No flow - user must upload data")
else:
    print(f"Flow found: {result['flow']['current_phase']}")
```

### Get Active Flows
```python
flows = service.get_active_flows()
for flow in flows:
    print(f"Flow {flow['flow_id']}: {flow['status']}")
```

### Validate Phase Transition
```python
validation = service.validate_phase_transition(
    flow_id=flow_id,
    from_phase="data_import",
    to_phase="attribute_mapping"
)
if validation["can_transition"]:
    print("Ready to proceed")
else:
    print(f"Requirements: {validation['missing_requirements']}")
```

## In CrewAI Tools

### Basic Tool Pattern
```python
class YourAgentTool(BaseTool):
    name: str = "your_tool_name"
    description: str = "What this tool does"
    
    def _run(self, flow_id: str, **kwargs) -> str:
        # Get service
        service = get_agent_service(
            self.context["client_account_id"],
            self.context["engagement_id"]
        )
        
        # Call service method
        result = service.your_method(flow_id)
        
        # Handle response
        if result["status"] == "error":
            return f"Error: {result['error']}"
            
        return json.dumps(result)
```

### Error Handling Pattern
```python
def _run(self, flow_id: str) -> str:
    service = get_agent_service(self.client_id, self.engagement_id)
    
    try:
        result = service.get_flow_status(flow_id)
        
        # Handle specific states
        if result["status"] == "not_found":
            return "No flow exists - upload data first"
        elif result["status"] == "error":
            return f"System error: {result['error']}"
        else:
            return json.dumps(result["flow"])
            
    except Exception as e:
        logger.error(f"Service call failed: {e}")
        return "Service temporarily unavailable"
```

## Response Formats

### Success Response
```python
{
    "status": "success",
    "flow_exists": True,
    "flow": {
        "flow_id": "uuid",
        "current_phase": "data_import",
        "next_phase": "attribute_mapping",
        "progress": 16.67,
        "phases_completed": {
            "data_import": True,
            "attribute_mapping": False,
            ...
        }
    }
}
```

### Not Found Response
```python
{
    "status": "not_found",
    "flow_exists": False,
    "message": "Flow not found in database",
    "guidance": "User must upload data to create flow"
}
```

### Error Response
```python
{
    "status": "error",
    "error": "Detailed error message",
    "error_type": "validation|permission|system",
    "guidance": "What to do about it"
}
```

## Migration Checklist

- [ ] Remove all `import requests/aiohttp/httpx`
- [ ] Replace HTTP calls with service methods
- [ ] Remove authentication headers
- [ ] Update error handling for new format
- [ ] Test with real database (no mocks)
- [ ] Verify multi-tenant context works

## Common Pitfalls

### ❌ Don't Do This
```python
# Making HTTP calls from agents
response = requests.get(f"http://localhost/api/flow/{id}")

# Using mock data
if not data:
    return {"mock": "data"}

# Ignoring context
service = AgentServiceLayer("", "")  # Bad!
```

### ✅ Do This Instead
```python
# Use service layer
service = get_agent_service(client_id, engagement_id)
result = service.get_flow_status(flow_id)

# Return real states
if result["status"] == "not_found":
    return "No data found"

# Always provide context
service = get_agent_service(
    context.client_account_id,
    context.engagement_id
)
```

## Performance Tips

1. **Reuse Service Instances**: Don't create new instances in loops
2. **Batch Operations**: Use batch methods when available
3. **Handle Timeouts**: All methods timeout at 30 seconds
4. **Log Sparingly**: Avoid logging in tight loops

## Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger("app.services.agents").setLevel(logging.DEBUG)
```

### Check Context
```python
print(f"Context: client={service.context.client_account_id}")
print(f"Context: engagement={service.context.engagement_id}")
```

### Trace Execution
```python
result = service.get_flow_status(flow_id)
print(f"Service returned: {json.dumps(result, indent=2)}")
```