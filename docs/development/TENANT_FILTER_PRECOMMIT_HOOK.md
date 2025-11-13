# Tenant Filter Pre-Commit Hook Documentation

## Overview

The tenant filter pre-commit hook automatically validates that all SQLAlchemy database queries include proper multi-tenant scoping filters (`client_account_id` and `engagement_id`) to prevent data leaks between tenants.

## Why This Matters

Multi-tenant data isolation is **critical for security**. Without proper filtering:
- Queries may return data from other clients/tenants
- Data leaks could expose sensitive information
- Compliance violations (GDPR, SOC2, etc.)

This hook prevents these issues from being committed to the codebase.

## How It Works

The hook uses AST (Abstract Syntax Tree) parsing to analyze Python files and detect:
1. `select()` queries on multi-tenant models
2. Missing `client_account_id` or `engagement_id` filters
3. Provides clear error messages showing which filters are missing

## Multi-Tenant Models

The following models **REQUIRE** tenant scoping:
- `CollectionFlow`
- `DiscoveryFlow`
- `AssessmentFlow`
- `Asset`
- `AssetDependency`
- `SixRAnalysis`
- `MigrationWave`
- `FieldMapping`
- `DataImport`
- `CrewAIFlowStateExtension`
- `EnhancedUserProfile`
- `TenantVendorProducts`
- `AssetProductLinks`
- `CollectionQuestionnaire`
- `CollectionQuestionnaireResponse`
- `ApplicationInfo`

## Correct Usage

### ✅ Good - Query with both filters
```python
query = select(CollectionFlow).where(
    CollectionFlow.client_account_id == context.client_account_id,
    CollectionFlow.engagement_id == context.engagement_id
)
```

### ✅ Good - Primary key only query (allowed exception)
```python
# Single-record lookup by PK doesn't need tenant scoping
query = select(CollectionFlow).where(CollectionFlow.id == record_id)
```

### ✅ Good - Using skip comment (for special cases)
```python
# Admin query that legitimately needs to see all tenants
query = select(CollectionFlow)  # SKIP_TENANT_CHECK
```

### ❌ Bad - Missing both filters
```python
query = select(CollectionFlow).where(
    CollectionFlow.flow_id == flow_id
)
# ERROR: Query on CollectionFlow missing tenant filters: client_account_id, engagement_id
```

### ❌ Bad - Missing engagement_id
```python
query = select(DiscoveryFlow).where(
    DiscoveryFlow.client_account_id == client_id
)
# ERROR: Query on DiscoveryFlow missing tenant filters: engagement_id
```

## Bypassing the Check

In rare cases, you may need to bypass the check:

### 1. Add Skip Comment
```python
# Use SKIP_TENANT_CHECK comment on the query line or within 5 lines after
query = select(CollectionFlow).where(...)  # SKIP_TENANT_CHECK
```

### 2. Primary Key Queries
Primary key lookups are automatically allowed:
```python
query = select(CollectionFlow).where(CollectionFlow.id == pk)
```

### 3. Excluded Files
The following are automatically skipped:
- `/tests/` - Test files
- `/alembic/versions/` - Database migrations
- `/scripts/` - Utility scripts
- `base_repository.py` - Base repository classes
- `demo_repository.py` - Demo data generators

## Running the Check Manually

### Check specific files
```bash
python backend/scripts/check_tenant_filters.py backend/app/repositories/collection_flow_repository.py
```

### Check all repository files
```bash
python backend/scripts/check_tenant_filters.py backend/app/repositories/*.py
```

### Check entire app directory
```bash
python backend/scripts/check_tenant_filters.py
```

## Pre-Commit Integration

The hook runs automatically on `git commit`:

```bash
# Stage files
git add backend/app/repositories/my_file.py

# Commit (hook runs automatically)
git commit -m "feat: Add new query"

# If violations found:
Check for missing multi-tenant filters in database queries.......................Failed
❌ backend/app/repositories/my_file.py:
   Line 42: Query on CollectionFlow missing tenant filters: engagement_id
   > query = select(CollectionFlow).where(
```

### Fix violations and retry
```bash
# Fix the code to include missing filters
# Then commit again
git commit -m "feat: Add new query"

# Should pass:
Check for missing multi-tenant filters in database queries.......................Passed
```

## Troubleshooting

### "False positive - I have the filters but hook still fails"

The AST parser may not detect complex filter patterns. Options:
1. Simplify the query structure (preferred)
2. Add `# SKIP_TENANT_CHECK` comment
3. Report the pattern as a bug to improve the parser

### "I need to query across all tenants (admin feature)"

This is legitimate for admin/system features. Add the skip comment:
```python
# Admin feature - needs to see all client data
query = select(CollectionFlow)  # SKIP_TENANT_CHECK
results = await db.execute(query)
```

### "Hook is too slow on large commits"

The hook only checks staged Python files, so it should be fast. If slow:
- Check if you're committing very large files (> 1000 lines)
- Consider modularizing large files (see CLAUDE.md)
- The hook typically runs in < 1 second for normal commits

## Implementation Details

### Script Location
`backend/scripts/check_tenant_filters.py`

### Pre-Commit Configuration
`.pre-commit-config.yaml`:
```yaml
- id: check-tenant-filters
  name: Check for missing multi-tenant filters in database queries
  entry: /opt/homebrew/bin/python3.12 backend/scripts/check_tenant_filters.py
  language: system
  files: ^backend/app/.*\.py$
  pass_filenames: true
  stages: [pre-commit]
```

### Technical Approach
- Uses Python AST parsing (not regex) for accuracy
- Recursively traverses call chains: `select().where().filter()`
- Tracks filters across multiple `.where()` calls
- Smart detection of PK-only queries
- Fast (<1s for typical commits)

## Best Practices

1. **Always include both filters** in multi-tenant queries
2. **Use repository base classes** that handle tenant scoping automatically
3. **Don't bypass unnecessarily** - the check prevents real security issues
4. **Document skip comments** - explain why tenant scoping isn't needed
5. **Review skip comments in PRs** - ensure they're legitimate

## References

- CLAUDE.md - Multi-tenant architecture documentation
- ADR-012 - Flow Status Management Separation
- `/docs/guidelines/API_REQUEST_PATTERNS.md` - API patterns

## Support

If you encounter issues:
1. Check this documentation
2. Review example queries in `backend/app/repositories/`
3. Ask in #engineering Slack channel
4. File a GitHub issue with "tenant-filter-check" label
