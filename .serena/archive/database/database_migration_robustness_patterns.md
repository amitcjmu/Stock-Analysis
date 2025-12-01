# Database Migration Robustness Patterns

## Dynamic Primary Key Detection Pattern
**Use Case**: Alembic migrations failing on mixed database schemas where tables use different PK column names ('id' vs 'flow_id')

### Core Detection Function
```python
def _detect_flow_id_column(bind, table_schema: str, table_name: str) -> str:
    """Detect whether a table uses flow_id or id as the primary key column."""
    col_check = bind.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            AND column_name IN ('flow_id', 'id')
        """),
        {"schema": table_schema, "table": table_name},
    ).fetchall()

    found = [r[0] for r in col_check]
    if "flow_id" in found:
        return "flow_id"
    if "id" in found:
        return "id"
    return "id"  # fallback
```

### Dynamic Query Builder Pattern
```python
def _select_orphaned_flows_query(schema: str, table_name: str, pk_col: str) -> str:
    """Build SELECT query that aliases the chosen PK as flow_id."""
    return f"""
        SELECT DISTINCT f.{pk_col} AS flow_id, f.client_account_id, f.engagement_id, f.created_at
        FROM {schema}.{table_name} f
        LEFT JOIN {schema}.crewai_flow_state_extensions cfse ON f.{pk_col} = cfse.flow_id
        WHERE f.master_flow_id IS NULL
        AND cfse.flow_id IS NULL
    """

def _update_master_flow_query(schema: str, table_name: str, pk_col: str) -> str:
    """Build UPDATE query that sets master_flow_id correctly."""
    return f"""
        UPDATE {schema}.{table_name}
        SET master_flow_id = {pk_col}, updated_at = NOW()
        WHERE master_flow_id IS NULL
    """
```

### Migration Implementation Pattern
```python
def upgrade() -> None:
    bind = op.get_bind()

    # Check table existence first
    tables_exist = bind.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'migration'
        AND table_name IN ('discovery_flows', 'assessment_flows', 'collection_flows')
    """)).fetchall()

    existing_tables = [row[0] for row in tables_exist]

    for table_name, flow_type in [
        ("discovery_flows", "discovery"),
        ("assessment_flows", "assessment"),
        ("collection_flows", "collection"),
    ]:
        if table_name in existing_tables:
            # Detect correct PK column for this table
            pk_col = _detect_flow_id_column(bind, "migration", table_name)
            logger.info(f"Using {pk_col} as primary key column for {table_name}")

            # Use dynamic queries
            orphaned_query_sql = _select_orphaned_flows_query("migration", table_name, pk_col)
            orphaned_flows = bind.execute(text(orphaned_query_sql)).fetchall()

            # Process orphaned flows...

            # Update with correct column
            update_sql = _update_master_flow_query("migration", table_name, pk_col)
            result = bind.execute(text(update_sql))
```

## Table Existence Validation Pattern
```python
# Always check table existence before migration operations
tables_exist = bind.execute(text("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = :schema
    AND table_name = ANY(:table_names)
"""), {
    "schema": "migration",
    "table_names": ["discovery_flows", "collection_flows", "assessment_flows"]
}).fetchall()

existing_tables = [row[0] for row in tables_exist]
if "discovery_flows" not in existing_tables:
    logger.warning("discovery_flows table not found, skipping migration")
    return
```

## Graceful Error Handling Pattern
```python
try:
    # Migration operation
    result = bind.execute(text(migration_sql))
    updated_count = result.rowcount if result else 0
    logger.info(f"Updated {updated_count} records")
except Exception as e:
    logger.warning(f"Failed to update {table_name}: {e}")
    # Continue with other operations - don't fail entire migration
```

## Downgrade Robustness Pattern
```python
def downgrade() -> None:
    bind = op.get_bind()

    # Use same dynamic detection in downgrade
    for table_name in ["discovery_flows", "assessment_flows", "collection_flows"]:
        try:
            pk_col = _detect_flow_id_column(bind, "migration", table_name)
            result = bind.execute(text(f"""
                UPDATE migration.{table_name}
                SET master_flow_id = NULL
                WHERE master_flow_id = {pk_col}
            """))
            reset_count = result.rowcount if result else 0
            print(f"Reset {reset_count} {table_name} records (using {pk_col})")
        except Exception as e:
            print(f"Could not reset {table_name}: {e}")
```

## Benefits
- **Schema Agnostic**: Works with tables using either 'id' or 'flow_id' as PK
- **Graceful Degradation**: Continues migration even if some tables fail
- **Logging**: Comprehensive logging for debugging
- **Reversible**: Downgrade operations use same detection logic
- **Production Safe**: Table existence checks prevent errors on partial schemas

## Files Using This Pattern
- `backend/alembic/versions/061_fix_null_master_flow_ids.py`
