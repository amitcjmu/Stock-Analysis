"""
Deduplicating repository for multi-tenant data access.
Extends ContextAwareRepository to add deduplication for engagement-level views.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc
from sqlalchemy.future import select
from sqlalchemy.sql import Select
import logging

from .context_aware_repository import ContextAwareRepository
from app.core.context import get_current_context

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar('ModelType')


class DeduplicatingRepository(ContextAwareRepository[ModelType]):
    """
    Repository that provides a deduplicated view of data across an engagement.
    It can also be scoped to a specific data import session.
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        model_class: Type[ModelType],
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        flow_id: Optional[str] = None
    ):
        """
        Initialize deduplicating repository.
        
        Args:
            db: Async database session
            model_class: SQLAlchemy model class
            client_account_id: Client account UUID for multi-tenant scoping
            engagement_id: Engagement UUID for project scoping
            flow_id: Optional flow UUID to scope the repository
        """
        super().__init__(db, model_class, client_account_id, engagement_id)
        self.flow_id = flow_id
        self.has_flow = hasattr(model_class, 'flow_id')
        logger.debug(f"Initialized {model_class.__name__} deduplicating repository. Flow-scoped: {self.flow_id is not None}")

    def _apply_context_filter(self, query: Select) -> Select:
        """
        Apply context filters (client, engagement, and session if provided).
        
        Args:
            query: SQLAlchemy select query
            
        Returns:
            Query with context filters applied
        """
        query = super()._apply_context_filter(query)
        if self.flow_id and self.has_flow:
            query = query.where(self.model_class.flow_id == self.flow_id)
            logger.debug(f"Applied flow filter: {self.flow_id}")
        return query

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model_class).where(self.model_class.id == id)
        query = self._apply_context_filter(query)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ModelType]:
        """
        Get all records with deduplication.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        if self.flow_id:
            # If scoped to a session, don't deduplicate, just get all from that session
            query = select(self.model_class)
            query = self._apply_context_filter(query)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()

        return await self._get_deduplicated_records(limit=limit, offset=offset)
    
    async def get_by_filters(self, **filters) -> List[ModelType]:
        """
        Get records by field filters with deduplication.
        
        Args:
            **filters: Field name and value pairs for filtering
            
        Returns:
            List of matching model instances
        """
        if self.flow_id:
            query = select(self.model_class)
            query = self._apply_context_filter(query)
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
            result = await self.db.execute(query)
            return result.scalars().all()
            
        return await self._get_deduplicated_records(filters=filters)
    
    async def create(self, **data) -> ModelType:
        """
        Create a new record with context applied.
        
        Args:
            **data: Field values for the new record
            
        Returns:
            Created model instance
        """
        instance = self.model_class(**data)
        instance = self._apply_context_to_instance(instance)
        
        # If the model supports flow_id and the repo is scoped, set it.
        if self.flow_id and self.has_flow:
            setattr(instance, 'flow_id', self.flow_id)
        
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        
        logger.info(f"Created {self.model_class.__name__} with ID {instance.id}")
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
        
        if not dedup_field or not self.has_flow:
            logger.warning(f"No deduplication field or flow_id found for {self.model_class.__name__}, returning regular query.")
            # Fallback to non-deduplicated query if model doesn't support it
            query = select(self.model_class)
            query = self._apply_context_filter(query)
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        query = query.where(getattr(self.model_class, field) == value)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()

        # Build subquery to get latest session for each unique asset
        # Use created_at timestamp to determine latest session since UUID max() is not supported
        latest_records_subquery = (
            select(
                dedup_field,
                self.model_class.flow_id,
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
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    latest_records_subquery = latest_records_subquery.where(getattr(self.model_class, field) == value)

        subquery = latest_records_subquery.alias("latest_records_subquery")
        
        query = (
            select(self.model_class)
            .join(subquery, and_(
                dedup_field == subquery.c[dedup_field.name],
                self.model_class.flow_id == subquery.c.flow_id
            ))
            .where(subquery.c.row_num == 1)
        )

        # Apply context filters to the main query as well
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
        Count records, with deduplication.
        
        Args:
            **filters: Field filters
            
        Returns:
            Count of records
        """
        # For a deduplicated count, we count the distinct values of the dedup field
        dedup_field = None
        for field_name in ['hostname', 'name', 'asset_name', 'identifier']:
            if hasattr(self.model_class, field_name):
                dedup_field = getattr(self.model_class, field_name)
                break

        if not dedup_field or not self.has_flow:
            logger.warning(f"Cannot perform deduplicated count for {self.model_class.__name__}")
            return await super().count(**filters)

        query = select(func.count(distinct(dedup_field)))
        query = self._apply_context_filter(query)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)

        result = await self.db.execute(query)
        return result.scalar_one()

def create_deduplicating_repository(
    db: AsyncSession,
    model_class: Type[ModelType]
) -> DeduplicatingRepository[ModelType]:
    """
    Factory function to create a DeduplicatingRepository with context.
    
    This function extracts the current request's context and creates a
    repository instance scoped to that context.
    
    Args:
        db: Async database session from dependency injection
        model_class: The SQLAlchemy model class for the repository
        
    Returns:
        An instance of DeduplicatingRepository for the given model
    """
    context = get_current_context()
    return DeduplicatingRepository(
        db=db,
        model_class=model_class,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id
    ) 