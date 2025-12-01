# Data-Driven Refactoring and Security Patterns

**Session Date**: January 2025
**Context**: PR #899 - Refactoring intelligent questionnaire options based on Qodo bot feedback

---

## Pattern 1: Data-Driven Refactoring (45% Code Reduction)

### Problem: If/Elif Chains Create Maintenance Burden

**Before** (205 lines, hard to extend):
```python
def get_dependencies_options(asset_context: Dict) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    architecture_pattern = (asset_context.get("architecture_pattern", "") or "").strip().lower()

    if architecture_pattern in ["monolithic", "monolith", "monolithic_application"]:
        options = [
            {"value": "minimal", "label": "Minimal - Standalone with no or few external dependencies"},
            {"value": "low", "label": "Low - Depends on 1-3 systems"},
            {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
            # ... 3 more options
        ]
        logger.info("Providing monolithic dependency options (minimal first)")
        return "select", options

    elif architecture_pattern in ["microservices", "microservices_architecture"]:
        options = [
            {"value": "high", "label": "High - Depends on 8-15 systems"},
            {"value": "very_high", "label": "Very High - Highly coupled with 16+ systems"},
            # ... 4 more options
        ]
        logger.info("Providing microservices dependency options (high first)")
        return "select", options

    # ... 5 more elif blocks (169 lines total)
```

### Solution: Dictionary-Based Configuration

**After** (113 lines, trivial to extend):
```python
# All possible options (reusable across patterns)
ALL_OPTIONS = {
    "minimal": {"value": "minimal", "label": "Minimal - Standalone with no or few external dependencies"},
    "low": {"value": "low", "label": "Low - Depends on 1-3 systems"},
    "moderate": {"value": "moderate", "label": "Moderate - Depends on 4-7 systems"},
    "high": {"value": "high", "label": "High - Depends on 8-15 systems"},
    "very_high": {"value": "very_high", "label": "Very High - Highly coupled with 16+ systems"},
    "unknown": {"value": "unknown", "label": "Unknown - Dependency analysis not yet performed"},
}

# Architecture-specific configurations (ordering + aliases)
ARCHITECTURE_CONFIG = {
    "monolithic": {
        "aliases": {"monolith", "monolithic_application"},
        "order": ["minimal", "low", "moderate", "high", "very_high", "unknown"],
        "log_message": "monolithic dependency options (minimal first)",
    },
    "microservices": {
        "aliases": {"microservices_architecture"},
        "order": ["high", "very_high", "moderate", "low", "minimal", "unknown"],
        "log_message": "microservices dependency options (high first)",
    },
    "soa_event_driven": {
        "aliases": {"soa", "service_oriented_architecture", "event_driven", "event-driven"},
        "order": ["moderate", "high", "very_high", "low", "minimal", "unknown"],
        "log_message": "SOA/Event-Driven dependency options (moderate first)",
    },
    # ... 4 more patterns
}

# Flat lookup map for O(1) pattern matching
PATTERN_MAP = {
    alias: key
    for key, config in ARCHITECTURE_CONFIG.items()
    for alias in config["aliases"] | {key}
}

def get_dependencies_options(asset_context: Dict) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    architecture_pattern = (asset_context.get("architecture_pattern", "") or "").strip().lower()
    config_key = PATTERN_MAP.get(architecture_pattern)

    if config_key:
        config = ARCHITECTURE_CONFIG[config_key]
        options = [ALL_OPTIONS[value] for value in config["order"]]
        logger.info(f"Providing {config['log_message']} for architecture_pattern: {architecture_pattern}")
        return "select", options

    return None
```

### Benefits
- **45% code reduction**: 205 lines → 113 lines
- **O(1) lookup**: `PATTERN_MAP` uses dictionary lookup instead of sequential if/elif
- **Single source of truth**: Option labels defined once in `ALL_OPTIONS`
- **Easy extension**: Add new pattern = 4 lines in `ARCHITECTURE_CONFIG`
- **Testability**: Configuration is data, not code logic

### When to Apply
- Functions with 3+ if/elif blocks checking similar conditions
- Repeated option lists with only ordering differences
- Pattern matching where aliases map to canonical keys
- Any code where Qodo bot suggests "consider data-driven design"

---

## Pattern 2: Dictionary Lookup Map for Aliases

### Problem: Multiple Aliases for Same Configuration

**Inefficient Approach**:
```python
if pattern in ["soa", "service_oriented_architecture", "service-oriented", "event_driven", "event-driven"]:
    # ... duplicate this check everywhere
```

### Solution: Flat Lookup Map

```python
# Build once at module load
PATTERN_MAP = {
    alias: key
    for key, config in ARCHITECTURE_CONFIG.items()
    for alias in config["aliases"] | {key}  # Include config key itself
}

# Result: {"soa": "soa_event_driven", "service_oriented_architecture": "soa_event_driven", ...}

# Use in function (O(1) lookup)
config_key = PATTERN_MAP.get(architecture_pattern)
if config_key:
    config = ARCHITECTURE_CONFIG[config_key]
```

### Benefits
- **O(1) lookup**: Dictionary lookup instead of O(n) list iteration
- **Single definition**: Aliases defined once in configuration
- **Self-documenting**: Clear mapping from alias to canonical key
- **Type safety**: No typos in repeated if/elif conditions

---

## Pattern 3: Security - .env.example Template Pattern

### Problem: Secrets in Git Repository

**WRONG** (Gitleaks will catch this):
```bash
# .env.observability committed to Git
GRAFANA_ADMIN_PASSWORD=***REDACTED***
POSTGRES_GRAFANA_PASSWORD=***REDACTED***
```

### Solution: Template File with Placeholders

**File**: `config/docker/.env.observability.example`
```bash
# Grafana Observability Stack Environment Variables
# Instructions:
#   1. Copy this file to .env.observability
#   2. Generate strong password: openssl rand -base64 32
#   3. Fill in all required values
#   4. NEVER commit .env.observability to git

# GRAFANA AUTHENTICATION (REQUIRED)
# Generate strong password (20+ chars):
# openssl rand -base64 32
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_GENERATE_WITH_OPENSSL

# POSTGRESQL (REQUIRED FOR LLM/MFO DASHBOARDS)
POSTGRES_GRAFANA_PASSWORD=CHANGE_ME_GENERATE_WITH_OPENSSL

# RETENTION POLICIES
LOKI_RETENTION_DAYS=14
TEMPO_RETENTION_DAYS=7
PROMETHEUS_RETENTION_DAYS=14
```

**File**: `config/docker/.gitignore`
```
# Observability environment file with secrets (DO NOT COMMIT)
.env.observability
```

### Benefits
- **Zero secrets in repository**: .gitignore prevents accidental commits
- **Clear setup instructions**: Users know exactly what to do
- **Security validation**: Gitleaks pre-commit hook catches violations
- **Documentation**: Example file shows all required variables

### When to Apply
- **ANY** file containing passwords, API keys, or tokens
- Configuration files for external services (Grafana, Prometheus, etc.)
- Database credentials for read-only users
- OAuth client secrets

---

## Pattern 4: Pre-commit Targeted Execution

### Problem: Unrelated Pre-commit Failures Block Your PR

**Scenario**: You modify `application_options.py` but pre-commit fails on 578 mypy errors in unrelated files like `performance_mixin.py`, `flow_management_mixin.py`.

### Solution: Run Pre-commit Only on Changed Files

```bash
# WRONG - Runs on all staged files (including unrelated changes)
cd backend && pre-commit run --all-files

# CORRECT - Runs only on specific changed files
cd backend && pre-commit run --files \
    app/services/ai_analysis/questionnaire_generator/tools/intelligent_options/application_options.py \
    app/services/ai_analysis/questionnaire_generator/tools/intelligent_options/__init__.py \
    app/services/ai_analysis/questionnaire_generator/tools/section_builders.py

# Or use git diff to automatically get changed files
cd backend && pre-commit run --files $(git diff --name-only --cached | grep '^app/')
```

### Benefits
- **Faster feedback**: Only checks files you actually changed
- **Avoid unrelated failures**: Don't get blocked by existing codebase issues
- **PR focus**: Validates your changes, not historical debt
- **CI alignment**: Many CI systems only check changed files

### When to Apply
- Large codebase with existing linting issues
- Adding new features to legacy code
- Refactoring specific modules
- Time-sensitive PRs where full codebase checks would delay

### Important Note
- Still run `pre-commit run --all-files` periodically (e.g., weekly) to catch drift
- Don't use this to bypass legitimate issues in your changes
- Document in PR if you intentionally skipped full checks

---

## Usage Guidelines

### Refactoring Checklist
Before converting if/elif to data-driven:
1. Do you have 3+ similar if/elif blocks?
2. Are the differences only in data (not logic)?
3. Would configuration be easier to test than code?
4. Would future engineers need to add new cases?

If yes to 2+, refactor to data-driven.

### Security Checklist
Before committing any config file:
1. Does it contain passwords, API keys, or tokens?
2. Run `git diff --cached` to review what you're committing
3. Look for base64 strings, long alphanumeric sequences
4. If suspicious, create .example file + add to .gitignore
5. Run `pre-commit` to let Gitleaks validate

### Pre-commit Strategy
- **Feature PRs**: Run on changed files only
- **Refactoring PRs**: Run on entire module being refactored
- **Security fixes**: Run --all-files to catch similar issues
- **Weekly maintenance**: Run --all-files on main branch

---

## Related Patterns
- **Qodo Bot Feedback Resolution**: See `qodo_bot_feedback_patterns.md`
- **Security Hardening**: See `security_hardening_patterns.md`
- **Pre-commit Troubleshooting**: See `precommit_troubleshooting_2025_01.md`
