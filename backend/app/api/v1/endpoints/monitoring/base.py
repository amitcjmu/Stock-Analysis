"""
Base module for monitoring endpoints.

Contains shared dependencies and utilities for all monitoring modules.
"""

from app.core.context import RequestContext, extract_context_from_request
from app.core.logging import get_logger as enhanced_get_logger
from fastapi import Request

logger = enhanced_get_logger(__name__)


async def get_monitoring_context(request: Request) -> RequestContext:
    """Get context for monitoring endpoints without authentication."""
    return extract_context_from_request(request)
