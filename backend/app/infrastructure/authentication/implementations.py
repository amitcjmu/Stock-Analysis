"""
Concrete implementations of the AuthenticationBackend interface.
"""

import os
import json
import secrets
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from .interface import AuthenticationBackend

logger = logging.getLogger(__name__)


class DatabaseAuthBackend(AuthenticationBackend):
    """
    Database-based authentication backend for local and on-premises deployments.
    Uses the existing application database for user management.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize database auth backend.
        
        Args:
            db_session: Database session (injected)
        """
        self._db = db_session
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._users_cache: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized DatabaseAuthBackend")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)
    
    async def authenticate(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user against database."""
        # Token-based auth (for existing sessions)
        if token:
            session = await self.validate_session(token)
            if session:
                return await self.get_user(session["user_id"])
        
        # Password-based auth
        if not password:
            logger.warning(f"Authentication failed for {username}: no password provided")
            return None
        
        # In production, this would query the database
        # For now, check cache and environment
        user = self._users_cache.get(username)
        
        if not user:
            # Check environment for demo users
            demo_password = os.getenv(f"DEMO_USER_{username.upper()}_PASSWORD")
            if demo_password and self._hash_password(password) == self._hash_password(demo_password):
                user = {
                    "id": f"demo_{username}",
                    "username": username,
                    "email": f"{username}@example.com",
                    "roles": ["user"],
                    "created_at": datetime.utcnow().isoformat()
                }
                self._users_cache[username] = user
        
        if user and user.get("password_hash") == self._hash_password(password):
            logger.info(f"User {username} authenticated successfully")
            return {k: v for k, v in user.items() if k != "password_hash"}
        
        logger.warning(f"Authentication failed for {username}")
        return None
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create user in database."""
        if username in self._users_cache:
            raise ValueError(f"User {username} already exists")
        
        user = {
            "id": f"user_{secrets.token_hex(8)}",
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password) if password else None,
            "profile": profile or {},
            "roles": ["user"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._users_cache[username] = user
        logger.info(f"Created user: {username}")
        
        return {k: v for k, v in user.items() if k != "password_hash"}
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update user in database."""
        # Find user by ID
        user = None
        for u in self._users_cache.values():
            if u["id"] == user_id:
                user = u
                break
        
        if not user:
            logger.warning(f"User {user_id} not found for update")
            return None
        
        # Apply updates
        for key, value in updates.items():
            if key == "password":
                user["password_hash"] = self._hash_password(value)
            elif key != "id":  # Don't allow ID updates
                user[key] = value
        
        user["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Updated user: {user_id}")
        
        return {k: v for k, v in user.items() if k != "password_hash"}
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user from database."""
        # Find and remove user
        username_to_delete = None
        for username, user in self._users_cache.items():
            if user["id"] == user_id:
                username_to_delete = username
                break
        
        if username_to_delete:
            del self._users_cache[username_to_delete]
            logger.info(f"Deleted user: {user_id}")
            return True
        
        logger.warning(f"User {user_id} not found for deletion")
        return False
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user from database."""
        for user in self._users_cache.values():
            if user["id"] == user_id:
                return {k: v for k, v in user.items() if k != "password_hash"}
        
        return None
    
    async def list_users(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List users from database."""
        users = list(self._users_cache.values())
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                users = [u for u in users if u.get(key) == value]
        
        # Apply pagination
        users = users[offset:offset + limit]
        
        # Remove sensitive data
        return [{k: v for k, v in u.items() if k != "password_hash"} for u in users]
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create authentication session."""
        token = self._generate_token()
        
        self._sessions[token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "metadata": metadata or {}
        }
        
        logger.info(f"Created session for user: {user_id}")
        return token
    
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token."""
        session = self._sessions.get(session_token)
        
        if not session:
            return None
        
        if datetime.utcnow() > session["expires_at"]:
            # Session expired
            del self._sessions[session_token]
            logger.info(f"Session expired: {session_token[:8]}...")
            return None
        
        return session
    
    async def revoke_session(self, session_token: str) -> bool:
        """Revoke session."""
        if session_token in self._sessions:
            del self._sessions[session_token]
            logger.info(f"Revoked session: {session_token[:8]}...")
            return True
        
        return False
    
    async def refresh_session(self, session_token: str) -> Optional[str]:
        """Refresh session token."""
        session = await self.validate_session(session_token)
        
        if not session:
            return None
        
        # Create new session
        new_token = await self.create_session(
            session["user_id"],
            session.get("metadata")
        )
        
        # Revoke old session
        await self.revoke_session(session_token)
        
        return new_token
    
    async def assign_role(self, user_id: str, role: str) -> bool:
        """Assign role to user."""
        user = await self.get_user(user_id)
        
        if not user:
            return False
        
        # Find user in cache
        for cached_user in self._users_cache.values():
            if cached_user["id"] == user_id:
                if "roles" not in cached_user:
                    cached_user["roles"] = []
                if role not in cached_user["roles"]:
                    cached_user["roles"].append(role)
                logger.info(f"Assigned role {role} to user {user_id}")
                return True
        
        return False
    
    async def remove_role(self, user_id: str, role: str) -> bool:
        """Remove role from user."""
        # Find user in cache
        for cached_user in self._users_cache.values():
            if cached_user["id"] == user_id:
                if "roles" in cached_user and role in cached_user["roles"]:
                    cached_user["roles"].remove(role)
                    logger.info(f"Removed role {role} from user {user_id}")
                    return True
        
        return False
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles."""
        user = await self.get_user(user_id)
        return user.get("roles", []) if user else []
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            # In production, this would test database connection
            return True
        except Exception as e:
            logger.error(f"Database auth health check failed: {e}")
            return False


class SSOAuthBackend(AuthenticationBackend):
    """
    SSO-based authentication backend for SaaS deployments.
    Integrates with SAML, OAuth2, or OIDC providers.
    """
    
    def __init__(self, provider: str = "oauth2", config: Optional[Dict[str, Any]] = None):
        """
        Initialize SSO auth backend.
        
        Args:
            provider: SSO provider type (oauth2, saml, oidc)
            config: Provider configuration
        """
        self.provider = provider
        self.config = config or {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load provider config from environment
        self.client_id = self.config.get("client_id") or os.getenv("SSO_CLIENT_ID")
        self.client_secret = self.config.get("client_secret") or os.getenv("SSO_CLIENT_SECRET")
        self.redirect_uri = self.config.get("redirect_uri") or os.getenv("SSO_REDIRECT_URI")
        self.authorize_url = self.config.get("authorize_url") or os.getenv("SSO_AUTHORIZE_URL")
        self.token_url = self.config.get("token_url") or os.getenv("SSO_TOKEN_URL")
        
        logger.info(f"Initialized SSOAuthBackend with provider: {provider}")
    
    async def authenticate(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Authenticate via SSO provider."""
        # SSO uses tokens, not passwords
        if not token:
            logger.warning(f"SSO authentication requires token")
            return None
        
        # Validate token with provider
        # In production, this would call the SSO provider's API
        if token.startswith("sso_"):
            # Simulated SSO validation
            user = {
                "id": f"sso_{username}",
                "username": username,
                "email": kwargs.get("email", f"{username}@sso.example.com"),
                "provider": self.provider,
                "roles": ["user"],
                "authenticated_at": datetime.utcnow().isoformat()
            }
            
            self._user_cache[username] = user
            logger.info(f"User {username} authenticated via SSO")
            return user
        
        logger.warning(f"SSO authentication failed for {username}")
        return None
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create user via SSO (usually auto-provisioned)."""
        # SSO users are typically auto-provisioned on first login
        user = {
            "id": f"sso_{secrets.token_hex(8)}",
            "username": username,
            "email": email,
            "provider": self.provider,
            "profile": profile or {},
            "roles": ["user"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._user_cache[username] = user
        logger.info(f"Auto-provisioned SSO user: {username}")
        
        return user
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update SSO user (limited updates)."""
        # Find user
        user = None
        for u in self._user_cache.values():
            if u["id"] == user_id:
                user = u
                break
        
        if not user:
            return None
        
        # SSO users have limited updatable fields
        allowed_updates = ["profile", "roles", "metadata"]
        for key, value in updates.items():
            if key in allowed_updates:
                user[key] = value
        
        user["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Updated SSO user: {user_id}")
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete SSO user (local cache only)."""
        # SSO users can't be deleted from provider, only from local cache
        username_to_delete = None
        for username, user in self._user_cache.items():
            if user["id"] == user_id:
                username_to_delete = username
                break
        
        if username_to_delete:
            del self._user_cache[username_to_delete]
            logger.info(f"Removed SSO user from cache: {user_id}")
            return True
        
        return False
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get SSO user."""
        for user in self._user_cache.values():
            if user["id"] == user_id:
                return user
        
        return None
    
    async def list_users(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List SSO users (from cache)."""
        users = list(self._user_cache.values())
        
        if filters:
            for key, value in filters.items():
                users = [u for u in users if u.get(key) == value]
        
        return users[offset:offset + limit]
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create SSO session."""
        token = f"sso_{secrets.token_urlsafe(32)}"
        
        self._sessions[token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=8),  # Shorter for SSO
            "metadata": metadata or {},
            "provider": self.provider
        }
        
        logger.info(f"Created SSO session for user: {user_id}")
        return token
    
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate SSO session."""
        session = self._sessions.get(session_token)
        
        if not session:
            return None
        
        if datetime.utcnow() > session["expires_at"]:
            del self._sessions[session_token]
            return None
        
        # In production, might also validate with SSO provider
        return session
    
    async def revoke_session(self, session_token: str) -> bool:
        """Revoke SSO session."""
        if session_token in self._sessions:
            # In production, might also notify SSO provider
            del self._sessions[session_token]
            logger.info(f"Revoked SSO session: {session_token[:8]}...")
            return True
        
        return False
    
    async def refresh_session(self, session_token: str) -> Optional[str]:
        """Refresh SSO session."""
        session = await self.validate_session(session_token)
        
        if not session:
            return None
        
        # In production, would refresh with SSO provider
        new_token = await self.create_session(
            session["user_id"],
            session.get("metadata")
        )
        
        await self.revoke_session(session_token)
        return new_token
    
    async def assign_role(self, user_id: str, role: str) -> bool:
        """Assign role (local only for SSO)."""
        for user in self._user_cache.values():
            if user["id"] == user_id:
                if "roles" not in user:
                    user["roles"] = []
                if role not in user["roles"]:
                    user["roles"].append(role)
                return True
        
        return False
    
    async def remove_role(self, user_id: str, role: str) -> bool:
        """Remove role (local only for SSO)."""
        for user in self._user_cache.values():
            if user["id"] == user_id:
                if "roles" in user and role in user["roles"]:
                    user["roles"].remove(role)
                    return True
        
        return False
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles."""
        user = await self.get_user(user_id)
        return user.get("roles", []) if user else []
    
    async def health_check(self) -> bool:
        """Check SSO provider connectivity."""
        try:
            # In production, would check SSO provider endpoint
            return bool(self.client_id and self.authorize_url)
        except Exception as e:
            logger.error(f"SSO health check failed: {e}")
            return False