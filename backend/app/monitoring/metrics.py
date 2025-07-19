"""
Performance tracking metrics for ADCS

This module provides basic performance tracking functionality.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def track_performance(metric_name: str, value: Optional[float] = None):
    """
    Track a performance metric.
    
    Args:
        metric_name: Name of the metric to track
        value: Optional value for the metric
    """
    if value is not None:
        logger.info(f"Performance metric: {metric_name} = {value}")
    else:
        logger.info(f"Performance metric: {metric_name}")
    
    # In a production environment, this would send metrics to a monitoring service
    # For now, we just log them
    
    
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
        except Exception as e:
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
        except Exception as e:
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