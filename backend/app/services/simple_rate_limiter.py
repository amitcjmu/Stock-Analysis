"""
Simple Synchronous Rate Limiter for LLM Calls
Implements basic rate limiting without async complexity.
"""

import time
import logging
from typing import Any, Dict, Optional, Callable
from threading import Lock
import random

logger = logging.getLogger(__name__)


class SimpleLLMRateLimiter:
    """
    Simple synchronous rate limiter for LLM API calls.
    Uses a token bucket algorithm with exponential backoff.
    """
    
    def __init__(self):
        self.lock = Lock()
        
        # Rate limit: 20 requests per minute (conservative)
        self.max_tokens = 20
        self.tokens = 20
        self.refill_rate = 20 / 60.0  # tokens per second
        self.last_refill = time.time()
        
        # Backoff state
        self.consecutive_429s = 0
        self.last_429_time = 0
        
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            
            self.tokens = min(self.tokens + tokens_to_add, self.max_tokens)
            self.last_refill = current_time
    
    def wait_for_token(self):
        """Wait until a token is available"""
        while True:
            self._refill_tokens()
            
            with self.lock:
                if self.tokens >= 1:
                    self.tokens -= 1
                    logger.debug(f"Rate limiter: Token acquired, {self.tokens:.1f} remaining")
                    
                    # Reset consecutive 429s on successful token acquisition
                    if time.time() - self.last_429_time > 60:
                        self.consecutive_429s = 0
                    return
                
            # Wait before checking again
            wait_time = 1.0 / self.refill_rate
            logger.debug(f"Rate limiter: Waiting {wait_time:.2f}s for token")
            time.sleep(wait_time)
    
    def handle_429_error(self):
        """Handle a 429 error with exponential backoff"""
        with self.lock:
            self.consecutive_429s += 1
            self.last_429_time = time.time()
            
            # Exponential backoff: 2^n seconds, max 60 seconds
            base_wait = min(60, 2 ** self.consecutive_429s)
            jitter = random.uniform(0, 1)
            wait_time = base_wait + jitter
            
            # Deplete all tokens to prevent immediate retries
            self.tokens = 0
            
        logger.warning(f"Rate limit hit! Waiting {wait_time:.1f}s (attempt {self.consecutive_429s})")
        time.sleep(wait_time)
    
    def reset_429_counter(self):
        """Reset the 429 counter after successful request"""
        with self.lock:
            self.consecutive_429s = 0


# Global rate limiter instance
simple_rate_limiter = SimpleLLMRateLimiter()


class RateLimitedLLMWrapper:
    """
    A simple wrapper that adds rate limiting to any LLM.
    """
    
    def __init__(self, base_llm):
        self.base_llm = base_llm
        self.rate_limiter = simple_rate_limiter
        
        # Copy attributes from base LLM
        for attr in ['model', 'temperature', 'max_tokens', 'base_url', 'api_key']:
            if hasattr(base_llm, attr):
                setattr(self, attr, getattr(base_llm, attr))
    
    def __call__(self, *args, **kwargs):
        """
        Rate-limited call to the LLM.
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Wait for rate limit token
                self.rate_limiter.wait_for_token()
                
                # Make the actual LLM call
                result = self.base_llm(*args, **kwargs)
                
                # Success - reset 429 counter
                self.rate_limiter.reset_429_counter()
                
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if any(indicator in error_str for indicator in ["429", "rate limit", "too many requests"]):
                    logger.warning(f"Received 429 error on attempt {attempt + 1}/{max_retries}")
                    
                    if attempt < max_retries - 1:
                        self.rate_limiter.handle_429_error()
                        continue
                    else:
                        logger.error("Max retries exceeded for rate-limited request")
                        raise
                else:
                    # Not a rate limit error, re-raise immediately
                    raise
    
    def __getattr__(self, name):
        """Delegate other attributes to base LLM"""
        return getattr(self.base_llm, name)


def add_simple_rate_limiting(llm):
    """
    Add simple rate limiting to an LLM instance.
    
    Args:
        llm: The base LLM instance
        
    Returns:
        A rate-limited version of the LLM
    """
    return RateLimitedLLMWrapper(llm)