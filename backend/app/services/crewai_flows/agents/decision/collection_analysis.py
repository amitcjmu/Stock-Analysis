"""
Collection Flow Phase Analysis Methods

Contains analysis methods specific to collection flow phases.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CollectionAnalysis:
    """Collection-specific analysis methods for phase results"""

    @staticmethod
    def analyze_platform_detection(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze platform detection results"""
        if not isinstance(results, dict):
            return {"platforms_detected": 0, "detection_confidence": 0}

        return {
            "platforms_detected": results.get("detected_platforms", {}).get("count", 0),
            "detection_confidence": results.get("crew_confidence", 0),
            "platforms_list": results.get("detected_platforms", {}).get(
                "platforms", []
            ),
            "adapter_recommendations": results.get("adapter_recommendations", []),
        }

    @staticmethod
    def analyze_automated_collection(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze automated collection results"""
        if not isinstance(results, dict):
            return {"data_collected": False, "quality_score": 0}

        return {
            "data_collected": results.get("collected_data", {}) != {},
            "quality_score": results.get("quality_scores", {}).get("overall", 0),
            "collection_metrics": results.get("collection_metrics", {}),
            "data_sources": results.get("data_sources", []),
        }

    @staticmethod
    def analyze_gap_analysis(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze gap analysis results"""
        if not isinstance(results, dict):
            return {"gaps_identified": [], "sixr_impact_high": False}

        gaps = results.get("identified_gaps", [])
        sixr_impact = results.get("sixr_impact", {})

        return {
            "gaps_identified": gaps,
            "gaps_count": len(gaps),
            "sixr_impact_high": sixr_impact.get("high_impact", False),
            "gap_categories": results.get("gap_categories", []),
            "severity_scores": results.get("gap_severity_scores", {}),
        }

    @staticmethod
    async def analyze_questionnaire_generation(
        results: Any, state: Any, db_session=None
    ) -> Dict[str, Any]:
        """
        Analyze questionnaire generation results.

        CRITICAL FIX (Bug #1055): Query database as source of truth for questionnaire count
        instead of relying on potentially incorrect phase result metadata.

        Args:
            results: Phase result dictionary (may have incorrect questionnaires_generated)
            state: Flow state object (contains collection_flow_id)
            db_session: Optional database session for querying actual questionnaire count

        Returns:
            Analysis dictionary with accurate questionnaires_count from database
        """
        if not isinstance(results, dict):
            return {"questionnaires_count": 0, "confidence": 0}

        # Default values from phase result metadata
        questionnaires_data = results.get("questionnaires_generated", [])
        questionnaires_count_from_result = 0

        # Handle both list and integer formats (legacy compatibility)
        if isinstance(questionnaires_data, list):
            questionnaires_count_from_result = len(questionnaires_data)
        elif isinstance(questionnaires_data, int):
            questionnaires_count_from_result = questionnaires_data

        # CRITICAL FIX: Query database as source of truth if db_session available
        actual_questionnaires_count = questionnaires_count_from_result
        data_source = "phase_result"

        if db_session and state:
            try:
                from sqlalchemy import select, func
                from app.models.collection_flow.adaptive_questionnaire_model import (
                    AdaptiveQuestionnaire,
                )
                from uuid import UUID

                # Extract collection_flow_id from state (try multiple possible locations)
                collection_flow_id = None
                if hasattr(state, "id"):
                    collection_flow_id = state.id
                elif hasattr(state, "collection_flow_id"):
                    collection_flow_id = state.collection_flow_id
                elif hasattr(state, "flow_id"):
                    collection_flow_id = state.flow_id
                elif isinstance(state, dict):
                    collection_flow_id = (
                        state.get("id")
                        or state.get("collection_flow_id")
                        or state.get("flow_id")
                    )

                if collection_flow_id:
                    # Convert to UUID if string
                    if isinstance(collection_flow_id, str):
                        collection_flow_id = UUID(collection_flow_id)

                    # Query database for actual questionnaire count
                    result = await db_session.execute(
                        select(func.count(AdaptiveQuestionnaire.id)).where(
                            AdaptiveQuestionnaire.collection_flow_id
                            == collection_flow_id
                        )
                    )
                    actual_questionnaires_count = result.scalar() or 0
                    data_source = "database"

                    logger.info(
                        f"✅ Questionnaire count from DATABASE: {actual_questionnaires_count} "
                        f"(phase_result had: {questionnaires_count_from_result})"
                    )
                else:
                    logger.warning(
                        "⚠️ Could not extract collection_flow_id from state - using phase_result"
                    )

            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to query database for questionnaire count (Bug #1055 fallback): {e}"
                )
                # Fallback to phase result on error
                data_source = "phase_result_fallback"
        else:
            if not db_session:
                logger.info(
                    "ℹ️ No db_session provided - using phase_result for questionnaire count"
                )
            if not state:
                logger.info(
                    "ℹ️ No state provided - using phase_result for questionnaire count"
                )

        return {
            "questionnaires_count": actual_questionnaires_count,
            "confidence": results.get("crew_confidence", 0),
            "questionnaires": (
                questionnaires_data if isinstance(questionnaires_data, list) else []
            ),
            "adaptive_logic": results.get("adaptive_logic", {}),
            "data_source": data_source,  # Track whether we used database or phase_result
        }

    @staticmethod
    def analyze_manual_collection(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze manual collection results"""
        if not isinstance(results, dict):
            return {"responses_received": 0, "response_quality": 0}

        responses = results.get("questionnaire_responses", [])

        return {
            "responses_received": len(responses),
            "response_quality": results.get("response_quality", {}).get("overall", 0),
            "responses": responses,
            "validation_results": results.get("validation_results", {}),
        }

    @staticmethod
    def analyze_synthesis(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze synthesis results"""
        if not isinstance(results, dict):
            return {"quality_score": 0, "sixr_readiness": 0}

        return {
            "quality_score": results.get("quality_report", {}).get(
                "overall_quality", 0
            ),
            "sixr_readiness": results.get("sixr_readiness", 0),
            "synthesized_data": results.get("synthesized_data", {}),
            "data_lineage": results.get("data_lineage", {}),
        }

    @staticmethod
    async def analyze_collection_phase_results(
        phase: str, results: Any, state: Any, db_session=None
    ) -> Dict[str, Any]:
        """
        Main method to analyze collection-specific phase results.

        Args:
            phase: Phase name
            results: Phase result dictionary
            state: Flow state object
            db_session: Optional database session (required for Bug #1055 fix in questionnaire_generation)

        Returns:
            Analysis dictionary with phase-specific metrics
        """
        if phase == "platform_detection":
            return CollectionAnalysis.analyze_platform_detection(results, state)
        elif phase == "automated_collection":
            return CollectionAnalysis.analyze_automated_collection(results, state)
        elif phase == "gap_analysis":
            return CollectionAnalysis.analyze_gap_analysis(results, state)
        elif phase == "questionnaire_generation":
            # CRITICAL: Pass db_session for Bug #1055 database query
            return await CollectionAnalysis.analyze_questionnaire_generation(
                results, state, db_session
            )
        elif phase == "manual_collection":
            return CollectionAnalysis.analyze_manual_collection(results, state)
        elif phase == "synthesis":
            return CollectionAnalysis.analyze_synthesis(results, state)
        else:
            logger.warning(f"Unknown collection phase for analysis: {phase}")
            return {}
