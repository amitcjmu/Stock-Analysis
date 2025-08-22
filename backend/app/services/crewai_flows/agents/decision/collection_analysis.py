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
    def analyze_questionnaire_generation(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze questionnaire generation results"""
        if not isinstance(results, dict):
            return {"questionnaires_count": 0, "confidence": 0}

        questionnaires = results.get("questionnaires_generated", [])

        return {
            "questionnaires_count": len(questionnaires),
            "confidence": results.get("crew_confidence", 0),
            "questionnaires": questionnaires,
            "adaptive_logic": results.get("adaptive_logic", {}),
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
    def analyze_collection_phase_results(
        phase: str, results: Any, state: Any
    ) -> Dict[str, Any]:
        """Main method to analyze collection-specific phase results"""
        if phase == "platform_detection":
            return CollectionAnalysis.analyze_platform_detection(results, state)
        elif phase == "automated_collection":
            return CollectionAnalysis.analyze_automated_collection(results, state)
        elif phase == "gap_analysis":
            return CollectionAnalysis.analyze_gap_analysis(results, state)
        elif phase == "questionnaire_generation":
            return CollectionAnalysis.analyze_questionnaire_generation(results, state)
        elif phase == "manual_collection":
            return CollectionAnalysis.analyze_manual_collection(results, state)
        elif phase == "synthesis":
            return CollectionAnalysis.analyze_synthesis(results, state)
        else:
            logger.warning(f"Unknown collection phase for analysis: {phase}")
            return {}
