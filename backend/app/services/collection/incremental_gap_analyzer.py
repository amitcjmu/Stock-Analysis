"""
Incremental Gap Analyzer

Efficiently recalculates gaps after bulk imports with dependency graph traversal.
Per Issue #777 and design doc Section 6.4.
"""

import asyncio
import logging
from collections import deque
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import AdaptiveQuestionnaire
from app.repositories.context_aware_repository import ContextAwareRepository
from app.schemas.collection import (
    GapAnalysisResponse,
    GapDetail,
    ProgressMetrics,
)

logger = logging.getLogger(__name__)


class GapAnalysisResults:
    """Results from bulk incremental gap analysis (multiple assets)."""

    def __init__(
        self,
        assets_analyzed: int,
        new_gaps_identified: int,
        gaps_closed: int,
        mode: str,
        dependency_depth_reached: Optional[int] = None,
        total_dependencies_analyzed: Optional[int] = None,
    ):
        self.assets_analyzed = assets_analyzed
        self.new_gaps_identified = new_gaps_identified
        self.gaps_closed = gaps_closed
        self.mode = mode
        self.dependency_depth_reached = dependency_depth_reached
        self.total_dependencies_analyzed = total_dependencies_analyzed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assets_analyzed": self.assets_analyzed,
            "new_gaps_identified": self.new_gaps_identified,
            "gaps_closed": self.gaps_closed,
            "mode": self.mode,
            "dependency_depth_reached": self.dependency_depth_reached,
            "total_dependencies_analyzed": self.total_dependencies_analyzed,
        }


class IncrementalGapAnalyzer:
    """
    Service for efficient gap recalculation after bulk imports.

    Provides:
    - Fast mode: Analyze only imported assets
    - Thorough mode: Analyze with dependency graph traversal
    - Guardrails: Max depth 3, max 10K assets, 60s timeout
    """

    # Traversal Guardrails (Per GPT-5 recommendation)
    MAX_DEPTH = 3
    MAX_ASSETS = 10_000
    GRAPH_BUILD_TIMEOUT = 60

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
    ):
        """
        Initialize incremental gap analyzer.

        Args:
            db: Async database session
            context: Request context with client_account_id, engagement_id
        """
        self.db = db
        self.context = context

        # Context-aware repositories
        self.questionnaire_repo = ContextAwareRepository(
            db, AdaptiveQuestionnaire, context
        )

    async def analyze_gaps(
        self,
        child_flow_id: UUID,
        asset_id: UUID,
        mode: str = "fast",
        critical_only: bool = False,
    ) -> GapAnalysisResponse:
        """
        Analyze gaps for a single asset.

        Args:
            child_flow_id: Collection child flow UUID
            asset_id: Asset UUID to analyze
            mode: "fast" or "thorough" analysis
            critical_only: If True, only return critical gaps

        Returns:
            Gap analysis response with progress metrics
        """
        # Get questionnaire for this asset
        questionnaires = await self.questionnaire_repo.get_by_filters(
            child_flow_id=child_flow_id,
            asset_id=asset_id,
        )

        if not questionnaires:
            # No questionnaire - all questions are gaps
            return GapAnalysisResponse(
                asset_id=str(asset_id),
                child_flow_id=str(child_flow_id),
                analysis_mode=mode,
                total_gaps=0,
                critical_gaps=0,
                gaps=[],
                progress_metrics=ProgressMetrics(
                    total_questions=0,
                    answered_questions=0,
                    unanswered_questions=0,
                    total_weight=0,
                    answered_weight=0,
                    completion_percent=0,
                ),
            )

        questionnaire = questionnaires[0]

        # Identify gaps
        gaps = await self._identify_gaps(questionnaire)

        # Filter critical-only if requested
        if critical_only:
            gaps = [g for g in gaps if g.get("is_critical", False)]

        # Convert to GapDetail objects
        gap_details = [
            GapDetail(
                question_id=g["question_id"],
                question_text=g.get("question_text", ""),
                section=g.get("section", "Unknown"),
                weight=g.get("weight", 40),
                is_critical=g.get("is_critical", False),
                depends_on=g.get("depends_on") if mode == "thorough" else None,
            )
            for g in gaps
        ]

        # Calculate progress metrics
        total_questions = len(questionnaire.closed_questions or []) + len(gaps)
        answered_questions = len(questionnaire.closed_questions or [])
        unanswered_questions = len(gaps)

        # Weight-based calculation (default weight = 40)
        answered_weight = answered_questions * 40
        total_weight = total_questions * 40
        completion_percent = (
            int((answered_weight / total_weight) * 100) if total_weight > 0 else 0
        )

        return GapAnalysisResponse(
            asset_id=str(asset_id),
            child_flow_id=str(child_flow_id),
            analysis_mode=mode,
            total_gaps=len(gap_details),
            critical_gaps=sum(1 for g in gap_details if g.is_critical),
            gaps=gap_details,
            progress_metrics=ProgressMetrics(
                total_questions=total_questions,
                answered_questions=answered_questions,
                unanswered_questions=unanswered_questions,
                total_weight=total_weight,
                answered_weight=answered_weight,
                completion_percent=completion_percent,
            ),
        )

    async def recalculate_incremental(
        self,
        asset_ids: List[UUID],
        mode: str = "fast",  # "fast" or "thorough"
    ) -> GapAnalysisResults:
        """
        Recalculate gaps for specified assets.

        Args:
            asset_ids: List of asset UUIDs to analyze
            mode: "fast" (assets only) or "thorough" (with dependencies)

        Returns:
            Gap analysis results
        """
        if mode == "fast":
            return await self._recalculate_fast(asset_ids)
        elif mode == "thorough":
            return await self._recalculate_thorough(asset_ids)
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'fast' or 'thorough'")

    async def _recalculate_fast(self, asset_ids: List[UUID]) -> GapAnalysisResults:
        """
        Analyze only the specified assets.

        Fastest option for large imports - no dependency traversal.
        """
        new_gaps_count = 0
        closed_gaps_count = 0

        for asset_id in asset_ids:
            # Get questionnaire for this asset
            questionnaires = await self.questionnaire_repo.get_by_filters(
                asset_id=asset_id
            )

            if not questionnaires:
                logger.warning(f"No questionnaire found for asset {asset_id}")
                continue

            questionnaire = questionnaires[0]

            # Analyze current state
            current_gaps = await self._identify_gaps(questionnaire)
            current_gap_ids = set(g["question_id"] for g in current_gaps)

            # Get previous gap state
            previous_gap_ids = set(questionnaire.reopened_questions or [])

            # Calculate changes
            newly_closed = previous_gap_ids - current_gap_ids
            newly_opened = current_gap_ids - previous_gap_ids

            closed_gaps_count += len(newly_closed)
            new_gaps_count += len(newly_opened)

            # Update questionnaire (would be done in actual implementation)
            logger.debug(
                f"Asset {asset_id}: {len(newly_closed)} gaps closed, "
                f"{len(newly_opened)} new gaps"
            )

        logger.info(
            f"✅ Fast gap analysis completed: {len(asset_ids)} assets analyzed, "
            f"{new_gaps_count} new gaps, {closed_gaps_count} gaps closed"
        )

        return GapAnalysisResults(
            assets_analyzed=len(asset_ids),
            new_gaps_identified=new_gaps_count,
            gaps_closed=closed_gaps_count,
            mode="fast",
        )

    async def _recalculate_thorough(self, asset_ids: List[UUID]) -> GapAnalysisResults:
        """
        Analyze specified assets AND their dependencies.

        Uses BFS traversal with guardrails:
        - Max depth: 3 levels
        - Max assets: 10,000
        - Timeout: 60 seconds for graph building
        - Circular dependency detection
        """
        # Build dependency graph with timeout
        try:
            dependency_graph = await asyncio.wait_for(
                self._build_dependency_graph(), timeout=self.GRAPH_BUILD_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(
                "⚠️  Dependency graph build timeout - falling back to fast mode"
            )
            return await self._recalculate_fast(asset_ids)

        # Find all affected assets using BFS with depth limit
        all_affected_assets = set(asset_ids)
        visited = set()
        queue = deque([(asset_id, 0) for asset_id in asset_ids])  # (asset_id, depth)
        max_depth_reached = 0

        while queue and len(all_affected_assets) < self.MAX_ASSETS:
            asset_id, depth = queue.popleft()

            if asset_id in visited or depth >= self.MAX_DEPTH:
                if depth >= self.MAX_DEPTH:
                    logger.debug(
                        f"Max depth {self.MAX_DEPTH} reached at asset {asset_id}"
                    )
                continue

            visited.add(asset_id)
            max_depth_reached = max(max_depth_reached, depth)

            # Get dependencies from graph
            dependencies = dependency_graph.get(asset_id, [])

            for dep_asset_id in dependencies:
                if dep_asset_id not in visited:
                    all_affected_assets.add(dep_asset_id)
                    queue.append((dep_asset_id, depth + 1))

        # Check if we hit the asset limit
        if len(all_affected_assets) >= self.MAX_ASSETS:
            logger.warning(
                f"⚠️  Reached max asset limit ({self.MAX_ASSETS}) during traversal"
            )

        # Now analyze all affected assets (same as fast mode)
        new_gaps_count = 0
        closed_gaps_count = 0

        for asset_id in all_affected_assets:
            questionnaires = await self.questionnaire_repo.get_by_filters(
                asset_id=asset_id
            )

            if not questionnaires:
                continue

            questionnaire = questionnaires[0]

            current_gaps = await self._identify_gaps(questionnaire)
            current_gap_ids = set(g["question_id"] for g in current_gaps)
            previous_gap_ids = set(questionnaire.reopened_questions or [])

            newly_closed = previous_gap_ids - current_gap_ids
            newly_opened = current_gap_ids - previous_gap_ids

            closed_gaps_count += len(newly_closed)
            new_gaps_count += len(newly_opened)

        logger.info(
            f"✅ Thorough gap analysis completed: {len(all_affected_assets)} assets analyzed "
            f"(original {len(asset_ids)}), max depth {max_depth_reached}, "
            f"{new_gaps_count} new gaps, {closed_gaps_count} gaps closed"
        )

        return GapAnalysisResults(
            assets_analyzed=len(all_affected_assets),
            new_gaps_identified=new_gaps_count,
            gaps_closed=closed_gaps_count,
            mode="thorough",
            dependency_depth_reached=max_depth_reached,
            total_dependencies_analyzed=len(all_affected_assets) - len(asset_ids),
        )

    async def _build_dependency_graph(self) -> Dict[UUID, List[UUID]]:
        """
        Build dependency graph from database.

        Returns:
            Dictionary mapping asset_id -> list of dependent asset_ids
        """
        # In a real implementation, this would query dependency tables
        # For now, return empty graph
        # TODO: Implement actual dependency graph building
        return {}

    async def _identify_gaps(
        self, questionnaire: AdaptiveQuestionnaire
    ) -> List[Dict[str, Any]]:
        """
        Identify current gaps for a questionnaire.

        A gap exists when:
        - Question is required
        - Question is not in closed_questions
        - Question does not have an answer in answers JSONB
        """
        gaps = []

        # Get all required questions for this asset type
        # In real implementation, would query CollectionQuestionRules
        # For now, return empty list as placeholder
        # TODO: Implement actual gap identification logic

        return gaps

    async def batch_update_progress(self, questionnaire_ids: List[UUID]) -> None:
        """
        Batch update progress calculations for multiple questionnaires.

        This would recalculate progress_percentage based on:
        - Total questions
        - Closed questions
        - Question weights
        """
        # Placeholder for batch progress update
        # TODO: Implement actual progress calculation
        logger.debug(
            f"Batch updating progress for {len(questionnaire_ids)} questionnaires"
        )
