"""
Questionnaire Caching Module
Handles caching of questionnaire templates for performance optimization.
"""

import logging

logger = logging.getLogger(__name__)


class QuestionnaireCaching:
    """Handles caching logic for questionnaire templates."""

    def __init__(self):
        """Initialize caching system."""
        self._memory_manager = None

    def get_memory_manager(self, db_session, crewai_service=None):
        """
        Initialize memory manager if not already set.

        Args:
            db_session: Database session for TenantMemoryManager
            crewai_service: Optional CrewAI service instance

        Returns:
            TenantMemoryManager instance
        """
        if self._memory_manager is None:
            from app.services.crewai_flows.memory.tenant_memory_manager import (
                TenantMemoryManager,
            )

            # If crewai_service not provided, create minimal one
            if crewai_service is None:
                # Use a placeholder - memory manager doesn't actually use it for storage
                crewai_service = type("CrewAIService", (), {})()

            self._memory_manager = TenantMemoryManager(crewai_service, db_session)

        return self._memory_manager

    def create_gap_pattern(self, gaps: list) -> str:
        """
        Create deterministic gap pattern signature from list of gap field names.

        Args:
            gaps: List of field names that are missing

        Returns:
            Sorted underscore-joined string (e.g., "backup_strategy_replication_config")
        """
        # Sort to ensure consistent ordering
        sorted_gaps = sorted(gaps) if gaps else []
        return "_".join(sorted_gaps)

    def customize_questions(
        self, cached_questions: list, asset_id: str, asset_name: str = None
    ) -> list:
        """
        Customize cached questions for specific asset.

        Only changes asset-specific references (name, ID).
        Question text, validation rules, etc. remain unchanged.

        Args:
            cached_questions: List of question dicts from cache
            asset_id: Asset UUID to customize for
            asset_name: Optional asset name (will lookup if not provided)

        Returns:
            Customized question list
        """
        if not cached_questions:
            return []

        # Get asset name if not provided
        if not asset_name:
            asset_name = asset_id[:8]  # Fallback to UUID prefix

        customized = []
        for question in cached_questions:
            customized_q = question.copy()

            # Replace asset references in question text
            if "question_text" in customized_q:
                customized_q["question_text"] = (
                    customized_q["question_text"]
                    .replace("{asset_name}", asset_name)
                    .replace("{asset_id}", asset_id)
                )

            # Update asset_id in metadata
            if "metadata" in customized_q:
                customized_q["metadata"]["asset_id"] = asset_id
                customized_q["metadata"]["asset_name"] = asset_name

            customized.append(customized_q)

        return customized
