# Pre-commit Troubleshooting Guide - January 2025

## Common Pre-commit Failures

### 1. Black Formatting Fails with Syntax Errors
**Problem**: Black can't format files with syntax errors
**Solution**: Fix syntax errors first, then run Black

### 2. Flake8 Complexity Warnings (C901)
**Problem**: Functions exceed complexity threshold
**Impact**: Warning only, doesn't block commit unless strict mode
**Solution**: Refactor complex functions or use `--no-verify` if not critical

### 3. File Length Violations (>400 lines)
**Problem**: Files exceed project's 400-line limit
**Solution**:
- Modularize into separate files
- Use `--no-verify` for emergency fixes
- Plan refactoring in separate PR

### 4. Duplicate Import Errors (F811)
**Problem**: Same module imported multiple times
**Solution**: Remove duplicate imports

### Emergency Commit Pattern
```bash
# When pre-existing issues block critical fixes
git add -A
git commit --no-verify -m "fix: Critical production fix

[Detailed message]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## File Cleanup Strategy
1. Delete corrupted backup files (*.corrupted.py, *_original.py)
2. Fix syntax errors in remaining files
3. Run `ruff check --fix` for auto-fixable issues
4. Use `black` for formatting after syntax fixes
