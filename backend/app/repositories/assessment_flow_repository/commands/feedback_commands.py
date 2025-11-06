"""
Feedback Commands - Learning feedback management
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentLearningFeedback
from app.models.assessment_flow_state import (
    AssessmentLearningFeedback as AssessmentLearningFeedbackState,
)

logger = logging.getLogger(__name__)


class FeedbackCommands:
    """Commands for learning feedback management"""

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    async def save_learning_feedback(
        self, flow_id: str, decision_id: str, feedback: AssessmentLearningFeedbackState
    ):
        """Save learning feedback for agent improvement"""

        feedback_record = AssessmentLearningFeedback(
            assessment_flow_id=flow_id,
            decision_id=decision_id,
            original_strategy=feedback.original_strategy.value,
            override_strategy=feedback.override_strategy.value,
            feedback_reason=feedback.feedback_reason,
            agent_id=feedback.agent_id,
            learned_pattern=feedback.learned_pattern,
        )

        self.db.add(feedback_record)
        await self.db.commit()
