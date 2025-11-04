# Pre-commit Complexity Reduction Pattern (Jan 2025)

## Problem: flake8 C901 "Function Too Complex"

**Error**:
```
backend/app/services/asset_service/deduplication.py:505:1: C901 'bulk_prepare_conflicts' is too complex (16)
```

**Threshold**: Cyclomatic complexity must be ≤ 15 (McCabe complexity metric)

## Solution: Extract Helper Function Pattern

**Before** (complexity 16):
```python
async def bulk_prepare_conflicts(...):
    # Step 1: Build indexes (complexity +2)
    existing_by_name = {}
    # ...

    # Step 2: Check each asset (complexity +14)
    for asset_data in assets_data:
        hostname = asset_data.get("hostname")
        ip = asset_data.get("ip_address")
        name = get_smart_asset_name(asset_data)
        asset_type = asset_data.get("asset_type", "Unknown")

        # Check name (complexity +2)
        if name and name in existing_by_name:
            # ... 10 lines of logic
            continue

        # Check hostname (complexity +2)
        if hostname and hostname in existing_by_hostname:
            # ... 8 lines of logic
            continue

        # Check IP (complexity +2)
        if ip and ip in existing_by_ip:
            # ... 8 lines of logic
            continue

        # No conflict (complexity +1)
        conflict_free.append(asset_data)
```

**After** (complexity ≤ 10):
```python
def _check_single_asset_conflict(
    asset_data: Dict[str, Any],
    existing_by_name: Dict[str, Asset],
    existing_by_name_type: Dict[Tuple[str, str], Asset],
    existing_by_hostname: Dict[str, Asset],
    existing_by_ip: Dict[str, Asset],
) -> Optional[Dict[str, Any]]:
    """Returns conflict dict if found, None otherwise."""
    hostname = asset_data.get("hostname")
    ip = asset_data.get("ip_address")
    name = get_smart_asset_name(asset_data)
    asset_type = asset_data.get("asset_type", "Unknown")

    # Check name
    if name and name in existing_by_name:
        # ... conflict logic
        return {...}

    # Check hostname
    if hostname and hostname in existing_by_hostname:
        return {...}

    # Check IP
    if ip and ip in existing_by_ip:
        return {...}

    return None  # No conflict


async def bulk_prepare_conflicts(...):
    # Step 1: Build indexes
    existing_by_name = {}
    # ...

    # Step 2: Check each asset using helper (complexity +2 only)
    for asset_data in assets_data:
        conflict = _check_single_asset_conflict(
            asset_data,
            existing_by_name,
            existing_by_name_type,
            existing_by_hostname,
            existing_by_ip,
        )

        if conflict:
            conflicts.append(conflict)
        else:
            conflict_free.append(asset_data)
```

## Pattern: Complexity Reduction via Extraction

### When to Extract
- Function complexity > 15
- Loop body has multiple conditional branches
- Repeated logic patterns in loop

### How to Extract
1. **Identify** the high-complexity section (usually loop body with if/elif chains)
2. **Extract** to pure function (no side effects preferred)
3. **Pass** all needed context as parameters
4. **Return** result (not mutate global state if possible)

### Naming Convention
- Prefix with `_` if internal helper
- Name describes WHAT it checks/does: `_check_single_asset_conflict`, `_validate_field_mapping`
- Use verb + noun pattern

## Complexity Calculation (McCabe)

```python
def example():          # +1 (entry point)
    if condition1:      # +1
        for item in items:  # +1
            if item.valid:  # +1
                process()
    elif condition2:    # +1
        handle()
    return result       # +0
# Total: 5
```

**Thresholds**:
- 1-5: Simple (good)
- 6-10: Moderate (acceptable)
- 11-15: Complex (review needed)
- 16+: Too complex (refactor required)

## Usage

Apply this pattern when pre-commit fails with C901:
1. Find the loop/conditional section causing complexity
2. Extract to helper function
3. Helper should be ≤ 10 complexity itself
4. Pass indexes/state as parameters (not global access)
5. Return result instead of mutating caller state

**Anti-pattern**: Extracting without reducing complexity (just moving code around)
