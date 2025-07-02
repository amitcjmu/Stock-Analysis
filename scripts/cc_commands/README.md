# CC Commands

This directory contains custom CC commands for the migration orchestrator platform.

## Available Commands

### check-db-sync

**Purpose**: Identify mismatches and differences between SQLAlchemy models and actual PostgreSQL database tables.

**Usage**:
```bash
# Check all tables for schema mismatches
./scripts/cc_commands/check-db-sync

# Check specific table only
./scripts/cc_commands/check-db-sync --table users

# Generate migration scripts for detected differences
./scripts/cc_commands/check-db-sync --fix --verbose

# Save detailed report to JSON file
./scripts/cc_commands/check-db-sync --output schema_report.json
```

**What it checks**:
- ✅ Missing tables in database vs models
- ✅ Extra tables in database not in models  
- ✅ Column type mismatches
- ✅ Column nullable/primary key differences
- ✅ Missing/extra columns
- ✅ Index differences
- ✅ Foreign key constraint mismatches

**Output**:
- Detailed comparison report
- Recommendations for fixing issues
- Optional Alembic migration generation
- JSON export for automation

**Example Output**:
```
🔍 DATABASE MODEL SYNCHRONIZATION REPORT
============================================================
📅 Generated: 2025-01-07T10:30:15.123456
🔍 Total Differences Found: 3
📋 Model Tables: 15
🗄️ Database Tables: 14
✅ Tables in Sync: 13
⚠️ Tables Only in Models: 1
⚠️ Tables Only in DB: 0

🔍 DETAILED DIFFERENCES:
----------------------------------------

Missing Table In Db:
  • Table 'new_feature_table' exists in models but not in database

Column Type Mismatch:
  • Column 'status' type mismatch: model=VARCHAR(50), db=VARCHAR(255)
  • Column 'created_at' type mismatch: model=TIMESTAMP, db=TIMESTAMPTZ

💡 RECOMMENDATIONS:
----------------------------------------
1. Run 'alembic revision --autogenerate' to create migration for missing tables
2. Review and resolve type/constraint mismatches manually
```

**Prerequisites**:
- Docker containers running (`docker-compose up -d`)
- Database accessible
- All SQLAlchemy models imported

**Common Use Cases**:
1. **Before deployment**: Verify schema is in sync
2. **After model changes**: Check what migrations are needed
3. **Debugging sync issues**: Find why data isn't persisting correctly
4. **Schema drift detection**: Regular monitoring for unintended changes
5. **Team coordination**: Ensure everyone has consistent schema

**Integration with Development Workflow**:
```bash
# Daily development check
./scripts/cc_commands/check-db-sync

# Before creating PR
./scripts/cc_commands/check-db-sync --fix

# CI/CD pipeline check
./scripts/cc_commands/check-db-sync --output ci_report.json

# Production deployment verification
./scripts/cc_commands/check-db-sync --table critical_table_name
```

## Command Development Guidelines

When creating new CC commands:

1. **Make them executable**: `chmod +x script_name`
2. **Include help**: `--help` flag with usage examples
3. **Docker-first**: All operations through containers
4. **Error handling**: Proper exit codes and error messages
5. **Colored output**: Use colors for better UX
6. **Documentation**: Update this README

## Directory Structure

```
scripts/cc_commands/
├── README.md              # This file
├── check-db-sync          # Database sync checker
└── [future commands]      # Additional commands as needed
```