"""
Performance tracking metrics for ADCS

This module provides basic performance tracking functionality.
"""

import logging
import time
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


def track_performance(metric_name: str):
    """
    Decorator to track performance metrics.
    
    Args:
        metric_name: Name of the metric to track
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                logger.info(f"Performance metric: {metric_name}")
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Performance metric: {metric_name} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Performance metric: {metric_name} failed after {execution_time:.3f}s - {str(e)}")
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                logger.info(f"Performance metric: {metric_name}")
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Performance metric: {metric_name} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Performance metric: {metric_name} failed after {execution_time:.3f}s - {str(e)}")
                raise
                
        # Return the appropriate wrapper based on whether the function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator
    
    
def track_execution_time(func: Callable) -> Callable:
    """
    Decorator to track execution time of a function.
    
    Args:
        func: Function to track
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            track_performance(f"{func.__name__}_execution_time", execution_time)
            return result
        except Exception:
            execution_time = time.time() - start_time
            track_performance(f"{func.__name__}_execution_time_error", execution_time)
            raise
            
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            track_performance(f"{func.__name__}_execution_time", execution_time)
            return result
        except Exception:
            execution_time = time.time() - start_time
            track_performance(f"{func.__name__}_execution_time_error", execution_time)
            raise
            
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
        

# Import asyncio for async detection
import asyncio