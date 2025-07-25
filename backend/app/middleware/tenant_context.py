"""
Tenant Context Middleware for Row-Level Security

This middleware sets the PostgreSQL session context with the current tenant's
client_account_id to enable Row-Level Security policies.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.database import get_db

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set tenant context for Row-Level Security.

    This middleware extracts the client_account_id from the request
    (either from user context or request state) and sets it in the
    PostgreSQL session configuration for RLS policies to use.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and set tenant context"""
        client_id = None

        try:
            # Try to get client_account_id from various sources
            client_id = self._extract_client_id(request)

            if client_id:
                # Set tenant context in database session
                await self._set_tenant_context(client_id)
                logger.debug(f"Set tenant context to {client_id}")
            else:
                logger.debug("No tenant context available for this request")

        except Exception as e:
            logger.error(f"Error setting tenant context: {e}")
            # Continue processing even if tenant context fails
            # This prevents breaking non-tenant-specific endpoints

        # Process the request
        response = await call_next(request)

        # Clear tenant context after request (optional, connection pooling handles this)
        if client_id:
            try:
                await self._clear_tenant_context()
            except Exception as e:
                logger.error(f"Error clearing tenant context: {e}")

        return response

    def _extract_client_id(self, request: Request) -> Optional[UUID]:
        """
        Extract client_account_id from the request.

        Priority order:
        1. Request state (set by auth middleware)
        2. User's default client_account_id (from JWT/session)
        3. Query parameter (for specific use cases)
        4. Header (for API clients)
        """
        # 1. Check request state (most common - set by auth middleware)
        if hasattr(request.state, "client_account_id"):
            return request.state.client_account_id

        # 2. Check user context
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "default_client_account_id"):
                return user.default_client_account_id

        # 3. Check query parameters (for specific API endpoints)
        client_id_param = request.query_params.get("client_account_id")
        if client_id_param:
            try:
                return UUID(client_id_param)
            except ValueError:
                logger.warning(
                    f"Invalid client_account_id in query params: {client_id_param}"
                )

        # 4. Check headers (for API clients)
        client_id_header = request.headers.get("X-Client-Account-ID")
        if client_id_header:
            try:
                return UUID(client_id_header)
            except ValueError:
                logger.warning(
                    f"Invalid client_account_id in header: {client_id_header}"
                )

        return None

    async def _set_tenant_context(self, client_id: UUID) -> None:
        """Set the tenant context in PostgreSQL session"""
        async for db in get_db():
            try:
                # Use the function we created in the migration
                await db.execute(
                    text("SELECT migration.set_tenant_context(:client_id)"),
                    {"client_id": str(client_id)},
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to set tenant context: {e}")
                await db.rollback()
                raise
            finally:
                await db.close()

    async def _clear_tenant_context(self) -> None:
        """Clear the tenant context from PostgreSQL session"""
        async for db in get_db():
            try:
                # Reset the session variable
                await db.execute(text("RESET app.client_id"))
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to clear tenant context: {e}")
                await db.rollback()
            finally:
                await db.close()


def get_current_tenant_id(request: Request) -> Optional[UUID]:
    """
    Helper function to get the current tenant ID from request.

    This can be used in endpoints to get the current tenant context.
    """
    if hasattr(request.state, "client_account_id"):
        return request.state.client_account_id

    if hasattr(request.state, "user") and hasattr(
        request.state.user, "default_client_account_id"
    ):
        return request.state.user.default_client_account_id

    return None
