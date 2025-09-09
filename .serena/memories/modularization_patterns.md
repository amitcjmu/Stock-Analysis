# Modularization Patterns and Strategies

## Core Principles
- **Zero Breaking Changes**: Always maintain backward compatibility using shim patterns
- **Target Module Size**: 400 lines per module (configurable)
- **Minimum Trigger**: Files exceeding 1000 lines
- **Directory-Based Approach**: Convert single files to packages with __init__.py

## Successful Patterns Applied

### 1. Shim Pattern for Backward Compatibility
```python
# Original file becomes a shim importing from modularized package
from .module_name import *  # For backward compatibility
```

### 2. Module Organization Strategy
- **base.py**: Core types, exceptions, constants
- **utils.py**: Helper functions and utilities
- **handlers/**: Specialized handler modules
- **strategies/**: Different implementation strategies
- **validators/**: Validation logic
- **transformers/**: Data transformation modules

### 3. Complexity Reduction Targets
- Cyclomatic complexity: <10 per function
- Module cohesion: Single responsibility principle
- Import optimization: Avoid circular dependencies

## Files Successfully Modularized

### PR #116 (Original Large-Scale Modularization)

1. **azure_adapter.py** (1582→385 lines)
   - Split into: auth, compute, network, storage, monitoring modules
   - Pattern: Cloud service modularization

2. **crewai_flow_service.py** (1561→39 lines)
   - Pattern: Service to package conversion
   - Maintained all public API surface

3. **collection_handlers.py** (1369→73 lines)
   - Split into 11 specialized handlers
   - Pattern: Handler specialization

4. **storage_manager.py** (1223→293 lines)
   - Added missing type definitions
   - Pattern: Storage layer modularization

5. **field_mapping_executor.py** (1206→245 lines)
   - Reduced complexity from 45 to <10
   - Pattern: Executor modularization

6. **cache_consistency_checker.py** (1185→76 lines)
   - Created validation, conflict, recovery modules
   - Pattern: Cache strategy separation

7. **invalidation_strategies.py** (1172→123 lines)
   - Split by strategy type: time, event, dependency
   - Pattern: Strategy pattern implementation

8. **crew_escalation_manager.py** (1165→294 lines)
   - Maintained crew integration patterns
   - Pattern: Escalation logic separation

9. **agent_reasoning_patterns.py** (1103→30 lines)
   - Most comprehensive: 41 modules in 6 subdirectories
   - Pattern: AI reasoning categorization

### Recent Pre-Commit Enforcement (2025-09)

10. **asset_inventory_executor.py** (832→22 lines)
    - **TRIGGER**: Pre-commit hook blocked commit (650 lines > 400 limit)
    - **SOLUTION**: 4-file modular structure with backward compatibility
    - **Pattern**: Phase executor modularization

    **Structure Created**:
    ```
    asset_inventory/
    ├── __init__.py (9 lines) - Backward compatibility exports
    ├── executor.py (111 lines) - Main orchestration logic
    ├── database_operations.py (368 lines) - Database interactions
    ├── utils.py (251 lines) - Asset processing utilities
    └── crew_processor.py (132 lines) - CrewAI agent processing
    ```

    **Backward Compatibility**:
    ```python
    # Original file becomes deprecation wrapper
    import warnings
    from .asset_inventory import AssetInventoryExecutor

    warnings.warn(
        "Importing AssetInventoryExecutor from asset_inventory_executor is deprecated. "
        "Please import from .asset_inventory instead.",
        FutureWarning,
        stacklevel=2,
    )
    ```

## Common Modularization Steps
1. Analyze file structure and dependencies
2. Identify logical boundaries and responsibilities
3. Create package directory structure
4. Extract modules maintaining import order
5. Create backward-compatible __init__.py
6. Replace original file with shim
7. Fix imports and type annotations
8. Validate with pre-commit hooks
9. Test in Docker environment

## Pre-commit Compliance
- Fix F401 (unused imports) in shims
- Fix F821 (undefined names) with proper imports
- Fix F841 (unused variables) with underscore prefix
- Maintain black formatting
- Pass flake8 complexity checks
- Ensure mypy type checking passes

## Risk Mitigation
- Always check for existing modularization first
- Preserve all public API interfaces
- Maintain original import paths
- Test with Docker before committing
- Use git stash for rollback safety
