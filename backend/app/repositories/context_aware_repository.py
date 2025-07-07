"""
Context-aware repository base class for multi-tenant data access.
Ensures all data operations are scoped to client account and engagement.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy import and_, or_
from sqlalchemy.future import select
from sqlalchemy.sql import Select
import logging

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar('ModelType')


class ContextAwareRepository(Generic[ModelType]):
    """
    Base repository class that automatically applies client account and engagement scoping.
    All queries are automatically filtered by the provided context.
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        model_class: Type[ModelType],
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None
    ):
        """
        Initialize repository with database session and context.
        
        Args:
            db: Async database session
            model_class: SQLAlchemy model class
            client_account_id: Client account UUID for multi-tenant scoping
            engagement_id: Engagement UUID for project scoping
        """
        self.db = db
        self.model_class = model_class
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        
        # Check if model supports multi-tenant fields
        self.has_client_account = hasattr(model_class, 'client_account_id')
        self.has_engagement = hasattr(model_class, 'engagement_id')
        
        # SECURITY: Enforce client context for multi-tenant models
        if self.has_client_account and not client_account_id:
            raise ValueError(
                f"SECURITY: Client account ID is required for multi-tenant model {model_class.__name__}. "
                f"This is a critical security requirement to prevent cross-tenant data access."
            )
        
        logger.debug(f"Initialized {model_class.__name__} repository with context: "
                    f"client_account_id={client_account_id}, engagement_id={engagement_id}")
    
    def _apply_context_filter(self, query: Select) -> Select:
        """
        Apply client account and engagement filters to a query.
        
        Args:
            query: SQLAlchemy select query
            
        Returns:
            Query with context filters applied
        """
        filters = []
        
        # SECURITY: Always apply client account filter for multi-tenant models
        if self.has_client_account:
            if not self.client_account_id:
                # This should never happen due to __init__ check, but double-check for security
                raise RuntimeError(
                    f"SECURITY: Attempted to query {self.model_class.__name__} without client context. "
                    f"This is a critical security violation."
                )
            filters.append(self.model_class.client_account_id == self.client_account_id)
        
        # Apply engagement filter if supported and provided
        if self.has_engagement and self.engagement_id:
            filters.append(self.model_class.engagement_id == self.engagement_id)
        
        # Apply filters
        if filters:
            query = query.where(and_(*filters))
            
        return query
    
    def _apply_context_to_instance(self, instance: ModelType) -> ModelType:
        """
        Apply context values to a model instance before saving.
        
        Args:
            instance: Model instance to update
            
        Returns:
            Updated model instance
        """
        # Set client account if supported and provided
        if self.has_client_account and self.client_account_id:
            setattr(instance, 'client_account_id', self.client_account_id)
        
        # Set engagement if supported and provided
        if self.has_engagement and self.engagement_id:
            setattr(instance, 'engagement_id', self.engagement_id)
            
        return instance
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID with context filtering.
        
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
        Get all records with context filtering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        query = select(self.model_class)
        query = self._apply_context_filter(query)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_filters(self, **filters) -> List[ModelType]:
        """
        Get records by field filters with context filtering.
        
        Args:
            **filters: Field name and value pairs for filtering
            
        Returns:
            List of matching model instances
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
        
        # Apply context filters
        query = self._apply_context_filter(query)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, **data) -> ModelType:
        """
        Create a new record with context applied.
        
        Args:
            **data: Field values for the new record
            
        Returns:
            Created model instance
        """
        # Apply field renames if method exists (for backward compatibility)
        if hasattr(self, '_handle_field_renames'):
            data = self._handle_field_renames(data)
        
        instance = self.model_class(**data)
        instance = self._apply_context_to_instance(instance)
        
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        
        logger.info(f"Created {self.model_class.__name__} with ID {instance.id}")
        return instance
    
    async def update(self, id: Any, **data) -> Optional[ModelType]:
        """
        Update a record by ID with context filtering.
        
        Args:
            id: Primary key value
            **data: Field values to update
            
        Returns:
            Updated model instance or None if not found
        """
        # Apply field renames if method exists (for backward compatibility)
        if hasattr(self, '_handle_field_renames'):
            data = self._handle_field_renames(data)
        
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        # Update fields
        for field_name, value in data.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, value)
        
        # Ensure context is maintained
        instance = self._apply_context_to_instance(instance)
        
        await self.db.commit()
        await self.db.refresh(instance)
        
        logger.info(f"Updated {self.model_class.__name__} with ID {id}")
        return instance
    
    async def delete(self, id: Any) -> bool:
        """
        Delete a record by ID with context filtering.
        
        Args:
            id: Primary key value
            
        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        await self.db.delete(instance)
        await self.db.commit()
        
        logger.info(f"Deleted {self.model_class.__name__} with ID {id}")
        return True
    
    async def count(self, **filters) -> int:
        """
        Count records with context filtering.
        
        Args:
            **filters: Optional field filters
            
        Returns:
            Number of matching records
        """
        from sqlalchemy import func
        
        query = select(func.count(self.model_class.id))
        
        # Apply field filters
        for field_name, value in filters.items():
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                query = query.where(field == value)
        
        # Apply context filters
        query = self._apply_context_filter(query)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def bulk_update(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """
        Bulk update records matching filters with context filtering.
        
        Args:
            filters: Conditions for records to update
            updates: Field values to update
            
        Returns:
            Number of updated records
        """
        from sqlalchemy import update
        
        # Build update query
        query = update(self.model_class)
        
        # Apply field filters
        filter_conditions = []
        for field_name, value in filters.items():
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                filter_conditions.append(field == value)
        
        # Apply context filters
        if self.has_client_account and self.client_account_id:
            filter_conditions.append(self.model_class.client_account_id == self.client_account_id)
        if self.has_engagement and self.engagement_id:
            filter_conditions.append(self.model_class.engagement_id == self.engagement_id)
        
        if filter_conditions:
            query = query.where(and_(*filter_conditions))
        
        # Apply updates with context
        update_data = updates.copy()
        if self.has_client_account and self.client_account_id:
            update_data['client_account_id'] = self.client_account_id
        if self.has_engagement and self.engagement_id:
            update_data['engagement_id'] = self.engagement_id
        
        query = query.values(**update_data)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        updated_count = result.rowcount
        logger.info(f"Bulk updated {updated_count} {self.model_class.__name__} records")
        return updated_count
    
    async def query_with_context(self, custom_query: Select) -> List[ModelType]:
        """
        Execute a custom query with context filtering applied.
        
        Args:
            custom_query: Custom SQLAlchemy select query
            
        Returns:
            List of model instances
        """
        query = self._apply_context_filter(custom_query)
        result = await self.db.execute(query)
        return result.scalars().all() 