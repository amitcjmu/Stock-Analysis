"""
Quality Assessment Learning Module - Handles quality assessment pattern learning
"""

import logging

# from dataclasses import asdict  # Removed - using context.to_dict() instead
from datetime import datetime
from typing import Any, Dict, Optional

from app.services.agent_learning.models import LearningContext, LearningPattern

logger = logging.getLogger(__name__)


class QualityAssessmentLearning:
    """Handles quality assessment pattern learning."""

    async def learn_quality_assessment(
        self, quality_data: Dict[str, Any], context: Optional[LearningContext] = None
    ):
        """Learn quality assessment patterns with context isolation."""
        if not context:
            context = LearningContext()

        memory = self._get_context_memory(context)

        pattern = LearningPattern(
            pattern_id=f"quality_{datetime.utcnow().timestamp()}",
            pattern_type="quality_assessment",
            context=context,
            pattern_data={
                "quality_metrics": quality_data.get("quality_metrics", {}),
                "validation_rules": quality_data.get("validation_rules", []),
                "threshold_adjustments": quality_data.get("threshold_adjustments", {}),
                "user_corrections": quality_data.get("user_corrections", []),
            },
            confidence=quality_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )

        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []

        self.learning_patterns[context_key].append(pattern)

        memory.add_experience(
            "learned_patterns",
            {
                "pattern_type": "quality_assessment",
                "quality_metrics": quality_data.get("quality_metrics", {}),
                "confidence": pattern.confidence,
                "context": context.to_dict(),
            },
        )

        self.global_stats["quality_assessment_patterns"] += 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()

        self._save_learning_patterns()

        logger.info(f"Learned quality assessment pattern in context {context_key}")
