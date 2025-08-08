"""
Adaptive Rate Limiter using Token Bucket Algorithm
Implements intelligent rate limiting that adapts to user behavior and testing patterns.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting with adaptive capacity."""

    tokens: float
    last_refill: float
    capacity: int
    refill_rate: float  # tokens per second
    burst_capacity: int = 0  # additional burst capacity
    adaptive_multiplier: float = 1.0  # adaptive scaling factor

    def refill(self, current_time: float) -> None:
        """Refill tokens based on elapsed time."""
        elapsed = current_time - self.last_refill
        tokens_to_add = elapsed * self.refill_rate * self.adaptive_multiplier

        # Calculate effective capacity (base + burst)
        effective_capacity = self.capacity + self.burst_capacity

        self.tokens = min(effective_capacity, self.tokens + tokens_to_add)
        self.last_refill = current_time

    def consume(self, cost: int = 1) -> bool:
        """Consume tokens if available."""
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def time_until_tokens(self, needed: int = 1) -> float:
        """Calculate seconds until enough tokens are available."""
        if self.tokens >= needed:
            return 0

        tokens_needed = needed - self.tokens
        seconds_needed = tokens_needed / (self.refill_rate * self.adaptive_multiplier)
        return max(0, seconds_needed)


@dataclass
class UserContext:
    """Context information for a user/client."""

    user_id: Optional[str] = None
    is_authenticated: bool = False
    is_testing: bool = False
    is_development: bool = False
    request_history: list = field(default_factory=list)
    last_activity: float = field(default_factory=time.time)
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    total_requests: int = 0

    def update_activity(self, success: bool = True):
        """Update user activity metrics."""
        self.last_activity = time.time()
        self.total_requests += 1

        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        # Keep only recent history (last 100 requests)
        self.request_history.append(
            {"timestamp": self.last_activity, "success": success}
        )
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on user behavior and context.
    """

    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.user_contexts: Dict[str, UserContext] = defaultdict(UserContext)

        # Base configurations for different user types
        self.base_configs = {
            "anonymous": {
                "capacity": 50,
                "refill_rate": 5,  # 5 tokens per second = 300/min
                "burst_capacity": 10,
            },
            "authenticated": {
                "capacity": 200,
                "refill_rate": 20,  # 20 tokens per second = 1200/min
                "burst_capacity": 50,
            },
            "testing": {
                "capacity": 500,
                "refill_rate": 100,  # 100 tokens per second = 6000/min
                "burst_capacity": 200,
            },
            "development": {
                "capacity": 1000,
                "refill_rate": 1000,  # Essentially unlimited
                "burst_capacity": 1000,
            },
        }

        # Endpoint-specific cost configurations
        self.endpoint_costs = {
            "/api/v1/auth/login": 5,  # Higher cost for auth endpoints
            "/api/v1/auth/register": 10,
            "/api/v1/auth/password/change": 5,
            "/api/v1/data-import/store-import": 3,  # Moderate cost for uploads
            "/api/v1/unified-discovery/flow/initialize": 2,
            "default": 1,  # Default cost for most endpoints
        }

        # Testing pattern detection
        self.testing_patterns = [
            "test",
            "jest",
            "playwright",
            "cypress",
            "selenium",
            "automated",
            "e2e",
            "integration",
        ]

        # Development environment indicators
        self.dev_indicators = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",  # nosec B104 - String used for environment detection, not binding
            "dev",
            "development",
            "staging",
        ]

    def _get_bucket_key(self, client_key: str, endpoint: str) -> str:
        """Generate a unique bucket key for client+endpoint combination."""
        return f"{client_key}:{endpoint}"

    def _get_user_type(self, context: UserContext, request_meta: Dict[str, Any]) -> str:
        """Determine user type based on context and request metadata."""
        # Check for development environment
        if context.is_development or self._is_development_request(request_meta):
            return "development"

        # Check for testing patterns
        if context.is_testing or self._is_testing_request(request_meta):
            return "testing"

        # Check authentication status
        if context.is_authenticated:
            return "authenticated"

        return "anonymous"

    def _is_testing_request(self, request_meta: Dict[str, Any]) -> bool:
        """Detect if request is from automated testing."""
        user_agent = request_meta.get("user_agent", "").lower()
        referer = request_meta.get("referer", "").lower()

        # Check for testing patterns in headers
        for pattern in self.testing_patterns:
            if pattern in user_agent or pattern in referer:
                return True

        # Check for rapid sequential requests (common in tests)
        # This would be enhanced with request history analysis
        return False

    def _is_development_request(self, request_meta: Dict[str, Any]) -> bool:
        """Detect if request is from development environment."""
        host = request_meta.get("host", "").lower()
        origin = request_meta.get("origin", "").lower()

        for indicator in self.dev_indicators:
            if indicator in host or indicator in origin:
                return True

        return False

    def _get_endpoint_cost(self, endpoint: str) -> int:
        """Get the token cost for an endpoint."""
        # Check exact match first
        if endpoint in self.endpoint_costs:
            return self.endpoint_costs[endpoint]

        # Check prefix matches
        for pattern, cost in self.endpoint_costs.items():
            if pattern != "default" and endpoint.startswith(pattern):
                return cost

        return self.endpoint_costs["default"]

    def _calculate_adaptive_multiplier(self, context: UserContext) -> float:
        """
        Calculate adaptive multiplier based on user behavior.
        Good behavior gets bonus capacity, bad behavior gets reduced capacity.
        """
        multiplier = 1.0

        # Reward consistent good behavior
        if context.consecutive_successes > 50:
            multiplier *= 1.5
        elif context.consecutive_successes > 20:
            multiplier *= 1.2

        # Penalize consistent failures (might indicate abuse)
        if context.consecutive_failures > 10:
            multiplier *= 0.5
        elif context.consecutive_failures > 5:
            multiplier *= 0.8

        # Activity-based adjustment
        if context.total_requests > 1000:
            # Long-time user bonus
            multiplier *= 1.1

        return max(0.1, min(2.0, multiplier))  # Cap between 0.1x and 2x

    def _get_or_create_bucket(
        self, bucket_key: str, user_type: str, adaptive_multiplier: float
    ) -> TokenBucket:
        """Get existing bucket or create new one with appropriate config."""
        if bucket_key not in self.buckets:
            config = self.base_configs[user_type]
            self.buckets[bucket_key] = TokenBucket(
                tokens=config["capacity"],
                last_refill=time.time(),
                capacity=config["capacity"],
                refill_rate=config["refill_rate"],
                burst_capacity=config["burst_capacity"],
                adaptive_multiplier=adaptive_multiplier,
            )
        else:
            # Update adaptive multiplier for existing bucket
            self.buckets[bucket_key].adaptive_multiplier = adaptive_multiplier

        return self.buckets[bucket_key]

    def is_allowed(
        self,
        client_key: str,
        endpoint: str,
        request_meta: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request is allowed under adaptive rate limits.

        Returns:
            tuple: (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        request_meta = request_meta or {}

        # Get or create user context
        context = self.user_contexts[client_key]

        # Update context from request metadata
        context.user_id = request_meta.get("user_id", context.user_id)
        context.is_authenticated = bool(context.user_id)

        # Determine user type and calculate adaptive multiplier
        user_type = self._get_user_type(context, request_meta)
        adaptive_multiplier = self._calculate_adaptive_multiplier(context)

        # Get bucket and refill tokens
        bucket_key = self._get_bucket_key(client_key, endpoint)
        bucket = self._get_or_create_bucket(bucket_key, user_type, adaptive_multiplier)
        bucket.refill(current_time)

        # Get endpoint cost
        cost = self._get_endpoint_cost(endpoint)

        # Try to consume tokens
        allowed = bucket.consume(cost)

        # Update user context
        context.update_activity(success=allowed)

        # Prepare rate limit info
        rate_limit_info = {
            "limit": bucket.capacity,
            "remaining": int(bucket.tokens),
            "reset": int(current_time + bucket.time_until_tokens(bucket.capacity)),
            "retry_after": int(bucket.time_until_tokens(cost)) if not allowed else None,
            "user_type": user_type,
            "adaptive_multiplier": adaptive_multiplier,
            "endpoint_cost": cost,
        }

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_key} on {endpoint}",
                extra={
                    "client_key": client_key,
                    "endpoint": endpoint,
                    "user_type": user_type,
                    "cost": cost,
                    "tokens_remaining": bucket.tokens,
                },
            )

        return allowed, rate_limit_info

    def reset_client(self, client_key: str):
        """Reset rate limits for a specific client (useful for testing)."""
        # Remove all buckets for this client
        keys_to_remove = [k for k in self.buckets if k.startswith(f"{client_key}:")]
        for key in keys_to_remove:
            del self.buckets[key]

        # Reset user context
        if client_key in self.user_contexts:
            del self.user_contexts[client_key]

    def get_client_stats(self, client_key: str) -> Dict[str, Any]:
        """Get statistics for a specific client."""
        context = self.user_contexts.get(client_key)
        if not context:
            return {}

        client_buckets = {
            k: v for k, v in self.buckets.items() if k.startswith(f"{client_key}:")
        }

        return {
            "user_id": context.user_id,
            "is_authenticated": context.is_authenticated,
            "total_requests": context.total_requests,
            "consecutive_successes": context.consecutive_successes,
            "consecutive_failures": context.consecutive_failures,
            "last_activity": datetime.fromtimestamp(context.last_activity).isoformat(),
            "buckets": {
                k: {
                    "tokens": b.tokens,
                    "capacity": b.capacity,
                    "refill_rate": b.refill_rate,
                    "adaptive_multiplier": b.adaptive_multiplier,
                }
                for k, b in client_buckets.items()
            },
        }

    def cleanup_inactive(self, inactive_hours: int = 24):
        """Clean up data for inactive clients."""
        current_time = time.time()
        inactive_threshold = current_time - (inactive_hours * 3600)

        # Find inactive clients
        inactive_clients = [
            client_key
            for client_key, context in self.user_contexts.items()
            if context.last_activity < inactive_threshold
        ]

        # Clean up their data
        for client_key in inactive_clients:
            self.reset_client(client_key)

        if inactive_clients:
            logger.info(f"Cleaned up {len(inactive_clients)} inactive clients")


# Global adaptive rate limiter instance
adaptive_rate_limiter = AdaptiveRateLimiter()


def get_adaptive_rate_limiter() -> AdaptiveRateLimiter:
    """Get the global adaptive rate limiter instance."""
    return adaptive_rate_limiter
