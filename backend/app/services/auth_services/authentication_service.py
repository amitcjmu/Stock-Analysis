"""
Authentication Service
Handles login, password changes, token validation, and session management.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import bcrypt
from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import User
from app.models.rbac import UserProfile, UserRole
from app.schemas.auth_schemas import LoginRequest, LoginResponse, PasswordChangeRequest, PasswordChangeResponse, Token

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for handling authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(self, login_request: LoginRequest) -> LoginResponse:
        """
        Authenticate user against the database.
        """
        try:
            # Find user by email
            user_query = select(User).where(User.email == login_request.email)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if user is active
            if not user.is_active or not user.is_verified:
                raise HTTPException(status_code=401, detail="Account not activated")
            
            # Get user profile for additional info
            profile_query = select(UserProfile).where(UserProfile.user_id == user.id)
            profile_result = await self.db.execute(profile_query)
            user_profile = profile_result.scalar_one_or_none()
            
            if not user_profile or user_profile.status != "active":
                raise HTTPException(status_code=401, detail="Account not approved")
            
            # Verify password hash - ALL users must have a password hash
            if not user.password_hash:
                logger.warning(f"Authentication attempt for user {user.email} without password hash - BLOCKED")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if provided password matches the stored hash
            if not bcrypt.checkpw(login_request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Get user roles
            user_roles_query = select(UserRole).where(
                and_(UserRole.user_id == user.id, UserRole.is_active == True)
            )
            roles_result = await self.db.execute(user_roles_query)
            user_roles = roles_result.scalars().all()
            
            # Determine if user is admin
            is_admin = any(
                role.role_type in ["platform_admin", "client_admin"] 
                for role in user_roles
            )
            
            # Get user associations
            from app.models.client_account import UserAccountAssociation
            assoc_query = select(UserAccountAssociation).where(
                UserAccountAssociation.user_id == user.id
            )
            assoc_result = await self.db.execute(assoc_query)
            associations = assoc_result.scalars().all()
            
            # Create user session data
            user_data = {
                "id": str(user.id),
                "username": user.email.split("@")[0],
                "email": user.email,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "role": "admin" if is_admin else "user",
                "status": "approved",
                "organization": user_profile.organization,
                "role_description": user_profile.role_description,
                "associations": [
                    {
                        "id": str(assoc.id),
                        "client_account_id": str(assoc.client_account_id),
                        "role": assoc.role
                    }
                    for assoc in associations
                ]
            }
            
            # Log successful login
            if user_profile:
                user_profile.last_login_at = datetime.utcnow()
                user_profile.login_count = (user_profile.login_count or 0) + 1
                user_profile.failed_login_attempts = 0
                await self.db.commit()
            
            # Create a proper JWT token with security
            try:
                from app.services.auth_services.jwt_service import JWTService
                jwt_service = JWTService()
                
                # Create JWT token with user information
                jwt_token = jwt_service.create_access_token(
                    data={
                        "sub": str(user.id),
                        "email": user.email,
                        "role": "admin" if is_admin else "user",
                        "is_admin": is_admin
                    }
                )
                
                token = Token(
                    access_token=jwt_token,
                    token_type="bearer"
                )
                
            except Exception as jwt_error:
                logger.warning(f"JWT token creation failed, falling back to db-token: {jwt_error}")
                # Fallback to db-token for backward compatibility during transition
                token = Token(
                    access_token=f"db-token-{user.id}-{uuid.uuid4().hex[:8]}",
                    token_type="bearer"
                )
            
            return LoginResponse(
                status="success",
                message="Login successful",
                user=user_data,
                token=token
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in authenticate_user: {e}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    async def change_user_password(self, user_id: uuid.UUID, password_change: PasswordChangeRequest) -> PasswordChangeResponse:
        """
        Change user's password.
        Requires current password verification.
        """
        try:
            # Find user by ID
            user_query = select(User).where(User.id == user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Verify current password
            if user.password_hash:
                if not bcrypt.checkpw(password_change.current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    raise HTTPException(status_code=401, detail="Current password is incorrect")
            else:
                # For users without password hash, any current password is accepted
                pass
            
            # Generate new password hash
            new_password_hash = bcrypt.hashpw(password_change.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update password in database
            user.password_hash = new_password_hash
            await self.db.commit()
            
            logger.info(f"Password changed successfully for user {user.email}")
            
            return PasswordChangeResponse(
                status="success",
                message="Password changed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in change_user_password: {e}")
            raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate authentication token and return user information.
        """
        try:
            # Try JWT token first
            try:
                from app.services.auth_services.jwt_service import JWTService
                jwt_service = JWTService()
                payload = jwt_service.verify_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        # Find user by ID
                        user_query = select(User).where(User.id == uuid.UUID(user_id))
                        result = await self.db.execute(user_query)
                        user = result.scalar_one_or_none()
                        
                        if user and user.is_active:
                            return {
                                "id": str(user.id),
                                "email": user.email,
                                "is_active": user.is_active,
                                "role": payload.get("role", "user"),
                                "is_admin": payload.get("is_admin", False)
                            }
            except Exception as jwt_error:
                logger.debug(f"JWT token validation failed: {jwt_error}")
            
            # Fallback to db-token validation for backward compatibility
            if token.startswith("db-token-"):
                # Remove the "db-token-" prefix
                token_content = token[9:]  # Remove "db-token-"
                
                # Find the last dash to separate user_id from hash
                last_dash_index = token_content.rfind("-")
                if last_dash_index > 0:
                    user_id_str = token_content[:last_dash_index]
                    try:
                        user_id = uuid.UUID(user_id_str)
                        
                        # Find user by ID
                        user_query = select(User).where(User.id == user_id)
                        result = await self.db.execute(user_query)
                        user = result.scalar_one_or_none()
                        
                        if user and user.is_active:
                            return {
                                "id": str(user.id),
                                "email": user.email,
                                "is_active": user.is_active
                            }
                    except ValueError:
                        pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error in validate_token: {e}")
            return None
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Get user by ID for authentication purposes.
        """
        try:
            user_query = select(User).where(User.id == user_id)
            result = await self.db.execute(user_query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {e}")
            return None

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics for users."""
        try:
            # Total users
            total_users_query = select(func.count()).select_from(User)
            total_users_result = await self.db.execute(total_users_query)
            total_users = total_users_result.scalar_one()

            # Active users
            active_users_query = select(func.count()).select_from(User).where(User.is_active == True)
            active_users_result = await self.db.execute(active_users_query)
            active_users = active_users_result.scalar_one()

            # Pending approvals
            pending_approvals_query = select(func.count()).select_from(UserProfile).where(UserProfile.status == 'pending')
            pending_approvals_result = await self.db.execute(pending_approvals_query)
            pending_approvals = pending_approvals_result.scalar_one()

            # Users by role
            roles_query = select(UserRole.role_type, func.count()).group_by(UserRole.role_type)
            roles_result = await self.db.execute(roles_query)
            users_by_role = {row[0]: row[1] for row in roles_result.all() if row[0]}

            return {
                "total_users": total_users,
                "active_users": active_users,
                "pending_approvals": pending_approvals,
                "users_by_role": users_by_role
            }
        except Exception as e:
            logger.error(f"Error getting user dashboard stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user dashboard stats") 