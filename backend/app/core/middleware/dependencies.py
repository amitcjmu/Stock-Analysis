"""
Context-aware dependency functions for FastAPI endpoints.
Provides convenient dependency injection for request context validation.
"""

from ..context import RequestContext
from ..context_utils import validate_context


async def get_current_context_dependency() -> RequestContext:
    """
    FastAPI dependency for getting current request context.

    Returns:
        Current RequestContext

    Usage:
        @app.get("/api/data")
        async def get_data(context: RequestContext = Depends(get_current_context_dependency)):
            # Use context.client_account_id, etc.

    Note: This function is deprecated. Use get_current_context_dependency from app.core.context instead.
    """
    from ..context import get_current_context_dependency as context_dependency

    return await context_dependency()


def create_context_aware_dependency(
    require_client: bool = True, require_engagement: bool = False
):
    """
    Create a context dependency with specific requirements.

    Args:
        require_client: Whether client context is required
        require_engagement: Whether engagement context is required

    Returns:
        FastAPI dependency function

    Usage:
        require_engagement = create_context_aware_dependency(require_engagement=True)

        @app.get("/api/engagement-data")
        async def get_engagement_data(context: RequestContext = Depends(require_engagement)):
            # Context is guaranteed to have engagement_id
    """

    async def context_dependency() -> RequestContext:
        from ..context import get_current_context

        context = get_current_context()

        # Validate requirements
        validate_context(
            context,
            require_client=require_client,
            require_engagement=require_engagement,
        )

        return context

    return context_dependency
