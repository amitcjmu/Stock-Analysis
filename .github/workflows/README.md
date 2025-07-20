# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated CI/CD, security, and quality checks.

## Workflows Overview

### 🔄 CI Pipeline (`ci.yml`)
**Triggers**: Push to main/develop, Pull Requests
**Purpose**: Continuous Integration pipeline with comprehensive checks

**Jobs**:
- **Frontend Checks**: ESLint, TypeScript check, Build validation
- **Backend Checks**: Python tests, Security scans (Bandit, Safety)
- **Docker Build**: Validate Docker images can be built
- **Code Quality**: Black, isort, flake8, secret scanning

### 🛡️ Security Checks (`security.yml`)
**Triggers**: Push, Pull Requests, Daily schedule (2 AM UTC)
**Purpose**: Comprehensive security scanning and vulnerability detection

**Jobs**:
- **Dependency Scan**: NPM audit, Python safety checks
- **Code Security**: Bandit, Semgrep, hardcoded secret detection
- **Docker Security**: Trivy container vulnerability scanning
- **Security Summary**: Consolidated security reporting

### 🚀 Deployment Check (`deployment-check.yml`)
**Triggers**: Pull Requests to main, Push to main
**Purpose**: Validate deployment readiness and configuration

**Jobs**:
- **Deployment Validation**: Docker Compose validation, environment checks
- **Integration Test**: Full stack testing with services
- **Readiness Summary**: Deployment readiness assessment

### 📝 Pull Request Checks (`pull-request.yml`)
**Triggers**: Pull Request events (open, sync, reopen)
**Purpose**: Automated PR validation and quality gates

**Jobs**:
- **PR Validation**: Title format, description checks, change analysis
- **Code Quality Gate**: Linting, type checking with relaxed rules for existing codebase
- **Security Check**: Basic security validation
- **Test Execution**: Smoke tests and critical functionality
- **PR Summary**: Consolidated merge recommendation

### 📦 Dependency Updates (`dependency-update.yml`)
**Triggers**: Weekly schedule (Mondays 9 AM UTC), Manual dispatch
**Purpose**: Monitor and report on dependency updates and security issues

**Jobs**:
- **Dependency Check**: NPM and Python package updates
- **Security Audit**: Vulnerability scanning
- **Report Generation**: Comprehensive dependency and security report

## Configuration Notes

### ESLint Warnings
The workflows are configured with relaxed ESLint rules to accommodate the existing codebase:
- CI Pipeline: `--max-warnings 100`
- PR Checks: `--max-warnings 200`

This allows for gradual improvement without blocking development.

### Security Scanning
Security checks are designed to be informative rather than blocking:
- Reports warnings and issues
- Generates artifacts for review
- Creates actionable summaries

### Test Strategy
- **Smoke Tests**: Basic functionality validation
- **Integration Tests**: Database and service connectivity
- **Non-blocking**: Tests report issues but don't always fail the pipeline

## Artifacts Generated

Each workflow generates artifacts that can be downloaded from the GitHub Actions interface:

- **Security Reports**: Bandit, Safety, Trivy scan results
- **Test Results**: Test execution logs and coverage
- **Quality Reports**: ESLint, TypeScript, and Python linting results
- **Deployment Summaries**: Readiness assessments
- **Dependency Reports**: Update and vulnerability information

## Customization

### Adding New Checks
To add new quality or security checks:
1. Edit the appropriate workflow file
2. Add new steps or jobs
3. Update the summary generation logic
4. Test with a PR

### Adjusting Thresholds
To modify warning thresholds or failure conditions:
1. Update the relevant step parameters
2. Modify the summary logic in PR checks
3. Consider backward compatibility

### Environment Variables
Some workflows use environment variables that may need configuration:
- `DATABASE_URL`: Test database connection
- `REDIS_URL`: Redis connection for testing
- Custom application environment variables

## Usage Examples

### Running Workflows Locally
While workflows are designed for GitHub Actions, you can run similar checks locally:

```bash
# Frontend checks
npm run lint
npm run typecheck
npm run build

# Backend checks
cd backend
python -m pytest tests/test_smoke.py
bandit -r app/
safety check

# Docker validation
docker-compose config
docker build -t test-backend -f backend/Dockerfile ./backend
```

### Manual Workflow Dispatch
Some workflows support manual triggering:
1. Go to Actions tab in GitHub
2. Select the workflow
3. Click "Run workflow"
4. Choose branch and parameters

## Troubleshooting

### Common Issues
1. **ESLint Failures**: Review the error count and consider adjusting max-warnings
2. **Security Issues**: Review artifacts for specific vulnerabilities
3. **Docker Build Failures**: Check Dockerfile syntax and dependencies
4. **Test Failures**: Review test logs in artifacts

### Getting Help
- Check workflow logs in the GitHub Actions interface
- Review generated artifacts for detailed reports
- Check this README for configuration details
- Refer to individual workflow files for specific implementation details