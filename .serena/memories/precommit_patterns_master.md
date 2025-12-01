# Pre-Commit Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 5 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **400 Line Limit**: Enforce file length via modularization, not `--no-verify`
> 2. **C901 Complexity**: Reduce via helper function extraction (target: ≤10)
> 3. **Agent Delegation**: Use `devsecops-linting-engineer` for pre-commit fixes
> 4. **Auto-Formatting**: Stage Black-modified files and re-commit
> 5. **Never --no-verify**: Unless ONLY C901 blocks and security checks pass

---

## Table of Contents

1. [Overview](#overview)
2. [Common Failures](#common-failures)
3. [Complexity Reduction](#complexity-reduction)
4. [Agent Delegation](#agent-delegation)
5. [Emergency Patterns](#emergency-patterns)
6. [Anti-Patterns](#anti-patterns)
7. [Code Templates](#code-templates)
8. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Pre-commit hook failure resolution, file length compliance, cyclomatic complexity reduction, and proper agent delegation for code quality issues.

### When to Reference
- Pre-commit hook blocks commit
- File exceeds 400-line limit
- C901 complexity warning
- Linting failures (Black, Flake8, Ruff)

### Key Checks
- **File Length**: Max 400 lines
- **Complexity**: Max 15 (prefer ≤10)
- **Security**: Bandit scans
- **Formatting**: Black, Ruff

---

## Common Failures

### Issue 1: File Length Violation (>400 lines)

**Error**: `File exceeds 400 line limit`

**Solution**: Modularize, DON'T use `--no-verify`

```
service.py (643 lines) →
  service/
    ├── __init__.py       (exports for backward compat)
    ├── core.py          (main class, < 400 lines)
    └── utils.py         (helpers, < 400 lines)
```

---

### Issue 2: Complexity Warning (C901)

**Error**: `C901 'function_name' is too complex (16)`

**Threshold**: Must be ≤ 15 (prefer ≤ 10)

**Solution**: Extract helper functions (see Pattern 1 below)

---

### Issue 3: Black Formatting

**Error**: `black...Failed - files reformatted`

**Solution**: Add formatted files and re-commit

```bash
git add <formatted_files>
git commit -m "..."  # Now succeeds
```

---

### Issue 4: Duplicate Imports (F811)

**Error**: `F811 redefinition of unused 'X' from line Y`

**Solution**: Remove duplicate import statements

---

### Issue 5: Unused Imports (F401)

**Error**: `F401 'module.X' imported but unused`

**Solution**: Remove unused import or add to `__all__`

---

## Complexity Reduction

### Pattern 1: Extract Helper Function

**Before** (complexity 16):
```python
async def bulk_prepare_conflicts(...):
    for asset_data in assets_data:
        if name and name in existing_by_name:
            # ... 10 lines of logic
            continue
        if hostname and hostname in existing_by_hostname:
            # ... 8 lines of logic
            continue
        if ip and ip in existing_by_ip:
            # ... 8 lines of logic
            continue
        conflict_free.append(asset_data)
```

**After** (complexity ≤ 10):
```python
def _check_single_asset_conflict(
    asset_data: Dict[str, Any],
    existing_by_name: Dict[str, Asset],
    existing_by_hostname: Dict[str, Asset],
    existing_by_ip: Dict[str, Asset],
) -> Optional[Dict[str, Any]]:
    """Returns conflict dict if found, None otherwise."""
    if name and name in existing_by_name:
        return {...}
    if hostname and hostname in existing_by_hostname:
        return {...}
    if ip and ip in existing_by_ip:
        return {...}
    return None


async def bulk_prepare_conflicts(...):
    for asset_data in assets_data:
        conflict = _check_single_asset_conflict(
            asset_data, existing_by_name, existing_by_hostname, existing_by_ip
        )
        if conflict:
            conflicts.append(conflict)
        else:
            conflict_free.append(asset_data)
```

### Complexity Calculation (McCabe)

| Complexity | Rating | Action |
|------------|--------|--------|
| 1-5 | Simple | Good |
| 6-10 | Moderate | Acceptable |
| 11-15 | Complex | Review needed |
| 16+ | Too complex | Refactor required |

### Extraction Checklist

- [ ] Identify high-complexity section (usually loop with if/elif chains)
- [ ] Extract to pure function (no side effects)
- [ ] Pass all needed context as parameters
- [ ] Return result (don't mutate global state)
- [ ] Prefix with `_` if internal helper
- [ ] Helper should be ≤ 10 complexity itself

---

## Agent Delegation

### Pattern 2: Use Specialized Agents

**NEVER**: `git commit --no-verify` to bypass checks

**Correct**: Delegate to appropriate agent:

| Check Type | Agent |
|------------|-------|
| File length, linting | `devsecops-linting-engineer` |
| Pre-commit failures | `sre-precommit-enforcer` |
| Modularization | `devsecops-linting-engineer` |
| Security scans | `sre-precommit-enforcer` |

**Agent Task Example**:
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

---

## Emergency Patterns

### When `--no-verify` Is Acceptable

**ONLY** when ALL of these are true:
1. Security checks passed
2. File length checks passed
3. Type checking passed
4. ONLY C901 complexity warnings remain
5. Complexity is unavoidable (e.g., tenant-scoped security queries)
6. Commit contains critical security fix

**Example**:
```bash
# Verify critical checks passed first
# - File length: PASSED
# - Security: PASSED
# - Type checking: PASSED
# - Only blocker: C901 (informational)

git commit --no-verify -m "fix: critical security issue

Note: Used --no-verify to bypass C901 complexity warning
which is informational, not blocking for production.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"
```

### When NOT to Use `--no-verify`

- Security checks fail
- File length violations (>400 lines)
- Type checking errors
- Black formatting issues
- Actual flake8 errors (F401, E402, etc.)

---

## Anti-Patterns

### Don't: Bypass Pre-Commit Routinely

```bash
# WRONG - Avoids fixing real issues
git commit --no-verify -m "quick fix"

# CORRECT - Fix issues properly
# 1. Run pre-commit to see failures
# 2. Fix each failure or delegate to agent
# 3. Commit with all checks passing
```

### Don't: Extract Without Reducing Complexity

```python
# WRONG - Just moving code, not reducing complexity
def main():
    _do_everything()  # Same complexity, just hidden

# CORRECT - Split logic into cohesive helpers
def main():
    data = _validate_input()
    result = _process_data(data)
    return _format_output(result)
```

### Don't: Ignore Complexity Warnings

```python
# WRONG - Function with complexity 20+
def massive_function():
    if a:
        if b:
            if c:
                for x in items:
                    if x.valid:
                        # ... 50 more lines

# CORRECT - Break into focused functions
def massive_function():
    validated = _validate_items(items)
    return _process_validated(validated)
```

---

## Code Templates

### Template 1: Pre-Commit Failure Handler

```bash
# When pre-commit fails:
pre-commit run --all-files

# If file length violation:
# Delegate to agent for modularization

# If C901 complexity:
# Extract helper functions to reduce complexity

# If Black formatting:
git add <formatted_files>
git commit -m "..."

# If security/type errors:
# Fix the actual issue, never bypass
```

### Template 2: File Modularization

```
original_file.py (600 lines)
↓
original_file/
├── __init__.py    # Preserve public API exports
├── core.py        # Main class/logic (< 400 lines)
├── utils.py       # Helper functions (< 400 lines)
└── types.py       # Type definitions (if needed)
```

**`__init__.py` template**:
```python
# Backward-compatible exports
from .core import MainClass, main_function
from .utils import helper_function

__all__ = ['MainClass', 'main_function', 'helper_function']
```

---

## Troubleshooting

### Issue: Commit blocked by multiple failures

**Process**:
1. Run `pre-commit run --all-files` to see all failures
2. Fix in priority order: Security → File Length → Formatting → Complexity
3. Stage fixes and re-run pre-commit
4. Commit when all pass

### Issue: File needs modularization but urgent fix needed

**Process**:
1. Create small focused fix commit if possible
2. If not possible, delegate modularization to agent
3. Let agent complete modularization
4. Then apply your fix to modularized code

### Issue: C901 in code that can't be simplified

**If truly unavoidable** (e.g., complex security validation):
1. Document why in code comments
2. Consider if logic can be table-driven instead
3. As last resort, use `--no-verify` with explanation in commit message

---

## Consolidated Sources

| Original Memory | Key Contribution |
|-----------------|------------------|
| `precommit-complexity-reduction-pattern-2025-01` | Complexity reduction |
| `precommit_troubleshooting_2025_01` | Common failures |
| `precommit-agent-delegation-pattern` | Agent delegation |
| `flake8-c901-complexity-warnings-handling` | C901 handling |
| `pre_commit_security_fixes` | Security integration |

**Archive Location**: `.serena/archive/precommit/`

---

## Search Keywords

precommit, pre-commit, complexity, c901, file_length, 400_lines, modularization, black, flake8, ruff
