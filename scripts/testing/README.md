# Testing Scripts

This directory contains Python test scripts for manual testing and validation of backend functionality.

## Files

### test_asset_inventory.py
Tests asset inventory functionality including CRUD operations and data validation.

**Usage**:
```bash
docker exec -it migration_backend python /app/scripts/testing/test_asset_inventory.py
```

### test_asset_writeback.py
Tests writeback functionality for assets - verifying data persistence and update operations.

**Usage**:
```bash
docker exec -it migration_backend python /app/scripts/testing/test_asset_writeback.py
```

### test_existing_data.py
Validates existing data integrity and relationships in the database.

**Usage**:
```bash
docker exec -it migration_backend python /app/scripts/testing/test_existing_data.py
```

### test_gap_analysis.py
Tests gap analysis functionality for discovery flows - identifies missing data fields.

**Usage**:
```bash
docker exec -it migration_backend python /app/scripts/testing/test_gap_analysis.py
```

### test_gap_analysis_e2e.py
End-to-end test for gap analysis workflow including questionnaire generation.

**Usage**:
```bash
docker exec -it migration_backend python /app/scripts/testing/test_gap_analysis_e2e.py
```

### test_recovery_999.py
Recovery test for issue #999 - validates specific bug fix scenarios.

**Usage**:
```bash
docker exec -it migration_backend python /app/scripts/testing/test_recovery_999.py
```

## Important Notes

- All scripts should be run from within the Docker container
- Scripts expect database to be running and accessible
- Use absolute paths when referencing files from inside container
- Check script headers for specific environment variables or prerequisites

## Location
`/scripts/testing/`
