# Disabled Workflows

These workflows have been disabled to conserve GitHub Actions minutes. They can be re-enabled when needed or when Actions quota is available.

## How to Disable/Enable Workflows

### To Disable a workflow:
Rename the file from `workflow.yml` to `workflow.yml.disabled`

### To Enable a workflow:
Rename the file from `workflow.yml.disabled` back to `workflow.yml`

## Currently Disabled Workflows

The following resource-intensive workflows should be disabled:

1. **ci.yml** - Full CI pipeline with extensive testing
2. **deployment-check.yml** - Deployment validation (7KB file)
3. **phase1-tests.yml** - Comprehensive test suite (13KB file)
4. **pull-request.yml** - Heavy PR validation (10KB file)
5. **redis-infrastructure-ci.yml** - Redis-specific tests (20KB file)
6. **redis-security.yml** - Redis security scanning (14KB file)
7. **security.yml** - Full security scanning suite
8. **merge-guardian.yml** - Merge protection checks
9. **enforce-pr-workflow.yml** - PR enforcement rules

## Workflows to Keep Active

1. **essential-pr-checks.yml** - Lightweight essential checks (NEW)
2. **enforce-policies.yml** - Simple policy checks (1.2KB - lightweight)

## Alternative Solutions

1. **Self-hosted runners**: Set up your own runners to avoid GitHub Actions limits
2. **GitHub Actions paid plan**: Upgrade to get more minutes
3. **Local pre-commit hooks**: Run checks locally before pushing
4. **External CI/CD**: Use Jenkins, GitLab CI, or CircleCI

## Local Testing Commands

Instead of relying on GitHub Actions, run these locally:

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
npm test
npm run type-check

# Security scan
pip install bandit
bandit -r backend/

# Docker build test
docker-compose -f config/docker/docker-compose.yml build
```
