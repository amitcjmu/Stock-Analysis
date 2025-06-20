## 🎯 **DUPLICATE DISCOVERY CODE TO REMOVE**

### **Backend - Legacy Discovery Endpoints**

#### **1. Test Discovery Endpoints (Complete Removal)**
- **File**: `backend/app/api/v1/endpoints/test_discovery.py`
- **Reason**: Provides authentication-free testing endpoints that bypass proper flow architecture
- **Contains**: `/test/agent/analysis`, `/test/flow/run`, `/test/flow/status` 
- **Action**: **DELETE ENTIRE FILE**

#### **2. Discovery Testing Endpoints (Complete Removal)**
- **File**: `backend/app/api/v1/discovery/testing_endpoints.py`
- **Reason**: 437 lines of testing code with field mapping, asset classification tests that don't use CrewAI flows
- **Contains**: `/test-field-mapping`, `/test-asset-classification`, `/test-json-parsing`
- **Action**: **DELETE ENTIRE FILE**

#### **3. Legacy Discovery Handlers (Selective Removal)**
- **Directory**: `backend/app/api/v1/endpoints/discovery_handlers/`
- **Files**:
  - `templates.py` - Legacy template handling
  - `feedback.py` - Non-flow feedback system
- **Action**: **DELETE DIRECTORY** (only 2 files, both legacy)

#### **4. Agent Discovery Status Handler (Review/Consolidate)**
- **File**: `backend/app/api/v1/endpoints/agents/discovery/handlers/status.py`
- **Issue**: 666 lines with cached CrewAI service and mock fallbacks
- **Contains**: Duplicate service initialization patterns
- **Action**: **CONSOLIDATE** - Remove caching logic, use proper dependency injection

#### **5. Discovery Dependencies Handler (Review)**
- **File**: `backend/app/api/v1/endpoints/agents/discovery/handlers/dependencies.py`
- **Issue**: May contain legacy dependency analysis not using CrewAI flows
- **Action**: **REVIEW** - Ensure all dependency analysis goes through CrewAI flows

### **Backend - Legacy Discovery Models/Utils**

#### **6. Discovery Utils (Review)**
- **File**: `backend/app/api/v1/discovery/utils.py`
- **Size**: 16KB, 384 lines
- **Risk**: May contain legacy processing logic that bypasses flows
- **Action**: **REVIEW** - Extract only flow-compatible utilities

#### **7. Discovery Persistence (Review)**
- **File**: `backend/app/api/v1/discovery/persistence.py`
- **Size**: 12KB, 289 lines
- **Risk**: Legacy asset persistence not integrated with flow state
- **Action**: **REVIEW** - Ensure persistence goes through flow state management

#### **8. App Server Mappings (Legacy)**
- **File**: `backend/app/api/v1/discovery/app_server_mappings.py`
- **Size**: 10KB, 263 lines
- **Risk**: Direct mapping logic not using CrewAI agents
- **Action**: **DELETE** - Replace with CrewAI flow-based mapping

### **Frontend - Legacy Discovery Components**

#### **9. Legacy Discovery Dashboard (Duplicate)**
- **File**: `src/pages/discovery/DiscoveryDashboard.tsx`
- **Issue**: 316 lines, likely superseded by `EnhancedDiscoveryDashboard.tsx`
- **Action**: **DELETE** - Use enhanced version only

#### **10. Legacy Dependency Analysis (Stub)**
- **File**: `src/pages/discovery/DependencyAnalysis.tsx`
- **Issue**: Only 12 lines, appears to be stub/placeholder
- **Action**: **DELETE** - Use proper Dependencies.tsx

#### **11. Legacy Discovery Hooks (Review)**
- **Files in**: `src/hooks/discovery/`
- **Potential Issues**:
  - `useScanQueries.ts` - May bypass flow architecture
  - `useDataCleansingQueries.ts` - Direct API calls instead of flow
  - `useTechDebtQueries.ts` - Direct queries vs flow integration
- **Action**: **REVIEW** - Ensure all hooks use flow state management

### **Configuration - Legacy API Endpoints**

#### **12. API Configuration (Clean Up)**
- **File**: `src/config/api.ts`
- **Issue**: Contains many discovery endpoints that may not use flows:
  - `CMDB_TEMPLATES`, `CMDB_FEEDBACK`, `ASSETS_BULK`, `ASSETS_CLEANUP`
  - Various agent endpoints that may bypass flow
- **Action**: **AUDIT** - Remove non-flow endpoint configurations

## 🚨 **HIGH PRIORITY REMOVALS**

### **Immediate Deletion (No Dependencies)**
1. `backend/app/api/v1/endpoints/test_discovery.py` 
2. `backend/app/api/v1/discovery/testing_endpoints.py`
3. `backend/app/api/v1/endpoints/discovery_handlers/` (entire directory)
4. `backend/app/api/v1/discovery/app_server_mappings.py`
5. `src/pages/discovery/DependencyAnalysis.tsx`

### **Review and Consolidate**
1. `backend/app/api/v1/discovery/utils.py` - Extract flow-compatible utilities only
2. `backend/app/api/v1/discovery/persistence.py` - Integrate with flow state
3. `src/pages/discovery/DiscoveryDashboard.tsx` - Verify if superseded by enhanced version
4. All hooks in `src/hooks/discovery/` - Ensure flow integration
5. `src/config/api.ts` - Remove non-flow endpoint configurations

## 🎯 **Verification Strategy**

After removals, verify:
1. All discovery operations go through `/api/v1/discovery/flow/run`
2. No direct agent calls bypass CrewAI flow service
3. Frontend uses `useDiscoveryFlowState` hook exclusively
4. No legacy endpoint configurations remain in API config

This cleanup will eliminate the mixing of old non-flow code with new CrewAI flow architecture, ensuring consistent behavior and preventing fallbacks to legacy systems.

