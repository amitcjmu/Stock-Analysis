"""
Notification Utilities Module

This module contains notification and communication utilities extracted from the base_flow.py
to improve maintainability and code organization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class NotificationUtilities:
    """
    Handles notification and communication operations for the UnifiedDiscoveryFlow
    """

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

    async def send_flow_start_notification(self):
        """Send flow start notification via agent-ui-bridge"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": "unified_discovery_flow",
                "agent_name": "Discovery Flow Orchestrator",
                "insight_type": "flow_start",
                "title": "Discovery Flow Started",
                "description": f"Initializing discovery flow with ID {self.flow._flow_id}",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": "initialization",
                    "progress": 0,
                    "status": "processing",
                    "flow_id": self.flow._flow_id,
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.HIGH,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info("📡 Sent flow start notification via agent-ui-bridge")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send flow start notification: {e}")
            return False

    async def send_flow_completion_notification(self, final_result: Dict[str, Any]):
        """Send flow completion notification"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": "unified_discovery_flow",
                "agent_name": "Discovery Flow Orchestrator",
                "insight_type": "flow_completion",
                "title": "Discovery Flow Completed",
                "description": f"Discovery flow {self.flow._flow_id} has completed successfully",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": "completion",
                    "progress": 100,
                    "status": "completed",
                    "flow_id": self.flow._flow_id,
                    "final_result": final_result,
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.HIGH,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info("📡 Sent flow completion notification via agent-ui-bridge")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send flow completion notification: {e}")
            return False

    async def send_error_notification(
        self, error_message: str, phase: Optional[str] = None
    ):
        """Send error notification"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": "unified_discovery_flow",
                "agent_name": "Discovery Flow Orchestrator",
                "insight_type": "error",
                "title": "Discovery Flow Error",
                "description": f"Error in discovery flow {self.flow._flow_id}: {error_message}",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": phase or "unknown",
                    "status": "error",
                    "flow_id": self.flow._flow_id,
                    "error_message": error_message,
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.LOW,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info("📡 Sent error notification via agent-ui-bridge")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send error notification: {e}")
            return False

    async def send_approval_request_notification(self, approval_data: Dict[str, Any]):
        """Send approval request notification"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": "unified_discovery_flow",
                "agent_name": "Discovery Flow Orchestrator",
                "insight_type": "approval_required",
                "title": "Field Mapping Approval Required",
                "description": f"Field mapping suggestions are ready for review in flow {self.flow._flow_id}",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": "field_mapping_approval",
                    "status": "awaiting_approval",
                    "flow_id": self.flow._flow_id,
                    "approval_data": approval_data,
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.MEDIUM,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info(
                "📡 Sent approval request notification via agent-ui-bridge"
            )
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send approval request notification: {e}")
            return False

    async def send_progress_update(self, progress: int, phase: str, message: str):
        """Send progress update notification"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": "unified_discovery_flow",
                "agent_name": "Discovery Flow Orchestrator",
                "insight_type": "progress_update",
                "title": f"Flow Progress: {progress}%",
                "description": message,
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": phase,
                    "progress": progress,
                    "status": "processing",
                    "flow_id": self.flow._flow_id,
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.HIGH,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info(
                f"📡 Sent progress update ({progress}%) via agent-ui-bridge"
            )
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send progress update: {e}")
            return False

    async def update_flow_status(self, status: str):
        """Update flow status in database"""
        try:
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import (
                    PostgresFlowStateStore,
                )

                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, status)
                    self.logger.info(f"✅ Updated flow status to '{status}'")
                    return True
            else:
                self.logger.warning("⚠️ Flow bridge not available for status update")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to update flow status: {e}")
            return False

    async def send_agent_communication(
        self, agent_id: str, message: str, data: Optional[Dict[str, Any]] = None
    ):
        """Send communication to a specific agent"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": agent_id,
                "agent_name": f"Agent {agent_id}",
                "insight_type": "agent_communication",
                "title": "Agent Communication",
                "description": message,
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "flow_id": self.flow._flow_id,
                    "source_agent": "unified_discovery_flow",
                    "target_agent": agent_id,
                    "communication_data": data or {},
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.MEDIUM,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info(f"📡 Sent communication to agent {agent_id}")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to send agent communication: {e}")
            return False

    async def broadcast_flow_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast flow event to all interested parties"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": "unified_discovery_flow",
                "agent_name": "Discovery Flow Orchestrator",
                "insight_type": "flow_event",
                "title": f"Flow Event: {event_type}",
                "description": f"Flow event '{event_type}' occurred in flow {self.flow._flow_id}",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "event_type": event_type,
                    "flow_id": self.flow._flow_id,
                    "event_data": event_data,
                },
            }

            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.HIGH,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id,
            )

            self.logger.info(f"📡 Broadcasted flow event '{event_type}'")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to broadcast flow event: {e}")
            return False
