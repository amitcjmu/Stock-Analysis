# SQLAlchemy Async Session Tracking Patterns

## Problem: Updates Not Persisting in Async Sessions
**Issue**: User model changes (like default_client_id, default_engagement_id) weren't being saved to database despite calling commit().

## Root Cause
Using `selectinload` for relationship loading in async SQLAlchemy creates a separate query that doesn't properly track changes for updates.

## Solution Pattern
Replace `selectinload` with `joinedload` for proper session tracking:

```python
# ❌ WRONG - Changes won't be tracked properly
from sqlalchemy.orm import selectinload
query = (
    select(UserProfile)
    .options(selectinload(UserProfile.user))
    .where(UserProfile.user_id == user_id)
)
result = await self.db.execute(query)
user_profile = result.scalar_one_or_none()

# ✅ CORRECT - Changes will be tracked
from sqlalchemy.orm import joinedload
query = (
    select(UserProfile)
    .options(joinedload(UserProfile.user))
    .where(UserProfile.user_id == user_id)
)
result = await self.db.execute(query)
user_profile = result.unique().scalar_one_or_none()  # Note: unique() needed with joinedload
```

## Key Differences
- **selectinload**: Executes separate query, may not track changes in async context
- **joinedload**: Performs JOIN query, ensures objects are attached to session
- **unique()**: Required with joinedload to handle potential duplicates from JOIN

## Files Fixed
- backend/app/services/rbac_handlers/user_management_handler.py:606-623

## Testing
After making changes to related models through joined relationships, verify with:
1. Check database directly after commit
2. Refresh page and verify persistence
3. Log the actual SQL being executed

## Related Patterns
- Always use joinedload when you need to modify related objects
- Use selectinload for read-only operations where performance matters
- Consider explicit refresh() if tracking issues persist
