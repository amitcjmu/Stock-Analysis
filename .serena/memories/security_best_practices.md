# Security Best Practices

## JWT Token Validation
- Never trust unverified JWT payloads for security decisions
- Reject suspicious subjects: "system", "admin", "root", "service", "bot"
- Validate minimum subject length (≥3 characters)
- Check for service account patterns before trusting

## Secure Error Logging
- Use safe_log_format() for all error logging
- Log exception type only, not full message: `type(e).__name__`
- Never log raw exception messages that may contain sensitive data
- Example:
```python
logger.error(
    safe_log_format(
        "Operation failed: {error_type}",
        error_type=type(e).__name__
    )
)
```

## Authorization Header Normalization
- Handle case variations: "Bearer" vs "bearer"
- Strip extra spaces and validate structure
- Check for empty tokens after scheme
```python
normalized_header = auth_header.strip()
if not normalized_header.lower().startswith("bearer "):
    return None
parts = normalized_header.split()
if len(parts) != 2 or not parts[1]:
    return None
```

## Frontend Debug Logging Controls
- Gate all debug logs behind environment variables
- Truncate logged data to prevent leaks
- Never log per-item details in production
```typescript
const DEBUG_ENABLED = process.env.NODE_ENV !== 'production' &&
                      process.env.NEXT_PUBLIC_DEBUG_LOGS === 'true';
if (DEBUG_ENABLED) {
    const truncated = JSON.stringify(data).substring(0, 200) + '...[truncated]';
    console.log(message, truncated);
}
```

## Database Session Management
- Always use try/finally for cleanup
- Support both async and sync sessions
- Close generators to prevent connection leaks
- Validate sessions before use
