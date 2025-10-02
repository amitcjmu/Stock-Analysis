"""
Flow State Manager - Query Operations
Handles all read operations for flow state
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from ..persistence.postgres_store import PostgresFlowStateStore
from ..flow_state_utils import build_unified_discovery_state

logger = logging.getLogger(__name__)


class FlowStateQueries:
    """Handles all read operations for flow state"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)

    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current flow state for agent analysis

        ADR-012: Uses child flow data for operational decisions, not master flow
        """
        try:
            # ADR-012: Get operational state from child flow repository
            logger.info(
                f"🔄 [ADR-012] Getting operational state from child flow: {flow_id}"
            )

            # First, determine flow type to get appropriate child flow
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            master_repo = CrewAIFlowStateExtensionsRepository(
                self.db,
                self.context.client_account_id,
                self.context.engagement_id,
                self.context.user_id,
            )
            master_flow = await master_repo.get_by_flow_id(flow_id)

            if not master_flow:
                logger.warning(f"⚠️ Master flow not found: {flow_id}")
                return None

            # Get child flow based on type (assuming discovery for now)
            if master_flow.flow_type == "discovery":
                from app.repositories.discovery_flow_repository import (
                    DiscoveryFlowRepository,
                )

                child_repo = DiscoveryFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
                child_flow = await child_repo.get_by_flow_id(flow_id)

                if child_flow:
                    # Load persisted state JSON for null-safe access to validation_results
                    base_state = await self.store.load_state(flow_id) or {}

                    # Create UnifiedDiscoveryFlowState from child flow operational data
                    state = build_unified_discovery_state(
                        self.context, flow_id, child_flow, base_state
                    )

                    logger.info(
                        f"✅ [ADR-012] Operational state loaded from child flow: {flow_id}"
                    )
                    return state
                else:
                    logger.warning(f"⚠️ Child flow not found: {flow_id}")
                    return None
            else:
                # For non-discovery flows, fall back to master flow data (to be expanded)
                logger.warning(
                    f"⚠️ [ADR-012] Non-discovery flow type not yet supported: {master_flow.flow_type}"
                )
                # Fall back to original behavior for now
                state = await self.store.load_state(flow_id)
                if state:
                    return state
                else:
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to get flow state for {flow_id}: {e}")
            return None

    async def get_flow_history(self, flow_id: str) -> Dict[str, Any]:
        """Get complete history for a flow"""
        try:
            # Import here to avoid circular imports
            from ..persistence.state_recovery import FlowStateRecovery

            recovery = FlowStateRecovery(self.db, self.context)

            # Get current state
            current_state = await self.store.load_state(flow_id)

            # Get version history
            versions = await self.store.get_flow_versions(flow_id)

            # Get recovery status
            recovery_status = await recovery.get_recovery_status(flow_id)

            return {
                "flow_id": flow_id,
                "current_state": current_state,
                "version_history": versions,
                "recovery_status": recovery_status,
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get flow history for {flow_id}: {e}")
            return {
                "flow_id": flow_id,
                "error": str(e),
                "retrieved_at": datetime.utcnow().isoformat(),
            }


async def get_flow_summary(flow_id: str, context: RequestContext) -> Dict[str, Any]:
    """Get a summary of flow state"""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        queries = FlowStateQueries(db, context)
        state = await queries.get_flow_state(flow_id)

        if not state:
            return {"flow_id": flow_id, "status": "not_found"}

        return {
            "flow_id": flow_id,
            "current_phase": state.get("current_phase"),
            "status": state.get("status"),
            "progress_percentage": state.get("progress_percentage"),
            "errors_count": len(state.get("errors", [])),
            "warnings_count": len(state.get("warnings", [])),
            "last_updated": state.get("updated_at"),
            "phase_completion": state.get("phase_completion", {}),
        }
