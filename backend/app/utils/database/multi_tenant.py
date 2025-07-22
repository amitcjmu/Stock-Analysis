"""
Multi-tenant database utilities.
Provides consistent multi-tenant filtering and context management.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

@dataclass
class TenantContext:
    """Multi-tenant context information."""
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    user_id: Optional[str] = None
    is_platform_admin: bool = False
    
    def __post_init__(self):
        """Validate tenant context."""
        if self.client_account_id and not isinstance(self.client_account_id, str):
            self.client_account_id = str(self.client_account_id)
        if self.engagement_id and not isinstance(self.engagement_id, str):
            self.engagement_id = str(self.engagement_id)
    
    def is_valid(self) -> bool:
        """Check if tenant context is valid."""
        return bool(self.client_account_id or self.engagement_id or self.is_platform_admin)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tenant context to dictionary."""
        return {
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "user_id": self.user_id,
            "is_platform_admin": self.is_platform_admin
        }

class MultiTenantHelper:
    """Helper class for multi-tenant database operations."""
    
    @staticmethod
    def apply_tenant_filter(
        query: Select,
        model_class: Type,
        tenant_context: TenantContext
    ) -> Select:
        """
        Apply multi-tenant filtering to a query.
        
        Args:
            query: SQLAlchemy select query
            model_class: Model class to filter
            tenant_context: Tenant context information
            
        Returns:
            Filtered query
        """
        # Platform admins bypass all filters
        if tenant_context.is_platform_admin:
            logger.debug("Platform admin context - bypassing tenant filters")
            return query
        
        filters = []
        
        # Apply client account filter
        if (tenant_context.client_account_id and 
            hasattr(model_class, 'client_account_id')):
            filters.append(model_class.client_account_id == tenant_context.client_account_id)
            logger.debug(f"Applied client_account_id filter: {tenant_context.client_account_id}")
        
        # Apply engagement filter
        if (tenant_context.engagement_id and 
            hasattr(model_class, 'engagement_id')):
            filters.append(model_class.engagement_id == tenant_context.engagement_id)
            logger.debug(f"Applied engagement_id filter: {tenant_context.engagement_id}")
        
        # Handle demo/mock data access
        if (hasattr(model_class, 'is_mock') and 
            not tenant_context.client_account_id and 
            not tenant_context.engagement_id):
            # Show universal mock data for users without specific context
            filters.append(
                and_(
                    model_class.is_mock == True,
                    model_class.client_account_id.is_(None) if hasattr(model_class, 'client_account_id') else True
                )
            )
            logger.debug("Applied mock data filter for universal access")
        
        # Apply filters to query
        if filters:
            query = query.where(and_(*filters))
        
        return query
    
    @staticmethod
    def validate_tenant_access(
        tenant_context: TenantContext,
        required_client_id: Optional[str] = None,
        required_engagement_id: Optional[str] = None
    ) -> bool:
        """
        Validate if tenant context has access to specific resources.
        
        Args:
            tenant_context: Tenant context to validate
            required_client_id: Required client account ID
            required_engagement_id: Required engagement ID
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Platform admins have access to everything
        if tenant_context.is_platform_admin:
            return True
        
        # Check client account access
        if required_client_id and tenant_context.client_account_id != required_client_id:
            logger.warning(f"Client access denied: required={required_client_id}, "
                         f"context={tenant_context.client_account_id}")
            return False
        
        # Check engagement access
        if required_engagement_id and tenant_context.engagement_id != required_engagement_id:
            logger.warning(f"Engagement access denied: required={required_engagement_id}, "
                         f"context={tenant_context.engagement_id}")
            return False
        
        return True
    
    @staticmethod
    def set_tenant_fields(
        data: Dict[str, Any],
        tenant_context: TenantContext
    ) -> Dict[str, Any]:
        """
        Set tenant fields on data before creation.
        
        Args:
            data: Data dictionary to modify
            tenant_context: Tenant context information
            
        Returns:
            Modified data dictionary
        """
        if tenant_context.client_account_id and 'client_account_id' not in data:
            data['client_account_id'] = tenant_context.client_account_id
        
        if tenant_context.engagement_id and 'engagement_id' not in data:
            data['engagement_id'] = tenant_context.engagement_id
        
        # Set audit fields
        if tenant_context.user_id:
            if 'created_by' not in data:
                data['created_by'] = tenant_context.user_id
            if 'updated_by' not in data:
                data['updated_by'] = tenant_context.user_id
        
        return data
    
    @staticmethod
    async def check_admin_status(
        session: AsyncSession,
        user_id: str
    ) -> bool:
        """
        Check if user is a platform admin.
        
        Args:
            session: Database session
            user_id: User ID to check
            
        Returns:
            True if user is platform admin, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from app.models.rbac import RoleType, UserRole
            
            query = select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_type == RoleType.ADMIN,
                    UserRole.is_active == True
                )
            )
            
            result = await session.execute(query)
            admin_role = result.scalar_one_or_none()
            
            is_admin = admin_role is not None
            logger.debug(f"Admin check for user {user_id}: {is_admin}")
            return is_admin
            
        except Exception as e:
            logger.error(f"Error checking admin status for user {user_id}: {e}")
            return False

# Convenience functions
def create_tenant_context(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    user_id: Optional[str] = None,
    is_platform_admin: bool = False
) -> TenantContext:
    """Create tenant context from parameters."""
    return TenantContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        is_platform_admin=is_platform_admin
    )

def get_tenant_context(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> TenantContext:
    """Get tenant context from request headers or parameters."""
    return TenantContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id
    )

def apply_tenant_filter(
    query: Select,
    model_class: Type,
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    is_platform_admin: bool = False
) -> Select:
    """Apply tenant filtering to query with individual parameters."""
    tenant_context = TenantContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        is_platform_admin=is_platform_admin
    )
    return MultiTenantHelper.apply_tenant_filter(query, model_class, tenant_context)

def validate_tenant_access(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    user_id: Optional[str] = None,
    is_platform_admin: bool = False,
    required_client_id: Optional[str] = None,
    required_engagement_id: Optional[str] = None
) -> bool:
    """Validate tenant access with individual parameters."""
    tenant_context = TenantContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        is_platform_admin=is_platform_admin
    )
    return MultiTenantHelper.validate_tenant_access(
        tenant_context, required_client_id, required_engagement_id
    )

# Context managers
@contextmanager
def tenant_context_scope(tenant_context: TenantContext):
    """Context manager for tenant operations."""
    logger.debug(f"Entering tenant context: {tenant_context.to_dict()}")
    try:
        yield tenant_context
    finally:
        logger.debug(f"Exiting tenant context: {tenant_context.to_dict()}")

# Tenant-aware repository mixin
class TenantAwareMixin:
    """Mixin class for tenant-aware repository operations."""
    
    def __init__(self, tenant_context: TenantContext):
        self.tenant_context = tenant_context
    
    def apply_tenant_filter(self, query: Select, model_class: Type) -> Select:
        """Apply tenant filtering to query."""
        return MultiTenantHelper.apply_tenant_filter(query, model_class, self.tenant_context)
    
    def validate_access(self, required_client_id: Optional[str] = None,
                       required_engagement_id: Optional[str] = None) -> bool:
        """Validate tenant access."""
        return MultiTenantHelper.validate_tenant_access(
            self.tenant_context, required_client_id, required_engagement_id
        )
    
    def set_tenant_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set tenant fields on data."""
        return MultiTenantHelper.set_tenant_fields(data, self.tenant_context)