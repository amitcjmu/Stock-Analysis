"""
Authentication Backend interface for abstracting authentication mechanisms.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class AuthenticationBackend(ABC):
    """
    Abstract interface for authentication backends.
    Supports both database-based and SSO-based authentication.
    """
    
    @abstractmethod
    async def authenticate(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.
        
        Args:
            username: User identifier (email, username, etc.)
            password: Password for database auth
            token: Token for SSO auth
            **kwargs: Additional auth parameters
            
        Returns:
            User info dict if authenticated, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_user(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: User email
            password: Password (for database auth)
            profile: Additional user profile data
            
        Returns:
            Created user info
        """
        pass
    
    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        
        Args:
            user_id: User identifier
            updates: Fields to update
            
        Returns:
            Updated user info or None if not found
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information.
        
        Args:
            user_id: User identifier
            
        Returns:
            User info or None if not found
        """
        pass
    
    @abstractmethod
    async def list_users(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List users with optional filtering.
        
        Args:
            filters: Optional filters
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of user info dicts
        """
        pass
    
    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an authentication session.
        
        Args:
            user_id: User identifier
            metadata: Session metadata
            
        Returns:
            Session token
        """
        pass
    
    @abstractmethod
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            Session info if valid, None otherwise
        """
        pass
    
    @abstractmethod
    async def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session.
        
        Args:
            session_token: Session token to revoke
            
        Returns:
            True if revoked, False if not found
        """
        pass
    
    @abstractmethod
    async def refresh_session(self, session_token: str) -> Optional[str]:
        """
        Refresh a session token.
        
        Args:
            session_token: Current session token
            
        Returns:
            New session token or None if invalid
        """
        pass
    
    @abstractmethod
    async def assign_role(self, user_id: str, role: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: User identifier
            role: Role name
            
        Returns:
            True if assigned, False if failed
        """
        pass
    
    @abstractmethod
    async def remove_role(self, user_id: str, role: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: User identifier
            role: Role name
            
        Returns:
            True if removed, False if failed
        """
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get user's roles.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of role names
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the authentication backend is operational.
        
        Returns:
            True if healthy, False otherwise
        """
        pass