"""
Agent Communication Protocol
Provides standardized communication between agents and the UI layer.
Implements Phase 2 of the Discovery Flow redesign.
"""

import logging
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AgentCommunicationProtocol:
    """
    Manages communication between individual agents and the UI layer.
    Provides message queuing, status tracking, and real-time updates.
    """

    def __init__(self):
        self.protocol_id = str(uuid.uuid4())
        self.active = True
        self.registered_agents: Set[str] = set()
        self.ui_subscribers: Set[str] = set()

        # Message queues
        self.ui_messages: deque = deque(maxlen=1000)  # Last 1000 messages
        self.agent_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Status tracking
        self.agent_statuses: Dict[str, Dict[str, Any]] = {}
        self.ui_interactions: List[Dict[str, Any]] = []

        # Metrics
        self.metrics = {
            "total_messages": 0,
            "ui_messages": 0,
            "agent_messages": 0,
            "interactions": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        logger.info(f"🔗 Agent Communication Protocol initialized: {self.protocol_id}")

    def register_agent(self, agent_id: str, agent_name: str = None) -> bool:
        """Register an agent with the communication protocol"""
        try:
            self.registered_agents.add(agent_id)
            self.agent_statuses[agent_id] = {
                "agent_id": agent_id,
                "agent_name": agent_name or agent_id,
                "status": "registered",
                "last_activity": datetime.now().isoformat(),
                "message_count": 0,
                "registered_at": datetime.now().isoformat(),
            }

            logger.info(f"🤖 Agent registered: {agent_id} ({agent_name})")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            self.metrics["errors"] += 1
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the communication protocol"""
        try:
            if agent_id in self.registered_agents:
                self.registered_agents.remove(agent_id)

                # Update status to unregistered
                if agent_id in self.agent_statuses:
                    self.agent_statuses[agent_id]["status"] = "unregistered"
                    self.agent_statuses[agent_id][
                        "unregistered_at"
                    ] = datetime.now().isoformat()

                logger.info(f"🤖 Agent unregistered: {agent_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            self.metrics["errors"] += 1
            return False

    def subscribe_ui(self, ui_session_id: str) -> bool:
        """Subscribe a UI session to receive agent communications"""
        try:
            self.ui_subscribers.add(ui_session_id)
            logger.info(f"🖥️ UI session subscribed: {ui_session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe UI session {ui_session_id}: {e}")
            self.metrics["errors"] += 1
            return False

    def unsubscribe_ui(self, ui_session_id: str) -> bool:
        """Unsubscribe a UI session from agent communications"""
        try:
            if ui_session_id in self.ui_subscribers:
                self.ui_subscribers.remove(ui_session_id)
                logger.info(f"🖥️ UI session unsubscribed: {ui_session_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unsubscribe UI session {ui_session_id}: {e}")
            self.metrics["errors"] += 1
            return False

    async def send_agent_message(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """Send a message from an agent to the UI layer"""
        try:
            # Validate agent is registered
            if agent_id not in self.registered_agents:
                logger.warning(
                    f"Unregistered agent attempted to send message: {agent_id}"
                )
                return False

            # Prepare message
            formatted_message = {
                "message_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "message_type": message.get("type", "general"),
                "content": message,
                "protocol_id": self.protocol_id,
            }

            # Add to queues
            self.ui_messages.append(formatted_message)
            self.agent_messages[agent_id].append(formatted_message)

            # Update metrics and status
            self.metrics["total_messages"] += 1
            self.metrics["agent_messages"] += 1

            if agent_id in self.agent_statuses:
                self.agent_statuses[agent_id][
                    "last_activity"
                ] = datetime.now().isoformat()
                self.agent_statuses[agent_id]["message_count"] += 1
                self.agent_statuses[agent_id]["status"] = "active"

            logger.debug(f"📤 Agent message sent: {agent_id} -> UI")
            return True

        except Exception as e:
            logger.error(f"Failed to send agent message from {agent_id}: {e}")
            self.metrics["errors"] += 1
            return False

    async def send_ui_interaction(self, interaction: Dict[str, Any]) -> bool:
        """Send a UI interaction to the agent layer"""
        try:
            # Prepare interaction
            formatted_interaction = {
                "interaction_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "interaction_type": interaction.get("type", "general"),
                "content": interaction,
                "protocol_id": self.protocol_id,
            }

            # Store interaction
            self.ui_interactions.append(formatted_interaction)

            # Update metrics
            self.metrics["total_messages"] += 1
            self.metrics["ui_messages"] += 1
            self.metrics["interactions"] += 1

            logger.debug(
                f"📥 UI interaction received: {interaction.get('type', 'unknown')}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to process UI interaction: {e}")
            self.metrics["errors"] += 1
            return False

    async def get_ui_messages(
        self, since: Optional[datetime] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for the UI layer"""
        try:
            messages = list(self.ui_messages)

            # Filter by timestamp if provided
            if since:
                messages = [
                    msg
                    for msg in messages
                    if datetime.fromisoformat(msg["timestamp"]) > since
                ]

            # Apply limit
            messages = messages[-limit:] if limit else messages

            return messages

        except Exception as e:
            logger.error(f"Failed to get UI messages: {e}")
            return []

    async def get_agent_messages(
        self, agent_id: str, since: Optional[datetime] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific agent"""
        try:
            messages = list(self.agent_messages.get(agent_id, []))

            # Filter by timestamp if provided
            if since:
                messages = [
                    msg
                    for msg in messages
                    if datetime.fromisoformat(msg["timestamp"]) > since
                ]

            # Apply limit
            messages = messages[-limit:] if limit else messages

            return messages

        except Exception as e:
            logger.error(f"Failed to get agent messages for {agent_id}: {e}")
            return []

    def get_protocol_status(self) -> Dict[str, Any]:
        """Get current protocol status"""
        uptime = datetime.now() - self.metrics["start_time"]

        return {
            "protocol_id": self.protocol_id,
            "active": self.active,
            "uptime_seconds": uptime.total_seconds(),
            "registered_agents": len(self.registered_agents),
            "ui_subscribers": len(self.ui_subscribers),
            "agent_list": list(self.registered_agents),
            "metrics": self.metrics.copy(),
            "message_queue_sizes": {
                "ui_messages": len(self.ui_messages),
                "agent_messages": {
                    agent_id: len(queue)
                    for agent_id, queue in self.agent_messages.items()
                },
            },
        }

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific agent"""
        return self.agent_statuses.get(agent_id)

    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get statuses for all registered agents"""
        return self.agent_statuses.copy()

    async def test_communication(self) -> Dict[str, Any]:
        """Test the communication protocol"""
        test_results = {
            "protocol_active": self.active,
            "test_timestamp": datetime.now().isoformat(),
            "tests": {},
        }

        try:
            # Test agent registration
            test_agent_id = f"test_agent_{uuid.uuid4().hex[:8]}"
            registration_success = self.register_agent(test_agent_id, "Test Agent")
            test_results["tests"]["agent_registration"] = registration_success

            # Test message sending
            if registration_success:
                test_message = {
                    "type": "test",
                    "content": "Communication test message",
                    "test_id": str(uuid.uuid4()),
                }

                message_success = await self.send_agent_message(
                    test_agent_id, test_message
                )
                test_results["tests"]["message_sending"] = message_success

                # Test message retrieval
                messages = await self.get_ui_messages(limit=1)
                retrieval_success = (
                    len(messages) > 0 and messages[-1]["agent_id"] == test_agent_id
                )
                test_results["tests"]["message_retrieval"] = retrieval_success

                # Cleanup test agent
                self.unregister_agent(test_agent_id)

            # Test UI interaction
            test_interaction = {
                "type": "test_interaction",
                "content": "Test UI interaction",
                "test_id": str(uuid.uuid4()),
            }

            interaction_success = await self.send_ui_interaction(test_interaction)
            test_results["tests"]["ui_interaction"] = interaction_success

            # Overall test result
            all_tests_passed = all(test_results["tests"].values())
            test_results["overall_success"] = all_tests_passed
            test_results["message"] = (
                "All tests passed" if all_tests_passed else "Some tests failed"
            )

            logger.info(
                f"🧪 Communication test completed: {'✅ PASSED' if all_tests_passed else '❌ FAILED'}"
            )

        except Exception as e:
            logger.error(f"Communication test failed: {e}")
            test_results["overall_success"] = False
            test_results["error"] = str(e)
            test_results["message"] = f"Test failed with error: {str(e)}"

        return test_results

    def cleanup_old_messages(self, older_than_hours: int = 24) -> int:
        """Clean up old messages to prevent memory buildup"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            cleaned_count = 0

            # Clean UI messages
            original_ui_count = len(self.ui_messages)
            self.ui_messages = deque(
                [
                    msg
                    for msg in self.ui_messages
                    if datetime.fromisoformat(msg["timestamp"]) > cutoff_time
                ],
                maxlen=1000,
            )
            cleaned_count += original_ui_count - len(self.ui_messages)

            # Clean agent messages
            for agent_id in list(self.agent_messages.keys()):
                original_count = len(self.agent_messages[agent_id])
                self.agent_messages[agent_id] = deque(
                    [
                        msg
                        for msg in self.agent_messages[agent_id]
                        if datetime.fromisoformat(msg["timestamp"]) > cutoff_time
                    ],
                    maxlen=100,
                )
                cleaned_count += original_count - len(self.agent_messages[agent_id])

            # Clean old UI interactions
            original_interactions = len(self.ui_interactions)
            self.ui_interactions = [
                interaction
                for interaction in self.ui_interactions
                if datetime.fromisoformat(interaction["timestamp"]) > cutoff_time
            ]
            cleaned_count += original_interactions - len(self.ui_interactions)

            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} old messages")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
            return 0


# Global protocol instance
_protocol_instance: Optional[AgentCommunicationProtocol] = None


def get_communication_protocol() -> AgentCommunicationProtocol:
    """Get or create the global communication protocol instance"""
    global _protocol_instance

    if _protocol_instance is None:
        _protocol_instance = AgentCommunicationProtocol()
        logger.info("🔗 Global Agent Communication Protocol created")

    return _protocol_instance


def reset_communication_protocol() -> AgentCommunicationProtocol:
    """Reset the global communication protocol (for testing)"""
    global _protocol_instance
    _protocol_instance = AgentCommunicationProtocol()
    logger.info("🔄 Global Agent Communication Protocol reset")
    return _protocol_instance
