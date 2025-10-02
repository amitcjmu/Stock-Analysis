"""
Multi-Tenant Memory Management Service
Handles learning persistence with enterprise privacy controls and data isolation

This module provides backward-compatible exports for the modularized tenant_memory_manager.
"""

# Import enums
from app.services.crewai_flows.memory.tenant_memory_manager.enums import (
    LearningScope,
    MemoryIsolationLevel,
)

# Import models
from app.services.crewai_flows.memory.tenant_memory_manager.models import (
    LearningDataClassification,
)

# Import base class
from app.services.crewai_flows.memory.tenant_memory_manager.base import (
    TenantMemoryManager as _BaseTenantMemoryManager,
)

# Import mixins
from app.services.crewai_flows.memory.tenant_memory_manager.isolation import (
    MemoryIsolationMixin,
)
from app.services.crewai_flows.memory.tenant_memory_manager.storage import StorageMixin
from app.services.crewai_flows.memory.tenant_memory_manager.analytics import (
    AnalyticsMixin,
)
from app.services.crewai_flows.memory.tenant_memory_manager.cleanup import CleanupMixin


# Combine all mixins into the complete TenantMemoryManager class
class TenantMemoryManager(
    _BaseTenantMemoryManager,
    MemoryIsolationMixin,
    StorageMixin,
    AnalyticsMixin,
    CleanupMixin,
):
    """
    Enterprise-grade memory management with multi-tenant isolation
    Supports engagement-scoped, client-scoped, and global learning with privacy controls

    This class combines all functionality from:
    - Base: Initialization and core setup methods
    - MemoryIsolationMixin: Memory creation and privacy control methods
    - StorageMixin: Storage and retrieval operations
    - AnalyticsMixin: Analytics and reporting
    - CleanupMixin: Cleanup and maintenance
    """

    pass


# Export all public API
__all__ = [
    "LearningScope",
    "MemoryIsolationLevel",
    "LearningDataClassification",
    "TenantMemoryManager",
]
