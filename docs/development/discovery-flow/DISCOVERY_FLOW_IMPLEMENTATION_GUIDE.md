# Discovery Flow Implementation Guide - Remediation Context

## 🎯 **Overview**

This guide provides practical implementation guidance for working with the Discovery Flow system during **Remediation Phase 1 (75% complete)**. It consolidates task tracking, implementation status, and development patterns for the ongoing 6-8 week remediation effort.

> **📋 Purpose**: Support ongoing remediation work with practical guidance
> **🔄 Context**: Active development during transition from mixed to unified patterns
> **📚 Architecture**: See `DISCOVERY_FLOW_ARCHITECTURE.md` for architectural overview

## 📊 **Current Implementation Status**

### **Overall Progress: 75% Complete**

#### ✅ **Completed Infrastructure (100%)**
- **PostgreSQL-Only State**: SQLite completely eliminated
- **CrewAI Flow Framework**: `@start/@listen` decorators implemented
- **Multi-Tenant Architecture**: Row-level security working
- **Event Bus Coordination**: Real-time flow communication
- **API v3 Infrastructure**: All endpoints functional

#### ⚠️ **Active Work Areas (25% Remaining)**
- **Session ID Cleanup**: 132+ files need session_id → flow_id migration
- **API Version Consolidation**: Frontend still uses mixed v1/v3
- **Flow Context Sync**: Bug fixes needed for context propagation
- **UI Integration Issues**: Field mapping shows "0 active flows"

## 🛠️ **Development Setup**

### **Required Environment**
```bash
# All development MUST be done in Docker containers
docker-compose up -d --build

# Verify all services running
docker-compose ps

# Access backend for development
docker exec -it migration_backend bash

# Access frontend for development  
docker exec -it migration_frontend bash
```

### **Remediation-Specific Tools**
```bash
# Session ID audit (track cleanup progress)
docker exec -it migration_backend grep -r "session_id" app/ --include="*.py" | wc -l
# Target: Reduce from 132+ to 0

# API version usage audit
docker exec -it migration_frontend grep -r "/api/v" src/ --include="*.ts" --include="*.tsx"

# Flow context debugging
docker exec -it migration_backend python -c "
from app.services.crewai_flows.flow_state_manager import FlowStateManager
print('Flow state manager loaded successfully')
"

# Database migration status
docker exec -it migration_backend alembic current
docker exec -it migration_backend alembic history
```

## 🎯 **Implementation Patterns**

### **Current Flow Creation Pattern**
```python
# Use this pattern (Phase 5 - Current)
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
from app.core.context import get_request_context

async def create_discovery_flow(
    flow_name: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str
) -> str:
    """Create new discovery flow with proper context"""
    
    context = RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id
    )
    
    # Initialize CrewAI Flow
    flow = UnifiedDiscoveryFlow()
    flow_id = await flow.initialize_with_context(context, flow_name)
    
    return flow_id
```

### **⚠️ Avoid Legacy Patterns**
```python
# DON'T USE - Session-based patterns (Phase 2 - Deprecated)
session_id = "disc_session_12345"  # Use flow_id instead
session_manager.create_session()   # Use flow creation

# DON'T USE - Direct SQLite access (Phase 3 - Eliminated)
sqlite_db.save_state()            # Use PostgreSQL persistence
```

### **Database Access Pattern**
```python
# Current pattern (PostgreSQL-only)
from app.core.database import AsyncSessionLocal
from app.repositories.context_aware_repository import ContextAwareRepository

class DiscoveryFlowRepository(ContextAwareRepository):
    """Repository with automatic multi-tenant scoping"""
    
    async def get_flow_by_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get flow with automatic tenant filtering"""
        async with AsyncSessionLocal() as session:
            query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == self.client_account_id
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
```

### **API Endpoint Implementation**
```python
# Current pattern (v3 API with v1 compatibility)
from fastapi import APIRouter, Depends, HTTPException
from app.core.context import get_request_context, RequestContext

router = APIRouter(prefix="/api/v3/discovery-flow")

@router.post("/flows")
async def create_flow(
    flow_data: FlowCreateRequest,
    context: RequestContext = Depends(get_request_context)
):
    """Create discovery flow with proper multi-tenant context"""
    
    try:
        flow_id = await create_discovery_flow(
            flow_name=flow_data.flow_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id
        )
        
        return {"flow_id": flow_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Flow creation failed: {str(e)}")
        raise HTTPException(500, "Flow creation failed")
```

## 🔧 **Remediation Tasks**

### **Week 1-2: Critical Bug Fixes**

#### **Task 1: Fix Flow Context Synchronization**
```python
# Problem: Context headers not propagated properly
# Location: app/core/context.py, app/api/middleware/

# Fix pattern:
async def propagate_context_headers(request: Request, call_next):
    """Ensure context headers flow through entire request cycle"""
    
    # Extract context
    client_id = request.headers.get('X-Client-Account-ID')
    engagement_id = request.headers.get('X-Engagement-ID')
    
    if client_id and engagement_id:
        # Set request-scoped context
        context_var.set(RequestContext(
            client_account_id=client_id,
            engagement_id=engagement_id
        ))
    
    response = await call_next(request)
    return response
```

#### **Task 2: Fix Field Mapping UI Issues**
```typescript
// Problem: Shows "0 active flows" despite flows existing
// Location: src/pages/discovery/AttributeMapping.tsx

// Current issue: Mixed API usage
const getActiveFlows = async () => {
  // ❌ Wrong - calls v1 API but expects v3 response format
  const response = await fetch('/api/v1/discovery/flows/active');
  
  // ✅ Fix - use consistent API version
  const response = await fetch('/api/v3/discovery-flow/flows?status=active', {
    headers: getMultiTenantHeaders()
  });
};
```

### **Week 3-4: API Consolidation**

#### **Task 3: Frontend API Migration**
```typescript
// Migration checklist for frontend components:

// 1. Update useUnifiedDiscoveryFlow hook
export const useUnifiedDiscoveryFlow = () => {
  // Change from mixed v1/v3 to v3 only
  const API_BASE = '/api/v3/discovery-flow';
  
  const createFlow = async (data: FlowCreateData) => {
    return await fetch(`${API_BASE}/flows`, {
      method: 'POST',
      headers: getMultiTenantHeaders(),
      body: JSON.stringify(data)
    });
  };
};

// 2. Update all component API calls
// Files to update:
// - src/pages/discovery/CMDBImport.tsx
// - src/pages/discovery/AttributeMapping.tsx  
// - src/components/DiscoveryFlowStatus.tsx
```

### **Week 5-6: Session ID Cleanup**

#### **Task 4: Systematic Session ID Elimination**
```bash
# Step 1: Find all session_id references
find backend/app -name "*.py" -exec grep -l "session_id" {} \;

# Step 2: Categorize by priority
# High priority: API endpoints, models, repositories
# Medium priority: Services, utilities
# Low priority: Comments, documentation

# Step 3: Replace patterns
# Replace: session_id → flow_id
# Replace: disc_session_ → flow_
# Replace: import_session_id → flow_id
```

```python
# Common replacement patterns:

# Before (deprecated)
class DiscoverySession(Base):
    session_id = Column(String, primary_key=True)
    
def get_by_session_id(session_id: str):
    return query.filter(model.session_id == session_id)

# After (current)
class DiscoveryFlow(Base):
    flow_id = Column(PostgresUUID, primary_key=True)
    
def get_by_flow_id(flow_id: str):
    return query.filter(model.flow_id == flow_id)
```

## 🧪 **Testing During Remediation**

### **Test Categories**
```python
# 1. Infrastructure tests (should pass)
pytest tests/unit/test_postgres_store.py
pytest tests/unit/test_multi_tenant_repository.py
pytest tests/unit/test_crewai_flows.py

# 2. Integration tests (mixed results expected)
pytest tests/integration/test_discovery_flow_api.py
pytest tests/integration/test_field_mapping.py  # Known failures

# 3. End-to-end tests (manual during remediation)
# Test complete flow: create → import → map → process
```

### **Manual Testing Checklist**
```bash
# Test flow creation
curl -X POST http://localhost:8000/api/v3/discovery-flow/flows \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: test-client" \
  -H "X-Engagement-ID: test-engagement" \
  -d '{"flow_name": "Test Flow"}'

# Test flow status
curl http://localhost:8000/api/v3/discovery-flow/flows/{flow_id}/status \
  -H "X-Client-Account-ID: test-client" \
  -H "X-Engagement-ID: test-engagement"

# Test file upload
curl -X POST http://localhost:8000/api/v3/data-import/imports \
  -H "X-Client-Account-ID: test-client" \
  -H "X-Engagement-ID: test-engagement" \
  -F "file=@test.csv" \
  -F "flow_id=test-flow-id"
```

## 🚨 **Common Issues & Solutions**

### **Issue 1: "Flow not found" errors**
```python
# Cause: Context headers missing or incorrect
# Solution: Always include multi-tenant headers

# ❌ Wrong
response = await fetch('/api/v3/discovery-flow/flows/123')

# ✅ Correct  
response = await fetch('/api/v3/discovery-flow/flows/123', {
  headers: {
    'X-Client-Account-ID': clientAccountId,
    'X-Engagement-ID': engagementId
  }
})
```

### **Issue 2: Data written to wrong tables**
```python
# Cause: Context not set in database operations
# Solution: Use ContextAwareRepository

# ❌ Wrong
async with AsyncSessionLocal() as session:
    result = await session.execute(query)  # No tenant filtering

# ✅ Correct
repository = FlowRepository(session, client_account_id)
result = await repository.get_flows()  # Automatic tenant filtering
```

### **Issue 3: CrewAI agent failures**
```python
# Cause: Missing or incorrect agent configuration
# Solution: Verify agent service layer integration

# Check agent health
from app.services.agent_service_layer import AgentServiceLayer
agent_service = AgentServiceLayer()
health = await agent_service.check_agent_health()
print(f"Agent health: {health}")
```

## 📝 **Implementation Checklist**

### **For New Features**
- [ ] Use flow_id as primary identifier
- [ ] Include multi-tenant context headers
- [ ] Use API v3 endpoints
- [ ] Implement with ContextAwareRepository
- [ ] Add proper error handling
- [ ] Include integration tests
- [ ] Document any workarounds for known issues

### **For Bug Fixes**
- [ ] Identify if issue relates to remediation work
- [ ] Check context header propagation
- [ ] Verify API version consistency
- [ ] Test with multiple tenants
- [ ] Validate against current architecture patterns
- [ ] Update related documentation

### **For Session ID Cleanup**
- [ ] Audit file for all session_id references
- [ ] Replace with flow_id equivalent
- [ ] Update database queries
- [ ] Update API calls
- [ ] Test functionality with new identifiers
- [ ] Remove any session-based utilities

## 🔮 **Post-Remediation Targets**

### **Clean Implementation Patterns (Target)**
```python
# Target: Pure CrewAI Flow patterns
class DiscoveryFlow(Flow[DiscoveryFlowState]):
    @start()
    def initialize(self):
        # Clean initialization without legacy references
        
    @listen(initialize)
    def import_data(self):
        # Direct crew execution
        
    @listen(import_data)
    def map_fields(self):
        # Seamless phase transitions
```

### **Performance Targets**
- **API Response Time**: <500ms for status calls
- **Flow Initialization**: <2 seconds
- **Phase Transitions**: <1 second
- **File Processing**: <30 seconds per MB

### **Quality Targets**
- **Test Coverage**: >90% for new code
- **Documentation**: 100% API endpoint coverage
- **Code Consistency**: Zero mixed identifier usage
- **Performance**: No regression from current state

---

**Implementation Status**: 75% complete, 6-8 weeks remaining  
**Priority**: Critical bug fixes first, then systematic cleanup  
**Support**: See `DISCOVERY_FLOW_TROUBLESHOOTING.md` for issue resolution

*This guide consolidates implementation tracking from multiple analysis documents and provides practical remediation guidance.*