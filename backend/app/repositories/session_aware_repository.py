"""
Session-aware repository for multi-tenant data access with session support.
Extends ContextAwareRepository to add session-level filtering and deduplication.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy import and_, or_, func, distinct, desc
from sqlalchemy.future import select
from sqlalchemy.sql import Select
import logging

from .context_aware_repository import ContextAwareRepository
from app.core.context import get_current_context, get_session_id

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar('ModelType')


class SessionAwareRepository(ContextAwareRepository[ModelType]):
    """
    Repository that supports both session-specific and engagement-level views.
    
    Modes:
    - session_view: Shows data only from the current session
    - engagement_view: Shows deduplicated data across all sessions in engagement
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        model_class: Type[ModelType],
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        session_id: Optional[str] = None,
        view_mode: str = "engagement_view"  # "session_view" or "engagement_view"
    ):
        """
        Initialize session-aware repository.
        
        Args:
            db: Async database session
            model_class: SQLAlchemy model class
            client_account_id: Client account UUID for multi-tenant scoping
            engagement_id: Engagement UUID for project scoping
            session_id: Session UUID for session scoping
            view_mode: "session_view" or "engagement_view"
        """
        super().__init__(db, model_class, client_account_id, engagement_id)
        self.session_id = session_id
        self.view_mode = view_mode
        
        # Check if model supports session fields
        self.has_session = hasattr(model_class, 'session_id')
        
        logger.debug(f"Initialized {model_class.__name__} session-aware repository with "
                    f"view_mode={view_mode}, session_id={session_id}")
    
    def _apply_session_filter(self, query: Select) -> Select:
        """
        Apply session filters based on view mode.
        
        Args:
            query: SQLAlchemy select query
            
        Returns:
            Query with session filters applied
        """
        # First apply base context filters (client/engagement)
        query = self._apply_context_filter(query)
        
        # Apply session filters if supported
        if self.has_session:
            if self.view_mode == "session_view" and self.session_id:
                # Session view: only current session data
                query = query.where(self.model_class.session_id == self.session_id)
                logger.debug(f"Applied session filter: session_id={self.session_id}")
            elif self.view_mode == "engagement_view":
                # Engagement view: all sessions in engagement (handled by deduplication)
                # No additional session filter needed here
                pass
        
        return query
    
    def _apply_session_to_instance(self, instance: ModelType) -> ModelType:
        """
        Apply session context to a model instance before saving.
        
        Args:
            instance: Model instance to update
            
        Returns:
            Updated model instance
        """
        # Apply base context (client/engagement)
        instance = self._apply_context_to_instance(instance)
        
        # Set session if supported and provided
        if self.has_session and self.session_id:
            setattr(instance, 'session_id', self.session_id)
            
        return instance
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID with session filtering.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model_class).where(self.model_class.id == id)
        query = self._apply_session_filter(query)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ModelType]:
        """
        Get all records with session filtering and optional deduplication.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        if self.view_mode == "engagement_view" and self.has_session:
            # Use deduplication for engagement view
            return await self._get_deduplicated_records(limit=limit, offset=offset)
        else:
            # Standard session view
            query = select(self.model_class)
            query = self._apply_session_filter(query)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            result = await self.db.execute(query)
            return result.scalars().all()
    
    async def get_by_filters(self, **filters) -> List[ModelType]:
        """
        Get records by field filters with session filtering.
        
        Args:
            **filters: Field name and value pairs for filtering
            
        Returns:
            List of matching model instances
        """
        if self.view_mode == "engagement_view" and self.has_session:
            # Use deduplication for engagement view
            return await self._get_deduplicated_records(filters=filters)
        else:
            # Standard session view
            query = select(self.model_class)
            
            # Apply field filters
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
            
            # Apply session filters
            query = self._apply_session_filter(query)
            
            result = await self.db.execute(query)
            return result.scalars().all()
    
    async def create(self, **data) -> ModelType:
        """
        Create a new record with session context applied.
        
        Args:
            **data: Field values for the new record
            
        Returns:
            Created model instance
        """
        instance = self.model_class(**data)
        instance = self._apply_session_to_instance(instance)
        
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        
        logger.info(f"Created {self.model_class.__name__} with ID {instance.id} in session {self.session_id}")
        return instance
    
    async def _get_deduplicated_records(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """
        Get deduplicated records across all sessions in engagement.
        
        This method implements smart deduplication logic for engagement-level views.
        It prioritizes the most recent session data for each unique asset.
        
        Args:
            filters: Optional field filters
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of deduplicated model instances
        """
        # Check if model has deduplication key (usually hostname or similar)
        dedup_field = None
        for field_name in ['hostname', 'name', 'asset_name', 'identifier']:
            if hasattr(self.model_class, field_name):
                dedup_field = getattr(self.model_class, field_name)
                break
        
        if not dedup_field:
            logger.warning(f"No deduplication field found for {self.model_class.__name__}, using regular query")
            return await self.get_by_filters(**(filters or {}))
        
        # Build subquery to get latest session for each unique asset
        # Use created_at timestamp to determine latest session since UUID max() is not supported
        latest_records_subquery = (
            select(
                dedup_field,
                self.model_class.session_id,
                func.row_number().over(
                    partition_by=dedup_field,
                    order_by=desc(self.model_class.created_at)
                ).label('row_num')
            )
        )
        
        # Apply context filters to latest records subquery
        latest_records_subquery = self._apply_context_filter(latest_records_subquery)
        
        # Apply field filters to latest records subquery if provided
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    if isinstance(value, list):
                        latest_records_subquery = latest_records_subquery.where(field.in_(value))
                    else:
                        latest_records_subquery = latest_records_subquery.where(field == value)
        
        latest_records_subquery = latest_records_subquery.alias('latest_records')
        
        # Subquery to get only the latest record for each asset (row_num = 1)
        subquery = (
            select(
                latest_records_subquery.c[dedup_field.name],
                latest_records_subquery.c.session_id.label('latest_session_id')
            )
            .where(latest_records_subquery.c.row_num == 1)
        )
        
        subquery = subquery.alias('latest_assets')
        
        # Main query to get full records for latest sessions
        query = select(self.model_class).join(
            subquery,
            and_(
                dedup_field == subquery.c[dedup_field.name],
                self.model_class.session_id == subquery.c.latest_session_id
            )
        )
        
        # Apply context filters to main query
        query = self._apply_context_filter(query)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        logger.debug(f"Deduplicated query returned {len(records)} records for {self.model_class.__name__}")
        return records
    
    async def count(self, **filters) -> int:
        """
        Count records with session filtering and optional deduplication.
        
        Args:
            **filters: Field name and value pairs for filtering
            
        Returns:
            Number of matching records
        """
        if self.view_mode == "engagement_view" and self.has_session:
            # Count deduplicated records
            records = await self._get_deduplicated_records(filters=filters)
            return len(records)
        else:
            # Standard session count
            query = select(func.count(self.model_class.id))
            
            # Apply field filters
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
            
            # Apply session filters
            query = self._apply_session_filter(query)
            
            result = await self.db.execute(query)
            return result.scalar()
    
    def switch_view_mode(self, view_mode: str) -> None:
        """
        Switch between session_view and engagement_view modes.
        
        Args:
            view_mode: "session_view" or "engagement_view"
        """
        if view_mode not in ["session_view", "engagement_view"]:
            raise ValueError("view_mode must be 'session_view' or 'engagement_view'")
        
        self.view_mode = view_mode
        logger.info(f"Switched {self.model_class.__name__} repository to {view_mode}")
    
    def set_session_context(self, session_id: str) -> None:
        """
        Update session context for the repository.
        
        Args:
            session_id: New session ID to use
        """
        self.session_id = session_id
        logger.info(f"Updated {self.model_class.__name__} repository session context to {session_id}")


def create_session_aware_repository(
    db: AsyncSession,
    model_class: Type[ModelType],
    view_mode: str = "engagement_view"
) -> SessionAwareRepository[ModelType]:
    """
    Factory function to create session-aware repository with current context.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class
        view_mode: "session_view" or "engagement_view"
        
    Returns:
        Configured SessionAwareRepository instance
    """
    context = get_current_context()
    
    return SessionAwareRepository(
        db=db,
        model_class=model_class,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        session_id=context.session_id,
        view_mode=view_mode
    ) 