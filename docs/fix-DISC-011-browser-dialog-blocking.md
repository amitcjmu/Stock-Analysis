# Fix for DISC-011: Browser Native Confirm Dialog Blocking UI Access

## Problem Summary
The `flowDeletionService.ts` was using `window.confirm()` on line 170, which creates a native browser dialog that:
- Blocks all UI access when triggered
- Cannot be interacted with by Playwright or other automation tools  
- Was triggering on page load with undefined flow data
- Prevented all UI testing

## Solution Implemented

### 1. Created React Hook for Modal-Based Deletion
**File:** `src/hooks/useFlowDeletion.tsx`
- Manages modal state for flow deletion confirmations
- Integrates with existing `flowDeletionService` but uses `skipBrowserConfirm: true`
- Provides actions for requesting, confirming, and canceling deletions
- Handles async deletion flow with proper error handling

### 2. Created React Modal Component
**File:** `src/components/flows/FlowDeletionModal.tsx`
- Uses shadcn/ui AlertDialog components (not native browser dialogs)
- Displays flow information and deletion impact
- Provides clear confirm/cancel actions
- Fully testable with Playwright

### 3. Updated flowDeletionService.ts
- Added warning comments about the native dialog issue
- Kept backward compatibility with `skipBrowserConfirm` parameter
- Service now logs warnings when native dialog is used

### 4. Example Integration: MasterFlowDashboard
**File:** `src/components/flows/MasterFlowDashboard.tsx`
- Replaced `confirm()` dialog with React modal approach
- Uses `useFlowDeletion` hook and `FlowDeletionModal` component
- Properly integrates with auth context for client/user information

## How to Use the Fix

### For New Components
```tsx
import { useFlowDeletion } from '@/hooks/useFlowDeletion';
import { FlowDeletionModal } from '@/components/flows/FlowDeletionModal';
import { useAuth } from '@/contexts/AuthContext';

export const YourComponent = () => {
  const { client, engagement, user } = useAuth();
  
  const [deletionState, deletionActions] = useFlowDeletion(
    (result) => {
      // Handle successful deletion
      console.log('Deleted:', result);
    },
    (error) => {
      // Handle deletion error
      console.error('Error:', error);
    }
  );

  const handleDelete = async (flowId: string) => {
    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'manual',
      user?.id
    );
  };

  return (
    <>
      {/* Your UI */}
      <button onClick={() => handleDelete('flow-123')}>Delete Flow</button>
      
      {/* Add the modal at the end */}
      <FlowDeletionModal
        open={deletionState.isModalOpen}
        candidates={deletionState.candidates}
        deletionSource={deletionState.deletionSource}
        isDeleting={deletionState.isDeleting}
        onConfirm={deletionActions.confirmDeletion}
        onCancel={deletionActions.cancelDeletion}
      />
    </>
  );
};
```

### For Existing Components Using Native Dialogs
1. Import the new hook and modal component
2. Replace `confirm()` calls with `deletionActions.requestDeletion()`
3. Add the `FlowDeletionModal` component to your JSX
4. Remove any native dialog logic

## Components Already Using Custom Confirmation
These components already use custom confirmation dialogs and pass `useCustomConfirmation: true`:
- `CMDBImport` (via `useFlowManagement` hook)
- `IncompleteFlowManager` (has its own confirmation dialog)
- `EnhancedDiscoveryDashboard`

## Testing the Fix
The new modal-based approach:
- ✅ Can be interacted with by Playwright
- ✅ Doesn't block UI access
- ✅ Handles undefined data gracefully
- ✅ Provides better UX with detailed flow information

## Migration Checklist
- [x] Create React hook for modal state management
- [x] Create React modal component
- [x] Update flowDeletionService with warnings
- [x] Update MasterFlowDashboard as example
- [ ] Update other components using native dialogs
- [ ] Add Playwright tests for deletion flows
- [ ] Remove all `window.confirm()` usage from codebase

## Future Improvements
1. Create a global modal provider to handle all confirmations
2. Add animation/transition effects to the modal
3. Add bulk deletion support in the modal UI
4. Add undo functionality for accidental deletions