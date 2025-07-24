"""
Flow State Bridge
PostgreSQL-only persistence for CrewAI flows.
Single source of truth implementation replacing dual SQLite/PostgreSQL system.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .persistence.postgres_store import PostgresFlowStateStore

logger = logging.getLogger(__name__)


class FlowStateBridge:
    """
    PostgreSQL-only persistence bridge for CrewAI flows.

    Single source of truth implementation that:
    1. Uses PostgreSQL as the only persistence layer
    2. Provides enterprise multi-tenancy and data isolation
    3. Includes state validation and recovery mechanisms
    4. Supports atomic operations and optimistic locking
    """

    def __init__(self, context: RequestContext):
        """Initialize bridge with tenant context"""
        self.context = context
        self._state_sync_enabled = True
        self._version_cache = {}  # Cache flow versions

    async def initialize_flow(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """
        Initialize flow state in PostgreSQL - alias for backward compatibility.
        """
        return await self.initialize_flow_state(state)

    async def initialize_flow_state(
        self, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """
        Initialize flow state in PostgreSQL as single source of truth.
        Called when flow starts execution.
        """
        try:
            logger.info(f"🔄 Initializing PostgreSQL-only flow state: {state.flow_id}")
            logger.info(f"   📋 Flow context: {state.flow_id}")

            # Use postgres store to persist state
            async with AsyncSessionLocal() as db:
                store = PostgresFlowStateStore(db, self.context)
                await store.save_state(
                    flow_id=state.flow_id,
                    state=state.model_dump(),
                    phase=state.current_phase or "initialized",
                )
                await db.commit()

            logger.info(
                f"✅ PostgreSQL flow state initialized: Flow ID={state.flow_id}"
            )

            return {
                "status": "success",
                "postgresql_persistence": {
                    "status": "success",
                    "flow_id": state.flow_id,
                },
                "persistence_model": "postgresql_only",
                "bridge_enabled": True,
            }

        except Exception as e:
            logger.error(f"❌ PostgreSQL flow state initialization failed: {e}")
            return {
                "status": "failed",
                "postgresql_persistence": {"status": "failed", "error": str(e)},
                "persistence_model": "postgresql_only",
                "bridge_enabled": False,
            }

    async def sync_state_update(
        self,
        state: UnifiedDiscoveryFlowState,
        phase: str,
        crew_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        DELTA TEAM FIX: State updates coordinated through Master Flow Orchestrator only.
        This method now logs state updates but delegates actual persistence to MFO.
        """
        if not self._state_sync_enabled:
            return {"status": "sync_disabled"}

        # FIX: Ensure flow_id is available from state before logging
        flow_id = getattr(state, "flow_id", None) or "MISSING_FLOW_ID"
        if flow_id == "MISSING_FLOW_ID":
            logger.warning(
                "⚠️ Cannot create/update flow - flow_id is missing from state"
            )
            logger.warning(
                f"⚠️ State attributes: {list(vars(state).keys()) if hasattr(state, '__dict__') else 'No __dict__'}"
            )
            return {"status": "missing_flow_id", "error": "flow_id not found in state"}

        # DELTA TEAM FIX: Log the state update but don't perform competing database writes
        logger.info(f"🔄 State update requested for Flow ID: {flow_id}, phase: {phase}")
        logger.info(
            "📋 State update delegated to Master Flow Orchestrator for consistency"
        )

        # Return success to maintain compatibility but indicate delegation
        return {
            "status": "delegated_to_mfo",
            "postgresql_update": {"status": "delegated", "phase": phase},
            "phase": phase,
            "crew_results_logged": crew_results is not None,
            "persistence_model": "mfo_controlled",
            "note": "State updates handled by Master Flow Orchestrator",
        }

    async def update_flow_state(
        self, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """
        DELTA TEAM FIX: Flow state updates coordinated through Master Flow Orchestrator.
        This method maintains compatibility but delegates to MFO for consistency.
        """
        try:
            # Determine current phase from state
            current_phase = getattr(state, "current_phase", "unknown")

            # DELTA TEAM FIX: Delegate to sync_state_update which now handles MFO coordination
            result = await self.sync_state_update(state, current_phase)

            logger.debug(
                f"🔄 Flow state update delegated for Flow ID: {state.flow_id}, phase: {current_phase}"
            )

            return result

        except Exception as e:
            logger.warning(f"⚠️ Flow state update delegation failed (non-critical): {e}")
            # Don't fail the flow - state coordination continues through MFO
            return {
                "status": "delegation_failed",
                "error": str(e),
                "impact": "State update delegated to Master Flow Orchestrator",
                "flow_continues": True,
            }

    async def recover_flow_state(
        self, flow_id: str
    ) -> Optional[UnifiedDiscoveryFlowState]:
        """
        Recover flow state from PostgreSQL when CrewAI persistence fails.
        Provides fallback recovery mechanism.
        """
        try:
            logger.info(f"🔄 Attempting flow state recovery for flow: {flow_id}")

            # Try to restore from PostgreSQL using postgres store
            async with AsyncSessionLocal() as db:
                # First check DiscoveryFlow table for current phase and progress
                from app.models.discovery_flow import DiscoveryFlow
                from sqlalchemy import select

                flow_result = await db.execute(
                    select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                )
                discovery_flow = flow_result.scalar_one_or_none()

                # Load state from extensions
                store = PostgresFlowStateStore(db, self.context)
                state_data = await store.load_state(flow_id)

                if state_data:
                    # If we have a discovery flow record, use its phase and progress
                    if discovery_flow:
                        state_data["current_phase"] = (
                            discovery_flow.current_phase
                            or state_data.get("current_phase", "initialized")
                        )
                        state_data["progress_percentage"] = (
                            discovery_flow.progress_percentage
                            or state_data.get("progress_percentage", 0.0)
                        )
                        state_data["status"] = discovery_flow.status or state_data.get(
                            "status", "initialized"
                        )

                        # Update phase completion based on discovery flow flags
                        phase_completion = state_data.get("phase_completion", {})
                        if discovery_flow.data_import_completed:
                            phase_completion["data_import"] = True
                        if discovery_flow.field_mapping_completed:
                            phase_completion["field_mapping"] = True
                        if discovery_flow.data_cleansing_completed:
                            phase_completion["data_cleansing"] = True
                        if discovery_flow.asset_inventory_completed:
                            phase_completion["asset_inventory"] = True
                        if discovery_flow.dependency_analysis_completed:
                            phase_completion["dependency_analysis"] = True
                        if discovery_flow.tech_debt_assessment_completed:
                            phase_completion["tech_debt_assessment"] = True
                        state_data["phase_completion"] = phase_completion

                        logger.info(
                            f"✅ Merged state from DiscoveryFlow table - phase: {discovery_flow.current_phase}, progress: {discovery_flow.progress_percentage}%"
                        )

                    # Reconstruct UnifiedDiscoveryFlowState from recovered data
                    restored_state = UnifiedDiscoveryFlowState(**state_data)
                    logger.info(f"✅ Flow state recovered from PostgreSQL: {flow_id}")
                    return restored_state
                else:
                    logger.warning(f"⚠️ No recoverable state found for flow: {flow_id}")
                    return None

        except Exception as e:
            logger.error(f"❌ Flow state recovery failed: {e}")
            return None

    async def validate_state_integrity(self, session_id: str) -> Dict[str, Any]:
        """
        Validate PostgreSQL flow state integrity.
        Comprehensive health check for state consistency.
        """
        try:
            # Validate PostgreSQL state integrity (single source of truth)
            pg_validation = await self.pg_persistence.validate_flow_integrity(
                session_id
            )

            overall_valid = pg_validation.get("valid", False)

            return {
                "status": "validated",
                "session_id": session_id,
                "overall_valid": overall_valid,
                "postgresql_validation": pg_validation,
                "persistence_model": "postgresql_only",
                "validation_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ PostgreSQL state integrity validation failed: {e}")
            return {
                "status": "validation_error",
                "session_id": session_id,
                "overall_valid": False,
                "error": str(e),
                "persistence_model": "postgresql_only",
            }

    async def cleanup_expired_states(
        self, expiration_hours: int = 72
    ) -> Dict[str, Any]:
        """
        Clean up expired flow states from PostgreSQL.
        Single source of truth cleanup.
        """
        try:
            cleanup_result = await self.pg_persistence.cleanup_expired_flows(
                expiration_hours
            )

            logger.info(
                f"✅ PostgreSQL cleanup completed: {cleanup_result.get('flows_cleaned', 0)} flows cleaned"
            )

            return {
                "status": "success",
                "postgresql_cleanup": cleanup_result,
                "persistence_model": "postgresql_only",
            }

        except Exception as e:
            logger.error(f"❌ PostgreSQL cleanup failed: {e}")
            return {
                "status": "cleanup_error",
                "error": str(e),
                "persistence_model": "postgresql_only",
            }

    def disable_sync(self, reason: str = "performance_optimization"):
        """
        Temporarily disable PostgreSQL state updates.
        Useful for performance optimization during intensive operations.
        """
        self._state_sync_enabled = False
        logger.info(f"🔄 PostgreSQL updates disabled: {reason}")

    def enable_sync(self):
        """Re-enable PostgreSQL state updates"""
        self._state_sync_enabled = True
        logger.info("🔄 PostgreSQL updates re-enabled")

    @asynccontextmanager
    async def sync_disabled(self, reason: str = "temporary_optimization"):
        """
        Context manager to temporarily disable sync during intensive operations.

        Usage:
            async with bridge.sync_disabled("bulk_processing"):
                # Intensive operations without state sync overhead
                pass
        """
        self.disable_sync(reason)
        try:
            yield
        finally:
            self.enable_sync()

    async def load_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Load flow state from PostgreSQL.

        Args:
            flow_id: The flow ID to load state for

        Returns:
            Dictionary containing the flow state or None if not found
        """
        try:
            logger.info(f"📥 Loading flow state for: {flow_id}")

            async with AsyncSessionLocal() as db:
                store = PostgresFlowStateStore(db, self.context)

                # Load the state by flow_id
                state_data = await store.load_state(flow_id)

                if state_data:
                    logger.info(f"✅ Loaded flow state for: {flow_id}")
                    return state_data
                else:
                    logger.warning(f"⚠️ No flow state found for: {flow_id}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error loading flow state for {flow_id}: {e}")
            raise

    async def save_state(self, flow_id: str, state_dict: Dict[str, Any]) -> bool:
        """
        Save flow state to PostgreSQL.

        Args:
            flow_id: The flow ID to save state for
            state_dict: Dictionary containing the flow state

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"💾 Saving flow state for: {flow_id}")

            async with AsyncSessionLocal() as db:
                store = PostgresFlowStateStore(db, self.context)

                # Ensure required fields are in state_dict
                state_dict["flow_id"] = flow_id
                state_dict["client_account_id"] = str(self.context.client_account_id)
                state_dict["engagement_id"] = str(self.context.engagement_id)
                state_dict["user_id"] = (
                    str(self.context.user_id) if self.context.user_id else None
                )
                state_dict["last_updated"] = datetime.utcnow().isoformat()

                # Save the state (determine current phase from state)
                current_phase = state_dict.get("current_phase", "unknown")
                await store.save_state(flow_id, state_dict, current_phase)

                logger.info(f"✅ Saved flow state for: {flow_id}")
                await db.commit()
                return True

        except Exception as e:
            logger.error(f"❌ Error saving flow state for {flow_id}: {e}")
            raise


# Factory function for creating flow state bridges
def create_flow_state_bridge(context: RequestContext) -> FlowStateBridge:
    """
    Factory function to create a flow state bridge with proper context.

    Args:
        context: RequestContext with tenant information

    Returns:
        FlowStateBridge instance configured for the tenant
    """
    return FlowStateBridge(context)


# Async context manager for automatic bridge lifecycle
@asynccontextmanager
async def managed_flow_bridge(context: RequestContext):
    """
    Async context manager for automatic bridge lifecycle management.

    Usage:
        async with managed_flow_bridge(context) as bridge:
            # Use bridge for flow operations
            await bridge.initialize_flow_state(state)
    """
    bridge = create_flow_state_bridge(context)
    try:
        yield bridge
    finally:
        # Cleanup if needed
        pass
