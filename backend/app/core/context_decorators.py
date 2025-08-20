"""
Context management decorators and utilities.
Extracted from context.py to reduce file size and complexity.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar

# Import context functions to avoid circular imports
from app.core.context import (
    RequestContext,
    _request_context,
    get_current_context,
    get_required_context,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _create_test_context(
    func_name: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    **extra_fields,
) -> RequestContext:
    """Create a test context for decorators."""
    return RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        request_id=f"test-{func_name}",
        **extra_fields,
    )


def require_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that ensures context is available"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_current_context()
        if not context:
            raise RuntimeError(f"Context required for {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def inject_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that injects context as first argument"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_required_context()
        return func(context, *args, **kwargs)

    return wrapper


def with_context(
    client_account_id: str, engagement_id: str, user_id: str, **extra_fields
):
    """Decorator to run function with specific context"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = _create_test_context(
                func.__name__, client_account_id, engagement_id, user_id, **extra_fields
            )
            token = _request_context.set(context)
            try:
                return await func(*args, **kwargs)
            finally:
                _request_context.reset(token)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = _create_test_context(
                func.__name__, client_account_id, engagement_id, user_id, **extra_fields
            )
            token = _request_context.set(context)
            try:
                return func(*args, **kwargs)
            finally:
                _request_context.reset(token)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Context propagation for async tasks
class ContextTask:
    """Wrapper for asyncio tasks that preserves context"""

    @staticmethod
    def create_task(coro, *, name=None):
        """Create task that preserves current context"""
        from app.core.context import set_request_context, clear_request_context

        context = get_current_context()

        async def wrapped():
            if context:
                set_request_context(context)
            try:
                return await coro
            finally:
                if context:
                    clear_request_context()

        return asyncio.create_task(wrapped(), name=name)
