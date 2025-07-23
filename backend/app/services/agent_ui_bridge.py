"""
Agent-UI Communication Bridge
Enables agents to communicate with users through the UI for clarifications, feedback, and iterative learning.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_ui_bridge_handlers import (
    AnalysisHandler,
    ClassificationHandler,
    ContextHandler,
    InsightHandler,
    QuestionHandler,
    StorageManager,
)
from .models.agent_communication import (
    ConfidenceLevel,
    DataClassification,
    QuestionType,
)

logger = logging.getLogger(__name__)


class AgentUIBridge:
    """Manages communication between AI agents and the UI."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize storage manager
        self.storage_manager = StorageManager(str(self.data_dir))

        # Initialize handlers
        self.question_handler = QuestionHandler(self.storage_manager)
        self.classification_handler = ClassificationHandler(self.storage_manager)
        self.insight_handler = InsightHandler(self.storage_manager)
        self.context_handler = ContextHandler(self.storage_manager)
        self.analysis_handler = AnalysisHandler(self.storage_manager)

        # Real-time communication channels
        self._flow_decisions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._flow_messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._flow_subscriptions: Dict[str, Dict[str, Any]] = {}
        self._decision_listeners: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._message_version_counter: Dict[str, int] = defaultdict(int)

        # Load existing data
        self._load_persistent_data()

    # === AGENT QUESTION MANAGEMENT ===

    def add_agent_question(
        self,
        agent_id: str,
        agent_name: str,
        question_type: QuestionType,
        page: str,
        title: str,
        question: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None,
        confidence: Optional[ConfidenceLevel] = None,
        priority: str = "medium",
    ) -> str:
        """Add a new question from an agent."""
        return self.question_handler.add_agent_question(
            agent_id,
            agent_name,
            question_type,
            page,
            title,
            question,
            context,
            options,
            confidence,
            priority,
        )

    def answer_agent_question(self, question_id: str, response: Any) -> Dict[str, Any]:
        """Process user response to an agent question."""
        return self.question_handler.answer_agent_question(question_id, response)

    def get_questions_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all pending questions for a specific page."""
        return self.question_handler.get_questions_for_page(page)

    # === DATA CLASSIFICATION MANAGEMENT ===

    def classify_data_item(
        self,
        item_id: str,
        data_type: str,
        content: Dict[str, Any],
        classification: DataClassification,
        agent_analysis: Dict[str, Any],
        confidence: ConfidenceLevel,
        page: str = "discovery",
        issues: List[str] = None,
        recommendations: List[str] = None,
    ) -> None:
        """Classify a data item based on agent analysis."""
        self.classification_handler.classify_data_item(
            item_id,
            data_type,
            content,
            classification,
            agent_analysis,
            confidence,
            page,
            issues,
            recommendations,
        )

    def get_classified_data_for_page(
        self, page: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get data classifications organized by type for a specific page."""
        return self.classification_handler.get_classified_data_for_page(page)

    def update_data_classification(
        self,
        item_id: str,
        new_classification: DataClassification,
        updated_by: str = "user",
    ) -> Dict[str, Any]:
        """Update the classification of a data item."""
        return self.classification_handler.update_data_classification(
            item_id, new_classification, updated_by
        )

    # === AGENT INSIGHTS MANAGEMENT ===

    def add_agent_insight(
        self,
        agent_id: str,
        agent_name: str,
        insight_type: str,
        title: str,
        description: str,
        confidence: ConfidenceLevel,
        supporting_data: Dict[str, Any],
        page: str = "discovery",
        actionable: bool = True,
        client_account_id: str = None,
        engagement_id: str = None,
        flow_id: str = None,
    ) -> str:
        """Add a new insight from an agent (will be reviewed before presentation)."""
        return self.insight_handler.add_agent_insight(
            agent_id,
            agent_name,
            insight_type,
            title,
            description,
            confidence,
            supporting_data,
            page,
            actionable,
            client_account_id,
            engagement_id,
            flow_id,
        )

    def get_insights_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get all insights for a specific page (reviewed and validated)."""
        # Get insights from handler
        page_insights = self.insight_handler.get_insights_for_page(page)

        # Apply presentation review to filter and improve insights
        if page_insights:
            try:
                # Use simplified presentation review without individual agent
                # This can be enhanced with CrewAI crews in the future
                logger.info(
                    f"Applying simplified presentation review for {len(page_insights)} insights"
                )

                # Basic filtering - remove low confidence insights
                reviewed_insights = []
                for insight in page_insights:
                    confidence_value = insight.get("confidence", "medium")
                    if (
                        confidence_value in ["high", "very_high"]
                        or len(page_insights) <= 3
                    ):
                        reviewed_insights.append(insight)

                logger.info(
                    f"Presentation review: {len(reviewed_insights)}/{len(page_insights)} insights approved for {page}"
                )
                return reviewed_insights

            except Exception as e:
                logger.error(f"Error in presentation review: {e}")
                # Fall back to original insights if review fails
                pass

        return page_insights

    # === CROSS-PAGE CONTEXT MANAGEMENT ===

    def set_cross_page_context(self, key: str, value: Any, page_source: str) -> None:
        """Set context that should be preserved across pages."""
        self.context_handler.set_cross_page_context(key, value, page_source)

    def get_cross_page_context(self, key: str = None) -> Any:
        """Get cross-page context."""
        return self.context_handler.get_cross_page_context(key)

    def clear_cross_page_context(self, key: str = None) -> None:
        """Clear cross-page context."""
        self.context_handler.clear_cross_page_context(key)

    # === LEARNING AND FEEDBACK ===

    def _store_learning_experience(self, learning_context: Dict[str, Any]) -> None:
        """Store learning experience for agents."""
        self.context_handler.store_learning_experience(learning_context)

    def get_recent_learning_experiences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning experiences for agent improvement."""
        return self.context_handler.get_recent_learning_experiences(limit)

    # === AGENT PROCESSING METHODS ===

    async def analyze_with_agents(
        self, analysis_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data using available agents and return intelligent insights."""
        return await self.analysis_handler.analyze_with_agents(analysis_request)

    async def process_with_agents(
        self, processing_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process data using agent-driven operations."""
        return await self.analysis_handler.process_with_agents(processing_request)

    # === REAL-TIME AGENT DECISION BROADCASTING ===

    def broadcast_agent_decision(
        self,
        flow_id: str,
        agent_id: str,
        agent_name: str,
        decision_type: str,
        decision: str,
        reasoning: str,
        confidence: ConfidenceLevel,
        affected_items: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Broadcast an agent decision in real-time for SSE streaming.

        Args:
            flow_id: Flow identifier
            agent_id: ID of the agent making the decision
            agent_name: Name of the agent
            decision_type: Type of decision (e.g., 'field_mapping', 'data_quality', 'migration_strategy')
            decision: The actual decision made
            reasoning: Explanation of why the decision was made
            confidence: Confidence level of the decision
            affected_items: List of items affected by this decision
            metadata: Additional decision metadata

        Returns:
            Decision ID
        """
        decision_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Increment version counter for this flow
        self._message_version_counter[flow_id] += 1
        version = self._message_version_counter[flow_id]

        decision_data = {
            "id": decision_id,
            "version": version,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "decision_type": decision_type,
            "decision": decision,
            "reasoning": reasoning,
            "confidence": (
                confidence.value if hasattr(confidence, "value") else str(confidence)
            ),
            "affected_items": affected_items or [],
            "metadata": metadata or {},
            "timestamp": timestamp.isoformat(),
            "flow_id": flow_id,
        }

        # Store the decision
        self._flow_decisions[flow_id].append(decision_data)

        # Limit stored decisions per flow (keep last 100)
        if len(self._flow_decisions[flow_id]) > 100:
            self._flow_decisions[flow_id] = self._flow_decisions[flow_id][-100:]

        # Notify any listeners
        self._notify_decision_listeners(flow_id, decision_data)

        # Also store as an insight for persistence
        self.add_agent_insight(
            agent_id=agent_id,
            agent_name=agent_name,
            insight_type=f"decision_{decision_type}",
            title=f"Decision: {decision}",
            description=reasoning,
            confidence=confidence,
            supporting_data={
                "decision_id": decision_id,
                "decision_type": decision_type,
                "decision": decision,
                "affected_items": affected_items,
            },
            page="flow_decisions",
            actionable=True,
            flow_id=flow_id,
        )

        logger.info(f"Broadcast agent decision {decision_id} for flow {flow_id}")
        return decision_id

    def get_flow_insights(self, flow_id: str) -> List[Dict[str, Any]]:
        """
        Get all insights for a specific flow, including agent decisions.
        Used by SSE endpoint for real-time updates.

        Args:
            flow_id: Flow identifier

        Returns:
            List of insights and decisions for the flow
        """
        insights = []

        # Get regular insights from handler
        all_insights = self.insight_handler.insights
        flow_insights = [
            insight for insight in all_insights.values() if insight.flow_id == flow_id
        ]

        # Convert to dict format
        for insight in flow_insights:
            insights.append(
                {
                    "id": insight.id,
                    "type": "insight",
                    "agent_id": insight.agent_id,
                    "agent_name": insight.agent_name,
                    "insight_type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "confidence": (
                        insight.confidence.value
                        if hasattr(insight.confidence, "value")
                        else str(insight.confidence)
                    ),
                    "supporting_data": insight.supporting_data,
                    "created_at": insight.created_at.isoformat(),
                    "is_validated": insight.is_validated,
                }
            )

        # Add recent decisions as insights
        if flow_id in self._flow_decisions:
            for decision in self._flow_decisions[flow_id][-10:]:  # Last 10 decisions
                insights.append(
                    {
                        "id": decision["id"],
                        "type": "decision",
                        "agent_id": decision["agent_id"],
                        "agent_name": decision["agent_name"],
                        "decision_type": decision["decision_type"],
                        "title": f"Decision: {decision['decision']}",
                        "description": decision["reasoning"],
                        "confidence": decision["confidence"],
                        "supporting_data": {
                            "affected_items": decision["affected_items"],
                            "metadata": decision["metadata"],
                        },
                        "created_at": decision["timestamp"],
                        "is_validated": True,  # Decisions are pre-validated
                    }
                )

        # Sort by creation time (most recent first)
        insights.sort(key=lambda x: x["created_at"], reverse=True)

        return insights

    def get_pending_messages(
        self, flow_id: str, since_version: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages for a flow since a specific version.
        Used by SSE endpoint for streaming updates.

        Args:
            flow_id: Flow identifier
            since_version: Get messages with version > since_version

        Returns:
            List of pending messages
        """
        messages = []

        # Get messages for this flow
        if flow_id in self._flow_messages:
            for message in self._flow_messages[flow_id]:
                if message.get("version", 0) > since_version:
                    messages.append(message)

        # Get unanswered questions as messages
        questions = self.get_questions_for_page(f"flow_{flow_id}")
        for question in questions:
            if not question.get("is_resolved", False):
                # Convert question to message format
                message_version = self._message_version_counter[flow_id] + 1
                self._message_version_counter[flow_id] = message_version

                messages.append(
                    {
                        "id": question["id"],
                        "version": message_version,
                        "type": "agent_question",
                        "agent_id": question.get("agent_id"),
                        "agent_name": question.get("agent_name"),
                        "title": question.get("title"),
                        "content": question.get("question"),
                        "context": question.get("context"),
                        "options": question.get("options"),
                        "priority": question.get("priority", "medium"),
                        "timestamp": question.get(
                            "created_at", datetime.utcnow().isoformat()
                        ),
                    }
                )

        return messages

    def create_subscription(
        self, flow_id: str, client_id: str, client_account_id: str
    ) -> str:
        """
        Create a subscription for flow events.

        Args:
            flow_id: Flow identifier
            client_id: Client/user ID
            client_account_id: Client account ID

        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())

        self._flow_subscriptions[subscription_id] = {
            "id": subscription_id,
            "flow_id": flow_id,
            "client_id": client_id,
            "client_account_id": client_account_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }

        logger.info(f"Created subscription {subscription_id} for flow {flow_id}")
        return subscription_id

    def remove_subscription(self, subscription_id: str) -> bool:
        """
        Remove a subscription.

        Args:
            subscription_id: Subscription identifier

        Returns:
            True if removed, False if not found
        """
        if subscription_id in self._flow_subscriptions:
            del self._flow_subscriptions[subscription_id]
            logger.info(f"Removed subscription {subscription_id}")
            return True
        return False

    def _notify_decision_listeners(self, flow_id: str, decision_data: Dict[str, Any]):
        """
        Notify any async listeners about a new decision.

        Args:
            flow_id: Flow identifier
            decision_data: Decision data to broadcast
        """
        if flow_id in self._decision_listeners:
            for queue in self._decision_listeners[flow_id]:
                try:
                    queue.put_nowait(decision_data)
                except asyncio.QueueFull:
                    logger.warning(f"Decision queue full for flow {flow_id}")

    def register_decision_listener(self, flow_id: str, queue: asyncio.Queue):
        """
        Register an async queue to receive decision updates.

        Args:
            flow_id: Flow identifier
            queue: Async queue to receive updates
        """
        self._decision_listeners[flow_id].append(queue)

    def unregister_decision_listener(self, flow_id: str, queue: asyncio.Queue):
        """
        Unregister a decision listener.

        Args:
            flow_id: Flow identifier
            queue: Queue to remove
        """
        if flow_id in self._decision_listeners:
            if queue in self._decision_listeners[flow_id]:
                self._decision_listeners[flow_id].remove(queue)

    # === UTILITY METHODS ===

    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current agent-UI interaction status."""
        question_stats = self.question_handler.get_question_statistics()
        classification_stats = (
            self.classification_handler.get_classification_statistics()
        )
        insight_stats = self.insight_handler.get_insight_statistics()
        coordination_stats = self.context_handler.get_agent_coordination_summary()

        # Add real-time stats
        realtime_stats = {
            "active_subscriptions": len(self._flow_subscriptions),
            "flows_with_decisions": len(self._flow_decisions),
            "total_decisions": sum(
                len(decisions) for decisions in self._flow_decisions.values()
            ),
            "flows_with_messages": len(self._flow_messages),
        }

        return {
            "questions": question_stats,
            "classifications": classification_stats,
            "insights": insight_stats,
            "coordination": coordination_stats,
            "realtime": realtime_stats,
            "storage": self.storage_manager.get_storage_statistics(),
        }

    # === PERSISTENCE METHODS ===

    def _load_persistent_data(self) -> None:
        """Load persistent data from storage using handlers."""
        try:
            # Load data into handlers
            questions_data = self.storage_manager.load_questions()
            self.question_handler.load_questions(questions_data)

            classifications_data = self.storage_manager.load_classifications()
            self.classification_handler.load_classifications(classifications_data)

            insights_data = self.storage_manager.load_insights()
            self.insight_handler.load_insights(insights_data)

            context_data = self.storage_manager.load_context()
            self.context_handler.load_context_data(context_data)

            self.storage_manager.load_learning_experiences()
            # Learning experiences are loaded into context handler

        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")


# Global instance for the application
agent_ui_bridge = AgentUIBridge()
