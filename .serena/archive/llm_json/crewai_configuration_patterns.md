# CrewAI Configuration Patterns

## Timeout Configuration
**CRITICAL**: Use configurable timeouts for complex AI operations

### Environment Variable Pattern
```python
import os

# Set timeout if not specified - Allow longer timeouts for complex analysis
if "max_execution_time" not in kwargs:
    # Default to 10 minutes, but allow override via environment variable
    default_timeout = int(os.getenv("CREWAI_TIMEOUT_SECONDS", "600"))
    kwargs["max_execution_time"] = default_timeout
    logger.info(f"⏱️ Setting CrewAI timeout to {default_timeout} seconds")
```

### Timeout Requirements by Agent Type
- **Basic agents**: 300 seconds (5 minutes)
- **Analysis agents**: 600 seconds (10 minutes)
- **Complex reasoning agents**: 1200 seconds (20 minutes)
- **Multi-step orchestration**: 1800 seconds (30 minutes)

### Common Issues and Fixes

#### Misleading Log Messages
**PROBLEM**: Log shows "15 seconds" but actual timeout is 300+ seconds
**CAUSE**: Hardcoded log message not reflecting actual timeout value
**FIX**: Use actual timeout value in log message
```python
# WRONG - Misleading log
logger.info("⏱️ Setting CrewAI timeout to 15 seconds")

# CORRECT - Accurate log
logger.info(f"⏱️ Setting CrewAI timeout to {default_timeout} seconds")
```

#### User Confusion Resolution
When users report timeout issues:
1. Check actual timeout value (not log message)
2. Verify environment variable configuration
3. Consider agent complexity requirements
4. Update both timeout and log message together

## Agent Memory Configuration
**PATTERN**: Use memory patches for external embedding services

```python
# Memory configuration with DeepInfra embeddings
memory_config = {
    "provider": "deepinfra",
    "model": "text-embedding-3-large",
    "dimensions": 1536
}
```

## Agent Pool Management
**PATTERN**: Async cleanup scheduling instead of threading

```python
# WRONG - Threading issues in async context
import threading
timer = threading.Timer(interval, cleanup_function)

# CORRECT - Async task scheduling
import asyncio
cleanup_task = asyncio.create_task(cleanup_scheduler_task())
```

## Error Handling Patterns
- Always log actual timeout values being used
- Provide fallback configurations for missing environment variables
- Use configurable defaults rather than hardcoded values
- Validate timeout values are reasonable for the operation type
