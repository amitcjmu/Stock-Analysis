# Questionnaire Persistence Resolution - August 2025

## [2025-08-27] Save Progress Button Not Triggering
### Context: Collection Adaptive Forms Save Progress button appears to click but doesn't trigger save functionality
### Root Cause: Frontend event handler not properly wired despite correct prop passing
### Investigation Path:
1. Verified database schema and permissions ✅
2. Fixed backend endpoints with proper request validation ✅
3. Fixed frontend infinite re-render loops with useCallback ✅
4. Added comprehensive debug logging throughout chain ✅
5. Button still not triggering onClick handler ❌

### Solutions Applied:

#### Backend Fixes (collection_crud_update_commands.py):
```python
# Fixed flow lookup query
flow_result = await db.execute(
    select(CollectionFlow)
    .where(CollectionFlow.flow_id == flow_id)  # Changed from .id to .flow_id
    .where(CollectionFlow.engagement_id == context.engagement_id)
)

# Fixed field references
flow.progress_percentage = form_metadata.get("completion_percentage", flow.progress_percentage)
# Removed non-existent updated_by field
```

#### Frontend Performance Fix (useAdaptiveFormFlow.ts):
```javascript
// Fixed infinite re-render loop
useEffect(() => {
  const shouldInitialize = autoInitialize && !checkingFlows && !hasBlockingFlows && !state.formData && !state.isLoading && !state.error;
  if (shouldInitialize) {
    const init = async () => {
      try {
        await initializeFlow();
      } catch (error) {
        setState(prev => ({ ...prev, error, isLoading: false }));
      }
    };
    init();
  }
}, [applicationId, flowIdFromUrl, checkingFlows, hasBlockingFlows, autoInitialize, state.formData, state.isLoading, state.error]);
// Removed initializeFlow from dependencies to prevent loop

// Wrapped handlers in useCallback
const handleSave = useCallback(async () => {
  // save logic
}, [state.formData, state.flowId, state.questionnaires, state.formValues, state.validation]);
```

#### Debug Logging Pattern:
```javascript
// AdaptiveFormContainer.tsx
onClick={() => {
  console.log('🔴 Save Progress button clicked in AdaptiveFormContainer');
  if (onSave) {
    console.log('✅ Calling onSave function...');
    onSave();
  } else {
    console.error('❌ onSave prop is not defined!');
  }
}}
```

### Database Validation:
```sql
-- Table exists with correct schema
-- Permissions verified for application_role
-- Test insert successful
INSERT INTO migration.collection_questionnaire_responses (...) VALUES (...);
```

### Remaining Issue:
Button onClick handler not firing despite correct wiring. Possible causes:
- Event propagation stopped by parent
- CSS pointer-events blocking
- React reconciliation issue
- Handler undefined at render time

### Testing Command:
```bash
# Check for saved responses
docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT COUNT(*) FROM migration.collection_questionnaire_responses;"
```

## Key Learnings:
1. Always check for infinite re-render loops when event handlers don't fire
2. Use useCallback for event handlers passed as props
3. Verify database field names match model definitions (flow_id vs id)
4. Add debug logging at every step of event chain to identify breaking point
5. Test with Playwright to simulate real user interactions
