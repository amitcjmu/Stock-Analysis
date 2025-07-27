"""
Credential Access Control Middleware
Enforces role-based and permission-based access control for credentials
"""

import logging
import uuid
from typing import Callable, Dict, List, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.credential_service import CredentialService

logger = logging.getLogger(__name__)

security = HTTPBearer()


class CredentialAccessControl:
    """Middleware for credential access control"""

    # Role hierarchy for permission inheritance
    ROLE_HIERARCHY = {
        "platform_admin": 5,
        "client_admin": 4,
        "engagement_manager": 3,
        "analyst": 2,
        "viewer": 1,
    }

    # Role-based default permissions
    ROLE_PERMISSIONS = {
        "platform_admin": ["read", "write", "delete", "rotate", "grant"],
        "client_admin": ["read", "write", "rotate", "grant"],
        "engagement_manager": ["read", "write", "rotate"],
        "analyst": ["read"],
        "viewer": ["read"],
    }

    # Sensitive operations requiring additional checks
    SENSITIVE_OPERATIONS = ["delete", "rotate", "grant"]

    @staticmethod
    async def check_credential_access(
        request: Request,
        credential_id: uuid.UUID,
        required_permission: str,
        db: AsyncSession,
    ) -> bool:
        """
        Check if current user has access to a credential

        Args:
            request: FastAPI request
            credential_id: Credential ID
            required_permission: Required permission type
            db: Database session

        Returns:
            True if access allowed

        Raises:
            HTTPException: If access denied
        """
        # Get current user from request
        user = getattr(request.state, "current_user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        # Platform admins have full access
        if user.role == "platform_admin":
            return True

        # Check role-based permissions
        user_permissions = CredentialAccessControl.ROLE_PERMISSIONS.get(user.role, [])
        if required_permission not in user_permissions:
            logger.warning(
                f"User {user.id} with role {user.role} lacks permission {required_permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role} does not have {required_permission} permission",
            )

        # For sensitive operations, require explicit permission
        if required_permission in CredentialAccessControl.SENSITIVE_OPERATIONS:
            service = CredentialService(db)
            try:
                credential, _ = await service.get_credential(
                    credential_id, user.id, decrypt_data=False
                )

                # Check if user has explicit permission
                has_permission = await service._check_permission(
                    credential, user.id, required_permission
                )

                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"No explicit permission for {required_permission} operation",
                    )

            except Exception as e:
                logger.error(f"Error checking credential access: {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )

        return True

    @staticmethod
    async def check_client_account_access(
        request: Request, client_account_id: uuid.UUID, db: AsyncSession
    ) -> bool:
        """
        Check if user has access to credentials for a client account

        Args:
            request: FastAPI request
            client_account_id: Client account ID
            db: Database session

        Returns:
            True if access allowed
        """
        user = getattr(request.state, "current_user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        # Platform admins have full access
        if user.role == "platform_admin":
            return True

        # Client admins can only access their own client's credentials
        if user.role == "client_admin":
            # TODO: Check if user belongs to the client account
            # This requires user-client relationship in the database
            pass

        # Engagement managers and below need explicit permissions
        # TODO: Implement engagement-based access control

        return True

    @staticmethod
    def require_permission(permission: str) -> Callable:
        """
        Decorator to require specific permission for an endpoint

        Args:
            permission: Required permission

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                # Extract request and credential_id from kwargs
                request = kwargs.get("request")
                credential_id = kwargs.get("credential_id")
                db = kwargs.get("db")

                if not all([request, credential_id, db]):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Missing required parameters",
                    )

                # Check access
                await CredentialAccessControl.check_credential_access(
                    request, credential_id, permission, db
                )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def get_permission_scope(user_role: str) -> List[str]:
        """
        Get list of permissions for a role

        Args:
            user_role: User role

        Returns:
            List of permissions
        """
        return CredentialAccessControl.ROLE_PERMISSIONS.get(user_role, [])

    @staticmethod
    def can_grant_permission(granting_role: str, permission_type: str) -> bool:
        """
        Check if a role can grant a specific permission

        Args:
            granting_role: Role of user granting permission
            permission_type: Type of permission to grant

        Returns:
            True if can grant
        """
        # Only admins can grant permissions
        if granting_role not in ["platform_admin", "client_admin"]:
            return False

        # Platform admins can grant any permission
        if granting_role == "platform_admin":
            return True

        # Client admins can only grant permissions they have
        client_permissions = CredentialAccessControl.ROLE_PERMISSIONS.get(
            granting_role, []
        )
        return permission_type in client_permissions

    @staticmethod
    async def audit_access_attempt(
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        permission: str,
        allowed: bool,
        reason: Optional[str] = None,
        db: AsyncSession = None,
    ) -> None:
        """
        Audit credential access attempts

        Args:
            user_id: User attempting access
            credential_id: Credential being accessed
            permission: Permission requested
            allowed: Whether access was allowed
            reason: Reason for denial if applicable
            db: Database session
        """
        # This will be handled by the security audit service
        logger.info(
            f"Credential access attempt: user={user_id}, credential={credential_id}, "
            f"permission={permission}, allowed={allowed}, reason={reason}"
        )


class CredentialRateLimiter:
    """Rate limiting for credential operations"""

    # Rate limits per operation type (requests per minute)
    RATE_LIMITS = {
        "read": 60,
        "decrypt": 20,
        "write": 10,
        "rotate": 5,
        "delete": 5,
        "grant": 10,
    }

    def __init__(self):
        # In-memory storage for rate limiting
        # In production, use Redis or similar
        self._request_counts: Dict[str, Dict[str, int]] = {}

    async def check_rate_limit(self, user_id: uuid.UUID, operation: str) -> bool:
        """
        Check if user has exceeded rate limit

        Args:
            user_id: User ID
            operation: Operation type

        Returns:
            True if within rate limit
        """
        self.RATE_LIMITS.get(operation, 60)

        # TODO: Implement actual rate limiting logic
        # This is a placeholder implementation

        return True

    async def record_request(self, user_id: uuid.UUID, operation: str) -> None:
        """
        Record a request for rate limiting

        Args:
            user_id: User ID
            operation: Operation type
        """
        # TODO: Implement request recording
        pass


# Global rate limiter instance
rate_limiter = CredentialRateLimiter()


async def credential_access_middleware(request: Request, call_next):
    """
    Middleware to enforce credential access control

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    # Skip for non-credential endpoints
    if not request.url.path.startswith("/api/v1/credentials"):
        return await call_next(request)

    # Extract operation from path
    request.url.path.split("/")
    operation = "read"  # Default

    if request.method == "POST":
        operation = "write"
    elif request.method == "DELETE":
        operation = "delete"
    elif "rotate" in request.url.path:
        operation = "rotate"
    elif "decrypt" in request.url.path:
        operation = "decrypt"

    # Check rate limit
    user = getattr(request.state, "current_user", None)
    if user:
        if not await rate_limiter.check_rate_limit(user.id, operation):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

        await rate_limiter.record_request(user.id, operation)

    # Continue to next handler
    response = await call_next(request)

    return response
