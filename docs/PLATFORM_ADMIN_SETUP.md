# Platform Admin Setup Guide

This document describes the platform admin setup and database initialization process for the AI Force Migration Platform.

## Overview

The platform uses a specific initialization process that ensures:
1. Platform admin account exists: `chocka@gmail.com` / `Password123!`
2. All users have UserProfile records with `status='active'` (required for login)
3. Demo data uses recognizable UUID pattern: `XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX` (DEFault/DEmo)
4. NO demo client admin accounts (only platform admin can create client admins)

**Note**: Database initialization is NOT automatic. It must be run manually when needed.

## Automated Database Initialization

### Core Module: `app/core/database_initialization.py`

This module provides automated initialization that:
- Creates platform admin if not exists
- Ensures all users have active profiles
- Creates minimal demo data with proper UUIDs
- Validates no demo client admins exist

### Usage

```python
from app.core.database import AsyncSessionLocal
from app.core.database_initialization import initialize_database

async with AsyncSessionLocal() as db:
    await initialize_database(db)
```

### Running via CLI

```bash
docker exec migration_backend python -m app.core.database_initialization
```

## Migration Hooks

### Module: `app/core/migration_hooks.py`

Provides hooks for Alembic migrations to ensure data consistency:

```python
from app.core.migration_hooks import MigrationHooks

def upgrade():
    # Your schema changes
    
    # Run all hooks to ensure consistency
    MigrationHooks.run_all_hooks(op)
```

### Available Hooks

1. `ensure_platform_admin_sync(op)` - Creates/updates platform admin
2. `ensure_user_profiles_sync(op)` - Creates missing user profiles
3. `cleanup_invalid_demo_admins_sync(op)` - Removes demo client admins
4. `run_all_hooks(op)` - Runs all hooks in correct order

## Seed Data Configuration

### Module: `app/core/seed_data_config.py`

Centralized configuration for all demo and test data:

```python
from app.core.seed_data_config import (
    PlatformAdminConfig,
    DemoClientConfig,
    DemoUserConfig,
    SeedDataManager
)

# Get platform admin data
admin_data = SeedDataManager.get_platform_admin_data()

# Get demo client data
client_data = SeedDataManager.get_demo_client_data()
```

### Key Configurations

#### Platform Admin (NEVER CHANGE)
- Email: `chocka@gmail.com`
- Password: `Password123!`
- Name: Platform Admin
- Role: Platform Administrator

#### Demo UUID Pattern
- Format: `XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX`
- Example: `84952e4d-def0-def0-def0-d365247ebb66`
- Meaning: "def0" = DEFault/DEmo (uses only valid hex characters)

#### Demo Users
1. `manager@demo-corp.com` - Engagement Manager
2. `analyst@demo-corp.com` - Analyst  
3. `viewer@demo-corp.com` - Viewer

**NO CLIENT ADMIN DEMO ACCOUNTS!**

## Manual Setup Scripts

Located in `/backend/scripts/`:

1. `clean_all_demo_data_fixed.py` - Removes all demo data
2. `setup_platform_admin.py` - Creates platform admin and demo data
3. `verify_platform_admin.py` - Verifies platform admin login
4. `test_platform_login.py` - Tests all user logins

### Running Setup

```bash
# Clean existing demo data
docker exec migration_backend python scripts/clean_all_demo_data_fixed.py

# Setup platform admin
docker exec migration_backend python scripts/setup_platform_admin.py

# Verify setup
docker exec migration_backend python scripts/test_platform_login.py
```

## Authentication Requirements

### Critical: UserProfile Requirement

**ALL users MUST have a UserProfile record with `status='active'` to login!**

The authentication service checks:
```python
if not user_profile or user_profile.status != "active":
    raise HTTPException(status_code=401, detail="Account not approved")
```

### Password Hashing

The platform uses SHA256 for password hashing (for demo purposes):
```python
def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
```

## Database Schema Requirements

### Users Table
- Must have `password_hash` field
- Must have `is_active` and `is_verified` flags
- Can have `default_client_id` and `default_engagement_id`

### UserProfile Table
- Primary key: `user_id` (FK to users.id)
- Must have `status` field (enum: active, pending_approval, suspended, deactivated)
- Must have `approved_at` timestamp for active users

### UserRole Table
- Defines user roles and permissions
- Uses `scope_type` and scope IDs for multi-tenant access
- Platform admin has global scope

## Common Issues and Solutions

### "Account not approved" Error
**Cause**: User exists but no UserProfile or profile status != 'active'
**Solution**: Run database initialization to create missing profiles

### "Invalid salt" Error  
**Cause**: Password hash format mismatch
**Solution**: Ensure using SHA256 hashing, not bcrypt

### Foreign Key Constraint Errors
**Cause**: Trying to delete users referenced by other tables
**Solution**: Use `clean_all_demo_data_fixed.py` which handles proper deletion order

## Best Practices

1. **Always run database initialization** after schema changes
2. **Never create demo client admin accounts**
3. **Use demo UUID pattern** for all test data
4. **Ensure all users have profiles** before allowing login
5. **Platform admin is special** - no client/engagement context needed

## Integration with CLAUDE.md

The CLAUDE.md file has been updated with:
- Database initialization requirements
- Platform admin credentials
- Demo UUID patterns
- UserProfile requirements
- Migration hook usage

This ensures AI coding assistants understand the platform requirements and maintain consistency.