"""
Insight Handler for Agent-UI Communication
Manages agent insights and recommendations.
"""

import logging
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List

from ..models.agent_communication import AgentInsight, ConfidenceLevel

logger = logging.getLogger(__name__)


class InsightHandler:
    """Handles agent insights and recommendations."""

    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.agent_insights: Dict[str, AgentInsight] = {}

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
        """Add a new insight from an agent (with presentation review filtering)."""
        insight_id = str(uuid.uuid4())

        # Get client context if not provided
        if not client_account_id or not engagement_id:
            try:
                from app.core.context import get_current_context

                context = get_current_context()
                client_account_id = client_account_id or context.client_account_id
                engagement_id = engagement_id or context.engagement_id
                flow_id = flow_id or getattr(context, "flow_id", None)
                logger.info(
                    f"Captured client context for insight: client={client_account_id}, engagement={engagement_id}"
                )
            except Exception as e:
                logger.warning(f"Could not capture client context: {e}")

        # Create preliminary insight with client context
        insight = AgentInsight(
            id=insight_id,
            agent_id=agent_id,
            agent_name=agent_name,
            insight_type=insight_type,
            title=title,
            description=description,
            confidence=confidence,
            supporting_data=supporting_data,
            actionable=actionable,
            page=page,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            flow_id=flow_id,
        )

        # Check for duplicates before adding - simple duplicate detection
        existing_insights = [
            existing
            for existing in self.agent_insights.values()
            if existing.page == page
            and existing.title == title
            and existing.agent_id == agent_id
        ]

        if existing_insights:
            logger.info(
                f"Duplicate insight detected and filtered out: {title} from {agent_name}"
            )
            return existing_insights[0].id  # Return existing insight ID

        # Add to storage
        self.agent_insights[insight_id] = insight
        self.storage_manager.save_insights(self.agent_insights)

        logger.info(f"Agent {agent_name} added insight: {title} (page: {page})")
        return insight_id

    def get_insights_for_page(self, page: str) -> List[Dict[str, Any]]:
        """Get insights for a specific page."""
        page_insights = [
            asdict(insight)
            for insight in self.agent_insights.values()
            if insight.page == page
        ]

        # Sort by confidence and creation time
        confidence_order = {"high": 4, "medium": 3, "low": 2, "uncertain": 1}
        page_insights.sort(
            key=lambda x: (
                confidence_order.get(x["confidence"], 0),
                x["actionable"],
                x["created_at"],
            ),
            reverse=True,
        )

        return page_insights

    def get_actionable_insights(self, page: str = None) -> List[Dict[str, Any]]:
        """Get actionable insights."""
        insights = [
            asdict(insight)
            for insight in self.agent_insights.values()
            if insight.actionable and (not page or insight.page == page)
        ]

        # Sort by confidence
        confidence_order = {"high": 4, "medium": 3, "low": 2, "uncertain": 1}
        insights.sort(
            key=lambda x: confidence_order.get(x["confidence"], 0), reverse=True
        )

        return insights

    def update_insight_actionability(
        self, insight_id: str, actionable: bool, updated_by: str = "user"
    ) -> Dict[str, Any]:
        """Update whether an insight is actionable."""
        if insight_id not in self.agent_insights:
            return {"success": False, "error": "Insight not found"}

        old_actionable = self.agent_insights[insight_id].actionable
        self.agent_insights[insight_id].actionable = actionable

        # Log the update for learning
        learning_context = {
            "insight_id": insight_id,
            "agent_id": self.agent_insights[insight_id].agent_id,
            "insight_type": self.agent_insights[insight_id].insight_type,
            "old_actionable": old_actionable,
            "new_actionable": actionable,
            "updated_by": updated_by,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.storage_manager.store_learning_experience(learning_context)
        self.storage_manager.save_insights(self.agent_insights)

        logger.info(
            f"Updated actionability for insight {insight_id}: {old_actionable} -> {actionable}"
        )

        return {
            "success": True,
            "old_actionable": old_actionable,
            "new_actionable": actionable,
            "learning_stored": True,
        }

    def get_insight_statistics(self, page: str = None) -> Dict[str, Any]:
        """Get insight statistics."""
        insights = list(self.agent_insights.values())
        if page:
            insights = [insight for insight in insights if insight.page == page]

        total_insights = len(insights)
        if total_insights == 0:
            return {
                "total_insights": 0,
                "actionable_insights": 0,
                "by_confidence": {},
                "by_type": {},
                "by_agent": {},
                "actionability_rate": 0.0,
            }

        actionable_insights = sum(1 for insight in insights if insight.actionable)

        # Group by confidence
        by_confidence = {}
        for insight in insights:
            conf = insight.confidence.value
            by_confidence[conf] = by_confidence.get(conf, 0) + 1

        # Group by type
        by_type = {}
        for insight in insights:
            insight_type = insight.insight_type
            by_type[insight_type] = by_type.get(insight_type, 0) + 1

        # Group by agent
        by_agent = {}
        for insight in insights:
            agent = insight.agent_name
            by_agent[agent] = by_agent.get(agent, 0) + 1

        actionability_rate = (
            actionable_insights / total_insights if total_insights > 0 else 0.0
        )

        return {
            "total_insights": total_insights,
            "actionable_insights": actionable_insights,
            "by_confidence": by_confidence,
            "by_type": by_type,
            "by_agent": by_agent,
            "actionability_rate": actionability_rate,
        }

    def filter_insights(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter insights based on criteria."""
        insights = list(self.agent_insights.values())

        # Apply filters
        if filters.get("page"):
            insights = [i for i in insights if i.page == filters["page"]]

        if filters.get("agent_id"):
            insights = [i for i in insights if i.agent_id == filters["agent_id"]]

        if filters.get("insight_type"):
            insights = [
                i for i in insights if i.insight_type == filters["insight_type"]
            ]

        if filters.get("confidence"):
            insights = [
                i for i in insights if i.confidence.value == filters["confidence"]
            ]

        if filters.get("actionable") is not None:
            insights = [i for i in insights if i.actionable == filters["actionable"]]

        if filters.get("min_confidence"):
            confidence_order = {"uncertain": 1, "low": 2, "medium": 3, "high": 4}
            min_level = confidence_order.get(filters["min_confidence"], 0)
            insights = [
                i
                for i in insights
                if confidence_order.get(i.confidence.value, 0) >= min_level
            ]

        # Convert to dicts and sort
        result = [asdict(insight) for insight in insights]

        # Sort by confidence and actionability
        confidence_order = {"high": 4, "medium": 3, "low": 2, "uncertain": 1}
        result.sort(
            key=lambda x: (
                confidence_order.get(x["confidence"], 0),
                x["actionable"],
                x["created_at"],
            ),
            reverse=True,
        )

        return result

    def clear_insights(self, page: str = None) -> int:
        """Clear insights for a page or all pages."""
        initial_count = len(self.agent_insights)

        if page:
            self.agent_insights = {
                insight_id: insight
                for insight_id, insight in self.agent_insights.items()
                if insight.page != page
            }
        else:
            self.agent_insights.clear()

        cleared_count = initial_count - len(self.agent_insights)

        if cleared_count > 0:
            self.storage_manager.save_insights(self.agent_insights)
            logger.info(f"Cleared {cleared_count} agent insights")

        return cleared_count

    def load_insights(self, insights_data: Dict[str, Any]) -> None:
        """Load insights from storage."""
        self.agent_insights.clear()
        for insight_id, insight_data in insights_data.items():
            # Convert dict back to AgentInsight
            insight = AgentInsight(
                id=insight_data["id"],
                agent_id=insight_data["agent_id"],
                agent_name=insight_data["agent_name"],
                insight_type=insight_data["insight_type"],
                title=insight_data["title"],
                description=insight_data["description"],
                confidence=ConfidenceLevel(insight_data["confidence"]),
                supporting_data=insight_data["supporting_data"],
                actionable=insight_data.get("actionable", True),
                page=insight_data.get("page", "discovery"),
                created_at=datetime.fromisoformat(insight_data["created_at"]),
            )
            self.agent_insights[insight_id] = insight
