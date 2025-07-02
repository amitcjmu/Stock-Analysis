# Auto-Seeding Demo Data

The platform now includes automatic demo data seeding that runs during database initialization.

## When It Runs

Auto-seeding runs automatically when:
- Running `python -m app.core.database_initialization`
- The database has no demo assets
- After fresh database setup or migrations

## What It Creates

The auto-seeder creates comprehensive demo data:

- **20 Servers** (Windows and Linux)
- **5 Applications** (CRM, HR Portal, Finance, etc.)
- **4 Databases** (PostgreSQL and MySQL)
- **9 Asset Dependencies** (apps → servers, apps → databases)
- **2 Discovery Flows** (complete and in-progress)
- **2 Data Imports** (CSV and Excel)
- **2 Migration Waves** (planned)

## Multi-Tenancy

All demo data is properly tied to:
- Demo Client ID: `11111111-1111-1111-1111-111111111111`
- Demo Engagement ID: `22222222-2222-2222-2222-222222222222`
- Demo User ID: `33333333-3333-3333-3333-333333333333`

## Usage

The auto-seeding is integrated into database initialization:

```bash
# Run database initialization (includes auto-seeding)
docker exec migration_backend python -m app.core.database_initialization
```

## Implementation

- Location: `/backend/app/core/auto_seed_demo_data.py`
- Called from: `DatabaseInitializer.auto_seed_demo_data()` in `database_initialization.py`
- Idempotent: Won't create duplicate data if run multiple times