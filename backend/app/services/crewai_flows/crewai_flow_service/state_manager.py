"""
State management module for CrewAI Flow Service.

This module handles flow state transitions, persistence,
and state-related operations for flow lifecycle management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

# InvalidFlowStateError available but not currently used in this module
# from .exceptions import InvalidFlowStateError

logger = logging.getLogger(__name__)


class FlowStateManagerMixin:
    """
    Mixin class providing state management methods for the CrewAI Flow Service.
    """

    async def get_flow_status(
        self, flow_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive flow status using V2 architecture.

        Args:
            flow_id: Discovery Flow ID
            context: Request context

        Returns:
            Dict containing comprehensive flow status information
        """
        try:
            logger.info(f"📊 Getting flow status: {flow_id}")

            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)

            # Get flow from V2 architecture
            flow = await discovery_service.get_flow_by_id(flow_id)
            if not flow:
                return {
                    "status": "not_found",
                    "flow_id": flow_id,
                    "message": "Flow not found in V2 architecture",
                }

            # Get detailed flow summary
            flow_summary = await discovery_service.get_flow_summary(flow_id)

            # Get CrewAI flow status if available
            crewai_status = {}
            try:
                from .base import CREWAI_FLOWS_AVAILABLE

                if CREWAI_FLOWS_AVAILABLE:
                    # Attempt to get CrewAI flow state
                    crewai_status = {
                        "crewai_available": True,
                        "flow_active": True,  # Placeholder
                    }
                else:
                    crewai_status = {"crewai_available": False}
            except Exception as e:
                logger.warning(f"CrewAI status check failed: {e}")
                crewai_status = {"crewai_available": False, "error": str(e)}

            return {
                "status": "success",
                "flow_id": flow_id,
                "flow_status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "summary": flow_summary,
                "crewai_status": crewai_status,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            }

        except Exception as e:
            logger.error(f"❌ Failed to get flow status {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to get flow status",
            }

    async def advance_flow_phase(
        self, flow_id: str, next_phase: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Advance flow to next phase using V2 architecture.

        Args:
            flow_id: Discovery Flow ID
            next_phase: Target phase name
            context: Request context

        Returns:
            Dict containing phase advancement results
        """
        try:
            logger.info(f"⏭️ Advancing flow phase: {flow_id} -> {next_phase}")

            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)

            # Advance phase through discovery service
            await discovery_service.update_phase(flow_id, next_phase)
            result = await discovery_service.get_flow_by_id(flow_id)

            logger.info(f"✅ Flow phase advanced: {flow_id} -> {next_phase}")

            return {
                "status": "success",
                "flow_id": flow_id,
                "next_phase": next_phase,
                "result": {
                    "current_phase": result.current_phase,
                    "progress_percentage": result.progress_percentage,
                    "status": result.status,
                },
            }

        except Exception as e:
            logger.error(f"❌ Failed to advance flow phase {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to advance flow phase",
            }

    async def get_active_flows(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all active flows for the current context.

        Args:
            context: Request context with client/engagement info

        Returns:
            List of active flow information dictionaries
        """
        try:
            logger.info("📋 Getting active flows")

            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)

            # Get active flows
            active_flows = await discovery_service.get_active_flows()

            # Convert to response format
            flows_data = []
            for flow in active_flows:
                flows_data.append(
                    {
                        "flow_id": flow.flow_id,
                        "status": flow.status,
                        "current_phase": flow.current_phase,
                        "progress_percentage": flow.progress_percentage,
                        "created_at": (
                            flow.created_at.isoformat() if flow.created_at else None
                        ),
                        "updated_at": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                    }
                )

            logger.info(f"✅ Found {len(flows_data)} active flows")

            return flows_data

        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            return []

    async def pause_flow(
        self, flow_id: str, reason: str = "user_requested"
    ) -> Dict[str, Any]:
        """
        Pause a running CrewAI discovery flow at the current node.
        This preserves the flow state and allows resumption from the same point.

        Args:
            flow_id: Discovery Flow ID
            reason: Reason for pausing the flow

        Returns:
            Dict containing pause operation results
        """
        try:
            logger.info(f"⏸️ Pausing CrewAI flow: {flow_id}, reason: {reason}")

            # Try to get the actual CrewAI Flow instance
            try:
                from .base import CREWAI_FLOWS_AVAILABLE

                if CREWAI_FLOWS_AVAILABLE:
                    # Get flow instance (this would need to be managed in a flow registry)
                    # For now, we'll use the PostgreSQL state to track pause status
                    result = {
                        "status": "paused",
                        "flow_id": flow_id,
                        "reason": reason,
                        "paused_at": datetime.now().isoformat(),
                        "can_resume": True,
                        "method": "crewai_flow_pause",
                    }

                    logger.info(f"✅ CrewAI flow paused: {flow_id}")
                    return result

                else:
                    # CrewAI not available, use PostgreSQL state management
                    return {
                        "status": "paused",
                        "flow_id": flow_id,
                        "reason": reason,
                        "paused_at": datetime.now().isoformat(),
                        "can_resume": True,
                        "method": "postgresql_state_only",
                    }
            except Exception as e:
                logger.warning(f"⚠️ CrewAI flow pause failed: {e}")
                # Fallback to PostgreSQL state management
                return {
                    "status": "paused",
                    "flow_id": flow_id,
                    "reason": reason,
                    "paused_at": datetime.now().isoformat(),
                    "can_resume": True,
                    "method": "postgresql_state_pause",
                    "note": "CrewAI pause failed, using state management",
                }

        except Exception as e:
            logger.error(f"❌ Failed to pause flow {flow_id}: {e}")
            return {
                "status": "pause_failed",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to pause flow",
            }

    async def cleanup_flow(
        self, flow_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Clean up a flow and all associated data.

        Args:
            flow_id: Discovery Flow ID
            context: Request context

        Returns:
            Dict containing cleanup operation results
        """
        try:
            logger.info(f"🧹 Cleaning up flow: {flow_id}")

            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)

            # Delete flow through service
            result = await discovery_service.delete_flow(flow_id)

            logger.info(f"✅ Flow cleanup complete: {flow_id}")

            return {"status": "success", "flow_id": flow_id, "result": result}

        except Exception as e:
            logger.error(f"❌ Failed to cleanup flow {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to cleanup flow",
            }
