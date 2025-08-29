# SQL Injection Prevention for PostgreSQL Enum Types

## Problem
When filtering by PostgreSQL enum types in SQLAlchemy, string interpolation creates SQL injection vulnerabilities.

## ❌ VULNERABLE Pattern
```python
# NEVER DO THIS - SQL Injection Risk!
query = query.where(
    text(f"pattern_type = '{pattern_type}'::patterntype")
)
```

## ✅ SECURE Pattern
Use SQLAlchemy's bindparams for safe parameter binding:

```python
from sqlalchemy import text

# Safe parameterized query with enum casting
query = query.where(
    text("pattern_type = :pattern_type::patterntype").bindparams(
        pattern_type=pattern_type
    )
)
```

## Alternative Approaches

### Direct Column Comparison (when enum is properly mapped)
```python
# If enum is properly mapped in the model
query = query.where(
    AgentDiscoveredPatterns.pattern_type == pattern_type
)
```

### Using CAST for Complex Cases
```python
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ENUM

query = query.where(
    Model.enum_column == cast(value, ENUM(name='enum_type_name'))
)
```

## Migration Safety for Enum Types

When creating enum types in migrations, always:
1. Check if enum exists before creating
2. Handle NULL and invalid values before type conversion
3. Use proper schema prefixes

```python
# Safe enum migration pattern
def upgrade():
    conn = op.get_bind()

    # Check if enum exists
    result = conn.execute(text("""
        SELECT 1 FROM pg_type
        WHERE typname = 'patterntype'
        AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
    """))

    if not result.fetchone():
        # Create enum
        op.execute("""
            CREATE TYPE migration.patterntype AS ENUM (...)
        """)

        # Coerce invalid values before altering column type
        op.execute("""
            UPDATE migration.table_name
            SET column_name = 'safe_default_value'
            WHERE column_name IS NULL
               OR column_name::text NOT IN (valid_enum_values)
        """)

        # Now safe to alter type
        op.execute("""
            ALTER TABLE migration.table_name
            ALTER COLUMN column_name TYPE migration.patterntype
            USING column_name::text::migration.patterntype
        """)
```

## Key Takeaways
- ALWAYS use parameterized queries with bindparams
- NEVER use string interpolation for SQL queries
- Handle NULL/invalid values before enum type conversion
- Use schema-qualified enum types in migrations
