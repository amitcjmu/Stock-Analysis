# File Length Limit Modularization (400-line Pre-commit Rule)

## Context
Project enforces a strict 400-line limit per Python file via pre-commit hook located at `scripts/check-file-length.py`.

## Successfully Modularized Files (2025-08)

### 1. master_flows.py (646→361 lines)
**Pattern**: API Endpoint Modularization
```python
# Split into:
master_flows_schemas.py    # Response models (58 lines)
master_flows_service.py    # Business logic (264 lines)
master_flows.py           # Route definitions only (361 lines)
```

### 2. flow_intelligence_knowledge.py (481→58 lines)
**Pattern**: Knowledge Base Modularization
```python
# Split into:
flow_intelligence_enums.py       # Enums (30 lines)
flow_intelligence_definitions.py # Flow definitions (251 lines)
flow_intelligence_context.py     # Context services (119 lines)
flow_intelligence_utils.py       # Utility functions (93 lines)
flow_intelligence_knowledge.py   # Facade for backward compatibility (58 lines)
```

## Critical Success Factors

### 1. Maintain Complete Backward Compatibility
```python
# Main file becomes re-export facade:
from .flow_intelligence_context import (
    AGENT_INTELLIGENCE,
    CONTEXT_SERVICES,
    NAVIGATION_RULES,
)
from .flow_intelligence_definitions import FLOW_DEFINITIONS
from .flow_intelligence_enums import ActionType, FlowType, PhaseStatus
from .flow_intelligence_utils import (
    get_flow_definition,
    get_navigation_path,
    # ... all other functions
)

__all__ = [  # Explicit exports for clarity
    "FlowType", "PhaseStatus", "ActionType",
    "FLOW_DEFINITIONS", "CONTEXT_SERVICES",
    # ... all exported items
]
```

### 2. Verify External Imports Still Work
```bash
# Test imports after modularization:
python -c "from app.knowledge_bases.flow_intelligence_knowledge import FlowType, get_navigation_path; print('Success')"

# Check all files importing the module:
grep -r "from.*flow_intelligence_knowledge import" backend/
grep -r "from app.api.v1.master_flows import" backend/
```

### 3. Fix Import Issues During Modularization
- Move imports to correct location (e.g., datetime at top of file, not bottom)
- Use relative imports within package: `from .module import item`
- Ensure all necessary imports are present in split modules

### 4. Common Fixes Required
```python
# Issue: Missing datetime import
from datetime import datetime  # Add at top of service module

# Issue: Non-existent method calls
# Instead of: discovery_repo.update_metadata(...)
# Use direct DB operations:
discovery_flow.metadata = {...}
await db.commit()

# Issue: Incorrect function signatures
# Check actual function definitions and fix calls
from app.models.flow_deletion_audit import FlowDeletionAudit
audit = FlowDeletionAudit(...)  # Use proper model
```

## Pre-commit Validation
```bash
# Check specific files:
/opt/homebrew/bin/python3.11 scripts/check-file-length.py backend/app/api/v1/master_flows*.py

# Run full pre-commit on modularized files:
/Users/chocka/Library/Python/3.9/bin/pre-commit run check-file-length --files <files>
```

## Using Linting Agents
Always use `devsecops-linting-engineer` agent to fix issues:
- Black formatting
- Flake8 violations
- Mypy type errors
- Bandit security issues
- File length compliance

## Checklist for 400-line Modularization
- [ ] Identify files exceeding 400 lines
- [ ] Plan logical module separation
- [ ] Create new module files with proper headers
- [ ] Move code maintaining functionality
- [ ] Add relative imports between modules
- [ ] Create re-export facade in main file
- [ ] Test all external imports still work
- [ ] Run linting agent to fix all issues
- [ ] Verify pre-commit passes
- [ ] Test functionality in Docker
- [ ] Commit with descriptive message
