# Database & Alembic Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 16 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **3-Digit Naming**: `092_description.py` not hash-based names
> 2. **Idempotent Migrations**: Use `DO $$ IF NOT EXISTS` blocks
> 3. **Schema Prefix**: Always use `migration.table_name`
> 4. **Dynamic PK Detection**: Tables may use `id` or `flow_id` as PK
> 5. **Table Existence Check**: Verify table exists before ALTER

---

## Table of Contents

1. [Migration Naming Convention](#migration-naming-convention)
2. [Idempotent Migrations](#idempotent-migrations)
3. [Robustness Patterns](#robustness-patterns)
4. [Common Patterns](#common-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)

---

## Migration Naming Convention

### 3-Digit Prefix Required

```bash
# Find next number
ls -1 backend/alembic/versions/ | grep "^[0-9]" | tail -1

# Create migration
docker exec migration_backend alembic revision -m "add_column_to_table"
# Then rename to 3-digit prefix
```

**File naming**: `092_add_column_to_table.py`
**Revision chain**: `down_revision = "091_previous_migration"`

---

## Idempotent Migrations

### Column Addition Pattern

```python
def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='my_table'
                AND column_name='new_column'
            ) THEN
                ALTER TABLE migration.my_table
                ADD COLUMN new_column JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='my_table'
                AND column_name='new_column'
            ) THEN
                ALTER TABLE migration.my_table
                DROP COLUMN new_column;
            END IF;
        END $$;
    """)
```

### Enum Creation Pattern

```python
# Idempotent enum creation
op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'my_enum') THEN
            CREATE TYPE migration.my_enum AS ENUM ('value1', 'value2');
        END IF;
    END $$;
""")
```

---

## Robustness Patterns

### Dynamic Primary Key Detection

Tables may use `id` or `flow_id` as PK:

```python
def _detect_flow_id_column(bind, schema: str, table: str) -> str:
    result = bind.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        AND column_name IN ('flow_id', 'id')
    """), {"schema": schema, "table": table}).fetchall()

    found = [r[0] for r in result]
    if "flow_id" in found:
        return "flow_id"
    return "id"
```

### Table Existence Check

```python
def upgrade() -> None:
    bind = op.get_bind()

    tables = bind.execute(text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'migration'
        AND table_name = 'my_table'
    """)).fetchall()

    if not tables:
        logger.warning("Table not found, skipping")
        return

    # Proceed with migration
```

### Graceful Error Handling

```python
try:
    result = bind.execute(text(migration_sql))
    logger.info(f"Updated {result.rowcount} records")
except Exception as e:
    logger.warning(f"Failed: {e}")
    # Continue - don't fail entire migration
```

---

## Common Patterns

### JSONB Default Values

```python
sa.Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
```

### UUID Columns

```python
from sqlalchemy.dialects.postgresql import UUID
sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
```

### Foreign Key with Cascade

```python
sa.Column("flow_id", UUID(as_uuid=True), sa.ForeignKey("migration.flows.id", ondelete="CASCADE"))
```

### Check Constraint (NOT Enum)

```python
sa.Column("status", sa.String(50), nullable=False)
op.execute("""
    ALTER TABLE migration.my_table
    ADD CONSTRAINT status_check CHECK (status IN ('pending', 'running', 'completed'))
""")
```

---

## Anti-Patterns

### Don't: Use Hash-Based Names

```python
# ❌ BAD
revision = "228e0eae6242"

# ✅ GOOD
revision = "092_add_new_column"
```

### Don't: Skip Existence Checks

```python
# ❌ BAD - Fails on re-run
op.add_column('my_table', sa.Column('col', sa.String()))

# ✅ GOOD - Idempotent
op.execute("DO $$ IF NOT EXISTS... END $$")
```

### Don't: Use `public` Schema

```python
# ❌ BAD
op.create_table('my_table', ...)

# ✅ GOOD
op.create_table('my_table', ..., schema='migration')
```

---

## Code Templates

### Template 1: Complete Migration

```python
"""add_new_feature_columns

Revision ID: 093_add_new_feature_columns
Revises: 092_previous
Create Date: 2025-11-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "093_add_new_feature_columns"
down_revision = "092_previous"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='my_table'
                AND column_name='new_column'
            ) THEN
                ALTER TABLE migration.my_table
                ADD COLUMN new_column JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='my_table'
                AND column_name='new_column'
            ) THEN
                ALTER TABLE migration.my_table
                DROP COLUMN new_column;
            END IF;
        END $$;
    """)
```

### Verification Commands

```bash
# Run migrations
docker exec migration_backend alembic upgrade head

# Check current revision
docker exec migration_backend alembic current

# Test idempotency
docker exec migration_backend alembic upgrade head
docker exec migration_backend alembic downgrade -1
docker exec migration_backend alembic upgrade head
```

---

## Consolidated Sources

| Original Memory | Key Contribution |
|-----------------|------------------|
| `alembic-idempotent-migrations-pattern` | Idempotent patterns |
| `database_migration_robustness_patterns` | Dynamic PK detection |
| `alembic_migration_gotchas` | Common gotchas |
| `alembic-jsonb-migration-patterns` | JSONB patterns |
| `database_migration_enum_patterns` | Enum handling |
| `database_architecture_decisions` | Architecture |

**Archive Location**: `.serena/archive/database/`

---

## Search Keywords

alembic, migration, database, idempotent, schema, postgresql, jsonb, enum
