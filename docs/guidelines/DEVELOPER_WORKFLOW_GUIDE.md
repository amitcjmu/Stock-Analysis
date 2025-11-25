# Developer Workflow Guide

This guide walks you through the complete workflow for fixing code issues in this project using VSCode without AI tools.

## Prerequisites

- Docker Desktop installed and running
- VSCode with Python and TypeScript extensions
- Git configured with your credentials
- Access to the GitHub repository

## 1. Creating a Fix Branch

### Start from Updated Main
```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create a descriptive branch name
git checkout -b fix/your-descriptive-fix-name
```

**Note:** After creating a branch, if you continue working and `main` has moved forward, use `./scripts/sync-with-main.sh` to keep your branch up to date before pushing.

**Branch Naming Conventions:**
- `fix/` - Bug fixes (e.g., `fix/collection-flow-resume-errors`)
- `feat/` - New features (e.g., `feat/asset-agnostic-collection`)
- `refactor/` - Code refactoring (e.g., `refactor/modularize-flow-handlers`)

## 2. Setting Up Development Environment

### Docker-First Development (Required)
This project requires Docker for all development - no local Python/Node.js services.

```bash
# Start all services
cd config/docker
docker-compose up -d

# Verify services are running
docker ps

# Access the application
# Frontend: http://localhost:8081 (NOT 3000)
# Backend API: http://localhost:8000
# Database: localhost:5433
```

### Common Docker Commands
```bash
# View logs
docker logs migration_backend -f
docker logs migration_frontend -f

# Access backend container for debugging
docker exec -it migration_backend bash

# Access database
docker exec -it migration_postgres psql -U postgres -d migration_db

# Restart a specific service
docker restart migration_backend
```

## 3. Making Code Changes

### Code Quality Standards

**API Field Naming (Critical):**
- Backend returns `snake_case` fields (e.g., `flow_id`, `client_account_id`)
- Frontend uses `snake_case` for all NEW code to match backend
- NO field name transformation - use API responses directly

**Request Body vs Query Parameters:**
```typescript
// ❌ WRONG - Causes 422 errors
await apiCall(`/api/endpoint?param=value`, { method: 'POST' })

// ✅ CORRECT
await apiCall(`/api/endpoint`, {
  method: 'POST',
  body: JSON.stringify({ param: 'value' })
})
```

**File Length Limit:**
- Python files must be ≤ 400 lines
- If longer, modularize into separate files
- Pre-commit checks will enforce this

### Making Changes

1. **Search existing code first** before adding new implementations:
   ```bash
   # Search for similar functionality
   grep -r "function_name" backend/
   find . -name "*.py" -exec grep -l "SimilarClass" {} \;
   ```

2. **Modify existing code** rather than creating new files when possible

3. **Follow architectural patterns:**
   - Use Master Flow Orchestrator (MFO) pattern for workflow operations
   - All API calls through `/api/v1/master-flows/*` endpoints
   - Multi-tenant data scoping with `client_account_id` and `engagement_id`

## 4. Running and Resolving Pre-commit Checks

### Install Pre-commit (One-time Setup)
```bash
# In the backend directory
cd backend
pip install pre-commit
pre-commit install
```

### Running Pre-commit Checks
```bash
# Run on staged files (before commit)
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hooks
pre-commit run black
pre-commit run flake8
pre-commit run mypy-staged
```

### Common Pre-commit Issues and Solutions

**1. Gitleaks (Secret Detection)**
```bash
# Issue: Hardcoded secrets detected
# Solution: Move secrets to environment variables
DATABASE_URL = os.getenv("DATABASE_URL")  # ✅ Good
DATABASE_URL = "postgresql://user:pass@localhost"  # ❌ Bad
```

**2. Bandit (Security)**
```bash
# Issue: Security warnings
# Common fixes:
# - Use os.path.join() instead of string concatenation for paths
# - Use subprocess with shell=False
# - Avoid eval(), exec(), and raw input()
```

**3. Black (Code Formatting)**
```bash
# Issue: Code formatting violations
# Solution: Let Black fix them automatically
black backend/app/your_file.py
```

**4. Flake8 (Linting)**
```bash
# Issue: Style violations (line length, unused imports, etc.)
# Common fixes:
# - Break long lines (max 120 characters)
# - Remove unused imports
# - Add blank lines where required
```

**5. MyPy (Type Checking)**
```bash
# Issue: Type annotation problems
# Solutions:
# - Add type annotations: def func(param: str) -> int:
# - Use Union for multiple types: Union[str, None]
# - Import types: from typing import List, Dict, Optional
```

**6. File Length Check**
```bash
# Issue: File exceeds 400 lines
# Solution: Break into smaller modules
mkdir original_file/
# Move classes/functions to separate files
# Update imports
```

### Pre-commit Hook Details

The project uses these pre-commit hooks:
- **Gitleaks**: Secret detection
- **Bandit**: Python security linting
- **Black**: Python code formatting
- **Flake8**: Python linting (max line length: 120)
- **MyPy**: Type checking for staged files
- **Hadolint**: Dockerfile security
- **SQLFluff**: SQL formatting
- **File checks**: YAML, JSON, merge conflicts, large files

## 5. Testing Your Changes

### Backend Tests
```bash
# Run from backend directory
cd backend
python -m pytest tests/backend/integration/ -v

# Run specific test
python -m pytest tests/backend/integration/test_your_feature.py -v
```

### Frontend Tests
```bash
# E2E user journey tests
npm run test:e2e:journey

# Admin interface tests
npm run test:admin
```

### Manual Testing
1. Access frontend at http://localhost:8081
2. Test your changes through the UI
3. Check browser console for errors
4. Verify API responses in Network tab

## 6. Committing Changes

### Stage and Review Changes
```bash
# Stage specific files
git add path/to/your/file.py

# Review staged changes
git diff --staged

# Run pre-commit on staged files
pre-commit run
```

### Commit Message Format
Follow the established pattern from recent commits:
```bash
# Format: type: Brief description
git commit -m "fix: Collection flow resume attribute errors"
git commit -m "feat: Add comprehensive client-side validation"
git commit -m "refactor: Implement modular flow handlers"
```

**Commit Types:**
- `fix:` - Bug fixes
- `feat:` - New features
- `refactor:` - Code restructuring
- `style:` - Code formatting
- `docs:` - Documentation changes

### Code Review Check (Recommended)

Before committing, review code against common patterns:

```bash
# Check changed files against code review repository patterns
./scripts/pre-commit-code-review-check.sh

# Or check only staged files
./scripts/pre-commit-code-review-check.sh --staged
```

This helps catch common issues before PR review. See `docs/code-reviews/review-comments-repository.md` for full pattern list.

### Handling Pre-commit Failures
```bash
# If pre-commit fails, fix issues and re-stage
git add .
pre-commit run

# Only use --no-verify after fixing issues at least once
git commit --no-verify -m "fix: Emergency commit after pre-commit fixes"
```

## 7. Pushing to Git

### ⚠️ CRITICAL: Sync with Main First

**Always sync your branch with the latest `main` before pushing** to prevent merge conflicts and keep PRs clean.

**Recommended: Use the sync script (automatic):**
```bash
# Sync with main and push (recommended)
./scripts/sync-with-main.sh --push

# Or just sync without pushing
./scripts/sync-with-main.sh

# Or use the safe push wrapper
./scripts/git-safe-push.sh origin fix/your-descriptive-fix-name
```

**Manual sync (if needed):**
```bash
# Fetch latest main
git fetch origin main

# Rebase onto main
git pull origin main --rebase

# Push your branch
git push origin fix/your-descriptive-fix-name

# For first push of new branch
git push -u origin fix/your-descriptive-fix-name
```

**Why this matters:**
- Prevents merge conflicts in PRs
- Keeps PRs clean (no "merge main" commits)
- Ensures code is always based on latest main
- Required workflow for Cursor AI agent

See `scripts/README.md` for detailed documentation on the sync scripts.

## 8. Creating a GitHub PR

### Using GitHub CLI (Recommended)
```bash
# Install if not available: brew install gh
# Login: gh auth login

# Create PR
gh pr create --title "Fix: Collection flow resume errors" --body "
## Summary
- Fixed attribute errors in collection flow resume
- Updated flow state handling

## Test Plan
- [ ] Tested flow resume functionality
- [ ] Pre-commit checks pass
- [ ] E2E tests pass
"
```

### Using GitHub Web Interface
1. Go to repository on GitHub
2. Click "Compare & pull request" button
3. Fill out PR template:
   - Clear title describing the fix
   - Summary of changes made
   - Test plan with checkboxes
   - Link any related issues

### PR Best Practices
- **Keep PRs focused** - One fix per PR
- **Include test plan** - How you verified the fix works
- **Reference issues** - Use "Fixes #123" if applicable
- **Request reviews** - Tag relevant team members

## Common Troubleshooting

### Docker Issues
```bash
# Service won't start
docker-compose down
docker-compose up -d --build

# Database connection issues
docker exec -it migration_postgres psql -U postgres -l

# Clear everything and restart
docker-compose down -v
docker-compose up -d
```

### Pre-commit Issues
```bash
# Pre-commit hook not found
cd backend
pre-commit clean
pre-commit install

# MyPy issues with imports
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

### Git Issues
```bash
# Accidentally committed to main
git reset --soft HEAD~1
git checkout -b fix/your-fix-name
git commit

# Merge conflicts
git pull origin main
# Resolve conflicts in editor
git add .
git commit
```

## Quick Reference

### Essential Commands
```bash
# Start development
cd config/docker && docker-compose up -d

# Make changes, then test
pre-commit run
docker logs migration_backend -f

# Commit and push
git add .
git commit -m "fix: Your descriptive message"
git push origin your-branch-name

# Create PR
gh pr create --title "Your Title" --body "Description"
```

### Key File Locations
- Pre-commit config: `.pre-commit-config.yaml`
- Docker compose: `config/docker/docker-compose.yml`
- Backend code: `backend/app/`
- Frontend code: `src/`
- Database migrations: `backend/alembic/versions/`

### Important URLs (Development)
- Frontend: http://localhost:8081
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5433

Remember: Always develop in Docker, fix pre-commit issues before committing, and keep PRs focused and well-documented.