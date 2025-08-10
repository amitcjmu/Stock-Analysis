# Legacy Discovery Endpoint Cleanup - Architectural Decision

**Date**: August 10, 2025  
**Status**: Completed  

## Context

The platform had legacy `/api/v1/discovery/*` endpoint references scattered throughout the codebase after the core API endpoints were removed in commit `16522875b`. These references needed cleanup to prevent confusion and ensure consistency with the unified flow architecture.

## Decision

Remove all legacy discovery endpoint references and replace with unified `/api/v1/flows/*` endpoints while implementing automated policy enforcement to prevent regression.

## Implementation

### Configuration Changes
- **Cache Middleware**: Removed legacy discovery flows TTL configuration
- **RBAC Middleware**: Removed 3 legacy discovery endpoint references  
- **Agent Monitoring**: Updated 3 endpoint references to unified flows API
- **Main App**: Removed legacy discovery flow status from allowlist

### Policy Enforcement
- **Active Guardrails**: `scripts/policy-checks.sh` prevents legacy endpoint reintroduction
- **Pre-commit Integration**: Automated enforcement in development workflow
- **Installation Automation**: `scripts/install-policy-hooks.sh` for team consistency

### Security Enhancements
- **Database Credential Security**: Implemented secure `.pgpass` file handling in operational scripts
- **URL Parsing Security**: Replaced manual parsing with `urllib.parse` for robust handling
- **Runtime Safety**: Added defensive programming for API monitoring code

## Consequences

### Positive
- **Consistency**: All endpoint references now use unified flow architecture
- **Automated Enforcement**: Policy checks prevent regression automatically  
- **Security**: Enhanced credential handling in operational tools
- **Maintainability**: Cleaner codebase with focused enforcement mechanisms

### Trade-offs
- **Initial Setup**: Developers need to run `scripts/install-policy-hooks.sh` once
- **Operational Scripts**: Moved to `infrastructure/operations/` for proper separation

## Validation

- All policy checks pass: ✅
- System health maintained: ✅  
- Zero business impact: ✅
- Pre-commit hooks active: ✅
- Security vulnerabilities resolved: ✅

## Lessons Learned

1. **Active enforcement beats static documentation** - Policy checks prevent issues better than reports
2. **Security-first approach** - Credential handling must be secure from the start
3. **Defensive programming** - Runtime safety requires validation at all access points
4. **Clean separation** - Operational tools belong in infrastructure, not application code

## Rollback

If issues arise:
1. Legacy endpoint guard middleware can be temporarily disabled via `LEGACY_ENDPOINTS_ALLOW=1`
2. All changes are in version control with clear commit history
3. System health scripts validate platform status

## Enforcement Mechanisms

- **`scripts/policy-checks.sh`** - Validates no legacy endpoint usage
- **Pre-commit hooks** - Catches issues before commit
- **CI/CD integration** - Validates on pull requests
- **Guard middleware** - Blocks legacy traffic in production (410 Gone)