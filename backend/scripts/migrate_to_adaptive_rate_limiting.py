#!/usr/bin/env python3
"""
Migration script to transition from simple rate limiting to adaptive rate limiting.
This script helps configure and test the new adaptive rate limiting system.
"""

import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.middleware.adaptive_rate_limiter import AdaptiveRateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def display_configuration():
    """Display current adaptive rate limiter configuration."""
    limiter = AdaptiveRateLimiter()

    print("\n" + "=" * 60)
    print("ADAPTIVE RATE LIMITER CONFIGURATION")
    print("=" * 60)

    print("\n📊 Base Configurations:")
    print("-" * 40)
    for user_type, config in limiter.base_configs.items():
        print(f"\n{user_type.upper()}:")
        print(f"  • Capacity: {config['capacity']} tokens")
        print(f"  • Refill Rate: {config['refill_rate']} tokens/second")
        print(f"  • Burst Capacity: {config['burst_capacity']} tokens")
        print(
            f"  • Effective Max: {config['capacity'] + config['burst_capacity']} tokens"
        )
        print(f"  • Requests/minute: ~{int(config['refill_rate'] * 60)}")

    print("\n💰 Endpoint Costs:")
    print("-" * 40)
    for endpoint, cost in sorted(limiter.endpoint_costs.items()):
        if endpoint != "default":
            print(f"  • {endpoint}: {cost} tokens")
    print(f"  • default: {limiter.endpoint_costs['default']} token")

    print("\n🔍 Testing Patterns:")
    print("-" * 40)
    print(f"  {', '.join(limiter.testing_patterns)}")

    print("\n🏠 Development Indicators:")
    print("-" * 40)
    print(f"  {', '.join(limiter.dev_indicators)}")

    print("\n" + "=" * 60)


def compare_with_old_limits():
    """Compare new adaptive limits with old static limits."""
    print("\n📊 RATE LIMIT COMPARISON")
    print("=" * 60)

    old_limits = {
        "/api/v1/auth/login": {"limit": 5, "window": 60},
        "/api/v1/auth/register": {"limit": 3, "window": 60},
        "/api/v1/auth/password/change": {"limit": 3, "window": 300},
        "/api/v1/data-import/store-import": {"limit": 15, "window": 60},
        "/api/v1/data-import": {"limit": 60, "window": 60},
        "default": {"limit": 100, "window": 60},
    }

    limiter = AdaptiveRateLimiter()

    print("\n🔄 OLD (Static) vs NEW (Adaptive) Limits:")
    print("-" * 60)

    for endpoint, old_config in old_limits.items():
        old_rpm = old_config["limit"] * (60 / old_config["window"])

        # Calculate new effective limits
        cost = limiter._get_endpoint_cost(
            endpoint if endpoint != "default" else "/api/v1/test"
        )

        print(f"\n📍 {endpoint}:")
        print(
            f"  OLD: {old_config['limit']} requests per {old_config['window']}s = {old_rpm:.0f} rpm"
        )
        print(
            f"  NEW (Anonymous): {limiter.base_configs['anonymous']['capacity'] // cost} requests burst, "
            f"~{int(limiter.base_configs['anonymous']['refill_rate'] * 60 / cost)} rpm sustained"
        )
        print(
            f"  NEW (Authenticated): {limiter.base_configs['authenticated']['capacity'] // cost} requests burst, "
            f"~{int(limiter.base_configs['authenticated']['refill_rate'] * 60 / cost)} rpm sustained"
        )
        print(f"  Endpoint Cost: {cost} tokens")


def test_scenarios():
    """Test various rate limiting scenarios."""
    print("\n🧪 TESTING RATE LIMIT SCENARIOS")
    print("=" * 60)

    limiter = AdaptiveRateLimiter()

    # Scenario 1: Anonymous user hitting login endpoint
    print("\n1️⃣ Anonymous user attempting multiple logins:")
    client_key = "anon:192.168.1.1:test"
    endpoint = "/api/v1/auth/login"

    allowed_count = 0
    for i in range(20):
        allowed, info = limiter.is_allowed(client_key, endpoint)
        if allowed:
            allowed_count += 1
        else:
            print(f"   ❌ Rate limited after {allowed_count} attempts")
            print(f"   ⏱️  Retry after: {info['retry_after']} seconds")
            break

    limiter.reset_client(client_key)

    # Scenario 2: Authenticated user normal usage
    print("\n2️⃣ Authenticated user normal API usage:")
    client_key = "user:user123:192.168.1.1"
    endpoint = "/api/v1/some/endpoint"
    request_meta = {"user_id": "user123"}

    allowed_count = 0
    for i in range(250):
        allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
        if allowed:
            allowed_count += 1
        else:
            print(f"   ✅ Allowed {allowed_count} requests before rate limit")
            print(f"   📊 User type: {info['user_type']}")
            break

    limiter.reset_client(client_key)

    # Scenario 3: Testing environment
    print("\n3️⃣ Automated testing (Playwright):")
    client_key = "test:192.168.1.1:playwright"
    endpoint = "/api/v1/test/endpoint"
    request_meta = {"user_agent": "Playwright/1.0"}

    allowed_count = 0
    for i in range(600):
        allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
        if allowed:
            allowed_count += 1
        else:
            print(f"   ✅ Allowed {allowed_count} requests (testing mode)")
            print(f"   📊 User type: {info['user_type']}")
            break
    else:
        print(f"   ✅ All {allowed_count} requests allowed (testing mode)")
        print("   📊 User type detected: testing")

    limiter.reset_client(client_key)

    # Scenario 4: Development environment
    print("\n4️⃣ Development environment (localhost):")
    client_key = "dev:localhost:dev"
    endpoint = "/api/v1/dev/endpoint"
    request_meta = {"host": "localhost:8000"}

    allowed_count = 0
    for i in range(1000):
        allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
        if allowed:
            allowed_count += 1
        if i == 999:
            print(f"   ✅ All {allowed_count} requests allowed (dev mode)")
            print(f"   📊 User type detected: {info['user_type']}")


def generate_nginx_config():
    """Generate example Nginx configuration for rate limiting."""
    print("\n📝 NGINX CONFIGURATION EXAMPLE")
    print("=" * 60)
    print(
        """
# Add to nginx.conf for additional protection at reverse proxy level

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=upload:10m rate=15r/m;

# Apply rate limits to specific endpoints
location /api/v1/auth/login {
    limit_req zone=login burst=2 nodelay;
    limit_req_status 429;
    proxy_pass http://backend;
}

location /api/v1/data-import/store-import {
    limit_req zone=upload burst=5 nodelay;
    limit_req_status 429;
    proxy_pass http://backend;
}

location /api/v1/ {
    limit_req zone=api burst=20 nodelay;
    limit_req_status 429;
    proxy_pass http://backend;
}

# Add rate limit headers
add_header X-RateLimit-Limit $limit_req_limit always;
add_header X-RateLimit-Remaining $limit_req_remaining always;
add_header X-RateLimit-Reset $limit_req_reset always;
"""
    )


def main():
    """Main migration script."""
    print("\n🚀 ADAPTIVE RATE LIMITING MIGRATION TOOL")
    print("=" * 60)

    # Display current configuration
    display_configuration()

    # Compare with old limits
    compare_with_old_limits()

    # Test scenarios
    test_scenarios()

    # Generate Nginx config
    generate_nginx_config()

    print("\n✅ MIGRATION CHECKLIST")
    print("=" * 60)
    print(
        """
1. ✓ Review adaptive rate limiter configuration
2. ✓ Compare with existing rate limits
3. ✓ Test various user scenarios
4. ✓ Update main.py to use AdaptiveRateLimitMiddleware
5. ✓ Add admin endpoints for rate limit management
6. ✓ Configure Nginx for additional protection
7. □ Deploy to staging environment
8. □ Monitor rate limit metrics
9. □ Adjust configurations based on usage patterns
10. □ Deploy to production

📊 Monitoring Commands:
- Check rate limit stats: GET /api/v1/admin/rate-limit/stats
- Reset client limits: POST /api/v1/admin/rate-limit/reset/{client_key}
- Update configurations: PUT /api/v1/admin/rate-limit/config
- Clean up inactive: POST /api/v1/admin/rate-limit/cleanup

🔧 Testing Headers:
- Development: Host: localhost
- Testing: User-Agent: playwright, jest, selenium
- Custom: X-Test-Environment: true
"""
    )


if __name__ == "__main__":
    main()
