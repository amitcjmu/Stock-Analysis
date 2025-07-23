"""
Base Repository Classes
Provides context-aware data access patterns for multi-tenant applications.
"""

import logging
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, Session

logger = logging.getLogger(__name__)


class ContextAwareRepository:
    """Base repository with context awareness for multi-tenant data access."""

    def __init__(
        self,
        db: Session,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self._is_platform_admin = None  # Cache admin status

        # Log context for debugging
        if client_account_id or engagement_id:
            logger.debug(
                f"Repository context: client_account_id={client_account_id}, engagement_id={engagement_id}, user_id={user_id}"
            )

    async def _check_is_platform_admin(self) -> bool:
        """Check if the current user is a platform admin."""
        if self._is_platform_admin is not None:
            return self._is_platform_admin

        if not self.user_id:
            self._is_platform_admin = False
            return False

        try:
            # Import models here to avoid circular imports
            from app.models.rbac import RoleType, UserRole

            # Check if this is an async session
            if isinstance(self.db, AsyncSession):
                # Async query
                query = select(UserRole).where(
                    and_(
                        UserRole.user_id == self.user_id,
                        UserRole.role_type == RoleType.ADMIN,
                        UserRole.is_active is True,
                    )
                )
                result = await self.db.execute(query)
                admin_role = result.scalar_one_or_none()
            else:
                # Sync query
                admin_role = (
                    self.db.query(UserRole)
                    .filter(
                        and_(
                            UserRole.user_id == self.user_id,
                            UserRole.role_type == RoleType.PLATFORM_ADMIN,
                            UserRole.is_active is True,
                        )
                    )
                    .first()
                )

            self._is_platform_admin = admin_role is not None
            if self._is_platform_admin:
                logger.info(
                    f"User {self.user_id} is a platform admin - bypassing client filtering"
                )
            return self._is_platform_admin

        except Exception as e:
            logger.warning(f"Could not check admin status for user {self.user_id}: {e}")
            self._is_platform_admin = False
            return False

    def _apply_context_filter(self, query: Query, model_class: Any) -> Query:
        """Apply context-based filtering to a query."""
        # Platform admins see everything - no filtering
        try:
            # Run sync check for platform admin (repositories typically use sync sessions)
            if self.user_id and not isinstance(self.db, AsyncSession):
                from app.models.rbac import RoleType, UserRole

                admin_role = (
                    self.db.query(UserRole)
                    .filter(
                        and_(
                            UserRole.user_id == self.user_id,
                            UserRole.role_type == RoleType.PLATFORM_ADMIN,
                            UserRole.is_active is True,
                        )
                    )
                    .first()
                )

                if admin_role:
                    logger.debug(
                        f"Platform admin {self.user_id} - bypassing all filters"
                    )
                    return query
        except Exception as e:
            logger.warning(f"Could not check admin status: {e}")

        filters = []

        # Apply client account filter if model has the field and context is available
        if hasattr(model_class, "client_account_id") and self.client_account_id:
            filters.append(model_class.client_account_id == self.client_account_id)

        # Apply engagement filter if model has the field and context is available
        if hasattr(model_class, "engagement_id") and self.engagement_id:
            filters.append(model_class.engagement_id == self.engagement_id)

        # For mock data access, if no context is provided, show universal mock data
        if (
            hasattr(model_class, "is_mock")
            and not self.client_account_id
            and not self.engagement_id
        ):
            # Show mock data that is either universal (no account/engagement) or specifically marked as demo
            filters.append(
                and_(
                    model_class.is_mock is True,
                    # Show universal mock data (no specific client/engagement)
                    (
                        model_class.client_account_id.is_(None)
                        if hasattr(model_class, "client_account_id")
                        else True
                    ),
                )
            )

        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))

        return query

    def _set_context_fields(self, data: dict) -> dict:
        """Set context fields on data before creation."""
        if self.client_account_id and "client_account_id" not in data:
            data["client_account_id"] = self.client_account_id

        if self.engagement_id and "engagement_id" not in data:
            data["engagement_id"] = self.engagement_id

        return data

    def set_context(
        self,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ):
        """Update the repository context."""
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self._is_platform_admin = None  # Reset admin cache when context changes

        logger.debug(
            f"Updated repository context: client_account_id={client_account_id}, engagement_id={engagement_id}, user_id={user_id}"
        )


class BaseRepository(ContextAwareRepository):
    """Extended base repository with common CRUD operations."""

    def __init__(
        self,
        db: Session,
        model_class: Any,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ):
        super().__init__(db, client_account_id, engagement_id, user_id)
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[Any]:
        """Get an entity by ID with context filtering."""
        query = self.db.query(self.model_class).filter(self.model_class.id == id)
        query = self._apply_context_filter(query, self.model_class)
        return query.first()

    def get_all(
        self, limit: int = 100, offset: int = 0, filters: Optional[dict] = None
    ) -> list:
        """Get all entities with context filtering and optional additional filters."""
        query = self.db.query(self.model_class)
        query = self._apply_context_filter(query, self.model_class)

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    query = query.filter(getattr(self.model_class, key) == value)

        return query.offset(offset).limit(limit).all()

    def create(self, data: dict) -> Any:
        """Create a new entity with context fields."""
        data = self._set_context_fields(data)
        entity = self.model_class(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, id: int, data: dict) -> Optional[Any]:
        """Update an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return None

        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return False

        self.db.delete(entity)
        self.db.commit()
        return True

    def count(self, filters: Optional[dict] = None) -> int:
        """Count entities with context filtering and optional additional filters."""
        query = self.db.query(self.model_class)
        query = self._apply_context_filter(query, self.model_class)

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    query = query.filter(getattr(self.model_class, key) == value)

        return query.count()
