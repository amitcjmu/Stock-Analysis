# Pre-commit Security Fixes

## Problem: Bandit Security Warnings
subprocess.run with shell=True triggers security warnings in pre-commit

## Solution: Add nosec Comments
```python
# For legitimate shell commands (Docker, git)
result = subprocess.run(
    cmd, shell=True, capture_output=True, text=True
)  # nosec B602
```

## Problem: Unused Imports
flake8 flags imported but unused modules

## Solution: Remove Unused Imports
```python
# Before
from dataclasses import dataclass, asdict

# After (if asdict not used)
from dataclasses import dataclass
```

## Black Formatting Auto-Fix
Pre-commit automatically reformats with black. Always:
1. Let it fail first time
2. Stage the reformatted files
3. Commit again

## When to Apply
- Adding new Python files
- Using subprocess for Docker/git commands
- After any flake8 failures
