# Database & Alembic Patterns Master

**Last Updated**: 2025-12-05
**Version**: 1.1
**Consolidates**: 16 memories + session learnings
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **3-Digit Naming**: `092_description.py` not hash-based names
> 2. **Idempotent Migrations**: Use `DO $$ IF NOT EXISTS` blocks
> 3. **Schema Prefix**: Always use `migration.table_name`
> 4. **Dynamic PK Detection**: Tables may use `id` or `flow_id` as PK
> 5. **CHECK Constraint Idempotency**: Use separate `pg_constraint` lookup

---

## Table of Contents

1. [Migration Naming Convention](#migration-naming-convention)
2. [Idempotent Migrations](#idempotent-migrations)
3. [CHECK Constraint Idempotency](#check-constraint-idempotency)
4. [Migration Chain Management](#migration-chain-management)
5. [pgvector Optimization](#pgvector-optimization)
6. [GIN Index Decision Pattern](#gin-index-decision-pattern)
7. [Robustness Patterns](#robustness-patterns)
8. [Common Patterns](#common-patterns)
9. [Anti-Patterns](#anti-patterns)
10. [Code Templates](#code-templates)

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

## CHECK Constraint Idempotency (Added 2025-12-05)

**Problem**: CHECK constraints inside column existence blocks get skipped if column exists but constraint doesn't.

**Solution**: Use separate `pg_constraint` lookup for constraint creation:

```python
def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- 1. Column creation (guarded by column existence)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'my_table'
                  AND column_name = 'status'
            ) THEN
                ALTER TABLE migration.my_table
                ADD COLUMN status VARCHAR(50);

                COMMENT ON COLUMN migration.my_table.status IS
                    'Status: pending, active, completed';
            END IF;

            -- 2. Index creation (always idempotent via IF NOT EXISTS)
            CREATE INDEX IF NOT EXISTS ix_my_table_status
            ON migration.my_table(status);

            -- 3. Constraint creation (guarded SEPARATELY by pg_constraint)
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_my_table_status'
            ) THEN
                ALTER TABLE migration.my_table
                ADD CONSTRAINT chk_my_table_status
                CHECK (status IN ('pending', 'active', 'completed') OR status IS NULL);
            END IF;
        END $$;
    """)
```

**Why**: If migration partially fails after column creation but before constraint, re-running would skip the whole block. Separate lookup ensures constraint is created on retry.

---

## Migration Chain Management (Added 2025-12-05)

**Problem**: When PR A (with migration 147) is merged after PR B (which added 147, 148), chain breaks.

**Solution**: Renumber migration and update references:

```bash
# 1. Checkout the PR branch
gh pr checkout 1241

# 2. Rename file
git mv alembic/versions/147_add_fields.py alembic/versions/149_add_fields.py

# 3. Update revision identifiers in file
# revision = "149_add_fields"
# down_revision = "148_previous_from_other_pr"

# 4. Update docstring
# Revision ID: 149_add_fields
# Revises: 148_previous_from_other_pr

# 5. Commit and push
git add -A && git commit -m "fix(alembic): renumber migration 147→149"
git push
```

**Verification**:
```bash
# Check chain is valid
grep -E "^(revision|down_revision)" alembic/versions/14[7-9]*.py
```

---

## pgvector Optimization (Added 2025-12-05)

### IVFFlat Index Tuning

**Problem**: Default `lists=100` is overkill for small datasets, hurting recall.

**Solution**: Set `lists` to ~sqrt(row_count):

```python
# For ~45 vectors: sqrt(45) ≈ 7, round up to 20 for growth
op.execute("""
    CREATE INDEX ix_patterns_embedding
    ON migration.agent_discovered_patterns
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 20);
""")
```

### Partial Index for Tenant-Scoped Queries

```python
# Add partial index for faster tenant-filtered vector queries
op.execute("""
    CREATE INDEX IF NOT EXISTS ix_patterns_tenant_vector
    ON migration.agent_discovered_patterns (client_account_id)
    WHERE embedding IS NOT NULL;
""")
```

### Embedding Normalization for Cosine Similarity

**Problem**: Cosine similarity thresholds only work correctly with unit-length vectors.

**Solution**: Normalize before similarity search:

```python
import math

# Normalize query embedding to unit length
norm = math.sqrt(sum(x * x for x in query_embedding))
if norm == 0:
    raise ValueError("Query embedding norm is zero; cannot normalize")
normalized_embedding = [x / norm for x in query_embedding]

# Use pgvector's native method (secure, no SQL injection)
distance_expr = cls.embedding.cosine_distance(normalized_embedding)
```

---

## GIN Index Decision Pattern (Added 2025-12-05)

**Problem**: GIN indexes on JSONB columns are expensive for write-heavy tables.

**Decision Process**:

1. Search codebase for JSONB column usage:
```bash
grep -r "WHERE.*custom_attributes" --include="*.py" | grep -v test
```

2. Check for index-benefiting patterns:
   - `WHERE custom_attributes @> '{"key": "value"}'`
   - `WHERE custom_attributes ? 'key'`
   - `WHERE custom_attributes ->> 'key' = 'value'`

3. **If NO WHERE clause filters on JSONB columns**: Skip GIN index
4. **If frequent reads with JSONB filters**: Add GIN index

**Example Decision** (from PR #1252):
- Analyzed: Zero WHERE clause filters on JSONB `custom_attributes`
- Result: Removed GIN index migration (would add write overhead with zero benefit)

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

## PostgreSQL Enum Case Sensitivity (Added 2025-12)

### Problem: Invalid Enum Value Error

**Symptom**:
```
invalid input value for enum patterntype: 'FIELD_MAPPING_APPROVAL'
```

**Root Cause**: PostgreSQL enum created with lowercase values, but SQLAlchemy converts string values to UPPERCASE enum names automatically.

**Solution**: Recreate PostgreSQL enum with UPPERCASE values:

```sql
DROP TYPE IF EXISTS migration.patterntype CASCADE;

CREATE TYPE migration.patterntype AS ENUM (
    'FIELD_MAPPING_APPROVAL',
    'FIELD_MAPPING_REJECTION',
    'TECHNOLOGY_CORRELATION',
    'WAVE_PLANNING_OPTIMIZATION'
    -- ... all values UPPERCASE
);

ALTER TABLE migration.agent_discovered_patterns
ALTER COLUMN pattern_type TYPE migration.patterntype
USING pattern_type::text::migration.patterntype;
```

**Key Insight**: Instead of fighting SQLAlchemy's enum handling, work with its expectations. SQLAlchemy converts to uppercase, so PostgreSQL enum must use uppercase.

**Affected Files**:
- `backend/app/models/agent_discovered_patterns.py`
- `backend/app/models/agent_memory.py`
- `backend/app/services/enrichment/constants.py`

---

## Soft-Delete Query Consistency (CRITICAL - Added 2025-12)

### The Golden Rule

**ALL asset listing queries MUST include `deleted_at IS NULL`**

### Problem Pattern

When implementing soft-delete, the update service correctly filters deleted assets, but listing queries did NOT include the filter:

1. Deleted assets appear in AG Grid
2. User attempts to edit
3. Update service correctly rejects with 404
4. User sees "Asset not found" for visible asset

### Required Filter

```python
# CORRECT - excludes soft-deleted
select(Asset).where(
    Asset.client_account_id == context.client_account_id,
    Asset.engagement_id == context.engagement_id,
    Asset.deleted_at.is_(None),  # Don't forget!
)

# WRONG - will show deleted assets
select(Asset).where(
    Asset.client_account_id == context.client_account_id,
    Asset.engagement_id == context.engagement_id,
    # Missing deleted_at filter!
)
```

### Files That Need the Filter

| File | Status |
|------|--------|
| `asset_list_handler.py` → `list_assets()` | Required |
| `asset_list_handler.py` → `get_asset_summary()` | Required |
| `pagination.py` → `_get_assets_from_db()` | Required |
| `asset_repository.py` → `get_all()` | Via `include_deleted` param |

### Exception: Trash View

Only trash view should show deleted assets:
```python
Asset.deleted_at.is_not(None)  # Only deleted assets
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

### Don't: Put CHECK Constraints Inside Column Check

```python
# ❌ BAD - Constraint skipped if column exists
IF NOT EXISTS (column check) THEN
    ADD COLUMN...
    ADD CONSTRAINT...  -- Skipped on retry!
END IF;

# ✅ GOOD - Separate checks
IF NOT EXISTS (column check) THEN ADD COLUMN... END IF;
IF NOT EXISTS (constraint check) THEN ADD CONSTRAINT... END IF;
```

### Don't: Add GIN Indexes Without JSONB Filters

```python
# ❌ BAD - No WHERE clause uses this
CREATE INDEX idx_gin ON table USING GIN (jsonb_column);

# ✅ GOOD - Only add if queries filter on JSONB
# First verify: grep -r "WHERE.*jsonb_column" --include="*.py"
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

### Template 2: Column with CHECK Constraint (Fully Idempotent)

```python
def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- Column creation
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'my_table'
                  AND column_name = 'priority'
            ) THEN
                ALTER TABLE migration.my_table
                ADD COLUMN priority VARCHAR(20);
                COMMENT ON COLUMN migration.my_table.priority IS 'Priority level';
            END IF;

            -- Index (idempotent)
            CREATE INDEX IF NOT EXISTS ix_my_table_priority
            ON migration.my_table(priority);

            -- Constraint (separate check)
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'chk_my_table_priority'
            ) THEN
                ALTER TABLE migration.my_table
                ADD CONSTRAINT chk_my_table_priority
                CHECK (priority IN ('low', 'medium', 'high') OR priority IS NULL);
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

# Verify chain
grep -E "^(revision|down_revision)" alembic/versions/*.py | sort
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
| Session 2025-12-05 | CHECK constraint idempotency, pgvector optimization, GIN decision |
| `field_mapping_enum_uppercase_fix` | PostgreSQL enum case sensitivity |
| `soft-delete-query-consistency-critical-2025-12` | Soft-delete filter requirements |

**Archive Location**: `.serena/archive/database/`

---

## Search Keywords

alembic, migration, database, idempotent, schema, postgresql, jsonb, enum, pgvector, gin, check constraint, pg_constraint, soft_delete, deleted_at, uppercase, patterntype
