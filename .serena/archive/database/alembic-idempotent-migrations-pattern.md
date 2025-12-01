# Alembic Idempotent Migrations with 3-Digit Naming

**Problem**: Auto-generated Alembic migrations use hash-based names (e.g., `228e0eae6242_*.py`) and aren't idempotent, causing failures on re-runs.

**Solution**: Manual migrations with 3-digit numeric prefix + PostgreSQL DO blocks with IF EXISTS checks.

## Naming Convention

```bash
# Find next migration number
ls -1 backend/alembic/versions/ | grep "^[0-9]" | tail -1
# If latest is 091_*.py, create 092_*.py

# Create empty migration
docker exec migration_backend alembic revision -m "add_columns_to_table"
```

## Idempotent Pattern

```python
"""add_supported_versions_requirement_details

Add columns to engagement_architecture_standards table.

Revision ID: 092_add_supported_versions_requirement_details
Revises: 091_add_phase_deprecation_comments_adr027
Create Date: 2025-10-15 01:18:03.651744
"""
from alembic import op
import sqlalchemy as sa

revision = "092_add_supported_versions_requirement_details"
down_revision = "091_add_phase_deprecation_comments_adr027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """IDEMPOTENT: Uses IF NOT EXISTS checks"""
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='engagement_architecture_standards'
                AND column_name='supported_versions'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                ADD COLUMN supported_versions JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """IDEMPOTENT: Uses IF EXISTS checks"""
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='engagement_architecture_standards'
                AND column_name='supported_versions'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                DROP COLUMN supported_versions;
            END IF;
        END $$;
    """)
```

## Key Requirements

1. **3-digit prefix**: `092_description.py` (NOT `228e0eae6242_description.py`)
2. **Revision chain**: `down_revision = "091_previous_migration"`
3. **Schema prefix**: Always use `migration.table_name`
4. **Test idempotency**: Run `upgrade head` → `downgrade -1` → `upgrade head`

## Why This Matters

- Prevents "Can't locate revision" errors
- Safe to run multiple times in CI/CD
- Easy to find and sequence migrations
- Production-ready deployment pattern

**Reference**: `backend/alembic/versions/092_add_supported_versions_requirement_details.py`
**CLAUDE.md**: Lines 522-531 (brief version)
