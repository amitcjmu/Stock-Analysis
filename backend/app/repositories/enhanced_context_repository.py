"""
Enhanced Context-Aware Repository with Role-Based Data Scoping.
Implements proper data filtering based on user roles and hierarchical access control.
"""

import logging
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar("ModelType")

# Import enhanced RBAC models
try:
    from app.models.client_account import ClientAccount, Engagement
    from app.models.rbac_enhanced import (DataScope, EnhancedUserProfile,
                                          RoleLevel)

    ENHANCED_RBAC_AVAILABLE = True
except ImportError:
    ENHANCED_RBAC_AVAILABLE = False
    EnhancedUserProfile = RoleLevel = DataScope = None
    ClientAccount = Engagement = None


class EnhancedContextRepository(Generic[ModelType]):
    """
    Enhanced repository with role-based data scoping.
    Automatically filters data based on user roles and access permissions.
    """

    def __init__(
        self,
        db: AsyncSession,
        model_class: Type[ModelType],
        user_id: str = None,
        user_profile: EnhancedUserProfile = None,
    ):
        """
        Initialize repository with database session and user context.

        Args:
            db: Async database session
            model_class: SQLAlchemy model class
            user_id: User ID for role-based filtering
            user_profile: Pre-loaded user profile (optional)
        """
        self.db = db
        self.model_class = model_class
        self.user_id = user_id
        self.user_profile = user_profile

        # Check if model supports multi-tenant fields
        self.has_client_account = hasattr(model_class, "client_account_id")
        self.has_engagement = hasattr(model_class, "engagement_id")
        self.has_is_mock = hasattr(model_class, "is_mock")
        self.has_is_active = hasattr(model_class, "is_active")
        self.has_is_deleted = hasattr(model_class, "is_deleted")

        logger.debug(
            f"Initialized {model_class.__name__} repository with enhanced context: "
            f"user_id={user_id}, has_client_account={self.has_client_account}"
        )

    async def _get_user_profile(self) -> Optional[EnhancedUserProfile]:
        """Get or load user profile for access control."""
        if not ENHANCED_RBAC_AVAILABLE or not self.user_id:
            return None

        if self.user_profile:
            return self.user_profile

        try:
            query = select(EnhancedUserProfile).where(
                and_(
                    EnhancedUserProfile.user_id == self.user_id,
                    EnhancedUserProfile.is_deleted == False,
                )
            )
            result = await self.db.execute(query)
            self.user_profile = result.scalar_one_or_none()
            return self.user_profile
        except Exception as e:
            logger.error(f"Error loading user profile: {e}")
            return None

    async def _apply_rbac_filter(self, query: Select) -> Select:
        """
        Apply role-based access control filters to a query.

        Args:
            query: SQLAlchemy select query

        Returns:
            Query with RBAC filters applied
        """
        if not ENHANCED_RBAC_AVAILABLE:
            # Fallback to basic filtering
            return self._apply_basic_filter(query)

        user_profile = await self._get_user_profile()
        if not user_profile:
            # No user profile - only allow demo data
            return self._apply_demo_only_filter(query)

        # Platform admins can see everything
        if user_profile.role_level == RoleLevel.PLATFORM_ADMIN:
            return self._apply_platform_admin_filter(query)

        # Apply scope-based filtering
        if user_profile.data_scope == DataScope.CLIENT:
            return self._apply_client_scope_filter(query, user_profile)
        elif user_profile.data_scope == DataScope.ENGAGEMENT:
            return self._apply_engagement_scope_filter(query, user_profile)
        elif user_profile.data_scope == DataScope.DEMO_ONLY:
            return self._apply_demo_only_filter(query)
        else:
            # Unknown scope - restrict to demo only
            return self._apply_demo_only_filter(query)

    def _apply_platform_admin_filter(self, query: Select) -> Select:
        """Apply filters for platform admin - can see all data including soft deleted."""
        filters = []

        # Platform admins can see soft deleted items if they choose
        # For now, exclude soft deleted by default
        if self.has_is_deleted:
            filters.append(self.model_class.is_deleted == False)

        if filters:
            query = query.where(and_(*filters))

        return query

    def _apply_client_scope_filter(
        self, query: Select, user_profile: EnhancedUserProfile
    ) -> Select:
        """Apply filters for client admin/user - can see their client data + demo."""
        filters = []

        # Exclude soft deleted items for non-platform admins
        if self.has_is_deleted:
            filters.append(self.model_class.is_deleted == False)

        # Exclude inactive items
        if self.has_is_active:
            filters.append(self.model_class.is_active == True)

        # Apply client scope filter
        if self.has_client_account and user_profile.scope_client_account_id:
            client_filter = or_(
                self.model_class.client_account_id
                == user_profile.scope_client_account_id,
                # Also include demo data
                self.model_class.is_mock == True if self.has_is_mock else False,
            )
            filters.append(client_filter)
        elif self.has_is_mock:
            # No client scope - only demo data
            filters.append(self.model_class.is_mock == True)

        if filters:
            query = query.where(and_(*filters))

        return query

    def _apply_engagement_scope_filter(
        self, query: Select, user_profile: EnhancedUserProfile
    ) -> Select:
        """Apply filters for engagement manager/user - can see their engagement data + demo."""
        filters = []

        # Exclude soft deleted items
        if self.has_is_deleted:
            filters.append(self.model_class.is_deleted == False)

        # Exclude inactive items
        if self.has_is_active:
            filters.append(self.model_class.is_active == True)

        # Apply engagement scope filter
        if self.has_engagement and user_profile.scope_engagement_id:
            engagement_filter = or_(
                self.model_class.engagement_id == user_profile.scope_engagement_id,
                # Also include demo data
                self.model_class.is_mock == True if self.has_is_mock else False,
            )
            filters.append(engagement_filter)
        elif self.has_client_account and user_profile.scope_client_account_id:
            # If no engagement field but has client field, filter by client
            client_filter = or_(
                self.model_class.client_account_id
                == user_profile.scope_client_account_id,
                self.model_class.is_mock == True if self.has_is_mock else False,
            )
            filters.append(client_filter)
        elif self.has_is_mock:
            # No scope - only demo data
            filters.append(self.model_class.is_mock == True)

        if filters:
            query = query.where(and_(*filters))

        return query

    def _apply_demo_only_filter(self, query: Select) -> Select:
        """Apply filters for anonymous users - only demo data."""
        filters = []

        # Exclude soft deleted items
        if self.has_is_deleted:
            filters.append(self.model_class.is_deleted == False)

        # Exclude inactive items
        if self.has_is_active:
            filters.append(self.model_class.is_active == True)

        # Only mock/demo data
        if self.has_is_mock:
            filters.append(self.model_class.is_mock == True)

        if filters:
            query = query.where(and_(*filters))

        return query

    def _apply_basic_filter(self, query: Select) -> Select:
        """Fallback basic filtering when enhanced RBAC is not available."""
        filters = []

        # Basic exclusions
        if self.has_is_deleted:
            filters.append(self.model_class.is_deleted == False)

        if self.has_is_active:
            filters.append(self.model_class.is_active == True)

        if filters:
            query = query.where(and_(*filters))

        return query

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID with RBAC filtering.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found or not accessible
        """
        query = select(self.model_class).where(self.model_class.id == id)
        query = await self._apply_rbac_filter(query)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[ModelType]:
        """
        Get all accessible records with RBAC filtering.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances user has access to
        """
        query = select(self.model_class)
        query = await self._apply_rbac_filter(query)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_filters(self, **filters) -> List[ModelType]:
        """
        Get records by field filters with RBAC filtering.

        Args:
            **filters: Field name and value pairs for filtering

        Returns:
            List of matching model instances user has access to
        """
        query = select(self.model_class)

        # Apply field filters
        for field_name, value in filters.items():
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                if isinstance(value, list):
                    query = query.where(field.in_(value))
                else:
                    query = query.where(field == value)

        # Apply RBAC filters
        query = await self._apply_rbac_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, **data) -> Optional[ModelType]:
        """
        Create a new record with proper context and access control.

        Args:
            **data: Field values for the new record

        Returns:
            Created model instance or None if not authorized
        """
        # Check if user can create in this context
        if not await self._can_user_create():
            logger.warning(
                f"User {self.user_id} not authorized to create {self.model_class.__name__}"
            )
            return None

        # Apply context to the new instance
        instance = self.model_class(**data)
        instance = await self._apply_context_to_instance(instance)

        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"Created {self.model_class.__name__} with ID {instance.id}")
        return instance

    async def update(self, id: Any, **data) -> Optional[ModelType]:
        """
        Update a record by ID with access control.

        Args:
            id: Primary key value
            **data: Field values to update

        Returns:
            Updated model instance or None if not found/accessible
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None

        # Check if user can update this instance
        if not await self._can_user_modify(instance):
            logger.warning(
                f"User {self.user_id} not authorized to update {self.model_class.__name__} {id}"
            )
            return None

        # Update fields
        for field_name, value in data.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, value)

        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"Updated {self.model_class.__name__} with ID {id}")
        return instance

    async def soft_delete(self, id: Any, reason: str = None) -> bool:
        """
        Soft delete a record (mark as deleted without removing from database).

        Args:
            id: Primary key value
            reason: Reason for deletion

        Returns:
            True if deleted successfully, False otherwise
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False

        # Check if user can delete this instance
        if not await self._can_user_delete(instance):
            logger.warning(
                f"User {self.user_id} not authorized to delete {self.model_class.__name__} {id}"
            )
            return False

        # Perform soft delete
        if self.has_is_deleted:
            setattr(instance, "is_deleted", True)
            if hasattr(instance, "deleted_at"):
                from datetime import datetime

                setattr(instance, "deleted_at", datetime.utcnow())
            if hasattr(instance, "deleted_by"):
                setattr(instance, "deleted_by", self.user_id)
            if hasattr(instance, "delete_reason"):
                setattr(instance, "delete_reason", reason)
        elif self.has_is_active:
            # Fallback to marking inactive
            setattr(instance, "is_active", False)

        await self.db.commit()

        logger.info(f"Soft deleted {self.model_class.__name__} with ID {id}")
        return True

    async def count(self, **filters) -> int:
        """
        Count accessible records with RBAC filtering.

        Args:
            **filters: Field name and value pairs for filtering

        Returns:
            Count of accessible records
        """
        from sqlalchemy import func

        query = select(func.count(self.model_class.id))

        # Apply field filters
        for field_name, value in filters.items():
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                if isinstance(value, list):
                    query = query.where(field.in_(value))
                else:
                    query = query.where(field == value)

        # Apply RBAC filters
        query = await self._apply_rbac_filter(query)

        result = await self.db.execute(query)
        return result.scalar()

    # Private helper methods

    async def _apply_context_to_instance(self, instance: ModelType) -> ModelType:
        """Apply user context to a model instance before saving."""
        user_profile = await self._get_user_profile()
        if not user_profile:
            return instance

        # Set client account if supported and user has scope
        if self.has_client_account and user_profile.scope_client_account_id:
            if user_profile.data_scope in [DataScope.CLIENT, DataScope.ENGAGEMENT]:
                setattr(
                    instance, "client_account_id", user_profile.scope_client_account_id
                )

        # Set engagement if supported and user has scope
        if self.has_engagement and user_profile.scope_engagement_id:
            if user_profile.data_scope == DataScope.ENGAGEMENT:
                setattr(instance, "engagement_id", user_profile.scope_engagement_id)

        return instance

    async def _can_user_create(self) -> bool:
        """Check if user can create new records."""
        user_profile = await self._get_user_profile()
        if not user_profile:
            return False

        # Platform admins can create anything
        if user_profile.role_level == RoleLevel.PLATFORM_ADMIN:
            return True

        # Viewers cannot create
        if user_profile.role_level == RoleLevel.VIEWER:
            return False

        # Others can create within their scope
        return True

    async def _can_user_modify(self, instance: ModelType) -> bool:
        """Check if user can modify a specific instance."""
        user_profile = await self._get_user_profile()
        if not user_profile:
            return False

        # Platform admins can modify anything
        if user_profile.role_level == RoleLevel.PLATFORM_ADMIN:
            return True

        # Viewers cannot modify
        if user_profile.role_level == RoleLevel.VIEWER:
            return False

        # Check scope access
        if self.has_client_account and hasattr(instance, "client_account_id"):
            client_id = getattr(instance, "client_account_id")
            if client_id and not user_profile.can_access_client(str(client_id)):
                return False

        if self.has_engagement and hasattr(instance, "engagement_id"):
            engagement_id = getattr(instance, "engagement_id")
            if engagement_id and not user_profile.can_access_engagement(
                str(engagement_id)
            ):
                return False

        return True

    async def _can_user_delete(self, instance: ModelType) -> bool:
        """Check if user can delete a specific instance."""
        user_profile = await self._get_user_profile()
        if not user_profile:
            return False

        # Only admins can delete
        if not user_profile.can_delete_data:
            return False

        # Platform admins can delete anything
        if user_profile.role_level == RoleLevel.PLATFORM_ADMIN:
            return True

        # Check scope access for other admin levels
        return await self._can_user_modify(instance)
