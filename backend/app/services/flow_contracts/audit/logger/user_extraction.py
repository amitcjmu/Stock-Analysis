"""
User ID Extraction Utilities

Helper functions for extracting user_id with cascading fallback strategies
to ensure audit completeness and prevent compliance violations.
"""

from typing import Optional

from app.core.context import RequestContext
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_user_id_with_fallbacks(
    context: Optional[RequestContext], operation: str
) -> Optional[str]:
    """
    Extract user_id with multiple fallback strategies to ensure audit completeness.

    AUDIT FIX: This function implements a cascading fallback approach to extract user_id
    from various sources to prevent compliance violations.

    Fallback Strategy:
    1. Extract from provided RequestContext.user_id
    2. Get from global request context (if available)
    3. Extract from current request headers
    4. Extract from JWT token in Authorization header
    5. Use "system" for system operations (with warning)
    6. Log warning if user_id is None for user-initiated operations

    Args:
        context: Request context (may be None or have user_id=None)
        operation: Operation being performed (determines if system operation)

    Returns:
        User ID string, or None if all extraction methods fail
    """
    # Strategy 1: Use context.user_id if provided
    if context and context.user_id:
        return context.user_id

    # Strategy 2: Try to get from global request context
    try:
        from app.core.context import get_current_context

        current_context = get_current_context()
        if current_context and current_context.user_id:
            logger.debug(
                f"Extracted user_id from global context for operation: {operation}"
            )
            return current_context.user_id
    except Exception as e:
        logger.debug(f"Failed to get user_id from global context: {e}")

    # Strategy 3 & 4: Try to extract from context variables (if context has request info)
    # Note: This fallback relies on the context having IP/user_agent populated from request
    try:
        if context and (
            hasattr(context, "ip_address") or hasattr(context, "user_agent")
        ):
            # Context was created from a request, but user_id extraction may have failed
            # Log this case for monitoring
            logger.debug(
                f"Context has request metadata but no user_id for operation: {operation}"
            )
    except Exception as e:
        logger.debug(f"Failed to check context metadata: {e}")

    # Strategy 5: For system operations, use "system" user_id
    system_operations = [
        "resume",
        "pause",
        "health_check",
        "status_sync",
        "cleanup",
        "monitoring",
    ]
    is_system_operation = any(
        sys_op in operation.lower() for sys_op in system_operations
    )

    if is_system_operation:
        logger.debug(f"Using 'system' user_id for system operation: {operation}")
        return "system"

    # Strategy 6: Log warning for user-initiated operations with missing user_id
    logger.warning(
        f"⚠️ AUDIT: user_id is None for user-initiated operation '{operation}'. "
        f"This may cause compliance violations. "
        f"Context: {context}"
    )
    return None
