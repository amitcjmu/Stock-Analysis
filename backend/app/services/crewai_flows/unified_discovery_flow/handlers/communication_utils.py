"""
Communication utilities for phase handlers.
Provides agent insight and error reporting functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CommunicationUtils:
    """Utilities for agent communication and insight reporting."""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance."""
        self.flow = flow_instance
        self.logger = logger

    async def send_phase_insight(
        self,
        phase: str,
        title: str,
        description: str,
        progress: int,
        data: Dict[str, Any],
    ):
        """Send phase insight via agent-ui-bridge"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": f"unified_discovery_{phase}",
                "agent_name": f"Discovery {phase.replace('_', ' ').title()} Agent",
                "insight_type": "phase_completion",
                "title": title,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": phase,
                    "progress": progress,
                    "flow_id": self.flow._flow_id,
                    **data,
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
                f"📡 [ECHO] Sent {phase} phase insight via agent-ui-bridge"
            )

        except Exception as e:
            self.logger.warning(f"⚠️ [ECHO] Failed to send {phase} phase insight: {e}")

    async def send_phase_error(self, phase: str, error_message: str):
        """Send phase error insight via agent-ui-bridge"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel

            insight = {
                "agent_id": f"unified_discovery_{phase}",
                "agent_name": f"Discovery {phase.replace('_', ' ').title()} Agent",
                "insight_type": "error",
                "title": f"{phase.replace('_', ' ').title()} Phase Failed",
                "description": f"Error in {phase} phase: {error_message}",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": phase,
                    "error": error_message,
                    "flow_id": self.flow._flow_id,
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

            self.logger.info(f"📡 [ECHO] Sent {phase} phase error via agent-ui-bridge")

        except Exception as e:
            self.logger.warning(f"⚠️ [ECHO] Failed to send {phase} phase error: {e}")
