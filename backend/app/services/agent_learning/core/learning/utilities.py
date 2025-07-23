"""
Utilities Module - Shared utilities for the learning system
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LearningUtilities:
    """Shared utility functions for the learning system."""

    async def cleanup_old_patterns(self, days_to_keep: int = 90):
        """Clean up old patterns to prevent unbounded growth."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        for context_key in list(self.learning_patterns.keys()):
            patterns = self.learning_patterns[context_key]
            active_patterns = [p for p in patterns if p.last_used > cutoff_date]

            if len(active_patterns) != len(patterns):
                self.learning_patterns[context_key] = active_patterns
                logger.info(
                    f"Cleaned up {len(patterns) - len(active_patterns)} old patterns in context {context_key}"
                )

        self._save_learning_patterns()
