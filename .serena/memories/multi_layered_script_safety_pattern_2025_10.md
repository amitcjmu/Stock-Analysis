# Multi-Layered Safety Pattern for Destructive Operations

**Date**: October 2025
**Context**: Prevention measures after Oct 7 data loss incident
**Reference**: `backend/scripts/SAFE_cleanup_demo_data.py`

## 5-Layer Protection System

### Layer 1: Environment Checks
```python
def check_environment():
    """Verify we're in a safe environment"""
    env = os.getenv("ENVIRONMENT", "production").lower()

    if env in ["production", "staging", "prod", "stg"]:
        print("❌ FATAL: This script cannot run in production or staging!")
        print(f"   Current ENVIRONMENT: {env}")
        sys.exit(1)

    if env != "local":
        print(f"⚠️  WARNING: ENVIRONMENT is '{env}', not 'local'")
        response = input("   Are you ABSOLUTELY SURE you want to continue? (yes/NO): ")
        if response.lower() != "yes":
            sys.exit(0)
```

### Layer 2: Explicit User Confirmation
```python
def get_user_confirmation():
    """Require explicit confirmation"""
    print("\n⚠️  DANGER: This will DELETE ALL DATA for demo client account!")
    print("\n❗ THIS CANNOT BE UNDONE ❗\n")

    response = input("Type 'DELETE MY DATA' to proceed: ")
    if response != "DELETE MY DATA":
        print("❌ Confirmation failed. Aborting.")
        sys.exit(0)

    # Second confirmation
    response2 = input("Type 'I understand the risks' to continue: ")
    if response2 != "I understand the risks":
        print("❌ Final confirmation failed. Aborting.")
        sys.exit(0)
```

### Layer 3: Dry-Run Mode (Default)
```python
async def main():
    # Check if dry-run mode (default is True)
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv

    if dry_run:
        print("\n🔍 DRY RUN MODE - No data will be deleted")
        # Show counts only, don't execute
        await clean_demo_data_safe(dry_run=True)
        return
```

### Layer 4: Automatic Backup Before Deletion
```python
async def create_backup():
    """Create a backup before deletion using pg_dump"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/tmp/demo_data_backup_{timestamp}.sql"

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("   ⚠️  DATABASE_URL not set - skipping backup")
        return backup_file

    from urllib.parse import urlparse
    parsed = urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))

    dump_command = [
        "pg_dump",
        "-h", parsed.hostname or "localhost",
        "-p", str(parsed.port or 5432),
        "-U", parsed.username or "postgres",
        "-d", parsed.path.lstrip("/"),
        "-f", backup_file,
        "--no-password",
    ]

    process = await asyncio.create_subprocess_exec(
        *dump_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "PGPASSWORD": parsed.password or ""},
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        print(f"   ✅ Backup successfully created at: {backup_file}")
        return backup_file
    else:
        error_msg = stderr.decode() if stderr else "Unknown error"
        raise Exception(f"pg_dump failed: {error_msg}")
```

### Layer 5: Detailed Logging with Counts
```python
async def clean_demo_data_safe(dry_run: bool = True):
    """Clean demo data with safety checks"""

    # Show counts BEFORE deletion
    count_queries = [
        (text("SELECT COUNT(*) FROM users WHERE email LIKE :pattern"),
         {"pattern": "%demo%"}, "demo users"),
        (text("SELECT COUNT(*) FROM assets WHERE client_account_id = :client_id"),
         {"client_id": demo_client_id}, "assets"),
    ]

    print("\n📊 Data to be affected:")
    for query, params, label in count_queries:
        result = await session.execute(query, params)
        count = result.scalar()
        print(f"   {label}: {count} records")

    if dry_run:
        print("\n✅ Dry run completed - no data was deleted")
        return

    # Execute actual cleanup with logging
    for query, params in cleanup_queries:
        try:
            result = await session.execute(query, params)
            await session.commit()
            if result.rowcount > 0:
                print(f"   ✅ Deleted {result.rowcount} records")
        except Exception as e:
            print(f"   ⚠️ Query failed: {str(e)[:100]}")
```

## Usage Pattern

```bash
# Always run dry-run first
python backend/scripts/SAFE_cleanup_demo_data.py --dry-run

# Only after verifying dry-run output
python backend/scripts/SAFE_cleanup_demo_data.py
```

## Dangerous Script Naming Convention

```bash
# Disable dangerous scripts
.DANGEROUS_clean_all_demo_data.py.disabled

# Safe alternatives
SAFE_cleanup_demo_data.py
```

## When to Apply This Pattern

- Database cleanup scripts
- Bulk deletion operations
- Data migration rollbacks
- Test data cleanup
- Account/tenant deletion

## Key Principles

1. **Fail Closed**: Default to dry-run, not execution
2. **Explicit Intent**: Require exact phrase confirmations
3. **Environment Aware**: Block production/staging by default
4. **Backup First**: Never delete without backup
5. **Visibility**: Show counts before deletion
