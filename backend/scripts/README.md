# Backend Scripts Directory

This directory contains organized scripts for backend operations, maintenance, and development.

## Directory Structure

### `/database`
Database management and migration scripts:
- **compare_tables.py** - Compares SQLAlchemy models with actual database tables
- **create_new_001_migration.py** - Regenerates migration 001 with all tables
- **generate_correct_migrations.py** - Planning script for migration regeneration
- **run_migration.py** - Railway database migration runner
- **init.sql** - Database initialization with extensions and schema
- **fix_crewai_flow_extensions.sql** - SQL fix for crewai_flow_state_extensions table

### `/deployment`
Railway deployment and production scripts:
- **railway_deploy_prep.py** - Prepares local database for Railway deployment
- **railway_migration_check.py** - Validates migrations for Railway compatibility
- **migrate_feedback_to_railway.py** - Exports feedback data to Railway PostgreSQL
- **start.sh** - Railway API server startup script

### `/development`
Development utilities and tools:
- **trigger_data_import.py** - Manually triggers data import phase execution

### `/one-time-fixes`
Scripts created for specific one-time fixes (archived for reference):
- **add_client_context.py** - Adds client context to JSON data files
- **fix_field_mappings_context.py** - Updates field mappings to demo context
- **complete_active_flows.py** - Completes active discovery flows
- **promote_assets.py** - Promotes discovery assets to main assets table

### `/qa`
Quality assurance and validation scripts (existing directory)

## Usage Notes

1. **Database scripts** should be run with caution, especially in production
2. **Deployment scripts** are designed for Railway platform deployment
3. **Development scripts** are for local development and testing
4. **One-time fixes** are kept for historical reference but should not be run without understanding their purpose

## Running Scripts

Most scripts should be run from the backend directory:
```bash
cd backend
python scripts/database/compare_tables.py
```

For Docker environments:
```bash
docker exec migration_backend python scripts/database/compare_tables.py
```
