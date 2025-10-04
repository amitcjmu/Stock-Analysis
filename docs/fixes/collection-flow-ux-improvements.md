# Collection Flow UX Improvements

## Issues Addressed

### Issue 1: No Loading State During Flow Creation
**Problem**: When creating a new collection flow, users saw confusing messages like "Asset Selection Required" or blocking flow warnings instead of a proper loading indicator while the backend processed.

**Root Cause**: The `QuestionnaireGenerationModal` was only triggered manually via callback, but when bootstrap questionnaires loaded immediately, the modal never showed. Users didn't know the system was generating AI questionnaires.

**Fix**: Added automatic modal display based on `completionStatus`:
- Shows modal when `completionStatus === "pending"` (waiting for AI questionnaire)
- Hides modal when `completionStatus === "ready"` or `"fallback"`
- Location: `/src/pages/collection/AdaptiveForms.tsx` lines 100-107

```typescript
// Auto-show generation modal when completionStatus is "pending"
React.useEffect(() => {
  if (completionStatus === "pending" && activeFlowId) {
    setShowGenerationModal(true);
  } else if (completionStatus === "ready" || completionStatus === "fallback") {
    setShowGenerationModal(false);
  }
}, [completionStatus, activeFlowId]);
```

### Issue 2: Form Stuck After Answering Questions
**Problem**: After answering questionnaire questions and clicking "Submit Form", the page remains on the same questionnaire without progressing to the next section or completion.

**Current Logic** (appears correct):
1. Submit questionnaire responses to backend
2. Wait 2 seconds for backend processing
3. Fetch updated questionnaires
4. If new questionnaires found, load next one
5. If no questionnaires, mark as complete and redirect to progress page

**Possible Root Causes**:
1. Backend not generating follow-up questionnaires after submission
2. API error when fetching questionnaires (should show warning toast)
3. Backend returning the same questionnaire again
4. Questionnaire status not being updated properly

**Debug Steps**:
- Check browser console after form submission for:
  - "📋 Retrieved X questionnaires after submission" log
  - Any error messages from questionnaire fetch
  - Flow completion status

**Files Involved**:
- `/src/hooks/collection/useAdaptiveFormFlow.ts` lines 1354-1499 (handleSubmit)
- Backend: Questionnaire generation and response handling endpoints

## Testing Checklist

- [ ] Create new collection flow and verify loading modal shows
- [ ] Verify modal shows "Generating AI questionnaire..." message
- [ ] Confirm modal hides when questionnaire is ready
- [ ] Submit questionnaire and verify next section loads OR completion redirect
- [ ] Check console logs during submission for errors
- [ ] Test with both bootstrap and AI-generated questionnaires
