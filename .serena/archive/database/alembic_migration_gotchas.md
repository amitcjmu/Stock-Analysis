# Alembic Migration Gotchas and Solutions

## Migration Name Length Limit
**Problem**: Alembic stores migration names in `alembic_version.version_num VARCHAR(50)`
```
value too long for type character varying(50)
```

**Solution**:
1. Keep migration names under 50 characters
2. Create migration to increase column size:
```python
# Migration 056_fix_alembic_version_column_size.py
op.alter_column(
    "alembic_version",
    "version_num",
    type_=sa.String(100),
    existing_type=sa.String(50),
    schema="migration"
)
```

## Migration Numbering
- Can have intentional gaps (e.g., 057-059 skipped)
- Use sequential numbers with descriptive names
- Format: `XXX_description.py` (e.g., `063_fix_enum_case.py`)

## Migration Chain Dependencies
- Always check `down_revision` references
- Verify with: `alembic current`
- Fix broken chains by updating `down_revision` in migration files

## Common Fixes Applied
1. Migration 055: Renamed from 56 chars to 25 chars
2. Migration 056: Increased alembic_version column to VARCHAR(100)
3. Migration 063: Fixed enum case sensitivity (UPPERCASE required)
