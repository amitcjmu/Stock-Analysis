# Local Policy Enforcement

This document describes the local pre-commit policy enforcement system that replaces GitHub CI Actions for architectural rule validation.

## Overview

Due to GitHub Actions limits, we've implemented a comprehensive local policy enforcement system using pre-commit hooks. This ensures architectural rules are enforced at commit time rather than during CI.

## Quick Setup

```bash
# One-time setup
./scripts/install-policy-hooks.sh

# Manual policy check
./scripts/policy-checks.sh
```

## Policy Rules Enforced

### 1. Legacy Endpoint Detection
**Rule**: Block usage of `/api/v1/discovery/*` endpoints in application code

**Rationale**: Force migration to unified `/api/v1/flows` endpoints via Master Flow Orchestrator

**Scope**: `backend/app/**/*.py` (excluding tests, scripts)

**Example Violation**:
```python
# ❌ BLOCKED
response = requests.get(f"{base_url}/api/v1/discovery/flows")

# ✅ ALLOWED  
response = requests.get(f"{base_url}/api/v1/flows")
```

### 2. Deprecated Import Prevention
**Rule**: Block imports from deprecated repository base classes

**Rationale**: Enforce migration to async `ContextAwareRepository`

**Scope**: All backend Python files

**Example Violations**:
```python
# ❌ BLOCKED - Old sync base
from app.repositories.base import ContextAwareRepository

# ❌ BLOCKED - Tool-specific variant
from app.core.context_aware import ContextAwareRepository

# ✅ ALLOWED - Unified async base
from app.repositories.context_aware_repository import ContextAwareRepository
```

### 3. Sync/Async Database Pattern Validation
**Rule**: Prevent sync database patterns in async application code

**Rationale**: Maintain consistent async database usage

**Scope**: `backend/app/**/*.py`

**Example Violations**:
```python
# ❌ BLOCKED - Sync session in async code
session = SessionLocal()
result = session.query(Model).all()

# ✅ ALLOWED - Async patterns
async with AsyncSessionLocal() as session:
    result = await session.execute(select(Model))
```

### 4. Environment Flag Consistency
**Rule**: Ensure proper import patterns for environment flags

**Rationale**: Consistent flag usage across codebase

**Scope**: All Python files using `CREWAI_ENABLE_MEMORY` or `LEGACY_ENDPOINTS_ALLOW`

**Required Pattern**:
```python
from app.core.env_flags import is_truthy_env
enable_memory = is_truthy_env("CREWAI_ENABLE_MEMORY", default=False)
```

### 5. Unified Endpoint Validation
**Rule**: Monitor and report endpoint usage patterns

**Rationale**: Track migration progress from legacy to unified endpoints

**Scope**: API and frontend code

**Behavior**: Reports usage statistics, warns on high legacy usage

## Script Details

### `scripts/policy-checks.sh`
Main enforcement script with these functions:

- `check_legacy_endpoints()` - Scans for `/api/v1/discovery` usage
- `check_deprecated_imports()` - Validates repository import patterns  
- `check_sync_db_patterns()` - Detects sync database usage
- `check_env_flags()` - Validates environment flag imports
- `check_unified_endpoints()` - Reports endpoint usage statistics

### Staged File Intelligence
The script automatically detects if it's running in a git pre-commit context and only checks staged files for performance. When run manually, it checks all relevant files.

## Integration with Pre-Commit

The policy checks are integrated into `.pre-commit-config.yaml`:

```yaml
- id: policy-enforcement
  name: Enforce architectural policies
  entry: scripts/policy-checks.sh
  language: system
  pass_filenames: false
  stages: [pre-commit]
```

## Usage Scenarios

### Development Workflow
```bash
# Normal development - policies run automatically
git add .
git commit -m "feat: new feature"  # Policies run automatically

# Emergency bypass (use sparingly)
git commit --no-verify -m "hotfix: emergency change"
```

### Manual Validation
```bash
# Check current codebase
./scripts/policy-checks.sh

# Check only staged changes (faster)
git add changed-files.py
./scripts/policy-checks.sh  # Only checks staged files
```

### New Developer Onboarding
```bash
# One-time setup for new developers
./scripts/install-policy-hooks.sh
```

## Performance Characteristics

- **Fast**: Only checks staged files during commits
- **Selective**: Different patterns target appropriate file types
- **Informative**: Clear error messages with guidance
- **Non-blocking**: Warnings for advisory checks

## Troubleshooting

### ripgrep Not Found
```bash
# macOS
brew install ripgrep

# Ubuntu/Debian
apt install ripgrep

# Manual install
curl -LO https://github.com/BurntSushi/ripgrep/releases/download/13.0.0/ripgrep_13.0.0_amd64.deb
sudo dpkg -i ripgrep_13.0.0_amd64.deb
```

### Pre-commit Issues
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hooks
pre-commit autoupdate

# Run specific hook
pre-commit run policy-enforcement --all-files
```

### False Positives
If the policy checker flags valid code:

1. **Review the pattern**: Is the usage actually correct?
2. **Add exclusions**: Modify the script to exclude specific valid patterns
3. **Emergency bypass**: Use `git commit --no-verify` sparingly

## Advantages Over GitHub CI

1. **No API Limits**: Runs locally without GitHub Actions consumption
2. **Faster Feedback**: Immediate validation at commit time
3. **Offline Capable**: Works without internet connection
4. **Customizable**: Easy to modify rules and add new checks
5. **Portable**: Works across different development environments

## Future Enhancements

- **IDE Integration**: VS Code extension for real-time policy validation
- **Rule Configuration**: External config file for policy customization
- **Metrics Collection**: Track policy violation trends
- **Auto-fixes**: Automatic corrections for common violations