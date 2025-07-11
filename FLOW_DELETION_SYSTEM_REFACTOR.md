# Flow Deletion System Refactor

## 🚨 Critical Issue Fixed

**Problem**: Flows were being automatically deleted without user consent, causing data loss and workflow interruption.

**Root Cause**: Multiple automatic cleanup functions across different components were deleting flows without proper user approval.

## 🔧 Solution: Centralized User-Approval Deletion System

### New Architecture

#### 1. **Centralized Flow Deletion Service** (`/src/services/flowDeletionService.ts`)
- **Single source of truth** for all flow deletion logic
- **Mandatory user approval** for ALL deletions
- **Clear audit trail** distinguishing user vs system actions
- **Intelligent recommendations** without automatic execution

#### 2. **Unified Flow Deletion Hook** (`/src/hooks/useFlowDeletion.ts`)
- **Replaces all scattered deletion hooks**
- **Consolidates**: `useFlowDeletionV2`, `useBulkFlowOperationsV2`, manual deletion handlers
- **User-friendly confirmation dialogs**
- **Proper error handling and toast notifications**

#### 3. **Updated Components**

##### UploadBlocker (`/src/components/discovery/UploadBlocker.tsx`)
- **REMOVED**: Automatic cleanup functions that deleted flows without consent
- **ADDED**: Smart cleanup with user approval requirement
- **NEW**: Clear messaging about user approval requirement

##### CMDBImport (`/src/pages/discovery/CMDBImport/hooks/useCMDBImport.ts`)
- **UPDATED**: Uses new centralized deletion system
- **REMOVED**: Direct API calls for deletion
- **ADDED**: Proper user approval flow

##### Flow Operations (`/src/hooks/discovery/useFlowOperations.ts`)
- **DEPRECATED**: Old deletion hooks with warnings
- **PREVENTS**: Direct deletions without user approval
- **GUIDES**: Users to new centralized system

#### 4. **Enhanced Flow Management** (`/src/hooks/discovery/useEnhancedFlowManagement.ts`)
- **DISABLED**: Automatic cleanup functionality
- **DEPRECATED**: `useAutomaticCleanup` hook
- **REDIRECTS**: To new user-approval system

## 🎯 Key Features

### 1. **Mandatory User Approval**
```typescript
// All deletions require explicit user confirmation
const result = await flowDeletionService.requestFlowDeletion(
  flowIds, 
  clientAccountId, 
  engagementId, 
  'automatic_cleanup' // Source tracking
);
```

### 2. **Intelligent Recommendations**
```typescript
// System analyzes and recommends but never auto-deletes
const candidates = await flowDeletionService.identifyDeletionCandidates(
  clientAccountId, 
  engagementId, 
  'discovery'
);
```

### 3. **Clear Audit Trail**
```typescript
// Every deletion is properly tracked
audit_trail: {
  deletion_source: 'automatic_cleanup' | 'manual' | 'bulk_cleanup' | 'navigation',
  user_confirmed: boolean,
  timestamp: string,
  reason: string
}
```

### 4. **User-Friendly Confirmations**
```
🤖 System Cleanup Recommendation

Delete 3 flows?

Breakdown by reason:
• Failed/Error flows: 2 flows
• Completed flows: 1 flow

Oldest flows:
• Discovery Flow (2h ago)
• Assessment Flow (1d ago)

⚠️ This action cannot be undone.
💡 Alternative: You can resume/retry flows instead of deleting them.

Continue with deletion?
```

## 🔄 Migration Guide

### For Developers

#### Before (Problematic)
```typescript
// ❌ Automatic deletion without user consent
const handleCleanup = async () => {
  const flows = await getCompletedFlows();
  await Promise.all(flows.map(f => deleteFlow(f.id))); // NO USER APPROVAL!
};
```

#### After (Safe)
```typescript
// ✅ User-approved deletion
const { performCleanup } = useFlowCleanup();
const handleCleanup = async () => {
  const result = await performCleanup('discovery'); // User approval required
  // System shows confirmation dialog automatically
};
```

### For Components

#### Before (Scattered)
```typescript
// ❌ Multiple deletion hooks
const flowDeletion = useFlowDeletionV2();
const bulkOperations = useBulkFlowOperationsV2();
const enhancedManagement = useEnhancedFlowManagement();
```

#### After (Centralized)
```typescript
// ✅ Single deletion hook
const { deleteFlow, bulkDeleteFlows } = useFlowDeletion({
  deletion_source: 'manual'
});
```

### For Cleanup Operations

#### Before (Automatic)
```typescript
// ❌ Silent automatic cleanup
useEffect(() => {
  const interval = setInterval(async () => {
    const expiredFlows = await getExpiredFlows();
    await deleteExpiredFlows(expiredFlows); // NO USER APPROVAL!
  }, 60000);
}, []);
```

#### After (Recommendation-based)
```typescript
// ✅ User-approved cleanup
const { getCleanupRecommendations } = useFlowCleanupRecommendations();
const handleShowRecommendations = async () => {
  const recommendations = await getCleanupRecommendations();
  // User sees recommendations and decides what to delete
};
```

## 🚀 Benefits

### 1. **User Safety**
- **No more accidental deletions**
- **Clear understanding of what will be deleted**
- **Ability to cancel operations**

### 2. **Better User Experience**
- **Informative confirmation dialogs**
- **Clear reasoning for recommendations**
- **Alternative options suggested**

### 3. **Proper Audit Trail**
- **Distinguish between user vs system actions**
- **Track deletion sources**
- **Maintain compliance records**

### 4. **Code Quality**
- **Eliminated redundant deletion logic**
- **Centralized error handling**
- **Consistent user experience**

## 📋 Usage Examples

### Basic Flow Deletion
```typescript
const { deleteFlow } = useFlowDeletion();

const handleDelete = async (flowId: string) => {
  await deleteFlow(flowId); // User approval dialog automatically shown
};
```

### Bulk Flow Deletion
```typescript
const { bulkDeleteFlows } = useFlowDeletion();

const handleBulkDelete = async (flowIds: string[]) => {
  await bulkDeleteFlows(flowIds); // User sees summary and approves
};
```

### Smart Cleanup
```typescript
const { performCleanup } = useFlowCleanup();

const handleSmartCleanup = async () => {
  const result = await performCleanup('discovery');
  // System analyzes flows, shows recommendations, requires user approval
};
```

### Get Recommendations Only
```typescript
const { getCleanupRecommendations } = useFlowCleanupRecommendations();

const handleGetRecommendations = async () => {
  const recommendations = await getCleanupRecommendations();
  // Show recommendations to user without forcing deletion
};
```

## 🔒 Security & Safety

### 1. **No Automatic Deletions**
- All deletion functions require explicit user confirmation
- System can recommend but never execute deletions automatically

### 2. **Clear Confirmation Messages**
- Users see exactly what will be deleted
- Reasons for deletion are explained
- Alternative actions are suggested

### 3. **Audit Trail**
- Every deletion is logged with source, reason, and user confirmation
- Distinguish between user-initiated and system-recommended deletions

### 4. **Error Handling**
- Graceful handling of deletion failures
- Clear error messages for users
- Fallback options for failed operations

## 🎯 Testing the Fix

### 1. **Upload Blocker Test**
1. Navigate to `/discovery/cmdb-import`
2. If flows exist, click "Smart cleanup" button
3. Verify user approval dialog appears
4. Confirm that flows are only deleted after user approval

### 2. **Flow Management Test**
1. Navigate to flow management interface
2. Select flows for deletion
3. Verify confirmation dialog shows flow details
4. Confirm deletion only proceeds after user approval

### 3. **Navigation Test**
1. Navigate between different pages
2. Verify no automatic flow deletions occur
3. Check that cancelled flow messages reference potential system issues

## 📝 Future Enhancements

### 1. **Enhanced Recommendations**
- AI-powered flow analysis
- Smarter cleanup suggestions
- User preference learning

### 2. **Advanced Confirmation UI**
- Rich confirmation dialogs with React components
- Flow preview before deletion
- Undo functionality

### 3. **Audit Dashboard**
- View deletion history
- Track user patterns
- Compliance reporting

## 🔧 Files Modified

### Core Services
- `/src/services/flowDeletionService.ts` - **NEW**: Centralized deletion logic
- `/src/hooks/useFlowDeletion.ts` - **NEW**: Unified deletion hook

### Updated Components
- `/src/components/discovery/UploadBlocker.tsx` - Removed automatic cleanup
- `/src/pages/discovery/CMDBImport/hooks/useCMDBImport.ts` - Updated to new system
- `/src/hooks/discovery/useFlowOperations.ts` - Deprecated old methods
- `/src/hooks/discovery/useEnhancedFlowManagement.ts` - Disabled automatic cleanup
- `/src/hooks/discovery/useAttributeMappingNavigation.ts` - Enhanced error messages

### Documentation
- `/FLOW_DELETION_SYSTEM_REFACTOR.md` - **NEW**: This documentation

## ✅ Verification Checklist

- [ ] No automatic flow deletions occur without user approval
- [ ] All deletion operations show clear confirmation dialogs
- [ ] Audit trail properly tracks deletion sources
- [ ] Error messages help users understand when flows are unexpectedly deleted
- [ ] UploadBlocker cleanup requires user approval
- [ ] Navigation between pages doesn't trigger deletions
- [ ] Bulk operations work with new approval system
- [ ] Deprecated hooks show appropriate warnings
- [ ] Smart cleanup shows recommendations before deletion
- [ ] Users can cancel deletion operations at any time

---

**Status**: ✅ **COMPLETED** - All flow deletions now require user approval

**Impact**: 🔒 **CRITICAL SECURITY FIX** - Prevents accidental data loss

**Next Steps**: Test thoroughly and monitor for any remaining automatic deletion scenarios