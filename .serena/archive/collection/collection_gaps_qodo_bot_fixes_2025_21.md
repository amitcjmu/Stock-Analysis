# Collection Gaps Phase 2 - Qodo Bot Fix Patterns

## Insight 1: Logger.bind() to LoggerAdapter Migration
**Problem**: Python's standard logger doesn't have .bind() method, causing AttributeError
**Solution**: Use LoggerAdapter for contextual logging
**Code**:
```python
# WRONG - AttributeError
import logging
logger = logging.getLogger(__name__)
self.logger = logger.bind(client_account_id=str(context.client_account_id))

# CORRECT - LoggerAdapter
self.logger = logging.LoggerAdapter(
    logger,
    {
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
    },
)
```
**Usage**: When adding context to standard Python loggers

## Insight 2: Parameter Shadowing fastapi.status Module
**Problem**: Query parameter named 'status' shadows imported status module
**Solution**: Rename parameter to avoid shadowing
**Code**:
```python
# WRONG - Shadows imported module
from fastapi import status
async def list_governance_requirements(
    status: Optional[str] = Query(None, description="Filter by status"),
    ...
):
    # status.HTTP_500_INTERNAL_SERVER_ERROR fails - status is now a string!

# CORRECT - No shadowing
async def list_governance_requirements(
    approval_status: Optional[str] = Query(None, description="Filter by status"),
    ...
):
    # status.HTTP_500_INTERNAL_SERVER_ERROR works correctly
```
**Usage**: When FastAPI endpoints import status module and have status parameters

## Insight 3: UUID Type Conversion for Database Operations
**Problem**: context.user_id is string but database expects UUID type
**Solution**: Convert to UUID with proper error handling
**Code**:
```python
# WRONG - Type mismatch
conflict.resolve_conflict(
    resolved_by=context.user_id,  # String passed to UUID field
    rationale=resolution.rationale,
)

# CORRECT - Proper conversion
from uuid import UUID
try:
    resolved_by_uuid = UUID(context.user_id) if context.user_id else None
except (ValueError, TypeError):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid user ID format in context",
    )

conflict.resolve_conflict(
    resolved_by=resolved_by_uuid,
    rationale=resolution.rationale,
)
```
**Usage**: When passing string IDs to UUID database fields

## Insight 4: Asset-Agnostic Collection Implementation
**Problem**: Forms hardcoded for "Application Data Collection" instead of generic assets
**Solution**: Update terminology throughout backend/frontend
**Code**:
```python
# Backend questionnaire template
return {
    "title": "Asset Data Collection",  # Not "Application Information Collection"
    "form_fields": [
        {
            "field_id": "asset_name",  # Not "application_name"
            "question_text": "What is the asset name?",
            "field_id": "asset_type",
            "options": [
                "application",
                "database",
                "server",
                "network_device",
                "storage_system",
                "middleware",
                "container",
                "virtual_machine",
                "cloud_service",
                # ... more asset types
            ],
        }
    ]
}

# Frontend
<CardTitle>Asset Data Collection</CardTitle>
<TabsTrigger value="single">Single Asset</TabsTrigger>
```
**Usage**: When implementing asset-agnostic collection vs application-specific

## Insight 5: Pre-commit Hook Variable Resolution
**Problem**: Linter reverts fixes, causing undefined variable errors
**Solution**: Ensure all variable references are updated consistently
**Code**:
```python
# After renaming parameter, update ALL references:
async def list_governance_requirements(
    approval_status: Optional[str] = Query(...),  # Renamed parameter
):
    if approval_status == "PENDING":  # Update condition
        requests = await repo.get_by_filters(status=approval_status)  # Update argument

    # In error handling too:
    "details": {
        "status": approval_status,  # Not the old 'status' variable
    }
```
**Usage**: When renaming parameters to avoid shadowing
