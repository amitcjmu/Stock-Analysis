"""
Discovery Handler Helper Functions

Shared utility functions used across discovery flow handlers.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _get_asset_breakdown(flow_state: Dict[str, Any]) -> Dict[str, int]:
    """Get breakdown of assets by type"""
    assets = flow_state.get("assets", [])
    breakdown = {}

    for asset in assets:
        asset_type = asset.get("asset_type", "unknown")
        breakdown[asset_type] = breakdown.get(asset_type, 0) + 1

    return breakdown


def _calculate_validation_rate(flow_state: Dict[str, Any]) -> float:
    """Calculate validation pass rate"""
    total_validations = flow_state.get("total_validations", 0)
    passed_validations = flow_state.get("passed_validations", 0)

    if total_validations == 0:
        return 0.0

    return passed_validations / total_validations


async def _send_notifications(flow_id: str, summary_report: Dict[str, Any]) -> bool:
    """Send completion notifications"""
    # Placeholder for notification logic
    logger.info(f"Sending notifications for flow {flow_id}")
    return True


async def _generate_reports(flow_id: str, flow_state: Dict[str, Any]) -> List[str]:
    """Generate discovery reports"""
    # Placeholder for report generation
    reports = [
        f"discovery_summary_{flow_id}.pdf",
        f"asset_inventory_{flow_id}.xlsx",
        f"data_quality_report_{flow_id}.html",
    ]
    logger.info(f"Generated reports for flow {flow_id}: {reports}")
    return reports


def _identify_next_steps(summary_report: Dict[str, Any]) -> List[str]:
    """Identify recommended next steps"""
    next_steps = []

    if summary_report["summary"]["total_assets_discovered"] > 0:
        next_steps.append("Run assessment flow to analyze discovered assets")

    if summary_report["summary"]["errors_encountered"] > 0:
        next_steps.append("Review and resolve discovery errors")

    if summary_report["quality_metrics"]["data_quality_score"] < 0.8:
        next_steps.append("Improve data quality before proceeding")

    return next_steps


def _classify_error(error: Exception) -> Dict[str, Any]:
    """Classify error type and severity"""
    error_str = str(error).lower()

    # Determine error type
    if "connection" in error_str or "timeout" in error_str:
        error_type = "connectivity"
        severity = "medium"
        can_retry = True
    elif "permission" in error_str or "unauthorized" in error_str:
        error_type = "authorization"
        severity = "high"
        can_retry = False
    elif "validation" in error_str:
        error_type = "validation"
        severity = "low"
        can_retry = True
    elif "memory" in error_str or "resource" in error_str:
        error_type = "resource"
        severity = "critical"
        can_retry = False
    else:
        error_type = "unknown"
        severity = "medium"
        can_retry = True

    return {
        "type": error_type,
        "severity": severity,
        "can_retry": can_retry,
        "requires_manual": severity in ["critical", "high"],
    }


def _determine_recovery_action(
    error_classification: Dict[str, Any], phase: str, flow_state: Dict[str, Any]
) -> str:
    """Determine appropriate recovery action"""
    if not error_classification["can_retry"]:
        return "manual_intervention_required"

    if error_classification["type"] == "connectivity":
        return "retry_with_backoff"

    if error_classification["type"] == "validation":
        return "retry_with_data_cleanup"

    if phase in ["data_import", "field_mapping"]:
        return "restart_from_phase"

    return "restart_from_last_checkpoint"


async def _execute_recovery(
    flow_id: str, recovery_action: str, flow_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute recovery procedures"""
    logger.info(f"Executing recovery action '{recovery_action}' for flow {flow_id}")

    recovery_result = {
        "action": recovery_action,
        "executed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if recovery_action == "retry_with_backoff":
        recovery_result["retry_delay_seconds"] = 30
    elif recovery_action == "restart_from_last_checkpoint":
        recovery_result["checkpoint"] = flow_state.get("last_checkpoint", "beginning")

    return recovery_result


async def _send_error_alerts(flow_id: str, error_report: Dict[str, Any]) -> None:
    """Send error alerts"""
    logger.warning(
        f"Sending error alerts for flow {flow_id}: {error_report['error_type']}"
    )


async def _validate_created_assets(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate created assets"""
    passed = 0
    failed = 0

    for asset in assets:
        if all(field in asset for field in ["asset_id", "asset_type", "name"]):
            passed += 1
        else:
            failed += 1

    return {
        "total": len(assets),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / len(assets) if assets else 0,
    }


def _create_asset_indexes(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create indexes for fast asset lookup"""
    indexes = {"by_id": {}, "by_type": {}, "by_name": {}}

    for asset in assets:
        asset_id = asset.get("asset_id")
        asset_type = asset.get("asset_type")
        asset_name = asset.get("name")

        if asset_id:
            indexes["by_id"][asset_id] = asset

        if asset_type:
            if asset_type not in indexes["by_type"]:
                indexes["by_type"][asset_type] = []
            indexes["by_type"][asset_type].append(asset)

        if asset_name:
            indexes["by_name"][asset_name] = asset

    return indexes


def _map_asset_relationships(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map relationships between assets"""
    relationships = []

    # Simple relationship mapping based on common patterns
    for asset in assets:
        # Check for explicit relationships
        if "depends_on" in asset:
            for dependency in asset["depends_on"]:
                relationships.append(
                    {
                        "source": asset["asset_id"],
                        "target": dependency,
                        "type": "depends_on",
                    }
                )

        # Check for parent-child relationships
        if "parent_id" in asset:
            relationships.append(
                {
                    "source": asset["asset_id"],
                    "target": asset["parent_id"],
                    "type": "child_of",
                }
            )

    return relationships


def _prepare_cmdb_format(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare assets for CMDB integration"""
    cmdb_assets = []

    for asset in assets:
        cmdb_asset = {
            "ci_id": asset.get("asset_id"),
            "ci_type": asset.get("asset_type"),
            "ci_name": asset.get("name"),
            "attributes": {
                k: v
                for k, v in asset.items()
                if k not in ["asset_id", "asset_type", "name"]
            },
        }
        cmdb_assets.append(cmdb_asset)

    return cmdb_assets


def _count_asset_types(assets: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count assets by type"""
    type_counts = {}

    for asset in assets:
        asset_type = asset.get("asset_type", "unknown")
        type_counts[asset_type] = type_counts.get(asset_type, 0) + 1

    return type_counts
