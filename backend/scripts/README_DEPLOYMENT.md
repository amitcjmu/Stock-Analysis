# Deployment Demo Data Seeding

This directory contains scripts to seed demo data after deploying to Railway/Vercel.

## Scripts

### 1. `seed_minimal_demo.py` (Recommended)
Minimal demo data seeding - creates just the essential demo accounts and data.

**Features:**
- 3 demo client accounts
- 3 demo users with different roles
- 2 discovery flows
- No external dependencies

**Usage:**
```bash
python scripts/seed_minimal_demo.py
```

### 2. `seed_demo_data.py` 
Complete demo data seeding - creates full demo dataset including assets, dependencies, etc.

**Features:**
- Multiple client accounts
- Complete discovery flows
- Assets and dependencies
- Field mappings
- Migration waves

**Usage:**
```bash
python scripts/seed_demo_data.py
```

## Demo Account Identification

All demo accounts are clearly identifiable:

1. **UUID Pattern**: `XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX`
   - Example: `11111111-def0-def0-def0-111111110000`
   - The "def0" segments make them visually distinct (DEFault/DEmo)

2. **Email Pattern**: `user@demo.company.com`
   - Example: `admin@demo.techcorp.com`
   - All demo emails contain "demo" in the domain

3. **Name Prefix**: All entities have "Demo" prefix
   - Example: "Demo TechCorp Industries"
   - Example: "Demo Cloud Migration 2024"

4. **Default Password**: `Demo123!` for all demo users

## Railway Deployment Steps

1. **Deploy the application** to Railway

2. **Run migrations** (if not auto-run):
   ```bash
   railway run alembic upgrade head
   ```

3. **Seed demo data**:
   ```bash
   # For minimal demo data (recommended)
   railway run python scripts/seed_minimal_demo.py
   
   # OR for complete demo data
   railway run python scripts/seed_demo_data.py
   ```

4. **Verify deployment**:
   - Login with `demo@demo.democorp.com` / `Demo123!`
   - Check that demo data is visible
   - All demo entities should have clear "Demo" labels

## Demo Users Created

### Minimal Seeding:
- `demo@demo.democorp.com` (engagement_manager)
- `analyst@demo.democorp.com` (analyst)
- `admin@demo.techcorp.com` (client_admin)

### Complete Seeding:
All of the above plus:
- `viewer@demo.democorp.com` (viewer)
- `admin@demo.retailplus.com` (client_admin)
- `manager@demo.manufacturing.com` (engagement_manager)
- Additional role-specific users

## Troubleshooting

### "Demo data already exists"
The scripts check for existing demo data. To re-seed:
1. Clear the database or delete demo records manually
2. Run the seeding script again

### Import errors
If you get import errors with `seed_demo_data.py`, use `seed_minimal_demo.py` instead.
The minimal script has no dependencies on other seeding modules.

### Database connection errors
Ensure your `DATABASE_URL` environment variable is set correctly in Railway.

## Security Notes

- Demo accounts are clearly marked and use simple passwords
- Never use these scripts on a production database with real data
- Consider removing demo data after testing is complete
- All demo UUIDs follow a recognizable pattern for easy identification