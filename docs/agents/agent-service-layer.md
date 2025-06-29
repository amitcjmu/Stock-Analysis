# Agent Service Layer Architecture

## Overview

The Agent Service Layer provides a synchronous interface between CrewAI agents and the asynchronous backend services. This eliminates the need for agents to make HTTP calls, handle authentication, or deal with network complexities.

## Problem Statement

### Current Challenges
1. **Sync/Async Mismatch**: CrewAI tools are synchronous, but backend services are async
2. **HTTP Complexity**: Agents struggle with authentication, headers, and network calls
3. **Mock Data Confusion**: HTTP endpoints return mock data when real data doesn't exist
4. **Performance Overhead**: Unnecessary network calls within the same container
5. **Context Propagation**: Multi-tenant context gets lost in HTTP calls

### Why Not HTTP Endpoints?

Agents cannot reliably use HTTP endpoints because:
- They run synchronously (CrewAI limitation)
- They're in the same container as the backend
- Authentication adds unnecessary complexity
- Network calls add latency and failure points

## Architecture

### Design Principles

1. **Direct Service Access**: No HTTP calls, direct Python method invocation
2. **Synchronous Interface**: Compatible with CrewAI's synchronous tools
3. **Real Data Only**: No mock or fallback data - clear error states
4. **Multi-Tenant Aware**: Maintains RequestContext throughout
5. **Minimal Dependencies**: Lightweight and focused

### Component Structure

```
┌─────────────────────┐
│   CrewAI Agents     │
│  (Synchronous)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Agent Service Layer │  ← Sync/Async Bridge
│  (ThreadPoolExecutor)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Backend Services   │
│  (Asynchronous)     │
└─────────────────────┘
```

## Implementation Guide

### Phase 1: Core Infrastructure

```python
# /backend/app/services/agents/agent_service_layer.py

class AgentServiceLayer:
    """Synchronous service layer for AI agents"""
    
    def __init__(self, client_account_id: str, engagement_id: str, user_id: Optional[str] = None):
        self.context = RequestContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            session_id=None
        )
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
```

### Phase 2: Service Methods

#### Flow Management Services

```python
def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
    """Get comprehensive flow status"""
    # Returns: flow existence, current phase, progress, next steps
    
def get_active_flows(self) -> List[Dict[str, Any]]:
    """List all active flows for the context"""
    # Returns: list of flows with status and progress
    
def validate_phase_transition(self, flow_id: str, from_phase: str, to_phase: str) -> Dict[str, Any]:
    """Check if phase transition is valid"""
    # Returns: validation result with requirements
```

#### Data Services

```python
def get_import_data(self, flow_id: str) -> Dict[str, Any]:
    """Retrieve raw import data"""
    # Returns: raw data, record count, field list
    
def get_field_mappings(self, flow_id: str) -> Dict[str, Any]:
    """Get current field mapping configuration"""
    # Returns: source-to-target mappings, confidence scores
    
def get_cleansing_results(self, flow_id: str) -> Dict[str, Any]:
    """Get data cleansing analysis"""
    # Returns: issues found, suggestions, quality metrics
```

#### Asset Services

```python
def get_discovered_assets(self, flow_id: str) -> List[Dict[str, Any]]:
    """Get all discovered assets"""
    # Returns: asset inventory with metadata
    
def get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
    """Get dependency analysis results"""
    # Returns: dependency graph, critical paths
    
def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
    """Get technical debt findings"""
    # Returns: debt items, risk scores, recommendations
```

## Usage in Agents

### Basic Tool Implementation

```python
from app.services.agents.agent_service_layer import get_agent_service

class FlowContextTool(BaseTool):
    name: str = "flow_context_analyzer"
    description: str = "Analyzes discovery flow context and status"
    
    def _run(self, flow_id: str, **kwargs) -> str:
        """Tool execution with service layer"""
        # Get service instance
        service = get_agent_service(
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id
        )
        
        # Direct service call
        result = service.get_flow_status(flow_id)
        
        # Handle clear states
        if result["status"] == "not_found":
            return json.dumps({
                "flow_exists": False,
                "guidance": "No flow found. User must upload data to start."
            })
        
        return json.dumps(result)
```

### Advanced Pattern: Multiple Service Calls

```python
class ComprehensiveAnalysisTool(BaseTool):
    def _run(self, flow_id: str) -> str:
        service = get_agent_service(
            self.client_account_id,
            self.engagement_id
        )
        
        # Gather comprehensive data
        flow_status = service.get_flow_status(flow_id)
        if flow_status["status"] == "not_found":
            return "Flow not found"
            
        # Get additional context
        assets = service.get_discovered_assets(flow_id)
        dependencies = service.get_asset_dependencies(flow_id)
        tech_debt = service.get_tech_debt_analysis(flow_id)
        
        # Combine results
        analysis = {
            "flow": flow_status,
            "assets_count": len(assets),
            "has_dependencies": bool(dependencies.get("edges")),
            "tech_debt_score": tech_debt.get("total_score", 0)
        }
        
        return json.dumps(analysis)
```

## Migration Strategy

### Step 1: Identify HTTP Calls
```bash
# Find all HTTP calls in agent code
grep -r "requests\|aiohttp\|httpx" app/services/agents/
grep -r "http://" app/services/crewai_flows/
```

### Step 2: Map to Service Methods
| Current HTTP Call | Service Method |
|------------------|----------------|
| GET /api/v1/unified-discovery/flow/status/{id} | get_flow_status() |
| GET /api/v1/unified-discovery/flows/active | get_active_flows() |
| POST /api/v1/field-mapping/validate | validate_mappings() |

### Step 3: Update Agent Tools
```python
# Before (HTTP)
response = requests.get(
    f"http://localhost/api/v1/flow/{flow_id}",
    headers={"Authorization": "Bearer token"}
)

# After (Service Layer)
service = get_agent_service(client_id, engagement_id)
result = service.get_flow_status(flow_id)
```

## Testing

### Unit Tests
```python
def test_flow_status_not_found():
    service = AgentServiceLayer("test-client", "test-engagement")
    result = service.get_flow_status("non-existent-id")
    assert result["status"] == "not_found"
    assert result["flow_exists"] is False
```

### Integration Tests
```python
async def test_with_real_database():
    # Create test flow
    flow = await create_test_flow()
    
    # Test through service layer
    service = AgentServiceLayer(flow.client_account_id, flow.engagement_id)
    result = service.get_flow_status(str(flow.flow_id))
    
    assert result["flow_exists"] is True
    assert result["flow"]["flow_id"] == str(flow.flow_id)
```

## Performance Considerations

### Thread Pool Configuration
```python
# For CPU-bound operations
executor = ThreadPoolExecutor(max_workers=4)

# For I/O-bound operations (default)
executor = ThreadPoolExecutor(max_workers=1)
```

### Connection Pooling
```python
# Reuse database connections
async with AsyncSessionLocal() as db:
    # Multiple operations on same connection
    flow = await get_flow(db, flow_id)
    assets = await get_assets(db, flow_id)
```

## Error Handling

### Standard Error Response
```python
{
    "status": "error",
    "error": "Descriptive error message",
    "error_type": "validation|not_found|permission|system",
    "guidance": "What the user should do"
}
```

### Common Error Scenarios
1. **Flow Not Found**: Clear "not_found" status
2. **Invalid Context**: Permission/access errors  
3. **Database Errors**: System errors with retry guidance
4. **Validation Failures**: Specific field/requirement issues

## Monitoring & Observability

### Metrics to Track
- Method call counts
- Response times (p50, p95, p99)
- Error rates by type
- Context validation failures
- Thread pool saturation

### Logging Standards
```python
logger.info(f"AgentService.get_flow_status called", extra={
    "flow_id": flow_id,
    "client_account_id": self.context.client_account_id,
    "method": "get_flow_status",
    "duration_ms": duration
})
```

## Security Considerations

### Context Validation
- Every method validates RequestContext
- No cross-tenant data access
- Audit trail for compliance

### No External Access
- Service layer has no HTTP endpoints
- Only accessible from within the container
- No authentication tokens needed

## Future Enhancements

### Caching Layer
```python
@lru_cache(maxsize=100)
def get_flow_status_cached(self, flow_id: str) -> Dict[str, Any]:
    # Cache frequently accessed flows
    pass
```

### Batch Operations
```python
def get_multiple_flows(self, flow_ids: List[str]) -> Dict[str, Any]:
    # Efficient batch retrieval
    pass
```

### Event Streaming
```python
def subscribe_to_flow_updates(self, flow_id: str) -> AsyncIterator[Dict]:
    # Real-time updates for long-running operations
    pass
```