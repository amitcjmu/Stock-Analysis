"""
Database utilities module for common database operations.
Provides session management, query builders, pagination, and multi-tenant helpers.
"""

from .session_manager import (
    DatabaseSessionManager,
    get_session_with_context,
    get_session_with_timeout,
    SessionConfig,
    DatabaseError,
    SessionTimeoutError,
    ConnectionError
)

from .query_builders import (
    QueryBuilder,
    QueryFilter,
    QuerySort,
    QueryPagination,
    build_context_query,
    build_paginated_query,
    build_filtered_query,
    apply_multi_tenant_filter
)

from .pagination import (
    PaginationHelper,
    PaginationParams,
    PaginationResult,
    create_pagination_metadata,
    apply_pagination,
    get_total_count
)

from .multi_tenant import (
    MultiTenantHelper,
    TenantContext,
    apply_tenant_filter,
    validate_tenant_access,
    get_tenant_context,
    create_tenant_context
)

from .transactions import (
    TransactionManager,
    transaction_scope,
    rollback_on_error,
    commit_or_rollback,
    DatabaseTransaction
)

__all__ = [
    # Session Management
    "DatabaseSessionManager",
    "get_session_with_context",
    "get_session_with_timeout",
    "SessionConfig",
    "DatabaseError",
    "SessionTimeoutError",
    "ConnectionError",
    
    # Query Building
    "QueryBuilder",
    "QueryFilter",
    "QuerySort",
    "QueryPagination",
    "build_context_query",
    "build_paginated_query",
    "build_filtered_query",
    "apply_multi_tenant_filter",
    
    # Pagination
    "PaginationHelper",
    "PaginationParams",
    "PaginationResult",
    "create_pagination_metadata",
    "apply_pagination",
    "get_total_count",
    
    # Multi-Tenant
    "MultiTenantHelper",
    "TenantContext",
    "apply_tenant_filter",
    "validate_tenant_access",
    "get_tenant_context",
    "create_tenant_context",
    
    # Transactions
    "TransactionManager",
    "transaction_scope",
    "rollback_on_error",
    "commit_or_rollback",
    "DatabaseTransaction"
]