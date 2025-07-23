"""
Base Learning Module - Core functionality and utilities for the learning system
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.agent_learning.models import (LearningContext,
                                                LearningPattern,
                                                PerformanceLearningPattern)
from app.services.embedding_service import EmbeddingService
from app.services.memory import AgentMemory
from app.utils.vector_utils import VectorUtils

logger = logging.getLogger(__name__)


class BaseLearningMixin:
    """Base mixin class providing core learning functionality."""

    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Context-scoped memory storage
        self.context_memories: Dict[str, AgentMemory] = {}

        # Learning patterns by context
        self.learning_patterns: Dict[str, List[LearningPattern]] = {}

        # Performance-based learning patterns
        self.performance_patterns: Dict[str, List[PerformanceLearningPattern]] = {}

        self.embedding_service = EmbeddingService()
        self.vector_utils = VectorUtils()

        # Global learning statistics
        self.global_stats = {
            "total_contexts": 0,
            "total_patterns": 0,
            "total_learning_events": 0,
            "field_mapping_patterns": 0,
            "data_source_patterns": 0,
            "quality_assessment_patterns": 0,
            "agents_tracked": set(),
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Load existing patterns
        self._load_learning_patterns()

    def _get_context_memory(self, context: LearningContext) -> AgentMemory:
        """Get or create context-scoped memory."""
        context_key = context.context_hash

        if context_key not in self.context_memories:
            # Create context-specific memory directory
            context_dir = self.data_dir / f"context_{context_key}"
            context_dir.mkdir(exist_ok=True)

            self.context_memories[context_key] = AgentMemory(str(context_dir))
            logger.info(f"Created context-scoped memory for {context_key}")

        return self.context_memories[context_key]

    def _get_context_from_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> LearningContext:
        """Extract context from request headers."""
        if not headers:
            return LearningContext()

        return LearningContext(
            client_account_id=headers.get("X-Client-ID"),
            engagement_id=headers.get("X-Engagement-ID"),
            flow_id=headers.get("X-Flow-ID"),
        )

    def _save_learning_patterns(self):
        """Save learning patterns to disk."""
        # This method is now obsolete as we are using the database.
        pass

    def _load_learning_patterns(self):
        """Load learning patterns from disk."""
        # This method is now obsolete as we are using the database.
        pass

    async def get_context_patterns(
        self, context: LearningContext
    ) -> List[LearningPattern]:
        """Get all patterns for a specific context."""
        context_key = context.context_hash
        return self.learning_patterns.get(context_key, [])

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        # Convert set to count for JSON serialization
        stats = self.global_stats.copy()
        stats["agents_tracked"] = len(stats["agents_tracked"])
        stats["total_contexts"] = len(self.context_memories)

        return stats

    def get_context_isolation_statistics(self) -> Dict[str, Any]:
        """Get statistics about context isolation and client separation."""
        client_contexts = set()
        engagement_contexts = set()

        for ctx_key, memory in self.context_memories.items():
            client_experiences = memory.experiences.get("client_context", [])
            engagement_experiences = memory.experiences.get("engagement_context", [])

            for exp in client_experiences:
                client_contexts.add(exp.get("client_account_id"))

            for exp in engagement_experiences:
                engagement_contexts.add(exp.get("engagement_id"))

        return {
            "total_client_contexts": len(client_contexts),
            "total_engagement_contexts": len(engagement_contexts),
            "total_isolated_contexts": len(self.context_memories),
            "context_isolation_enabled": True,
            "learning_patterns_by_context": {
                ctx_key: len(patterns)
                for ctx_key, patterns in self.learning_patterns.items()
            },
        }
