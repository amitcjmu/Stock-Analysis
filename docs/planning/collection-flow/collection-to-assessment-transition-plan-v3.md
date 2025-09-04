# Collection to Assessment Transition - Fix Plan v3

## Current State Analysis (September 2025)

### What's Actually Broken
1. **Infinite Loop Between Pages**
   - Progress page → Continue button → Adaptive Forms page
   - Adaptive Forms page → Shows "blocked" message → Back to Progress
   - No actual progress is made

2. **Adaptive Forms Page Logic Flaw**
   - Treats ANY existing flow as "blocking new collection"
   - Should INSTEAD: Check if we're continuing an existing flow (via flowId param)
   - If flowId is provided, should fetch and display questionnaires for THAT flow

3. **Continue Button Misconception**
   - Currently just navigates between pages
   - Should ACTUALLY: Trigger flow continuation/execution

4. **Missing Questionnaire Display**
   - Even with flowId param, adaptive-forms doesn't fetch questionnaires
   - The `getFlowQuestionnaires` API exists but isn't being called properly

## Root Cause Analysis

### The Real Problem
There are THREE separate issues working together to create the infinite loop:

1. **Multiple Incomplete Flows Confusion**
   - When there are 2+ incomplete flows, clicking Continue on Flow A (with flowId=A)
   - Navigates to adaptive-forms?flowId=A
   - But Flow B still exists and triggers the blocking message
   - The page shows "1 incomplete collection flow" even though we're continuing Flow A

2. **Blocking Logic is Too Broad**
   - The blocking check happens BEFORE the form initialization
   - It should only block NEW flow creation, not continuation
   - Current code: blocks if ANY other flow exists
   - Should be: allow if flowId matches one of the existing flows

3. **Flow Continuation Not Triggered**
   - The Continue button just navigates, doesn't trigger backend flow execution
   - No questionnaires are fetched because the flow isn't actually continued

### What We Have vs What We Need

#### What We Have:
```typescript
// Current Continue button - just navigates
navigate(`/collection/adaptive-forms?flowId=${flow.id}`);

// Current adaptive-forms - blocks everything
if (blockingFlows.length > 0) {
  return <BlockedMessage />;
}
```

#### What We Need:
```typescript
// Continue button should trigger flow continuation
await collectionFlowApi.continueFlow(flow.id);
const questionnaires = await collectionFlowApi.getFlowQuestionnaires(flow.id);
if (questionnaires.length > 0) {
  navigate(`/collection/adaptive-forms?flowId=${flow.id}`);
}

// Adaptive-forms should handle continuation
if (flowId && activeFlowId === flowId) {
  // Fetch and display questionnaires for THIS flow
  const questionnaires = await collectionFlowApi.getFlowQuestionnaires(flowId);
  return <QuestionnaireForm questionnaires={questionnaires} />;
}
```

## Implementation Plan

### Phase 1: Fix Adaptive Forms Page Logic
**File:** `src/pages/collection/AdaptiveForms.tsx`

#### 1.1 Fix the Blocking Logic
- **Problem:** Page blocks when OTHER flows exist, even when continuing current flow
- **Current Code Issue:** 
  - Line 85-87 filters out current flowId from blockingFlows
  - BUT if there are OTHER incomplete flows, hasBlockingFlows is still true
  - This causes the blocking message to show even when continuing a valid flow
- **Solution:** Check if we're continuing ANY existing flow, not just if other flows exist
- **Implementation:**
  ```typescript
  // Current logic (WRONG):
  const blockingFlows = incompleteFlows.filter((flow) => {
    const id = flow.flow_id || flow.id;
    return id !== flowId && !deletingFlows.has(id);  // Filters out current flow
  });
  const hasBlockingFlows = blockingFlows.length > 0;  // But still true if OTHER flows exist!
  
  // Fixed logic (RIGHT):
  const flowIdFromUrl = searchParams.get('flowId');
  const allIncompleteFlows = incompleteFlows.filter(f => !deletingFlows.has(f.id));
  const isContinuingExistingFlow = flowIdFromUrl && 
    allIncompleteFlows.some(f => f.flow_id === flowIdFromUrl || f.id === flowIdFromUrl);
  const hasBlockingFlows = !isContinuingExistingFlow && allIncompleteFlows.length > 0;
  
  // Now hasBlockingFlows is only true if we're NOT continuing an existing flow
  ```

#### 1.2 Fetch Questionnaires for Active Flow
- **Problem:** Questionnaires aren't fetched even with flowId
- **Solution:** Use existing `useAdaptiveFormFlow` hook properly
- **Implementation:**
  - Hook already has questionnaire fetching logic
  - Need to trigger it when flowId is present
  - Display questionnaires when available

### Phase 2: Fix Progress Page Continue Button
**File:** `src/components/collection/progress/FlowDetailsCard.tsx`

#### 2.1 Make Continue Actually Continue the Flow
- **Problem:** Continue button just navigates without triggering flow execution
- **Solution:** Call flow continuation API before navigation
- **Implementation:**
  ```typescript
  const handleContinue = async () => {
    // For stuck/incomplete flows
    if (flow.progress < 100) {
      // Trigger flow continuation
      const continueResult = await collectionFlowApi.continueFlow(flow.id);
      
      // Check what needs user input
      if (continueResult.requires_user_input) {
        // Navigate to adaptive forms for questionnaires
        navigate(`/collection/adaptive-forms?flowId=${flow.id}`);
      } else {
        // Stay on progress page if flow is running automatically
        toast({ title: 'Flow resumed' });
      }
    }
  };
  ```

### Phase 3: Connect Backend Flow Execution
**File:** `src/services/api/collection-flow.ts`

#### 3.1 Ensure continueFlow API Works
- Already exists but may not be triggering backend properly
- Verify it calls `/api/v1/collection/flows/{flowId}/continue`

#### 3.2 Ensure getFlowQuestionnaires Returns Data
- Currently returns empty on "no_applications_selected" error
- Should handle this gracefully and show application selection UI

### Phase 4: Fix Flow State Management
**File:** `src/hooks/collection/useAdaptiveFormFlow.ts`

#### 4.1 Fix Questionnaire Loading
- **Problem:** Hook doesn't load questionnaires on mount with flowId
- **Solution:** Add effect to load when flowId changes
- **Implementation:**
  ```typescript
  useEffect(() => {
    if (flowId && !isLoading) {
      fetchQuestionnaires(flowId);
    }
  }, [flowId]);
  ```

#### 4.2 Handle "No Applications Selected" Properly
- **Problem:** Error throws and breaks the flow
- **Solution:** Show application selection UI instead
- **Implementation:**
  - Detect the specific error
  - Set state to show application picker
  - Allow user to select applications and retry

## Testing Strategy

### Test Case 1: Continue Stuck Flow
1. Navigate to Progress page with stuck flow (0% progress)
2. Click Continue
3. **Expected:** Flow continues, navigates to adaptive-forms with questionnaires

### Test Case 2: Resume Paused Flow with Questionnaires
1. Have a flow at 30% with pending questionnaires
2. Click Continue on Progress page
3. **Expected:** Navigate to adaptive-forms, see questionnaire form

### Test Case 3: Complete Flow Transition
1. Have a flow at 100% completion
2. Click Continue
3. **Expected:** Check readiness, transition to assessment if ready

### Test Case 4: No Applications Selected
1. Continue a flow with no applications selected
2. **Expected:** Show application selection UI, not an error

## Success Criteria

1. ✅ No more infinite loops between pages
2. ✅ Continue button actually continues/resumes the flow
3. ✅ Adaptive forms page shows questionnaires for the active flow
4. ✅ Can complete questionnaires and progress the flow
5. ✅ Completed flows can transition to assessment
6. ✅ Application selection works when needed

## What We're NOT Doing

1. **NOT** adding more transition infrastructure (we have enough)
2. **NOT** creating new database tables or migrations
3. **NOT** building new API endpoints (existing ones work)
4. **NOT** adding complex state management (use what exists)

## Key Insight

The infrastructure exists. The APIs exist. The problem is they're not connected properly. We need to:
1. Fix the logic that determines when to block vs continue
2. Actually call the flow continuation APIs
3. Display the questionnaires that are returned
4. Handle edge cases like "no applications selected"

This is about fixing the wiring, not building new components.