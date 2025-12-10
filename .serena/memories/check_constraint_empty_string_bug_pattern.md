# CHECK Constraint Empty String Bug Pattern

## Problem
PostgreSQL CHECK constraints on the `assets` table only allow specific values OR NULL, but NOT empty strings `''`.

When data cleansing produces empty strings for categorical fields, `CheckViolationError` occurs during asset creation.

## Root Cause
The cleansing pipeline may produce empty strings for fields that have CHECK constraints. The data transformation at line 259 in `transforms.py` removes `None` values but NOT empty strings:

```python
cleaned_data = {k: v for k, v in asset_data.items() if v is not None}
```

## All Fields with CHECK Constraints (as of December 2025)

### From migration 149 (`149_add_cmdb_assessment_fields_issue_798.py`)
- `virtualization_type`
- `business_logic_complexity`
- `configuration_complexity`
- `change_tolerance`

### From migration 150 (`150_security_and_data_integrity.py`)
- `application_type`
- `lifecycle`
- `hosting_model`
- `server_role`
- `security_zone`
- `application_data_classification`
- `risk_level`
- `tshirt_size`
- `six_r_strategy`
- `migration_complexity`
- `sixr_ready`
- `status`
- `migration_status`
- `criticality`
- `asset_type`

**NOTE**: `environment` field explicitly allows empty string `""` in its CHECK constraint, so it should NOT be sanitized.

## Fix Applied In
1. `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/transforms.py`
   - Added sanitization loop after line 259 to delete empty strings for CHECK constraint fields

2. `backend/app/services/asset_service/deduplication/orchestration.py`
   - Added `CHECK_CONSTRAINT_FIELDS` list and `sanitize_check_constraint_fields()` function
   - Called before `create_new_asset()`

3. `backend/app/services/asset_service/base.py`
   - Imports and calls `sanitize_check_constraint_fields()` before asset creation

## Error Signature
```
asyncpg.exceptions.CheckViolationError: new row for relation "assets" violates check constraint "chk_assets_application_type"
```

## Prevention
When adding new CHECK constraints in migrations:
1. Update `CHECK_CONSTRAINT_FIELDS` in `orchestration.py`
2. Update `check_constraint_fields` in `transforms.py`
3. Always allow NULL in CHECK constraints (for optional fields)
4. Consider if empty string should be allowed (like `environment` does)
