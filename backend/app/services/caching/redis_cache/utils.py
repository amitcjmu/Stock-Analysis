"""
Utility functions and decorators for Redis cache operations.

Provides fallback mechanisms and error handling for Redis operations.
"""

import json
from functools import wraps
from typing import Any, Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


def redis_fallback(func: Callable) -> Callable:
    """Decorator to handle Redis failures gracefully"""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.enabled or self.client is None:
            logger.debug(f"Redis disabled or unavailable, skipping {func.__name__}")
            return _get_fallback_result(func.__name__)

        try:
            return await func(self, *args, **kwargs)
        except (ConnectionError, TimeoutError) as e:
            # Network-related errors - likely Redis is down
            logger.warning(f"Redis connection error in {func.__name__}: {str(e)}")
            return _get_fallback_result(func.__name__)
        except (json.JSONDecodeError, ValueError) as e:
            # Data format errors - log but don't fail
            logger.error(f"Redis data error in {func.__name__}: {str(e)}")
            return _get_fallback_result(func.__name__)
        except Exception as e:
            # Unexpected errors - log with full details
            logger.error(
                f"Unexpected Redis error in {func.__name__}: {type(e).__name__}: {str(e)}"
            )
            return _get_fallback_result(func.__name__)

    return wrapper


def _get_fallback_result(operation_name: str) -> Any:
    """Get appropriate fallback value for a given operation"""
    # Read operations return None
    if operation_name in [
        "get",
        "get_flow_state",
        "get_import_sample",
        "get_mapping_pattern",
        "acquire_lock",
    ]:
        return None
    # Existence checks return False
    elif operation_name in ["exists"]:
        return False
    # IMPORTANT: When Redis is unavailable, allow flow registration to succeed
    # This prevents "flow already exists" errors when Redis is not configured
    elif operation_name in ["register_flow_atomic"]:
        logger.warning(
            "Redis unavailable - allowing flow registration without deduplication check"
        )
        return True
    # Write operations that should "succeed" silently
    elif operation_name in ["set", "delete", "release_lock", "unregister_flow_atomic"]:
        return True
    # List operations return empty list
    elif operation_name in ["get_active_flows", "get_sse_clients"]:
        return []
    # Default to False for unknown operations
    else:
        logger.warning(f"No fallback defined for operation: {operation_name}")
        return False
