"""
Collection Flow Response Builders
Response formatting functions for various collection flow operations.
"""

from typing import Any, Dict, List
from uuid import UUID

from app.models.collection_flow import CollectionFlow


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
