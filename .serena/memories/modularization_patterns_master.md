# Modularization Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 15 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **400 Line Limit**: Target module size, enforced by pre-commit
> 2. **Shim Pattern**: Original file becomes import wrapper for backward compatibility
> 3. **Package Structure**: base.py, utils.py, handlers/, strategies/
> 4. **Zero Breaking Changes**: Always maintain public API surface
> 5. **Complexity < 10**: Cyclomatic complexity per function

---

## Core Patterns

### Pattern 1: Directory-Based Modularization

**Before**: `large_file.py` (1000+ lines)

**After**:
```
large_file/
├── __init__.py       # Backward-compatible exports
├── base.py           # Core types, exceptions, constants
├── utils.py          # Helper functions
├── handlers/         # Specialized handlers
└── strategies/       # Implementation strategies
```

### Pattern 2: Shim for Backward Compatibility

```python
# Original file becomes shim
# large_file.py
import warnings
from .large_file import *  # Re-export all

warnings.warn(
    "Import from .large_file package instead",
    FutureWarning, stacklevel=2
)
```

### Pattern 3: __init__.py Exports

```python
# __init__.py
from .base import BaseClass, BaseException
from .executor import MainExecutor
from .utils import helper_function

__all__ = ['BaseClass', 'BaseException', 'MainExecutor', 'helper_function']
```

---

## Successful Examples

| Original File | Before | After | Pattern |
|--------------|--------|-------|---------|
| `azure_adapter.py` | 1582 | 385 | Cloud service split |
| `crewai_flow_service.py` | 1561 | 39 | Service to package |
| `collection_handlers.py` | 1369 | 73 | 11 specialized handlers |
| `field_mapping_executor.py` | 1206 | 245 | Executor modularization |
| `asset_inventory_executor.py` | 832 | 22 | Phase executor split |

---

## Pre-Commit Compliance

**Fix Common Issues**:
- F401 (unused imports): Remove or use `__all__`
- F821 (undefined names): Add proper imports
- F841 (unused variables): Prefix with `_`
- Complexity: Split large functions

---

## Steps to Modularize

1. Analyze dependencies and logical boundaries
2. Create package directory structure
3. Extract modules maintaining cohesion
4. Create backward-compatible `__init__.py`
5. Replace original file with shim
6. Fix imports and type annotations
7. Validate with `pre-commit run --all-files`
8. Test in Docker

---

## Consolidated Sources

| Original Memory | Key Contribution |
|-----------------|------------------|
| `modularization_patterns` | Core patterns |
| `file_length_limit_modularization` | 400-line enforcement |
| `modularization-pattern-handlers-and-tasks` | Handler patterns |
| `flow_commands_modularization_success` | Flow examples |

**Archive Location**: `.serena/archive/modularization/`

---

## Search Keywords

modularization, file_length, 400_lines, shim, backward_compatibility, package, split
