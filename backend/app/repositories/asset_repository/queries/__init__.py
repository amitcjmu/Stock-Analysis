"""
Asset Repository Query Operations

Handles all read-only operations for assets, including:
- Basic queries by attribute (hostname, type, environment, etc.)
- Search and filtering operations
- Analytics and aggregation queries
- Master flow and phase progression queries

This package is modularized for maintainability:
- base.py: Base query classes with common filtering
- asset_queries.py: Asset-specific queries
- analytics_queries.py: Data quality and analytics queries
- dependency_queries.py: Asset dependency queries
- workflow_queries.py: Workflow progress queries
"""

from app.repositories.asset_repository.queries.analytics_queries import (
    AssetAnalyticsQueries,
)
from app.repositories.asset_repository.queries.asset_queries import AssetQueries
from app.repositories.asset_repository.queries.dependency_queries import (
    AssetDependencyQueries,
)
from app.repositories.asset_repository.queries.workflow_queries import (
    WorkflowProgressQueries,
)

__all__ = [
    "AssetQueries",
    "AssetAnalyticsQueries",
    "AssetDependencyQueries",
    "WorkflowProgressQueries",
]
