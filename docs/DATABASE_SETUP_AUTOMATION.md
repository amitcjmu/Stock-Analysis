# Database Setup Automation

This document describes the automated database setup system that ensures consistent platform initialization across database changes.

## What We've Built

### 1. **Core Database Initialization Module**
**File**: `/backend/app/core/database_initialization.py`

This module ensures:
- Platform admin account always exists (chocka@gmail.com / Password123!)
- All users have UserProfile records with status='active' (required for login)
- Demo data uses recognizable UUID pattern (XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX)
- No demo client admin accounts exist

**Key Features**:
- Idempotent - can be run multiple times safely
- Automatically runs on application startup
- Can be run manually via CLI

### 2. **Migration Hooks**
**File**: `/backend/app/core/migration_hooks.py`

Provides hooks for Alembic migrations:
- `ensure_platform_admin_sync()` - Creates/updates platform admin
- `ensure_user_profiles_sync()` - Creates missing user profiles
- `cleanup_invalid_demo_admins_sync()` - Removes demo client admins
- `run_all_hooks()` - Runs all hooks in correct order

**Usage in migrations**:
```python
from app.core.migration_hooks import MigrationHooks

def upgrade():
    # Schema changes
    MigrationHooks.run_all_hooks(op)
```

### 3. **Seed Data Configuration**
**File**: `/backend/app/core/seed_data_config.py`

Centralized configuration for all demo/test data:
- Platform admin configuration (immutable)
- Demo UUID generation functions
- Demo client/engagement/user configurations
- Validation to prevent demo admin creation

### 4. **Manual Execution Required**
**Important**: Database initialization is NOT automatic. It must be run manually.

**When to run**:
- Initial database setup
- After major schema changes
- When users report login issues
- To reset demo data

## Benefits

1. **Consistent Setup**: Single command initializes everything correctly
2. **Consistent Across Environments**: Same setup in dev, staging, production
3. **Survives Database Changes**: Migration hooks ensure consistency
4. **Self-Documenting**: Code is the documentation
5. **Error Resistant**: Handles missing profiles, wrong passwords, etc.
6. **Explicit Control**: Run only when needed, not on every startup

## How It Works

### When Run Manually:
1. Checks if platform admin exists
2. Creates/updates platform admin if needed
3. Ensures platform admin has active profile
4. Creates demo data if missing
5. Ensures all users have profiles
6. Cleans up invalid data

### During Migrations:
1. Schema changes are applied
2. Migration hooks run automatically
3. Data consistency is maintained

### Manual Execution:
```bash
docker exec migration_backend python -m app.core.database_initialization
```

## Key Requirements Enforced

1. **UserProfile Requirement**:
   - ALL users must have UserProfile with status='active' to login
   - Automatically created for any user missing a profile

2. **Platform Admin**:
   - Email: chocka@gmail.com
   - Password: Password123!
   - Always exists, always accessible

3. **Demo Data**:
   - Uses pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX (DEFault/DEmo)
   - No demo client admins
   - Tied to proper client/engagement context

4. **Password Hashing**:
   - Uses SHA256 (for demo purposes)
   - Consistent across all scripts

## Files Archived

The following outdated documentation was moved to `/docs/archive/`:
- `DEMO_DATA_SETUP.md` - Old demo corporation approach
- `DATABASE_RESET_AND_SEEDING_PLAN.md` - Old seeding strategy
- `DEMO_DATA_REFERENCE.md` - Old UUID patterns
- `db_seeding_audit_report.md` - Outdated seeding report

## Future Database Changes

When making database changes:

1. **Update Schema**: Make your Alembic migration
2. **Add Hooks**: Use MigrationHooks in your migration
3. **Update Config**: Modify seed_data_config.py if needed
4. **Test**: Run database_initialization manually
5. **Deploy**: Startup will handle the rest

The system is designed to be self-healing and maintain consistency automatically.