"""
Request logging middleware for detailed request monitoring.
Provides structured logging of all requests with context information.
"""

import logging
import time
from typing import Callable, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Additional middleware for detailed request logging with context.
    """

    def __init__(self, app: Callable, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request details with context information.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from downstream handler
        """
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        start_time = time.time()

        # Extract basic request info
        method = request.method
        url = str(request.url)

        try:
            # Process request
            response = await call_next(request)

            # Log response - only log server errors and client errors (excluding auth failures)
            process_time = time.time() - start_time
            status_code = response.status_code

            # Only log errors and warnings (reduce noise from normal operations)
            if status_code >= 500:
                # Server errors - always log
                logger.error(
                    f"❌ {method} {url} | Status: {status_code} | Time: {process_time:.3f}s"
                )
            elif status_code >= 400 and status_code not in [401, 403]:
                # Client errors (except auth failures which are expected) - log as warning
                logger.warning(
                    f"⚠️ {method} {url} | Status: {status_code} | Time: {process_time:.3f}s"
                )
            # Don't log successful requests (200-399) or auth failures (401, 403) - too noisy

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                safe_log_format(
                    "❌ {method} {url} | Error: {e} | Time: {process_time}s",
                    method=method,
                    url=url,
                    e=e,
                    process_time=f"{process_time:.3f}",
                )
            )
            raise
