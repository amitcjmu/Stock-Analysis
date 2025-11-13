# Duplicate Asset Bug Fix - Database Constraint Mismatch (Jan 2025)

## Problem: Unique Constraint Violations Despite Conflict Detection

**Symptom**: Assets with same name but different types bypassed conflict detection, causing database unique constraint violations.

**Error**:
```
duplicate key value violates unique constraint "ix_assets_unique_name_per_context"
Key (client_account_id, engagement_id, name)=(uuid, uuid, "On Premise") already exists.
```

**Root Cause**: Conflict detection checked `(name, asset_type)` composite (4 fields), but database constraint only enforces `(client_account_id, engagement_id, name)` (3 fields).

**Example**:
- Existing: `name="On Premise"`, `asset_type="Server"`
- New: `name="On Premise"`, `asset_type="Application"`
- Conflict check: `("On Premise", "Application")` != `("On Premise", "Server")` → NO CONFLICT ❌
- Database INSERT: Unique on NAME alone → VIOLATION ✅

## Solution: Check Name Alone First

**File**: `backend/app/services/asset_service/deduplication.py`

### Change 1: Add Name-Only Index

```python
# Declare indexes matching DB constraints
existing_by_hostname = {}
existing_by_ip = {}
existing_by_name = {}  # CRITICAL: name-only (matches DB constraint)
existing_by_name_type = {}  # name+type (for detailed messaging)
```

### Change 2: Build Both Indexes in Query

```python
# Query by NAME alone (matches DB constraint)
for asset in result.scalars().all():
    # Name-only index (critical for constraint matching)
    existing_by_name[asset.name] = asset
    # Name+type composite (for better conflict messaging)
    key = (asset.name, asset.asset_type or "Unknown")
    existing_by_name_type[key] = asset
```

### Change 3: Check NAME FIRST in Conflict Detection

```python
# CRITICAL: Check NAME ALONE first (matches DB constraint)
if name and name in existing_by_name:
    existing = existing_by_name[name]
    name_type_key = (name, asset_type)
    if name_type_key in existing_by_name_type:
        conflict_key = f"{name} ({asset_type})"  # Exact duplicate
    else:
        conflict_key = f"{name} (name conflict: existing={existing.asset_type}, new={asset_type})"

    conflicts.append({...})
    continue

# Then check hostname/IP (secondary)
```

## Pattern: Always Match Application Logic to Database Constraints

**Rule**: Conflict detection logic MUST check the EXACT fields defined in database unique constraints.

**Verification Steps**:
1. Find constraint in model: `UniqueConstraint("client_account_id", "engagement_id", "name")`
2. Match in conflict detection: Check these fields in same order
3. Build separate indexes for:
   - DB constraint matching (e.g., name-only)
   - Detailed error messaging (e.g., name+type)

**Common Mistake**: Checking composite keys that include more fields than the actual DB constraint.

## Usage

When implementing deduplication for ANY entity with unique constraints:
1. Check DB schema for EXACT constraint fields
2. Build index matching THOSE fields only
3. Check constraint fields BEFORE other identifier fields (hostname, IP, etc.)
4. Use additional fields ONLY for better error messages, not for conflict detection

**Files to Update**:
- `bulk_prepare_conflicts()` in deduplication modules
- Any custom conflict detection logic

## Related Issues

- Enhancement #907: Asset Creation Preview Modal
- Enhancement #908: Pessimistic Locking for Flow State
- Technical Debt #909: Modularize deduplication.py (715 lines > 400)
