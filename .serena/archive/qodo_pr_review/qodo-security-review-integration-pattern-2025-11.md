# Qodo Bot Security Review Integration Pattern

## Purpose
Automated code review that catches security, performance, and correctness issues missed by pre-commit hooks.

## When Qodo Review Runs
- Automatically on PR creation
- Provides prioritized findings (importance 1-10)
- Categories: Security Compliance, Suggestions, Possible Issues

## High-Value Findings from Session

### 1. Information Disclosure (Security)
**Issue**: Error messages exposed schema details
```python
# ❌ BAD - Exposes 60+ field names
raise FieldValidationError(
    f"Field '{field_name}' is not editable. "
    f"Allowed fields: {sorted(ALLOWED_EDITABLE_FIELDS)}"
)

# ✅ GOOD - Generic error
raise FieldValidationError(
    f"Field '{field_name}' is not editable or does not exist"
)
```

### 2. Lenient Boolean Parsing (Security)
**Issue**: Ambiguous input values accepted
```python
# ❌ BAD - Accepts "yes", "no", "1", "0"
if value.lower() in ("true", "1", "yes"):
    return True
if value.lower() in ("false", "0", "no"):
    return False

# ✅ GOOD - Strict validation
if value.lower() == "true":
    return True
if value.lower() == "false":
    return False
```

### 3. N+1 Query Problem (Performance)
**Issue**: Loading all objects for counting
```python
# ❌ BAD - Loads all deleted assets into memory
count_query = select(Asset).where(Asset.deleted_at.isnot(None))
count_result = await db.execute(count_query)
total = len(count_result.scalars().all())  # O(n) memory

# ✅ GOOD - Database-level count
from sqlalchemy import func

count_query = select(func.count(Asset.id)).where(
    Asset.deleted_at.isnot(None)
)
total = (await db.execute(count_query)).scalar_one()  # O(1) memory
```

### 4. Optional Field Validation (UX)
**Issue**: Clearing optional number fields triggered errors
```typescript
// ❌ BAD - No empty check
if (column.column_type === 'number') {
  const numValue = parseFloat(editValue);
  if (isNaN(numValue)) {
    setValidationError('Must be a valid number');
  }
}

// ✅ GOOD - Handle empty for optional fields
if (column.column_type === 'number') {
  if (editValue === '' || editValue === null) {
    if (column.validation.required) {
      setValidationError(`${column.display_name} is required`);
      return;
    }
    // Allow empty for optional fields
  } else {
    const numValue = parseFloat(editValue);
    if (isNaN(numValue)) {
      setValidationError('Must be a valid number');
    }
  }
}
```

## Response Priority Framework

| Importance | Action | Timeline |
|------------|--------|----------|
| 9-10 | Fix immediately | Same day |
| 7-8 | Fix before merge | Next commit |
| 5-6 | Consider fixing | Optional |
| 1-4 | Note for future | Backlog |

## Integration Workflow
```bash
# 1. PR created → Qodo runs automatically
gh pr create --title "..." --body "..."

# 2. Review feedback in PR comments
# High-priority issues appear first

# 3. Fix issues locally
git checkout feature-branch
# Apply fixes

# 4. Commit and push fixes
git add -A
git commit -m "fix: Address Qodo PR review findings"
git push

# 5. Qodo re-reviews automatically
```

## Common Issue Categories

### Security
- Information disclosure in errors
- Input validation gaps
- Authentication/authorization issues

### Performance
- N+1 queries
- Inefficient counts/aggregations
- Missing indexes

### Correctness
- API endpoint mismatches
- Empty state handling
- Type coercion issues

## Value Assessment
- **High**: Catches issues pre-commit hooks miss
- **Medium**: Prioritized by importance score
- **Low**: Some false positives (use judgment)

## When to Override
```python
# Qodo suggests refactoring for complexity
# but current structure is intentional:

def validate_field_value(self, field_name: str, value: Any) -> Any:  # noqa: C901
    """Complexity 21 is acceptable - handles 60+ field types"""
    # Multiple if-elif for different field types is clearest
```
