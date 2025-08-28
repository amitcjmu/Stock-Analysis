# Qodo Bot PR Review Handling

## Systematic Approach to Address All PR Suggestions

### Priority Classification
Qodo bot suggestions come with priority levels:
- **HIGH**: Security, data integrity, critical bugs
- **MEDIUM**: Performance, UX, maintainability
- **LOW**: Code quality, consistency, minor improvements

### Complete Resolution Workflow

#### 1. Gather All Suggestions
```bash
# Use GitHub CLI to get full PR review
gh pr view [PR_NUMBER] --comments | grep -A5 "qodo"

# Or check PR page directly for Qodo bot comments
# Look for the screenshot/full list, not just initial comments
```

#### 2. Common Qodo Suggestions & Fixes

##### Foreign Key Schema Mismatches
**Issue**: FK references wrong schema (e.g., `"assets.id"` vs `"migration.assets.id"`)
**Fix**: Check actual table schema location in migrations

##### Legacy Endpoint Aliases
**Issue**: Breaking changes need backward compatibility
**Fix**: Add duplicate route with deprecation notice
```python
@router.post("/legacy/endpoint")  # Old path
async def legacy_handler(...):
    """LEGACY: Forward to new endpoint"""
    return await new_handler(...)
```

##### Form Reset Prevention
**Issue**: useEffect causing unintended resets
**Fix**: Add `hasInteracted` flag or proper dependency array

##### Number Rendering Checks
**Issue**: `questionNumber !== undefined` doesn't handle 0
**Fix**: `questionNumber !== undefined && questionNumber !== null && questionNumber >= 0`

##### JSON Filter Portability
**Issue**: Database-specific JSON operators
**Fix**: Use SQLAlchemy's database-agnostic approach with fallback

### 3. Multi-Agent Resolution
Use specialized agents for different suggestion types:
- `devsecops-linting-engineer`: Security and linting issues
- `pgvector-data-architect`: Database/migration issues
- `qa-playwright-tester`: Validation of fixes

### 4. Validation Before Push
- Run pre-commit hooks at least once
- Test affected functionality
- Verify no new issues introduced

### 5. Commit Message Template
```bash
git commit -m "fix: Address all Qodo bot PR suggestions

HIGH Priority Fixes:
- [List HIGH priority items addressed]

MEDIUM Priority Fixes:
- [List MEDIUM priority items addressed]

LOW Priority Fixes:
- [List LOW priority items addressed]

All fixes follow project conventions with snake_case field naming
and maintain backward compatibility.

🤖 Generated with CC

Co-Authored-By: Claude <noreply@anthropic.com>"
```
