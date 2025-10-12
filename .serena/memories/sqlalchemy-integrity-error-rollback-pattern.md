# SQLAlchemy IntegrityError Handling with Session Rollback

## Problem
After IntegrityError (duplicate keys, constraint violations), SQLAlchemy marks session as invalid. All subsequent operations fail with "This session is in 'inactive' state", causing cascading failures across multiple operations.

## Solution
Immediate rollback after IntegrityError to prevent session invalidation.

## Implementation Pattern

```python
from sqlalchemy.exc import IntegrityError

async def create_asset(...):
    try:
        created_asset = await create_method(...)
        return created_asset
    except IntegrityError as ie:
        await session.rollback()  # CRITICAL: Prevent session invalidation

        # Differentiate error types
        error_msg = str(ie.orig).lower() if hasattr(ie, "orig") else str(ie).lower()

        is_unique_violation = any(
            keyword in error_msg
            for keyword in ["unique constraint", "duplicate key", "duplicate entry"]
        )

        if is_unique_violation:
            # Race condition - can retry
            logger.warning(f"⚠️ Unique constraint violation (race condition): {ie}")
            raise  # Caller can retry
        else:
            # NOT NULL, foreign key, CHECK constraint - unrecoverable
            logger.error(f"❌ Unrecoverable IntegrityError: {ie}")
            raise  # Caller should NOT retry
```

## When to Apply
- Any database operation that might trigger IntegrityError
- Especially bulk operations where cascading failures are costly
- Asset creation, import processing, batch updates

## Benefits
- Prevents cascading session invalidation failures
- Enables proper retry logic for race conditions only
- Provides clear diagnostics (unique constraint vs other errors)

## Real-World Impact
Fixed Railway production error with 30+ cascading rollback failures after single IntegrityError.

## Related Files
- `backend/app/services/asset_service/deduplication.py` - Reference implementation
- ADR-015: Persistent Multi-Tenant Agent Architecture
