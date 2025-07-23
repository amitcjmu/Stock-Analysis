"""
ADR-012 Status Synchronization Operations

This module contains methods for atomic status synchronization between
master flow orchestrator and individual flow implementations.
"""

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.flow_status_sync import FlowStatusSyncService
from app.services.mfo_sync_agent import MFOSyncAgent

logger = get_logger(__name__)


class StatusSyncOperations:
    """Handles ADR-012 compliant status synchronization operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.status_sync_service = FlowStatusSyncService(db, context)
        self.mfo_sync_agent = MFOSyncAgent(db, context)

    async def start_flow_with_atomic_sync(
        self, flow_id: str, flow_type: str
    ) -> Dict[str, Any]:
        """Start a flow with atomic status synchronization"""
        return await self.status_sync_service.start_flow(flow_id, flow_type)

    async def pause_flow_with_atomic_sync(
        self, flow_id: str, flow_type: str, reason: str = "user_requested"
    ) -> Dict[str, Any]:
        """Pause a flow with atomic status synchronization"""
        return await self.status_sync_service.pause_flow(flow_id, flow_type, reason)

    async def resume_flow_with_atomic_sync(
        self, flow_id: str, flow_type: str
    ) -> Dict[str, Any]:
        """Resume a flow with atomic status synchronization"""
        return await self.status_sync_service.resume_flow(flow_id, flow_type)

    async def reconcile_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Reconcile master flow status using MFO sync agent"""
        return await self.mfo_sync_agent.reconcile_master_status(flow_id)

    async def monitor_flow_health(self) -> Dict[str, Any]:
        """Monitor flow health and fix inconsistencies"""
        return await self.mfo_sync_agent.monitor_flows_health()
