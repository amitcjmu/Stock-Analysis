# Agent 3: APIs & Services Cleanup

## 🎯 **Your Mission**
Remove all session_id references from API endpoints and service layers. Ensure all APIs use flow_id exclusively.

## 📋 **Your Files**

### **1. V3 Data Import API**
**File**: `/backend/app/api/v3/data_import.py`  
**Lines to modify**: 158, 164, 171 (around debug endpoint)

**Specific Changes**:
```python
# REMOVE session_id from debug response:
# Line ~65 in debug endpoint
"session_id": context.session_id,  # REMOVE THIS LINE

# Ensure response only includes:
return {
    "flow_id": context.flow_id,
    "debug_info": debug_data
}
```

### **2. V1 Unified Discovery API**
**File**: `/backend/app/api/v1/unified_discovery.py`  
**Lines to modify**: 45, 78, 123, 156, 304-315

**Specific Changes**:
```python
# Line 45 - UPDATE route:
# FROM: @router.get("/flow/status/{session_id}")
# TO: @router.get("/flow/status/{flow_id}")
async def get_flow_status(flow_id: str, context: RequestContext = Depends(get_request_context)):
    flow = await discovery_service.get_flow_by_flow_id(flow_id)  # UPDATE method call
    return flow_status_response(flow)

# Line 78 - UPDATE initialize_flow:
@router.post("/flow/initialize")
async def initialize_flow(request: FlowInitRequest):
    # REMOVE any session_id generation
    # REMOVE: session_id = f"disc_session_{uuid.uuid4()}"
    flow_id = await discovery_service.create_flow(...)
    return {"flow_id": flow_id, "status": "initialized"}

# UPDATE all other endpoints to use flow_id parameter instead of session_id
```

### **3. Discovery Flow Service**
**File**: `/backend/app/services/discovery_flow_service.py`  
**Lines to modify**: 90, 167-180, 461-469

**Specific Changes**:
```python
# Line 90 - REMOVE import_session_id parameter:
async def create_discovery_flow(
    flow_id: str,
    raw_data: List[Dict[str, Any]],
    metadata: Dict[str, Any] = None,
    data_import_id: str = None,  # Keep this if needed
    # REMOVE: import_session_id parameter
    user_id: str = None
)

# Lines 167-180 - REMOVE entire method:
async def get_flow_by_import_session(self, import_session_id: str) -> Optional[DiscoveryFlow]:
    # DELETE ENTIRE METHOD

# Lines 461-469 - REMOVE session compatibility:
# In create_flow_from_crewai method, REMOVE:
if metadata and "import_session_id" in metadata:
    data_import_id = metadata["import_session_id"]
elif crewai_state and "session_id" in crewai_state:
    data_import_id = crewai_state["session_id"]
```

### **4. Data Import Service**
**File**: `/backend/app/services/data_import_service.py` (if exists)  
**Action**: Update all session_id references to flow_id

**Changes**:
```python
# Update method signatures
# FROM: async def import_data(session_id: str, ...)
# TO: async def import_data(flow_id: str, ...)

# Update all internal logic to use flow_id
```

### **5. Unified Discovery Service**
**File**: `/backend/app/services/unified_discovery_service.py` (if exists)  
**Action**: Remove or update session methods

**Changes**:
```python
# REMOVE methods like:
async def get_by_session_id(...)
async def create_session(...)

# UPDATE to use flow_id exclusively
```

### **6. V2 Discovery Flow API**
**File**: `/backend/app/api/v2/discovery_flow_v2.py` (if exists)  
**Action**: Clean up any remaining session_id references

### **7. Background Tasks**
**File**: `/backend/app/tasks/discovery_tasks.py` (if exists)  
**Action**: Update task parameters

**Changes**:
```python
# UPDATE task signatures:
# FROM: @celery_app.task
# def process_discovery(session_id: str):
# TO: def process_discovery(flow_id: str):
```

### **8. WebSocket Handlers**
**File**: `/backend/app/websocket/handlers.py` (if exists)  
**Action**: Update subscriptions

**Changes**:
```python
# UPDATE subscription patterns:
# FROM: f"session:{session_id}"
# TO: f"flow:{flow_id}"

# Update all event emissions to use flow_id
```

### **9. Agent Bridge Service**
**File**: `/backend/app/services/agent_bridge_service.py` (if exists)  
**Action**: Update context passing

**Changes**:
```python
# Ensure agent context uses flow_id
# Remove any session_id from agent communications
```

### **10. Admin/Migration Status Endpoint**
**File**: `/backend/app/api/v1/admin/session_migration_status.py` (if exists)  
**Action**: DELETE if it exists (no longer needed)

## ✅ **Verification Steps**

```bash
# Check each API file
docker exec -it migration_backend grep -n "session_id" app/api/v3/data_import.py
docker exec -it migration_backend grep -n "session_id" app/api/v1/unified_discovery.py

# Check all services
docker exec -it migration_backend grep -r "session_id" app/services/ --include="*.py"

# Test API endpoints
curl -X GET http://localhost:8000/api/v1/unified-discovery/flow/status/[flow-id]
curl -X POST http://localhost:8000/api/v3/discovery-flow/flows

# Run API tests
docker exec -it migration_backend pytest tests/api/ -v
```

## 🚨 **Critical Notes**

1. **Wait for Agent 1 to complete context.py** before testing APIs
2. **Coordinate with Agent 2** if you need model changes
3. **Update API documentation** if you change endpoint signatures
4. Some endpoints might need both URL and body parameter updates

## 📝 **Progress Tracking**

Update the master plan tracker after each file:
- [ ] `/backend/app/api/v3/data_import.py`
- [ ] `/backend/app/api/v1/unified_discovery.py`
- [ ] `/backend/app/services/discovery_flow_service.py`
- [ ] `/backend/app/services/data_import_service.py`
- [ ] `/backend/app/services/unified_discovery_service.py`
- [ ] `/backend/app/api/v2/discovery_flow_v2.py`
- [ ] `/backend/app/tasks/discovery_tasks.py`
- [ ] `/backend/app/websocket/handlers.py`
- [ ] `/backend/app/services/agent_bridge_service.py`
- [ ] Admin endpoints cleanup

## 🔄 **Commit Pattern**

```bash
git add app/api/v3/data_import.py
git commit -m "cleanup: Remove session_id from v3 data import API"

git add app/api/v1/unified_discovery.py
git commit -m "cleanup: Update unified discovery API to use flow_id"

git add app/services/discovery_flow_service.py
git commit -m "cleanup: Remove session_id methods from discovery flow service"
```

## ⚠️ **If You Get Stuck**

- Check if frontend is calling deprecated endpoints
- Look for Swagger/OpenAPI definitions that need updating
- Coordinate with Agent 4 if frontend expects certain API responses
- Test with Postman/curl to verify endpoints work

---

**Remember**: APIs are the contract with frontend. Make sure you're consistent in using flow_id everywhere!