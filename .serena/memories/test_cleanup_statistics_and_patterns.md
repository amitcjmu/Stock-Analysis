# Test Cleanup Statistics and Patterns

## Final Statistics (Batch 4)
- **153 Python files** analyzed in /tests and /backend/tests
- **90 legitimate test files** (59%)
- **33 debug/fix scripts** (22%) → moved to backend/scripts/debug/
- **18 high-risk scripts** (12%) → deleted (hardcoded credentials)
- **12 miscellaneous files** (7%) → configs/utilities

## Directory Structure Pattern
```
backend/
├── scripts/
│   ├── debug/           # Debug utilities (NEW)
│   │   ├── debug_*.py   # Analysis scripts
│   │   ├── fix_*.py     # Fix scripts
│   │   └── check_*.py   # Validation scripts
│   └── run_tests_docker.py
tests/
├── backend/
│   ├── integration/     # Real integration tests only
│   ├── flows/          # Flow-specific tests
│   └── test_*.py       # Unit tests
```

## Key Cleanup Commands
```bash
# Move debug scripts in batch
for file in debug_*.py fix_*.py check_*.py; do
    mv "tests/backend/$file" "backend/scripts/debug/"
done

# Find real test files
grep -r "import pytest\|import unittest" tests/ --include="*.py"

# Identify security risks
grep -r "password\|secret\|key" tests/ --include="*.py" | grep -v "TEST_"
```

## Security Patterns to Remove
1. Hardcoded credentials: `postgres:password`
2. Real-looking keys: `sk_live_*` → `TEST_KEY_123_FAKE`
3. SQL injection risks: Direct string formatting in SQL
4. Command injection: `shell=True` in subprocess

## Test Quality Improvements Applied
1. Replace hardcoded UUIDs with `str(uuid.uuid4())`
2. Add `@pytest.mark.mfo` for MFO tests
3. Use snake_case field names (not camelCase)
4. Add tenant isolation checks
5. Improve assertions (no truthy checks for numeric fields)