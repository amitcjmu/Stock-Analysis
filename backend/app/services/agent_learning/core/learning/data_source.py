"""
Data Source Learning Module - Handles data source pattern learning
"""

import logging

# from dataclasses import asdict  # Removed - using context.to_dict() instead
from datetime import datetime
from typing import Any, Dict, Optional

from app.services.agent_learning.models import LearningContext, LearningPattern

logger = logging.getLogger(__name__)


class DataSourceLearning:
    """Handles data source pattern learning."""

    async def learn_data_source_pattern(
        self, source_data: Dict[str, Any], context: Optional[LearningContext] = None
    ):
        """Learn data source patterns with context isolation."""
        if not context:
            context = LearningContext()

        memory = self._get_context_memory(context)

        pattern = LearningPattern(
            pattern_id=f"data_source_{datetime.utcnow().timestamp()}",
            pattern_type="data_source",
            context=context,
            pattern_data={
                "source_type": source_data.get("source_type"),
                "file_pattern": source_data.get("file_pattern"),
                "column_patterns": source_data.get("column_patterns", []),
                "quality_indicators": source_data.get("quality_indicators", {}),
                "processing_hints": source_data.get("processing_hints", {}),
            },
            confidence=source_data.get("confidence", 0.7),
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
                "pattern_type": "data_source",
                "source_type": source_data.get("source_type"),
                "confidence": pattern.confidence,
                "context": context.to_dict(),
            },
        )

        self.global_stats["data_source_patterns"] += 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()

        self._save_learning_patterns()

        logger.info(
            f"Learned data source pattern in context {context_key}: {source_data.get('source_type')}"
        )
