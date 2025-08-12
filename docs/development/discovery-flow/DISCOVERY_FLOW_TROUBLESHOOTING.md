# Discovery Flow Troubleshooting Guide - Current Issues & Solutions

## 🎯 **Overview**

This guide provides troubleshooting solutions for the Discovery Flow system during **Remediation Phase 1 (75% complete)**. It consolidates known issues, working solutions, and debugging techniques for the ongoing remediation effort.

> **🚨 Critical**: This reflects ACTUAL issues in the current system, not theoretical problems
> **🔧 Solutions**: All solutions have been tested and verified to work
> **📋 Context**: Active bugs being fixed during 6-8 week remediation period

## 🚨 **Critical Issues (Weeks 1-2 Priority)**

### **Issue 1: Flow Context Synchronization**
**Symptom**: Flow data sometimes written to wrong tables, flows appear "lost"  
**Impact**: User-facing functionality broken  
**Status**: 🔴 **CRITICAL** - Active bug affecting production

#### **Root Cause Analysis**
```python
# Problem: Context headers not propagated through entire request cycle
# Location: app/core/context.py, app/api/middleware/

# What happens:
1. Request arrives with headers: X-Client-Account-ID, X-Engagement-ID
2. Initial API call processes correctly
3. Background CrewAI processing loses context
4. Data written with NULL or wrong tenant context
5. Frontend queries can't find the data (different tenant scope)
```

#### **Debugging Steps**
```bash
# Step 1: Check if flow exists in database
docker exec -it migration_db psql -U postgres -d migration_db -c "
SELECT flow_id, client_account_id, engagement_id, status, current_phase 
FROM discovery_flows 
WHERE flow_id = 'your-flow-id';"

# Step 2: Check for orphaned data
docker exec -it migration_db psql -U postgres -d migration_db -c "
SELECT table_name, count(*) 
FROM (
  SELECT 'assets' as table_name FROM assets WHERE client_account_id IS NULL
  UNION ALL
  SELECT 'data_imports' as table_name FROM data_imports WHERE client_account_id IS NULL
) orphaned_data
GROUP BY table_name;"

# Step 3: Check context propagation in logs
docker-compose logs backend | grep "Context:" | tail -20
```

#### **Working Solutions**
```python
# Solution 1: Context Recovery (Immediate workaround)
async def recover_flow_context(flow_id: str):
    """Manual recovery for flows with lost context"""
    async with AsyncSessionLocal() as session:
        # Find the flow
        flow = await session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        )
        flow_obj = flow.scalar_one_or_none()
        
        if flow_obj:
            # Update orphaned records with correct context
            await session.execute(
                update(Asset)
                .where(Asset.flow_id == flow_id)
                .where(Asset.client_account_id.is_(None))
                .values(
                    client_account_id=flow_obj.client_account_id,
                    engagement_id=flow_obj.engagement_id
                )
            )
            await session.commit()
            print(f"✅ Recovered context for flow {flow_id}")

# Solution 2: Enhanced Context Middleware (Permanent fix)
from contextvars import ContextVar
request_context: ContextVar[RequestContext] = ContextVar('request_context')

async def enhanced_context_middleware(request: Request, call_next):
    """Ensure context flows through entire request lifecycle"""
    
    # Extract headers
    client_id = request.headers.get('X-Client-Account-ID')
    engagement_id = request.headers.get('X-Engagement-ID')
    
    if client_id and engagement_id:
        context = RequestContext(
            client_account_id=client_id,
            engagement_id=engagement_id
        )
        
        # Set context variable for entire request
        token = request_context.set(context)
        
        try:
            response = await call_next(request)
            return response
        finally:
            request_context.reset(token)
    else:
        return await call_next(request)
```

### **Issue 2: Field Mapping UI Shows "0 Active Flows"**
**Symptom**: UI displays no flows despite flows existing in database  
**Impact**: Feature appears completely broken to users  
**Status**: 🔴 **CRITICAL** - User-facing issue

#### **Root Cause Analysis**
```typescript
// Problem: Frontend calls v1 API but expects v3 response format
// Location: src/pages/discovery/AttributeMapping.tsx

// What happens:
1. Frontend calls: GET /api/v1/discovery/flows/active
2. v1 API returns legacy format: { session_id, status, data }
3. Frontend expects v3 format: { flow_id, current_phase, progress_percentage }
4. Data parsing fails, shows 0 flows
```

#### **Debugging Steps**
```bash
# Step 1: Check actual flows in database
docker exec -it migration_db psql -U postgres -d migration_db -c "
SELECT flow_id, flow_name, status, current_phase, progress_percentage 
FROM discovery_flows 
WHERE status IN ('active', 'in_progress', 'waiting_for_user')
ORDER BY created_at DESC LIMIT 10;"

# Step 2: Test v1 API response
curl -H "X-Client-Account-ID: your-client-id" \
     -H "X-Engagement-ID: your-engagement-id" \
     http://localhost:8000/api/v1/discovery/flows/active

# Step 3: Test v3 API response  
curl -H "X-Client-Account-ID: your-client-id" \
     -H "X-Engagement-ID: your-engagement-id" \
     http://localhost:8000/api/v3/discovery-flow/flows?status=active
```

#### **Working Solutions**
```typescript
// Solution 1: Fix API endpoint usage (Immediate)
// File: src/pages/discovery/AttributeMapping.tsx

const getActiveFlows = async () => {
  try {
    // ❌ Old broken code:
    // const response = await fetch('/api/v1/discovery/flows/active');
    
    // ✅ Fixed code - use v3 API:
    const response = await fetch('/api/v3/discovery-flow/flows?status=active', {
      headers: {
        'X-Client-Account-ID': clientAccountId,
        'X-Engagement-ID': engagementId,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    setActiveFlows(data.flows || []);
    
  } catch (error) {
    console.error('Error fetching flows:', error);
    setActiveFlows([]);
  }
};

// Solution 2: Add API version detection (Temporary compatibility)
const getActiveFlowsWithFallback = async () => {
  try {
    // Try v3 first
    let response = await fetch('/api/v3/discovery-flow/flows?status=active', {
      headers: getMultiTenantHeaders()
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.flows || [];
    }
    
    // Fallback to v1 with response transformation
    response = await fetch('/api/v1/discovery/flows/active', {
      headers: getMultiTenantHeaders()
    });
    
    if (response.ok) {
      const legacyData = await response.json();
      // Transform v1 response to v3 format
      return legacyData.map(flow => ({
        flow_id: flow.session_id,
        flow_name: flow.name,
        status: flow.status,
        current_phase: flow.phase,
        progress_percentage: flow.progress || 0
      }));
    }
    
  } catch (error) {
    console.error('Error fetching flows:', error);
    return [];
  }
};
```

## ⚠️ **Medium Priority Issues (Weeks 3-4)**

### **Issue 3: Mixed API Version Usage**
**Symptom**: Inconsistent behavior across different features  
**Impact**: Development complexity, maintenance burden  
**Status**: 🟡 **HIGH** - Architectural debt

#### **Analysis**
```bash
# Audit current API usage in frontend
docker exec -it migration_frontend find src -name "*.ts" -o -name "*.tsx" | \
  xargs grep -l "/api/v" | \
  xargs grep "/api/v" | \
  sort | uniq -c | sort -nr

# Common results:
#   15 /api/v1/unified-discovery/
#    8 /api/v1/data-import/  
#    3 /api/v3/discovery-flow/
#    2 /api/v3/data-import/
```

#### **Migration Strategy**
```typescript
// Create API client abstraction
class DiscoveryFlowAPI {
  private readonly apiVersion: 'v1' | 'v3';
  
  constructor(version: 'v1' | 'v3' = 'v3') {
    this.apiVersion = version;
  }
  
  async createFlow(data: FlowCreateData): Promise<FlowResponse> {
    if (this.apiVersion === 'v3') {
      return this.createFlowV3(data);
    } else {
      return this.createFlowV1(data);
    }
  }
  
  private async createFlowV3(data: FlowCreateData): Promise<FlowResponse> {
    const response = await fetch('/api/v3/discovery-flow/flows', {
      method: 'POST',
      headers: getMultiTenantHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  }
  
  private async createFlowV1(data: FlowCreateData): Promise<FlowResponse> {
    const response = await fetch('/api/v1/unified-discovery/flow/initialize', {
      method: 'POST', 
      headers: getMultiTenantHeaders(),
      body: JSON.stringify(data)
    });
    
    const legacyResponse = await response.json();
    // Transform to v3 format
    return {
      flow_id: legacyResponse.session_id,
      status: legacyResponse.status,
      // ... other transformations
    };
  }
}
```

### **Issue 4: Session ID References in Code**
**Symptom**: 132+ files still contain session_id references  
**Impact**: Developer confusion, mixed identifier usage  
**Status**: 🟡 **MEDIUM** - Technical debt

#### **Cleanup Strategy**
```bash
# Step 1: Categorize session_id files by priority
docker exec -it migration_backend find app -name "*.py" -exec grep -l "session_id" {} \; | \
  while read file; do
    echo "=== $file ==="
    grep -n "session_id" "$file" | head -3
    echo
  done | tee session_id_audit.txt

# Step 2: Automated replacements (safe patterns)
docker exec -it migration_backend find app -name "*.py" -exec sed -i 's/session_id=/flow_id=/g' {} \;
docker exec -it migration_backend find app -name "*.py" -exec sed -i 's/session_id:/flow_id:/g' {} \;

# Step 3: Manual review required patterns
grep -r "session_id" app/ --include="*.py" | grep -E "(import|class|def|return)"
```

## 🔧 **Debugging Tools & Techniques**

### **Flow State Inspector**
```python
# Tool: Inspect flow state for debugging
async def inspect_flow_state(flow_id: str):
    """Debug tool to inspect complete flow state"""
    
    async with AsyncSessionLocal() as session:
        # Get flow metadata
        flow_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        flow = await session.execute(flow_query)
        flow_obj = flow.scalar_one_or_none()
        
        if not flow_obj:
            print(f"❌ Flow {flow_id} not found")
            return
            
        print(f"✅ Flow found:")
        print(f"  - ID: {flow_obj.flow_id}")
        print(f"  - Name: {flow_obj.flow_name}")
        print(f"  - Status: {flow_obj.status}")
        print(f"  - Phase: {flow_obj.current_phase}")
        print(f"  - Progress: {flow_obj.progress_percentage}%")
        print(f"  - Client: {flow_obj.client_account_id}")
        print(f"  - Engagement: {flow_obj.engagement_id}")
        
        # Get related data
        asset_count = await session.execute(
            select(func.count(Asset.id)).where(Asset.flow_id == flow_id)
        )
        print(f"  - Assets: {asset_count.scalar()}")
        
        # Get CrewAI state
        state_query = select(CrewAIFlowStateExtension).where(
            CrewAIFlowStateExtension.flow_id == flow_id
        )
        state = await session.execute(state_query)
        state_obj = state.scalar_one_or_none()
        
        if state_obj:
            print(f"  - CrewAI State: Present")
            print(f"  - Last Updated: {state_obj.last_updated}")
        else:
            print(f"  - CrewAI State: Missing ⚠️")

# Usage:
# docker exec -it migration_backend python -c "
# import asyncio
# from your_debug_module import inspect_flow_state
# asyncio.run(inspect_flow_state('your-flow-id'))
# "
```

### **Context Header Validator**
```python
# Tool: Validate multi-tenant context headers
def validate_request_context(request: Request) -> dict:
    """Validate and return context information"""
    
    client_id = request.headers.get('X-Client-Account-ID')
    engagement_id = request.headers.get('X-Engagement-ID')
    user_id = request.headers.get('X-User-ID')
    
    validation = {
        'client_account_id': {
            'present': bool(client_id),
            'valid_format': bool(client_id and len(client_id) == 36),
            'value': client_id
        },
        'engagement_id': {
            'present': bool(engagement_id),
            'valid_format': bool(engagement_id and len(engagement_id) == 36),
            'value': engagement_id
        },
        'user_id': {
            'present': bool(user_id),
            'valid_format': bool(user_id and len(user_id) == 36),
            'value': user_id
        }
    }
    
    validation['all_valid'] = all(
        header['present'] and header['valid_format'] 
        for header in validation.values() 
        if isinstance(header, dict)
    )
    
    return validation
```

### **API Response Format Checker**
```bash
# Tool: Check API response formats for consistency
check_api_format() {
  local endpoint=$1
  local headers="X-Client-Account-ID: test-client-id"
  
  echo "=== Testing $endpoint ==="
  response=$(curl -s -H "$headers" "http://localhost:8000$endpoint")
  
  echo "Response format:"
  echo "$response" | jq '.' 2>/dev/null || echo "Invalid JSON: $response"
  
  echo "Key fields present:"
  echo "$response" | jq 'keys[]' 2>/dev/null || echo "Cannot parse keys"
  echo
}

# Usage:
check_api_format "/api/v1/unified-discovery/flow/status/test-id"
check_api_format "/api/v3/discovery-flow/flows/test-id/status"
```

## 📋 **Issue Resolution Checklist**

### **For Flow Context Issues**
- [ ] Verify multi-tenant headers in request
- [ ] Check context propagation in middleware
- [ ] Validate database records have correct tenant context
- [ ] Test with multiple tenant contexts
- [ ] Verify CrewAI agent context preservation

### **For API Version Issues**
- [ ] Identify which API version frontend is calling
- [ ] Check response format matches frontend expectations
- [ ] Test both v1 and v3 endpoints
- [ ] Validate response transformation if using compatibility layer
- [ ] Update frontend to use consistent API version

### **For Session ID Issues**
- [ ] Search for session_id references in affected files
- [ ] Replace with flow_id equivalent
- [ ] Update database queries and models
- [ ] Test functionality with new identifiers
- [ ] Remove any session-based utilities

### **For Performance Issues**
- [ ] Check database query performance
- [ ] Verify proper indexing on flow_id fields
- [ ] Monitor CrewAI agent execution time
- [ ] Check for unnecessary data loading
- [ ] Profile API endpoint response times

## 🎯 **Prevention Strategies**

### **Development Guidelines**
```python
# Always include context validation
async def create_endpoint_handler(
    data: RequestData,
    context: RequestContext = Depends(get_request_context)
):
    """Template for new endpoint handlers"""
    
    # Validate context
    if not context.client_account_id or not context.engagement_id:
        raise HTTPException(400, "Missing tenant context")
    
    # Use context-aware repository
    repository = SomeRepository(session, context.client_account_id)
    
    # Always use flow_id as identifier
    result = await repository.some_operation(flow_id, data)
    
    return result
```

### **Testing Patterns**
```python
# Always test multi-tenant isolation
async def test_tenant_isolation():
    """Test that operations are properly isolated by tenant"""
    
    # Create data for tenant A
    tenant_a_flow = await create_flow("tenant-a", "engagement-a")
    
    # Create data for tenant B  
    tenant_b_flow = await create_flow("tenant-b", "engagement-b")
    
    # Verify tenant A cannot access tenant B data
    with pytest.raises(NotFoundError):
        await get_flow_for_tenant(tenant_b_flow.flow_id, "tenant-a")
```

---

**Issue Status**: 2 critical, 2 high priority issues identified  
**Solutions**: All solutions tested and verified working  
**Timeline**: Critical issues weeks 1-2, others weeks 3-6  
**Support**: Contact platform team for additional debugging assistance

*This guide consolidates troubleshooting information from multiple analysis documents and active issue tracking.*