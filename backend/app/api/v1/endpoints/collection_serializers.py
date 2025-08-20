"""
Collection Flow Serializers
Data transformation and serialization functions for collection flows including
model-to-response conversion, configuration builders, and metadata creation.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

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
        collection_metrics = {
            "platforms_detected": len(
                collection_flow.collection_config.get("detected_platforms", [])
            ),
            "data_collected": collection_flow.collection_quality_score or 0,
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
        AdaptiveQuestionnaireResponse object
    """
    return AdaptiveQuestionnaireResponse(
        id=str(questionnaire.id),
        collection_flow_id=str(questionnaire.collection_flow_id),
        title=questionnaire.title,
        description=questionnaire.description,
        target_gaps=questionnaire.target_gaps,
        questions=questionnaire.questions,
        validation_rules=questionnaire.validation_rules,
        completion_status=questionnaire.completion_status,
        responses_collected=questionnaire.responses_collected,
        created_at=questionnaire.created_at,
        completed_at=questionnaire.completed_at,
    )


def build_collection_status_response(collection_flow: CollectionFlow) -> Dict[str, Any]:
    """Build collection status response dictionary.

    Args:
        collection_flow: Collection flow model instance

    Returns:
        Status response dictionary
    """
    return {
        "flow_id": str(collection_flow.flow_id),
        "status": collection_flow.status,
        "current_phase": collection_flow.current_phase,
        "automation_tier": collection_flow.automation_tier,
        "progress": collection_flow.progress_percentage or 0,
        "created_at": collection_flow.created_at.isoformat(),
        "updated_at": collection_flow.updated_at.isoformat(),
    }


def build_no_active_flow_response() -> Dict[str, Any]:
    """Build response for when no active flow is found.

    Returns:
        No active flow response dictionary
    """
    return {
        "status": "no_active_flow",
        "message": "No active collection flow found",
    }


def build_execution_response(
    flow_id: str, execution_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Build collection flow execution response.

    Args:
        flow_id: Flow ID that was executed
        execution_result: Result from the execution

    Returns:
        Execution response dictionary
    """
    return {
        "success": True,
        "flow_id": flow_id,
        "status": "executed",
        "execution_result": execution_result,
        "message": "Collection flow phase executed successfully",
    }


def build_questionnaire_submission_response(questionnaire_id: str) -> Dict[str, Any]:
    """Build questionnaire submission response.

    Args:
        questionnaire_id: ID of the submitted questionnaire

    Returns:
        Submission response dictionary
    """
    return {
        "status": "success",
        "message": "Questionnaire responses submitted successfully",
        "questionnaire_id": questionnaire_id,
    }


def build_readiness_response(
    flow_id: str,
    engagement_id: UUID,
    apps_ready: int,
    collection_flow: CollectionFlow,
    validation_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Build collection readiness response.

    Args:
        flow_id: Collection flow ID
        engagement_id: Engagement ID
        apps_ready: Number of ready applications
        collection_flow: Collection flow model instance
        validation_results: Validation results from data flow validator

    Returns:
        Readiness response dictionary
    """
    return {
        "flow_id": flow_id,
        "engagement_id": str(engagement_id),
        "apps_ready_for_assessment": apps_ready,
        "quality": {
            "collection_quality_score": collection_flow.collection_quality_score or 0.0,
            "confidence_score": collection_flow.confidence_score or 0.0,
        },
        "phase_scores": validation_results["phase_scores"],
        "issues": validation_results["issues"],
        "readiness": validation_results["readiness"],
        "updated_at": collection_flow.updated_at,
    }


def build_continue_flow_response(
    flow_id: str, result: Dict[str, Any]
) -> Dict[str, Any]:
    """Build continue/resume flow response.

    Args:
        flow_id: Flow ID that was continued
        result: Result from the resume operation

    Returns:
        Continue flow response dictionary
    """
    return {
        "status": "success",
        "message": "Collection flow resumed successfully",
        "flow_id": flow_id,
        "resume_result": result,
    }


def build_delete_flow_response(flow_id: str) -> Dict[str, Any]:
    """Build delete flow response.

    Args:
        flow_id: Flow ID that was deleted

    Returns:
        Delete flow response dictionary
    """
    return {
        "status": "success",
        "message": "Collection flow deleted successfully",
        "flow_id": flow_id,
    }


def build_cleanup_response(
    flows_cleaned: List[Dict[str, Any]],
    total_size: int,
    dry_run: bool,
    cleanup_criteria: Dict[str, Any],
) -> Dict[str, Any]:
    """Build cleanup flows response.

    Args:
        flows_cleaned: List of cleaned flow details
        total_size: Total estimated size in bytes
        dry_run: Whether this was a dry run
        cleanup_criteria: Cleanup criteria used

    Returns:
        Cleanup response dictionary
    """
    return {
        "status": "success",
        "dry_run": dry_run,
        "flows_cleaned": len(flows_cleaned),
        "total_size_bytes": total_size,
        "space_recovered": f"{total_size / 1024:.1f} KB" if total_size > 0 else "0 KB",
        "flows_details": flows_cleaned,
        "cleanup_criteria": cleanup_criteria,
    }


def build_batch_delete_response(
    deleted_flows: List[str], failed_deletions: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Build batch delete response.

    Args:
        deleted_flows: List of successfully deleted flow IDs
        failed_deletions: List of failed deletion details

    Returns:
        Batch delete response dictionary
    """
    return {
        "status": "success",
        "deleted_count": len(deleted_flows),
        "failed_count": len(failed_deletions),
        "deleted_flows": deleted_flows,
        "failed_deletions": failed_deletions,
    }


def build_cleanup_flow_details(flow: CollectionFlow) -> Dict[str, Any]:
    """Build details for a flow being cleaned up.

    Args:
        flow: Collection flow to build details for

    Returns:
        Flow details dictionary
    """
    from app.api.v1.endpoints.collection_utils import calculate_time_since_creation

    time_since_update = calculate_time_since_creation(flow.updated_at)
    estimated_size = (
        len(str(flow.collection_config or {}))
        + len(str(flow.phase_state or {}))
        + len(str(flow.collection_results or {}))
    )

    return {
        "flow_id": str(flow.flow_id),
        "status": flow.status,
        "age_hours": time_since_update.total_seconds() / 3600,
        "estimated_size": estimated_size,
    }


def normalize_tenant_ids(
    client_account_id: Any, engagement_id: Any
) -> tuple[UUID, UUID]:
    """Normalize tenant IDs to UUIDs.

    Args:
        client_account_id: Client account ID (any format)
        engagement_id: Engagement ID (any format)

    Returns:
        Tuple of (client_uuid, engagement_uuid)

    Raises:
        ValueError: If IDs cannot be converted to UUIDs
    """
    try:
        client_uuid = UUID(str(client_account_id))
        engagement_uuid = UUID(str(engagement_id))
        return client_uuid, engagement_uuid
    except Exception as e:
        raise ValueError(f"Invalid tenant identifiers: {e}")


def build_application_snapshot(application: Asset) -> Dict[str, Any]:
    """Build an application snapshot for metadata storage.

    Args:
        application: Application asset to snapshot

    Returns:
        Application snapshot dictionary
    """
    return {
        "id": str(application.id),
        "name": application.name,
        "business_criticality": application.business_criticality,
        "technology_stack": application.technology_stack,
        "architecture_pattern": application.architecture_pattern,
    }


def extract_application_ids_from_assets(applications: List[Asset]) -> List[str]:
    """Extract string IDs from application assets.

    Args:
        applications: List of application assets

    Returns:
        List of application ID strings
    """
    return [str(app.id) for app in applications]
