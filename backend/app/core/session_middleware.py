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

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Ensures a session ID is present for every request.
        
        It checks for a 'session-id' in the header. If not found,
        it generates a new UUID for the session.
        """
        session_id = request.headers.get("session-id")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"✅ SessionMiddleware: Generated new session ID: {session_id}")
        else:
            logger.info(f"✅ SessionMiddleware: Using session ID from header: {session_id}")
        
        # Add session_id to the request state to make it accessible in endpoints
        request.state.session_id = session_id
        
        response = await call_next(request)
        
        # Optionally, set the session ID in the response headers/cookies
        response.headers["X-Session-ID"] = session_id
        
        return response 