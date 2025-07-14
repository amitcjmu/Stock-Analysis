"""
LLM Rate Limiter Service
Implements rate limiting for LLM API calls to prevent 429 errors.
Uses exponential backoff and request queuing.
"""

import asyncio
import time
import logging
from typing import Any, Dict, Optional, Callable
from collections import deque
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class LLMRateLimiter:
    """
    Rate limiter for LLM API calls with the following features:
    - Token bucket algorithm for rate limiting
    - Exponential backoff on 429 errors
    - Request queuing
    - Per-model rate limits
    """
    
    def __init__(self):
        # Rate limit configuration per model
        self.rate_limits = {
            "default": {
                "requests_per_minute": 20,  # Conservative default
                "requests_per_hour": 500,
                "burst_size": 5
            },
            "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": {
                "requests_per_minute": 30,
                "requests_per_hour": 1000,
                "burst_size": 10
            },
            "google/gemma-3-4b-it": {
                "requests_per_minute": 50,
                "requests_per_hour": 2000,
                "burst_size": 15
            }
        }
        
        # Token buckets for each model
        self.token_buckets = {}
        
        # Request queues
        self.request_queues = {}
        
        # Backoff state
        self.backoff_until = {}
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        
        # Initialize token buckets
        self._initialize_buckets()
    
    def _initialize_buckets(self):
        """Initialize token buckets for all models"""
        for model, limits in self.rate_limits.items():
            self.token_buckets[model] = {
                "tokens": limits["burst_size"],
                "max_tokens": limits["burst_size"],
                "refill_rate": limits["requests_per_minute"] / 60.0,  # tokens per second
                "last_refill": time.time()
            }
            self.request_queues[model] = deque()
            self.backoff_until[model] = 0
    
    def _get_model_key(self, model: str) -> str:
        """Get the rate limit key for a model"""
        # Extract base model name from full path
        if "/" in model:
            base_model = model.split("/")[-1]
            for key in self.rate_limits:
                if base_model in key:
                    return key
        return "default"
    
    def _refill_bucket(self, model_key: str):
        """Refill tokens in the bucket based on elapsed time"""
        bucket = self.token_buckets.get(model_key, self.token_buckets["default"])
        current_time = time.time()
        elapsed = current_time - bucket["last_refill"]
        
        # Calculate tokens to add
        tokens_to_add = elapsed * bucket["refill_rate"]
        bucket["tokens"] = min(bucket["tokens"] + tokens_to_add, bucket["max_tokens"])
        bucket["last_refill"] = current_time
    
    async def acquire_token(self, model: str, priority: int = 0) -> bool:
        """
        Acquire a token for making an LLM request.
        Returns True if token acquired, False if rate limited.
        """
        model_key = self._get_model_key(model)
        
        # Check if we're in backoff period
        if time.time() < self.backoff_until.get(model_key, 0):
            wait_time = self.backoff_until[model_key] - time.time()
            logger.warning(f"Rate limiter: In backoff period for {model_key}, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        # Refill bucket
        self._refill_bucket(model_key)
        
        bucket = self.token_buckets[model_key]
        
        # Try to acquire token
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            self.stats["total_requests"] += 1
            logger.debug(f"Rate limiter: Token acquired for {model_key}, {bucket['tokens']:.1f} tokens remaining")
            return True
        else:
            self.stats["rate_limited_requests"] += 1
            logger.warning(f"Rate limiter: No tokens available for {model_key}, request queued")
            
            # Calculate wait time until next token
            wait_time = 1.0 / bucket["refill_rate"]
            await asyncio.sleep(wait_time)
            
            # Try again after waiting
            return await self.acquire_token(model, priority)
    
    def handle_rate_limit_error(self, model: str, retry_after: Optional[float] = None):
        """
        Handle a 429 rate limit error from the API.
        Implements exponential backoff.
        """
        model_key = self._get_model_key(model)
        
        # Use retry_after if provided, otherwise use exponential backoff
        if retry_after:
            backoff_time = retry_after
        else:
            # Exponential backoff: 2^n seconds with jitter
            current_backoff = max(0, self.backoff_until.get(model_key, 0) - time.time())
            backoff_time = min(60, max(2, current_backoff * 2)) + random.uniform(0, 1)
        
        self.backoff_until[model_key] = time.time() + backoff_time
        
        # Reduce tokens to 0 to prevent immediate retries
        if model_key in self.token_buckets:
            self.token_buckets[model_key]["tokens"] = 0
        
        logger.warning(f"Rate limit hit for {model_key}, backing off for {backoff_time:.1f}s")
        self.stats["failed_requests"] += 1
    
    def record_success(self, model: str):
        """Record a successful request"""
        self.stats["successful_requests"] += 1
        
        # Reset backoff on success
        model_key = self._get_model_key(model)
        if model_key in self.backoff_until:
            self.backoff_until[model_key] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            **self.stats,
            "current_buckets": {
                model: {
                    "tokens": bucket["tokens"],
                    "max_tokens": bucket["max_tokens"],
                    "in_backoff": time.time() < self.backoff_until.get(model, 0)
                }
                for model, bucket in self.token_buckets.items()
            }
        }
    
    async def execute_with_rate_limit(
        self, 
        model: str, 
        func: Callable, 
        *args, 
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Execute a function with rate limiting and retry logic.
        
        Args:
            model: The model name for rate limiting
            func: The async function to execute
            *args: Arguments for the function
            max_retries: Maximum number of retries on rate limit
            **kwargs: Keyword arguments for the function
        
        Returns:
            The result of the function call
        """
        for attempt in range(max_retries):
            try:
                # Acquire token before making request
                await self.acquire_token(model)
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Record success
                self.record_success(model)
                
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                    # Extract retry-after if available
                    retry_after = None
                    if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            retry_after = float(retry_after)
                    
                    self.handle_rate_limit_error(model, retry_after)
                    
                    if attempt < max_retries - 1:
                        wait_time = self.backoff_until.get(self._get_model_key(model), 0) - time.time()
                        if wait_time > 0:
                            logger.info(f"Waiting {wait_time:.1f}s before retry attempt {attempt + 2}/{max_retries}")
                            await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries ({max_retries}) exceeded for {model}")
                        raise
                else:
                    # Not a rate limit error, re-raise
                    raise


# Global rate limiter instance
llm_rate_limiter = LLMRateLimiter()


# Convenience wrapper for LLM calls
async def rate_limited_llm_call(model: str, func: Callable, *args, **kwargs) -> Any:
    """
    Make a rate-limited LLM call.
    
    Args:
        model: The model name
        func: The LLM function to call
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        The result of the LLM call
    """
    return await llm_rate_limiter.execute_with_rate_limit(model, func, *args, **kwargs)