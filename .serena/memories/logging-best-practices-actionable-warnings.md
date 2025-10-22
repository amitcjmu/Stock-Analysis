# Logging Best Practices - Actionable Warnings Only

## Problem
Module-level singleton initialization logged misleading "FALLBACK mode" warning during every backend startup, even though fallback was intentional and not an error.

```python
# Original warning (MISLEADING):
logger.warning("⚠️ 6R Decision Engine initialized in FALLBACK mode - no AI analysis available")
```

**User Feedback**: "ok then the warning should not be there if it doesnt provide reliable information back. Something needs to be logged only if its useful for us to help debug. In this case what's the value?"

## Solution: Context-Aware Logging Levels

### Pattern: Use Internal Flag to Suppress Expected Behavior
```python
def __init__(self, crewai_service=None, require_ai: bool = False,
             _warn_fallback: bool = True):
    """
    Args:
        _warn_fallback: If False, suppresses FALLBACK mode warning.
                       Use for module-level singletons where fallback is expected.
    """
    if CREWAI_AVAILABLE and crewai_service:
        self.ai_available = True
        logger.info("✅ Engine initialized in AI-POWERED mode")
    else:
        self.ai_available = False

        if require_ai:
            # FAIL-FAST for production where AI is required
            raise ValueError("AI required but not available")

        # Only warn if fallback is UNEXPECTED
        if _warn_fallback:
            logger.warning("⚠️ Engine in FALLBACK mode - no AI available")
        else:
            logger.debug("Engine in FALLBACK mode (expected for singleton)")

# Module-level singleton (fallback expected)
engine = Engine(crewai_service=None, _warn_fallback=False)

# Per-request instance (fallback unexpected)
service = AnalysisService(crewai_service=TenantScopedAgentPool, require_ai=True)
```

## Logging Level Guidelines

### ERROR - Action Required
```python
logger.error("Failed to process payment: {e}")  # ✅ Actionable
logger.error("AI service unavailable")           # ❌ If expected fallback
```

### WARNING - Attention Needed
```python
logger.warning("API rate limit approaching")     # ✅ Preventive action
logger.warning("Using fallback mode")            # ❌ If intentional design
```

### INFO - Important Events
```python
logger.info("✅ AI-powered analysis enabled")     # ✅ Configuration status
logger.info("Processing started")                 # ❌ Too verbose
```

### DEBUG - Development Details
```python
logger.debug("Using fallback mode (singleton)")   # ✅ Expected behavior
logger.debug("Cache miss for key: {key}")         # ✅ Performance tuning
```

## Anti-Patterns to Avoid

### ❌ Logging Expected Behavior as Warning
```python
# BAD - Warns about intentional design choice
logger.warning("Using default configuration")
```

### ❌ Logging Without Context
```python
# BAD - No indication why this matters
logger.warning("Fallback mode active")

# GOOD - Explains impact
logger.warning("AI analysis unavailable - using rule-based fallback")
```

### ❌ Always Logging at Same Level
```python
# BAD - Module import logs warning every time
engine = Engine()  # Logs WARNING even when expected

# GOOD - Different levels for different contexts
module_engine = Engine(_warn_fallback=False)      # DEBUG
request_engine = Engine(ai_service, require_ai=True)  # WARNING if fails
```

## Decision Tree
```
Is this expected behavior?
├─ YES → Use DEBUG level (or suppress)
└─ NO → Does it need action?
    ├─ YES, URGENT → ERROR
    ├─ YES, SOON → WARNING
    └─ NO → INFO
```

## Related Pattern
When same code runs in multiple contexts (module init, per-request), use context parameter to control logging verbosity.
