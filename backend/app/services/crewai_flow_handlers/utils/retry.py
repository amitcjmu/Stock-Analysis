"""
Retry decorator for async functions with exponential backoff.
"""

import asyncio
import functools
import logging
from typing import Type, TypeVar, Callable, Any, Optional

logger = logging.getLogger(__name__)
T = TypeVar('T')

def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator that adds retry behavior to async functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.warning(
                            f"Retry {attempt}/{max_retries} for {func.__name__} "
                            f"after error: {str(last_exception)}"
                        )
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate next delay with exponential backoff
                    sleep_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Retrying {func.__name__} in {sleep_time:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(sleep_time)
            
            # This should never be reached due to the raise above
            raise RuntimeError("Unexpected error in retry logic")
            
        return wrapper
    return decorator
