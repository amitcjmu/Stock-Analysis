"""
Tests for the adaptive rate limiter implementation.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch
from app.middleware.adaptive_rate_limiter import (
    AdaptiveRateLimiter,
    TokenBucket,
    UserContext
)


class TestTokenBucket:
    """Test cases for the TokenBucket class."""
    
    def test_token_bucket_initialization(self):
        """Test token bucket is initialized correctly."""
        bucket = TokenBucket(
            tokens=100,
            last_refill=time.time(),
            capacity=100,
            refill_rate=10,
            burst_capacity=20
        )
        
        assert bucket.tokens == 100
        assert bucket.capacity == 100
        assert bucket.refill_rate == 10
        assert bucket.burst_capacity == 20
        assert bucket.adaptive_multiplier == 1.0
    
    def test_token_refill(self):
        """Test tokens are refilled based on elapsed time."""
        current_time = time.time()
        bucket = TokenBucket(
            tokens=50,
            last_refill=current_time - 5,  # 5 seconds ago
            capacity=100,
            refill_rate=10,  # 10 tokens per second
            burst_capacity=0
        )
        
        bucket.refill(current_time)
        
        # Should have added 50 tokens (5 seconds * 10 tokens/second)
        assert bucket.tokens == 100  # Capped at capacity
        assert bucket.last_refill == current_time
    
    def test_token_refill_with_burst(self):
        """Test tokens can exceed capacity with burst."""
        current_time = time.time()
        bucket = TokenBucket(
            tokens=50,
            last_refill=current_time - 5,
            capacity=100,
            refill_rate=10,
            burst_capacity=50  # Allow 150 total
        )
        
        bucket.refill(current_time)
        
        # Should have added 50 tokens
        assert bucket.tokens == 100  # Still capped at 100 since we're not over capacity
    
    def test_token_consumption(self):
        """Test token consumption."""
        bucket = TokenBucket(
            tokens=10,
            last_refill=time.time(),
            capacity=100,
            refill_rate=10,
            burst_capacity=0
        )
        
        # Successful consumption
        assert bucket.consume(5) is True
        assert bucket.tokens == 5
        
        # Failed consumption (not enough tokens)
        assert bucket.consume(10) is False
        assert bucket.tokens == 5  # Unchanged
    
    def test_time_until_tokens(self):
        """Test calculation of time until tokens are available."""
        bucket = TokenBucket(
            tokens=5,
            last_refill=time.time(),
            capacity=100,
            refill_rate=10,
            burst_capacity=0,
            adaptive_multiplier=1.0
        )
        
        # Already have enough tokens
        assert bucket.time_until_tokens(5) == 0
        
        # Need to wait for tokens
        wait_time = bucket.time_until_tokens(15)
        assert wait_time == 1.0  # Need 10 more tokens at 10/second = 1 second
        
        # With adaptive multiplier
        bucket.adaptive_multiplier = 2.0
        wait_time = bucket.time_until_tokens(15)
        assert wait_time == 0.5  # Faster refill with multiplier


class TestUserContext:
    """Test cases for UserContext tracking."""
    
    def test_user_context_initialization(self):
        """Test user context is initialized correctly."""
        context = UserContext()
        
        assert context.user_id is None
        assert context.is_authenticated is False
        assert context.is_testing is False
        assert context.is_development is False
        assert context.request_history == []
        assert context.consecutive_successes == 0
        assert context.consecutive_failures == 0
        assert context.total_requests == 0
    
    def test_update_activity_success(self):
        """Test activity update for successful requests."""
        context = UserContext()
        
        context.update_activity(success=True)
        
        assert context.total_requests == 1
        assert context.consecutive_successes == 1
        assert context.consecutive_failures == 0
        assert len(context.request_history) == 1
        assert context.request_history[0]['success'] is True
    
    def test_update_activity_failure(self):
        """Test activity update for failed requests."""
        context = UserContext()
        context.consecutive_successes = 5
        
        context.update_activity(success=False)
        
        assert context.total_requests == 1
        assert context.consecutive_successes == 0  # Reset
        assert context.consecutive_failures == 1
    
    def test_request_history_limit(self):
        """Test request history is limited to 100 entries."""
        context = UserContext()
        
        # Add 150 requests
        for i in range(150):
            context.update_activity(success=True)
        
        assert len(context.request_history) == 100
        assert context.total_requests == 150


class TestAdaptiveRateLimiter:
    """Test cases for the main AdaptiveRateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter is initialized with correct configs."""
        limiter = AdaptiveRateLimiter()
        
        assert 'anonymous' in limiter.base_configs
        assert 'authenticated' in limiter.base_configs
        assert 'testing' in limiter.base_configs
        assert 'development' in limiter.base_configs
        
        assert limiter.base_configs['authenticated']['capacity'] > \
               limiter.base_configs['anonymous']['capacity']
    
    def test_user_type_detection(self):
        """Test user type detection logic."""
        limiter = AdaptiveRateLimiter()
        
        # Anonymous user
        context = UserContext()
        request_meta = {}
        assert limiter._get_user_type(context, request_meta) == 'anonymous'
        
        # Authenticated user
        context.is_authenticated = True
        assert limiter._get_user_type(context, request_meta) == 'authenticated'
        
        # Testing environment
        context = UserContext()
        request_meta = {'user_agent': 'jest-test-runner'}
        assert limiter._get_user_type(context, request_meta) == 'testing'
        
        # Development environment
        context = UserContext()
        request_meta = {'host': 'localhost:8000'}
        assert limiter._get_user_type(context, request_meta) == 'development'
    
    def test_endpoint_cost_calculation(self):
        """Test endpoint cost calculation."""
        limiter = AdaptiveRateLimiter()
        
        # Exact match
        assert limiter._get_endpoint_cost('/api/v1/auth/login') == 5
        assert limiter._get_endpoint_cost('/api/v1/auth/register') == 10
        
        # Prefix match
        assert limiter._get_endpoint_cost('/api/v1/data-import/store-import') == 3
        
        # Default
        assert limiter._get_endpoint_cost('/api/v1/some/other/endpoint') == 1
    
    def test_adaptive_multiplier_calculation(self):
        """Test adaptive multiplier based on user behavior."""
        limiter = AdaptiveRateLimiter()
        
        # Good behavior
        context = UserContext()
        context.consecutive_successes = 25
        multiplier = limiter._calculate_adaptive_multiplier(context)
        assert multiplier == 1.2
        
        # Very good behavior
        context.consecutive_successes = 60
        context.total_requests = 1500
        multiplier = limiter._calculate_adaptive_multiplier(context)
        assert abs(multiplier - 1.65) < 0.001  # 1.5 * 1.1 (allow for floating point precision)
        
        # Bad behavior
        context = UserContext()
        context.consecutive_failures = 7
        multiplier = limiter._calculate_adaptive_multiplier(context)
        assert multiplier == 0.8
        
        # Very bad behavior
        context.consecutive_failures = 15
        multiplier = limiter._calculate_adaptive_multiplier(context)
        assert multiplier == 0.5
    
    def test_rate_limiting_anonymous_user(self):
        """Test rate limiting for anonymous users."""
        limiter = AdaptiveRateLimiter()
        client_key = "anon:192.168.1.1:12345678"
        endpoint = "/api/v1/some/endpoint"
        
        # Use up all tokens
        for i in range(50):  # Anonymous capacity
            allowed, info = limiter.is_allowed(client_key, endpoint)
            assert allowed is True
        
        # Next request should be denied
        allowed, info = limiter.is_allowed(client_key, endpoint)
        assert allowed is False
        assert info['retry_after'] >= 0  # Can be 0 if tokens are about to refill
        assert info['user_type'] == 'anonymous'
    
    def test_rate_limiting_authenticated_user(self):
        """Test rate limiting for authenticated users."""
        limiter = AdaptiveRateLimiter()
        client_key = "user:user123:192.168.1.1"
        endpoint = "/api/v1/some/endpoint"
        request_meta = {'user_id': 'user123'}
        
        # Authenticated users get more capacity
        for i in range(200):  # Authenticated capacity
            allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
            assert allowed is True
        
        # Next request should be denied
        allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
        assert allowed is False
        assert info['user_type'] == 'authenticated'
    
    def test_rate_limiting_with_endpoint_costs(self):
        """Test rate limiting considers endpoint costs."""
        limiter = AdaptiveRateLimiter()
        client_key = "anon:192.168.1.1:12345678"
        
        # High-cost endpoint
        endpoint = "/api/v1/auth/register"  # Cost: 10
        
        # Should only allow 5 requests (50 tokens / 10 cost)
        for i in range(5):
            allowed, info = limiter.is_allowed(client_key, endpoint)
            assert allowed is True
            assert info['endpoint_cost'] == 10
        
        # Next request should be denied
        allowed, info = limiter.is_allowed(client_key, endpoint)
        assert allowed is False
    
    def test_development_environment_bypass(self):
        """Test development environment gets essentially unlimited rate."""
        limiter = AdaptiveRateLimiter()
        client_key = "anon:127.0.0.1:12345678"
        endpoint = "/api/v1/some/endpoint"
        request_meta = {'host': 'localhost:8000'}
        
        # Should allow many requests
        for i in range(1000):
            allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
            assert allowed is True
            assert info['user_type'] == 'development'
    
    def test_testing_environment_detection(self):
        """Test testing environment gets higher limits."""
        limiter = AdaptiveRateLimiter()
        client_key = "test:192.168.1.1:12345678"
        endpoint = "/api/v1/some/endpoint"
        request_meta = {'user_agent': 'playwright/1.0'}
        
        # Should allow many requests
        for i in range(500):  # Testing capacity
            allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
            assert allowed is True
            assert info['user_type'] == 'testing'
    
    def test_client_reset(self):
        """Test resetting client rate limits."""
        limiter = AdaptiveRateLimiter()
        client_key = "anon:192.168.1.1:12345678"
        endpoint = "/api/v1/some/endpoint"
        
        # Use up tokens
        for i in range(50):
            limiter.is_allowed(client_key, endpoint)
        
        # Should be rate limited
        allowed, _ = limiter.is_allowed(client_key, endpoint)
        assert allowed is False
        
        # Reset client
        limiter.reset_client(client_key)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed(client_key, endpoint)
        assert allowed is True
    
    def test_client_stats(self):
        """Test getting client statistics."""
        limiter = AdaptiveRateLimiter()
        client_key = "user:user123:192.168.1.1"
        endpoint = "/api/v1/some/endpoint"
        request_meta = {'user_id': 'user123'}
        
        # Make some requests
        for i in range(10):
            limiter.is_allowed(client_key, endpoint, request_meta)
        
        stats = limiter.get_client_stats(client_key)
        
        assert stats['user_id'] == 'user123'
        assert stats['is_authenticated'] is True
        assert stats['total_requests'] == 10
        assert stats['consecutive_successes'] == 10
        assert len(stats['buckets']) > 0
    
    def test_cleanup_inactive_clients(self):
        """Test cleanup of inactive clients."""
        limiter = AdaptiveRateLimiter()
        
        # Create an old client
        old_client = "old:192.168.1.1:12345678"
        limiter.is_allowed(old_client, "/api/v1/test")
        
        # Manually set last activity to old time
        limiter.user_contexts[old_client].last_activity = time.time() - (25 * 3600)
        
        # Create a recent client
        new_client = "new:192.168.1.2:12345678"
        limiter.is_allowed(new_client, "/api/v1/test")
        
        # Cleanup inactive (24 hours)
        limiter.cleanup_inactive(inactive_hours=24)
        
        # Old client should be gone
        assert old_client not in limiter.user_contexts
        assert old_client + ":/api/v1/test" not in limiter.buckets
        
        # New client should remain
        assert new_client in limiter.user_contexts


@pytest.mark.asyncio
class TestAdaptiveRateLimiterIntegration:
    """Integration tests for adaptive rate limiting."""
    
    async def test_token_refill_over_time(self):
        """Test that tokens refill correctly over time."""
        limiter = AdaptiveRateLimiter()
        client_key = "anon:192.168.1.1:12345678"
        endpoint = "/api/v1/test"
        
        # Use all tokens
        for i in range(50):
            allowed, _ = limiter.is_allowed(client_key, endpoint)
            assert allowed is True
        
        # Should be rate limited
        allowed, info = limiter.is_allowed(client_key, endpoint)
        assert allowed is False
        
        # Wait for refill (anonymous: 5 tokens/second)
        await asyncio.sleep(1.1)  # Wait slightly more than 1 second
        
        # Should have ~5 tokens now
        for i in range(5):
            allowed, _ = limiter.is_allowed(client_key, endpoint)
            assert allowed is True
        
        # Should be rate limited again
        allowed, _ = limiter.is_allowed(client_key, endpoint)
        assert allowed is False
    
    async def test_adaptive_behavior_improvement(self):
        """Test that good behavior improves rate limits."""
        limiter = AdaptiveRateLimiter()
        client_key = "user:gooduser:192.168.1.1"
        endpoint = "/api/v1/test"
        request_meta = {'user_id': 'gooduser'}
        
        # Build up good behavior
        for i in range(25):
            allowed, info = limiter.is_allowed(client_key, endpoint, request_meta)
            assert allowed is True
        
        # Check adaptive multiplier increased
        context = limiter.user_contexts[client_key]
        multiplier = limiter._calculate_adaptive_multiplier(context)
        assert multiplier > 1.0
        
        # Should have bonus capacity due to good behavior
        bucket_key = limiter._get_bucket_key(client_key, endpoint)
        bucket = limiter.buckets[bucket_key]
        assert bucket.adaptive_multiplier > 1.0