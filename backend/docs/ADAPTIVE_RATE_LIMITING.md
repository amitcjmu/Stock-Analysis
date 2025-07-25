# Adaptive Rate Limiting Implementation

This document describes the adaptive rate limiting system implemented to replace the aggressive static rate limiting that was causing 429 errors after just 5 requests.

## Overview

The new adaptive rate limiting system uses a **token bucket algorithm** with intelligent user behavior analysis to provide fair and flexible rate limiting that adapts to different user types and usage patterns.

## Key Features

### 1. Token Bucket Algorithm
- Each client gets a bucket with a certain capacity of tokens
- Tokens are consumed when making requests (different costs per endpoint)
- Tokens refill continuously at a configured rate
- Burst capacity allows temporary spikes in traffic

### 2. User Type Detection
The system automatically detects and categorizes users:

- **Anonymous Users**: Default rate limits for unauthenticated requests
- **Authenticated Users**: Higher limits for logged-in users
- **Testing Environment**: Very high limits for automated testing (Playwright, Jest, etc.)
- **Development Environment**: Essentially unlimited for localhost/development

### 3. Adaptive Behavior
The system adjusts rate limits based on user behavior:

- **Good Behavior Bonus**: Consistent successful requests increase capacity (up to 2x)
- **Bad Behavior Penalty**: Repeated failures reduce capacity (down to 0.1x)
- **Long-term User Bonus**: Users with history get slightly higher limits

### 4. Endpoint-Specific Costs
Different endpoints have different token costs:

- `/api/v1/auth/login`: 5 tokens (prevent brute force)
- `/api/v1/auth/register`: 10 tokens (prevent spam)
- `/api/v1/data-import/store-import`: 3 tokens (moderate cost)
- Default endpoints: 1 token

## Configuration

### Base Configurations

| User Type | Capacity | Refill Rate | Burst | Requests/min |
|-----------|----------|-------------|-------|--------------|
| Anonymous | 50 | 5/sec | 10 | ~300 |
| Authenticated | 200 | 20/sec | 50 | ~1200 |
| Testing | 500 | 100/sec | 200 | ~6000 |
| Development | 1000 | 1000/sec | 1000 | ~60000 |

### Comparison with Old Limits

| Endpoint | Old Limit | New (Anonymous) | New (Authenticated) |
|----------|-----------|-----------------|---------------------|
| Login | 5/min | 60/min | 240/min |
| Register | 3/min | 30/min | 120/min |
| Upload | 15/min | 100/min | 400/min |
| Default | 100/min | 300/min | 1200/min |

## Implementation Details

### Middleware Integration
```python
# In main.py
from app.middleware.adaptive_rate_limit_middleware import AdaptiveRateLimitMiddleware
app.add_middleware(AdaptiveRateLimitMiddleware)
```

### Client Identification
Clients are identified by a combination of:
- IP address
- User agent hash
- Authenticated user ID (if available)

### Rate Limit Headers
All responses include rate limit information:
- `X-RateLimit-Limit`: Token bucket capacity
- `X-RateLimit-Remaining`: Tokens remaining
- `X-RateLimit-Reset`: Unix timestamp when bucket refills
- `X-RateLimit-UserType`: Detected user type
- `Retry-After`: Seconds to wait (on 429 responses)

## Admin Management

### Endpoints

#### Get Rate Limit Stats
```bash
GET /api/v1/admin/rate-limit/stats
GET /api/v1/admin/rate-limit/stats?client_key=user:123:192.168.1.1
```

#### Reset Client Limits
```bash
POST /api/v1/admin/rate-limit/reset/{client_key}
```

#### Update Configuration
```bash
PUT /api/v1/admin/rate-limit/config?user_type=authenticated&capacity=300
```

#### Cleanup Inactive Clients
```bash
POST /api/v1/admin/rate-limit/cleanup?inactive_hours=24
```

#### Update Endpoint Cost
```bash
PUT /api/v1/admin/rate-limit/endpoint-cost?endpoint=/api/v1/special&cost=5
```

## Testing Mode Detection

The system automatically detects testing environments by looking for:

### User Agent Patterns
- `jest`, `playwright`, `cypress`, `selenium`
- `automated`, `e2e`, `integration`

### Host Patterns
- `localhost`, `127.0.0.1`, `0.0.0.0`
- `dev`, `development`, `staging`

### Custom Headers
- `X-Test-Environment: true`
- `X-Automated-Test: true`

## Migration Guide

1. **Update main.py**: Replace `RateLimitMiddleware` with `AdaptiveRateLimitMiddleware`
2. **Run migration script**: `docker exec migration_backend python scripts/migrate_to_adaptive_rate_limiting.py`
3. **Test in staging**: Verify rate limits work as expected
4. **Monitor metrics**: Use admin endpoints to track usage
5. **Adjust configs**: Fine-tune based on real usage patterns

## Best Practices

### For Developers
- Add `Host: localhost` header in development
- Use appropriate user agents for testing tools
- Include authentication tokens for higher limits

### For Testing
- Automated tests are automatically detected and given higher limits
- Add `X-Test-Environment: true` header if detection fails
- Use the admin reset endpoint between test runs if needed

### For Production
- Monitor rate limit metrics regularly
- Adjust configurations based on usage patterns
- Consider implementing caching to reduce API calls
- Use Nginx rate limiting as an additional layer

## Troubleshooting

### Common Issues

1. **Still getting 429 errors**
   - Check if you're authenticated (higher limits)
   - Verify endpoint costs aren't too high
   - Check adaptive multiplier (bad behavior penalty?)

2. **Testing failing due to rate limits**
   - Ensure test user agent is detected
   - Add test environment headers
   - Use admin endpoints to reset limits

3. **Development being rate limited**
   - Verify localhost/127.0.0.1 is being used
   - Check development environment detection
   - Use admin endpoints to update config

### Debug Information

Enable debug logging to see rate limit decisions:
```python
import logging
logging.getLogger('app.middleware.adaptive_rate_limiter').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Redis Backend**: Store rate limit state in Redis for distributed systems
2. **Machine Learning**: Use ML to detect and adapt to usage patterns
3. **Geographic Awareness**: Different limits based on geographic location
4. **API Key Support**: Per-API-key rate limits for partners
5. **Webhook Notifications**: Alert when users hit rate limits frequently
