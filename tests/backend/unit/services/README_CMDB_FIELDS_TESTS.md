# CMDB Fields Unit Tests

## Test File
`test_asset_service_cmdb_fields.py`

## Purpose
Unit tests for PR #833: CMDB fields population and child table creation logic in AssetService.

## Coverage
Tests the following features:
- 24 new explicit CMDB columns population in assets table
- Conditional creation of `asset_eol_assessments` records
- Conditional creation of `asset_contacts` records
- Data validation (e.g., EOL risk level constraints)

## Test Classes

### 1. TestCMDBFieldsPopulation (1 test)
Validates that all 24 CMDB fields are properly extracted and passed to asset creation.

### 2. TestEOLAssessmentCreation (5 tests)
Tests conditional creation of EOL assessment records:
- Created when EOL data exists
- Not created when no EOL data
- Risk level validation (low, medium, high, critical)
- Invalid risk level handling (set to NULL)
- Case-insensitive normalization

### 3. TestAssetContactCreation (5 tests)
Tests conditional creation of contact records:
- Multiple contacts for one asset (business_owner, technical_owner, architect)
- Not created when no email data
- Name fallback from email
- Single contact creation

### 4. TestIntegratedCMDBWorkflow (1 test)
End-to-end test for complete CMDB data flow with all features together.

## Running Tests

```bash
# Run this specific test file
pytest tests/backend/unit/services/test_asset_service_cmdb_fields.py -v

# Run with markers
pytest -m "unit and discovery" tests/backend/unit/services/test_asset_service_cmdb_fields.py

# Run with coverage
pytest tests/backend/unit/services/test_asset_service_cmdb_fields.py --cov=app.services.asset_service

# Run specific test class
pytest tests/backend/unit/services/test_asset_service_cmdb_fields.py::TestEOLAssessmentCreation -v
```

## Test Standards Compliance

✅ **Location**: `tests/backend/unit/services/` (per testing-strategy.md)
✅ **Markers**: `@pytest.mark.unit`, `@pytest.mark.discovery`, `@pytest.mark.asyncio`
✅ **Fixtures**: Defined within test file (standard practice)
✅ **Mocking**: Uses `AsyncMock(spec=AsyncSession)` for database session
✅ **Coverage Target**: 90%+
✅ **Documentation**: Clear docstrings

## Related Files

**Implementation:**
- `backend/app/services/asset_service.py` (Lines 269-631)
- `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/transforms.py`

**Models:**
- `backend/app/models/asset/specialized.py` (AssetEOLAssessment, AssetContact)

**Migrations:**
- `backend/alembic/versions/116_add_cmdb_explicit_fields.py`
- `backend/alembic/versions/117_create_cmdb_specialized_tables.py`
