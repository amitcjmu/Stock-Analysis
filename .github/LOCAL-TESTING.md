# Local Testing Guide

Since GitHub Actions are limited, run these checks locally before pushing:

## Quick Check Script

```bash
#!/bin/bash
# Save as: scripts/local-checks.sh

echo "🔍 Running local checks..."

# Python syntax check
echo "Checking Python syntax..."
python -m py_compile backend/**/*.py 2>/dev/null || echo "⚠️ Python syntax issues found"

# TypeScript check (if in root)
if [ -f "package.json" ]; then
    echo "Checking TypeScript..."
    npm run type-check 2>/dev/null || npx tsc --noEmit 2>/dev/null || echo "⚠️ TypeScript issues found"
fi

# Basic security scan
echo "Scanning for secrets..."
! grep -r -E "(api[_-]?key|secret|token|password).*=.*['\"][A-Za-z0-9+/]{20,}" \
    --include="*.py" --include="*.ts" --include="*.tsx" \
    --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null || \
    echo "⚠️ Potential secrets found"

echo "✅ Local checks complete"
```

## Pre-commit Hooks (Already Configured)

Your project already has pre-commit hooks that run automatically:

```bash
# Run all pre-commit checks manually
pre-commit run --all-files

# Run specific checks
pre-commit run black --all-files
pre-commit run flake8 --all-files
pre-commit run mypy --all-files
```

## Manual Testing Commands

### Backend
```bash
cd backend

# Syntax and style
black . --check
flake8 .
mypy .

# Tests (when Actions quota available)
pytest tests/

# Security
bandit -r app/
```

### Frontend
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Tests (when Actions quota available)
npm test
```

### Docker
```bash
# Build test
docker-compose -f config/docker/docker-compose.yml build

# Start services
./docker-start.sh
```

## When to Run Full Checks

Run the full test suite locally when:
- Before merging to main
- After significant changes
- Before releases
- When debugging issues

## GitHub Actions Management

```bash
# Check workflow status
./scripts/manage-github-workflows.sh status

# Temporarily enable all workflows (uses Actions minutes!)
./scripts/manage-github-workflows.sh enable

# Disable heavy workflows again
./scripts/manage-github-workflows.sh disable
```
