"""
Authentication Handlers
Handles login, password change, and token-related endpoints.
"""

import logging
from typing import Dict, Any
import uuid
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth_schemas import (
    LoginRequest, LoginResponse, 
    PasswordChangeRequest, PasswordChangeResponse
)
from app.services.auth_services.authentication_service import AuthenticationService

logger = logging.getLogger(__name__)

# Create authentication router
authentication_router = APIRouter()


@authentication_router.post("/login", response_model=LoginResponse)
async def login_user(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user against the database.
    For now, this is a simplified implementation that checks if user exists and is active.
    In production, this would verify password hashes.
    """
    try:
        auth_service = AuthenticationService(db)
        return await auth_service.authenticate_user(login_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login_user: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@authentication_router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_change: PasswordChangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Change user's password.
    Requires authentication and current password verification.
    """
    try:
        # Get user ID from request headers
        user_id_str = request.headers.get("X-User-ID")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Convert string to UUID, handle validation
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id_str}")
        
        auth_service = AuthenticationService(db)
        return await auth_service.change_user_password(user_id, password_change)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in change_password: {e}")
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")


@authentication_router.get("/health")
async def authentication_health_check():
    """Health check for authentication system."""
    return {
        "status": "healthy",
        "service": "Authentication Service",
        "version": "1.0.0"
    } 