# Alembic Migration Production Fixes - September 27, 2025

## Critical Fix 1: SQLAlchemy Bind.execute() for Alembic Operations
**Problem**: Migration 076 failing with "TypeError: execute() takes 2 positional arguments but 3 were given"
**Root Cause**: Direct use of `op.execute()` with parameters not supported in production Alembic
**Solution**: Use bind.execute() with proper parameter binding
```python
# WRONG - Causes TypeError in production
op.execute(text(f"UPDATE table SET field = '{value}'"))

# CORRECT - Use bind.execute with parameters
bind = op.get_bind()
bind.execute(
    text("UPDATE table SET field = :param"),
    {"param": value}
)
```
**Usage**: Always use bind.execute() for parameterized queries in Alembic migrations

## Critical Fix 2: PostgreSQL ENUM Sequencing in Migrations
**Problem**: "invalid input value for enum collectionflowstatus: 'asset_selection'"
**Solution**: Separate enum updates from data migrations
```python
# Migration 076 - Update data only (skip status column)
UPDATE migration.collection_flows
SET current_phase = 'asset_selection'
WHERE current_phase IN ('platform_detection', 'automated_collection')

# Migration 077 - Update enum AFTER it exists
ALTER TYPE collectionflowstatus ADD VALUE 'asset_selection';
UPDATE migration.collection_flows SET status = 'asset_selection'...
```

## Critical Fix 3: SQL Injection Prevention in Migrations
**Problem**: Using f-strings for SQL generation creates injection vulnerabilities
**Solution**: Always use parameter binding
```python
# VULNERABLE
text(f"UPDATE ... WHERE id = '{revision}'")

# SECURE
text("UPDATE ... WHERE id = :revision_id"),
{"revision_id": revision}
```

## Critical Fix 4: React Hook Temporal Dead Zone
**Problem**: "Cannot access 'loadUsers' before initialization"
**Solution**: Define useCallback functions before useEffect hooks that reference them
```typescript
// WRONG - useEffect references undefined callback
useEffect(() => {
  loadUsers(); // Error: loadUsers not defined yet
}, [loadUsers]);

const loadUsers = useCallback(async () => {...}, []);

// CORRECT - Define callbacks first
const loadUsers = useCallback(async () => {...}, []);

useEffect(() => {
  loadUsers(); // Works: loadUsers already defined
}, [loadUsers]);
```

## Critical Fix 5: Admin Role Restriction Pattern
**Problem**: Administrator role could be assigned with non-admin access levels
**Solution**: Conditional role options and automatic reset
```typescript
// Restrict role options based on access level
{approvalData.access_level === 'admin' && (
  <SelectItem value="Administrator">Administrator</SelectItem>
)}

// Auto-reset with functional update + notification
setApprovalData(prev => {
  if (value !== 'admin' && prev.role_name === 'Administrator') {
    toast({ title: "Role Updated", description: "Reset to Analyst" });
    return { ...prev, access_level: value, role_name: 'Analyst' };
  }
  return { ...prev, access_level: value };
});
```

## Key Patterns Learned:
1. **Always test migrations in Docker** before production deployment
2. **Use bind.execute()** for all parameterized Alembic operations
3. **Sequence enum changes** after data migrations
4. **React hook order matters** - callbacks before effects
5. **Use functional setState** to prevent stale closures
