"""
Enhanced dependency repository for application and server relationships.

This module is modularized to meet pre-commit file length requirements (< 400 lines per file).
The DependencyRepository class is composed of multiple mixins for different functionality areas.
"""

from app.repositories.dependency_repository.app_app_queries import AppAppQueryMixin
from app.repositories.dependency_repository.app_server_queries import (
    AppServerQueryMixin,
)
from app.repositories.dependency_repository.base import (
    DependencyRepository as BaseDependencyRepository,
)
from app.repositories.dependency_repository.flow_queries import FlowQueryMixin
from app.repositories.dependency_repository.generic_commands import GenericCommandMixin


class DependencyRepository(
    BaseDependencyRepository,
    AppServerQueryMixin,
    AppAppQueryMixin,
    FlowQueryMixin,
    GenericCommandMixin,
):
    """
    Enhanced dependency repository with application-specific operations.

    Combines functionality from multiple mixins:
    - AppServerQueryMixin: Application-to-server dependency queries
    - AppAppQueryMixin: Application-to-application dependency queries
    - FlowQueryMixin: Assessment Flow-specific dependency queries
    - GenericCommandMixin: Generic dependency creation operations
    """

    pass


__all__ = ["DependencyRepository"]
