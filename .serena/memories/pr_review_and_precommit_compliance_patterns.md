# PR Review and Pre-commit Compliance Patterns [2025-01-18]

## Insight 1: Specialized Agent Delegation for PR Reviews
**Problem**: Manual PR review suggestions and pre-commit fixes are time-consuming
**Solution**: Delegate to specialized agents for systematic fixes
**Code**:
```python
# For pre-commit compliance
Task(subagent_type="sre-precommit-enforcer")
# For security and linting
Task(subagent_type="devsecops-linting-engineer")
# For Python/FastAPI modularization
Task(subagent_type="python-crewai-fastapi-expert")
```
**Usage**: Always use agents for PR review fixes instead of manual edits

## Insight 2: SQL Injection Prevention in Migrations
**Problem**: Bandit flags SQL with f-strings as injection risk
**Solution**: Add double quotes for column names and nosec annotations
**Code**:
```python
# Column names from controlled dictionary, not user input  # nosec B608
audit_sql = text(f'''
    SELECT "{legacy}" as legacy_val, "{canonical}" as canonical_val
    FROM migration.discovery_flows
    WHERE "{legacy}" IS DISTINCT FROM "{canonical}"
''')
```
**Usage**: When using f-strings in migrations with controlled column names

## Insight 3: File Modularization Pattern (<400 lines)
**Problem**: Pre-commit blocks files over 400 lines
**Solution**: Extract mixins/utilities while maintaining backward compatibility
**Pattern**:
```
original_file.py → original_file/
├── __init__.py (re-exports for compatibility)
├── base_model.py (main class)
├── collaboration_mixin.py (methods by concern)
└── serialization_mixin.py (conversion methods)
```
**Usage**: Split large models/endpoints into focused modules

## Insight 4: Merge Conflict Resolution - Deleted Files
**Problem**: File deleted in branch but modified in main
**Solution**: Keep deletion if intentional
**Code**:
```bash
git rm config/docker/docker-compose.override.yml
git commit -m "Merge: Keep file deleted as intended"
```
**Usage**: When override files cause version conflicts

## Insight 5: IS DISTINCT FROM for NULL-safe Comparisons
**Problem**: Boolean migration comparisons miss NULLs
**Solution**: Use IS DISTINCT FROM instead of !=
**Code**:
```sql
UPDATE migration.discovery_flows
SET "{canonical}" = "{legacy}"
WHERE "{legacy}" IS NOT NULL
  AND "{canonical}" IS DISTINCT FROM "{legacy}"
```
**Usage**: Database migrations with nullable boolean columns
