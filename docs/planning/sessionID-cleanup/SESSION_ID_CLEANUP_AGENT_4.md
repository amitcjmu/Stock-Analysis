# Agent 4: Frontend Infrastructure Cleanup

## 🎯 **Your Mission**
Remove all sessionId references from frontend infrastructure - hooks, services, utilities, and types. This is critical for frontend functionality.

## 📋 **Your Files**

### **1. CRITICAL - Main Discovery Hook**
**File**: `/src/hooks/useUnifiedDiscoveryFlow.ts`  
**Lines to modify**: 10, 139, 144-150, 153-159, and all sessionId references

**Specific Changes**:
```typescript
// Line ~10 - UPDATE interface:
interface DiscoveryFlowOptions {
  flowId?: string;
  // REMOVE: sessionId?: string;
  enableRealTimeUpdates?: boolean;
}

// Lines 144-150 - REMOVE conversion logic:
// DELETE THIS ENTIRE BLOCK:
const getFlowId = useCallback(() => {
  if (options.sessionId) {
    return SessionToFlowMigration.convertSessionToFlowId(options.sessionId);
  }
  return options.flowId;
}, [options.sessionId, options.flowId]);

// REPLACE WITH:
const flowId = options.flowId;

// Lines 153-159 - REMOVE URL param extraction:
// DELETE THIS ENTIRE useEffect:
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get('sessionId');
  if (sessionId) {
    setCurrentSessionId(sessionId);
  }
}, []);

// UPDATE all references throughout the file
// FROM: sessionId
// TO: flowId
```

### **2. Discovery Service**
**File**: `/src/services/discoveryUnifiedService.ts`  
**Lines to modify**: 388-401, 492-493, 567, and all sessionId methods

**Specific Changes**:
```typescript
// Lines 388-401 - REMOVE this method entirely:
async getFlowStatusLegacy(sessionId: string): Promise<ApiResponse<DiscoveryFlowStatus>> {
  // DELETE ENTIRE METHOD
}

// Lines 492-493 - REMOVE this method:
async getFlowStatusBySessionId(sessionId: string) {
  // DELETE ENTIRE METHOD
}

// UPDATE all API calls:
// FROM: `/api/v1/unified-discovery/flow/status/${sessionId}`
// TO: `/api/v3/discovery-flow/flows/${flowId}/status`

// Remove any methods with sessionId parameters
// Update method signatures to use flowId
```

### **3. PRESERVE Migration Utilities (Updated)**
**File**: `/src/utils/migration/sessionToFlow.ts`  
**Action**: **DO NOT DELETE** - This contains working migration infrastructure

**Why Preserve**:
- Contains proper deprecation warning system
- Provides conversion utilities during transition  
- Frontend components depend on this during cleanup phase
- Will be removed AFTER all components are updated

```typescript
// KEEP these methods during transition:
// - SessionToFlowMigration.convertSessionToFlowId()
// - SessionToFlowMigration.logDeprecationWarning()
// - SessionToFlowMigration.getIdentifier()
```

### **4. Context Utilities**
**File**: `/src/utils/contextUtils.ts`  
**Lines to modify**: 34, 67, 89

**Specific Changes**:
```typescript
// Line 34 - REMOVE this function:
export const extractSessionId = (context: any): string | null => {
  // DELETE ENTIRE FUNCTION
};

// Line 67 - REMOVE this function:
export const buildLegacyUrl = (sessionId: string, path: string): string => {
  // DELETE ENTIRE FUNCTION
};

// Remove any other session extraction logic
```

### **5. API Client**
**File**: `/src/services/apiClient.ts`  
**Action**: Remove session_id header injection

**Changes**:
```typescript
// REMOVE any code like:
if (sessionId) {
  headers['X-Session-ID'] = sessionId;
}

// ENSURE flow_id is included:
if (flowId) {
  headers['X-Flow-ID'] = flowId;
}
```

### **6. Type Definitions**
**File**: `/src/types/discovery.ts`  
**Action**: Remove sessionId from all interfaces

**Changes**:
```typescript
// UPDATE all interfaces:
export interface DiscoveryFlow {
  flowId: string;
  // REMOVE: sessionId?: string;
  // ... other fields
}

export interface DiscoveryFlowOptions {
  flowId: string;
  // REMOVE: sessionId?: string;
}

// Remove sessionId from ALL type definitions
```

### **7. State Management**
**File**: `/src/store/discoverySlice.ts` (or similar Redux/Zustand file)  
**Action**: Remove sessionId from state

**Changes**:
```typescript
// UPDATE initial state:
const initialState = {
  currentFlowId: null,
  // REMOVE: currentSessionId: null,
  flows: [],
  // ...
};

// UPDATE all actions to remove sessionId
// UPDATE all selectors to use flowId
```

### **8. WebSocket Client**
**File**: `/src/services/websocketClient.ts`  
**Action**: Update subscriptions

**Changes**:
```typescript
// UPDATE subscription patterns:
// FROM: subscribe(`session:${sessionId}`)
// TO: subscribe(`flow:${flowId}`)

// Update all event handlers to use flowId
```

## ✅ **Verification Steps**

```bash
# Check each file
docker exec -it migration_frontend grep -n "sessionId" src/hooks/useUnifiedDiscoveryFlow.ts
docker exec -it migration_frontend grep -n "SessionToFlow" src/

# After deleting migration utils
docker exec -it migration_frontend ls src/utils/migration/
# Should return: No such file or directory

# Check all infrastructure files
docker exec -it migration_frontend grep -r "sessionId" src/hooks/ src/services/ src/utils/ src/types/ --include="*.ts"

# Run type checking
docker exec -it migration_frontend npm run type-check
```

## 🚨 **Critical Notes**

1. **Complete the hook first** - All components depend on it
2. **Delete sessionToFlow.ts completely** - Don't just comment it out
3. **Update imports** - Remove any imports of deleted files
4. **Check for broken imports** after deleting files

## 📝 **Progress Tracking**

Update the master plan tracker after each file:
- [x] `/src/hooks/useUnifiedDiscoveryFlow.ts` - CRITICAL - ✅ COMPLETED
- [x] `/src/services/discoveryUnifiedService.ts` - ✅ COMPLETED
- [x] `/src/utils/migration/sessionToFlow.ts` - **PRESERVED** (working infrastructure)
- [x] `/src/utils/contextUtils.ts` - Remove session extraction - ✅ COMPLETED
- [x] `/src/services/apiClient.ts` - (Not found, checked other files)
- [x] `/src/types/discovery.ts` - ✅ COMPLETED
- [x] `/src/store/discoverySlice.ts` - (Not found)
- [x] `/src/services/websocketClient.ts` - (Not found)

**Additional files cleaned:**
- [x] `/src/contexts/AuthContext/hooks/useAuthHeaders.ts` - ✅ COMPLETED
- [x] `/src/config/api.ts` - ✅ COMPLETED  
- [x] `/src/api/v3/utils/requestConfig.ts` - ✅ COMPLETED
- [x] `/src/pages/discovery/hooks/useCMDBImport.ts` - ✅ COMPLETED

## 🔄 **Commit Pattern**

```bash
git add src/hooks/useUnifiedDiscoveryFlow.ts
git commit -m "cleanup: Remove sessionId from main discovery hook"

git rm src/utils/migration/sessionToFlow.ts
git commit -m "cleanup: Delete session to flow migration utilities"

git add src/services/discoveryUnifiedService.ts
git commit -m "cleanup: Remove sessionId methods from discovery service"
```

## ⚠️ **If You Get Stuck**

- Check TypeScript errors after changes
- Look for components importing deleted files
- Coordinate with Agent 5 on component dependencies
- Run the app locally to test basic functionality

## 🔍 **Common Import Fixes**

After deleting files, you'll need to fix imports:
```typescript
// REMOVE these imports:
import { SessionToFlowMigration } from '@/utils/migration/sessionToFlow';
import { extractSessionId, buildLegacyUrl } from '@/utils/contextUtils';

// If you see errors like "Module not found", search for and remove the import
```

---

**Remember**: This is infrastructure cleanup. Be thorough - every component depends on these files working correctly!