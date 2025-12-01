# Issue #677: Questionnaire Display Race Condition Fix

## Problem
Collection flow showed "0/0 fields" instead of displaying generated questionnaires (e.g., "31/31 fields"). Root cause was a two-part timing issue.

## Root Cause Analysis

### Part 1: Frontend Race Condition
Frontend polled questionnaires immediately when phase changed to `questionnaire_generation`, but AI agent needed 30-60 seconds to generate and save questionnaires.

### Part 2: Backend Phase Transition Unreliability
Background tasks generating questionnaires could be interrupted by server reloads. Phase never transitioned from `questionnaire_generation` to `manual_collection` even after questionnaire was successfully created in database.

## Solution: Two-Part Fix

### Frontend Fix: Conditional Polling

**File**: `src/hooks/collection/useAdaptiveFormFlow.ts`
```typescript
// Add phase polling
const { data: flowDetails } = useQuery({
  queryKey: ['collection-flow-details', flowId],
  queryFn: () => collectionService.getCollectionFlowDetails(flowId),
  refetchInterval: 2000, // Check phase every 2 seconds
  enabled: !!flowId && flowId !== 'XXXXXXXX...'
});

const currentPhase = flowDetails?.current_phase;
```

**File**: `src/hooks/collection/useQuestionnairePolling.ts`
```typescript
// Only poll when phase signals ready
const { data: questionnaires } = useQuery({
  queryKey: ['questionnaires', flowId],
  queryFn: () => collectionService.getQuestionnaires(flowId),
  refetchInterval: 5000,
  enabled: !!flowId && currentPhase === 'manual_collection' // Wait for ready signal
});

// Show loading message during generation
if (currentPhase === 'questionnaire_generation') {
  return {
    questionnaires: [],
    status: 'Generating questionnaire with AI agent...',
    isLoading: true
  };
}
```

### Backend Fix: Defensive Phase Transition

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py`
```python
# In get_adaptive_questionnaires endpoint
if existing_questionnaires:
    # Defensive check: Questionnaire exists but phase not updated
    has_questions = any(
        hasattr(q, "questions") and q.questions and len(q.questions) > 0
        for q in existing_questionnaires
    )

    if has_questions and flow.current_phase == "questionnaire_generation":
        logger.warning(
            f"⚠️ Flow {flow_id} has questionnaire but phase still "
            f"'questionnaire_generation'. Performing defensive phase transition"
        )

        try:
            await db.execute(
                sql_update(CollectionFlow)
                .where(CollectionFlow.flow_id == UUID(flow_id))
                .values(
                    current_phase="manual_collection",
                    status="paused",  # Awaiting user input
                    progress_percentage=50.0,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
            logger.info(f"✅ Defensive phase transition: {flow_id} → manual_collection")
        except Exception as e:
            # Don't fail request if phase transition fails
            logger.error(f"❌ Defensive phase transition failed: {e}")

    return existing_questionnaires
```

## Why This Works

1. **Frontend**: Waits for backend's explicit "ready" signal (phase = `manual_collection`) instead of polling too early
2. **Backend**: Self-healing defensive fix automatically corrects phase if background task was interrupted
3. **Resilient**: Handles server reloads, crashes, and timeouts gracefully

## Testing Evidence

- Frontend shows "Generating questionnaire..." during loading (not "0/0 fields")
- Phase correctly transitions to `manual_collection` after generation
- Database verification: `current_phase = 'manual_collection'`, `status = 'paused'`
- User can interact with questionnaire form displaying correct field count

## Usage Pattern

Apply this pattern when:
- Background async tasks take significant time (30-60s)
- Tasks can be interrupted by server restarts/reloads
- Frontend needs to wait for backend completion signal
- Self-healing behavior is desired for stuck states

## Related Issues

- Issue #678: Asset-type-agnostic gaps (separate backend fix needed)
- Issue #679: Not checking existing data before generating gaps (separate backend fix needed)

## Key Learnings

1. **Defensive Programming**: Add checks in query endpoints to auto-fix stuck states
2. **Phase Signals**: Use phase transitions as completion signals, not just for state tracking
3. **Race Conditions**: Always wait for explicit ready signals when dealing with async operations
4. **Self-Healing**: Make systems resilient to interruptions by adding recovery logic
