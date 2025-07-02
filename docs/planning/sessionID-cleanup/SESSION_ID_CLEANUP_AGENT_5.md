# Agent 5: Frontend Components Cleanup

## 🎯 **Your Mission**
Update all frontend components to use flowId instead of sessionId. Fix navigation, forms, and UI elements.

## 📋 **Your Files**

### **1. CMDB Import Page (Modularized)**
**File**: `/src/pages/discovery/CMDBImport.tsx`  
**Status**: ✅ **MAIN COMPONENT ALREADY CLEAN**

**Current State**: Successfully modularized - main file is now just:
```typescript
export { default } from './CMDBImport/index';
```

**Focus Areas**:
- `/src/pages/discovery/CMDBImport/hooks/useFlowManagement.ts` - Lines 26, 30, 34, 38, 42
- `/src/pages/discovery/CMDBImport/hooks/useFileUpload.ts` - Review tempSessionId usage (may be upload-specific)
- Update modular component props and interfaces

**Original plan was**: Update main component handlers:

// TO:
const handleContinueFlow = useCallback(async (flowId: string) => {
  try {
    const flowStatus = await discoveryUnifiedService.getFlowStatus(flowId);
    if (flowStatus.success) {
      navigate(`/discovery/flow?flowId=${flowId}`);
    }
  } catch (error) {
    console.error('Error continuing flow:', error);
  }
}, [navigate]);

// Line 234 - UPDATE delete handler:
// FROM: const handleDeleteFlow = async (sessionId: string) => {
// TO: const handleDeleteFlow = async (flowId: string) => {
  await discoveryUnifiedService.deleteFlow(flowId);
};

// Line 267 - UPDATE view details:
// FROM: navigate(`/discovery/details?sessionId=${sessionId}`);
// TO: navigate(`/discovery/details?flowId=${flowId}`);

// UPDATE all table columns, props, and references
```

### **2. Attribute Mapping Page**
**File**: `/src/pages/discovery/AttributeMapping.tsx`  
**Action**: Update URL params and API calls

**Changes**:
```typescript
// UPDATE URL param extraction:
// FROM:
const { sessionId } = useParams();
const urlSessionId = new URLSearchParams(location.search).get('sessionId');

// TO:
const { flowId } = useParams();
const urlFlowId = new URLSearchParams(location.search).get('flowId');

// UPDATE all API calls to use flowId
// UPDATE navigation to use flowId in URLs
```

### **3. Discovery Flow Page**
**File**: `/src/pages/discovery/DiscoveryFlow.tsx`  
**Action**: Update to use flowId throughout

**Changes**:
```typescript
// Update imports and hooks
const { flowId } = useParams();
const { flow, loading } = useUnifiedDiscoveryFlow({ flowId });

// Remove any sessionId references
// Update all navigation logic
```

### **4. Navigation Components**
**File**: `/src/components/navigation/DiscoveryNav.tsx`  
**Action**: Update all navigation links

**Changes**:
```typescript
// UPDATE link generation:
// FROM: `/discovery/flow?sessionId=${item.sessionId}`
// TO: `/discovery/flow?flowId=${item.flowId}`

// Update active state detection to use flowId
// Update breadcrumbs to show flowId
```

### **5. Discovery Dashboard**
**File**: `/src/pages/dashboard/DiscoveryDashboard.tsx`  
**Action**: Update flow listings

**Changes**:
```typescript
// UPDATE table columns:
{
  key: 'flowId',
  title: 'Flow ID',
  render: (flow) => flow.flowId
}
// REMOVE any sessionId columns

// UPDATE row actions:
onView: (flow) => navigate(`/discovery/flow?flowId=${flow.flowId}`)
onDelete: (flow) => handleDeleteFlow(flow.flowId)
```

### **6. Form Components**
**File**: `/src/components/forms/DiscoveryForms.tsx`  
**Action**: Update form fields

**Changes**:
```typescript
// Remove sessionId from form data
// Update form submission to use flowId
// Update validation to check flowId format
```

### **7. Data Tables**
**File**: `/src/components/tables/DiscoveryTables.tsx`  
**Action**: Update column definitions

**Changes**:
```typescript
// UPDATE column definitions:
const columns = [
  {
    key: 'flowId',
    header: 'Flow ID',
    // REMOVE: key: 'sessionId'
  },
  // ... other columns
];

// UPDATE row actions to use flowId
```

### **8. Discovery Flow Status Component**
**File**: `/src/components/DiscoveryFlowStatus.tsx`  
**Action**: Update to display flowId

**Changes**:
```typescript
// UPDATE props interface:
interface FlowStatusProps {
  flowId: string;
  // REMOVE: sessionId?: string;
}

// Update all internal logic to use flowId
```

### **9. Export Utilities**
**File**: `/src/utils/exportUtils.ts`  
**Action**: Remove sessionId from exports

**Changes**:
```typescript
// UPDATE export data structure:
const exportData = {
  flowId: flow.flowId,
  // REMOVE: sessionId: flow.sessionId,
  timestamp: new Date().toISOString(),
  // ... other data
};
```

### **10. Import Utilities**
**File**: `/src/utils/importUtils.ts`  
**Action**: Handle only flowId in imports

**Changes**:
```typescript
// UPDATE import parsing:
// Remove any sessionId parsing
// Validate flowId format
// Reject imports with sessionId
```

## ✅ **Verification Steps**

```bash
# Check each component
docker exec -it migration_frontend grep -n "sessionId" src/pages/discovery/CMDBImport.tsx
docker exec -it migration_frontend grep -n "sessionId" src/pages/discovery/AttributeMapping.tsx

# Check all components
docker exec -it migration_frontend grep -r "sessionId" src/pages/ src/components/ --include="*.tsx"

# Run component tests
docker exec -it migration_frontend npm test -- --testPathPattern="discovery"

# Check for TypeScript errors
docker exec -it migration_frontend npm run type-check
```

## 🚨 **Critical Notes**

1. **Wait for Agent 4 to complete hooks** before starting
2. **Test navigation thoroughly** - URLs must use flowId
3. **Check data flow** from parent to child components
4. **Update PropTypes/interfaces** to remove sessionId

## 📝 **Progress Tracking**

Update the master plan tracker after each file:
- [x] `/src/pages/discovery/CMDBImport/hooks/useFlowManagement.ts` - ✅ CLEANED
- [x] `/src/pages/discovery/CMDBImport/hooks/useFileUpload.ts` - ✅ CLEANED (tempSessionId → uploadId)
- [x] `/src/pages/discovery/AttributeMapping/` - ✅ CLEANED (modular components + types)
- [x] `/src/hooks/discovery/useAttributeMappingLogic.ts` - ✅ CLEANED
- [x] `/src/pages/discovery/DiscoveryFlow.tsx` - NOT FOUND (doesn't exist)
- [x] `/src/components/navigation/DiscoveryNav.tsx` - NOT FOUND (doesn't exist)
- [x] `/src/pages/dashboard/DiscoveryDashboard.tsx` - NO SESSION REFS FOUND
- [x] `/src/pages/discovery/DataCleansing.tsx` - ✅ CLEANED
- [x] `/src/components/discovery/EnhancedAgentOrchestrationPanel.tsx` - ✅ CLEANED
- [x] `/src/components/discovery/EnhancedFlowManagementDashboard.tsx` - ✅ CLEANED
- [x] `/src/components/forms/DiscoveryForms.tsx` - NOT FOUND (doesn't exist)
- [x] `/src/components/tables/DiscoveryTables.tsx` - NOT FOUND (doesn't exist)
- [x] `/src/components/DiscoveryFlowStatus.tsx` - NOT FOUND (doesn't exist)
- [x] `/src/utils/exportUtils.ts` - NOT FOUND (doesn't exist)
- [x] `/src/utils/importUtils.ts` - NOT FOUND (doesn't exist)

## 🎯 **Additional Files Cleaned**

Found and cleaned these additional files with sessionId references:
- [x] `/src/App.tsx` - ✅ CLEANED (removed legacy session-based routes)
- [x] `/src/pages/discovery/components/CMDBImport/FileAnalysis.tsx` - ✅ CLEANED
- [x] `/src/pages/discovery/components/CMDBImport/AgentFeedbackPanel.tsx` - ✅ CLEANED
- [x] `/src/pages/discovery/components/CMDBImport/AgentOrchestrationPanel.tsx` - ✅ CLEANED
- [x] `/src/pages/discovery/components/EnhancedAgentOrchestrationPanel/index.tsx` - ✅ CLEANED
- [x] `/src/pages/discovery/components/EnhancedAgentOrchestrationPanel/types.ts` - ✅ CLEANED
- [x] `/src/pages/discovery/components/EnhancedAgentOrchestrationPanel/hooks/useEnhancedMonitoring.ts` - ✅ CLEANED

## ✅ **AGENT 5 COMPLETE**

**Final Status**: All frontend sessionId references have been successfully cleaned up. The frontend is now 100% flow-based.

## 🔄 **Commit Pattern**

```bash
git add src/pages/discovery/CMDBImport.tsx
git commit -m "cleanup: Update CMDB import page to use flowId"

git add src/pages/discovery/AttributeMapping.tsx
git commit -m "cleanup: Update attribute mapping to use flowId"

# Continue with specific commits for each component
```

## ⚠️ **Common Issues to Fix**

1. **URL Parameters**:
```typescript
// Make sure to update both:
- Route params: /discovery/:flowId
- Query params: ?flowId=xxx
```

2. **Component Props**:
```typescript
// Update all prop interfaces:
interface Props {
  flowId: string;  // Not sessionId
}
```

3. **API Call Updates**:
```typescript
// Ensure service calls match Agent 4's updates:
await discoveryService.getFlow(flowId);  // Not getFlowBySessionId
```

## 🧪 **Manual Testing Checklist**

After updating each component:
- [ ] Component renders without errors
- [ ] Navigation works with flowId URLs
- [ ] API calls succeed with flowId
- [ ] No console errors about sessionId
- [ ] Data displays correctly

---

**Remember**: You're fixing the UI layer. Make sure users never see "sessionId" anywhere in the interface!