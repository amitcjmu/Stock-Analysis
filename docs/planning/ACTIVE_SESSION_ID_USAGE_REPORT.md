# Active session_id Usage Report - Remediation Blockers

## 🎯 **Executive Summary**

This report identifies **active session_id usage** in the codebase that blocks completion of the session_id → flow_id migration. These are **executing code paths** that need modification during Remediation Phase 1, not legacy references or documentation.

**Total Active Usage Found**: 47 files with active session_id usage  
**Critical Blockers**: 18 files requiring immediate attention  
**Estimated Cleanup Time**: 4-6 weeks (aligns with remediation timeline)

## 🚨 **CRITICAL PRIORITY (Must Fix - Weeks 1-2)**

### **Backend API Endpoints (Active Production Code)**

#### **1. Core Context System**
**File**: `/backend/app/core/context.py`  
**Lines**: 27, 55, 82  
**Issue**: RequestContext class actively propagates session_id  
```python
# ACTIVE USAGE - Line 27
@dataclass
class RequestContext:
    client_account_id: str
    engagement_id: str
    session_id: Optional[str] = None  # ❌ STILL ACTIVE

# ACTIVE USAGE - Line 55  
def get_session_context(session_id: str) -> RequestContext:
    # Function actively called by middleware
    return RequestContext(session_id=session_id)
```
**Impact**: Core system component that propagates session_id to all downstream operations

#### **2. API v1 Session Endpoints**
**File**: `/backend/app/api/v1/endpoints/sessions.py`  
**Lines**: 46, 55, 78  
**Issue**: Active endpoints returning session_id to frontend  
```python
# ACTIVE USAGE - Line 46
@router.get("/current")
async def get_current_session(context: RequestContext = Depends(get_request_context)):
    return {
        "id": context.session_id,  # ❌ ACTIVELY RETURNED
        "client_account_id": context.client_account_id
    }

# ACTIVE USAGE - Line 55
@router.post("/create")  
async def create_session(session_data: SessionCreateRequest):
    session_id = f"disc_session_{uuid.uuid4()}"  # ❌ ACTIVELY CREATED
    return {"session_id": session_id}
```
**Impact**: Frontend receives session_id from these endpoints and uses them in subsequent calls

#### **3. API v3 Inadvertent Exposure**
**File**: `/backend/app/api/v3/data_import.py`  
**Lines**: 158, 164, 171  
**Issue**: V3 API accidentally exposing session_id in responses  
```python
# ACTIVE USAGE - Line 158
@router.post("/imports/{import_id}/debug")
async def get_import_debug_info(context: RequestContext = Depends(get_request_context)):
    return {
        "flow_id": context.flow_id,
        "session_id": context.session_id,  # ❌ V3 API EXPOSING DEPRECATED FIELD
        "debug_info": debug_data
    }
```
**Impact**: New V3 API perpetuating session_id usage instead of eliminating it

### **Database Models & Queries (Active Schema)**

#### **4. Discovery Flow Model**
**File**: `/backend/app/models/discovery_flow.py`  
**Lines**: 34, 67, 89  
**Issue**: Database model with active session_id foreign key  
```python
# ACTIVE USAGE - Line 34
class DiscoveryFlow(Base):
    __tablename__ = "discovery_flows"
    
    flow_id = Column(UUID(as_uuid=True), primary_key=True)
    import_session_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # ❌ ACTIVE FK
    
    # ACTIVE USAGE - Line 67
    @property
    def session_id(self):
        return self.import_session_id  # ❌ PROPERTY ACTIVELY ACCESSED
```
**Impact**: Database schema actively stores and indexes session_id relationships

#### **5. Repository Query Methods**
**File**: `/backend/app/repositories/discovery_flow_repository.py`  
**Lines**: 45, 67, 89, 123  
**Issue**: Repository methods actively filtering by session_id  
```python
# ACTIVE USAGE - Line 45
async def get_flow_by_session_id(self, session_id: str) -> Optional[DiscoveryFlow]:
    query = select(DiscoveryFlow).where(DiscoveryFlow.import_session_id == session_id)
    result = await self.session.execute(query)  # ❌ ACTIVELY QUERIED
    return result.scalar_one_or_none()

# ACTIVE USAGE - Line 67
async def get_flows_for_session(self, session_id: str) -> List[DiscoveryFlow]:
    # Method actively called by service layer
    return await self._filter_by_session(session_id)
```
**Impact**: Data access layer actively queries and filters by session_id

#### **6. Asset Model Relationships**
**File**: `/backend/app/models/asset.py`  
**Lines**: 93, 198  
**Issue**: Asset model with session_id foreign key still actively used  
```python
# ACTIVE USAGE - Line 93
class Asset(Base):
    flow_id = Column(PostgresUUID(as_uuid=True), ForeignKey('discovery_flows.flow_id'))
    session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('data_import_sessions.id'))  # ❌ ACTIVE FK
    
# ACTIVE USAGE - Line 198  
    @property
    def legacy_session_id(self):
        return self.session_id  # ❌ ACTIVELY ACCESSED BY SERVICE LAYER
```
**Impact**: Asset relationships still depend on session_id for data integrity

## 🔴 **HIGH PRIORITY (Weeks 3-4)**

### **Frontend Active Usage**

#### **7. Main Discovery Hook**
**File**: `/src/hooks/useUnifiedDiscoveryFlow.ts`  
**Lines**: 10, 152, 161-164, 228-232  
**Issue**: Hook actively accepts and processes session_id parameters  
```typescript
// ACTIVE USAGE - Line 10
interface DiscoveryFlowOptions {
  flowId?: string;
  sessionId?: string;  // ❌ STILL ACTIVELY ACCEPTED
  enableRealTimeUpdates?: boolean;
}

// ACTIVE USAGE - Lines 161-164
const getFlowId = useCallback(() => {
  if (options.sessionId) {
    // ❌ ACTIVELY CONVERTS SESSION_ID TO FLOW_ID
    return SessionToFlowMigration.convertSessionToFlowId(options.sessionId);
  }
  return options.flowId;
}, [options.sessionId, options.flowId]);

// ACTIVE USAGE - Lines 228-232
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get('sessionId');  // ❌ ACTIVELY READS FROM URL
  if (sessionId) {
    setCurrentSessionId(sessionId);
  }
}, []);
```
**Impact**: Primary frontend hook still actively supporting session_id workflow

#### **8. CMDB Import Component**
**File**: `/src/pages/discovery/CMDBImport.tsx`  
**Lines**: 174-198, 234, 267  
**Issue**: Component functions actively using session_id for navigation  
```typescript
// ACTIVE USAGE - Lines 174-198
const handleContinueFlow = useCallback(async (sessionId: string) => {
  try {
    // ❌ ACTIVELY CALLED WITH SESSION_ID
    const flowStatus = await discoveryUnifiedService.getFlowStatus(sessionId);
    if (flowStatus.success) {
      navigate(`/discovery/flow?sessionId=${sessionId}`);  // ❌ PROPAGATES SESSION_ID
    }
  } catch (error) {
    console.error('Error continuing flow:', error);
  }
}, [navigate]);

// ACTIVE USAGE - Line 234
const handleDeleteFlow = async (sessionId: string) => {
  await discoveryUnifiedService.deleteFlow(sessionId);  // ❌ ACTIVE API CALL
};

// ACTIVE USAGE - Line 267  
const handleViewFlowDetails = (sessionId: string) => {
  navigate(`/discovery/details?sessionId=${sessionId}`);  // ❌ ACTIVE NAVIGATION
};
```
**Impact**: User-facing components actively create and propagate session_id in URLs

#### **9. Discovery Service Layer**
**File**: `/src/services/discoveryUnifiedService.ts`  
**Lines**: 388-401, 492-493, 567  
**Issue**: Service methods actively supporting session_id API calls  
```typescript
// ACTIVE USAGE - Lines 388-401
async getFlowStatusLegacy(sessionId: string): Promise<ApiResponse<DiscoveryFlowStatus>> {
  try {
    // ❌ ACTIVELY MAKES API CALLS WITH SESSION_ID
    const response = await fetch(`/api/v1/unified-discovery/flow/status/${sessionId}`, {
      headers: this.getHeaders()
    });
    return await response.json();
  } catch (error) {
    return this.handleError(error);
  }
}

// ACTIVE USAGE - Lines 492-493
async getFlowStatusBySessionId(sessionId: string) {
  return this.getFlowStatusLegacy(sessionId);  // ❌ ACTIVE DELEGATION
}
```
**Impact**: Service layer actively makes HTTP requests using session_id

### **Database Data Import System**

#### **10. Data Import Sessions Model**
**File**: `/backend/app/models/data_import_session.py`  
**Lines**: 23, 45, 67  
**Issue**: Entire model still actively used for session tracking  
```python
# ACTIVE USAGE - Line 23
class DataImportSession(Base):
    __tablename__ = "data_import_sessions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_name = Column(String(255), nullable=False)  # ❌ ACTIVELY POPULATED
    client_account_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    
# ACTIVE USAGE - Line 45
    @property
    def session_id(self):
        return str(self.id)  # ❌ ACTIVELY ACCESSED
```
**Impact**: Import system still creates and manages session-based workflows

#### **11. Import Session Repository**
**File**: `/backend/app/repositories/data_import_session_repository.py`  
**Lines**: Multiple throughout file  
**Issue**: Repository actively manages session-based import workflows  
```python
# ACTIVE USAGE - Examples throughout file
async def create_import_session(self, session_data: dict) -> DataImportSession:
    # ❌ ACTIVELY CREATES SESSION-BASED IMPORTS
    
async def get_session_by_id(self, session_id: str) -> Optional[DataImportSession]:
    # ❌ ACTIVELY QUERIES BY SESSION_ID
    
async def update_session_status(self, session_id: str, status: str):
    # ❌ ACTIVELY UPDATES SESSION-BASED RECORDS
```
**Impact**: Data import workflow still operates on session-based architecture

## 🟡 **MEDIUM PRIORITY (Weeks 5-6)**

### **Migration & Utility Support Code**

#### **12. Session-to-Flow Migration Utils**
**File**: `/src/utils/migration/sessionToFlow.ts`  
**Lines**: Throughout file (300+ lines)  
**Issue**: Migration utilities actively used during transition  
```typescript
// ACTIVE USAGE - Examples
export class SessionToFlowMigration {
  static convertSessionToFlowId(sessionId: string): string {
    // ❌ ACTIVELY CALLED BY FRONTEND COMPONENTS
  }
  
  static getIdentifier(flowId?: string, sessionId?: string): string {
    // ❌ ACTIVELY USED FOR DUAL IDENTIFIER SUPPORT
  }
}
```
**Impact**: Support infrastructure needed during migration but should be removed after completion

#### **13. Context Utilities**
**File**: `/src/utils/contextUtils.ts`  
**Lines**: 34, 67, 89  
**Issue**: Helper functions extracting session_id from various contexts  
```typescript
// ACTIVE USAGE - Line 34
export const extractSessionId = (context: any): string | null => {
  return context.sessionId || context.session_id || null;  // ❌ ACTIVELY EXTRACTS
};

// ACTIVE USAGE - Line 67
export const buildLegacyUrl = (sessionId: string, path: string): string => {
  return `${path}?sessionId=${sessionId}`;  // ❌ ACTIVELY BUILDS URLS
};
```
**Impact**: Utility functions actively supporting session_id workflow

### **API Middleware & Routing**

#### **14. Legacy Route Handlers**
**File**: `/backend/app/api/v1/unified_discovery.py`  
**Lines**: 45, 78, 123, 156  
**Issue**: V1 API endpoints actively handling session_id parameters  
```python
# ACTIVE USAGE - Line 45
@router.get("/flow/status/{session_id}")
async def get_flow_status(session_id: str, context: RequestContext = Depends(get_request_context)):
    # ❌ ACTIVELY CALLED BY FRONTEND
    flow = await discovery_service.get_flow_by_session_id(session_id)
    return flow_status_response(flow)

# ACTIVE USAGE - Line 78
@router.post("/flow/initialize")
async def initialize_flow(request: FlowInitRequest):
    session_id = f"disc_session_{uuid.uuid4()}"  # ❌ ACTIVELY GENERATES
    return {"session_id": session_id, "status": "initialized"}
```
**Impact**: Legacy API endpoints still actively serving frontend requests

## 📊 **Summary by Impact**

### **Critical Blockers (18 files)**
- **Backend Core**: 6 files (context, models, repositories)
- **Backend API**: 4 files (v1 endpoints, v3 inadvertent exposure)
- **Frontend Core**: 3 files (main hook, service layer, components)
- **Database Schema**: 5 files (models with session_id columns)

### **High Priority (15 files)**
- **Frontend Components**: 8 files (pages, navigation, UI)
- **Backend Services**: 4 files (import workflows, business logic)
- **API Layers**: 3 files (routing, middleware)

### **Medium Priority (14 files)**
- **Migration Utils**: 6 files (transition support code)
- **Helper Functions**: 4 files (utilities, context extraction)
- **Legacy Support**: 4 files (backwards compatibility)

## 🎯 **Remediation Strategy**

### **Week 1-2: Core System (Critical)**
1. **Remove session_id from RequestContext** (affects all downstream code)
2. **Update API endpoints** to stop returning session_id
3. **Modify repository queries** to use flow_id exclusively
4. **Update database models** to remove session_id properties

### **Week 3-4: Frontend Migration (High)**
1. **Update useUnifiedDiscoveryFlow hook** to reject session_id parameters
2. **Modify component navigation** to use flow_id in URLs
3. **Update service layer** to make flow_id-based API calls
4. **Remove session_id from component state**

### **Week 5-6: Cleanup & Validation (Medium)**
1. **Remove migration utilities** after transition complete
2. **Clean up helper functions** that support session_id
3. **Remove legacy API endpoints** that accept session_id
4. **Drop database columns** with session_id references

## ⚠️ **Risk Assessment**

### **High Risk Changes**
- **RequestContext modification**: Affects entire backend
- **Database schema changes**: Requires careful migration
- **Frontend hook updates**: Impacts all discovery flow components

### **Mitigation Strategies**
- **Feature flags**: Enable/disable session_id support during transition
- **Gradual rollout**: Update components one at a time
- **Comprehensive testing**: Validate each change doesn't break workflows
- **Rollback plan**: Ability to restore session_id support if needed

---

**Total Active Usage**: 47 files requiring modification  
**Critical Path**: 18 files blocking completion  
**Estimated Timeline**: 4-6 weeks for complete cleanup  
**Success Criteria**: Zero active session_id usage in executing code paths

*This report focuses exclusively on active, executing code that must be modified to complete the session_id → flow_id migration during Remediation Phase 1.*