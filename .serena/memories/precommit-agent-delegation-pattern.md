# Pre-Commit File Length Violations - Agent Delegation Pattern

**Problem**: Attempting to commit with `--no-verify` to bypass 400-line file length check

**NEVER DO THIS**: `git commit --no-verify` - bypasses critical quality checks

**Correct Approach**: Delegate to specialized agents

**Agent Selection**:
- `devsecops-linting-engineer`: File length, linting, code quality, modularization
- `sre-precommit-enforcer`: Pre-commit hook failures, security scans, compliance

**Example Task**:
```python
Task(
    subagent_type="devsecops-linting-engineer",
    prompt="""
    Modularize backend/app/services/data_import/background_execution_service.py
    Current: 643 lines, Target: < 400 lines per module
    Preserve bug fixes at lines X-Y
    Follow codebase patterns: core/ + utils/ + __init__.py
    """
)
```

**Modularization Pattern**:
```
service.py (643 lines) →
  service/
    ├── __init__.py       (exports for backward compat)
    ├── core.py          (main class, < 400 lines)
    └── utils.py         (pure functions, < 400 lines)
```

**Process**:
1. Pre-commit blocks commit with specific check failure
2. Read error message to identify check type
3. Choose appropriate agent (linting vs security vs architecture)
4. Let agent fix properly with full check verification
5. Commit with all checks passing

**Reference**: Used in commit 03e4a67d9 for background_execution_service.py modularization
