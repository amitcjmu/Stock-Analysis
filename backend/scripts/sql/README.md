# SQL Scripts

This directory contains SQL scripts for database operations, testing, and data seeding.

## Files

### create_test_data.sql
Original SQL script for creating test data including demo assets, applications, and discovery data.

**Usage**:
```bash
docker exec -it migration_postgres psql -U postgres -d migration_db -f /path/to/create_test_data.sql
```

### create_test_data_v2.sql
Enhanced version of test data creation script with additional asset types including unmapped assets (databases, servers, network devices).

**Features**:
- Creates diverse asset types for comprehensive testing
- Includes mapped and unmapped assets
- Sets up realistic discovery and assessment data
- Populates Demo Corp engagement with varied asset scenarios

**Usage**:
```bash
docker exec -it migration_postgres psql -U postgres -d migration_db -f /path/to/create_test_data_v2.sql
```

**Reference**: See `/docs/implementation/UNMAPPED_ASSETS_IMPLEMENTATION.md` for details on unmapped assets testing.

## Location
`/backend/scripts/sql/`
