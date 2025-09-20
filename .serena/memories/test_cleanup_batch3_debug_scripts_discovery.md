# Test Cleanup Batch 3 - Debug Scripts Discovery

## Major Finding: 80% of "Keep" Files Were Debug Scripts

**Problem**: 109 files marked as "Keep" in test suite, but most were not actual tests
**Discovery**: Files with `test_` prefix in `backend/scripts/` were debug utilities, not tests

## Identification Pattern

**Criteria for Real Tests**:
```python
# Real test file pattern
import pytest  # or
import unittest

@pytest.mark.asyncio
class TestClassName:
    def test_method_name(self):
        assert something
```

**Debug Script Pattern** (to remove):
```python
#!/usr/bin/env python3
# No pytest/unittest imports
# Direct script execution
if __name__ == "__main__":
    # Hardcoded values
    # Direct API calls
    # Manual testing
```

## Files Removed (87 total)

### Categories:
1. **backend/scripts/test_*.py** (28 files) - Debug utilities
2. **scripts/test_*.py** (9 files) - Context debugging
3. **tests/backend/test_*.py** (30 files) - Scripts without test framework
4. **tests/backend/e2e/** - Obsolete E2E directory
5. **Misplaced tests** in service directories

## Cleanup Commands

```bash
# Identify non-test files
grep -L "import pytest\|import unittest" tests/backend/test_*.py

# Remove debug scripts from backend/scripts
rm backend/scripts/test_*.py

# Remove obsolete directories
rm -rf tests/backend/e2e/
rm -rf tests/backend/collaboration/
rm -rf tests/backend/planning/
```

## Lessons Learned

1. **File naming != file purpose** - `test_` prefix doesn't make it a test
2. **Location matters** - Scripts belong in `scripts/`, tests in `tests/`
3. **Framework required** - Tests must import pytest/unittest
4. **Regular cleanup needed** - Debug scripts accumulate over time

## Future Prevention

```python
# Pre-commit hook to verify test files
def check_test_file(filepath):
    if filepath.startswith('test_'):
        with open(filepath) as f:
            content = f.read()
            if 'import pytest' not in content and 'import unittest' not in content:
                raise ValueError(f"{filepath} uses test_ prefix but isn't a test")
```

**Usage**: Apply when reviewing test directories to identify debug scripts masquerading as tests
