# File Length Limit Pre-Commit Enforcement and Modularization Strategy

**Date**: November 6, 2025
**Context**: Pre-commit hook blocked commit due to file exceeding 400-line limit

---

## Problem

Active development session, file grew to 411 lines, pre-commit hook blocked commit:

```
❌ backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py: 411 lines (exceeds 400 line limit)

These files must be modularized before committing.
```

## Anti-Pattern: Rushed Arbitrary Splitting

**Don't do this** when hitting file length limit mid-session:
```python
# BAD: Arbitrary split just to pass pre-commit
utils.py → utils_part1.py + utils_part2.py  # No logical grouping
```

**Problems**:
- Breaks logical cohesion
- Creates circular dependencies
- Makes code harder to navigate
- Rushed decisions during active development

## Best Practice: Defer and Delegate

### Strategy 1: Defer to Next Session
```markdown
# In handoff document:
**Blocker**: utils.py is 411 lines (exceeds 400 limit) - needs modularization

**Recommended Split**:
- gap_detection.py - Gap analysis logic (_check_missing_critical_fields)
- asset_serialization.py - Asset data extraction (_analyze_selected_assets)
- eol_detection.py - EOL status determination (_determine_eol_status)
- data_extraction.py - Agent result parsing (_extract_questionnaire_data)
- utils.py - Small helpers (<100 lines)

**Delegate to**: Next session or devsecops-linting-engineer agent
```

### Strategy 2: Delegate to Specialized Agent
```bash
# Use Task tool with devsecops-linting-engineer
Task: "Modularize collection_crud_questionnaires/utils.py (411 lines) following
      responsibility-based separation. Create separate files for gap detection,
      asset serialization, EOL detection, and data extraction. Preserve all
      functionality and update imports."
```

### Strategy 3: Stash and Continue
```bash
# If urgent fixes needed before modularization
git stash push -m "utils.py changes - needs modularization"
# Continue with other work
# Return to modularization later with proper planning
```

## Proper Modularization Process

### 1. Analyze Responsibilities

```python
# utils.py (411 lines) breakdown:
# Lines 1-50: Import statements and module setup
# Lines 51-110: Agent result parsing (_extract_questionnaire_data)
# Lines 111-215: Asset serialization (_analyze_selected_assets)
# Lines 216-283: Gap detection (_check_missing_critical_fields)
# Lines 284-340: EOL detection (_determine_eol_status)
# Lines 341-411: Helper functions and utilities
```

### 2. Group by Cohesion

```
collection_crud_questionnaires/
├── __init__.py               # Public API exports
├── commands.py               # Write operations (existing)
├── queries.py                # Read operations (existing)
├── utils/                    # NEW: Modularized utilities
│   ├── __init__.py          # Re-export for backward compat
│   ├── gap_detection.py     # _check_missing_critical_fields
│   ├── asset_serialization.py  # _analyze_selected_assets
│   ├── eol_detection.py     # _determine_eol_status
│   ├── data_extraction.py   # _extract_questionnaire_data
│   └── helpers.py           # Small utility functions
```

### 3. Preserve Public API

```python
# utils/__init__.py - Maintain backward compatibility
from .gap_detection import _check_missing_critical_fields
from .asset_serialization import _analyze_selected_assets
from .eol_detection import _determine_eol_status
from .data_extraction import _extract_questionnaire_data

__all__ = [
    "_check_missing_critical_fields",
    "_analyze_selected_assets",
    "_determine_eol_status",
    "_extract_questionnaire_data",
]
```

### 4. Update Imports Systematically

```python
# Before (single file):
from app.api.v1.endpoints.collection_crud_questionnaires.utils import (
    _check_missing_critical_fields,
    _analyze_selected_assets,
)

# After (modularized):
from app.api.v1.endpoints.collection_crud_questionnaires.utils import (
    _check_missing_critical_fields,  # Still works via __init__.py
    _analyze_selected_assets,
)
# OR direct import if needed:
from app.api.v1.endpoints.collection_crud_questionnaires.utils.gap_detection import (
    _check_missing_critical_fields
)
```

## Modularization Patterns

### Pattern 1: Directory with __init__.py (Recommended)
```
utils.py → utils/__init__.py + utils/*.py
```
- Preserves import paths
- Backward compatible
- Clean namespace

### Pattern 2: Parallel Files
```
utils.py → utils_gap.py + utils_eol.py + utils_data.py
```
- Simpler structure
- Requires import updates
- Less namespace pollution

### Pattern 3: Subdirectory per Responsibility
```
utils.py → gap_detection/core.py + eol/detector.py + serialization/assets.py
```
- Most modular
- Best for >1000 line files
- Overkill for 400-line splits

## When to Apply Each Strategy

| Situation | Strategy | Reason |
|-----------|----------|--------|
| Active development, mid-session | Defer to next session | Avoid rushed decisions |
| Clear module boundaries | Modularize immediately | Clean split, low risk |
| Complex dependencies | Delegate to agent | Agent can trace all imports |
| Urgent fixes needed | Stash changes | Unblock critical work |
| >600 lines | Pattern 3 (subdirectories) | Major refactor needed |
| 400-600 lines | Pattern 1 (directory) | Balanced approach |
| <400 lines | Skip modularization | Not worth overhead |

## Pre-Commit Hook Philosophy

**Purpose**: Enforce maintainability through file length limits

**Balance**:
- ✅ Prevents monolithic files from growing unbounded
- ✅ Encourages modular design
- ❌ Should not block urgent fixes
- ❌ Should not force arbitrary splits

**Escape Hatch**: Use `.pre-commit-config.yaml` excludes for temporary exceptions:
```yaml
# Only as last resort, with comment explaining why
- id: check-file-length
  exclude: |
    ^backend/app/api/v1/endpoints/collection_crud_questionnaires/utils\.py$
  # TODO: Modularize utils.py (issue #XXX)
```

## Testing After Modularization

```python
# Verify all imports still work
def test_backward_compatible_imports():
    """Ensure modularization didn't break existing imports."""
    from app.api.v1.endpoints.collection_crud_questionnaires.utils import (
        _check_missing_critical_fields,
        _analyze_selected_assets,
    )
    # Should not raise ImportError

# Verify functionality preserved
def test_gap_detection_still_works():
    """Ensure modularization didn't break logic."""
    missing, existing = _check_missing_critical_fields(test_asset)
    assert len(missing) > 0  # Same behavior as before
```

## Files

- Blocked: `backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py` (411 lines)
- Handoff: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/COLLECTION_FLOW_FIXES_STATUS.md`

## Related Patterns

- Modular repository pattern
- Facade pattern for backward compatibility
- Responsibility-driven design
