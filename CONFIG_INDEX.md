# Configuration Files Index

This document provides a complete index of all configuration files in the project and their new organized locations.

## Directory Structure

```
config/
├── database/           # Database related configurations
├── dependencies/       # Package and dependency configurations
├── deployment/         # Deployment platform configurations
├── docker/            # Docker and container configurations
└── tools/             # Development tool configurations

logs/                  # Log files
reports/              # Analysis and test reports
├── analysis/         # Code analysis reports
└── security/         # Security audit reports

test-data/            # Test data files and fixtures

scripts/              # Utility and maintenance scripts
├── analysis/         # Analysis and extraction scripts
├── maintenance/      # Cleanup and maintenance scripts
├── monitoring/       # Monitoring scripts
├── qa/              # Quality assurance scripts
├── security/        # Security audit scripts
└── setup/           # Setup and installation scripts
```

## Configuration Files by Category

### Docker & Container Configurations
**Location**: `/config/docker/`

- `docker-compose.yml` - Main development environment
- `docker-compose.dev.yml` - Development specific overrides
- `docker-compose.prod.yml` - Production environment
- `docker-compose.test.yml` - Test environment
- `docker-compose.staging.yml` - Staging environment
- `docker-compose.security.yml` - Security hardened environment
- `docker-compose.secure.yml` - Secure configuration variant
- `docker-compose.assessment-dev.yml` - Assessment development
- `docker-compose.deployment.yml` - Deployment configuration
- `docker-compose.frontend-fix.yml` - Frontend fix configuration
- `docker-compose.observability.yml` - Observability stack
- `docker-compose.override.yml` - Local development overrides

### Database Configurations
**Location**: `/config/database/`

- `alembic.ini` - Database migration configuration
- `db_schema.sql` - Database schema definitions
- `check_collection_flows.sql` - Database validation queries
- `redis.conf` - Redis cache configuration

### Dependency Management
**Location**: `/config/dependencies/`

- `requirements-docker.txt` - Docker container Python dependencies
- `requirements-dev.txt` - Development dependencies
- `requirements-docker-secure.txt` - Secure Docker dependencies
- `requirements-lint.txt` - Linting tool dependencies
- `requirements-secure-minimal.txt` - Minimal secure dependencies
- `requirements-secure.txt` - Secure production dependencies
- `requirements-security.txt` - Security-focused dependencies
- `requirements-types.txt` - Type checking dependencies
- `requirements-updated.txt` - Updated dependencies list
- `requirements.txt` - Main Python dependencies
- `package-secure.json` - Secure package configuration
- `package-updated.json` - Updated package configuration

### Development Tools
**Location**: `/config/tools/`

- `eslint.config.js` - ESLint linting configuration
- `postcss.config.js` - PostCSS processing configuration
- `tailwind.config.ts` - Tailwind CSS framework configuration
- `playwright.config.ts` - End-to-end testing configuration
- `vite.config.ts` - Vite build tool configuration
- `vitest.config.ts` - Vitest testing framework configuration
- `components.json` - UI components configuration
- `pyproject.toml` - Python project configuration
- `pyrightconfig.json` - Pyright type checker configuration
- `pytest.ini` - Pytest testing configuration
- `.prettierrc.json` - Prettier code formatter configuration

### Deployment Platform Configurations
**Location**: `/config/deployment/`

- `railway.toml` - Railway deployment configuration
- `vercel.json` - Vercel deployment configuration
- `railway.json` - Railway backend configuration
- `nixpacks.toml` - Nixpacks build configuration
- `.gitlab-ci.yml` - GitLab CI/CD pipeline configuration

### Root Level Configurations (Unchanged)
These remain in the root directory for tool discovery:

- `package.json` - Node.js package definition
- `package-lock.json` - Node.js dependency lock file
- `tsconfig.json` - TypeScript base configuration
- `tsconfig.app.json` - TypeScript application configuration
- `tsconfig.node.json` - TypeScript Node.js configuration

## Reports and Analysis
**Location**: `/reports/`

### Analysis Reports (`/reports/analysis/`)
- `comprehensive_git_metrics.json` - Git repository metrics
- `detailed_agent_info.json` - AI agent analysis information
- `detailed_line_stats.json` - Code line statistics
- `git_metrics_output.json` - Git metrics output data
- `feature_timeline.json` - Feature development timeline
- `key_features_timeline.json` - Key features timeline
- `modularization_analysis_report.json` - Code modularization analysis
- `foundation-validation-report.json` - Foundation validation results
- `eslint-output.json` - ESLint analysis results
- `ruff-report.txt` - Python Ruff linter report
- `dependency_graph.svg` - Project dependency visualization
- `backend_test_suites.txt` - Backend test suite information
- `auth_test_result.png` - Authentication test results
- `legacy-discovery-endpoints-audit.md` - Legacy endpoint audit

### Security Reports (`/reports/security/`)
- `bandit-report.json` - Python security analysis (root)
- `bandit_report.json` - Python security analysis (backend)
- `redis_security_audit_report.json` - Redis security audit (root)
- `redis_security_audit_report.json` - Redis security audit (backend)

## Logs
**Location**: `/logs/`

- `backend_log.txt` - Backend application logs (root)
- `backend_log.txt` - Backend application logs (backend copy)
- `backend.log` - Backend service logs
- `api_routes_error.log` - API routing error logs

## Test Data
**Location**: `/test-data/`

- `e2e-test-data.csv` - End-to-end test data
- `test-discovery-data.csv` - Discovery flow test data
- `test_data2.csv` - Additional test data
- `test_data_import.csv` - Data import test data
- `test_cmdb_import.csv` - CMDB import test data
- `test_marathon_upload.csv` - Marathon upload test data
- `test_api.json` - API test configuration
- `cookies.txt` - Test cookies data

## Reference Updates Required

When referencing configuration files in code or scripts, use these new paths:

### Docker Compose
```bash
# Old: docker-compose -f docker-compose.yml
# New: docker-compose -f config/docker/docker-compose.yml
```

### Tool Configurations
```bash
# Old: --config eslint.config.js
# New: --config config/tools/eslint.config.js
```

### Database Configurations
```bash
# Old: alembic -c alembic.ini
# New: alembic -c config/database/alembic.ini
```

## Scripts Updated

The following script has been created to help with reference updates:
- `/scripts/update_config_references.sh` - Updates file references in scripts

## Benefits of This Organization

1. **Clear Separation of Concerns**: Configuration types are grouped logically
2. **Reduced Root Clutter**: Root directory now focuses on essential project files
3. **Easier Maintenance**: Related configurations are co-located
4. **Better Documentation**: Clear structure aids in understanding project setup
5. **Improved Security**: Security reports and configs are properly grouped
6. **Enhanced Development**: Development tools configs are easily accessible
7. **Simplified Deployment**: Deployment configs are centralized

## Migration Notes

- All file moves preserve functionality
- Critical root-level configs remain for tool discovery
- References in key scripts have been updated
- Additional reference updates may be needed for some edge cases
