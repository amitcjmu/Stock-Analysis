"""
Query builder utilities for common database operations.
Provides reusable query construction patterns and filters.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operator enumeration."""

    EQ = "eq"  # Equal
    NE = "ne"  # Not Equal
    GT = "gt"  # Greater Than
    GTE = "gte"  # Greater Than or Equal
    LT = "lt"  # Less Than
    LTE = "lte"  # Less Than or Equal
    LIKE = "like"  # Like (contains)
    ILIKE = "ilike"  # Case-insensitive Like
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class QueryFilter:
    """Query filter specification."""

    field: str
    operator: FilterOperator
    value: Any = None

    def apply(self, query: Select, model_class: Type) -> Select:
        """Apply filter to query."""
        if not hasattr(model_class, self.field):
            logger.warning(
                f"Model {model_class.__name__} does not have field {self.field}"
            )
            return query

        field_attr = getattr(model_class, self.field)

        if self.operator == FilterOperator.EQ:
            return query.where(field_attr == self.value)
        elif self.operator == FilterOperator.NE:
            return query.where(field_attr != self.value)
        elif self.operator == FilterOperator.GT:
            return query.where(field_attr > self.value)
        elif self.operator == FilterOperator.GTE:
            return query.where(field_attr >= self.value)
        elif self.operator == FilterOperator.LT:
            return query.where(field_attr < self.value)
        elif self.operator == FilterOperator.LTE:
            return query.where(field_attr <= self.value)
        elif self.operator == FilterOperator.LIKE:
            return query.where(field_attr.like(f"%{self.value}%"))
        elif self.operator == FilterOperator.ILIKE:
            return query.where(field_attr.ilike(f"%{self.value}%"))
        elif self.operator == FilterOperator.IN:
            return query.where(field_attr.in_(self.value))
        elif self.operator == FilterOperator.NOT_IN:
            return query.where(~field_attr.in_(self.value))
        elif self.operator == FilterOperator.IS_NULL:
            return query.where(field_attr.is_(None))
        elif self.operator == FilterOperator.IS_NOT_NULL:
            return query.where(field_attr.is_not(None))
        else:
            logger.warning(f"Unknown filter operator: {self.operator}")
            return query


@dataclass
class QuerySort:
    """Query sort specification."""

    field: str
    order: SortOrder = SortOrder.ASC

    def apply(self, query: Select, model_class: Type) -> Select:
        """Apply sort to query."""
        if not hasattr(model_class, self.field):
            logger.warning(
                f"Model {model_class.__name__} does not have field {self.field}"
            )
            return query

        field_attr = getattr(model_class, self.field)

        if self.order == SortOrder.ASC:
            return query.order_by(field_attr.asc())
        else:
            return query.order_by(field_attr.desc())


@dataclass
class QueryPagination:
    """Query pagination specification."""

    page: int = 1
    page_size: int = 50

    def apply(self, query: Select) -> Select:
        """Apply pagination to query."""
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 50
        if self.page_size > 1000:
            self.page_size = 1000

        offset = (self.page - 1) * self.page_size
        return query.offset(offset).limit(self.page_size)


class QueryBuilder:
    """
    Fluent query builder for common database operations.
    """

    def __init__(self, model_class: Type):
        self.model_class = model_class
        self._query = select(model_class)
        self._filters: List[QueryFilter] = []
        self._sorts: List[QuerySort] = []
        self._pagination: Optional[QueryPagination] = None
        self._multi_tenant_context: Optional[Dict[str, Any]] = None

    def filter(
        self, field: str, operator: FilterOperator, value: Any = None
    ) -> "QueryBuilder":
        """Add a filter to the query."""
        self._filters.append(QueryFilter(field, operator, value))
        return self

    def filter_by(self, **kwargs) -> "QueryBuilder":
        """Add equality filters using keyword arguments."""
        for field, value in kwargs.items():
            self._filters.append(QueryFilter(field, FilterOperator.EQ, value))
        return self

    def like(self, field: str, value: str) -> "QueryBuilder":
        """Add a LIKE filter."""
        self._filters.append(QueryFilter(field, FilterOperator.LIKE, value))
        return self

    def ilike(self, field: str, value: str) -> "QueryBuilder":
        """Add a case-insensitive LIKE filter."""
        self._filters.append(QueryFilter(field, FilterOperator.ILIKE, value))
        return self

    def in_(self, field: str, values: List[Any]) -> "QueryBuilder":
        """Add an IN filter."""
        self._filters.append(QueryFilter(field, FilterOperator.IN, values))
        return self

    def not_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """Add a NOT IN filter."""
        self._filters.append(QueryFilter(field, FilterOperator.NOT_IN, values))
        return self

    def is_null(self, field: str) -> "QueryBuilder":
        """Add an IS NULL filter."""
        self._filters.append(QueryFilter(field, FilterOperator.IS_NULL))
        return self

    def is_not_null(self, field: str) -> "QueryBuilder":
        """Add an IS NOT NULL filter."""
        self._filters.append(QueryFilter(field, FilterOperator.IS_NOT_NULL))
        return self

    def sort(self, field: str, order: SortOrder = SortOrder.ASC) -> "QueryBuilder":
        """Add a sort to the query."""
        self._sorts.append(QuerySort(field, order))
        return self

    def sort_by(self, field: str, ascending: bool = True) -> "QueryBuilder":
        """Add a sort with boolean direction."""
        order = SortOrder.ASC if ascending else SortOrder.DESC
        self._sorts.append(QuerySort(field, order))
        return self

    def paginate(self, page: int, page_size: int = 50) -> "QueryBuilder":
        """Add pagination to the query."""
        self._pagination = QueryPagination(page, page_size)
        return self

    def with_tenant_context(
        self,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> "QueryBuilder":
        """Add multi-tenant context to the query."""
        self._multi_tenant_context = {
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
        }
        return self

    def build(self) -> Select:
        """Build the final query."""
        query = self._query

        # Apply multi-tenant filters first
        if self._multi_tenant_context:
            query = self._apply_tenant_filters(query)

        # Apply filters
        for filter_spec in self._filters:
            query = filter_spec.apply(query, self.model_class)

        # Apply sorts
        for sort_spec in self._sorts:
            query = sort_spec.apply(query, self.model_class)

        # Apply pagination
        if self._pagination:
            query = self._pagination.apply(query)

        return query

    def _apply_tenant_filters(self, query: Select) -> Select:
        """Apply multi-tenant filters to query."""
        filters = []

        if self._multi_tenant_context.get("client_account_id") and hasattr(
            self.model_class, "client_account_id"
        ):
            filters.append(
                self.model_class.client_account_id
                == self._multi_tenant_context["client_account_id"]
            )

        if self._multi_tenant_context.get("engagement_id") and hasattr(
            self.model_class, "engagement_id"
        ):
            filters.append(
                self.model_class.engagement_id
                == self._multi_tenant_context["engagement_id"]
            )

        if filters:
            query = query.where(and_(*filters))

        return query

    async def execute(self, session: AsyncSession) -> List[Any]:
        """Execute the query and return results."""
        query = self.build()
        result = await session.execute(query)
        return result.scalars().all()

    async def count(self, session: AsyncSession) -> int:
        """Execute a count query."""
        # Build count query without pagination
        query = select(func.count()).select_from(self.model_class)

        # Apply multi-tenant filters
        if self._multi_tenant_context:
            query = self._apply_tenant_filters(query)

        # Apply filters
        for filter_spec in self._filters:
            query = filter_spec.apply(query, self.model_class)

        result = await session.execute(query)
        return result.scalar()


# Convenience functions
def build_context_query(
    model_class: Type,
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
) -> QueryBuilder:
    """Build query with multi-tenant context."""
    return QueryBuilder(model_class).with_tenant_context(
        client_account_id, engagement_id
    )


def build_paginated_query(
    model_class: Type, page: int = 1, page_size: int = 50
) -> QueryBuilder:
    """Build paginated query."""
    return QueryBuilder(model_class).paginate(page, page_size)


def build_filtered_query(model_class: Type, filters: Dict[str, Any]) -> QueryBuilder:
    """Build query with filters."""
    builder = QueryBuilder(model_class)
    return builder.filter_by(**filters)


def apply_multi_tenant_filter(
    query: Select,
    model_class: Type,
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
) -> Select:
    """Apply multi-tenant filtering to existing query."""
    filters = []

    if client_account_id and hasattr(model_class, "client_account_id"):
        filters.append(model_class.client_account_id == client_account_id)

    if engagement_id and hasattr(model_class, "engagement_id"):
        filters.append(model_class.engagement_id == engagement_id)

    if filters:
        return query.where(and_(*filters))

    return query
