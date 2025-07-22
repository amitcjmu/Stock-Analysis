"""
Pagination utilities for database queries.
Provides consistent pagination patterns and metadata generation.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 50
    
    def __post_init__(self):
        """Validate pagination parameters."""
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 50
        if self.page_size > 1000:
            self.page_size = 1000
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size

@dataclass
class PaginationResult(Generic[T]):
    """Pagination result containing data and metadata."""
    data: List[T]
    total_items: int
    page: int
    page_size: int
    total_pages: int
    has_previous: bool
    has_next: bool
    previous_page: Optional[int] = None
    next_page: Optional[int] = None
    
    @classmethod
    def create(cls, data: List[T], total_items: int, page: int, page_size: int) -> 'PaginationResult[T]':
        """Create pagination result with calculated metadata."""
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
        has_previous = page > 1
        has_next = page < total_pages
        
        return cls(
            data=data,
            total_items=total_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_previous=has_previous,
            has_next=has_next,
            previous_page=page - 1 if has_previous else None,
            next_page=page + 1 if has_next else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pagination result to dictionary."""
        return {
            "data": self.data,
            "pagination": {
                "total_items": self.total_items,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_previous": self.has_previous,
                "has_next": self.has_next,
                "previous_page": self.previous_page,
                "next_page": self.next_page
            }
        }

class PaginationHelper:
    """Helper class for database pagination operations."""
    
    @staticmethod
    async def paginate_query(
        session: AsyncSession,
        query: Select,
        page: int = 1,
        page_size: int = 50
    ) -> PaginationResult[Any]:
        """
        Paginate a database query and return results with metadata.
        
        Args:
            session: Database session
            query: SQLAlchemy select query
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            PaginationResult with data and metadata
        """
        params = PaginationParams(page, page_size)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await session.execute(count_query)
        total_items = total_count_result.scalar() or 0
        
        # Apply pagination to original query
        paginated_query = query.offset(params.offset).limit(params.limit)
        
        # Execute paginated query
        result = await session.execute(paginated_query)
        data = result.scalars().all()
        
        logger.debug(f"Paginated query: page={page}, page_size={page_size}, total_items={total_items}")
        
        return PaginationResult.create(data, total_items, page, page_size)
    
    @staticmethod
    async def paginate_model(
        session: AsyncSession,
        model_class: type,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> PaginationResult[Any]:
        """
        Paginate a model with optional filters and ordering.
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            page: Page number (1-based)
            page_size: Number of items per page
            filters: Optional filters to apply
            order_by: Optional field to order by
            
        Returns:
            PaginationResult with data and metadata
        """
        # Build base query
        query = select(model_class)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(model_class, field) and value is not None:
                    query = query.where(getattr(model_class, field) == value)
        
        # Apply ordering
        if order_by and hasattr(model_class, order_by):
            query = query.order_by(getattr(model_class, order_by))
        
        return await PaginationHelper.paginate_query(session, query, page, page_size)

# Convenience functions
def create_pagination_metadata(total_items: int, page: int, page_size: int) -> Dict[str, Any]:
    """Create pagination metadata dictionary."""
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
    has_previous = page > 1
    has_next = page < total_pages
    
    return {
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_previous": has_previous,
        "has_next": has_next,
        "previous_page": page - 1 if has_previous else None,
        "next_page": page + 1 if has_next else None
    }

def apply_pagination(query: Select, page: int = 1, page_size: int = 50) -> Select:
    """Apply pagination to a SQLAlchemy query."""
    params = PaginationParams(page, page_size)
    return query.offset(params.offset).limit(params.limit)

async def get_total_count(session: AsyncSession, query: Select) -> int:
    """Get total count for a query."""
    count_query = select(func.count()).select_from(query.subquery())
    result = await session.execute(count_query)
    return result.scalar() or 0

# Pagination decorators and utilities
def validate_pagination_params(page: int, page_size: int) -> PaginationParams:
    """Validate and normalize pagination parameters."""
    return PaginationParams(page, page_size)

def calculate_pagination_range(current_page: int, total_pages: int, max_visible: int = 10) -> List[int]:
    """Calculate pagination range for UI display."""
    if total_pages <= max_visible:
        return list(range(1, total_pages + 1))
    
    # Calculate start and end of visible range
    half_visible = max_visible // 2
    start = max(1, current_page - half_visible)
    end = min(total_pages, start + max_visible - 1)
    
    # Adjust start if we're near the end
    if end - start + 1 < max_visible:
        start = max(1, end - max_visible + 1)
    
    return list(range(start, end + 1))