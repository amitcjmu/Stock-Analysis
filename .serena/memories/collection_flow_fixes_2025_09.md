# Collection Flow Fixes and Patterns

## Bootstrap Questionnaire Completion Issue (2025-09-02)
### Context: Collection flow not progressing after form submission
### Problem: Bootstrap questionnaire kept being returned after submission
### Root Cause: Backend didn't check for existing responses before returning bootstrap

### Solution 1: Backend Response Check
**File:** `backend/app/api/v1/endpoints/collection_crud_questionnaires.py:166-184`
```python
# Check if bootstrap questionnaire already completed
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse

response_check = await db.execute(
    select(CollectionQuestionnaireResponse)
    .where(CollectionQuestionnaireResponse.collection_flow_id == flow.id)
    .where(CollectionQuestionnaireResponse.questionnaire_type == "adaptive_form")
    .limit(1)
)
has_responses = response_check.scalar_one_or_none() is not None

if has_responses:
    logger.info(f"Bootstrap questionnaire already completed for flow {flow_id}")
    return []  # Return empty list to indicate completion
```

### Solution 2: Frontend Completion Percentage
**File:** `src/hooks/collection/useAdaptiveFormFlow.ts:750-765`
```typescript
// For bootstrap questionnaires, send 100% completion when submitted
const isBootstrapForm = questionnaireId.startsWith('bootstrap_');
const completionPercentage = isBootstrapForm ? 100 : (state.validation?.completionPercentage || 0);

const submissionData = {
    responses: data,
    form_metadata: {
        completion_percentage: completionPercentage,
        // ... other fields
    }
};
```

### Result: Flow properly completes and shows completion screen

## Asset Inventory API Pattern (2025-09-02)
### Context: Collection flow application selection failing with discovery API
### Problem: Wrong API endpoint used for non-discovery flows
### Solution: Use asset-inventory endpoints for collection flows
```typescript
// Instead of: /unified-discovery/assets
// Use: /asset-inventory/list/paginated

// Filter for applications only:
const applications = allAssets.filter(asset =>
    asset.asset_type?.toLowerCase() === 'application' ||
    asset.asset_type?.toLowerCase() === 'app'
);
```

## Database Storage Pattern
### Context: Understanding where collection data is stored
### Tables:
- `CollectionQuestionnaireResponse` - Stores all form responses
- `CollectionFlow` - Main flow tracking with status/progress
- Response linked via `collection_flow_id` to flow's internal ID

### Key Fields:
- `questionnaire_type`: "adaptive_form" for bootstrap
- `question_id`: Field identifier
- `response_value`: JSON storage for complex values
- `asset_id`: Links to specific application if selected
