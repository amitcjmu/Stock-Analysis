# Multi-Tenant Questionnaire Deduplication with Failed Retry Pattern

## Problem
When reusing assets across collection flows, attempting to create a new questionnaire for an asset that previously failed causes:
```
duplicate key value violates unique constraint "uq_questionnaire_per_asset_per_engagement"
```

## Root Cause
Deduplication query filters OUT failed questionnaires:
```python
# This excludes failed records from consideration
AdaptiveQuestionnaire.completion_status != "failed"
```

Then tries to INSERT new record, hitting unique constraint on `(engagement_id, asset_id)`.

## Solution Pattern

### 1. Enhanced Deduplication Query (Add client_account_id)
```python
async def get_existing_questionnaire_for_asset(
    client_account_id: UUID,  # ✅ Added for org-level isolation
    engagement_id: UUID,
    asset_id: UUID,
    db: AsyncSession,
) -> Optional[AdaptiveQuestionnaire]:
    result = await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.client_account_id == client_account_id,  # ✅ Multi-tenant
            AdaptiveQuestionnaire.engagement_id == engagement_id,
            AdaptiveQuestionnaire.asset_id == asset_id,
            AdaptiveQuestionnaire.completion_status != "failed",  # Excludes failed
        )
    )
    return result.scalar_one_or_none()
```

### 2. Separate Failed Questionnaire Check + UPDATE Pattern
```python
# After checking for reusable questionnaires, check for FAILED separately
failed_result = await db.execute(
    select(AdaptiveQuestionnaire).where(
        AdaptiveQuestionnaire.client_account_id == context.client_account_id,
        AdaptiveQuestionnaire.engagement_id == context.engagement_id,
        AdaptiveQuestionnaire.asset_id == asset_id,
        AdaptiveQuestionnaire.completion_status == "failed",  # Only failed
    )
)
failed_questionnaire = failed_result.scalar_one_or_none()

if failed_questionnaire:
    # UPDATE existing failed record to pending (prevents duplicate INSERT)
    failed_questionnaire.completion_status = "pending"
    failed_questionnaire.updated_at = datetime.now(timezone.utc)
    failed_questionnaire.collection_flow_id = flow.id  # Update to current flow
    failed_questionnaire.description = "Generating tailored questionnaire..."
    await db.commit()
    await db.refresh(failed_questionnaire)

    # Trigger background regeneration with updated ID
    questionnaire_id = failed_questionnaire.id
    task = asyncio.create_task(_background_generate(questionnaire_id, ...))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return  # Skip creating new questionnaire
```

## Multi-Tenant Isolation Levels

**Organization-level**: `client_account_id` (one company's data)
**Project-level**: `engagement_id` (one migration project)
**Asset-level**: `asset_id` (one application/server/database)

**Unique Constraint**: `(client_account_id, engagement_id, asset_id)`

Ensures questionnaire deduplication scoped to:
- Same organization
- Same project
- Same asset
- Across multiple collection flows

## When to Apply

Use this pattern when:
- Entity has unique constraint on composite key
- Entity has status field (pending/ready/completed/failed)
- Failed entities should be retried on next attempt
- Entity is scoped by multi-tenant hierarchy (org → project → resource)

## Related Files
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py` (lines 100-150)
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/deduplication.py` (lines 18-45)
- `backend/app/models/collection_flow/adaptive_questionnaire_model.py` (completion_status field)
