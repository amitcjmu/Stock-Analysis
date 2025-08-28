# Automated Bug Fix Workflow

## Command Usage
```bash
/fix-bugs  # Automatically finds and fixes GitHub bug issues
```

## Workflow Phases

### Phase 1: Issue Discovery & Triage
```bash
gh issue list --label bug --state open --json number,title,body,comments
```
- Automatically filters already fixed issues
- Skips test reports and non-actionable items
- Prioritizes by impact

### Phase 2: Multi-Agent Pipeline
Each bug goes through:
1. **QA Agent** - Reproduces and analyzes
2. **SRE Agent** - Implements fix
3. **DevSecOps Agent** - Validates and cleans
4. **QA Validation** - Confirms fix works

### Phase 3: Batch Commit & PR
- Creates single PR for multiple fixes (max 5)
- Comprehensive commit message with all issues
- Updates GitHub issues automatically

## Key Learnings

### Issue Selection
- Skip issues with comments like "Fixed in PR #"
- Focus on reproducible, actionable bugs
- Test reports (#155, #153) are informational only

### Fix Implementation
```python
# Example: Phase name mismatch fix
# File: flow_execution_service.py
def determine_phase_to_execute(discovery_flow):
    # WRONG: Invalid phase
    return "initialization"  # ❌

    # CORRECT: Valid discovery phase
    return "field_mapping"  # ✅
```

### API Endpoint Fixes
```python
# Missing endpoint pattern
# File: unified_discovery.py
@router.get("/assets")
async def get_assets(
    page_size: int = Query(100, ge=1, le=200),
    context: RequestContext = Depends(get_current_context)
):
    handler = AssetListHandler(db, context)
    return await handler.list_assets(page_size=page_size)
```

### Migration Creation
```python
# For missing tables (like sixr_analysis)
def upgrade():
    # Define enums once
    status_enum = postgresql.ENUM(..., create_type=False)
    status_enum.create(op.get_bind(), checkfirst=True)

    # Create tables with proper schema
    if not table_exists("sixr_analyses"):
        op.create_table("sixr_analyses", ..., schema="migration")
```

## Success Metrics
- 4 bugs fixed in single session
- All fixes validated by QA agent
- Single PR with comprehensive fixes
- Zero regressions introduced

## Common Bug Patterns Fixed

### 1. UI Text Overflow
```css
/* Add to components with long text */
.break-words.overflow-wrap-anywhere
```

### 2. Missing API Endpoints
- Check router_registry.py for registration
- Implement modular handler pattern
- Include tenant isolation

### 3. Database Schema Issues
- Create idempotent migrations
- Use proper schema (migration, not public)
- Check table existence before creation

### 4. Phase/Status Mismatches
- Validate against PHASE_SEQUENCES
- Use canonical phase names
- Add defensive fallbacks
