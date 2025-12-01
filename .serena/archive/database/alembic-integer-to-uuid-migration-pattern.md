# Alembic Migration Pattern: INTEGER to UUID Type Conversion with Data Transformation

## Problem
Converting database columns from INTEGER to UUID when:
1. Existing data contains INTEGER values (e.g., 1, 2, 3)
2. New system requires UUID for multi-tenant scoping
3. Data must be preserved/transformed during migration
4. Migration must be idempotent for safety

## Root Cause
Direct type conversion fails:
```sql
-- ❌ FAILS with: invalid input syntax for type uuid: "1"
ALTER TABLE migration.planning_flows
ALTER COLUMN client_account_id TYPE UUID
USING client_account_id::text::uuid;
```

PostgreSQL cannot cast INTEGER "1" to a valid UUID format.

## Solution: Temporary Column Approach with Data Transformation

### Pattern for Tables with Data (Requires Transformation)

```python
# In Alembic migration file
def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if column is still INTEGER
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
                AND column_name = 'client_account_id'
                AND data_type = 'integer'
            ) THEN
                -- Step 1: Add temporary UUID column
                ALTER TABLE migration.planning_flows
                ADD COLUMN client_account_id_uuid UUID;

                -- Step 2: Transform data (map INTEGER → UUID)
                UPDATE migration.planning_flows
                SET client_account_id_uuid = CASE
                    WHEN client_account_id = 1 THEN '11111111-1111-1111-1111-111111111111'::UUID
                    ELSE NULL
                END;

                -- Step 3: Drop old INTEGER column
                ALTER TABLE migration.planning_flows
                DROP COLUMN client_account_id;

                -- Step 4: Rename UUID column to original name
                ALTER TABLE migration.planning_flows
                RENAME COLUMN client_account_id_uuid TO client_account_id;

                RAISE NOTICE 'Converted client_account_id from INTEGER to UUID';
            ELSE
                RAISE NOTICE 'client_account_id already UUID type, skipping';
            END IF;
        END $$;
        """
    )
```

### Pattern for Empty Tables (Simple Cast)

```python
# For tables with no data, use simpler approach
def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE migration.project_timelines
        ALTER COLUMN client_account_id TYPE UUID
        USING client_account_id::text::uuid;
        """
    )
```

## SQLAlchemy Model Update

```python
# Update model to match new schema
class PlanningFlow(Base):
    __tablename__ = "planning_flows"

    # ❌ OLD
    # client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # ✅ NEW
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
```

## Downgrade Pattern

```python
def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
                AND column_name = 'client_account_id'
                AND data_type = 'uuid'
            ) THEN
                -- Reverse transformation
                ALTER TABLE migration.planning_flows
                ADD COLUMN client_account_id_int INTEGER;

                UPDATE migration.planning_flows
                SET client_account_id_int = CASE
                    WHEN client_account_id = '11111111-1111-1111-1111-111111111111'::UUID THEN 1
                    ELSE NULL
                END;

                ALTER TABLE migration.planning_flows DROP COLUMN client_account_id;
                ALTER TABLE migration.planning_flows RENAME COLUMN client_account_id_int TO client_account_id;
            END IF;
        END $$;
        """
    )
```

## Key Learnings

1. **DO Block Idempotency**: Always check column type before conversion
2. **Four-Step Process**: Add temp column → Transform data → Drop old → Rename
3. **Data Mapping**: Use CASE statement for INTEGER → UUID transformation
4. **Demo Data UUIDs**:
   - Demo client: `11111111-1111-1111-1111-111111111111`
   - Demo engagement: `22222222-2222-2222-2222-222222222222`
5. **Empty Tables**: Use simple `USING` clause when no data exists

## When to Use

- Converting tenant scoping columns to UUID for multi-tenant architecture
- Migrating from INTEGER IDs to UUID for any column with existing data
- Need to map legacy ID values to new UUID values
- Migration must be reversible and idempotent

## Reference

- File: `backend/alembic/versions/115_fix_planning_flows_tenant_columns.py`
- Error resolved: `operator does not exist: integer = character varying`
- Tables affected: planning_flows, project_timelines, timeline_phases, timeline_milestones
