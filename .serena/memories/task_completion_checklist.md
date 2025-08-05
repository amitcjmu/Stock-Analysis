# Task Completion Checklist

## Required Steps After Completing Any Development Task

### 1. Code Quality Checks
```bash
# Frontend linting and type checking
npm run lint                    # Must pass with 0 warnings for production
npm run typecheck              # TypeScript compilation check

# Backend linting and formatting
black backend/                  # Code formatting
flake8 backend/                # Python linting
mypy backend/ --ignore-missing-imports  # Type checking
bandit -r backend/ -ll         # Security scanning
```

### 2. Testing Requirements
```bash
# Run relevant tests based on changes
npm run test                   # Frontend unit tests
npm run test:e2e              # E2E tests if UI changes
python -m pytest tests/ -v    # Backend tests

# For AI agent changes
npm run test:backend:agents    # Test agent functionality

# For integration changes
npm run test:backend:integration  # Integration tests
npm run test:complete         # Full test suite
```

### 3. Pre-commit Compliance
```bash
# Pre-commit hooks must pass
git add .
git commit -m "description"   # Pre-commit runs automatically

# If pre-commit fails, fix issues and recommit
# Never use --no-verify unless pre-commit has been run at least once
```

### 4. Container Health Verification
```bash
# Ensure all services are healthy
docker-compose ps             # Check service status
curl http://localhost:8000/health     # Backend health
curl http://localhost:8081            # Frontend health
curl http://localhost:8000/api/v1/monitoring/agents  # Agent status
```

### 5. Database Migration Checks
```bash
# If database changes were made
python -m alembic upgrade head        # Apply migrations
python -m alembic current            # Verify current state

# Ensure migrations are idempotent and reversible
python -m alembic downgrade -1       # Test rollback
python -m alembic upgrade head       # Re-apply
```

### 6. Security Validation
```bash
# Security checks must pass
bandit -r backend/ -ll               # Python security
npm audit                           # Node.js dependency audit

# Check for sensitive data
grep -r "password\|secret\|token" --exclude-dir=node_modules .
```

### 7. Performance Verification
```bash
# For AI agent changes, verify performance
curl http://localhost:8000/api/v1/monitoring/agents/performance

# Check logs for performance issues
docker-compose logs backend | grep -i "slow\|timeout\|error"
```

### 8. Documentation Updates
- Update relevant documentation if APIs changed
- Update type definitions if data structures changed
- Update CHANGELOG.md for significant changes
- Update README.md if setup process changed

### 9. Environment Compatibility
```bash
# Ensure changes work in container environment
docker-compose down
docker-compose up -d --build
# Test core functionality after rebuild
```

### 10. Final Verification Checklist
- [ ] All linting passes without warnings
- [ ] All tests pass
- [ ] Pre-commit hooks pass
- [ ] Container services are healthy
- [ ] No sensitive data exposed
- [ ] Database migrations work correctly
- [ ] Performance is acceptable
- [ ] Documentation is updated
- [ ] Changes work in container environment

## Never Skip These Steps
1. **Pre-commit checks** - Required for security and quality
2. **Container testing** - All development must work in containers
3. **Type checking** - TypeScript compilation must succeed
4. **Agent testing** - If AI agents are modified, test agent functionality

## Platform-Specific Notes
- Use `/opt/homebrew/bin/python3.11` for Python execution on macOS
- Use `/opt/homebrew/bin/gh` for GitHub CLI operations
- All development happens in Docker containers, never run services locally
