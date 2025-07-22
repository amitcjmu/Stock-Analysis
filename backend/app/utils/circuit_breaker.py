"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by stopping requests after consecutive failures.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately  
    - HALF_OPEN: Testing with limited requests
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func: Callable, *args, **kwargs):
        """Synchronous call through circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN for {self.name}")
                
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    async def async_call(self, func: Callable, *args, **kwargs):
        """Asynchronous call through circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔄 Circuit breaker {self.name} entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker is OPEN for {self.name}")
                
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try resetting"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
        
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"✅ Circuit breaker {self.name} recovered, closing circuit")
            
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"⚡ Circuit breaker {self.name} OPEN after {self.failure_count} failures"
            )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"⚡ Circuit breaker {self.name} reopened after test failure")
            
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "time_until_retry": max(
                0,
                self.recovery_timeout - (time.time() - (self.last_failure_time or 0))
            ) if self.state == CircuitState.OPEN else 0
        }
        
    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        logger.info(f"🔄 Circuit breaker {self.name} manually reset")


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception
            )
        return self.breakers[name]
        
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self.breakers.items()
        }
        
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
        logger.info("🔄 All circuit breakers reset")


# Global instance
circuit_breaker_manager = CircuitBreakerManager()