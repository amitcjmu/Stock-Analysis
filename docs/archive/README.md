# Archived Documentation

This folder contains outdated documentation that has been superseded by newer approaches.

## Archived Files

### Demo Data Documentation (Outdated)
- `DEMO_DATA_SETUP.md` - Old demo corporation setup (replaced by platform admin setup)
- `DATABASE_RESET_AND_SEEDING_PLAN.md` - Old seeding approach with demo users
- `DEMO_DATA_REFERENCE.md` - Old UUID patterns and demo user references
- `db_seeding_audit_report.md` - Outdated seeding coverage report

## Why These Were Archived

These documents were archived because they:
1. Referenced old demo user structure (demo@democorp.com) instead of platform admin (chocka@gmail.com)
2. Used old UUID patterns (11111111-1111-1111-1111-111111111111) instead of new pattern (XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX)
3. Included demo client admin accounts which are no longer needed
4. Focused on demo corporation setup instead of platform admin initialization

## Current Approach

For current database setup and initialization, see:
- `/docs/PLATFORM_ADMIN_SETUP.md` - Platform admin and database initialization
- `/backend/app/core/database_initialization.py` - Automated initialization module
- `/backend/app/core/seed_data_config.py` - Centralized seed data configuration
