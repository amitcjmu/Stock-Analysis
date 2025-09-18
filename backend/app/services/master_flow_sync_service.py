"""
Master Flow Synchronization Service - Backward Compatibility Wrapper

This module maintains backward compatibility while the actual implementation
has been modularized into the master_flow_sync_service/ directory.
"""

# Import everything from the modularized implementation
from .master_flow_sync_service.models import FlowSyncStatus, SyncResult
from .master_flow_sync_service.service import MasterFlowSyncService
from .master_flow_sync_service.mappers import FlowStatusMapper
from .master_flow_sync_service.database import FlowSyncDatabase

# Ensure backward compatibility
__all__ = [
    "FlowSyncStatus",
    "SyncResult",
    "MasterFlowSyncService",
    "FlowStatusMapper",
    "FlowSyncDatabase",
]
