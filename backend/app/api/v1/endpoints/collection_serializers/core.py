"""
Core Collection Flow Serialization Functions
Core serialization and data transformation functions for collection flows.
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AutomationTier
from app.models.discovery_flow import DiscoveryFlow
from app.models.sixr_analysis import SixRQuestionResponse as AdaptiveQuestionnaire
from app.models.collection_flow import CollectionGapAnalysis
from app.schemas.collection_flow import (
    CollectionFlowResponse,
    CollectionGapAnalysisResponse,
    AdaptiveQuestionnaireResponse,
)

logger = logging.getLogger(__name__)


def serialize_collection_flow(
    collection_flow: CollectionFlow,
    gaps_identified: int = 0,
    collection_metrics: Optional[Dict[str, Any]] = None,
) -> CollectionFlowResponse:
    """Serialize a CollectionFlow model to CollectionFlowResponse.

    Alias for build_collection_flow_response for backward compatibility.
    """
    return build_collection_flow_response(
        collection_flow, gaps_identified, collection_metrics
    )


def build_collection_flow_response(
    collection_flow: CollectionFlow,
    gaps_identified: int = 0,
    collection_metrics: Optional[Dict[str, Any]] = None,
) -> CollectionFlowResponse:
    """Build a CollectionFlowResponse from a CollectionFlow model.

    Args:
        collection_flow: Collection flow model instance
        gaps_identified: Number of gaps identified (optional)
        collection_metrics: Collection metrics dictionary (optional)

    Returns:
        CollectionFlowResponse object
    """
    # Build default collection metrics if not provided
    if collection_metrics is None:
        config = collection_flow.collection_config or {}

        # Support BOTH manual selection and automated detection paths
        # Manual path: application_count, selected_application_ids, processed_application_count
        # Automated path: detected_platforms, collection_quality_score
        platforms_detected = (
            config.get("application_count")  # Manual: total selected
            or len(config.get("selected_application_ids", []))  # Manual: from IDs array
            or len(config.get("application_details", []))  # Manual: from details array
            or len(
                config.get("detected_platforms", [])
            )  # Automated: platform detection
        )

        data_collected = (
            config.get("processed_application_count")  # Manual: apps processed
            or len(config.get("application_details", []))  # Manual: from details array
            or collection_flow.collection_quality_score  # Automated: quality score
            or 0
        )

        collection_metrics = {
            "platforms_detected": platforms_detected,
            "data_collected": data_collected,
            "gaps_resolved": 0,  # Default since resolution tracking isn't implemented
        }

    response_dict = {
        "id": str(collection_flow.flow_id),
        "client_account_id": str(collection_flow.client_account_id),
        "engagement_id": str(collection_flow.engagement_id),
        "status": collection_flow.status,
        "automation_tier": collection_flow.automation_tier,
        "current_phase": collection_flow.current_phase,
        "progress": collection_flow.progress_percentage or 0,
        "collection_config": collection_flow.collection_config,
        "created_at": collection_flow.created_at,
        "updated_at": collection_flow.updated_at,
        "completed_at": collection_flow.completed_at,
        "gaps_identified": gaps_identified,
        "collection_metrics": collection_metrics,
    }

    # Include discovery_flow_id if present
    if collection_flow.discovery_flow_id:
        response_dict["discovery_flow_id"] = str(collection_flow.discovery_flow_id)

    return CollectionFlowResponse(**response_dict)


def build_collection_config_from_discovery(
    discovery_flow: DiscoveryFlow,
    applications: List[Asset],
    selected_application_ids: List[str],
    collection_strategy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build collection configuration from discovery flow and applications.

    Args:
        discovery_flow: Discovery flow to extract data from
        applications: List of application assets
        selected_application_ids: List of selected application IDs
        collection_strategy: Optional collection strategy configuration

    Returns:
        Collection configuration dictionary
    """
    strategy = collection_strategy or {}

    # Determine automation tier
    automation_tier = strategy.get("automation_tier", AutomationTier.TIER_2.value)
    if strategy.get("automation_tier") == "inherited":
        discovery_metadata = discovery_flow.metadata or {}
        automation_tier = discovery_metadata.get(
            "detected_tier", AutomationTier.TIER_2.value
        )

    # Build discovery metadata
    discovery_metadata = {
        "completed_at": (
            discovery_flow.completed_at.isoformat()
            if discovery_flow.completed_at
            else None
        ),
        "data_quality_score": discovery_flow.data_quality_score,
    }

    # Build application snapshots (limit to first 10 for metadata size)
    application_snapshots = [
        {
            "id": str(app.id),
            "name": app.name,
            "business_criticality": app.business_criticality,
            "technology_stack": app.technology_stack,
            "architecture_pattern": app.architecture_pattern,
        }
        for app in applications[:10]
    ]

    return {
        "discovery_flow_id": str(discovery_flow.flow_id),
        "selected_application_ids": selected_application_ids,
        "application_count": len(selected_application_ids),
        "start_phase": strategy.get("start_phase", "gap_analysis"),
        "priority": strategy.get("priority", "critical_gaps_first"),
        "automation_tier": automation_tier,
        "discovery_metadata": discovery_metadata,
        "application_snapshots": application_snapshots,
    }


def build_collection_metrics_for_discovery_transition(
    selected_application_ids: List[str], discovery_flow_id: str, automation_tier: str
) -> Dict[str, Any]:
    """Build collection metrics for discovery-to-collection transition.

    Args:
        selected_application_ids: List of selected application IDs
        discovery_flow_id: Discovery flow ID
        automation_tier: Automation tier value

    Returns:
        Collection metrics dictionary
    """
    return {
        "applications_selected": len(selected_application_ids),
        "discovery_flow_id": discovery_flow_id,
        "automation_tier": automation_tier,
    }


def build_gap_analysis_response(
    gap: CollectionGapAnalysis,
) -> CollectionGapAnalysisResponse:
    """Build a CollectionGapAnalysisResponse from a gap analysis model.

    Args:
        gap: Gap analysis model instance

    Returns:
        CollectionGapAnalysisResponse object
    """
    return CollectionGapAnalysisResponse(
        id=str(gap.id),
        collection_flow_id=str(gap.collection_flow_id),
        attribute_name=gap.attribute_name,
        attribute_category=gap.attribute_category,
        business_impact=gap.business_impact,
        priority=gap.priority,
        collection_difficulty=gap.collection_difficulty,
        affects_strategies=gap.affects_strategies,
        blocks_decision=gap.blocks_decision,
        recommended_collection_method=gap.recommended_collection_method,
        resolution_status=gap.resolution_status,
        created_at=gap.created_at,
    )


def build_questionnaire_response(
    questionnaire: AdaptiveQuestionnaire,
) -> AdaptiveQuestionnaireResponse:
    """Build an AdaptiveQuestionnaireResponse from a questionnaire model.

    Args:
        questionnaire: Questionnaire model instance

    Returns:
        AdaptiveQuestionnaireResponse object with completion_status and optional status_line
    """
    # Generate status line for UI display based on completion_status
    status_line = None
    if questionnaire.completion_status == "pending":
        # Calculate estimated time (simple heuristic)
        from datetime import datetime, timezone

        if questionnaire.created_at:
            # Use timezone-aware datetime to match database timestamps
            now = datetime.now(timezone.utc)
            # Ensure created_at is timezone-aware
            if questionnaire.created_at.tzinfo is None:
                created_at_aware = questionnaire.created_at.replace(tzinfo=timezone.utc)
            else:
                created_at_aware = questionnaire.created_at
            elapsed = now - created_at_aware
            estimated_remaining = max(0, 30 - elapsed.total_seconds())  # 30s timeout
            status_line = f"Generating AI questionnaire... (Est. {int(estimated_remaining)}s remaining)"
        else:
            status_line = "Generating AI questionnaire... (Est. 30s remaining)"
    elif questionnaire.completion_status == "ready":
        status_line = "Questionnaire ready for completion"
    elif questionnaire.completion_status == "fallback":
        status_line = "Using bootstrap questionnaire template"
    elif questionnaire.completion_status == "failed":
        status_line = "Questionnaire generation failed - please try again"

    # Extract target_gaps from questions if not a direct attribute
    # This handles backward compatibility with older questionnaire models
    target_gaps = []
    if hasattr(questionnaire, "target_gaps") and questionnaire.target_gaps is not None:
        target_gaps = questionnaire.target_gaps
    else:
        # Log that we're using fallback extraction
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Questionnaire {questionnaire.id} missing target_gaps attribute, extracting from questions"
        )

        # Extract unique target gaps from individual questions while preserving order
        seen_gaps = set()
        for question in questionnaire.questions or []:
            if isinstance(question, dict):
                question_gaps = question.get("target_gaps", [])
                for gap in question_gaps:
                    if gap not in seen_gaps:
                        target_gaps.append(gap)
                        seen_gaps.add(gap)

        # Log if no gaps were found
        if not target_gaps:
            logger.debug(
                f"No target_gaps found in questionnaire {questionnaire.id} questions"
            )

    # Build base response
    response = AdaptiveQuestionnaireResponse(
        id=str(questionnaire.id),
        collection_flow_id=str(questionnaire.collection_flow_id),
        title=questionnaire.title,
        description=questionnaire.description,
        target_gaps=target_gaps,
        questions=questionnaire.questions,
        validation_rules=questionnaire.validation_rules,
        completion_status=questionnaire.completion_status,
        status_line=status_line,
        responses_collected=questionnaire.responses_collected,
        created_at=questionnaire.created_at,
        completed_at=questionnaire.completed_at,
    )

    return response
