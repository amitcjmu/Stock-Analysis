"""
Infrastructure-aware authentication service that uses deployment abstractions.
"""

import logging
from typing import Optional, Dict, Any, List

from app.infrastructure import get_service_factory

logger = logging.getLogger(__name__)


class InfrastructureAuthService:
    """
    Authentication service that automatically selects the appropriate backend
    based on deployment configuration.
    """
    
    def __init__(self):
        """Initialize the infrastructure auth service."""
        self._backend = None
        self._factory = get_service_factory()
    
    async def _get_backend(self):
        """Get or create the authentication backend."""
        if self._backend is None:
            self._backend = await self._factory.get_auth_backend()
        return self._backend
    
    async def authenticate_user(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user using the configured backend.
        
        Args:
            username: User identifier
            password: Password (for database auth)
            token: Token (for SSO auth)
            **kwargs: Additional auth parameters
            
        Returns:
            User info if authenticated, None otherwise
        """
        backend = await self._get_backend()
        
        try:
            user = await backend.authenticate(
                username=username,
                password=password,
                token=token,
                **kwargs
            )
            
            if user:
                logger.info(f"User {username} authenticated successfully")
                # Log telemetry
                telemetry = await self._factory.get_telemetry_service()
                await telemetry.record_event(
                    "user_authenticated",
                    properties={
                        "username": username,
                        "auth_method": "sso" if token else "password"
                    }
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            # Log error to telemetry
            telemetry = await self._factory.get_telemetry_service()
            await telemetry.record_error(e, context={"username": username})
            return None
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: User email
            password: Password (for database auth)
            profile: Additional user profile data
            
        Returns:
            Created user info or None if failed
        """
        backend = await self._get_backend()
        
        try:
            user = await backend.create_user(
                username=username,
                email=email,
                password=password,
                profile=profile
            )
            
            # Log telemetry
            telemetry = await self._factory.get_telemetry_service()
            await telemetry.record_event(
                "user_created",
                properties={"username": username, "email": email}
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return None
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create an authentication session.
        
        Args:
            user_id: User identifier
            metadata: Session metadata
            
        Returns:
            Session token or None if failed
        """
        backend = await self._get_backend()
        
        try:
            token = await backend.create_session(user_id, metadata)
            
            # Log telemetry
            telemetry = await self._factory.get_telemetry_service()
            await telemetry.record_metric(
                "active_sessions",
                1.0,
                tags={"user_id": user_id}
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating session for {user_id}: {e}")
            return None
    
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            Session info if valid, None otherwise
        """
        backend = await self._get_backend()
        
        try:
            return await backend.validate_session(session_token)
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    async def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session.
        
        Args:
            session_token: Session token to revoke
            
        Returns:
            True if revoked, False otherwise
        """
        backend = await self._get_backend()
        
        try:
            revoked = await backend.revoke_session(session_token)
            
            if revoked:
                # Log telemetry
                telemetry = await self._factory.get_telemetry_service()
                await telemetry.record_event(
                    "session_revoked",
                    properties={"session_token": session_token[:8] + "..."}
                )
            
            return revoked
            
        except Exception as e:
            logger.error(f"Error revoking session: {e}")
            return False
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get user's roles.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of role names
        """
        backend = await self._get_backend()
        
        try:
            return await backend.get_user_roles(user_id)
        except Exception as e:
            logger.error(f"Error getting roles for {user_id}: {e}")
            return []
    
    async def health_check(self) -> bool:
        """
        Check if the authentication service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        backend = await self._get_backend()
        
        try:
            return await backend.health_check()
        except Exception as e:
            logger.error(f"Auth service health check failed: {e}")
            return False


# Global service instance
_auth_service: Optional[InfrastructureAuthService] = None


def get_infrastructure_auth_service() -> InfrastructureAuthService:
    """
    Get the global infrastructure auth service instance.
    
    Returns:
        Infrastructure auth service instance
    """
    global _auth_service
    
    if _auth_service is None:
        _auth_service = InfrastructureAuthService()
    
    return _auth_service