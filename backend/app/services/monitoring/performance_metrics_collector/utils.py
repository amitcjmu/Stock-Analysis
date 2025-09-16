"""
Helper functions and decorators for performance metrics collection.

This module provides utility functions and decorators for automatic
performance tracking, including decorators for authentication and cache
operations monitoring.
"""

import asyncio
import time
from typing import Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


def track_auth_performance(operation_type: str = "login"):
    """Decorator to automatically track authentication performance"""

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from .collector import get_metrics_collector

            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()

                if operation_type == "login":
                    collector.record_auth_login_duration(duration, status)
                elif operation_type == "session_validation":
                    collector.record_session_validation_duration(duration, status)
                elif operation_type == "context_switch":
                    collector.record_context_switch_duration(duration, "client", status)

        async def async_wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from .collector import get_metrics_collector

            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()

                if operation_type == "login":
                    collector.record_auth_login_duration(duration, status)
                elif operation_type == "session_validation":
                    collector.record_session_validation_duration(duration, status)
                elif operation_type == "context_switch":
                    collector.record_context_switch_duration(duration, "client", status)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def track_cache_performance(operation: str = "get", cache_type: str = "redis"):
    """Decorator to automatically track cache performance"""

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from .collector import get_metrics_collector

            start_time = time.time()
            status = "success"
            result_type = "hit"
            try:
                result = func(*args, **kwargs)
                if result is None:
                    result_type = "miss"
                return result
            except Exception:
                status = "error"
                result_type = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()
                collector.record_cache_operation(
                    operation, duration, cache_type, status, result_type
                )

        async def async_wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from .collector import get_metrics_collector

            start_time = time.time()
            status = "success"
            result_type = "hit"
            try:
                result = await func(*args, **kwargs)
                if result is None:
                    result_type = "miss"
                return result
            except Exception:
                status = "error"
                result_type = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()
                collector.record_cache_operation(
                    operation, duration, cache_type, status, result_type
                )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
