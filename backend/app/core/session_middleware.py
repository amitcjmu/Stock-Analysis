"""
Session Management Middleware for FastAPI
"""

import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

logger = logging.getLogger(__name__)

# Paths to exclude from session management
EXCLUDED_PATHS = ["/health", "/docs", "/openapi.json"]

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Ensures a session ID is present for every request, except for excluded paths.
        
        It checks for a 'session_id' in a cookie. If not found,
        it generates a new UUID for the session.
        """
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        session_id = request.cookies.get("session_id")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"✅ SessionMiddleware: No session cookie found. Generated new session ID: {session_id}")
        
        # Add session_id to the request state to make it accessible in endpoints
        request.state.session_id = session_id
        
        response = await call_next(request)
        
        # Set the session ID in a secure, HttpOnly cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,       # Prevents client-side script access
            samesite='lax',      # Good default for modern browsers
            max_age=60*60*24*7,  # 1 week expiry
            secure=request.url.scheme == "https", # Only send over HTTPS in production
            path="/"
        )
        response.headers["X-Session-ID"] = session_id # Keep for non-browser clients
        
        return response 