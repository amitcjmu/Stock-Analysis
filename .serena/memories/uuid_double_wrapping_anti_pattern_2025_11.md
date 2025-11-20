# UUID Double-Wrapping Anti-Pattern (November 2025)

## Problem

When converting context string IDs to UUID objects for database queries, then passing those UUID objects to methods that internally convert strings to UUIDs, a "double-wrapping" error occurs:

```python
AttributeError: 'UUID' object has no attribute 'replace'
```

## Root Cause

1. Context IDs arrive as **strings** from request headers (e.g., `'11111111-1111-1111-1111-111111111111'`)
2. Endpoint converts strings to **UUID objects** for database queries
3. Endpoint passes UUID objects to service methods
4. Service methods try to wrap them in `UUID()` constructor again
5. `UUID()` constructor expects strings and calls `.replace()` on input
6. UUID objects don't have `.replace()` method → AttributeError

## Example Error Trace

```python
# In readiness_gaps.py endpoint:
client_account_uuid = UUID(context.client_account_id)  # String → UUID ✅

# Passed to service method:
readiness_result = await service.analyze_asset_readiness(
    client_account_id=client_account_uuid  # ❌ Passing UUID object
)

# In asset_readiness_service.py (line 61):
Asset.client_account_id == UUID(client_account_id)  # ❌ UUID(UUID object) fails
```

**Error**:
```
AttributeError: 'UUID' object has no attribute 'replace'
File: /app/app/services/assessment/asset_readiness_service.py:61
```

## Solution: Convert UUID Back to String

### ✅ CORRECT Pattern

```python
# Step 1: Convert context strings to UUIDs for database queries
# Pattern per Serena memory: collection_gaps_qodo_bot_fixes_2025_21
try:
    client_account_uuid = (
        UUID(context.client_account_id)
        if isinstance(context.client_account_id, str)
        else context.client_account_id
    )
    engagement_uuid = (
        UUID(context.engagement_id)
        if isinstance(context.engagement_id, str)
        else context.engagement_id
    )
except (ValueError, TypeError) as e:
    raise HTTPException(
        status_code=400,
        detail=f"Invalid tenant ID format in context: {str(e)}",
    )

# Step 2: Use UUID objects in SQLAlchemy WHERE clauses
app_query = select(CanonicalApplication).where(
    CanonicalApplication.client_account_id == client_account_uuid,  # ✅ UUID object
    CanonicalApplication.engagement_id == engagement_uuid,         # ✅ UUID object
)

# Step 3: Convert back to strings when passing to methods that do internal conversion
readiness_result = await service.analyze_asset_readiness(
    asset_id=asset.id,
    client_account_id=str(client_account_uuid),  # ✅ String for internal UUID() conversion
    engagement_id=str(engagement_uuid),          # ✅ String for internal UUID() conversion
    db=db,
)
```

## The Three-Stage UUID Conversion Pattern

### Stage 1: API Boundary → UUID Objects
**Purpose**: Validate and convert incoming string IDs
**Location**: FastAPI endpoint entry point
**Pattern**:
```python
try:
    client_account_uuid = UUID(context.client_account_id) if isinstance(...) else ...
except (ValueError, TypeError) as e:
    raise HTTPException(status_code=400, detail=f"Invalid ID: {e}")
```

### Stage 2: Database Queries → Use UUID Objects
**Purpose**: Match database column types
**Location**: SQLAlchemy queries
**Pattern**:
```python
query = select(Model).where(
    Model.client_account_id == client_account_uuid  # UUID object matches UUID column
)
```

### Stage 3: Service Method Calls → Back to Strings
**Purpose**: Avoid double-wrapping when methods do internal UUID() conversion
**Location**: Service method invocations
**Pattern**:
```python
result = await service.method(
    client_account_id=str(client_account_uuid),  # String for internal conversion
    engagement_id=str(engagement_uuid)
)
```

## Detection

### Symptoms
- `AttributeError: 'UUID' object has no attribute 'replace'`
- Error occurs in service layer, not endpoint
- Error trace shows `UUID()` constructor call on UUID column comparison

### Search Pattern
```bash
# Find potential violations
grep -r "UUID(client_account_uuid)" backend/
grep -r "UUID(engagement_uuid)" backend/
grep -r "UUID.*_uuid)" backend/  # Passing _uuid variables to UUID()
```

## When to Use This Pattern

Apply when:
1. **Context IDs** come as strings from request headers
2. **Database columns** are UUID type (need UUID objects for queries)
3. **Service methods** internally convert string IDs to UUID (documented in method signature or implementation)
4. **Error indicates** double-wrapping (AttributeError on `.replace()`)

## Related Patterns

- **uuid-tenant-id-enforcement-codebase-pattern-2025-10**: Never convert UUID to integers, always use UUID objects
- **collection_gaps_qodo_bot_fixes_2025_21**: Add try-except for UUID validation
- **sqlalchemy-uuid-string-join-casting**: Use `cast(column, String)` for cross-type joins

## Files Using This Pattern

1. `backend/app/api/v1/canonical_applications/router/readiness_gaps.py:73-156` - Readiness gaps endpoint
2. `backend/app/api/v1/endpoints/collection_applications/handlers.py:*` - Collection flow handlers (should adopt)

## Discovery Context

- Found during "Refresh Readiness" database persistence fix (November 2025)
- Initial fix converted context strings to UUIDs for queries (correct)
- But passed UUID objects to `analyze_asset_readiness()` (incorrect)
- Service method tried `UUID(client_account_id)` causing double-wrapping
- Fix: Convert UUID objects back to strings before passing to service methods

## Prevention Checklist

Before writing endpoint code that converts context IDs:

- [ ] Convert context strings to UUID objects with try-except
- [ ] Use UUID objects in database WHERE clauses
- [ ] Check if service methods do internal `UUID()` conversion
- [ ] If yes, convert UUID objects back to strings before passing
- [ ] Test with actual backend (not just type checking)
- [ ] Verify no AttributeError on `.replace()` in service layer

## Anti-Pattern Summary

**❌ WRONG**: Pass UUID objects to methods that convert strings to UUIDs
```python
client_uuid = UUID(context.client_account_id)
service.method(client_account_id=client_uuid)  # ❌ Method does UUID() again
```

**✅ CORRECT**: Pass strings to methods that convert internally
```python
client_uuid = UUID(context.client_account_id)  # For DB queries
service.method(client_account_id=str(client_uuid))  # ✅ String for internal UUID()
```

## Reference

- Session: November 2025 - Collection Flow UUID Validation Fixes
- Error: "Refresh Readiness 500 errors" - Double UUID wrapping
- Fix Commit: [Timestamp 01:27:59]
- Related Issue: Collection flow asset selection page showing instead of questionnaire
