"""
Discovery Flow Handlers
MFO-041: Implement Discovery asset creation handler

Handlers for discovery flow lifecycle events and asset creation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def discovery_initialization(
    flow_id: str, flow_type: str, context: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Initialize discovery flow

    Sets up:
    - Initial flow state
    - Configuration defaults
    - Resource allocation
    - Monitoring setup
    """
    try:
        logger.info(f"Initializing discovery flow {flow_id}")

        # Extract configuration
        config = kwargs.get("configuration", {})
        initial_state = kwargs.get("initial_state", {})

        # Set up discovery-specific initialization
        initialization_result = {
            "initialized": True,
            "flow_id": flow_id,
            "initialization_time": datetime.utcnow().isoformat(),
            "discovery_config": {
                "parallel_processing": config.get("parallel_processing", True),
                "incremental_discovery": config.get("incremental_discovery", True),
                "data_quality_threshold": config.get("data_quality_threshold", 0.95),
                "auto_remediation": config.get("auto_remediation", True),
                "batch_size": config.get("batch_size", 1000),
                "validation_mode": config.get("validation_mode", "strict"),
            },
            "resource_allocation": {
                "cpu_cores": config.get("cpu_cores", 4),
                "memory_gb": config.get("memory_gb", 8),
                "storage_gb": config.get("storage_gb", 100),
            },
            "monitoring": {
                "metrics_enabled": True,
                "log_level": config.get("log_level", "INFO"),
                "alerts_enabled": config.get("alerts_enabled", True),
            },
        }

        # Set up data sources if provided
        if "data_sources" in initial_state:
            initialization_result["data_sources"] = initial_state["data_sources"]

        # Initialize statistics tracking
        initialization_result["statistics"] = {
            "total_records_processed": 0,
            "assets_created": 0,
            "errors_encountered": 0,
            "warnings_generated": 0,
            "start_time": datetime.utcnow().isoformat(),
        }

        logger.info(f"Discovery flow {flow_id} initialized successfully")
        return initialization_result

    except Exception as e:
        logger.error(f"Discovery initialization error for flow {flow_id}: {e}")
        return {
            "initialized": False,
            "flow_id": flow_id,
            "error": str(e),
            "initialization_time": datetime.utcnow().isoformat(),
        }


async def discovery_finalization(
    flow_id: str, flow_type: str, context: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Finalize discovery flow

    Performs:
    - Final validation
    - Report generation
    - Resource cleanup
    - Notifications
    """
    try:
        logger.info(f"Finalizing discovery flow {flow_id}")

        flow_state = kwargs.get("flow_state", {})

        # Calculate final statistics
        statistics = flow_state.get("statistics", {})
        statistics["end_time"] = datetime.utcnow().isoformat()

        # Generate summary report
        summary_report = {
            "flow_id": flow_id,
            "completion_time": datetime.utcnow().isoformat(),
            "status": "completed",
            "summary": {
                "total_assets_discovered": statistics.get("assets_created", 0),
                "total_records_processed": statistics.get("total_records_processed", 0),
                "data_sources_processed": len(flow_state.get("data_sources", [])),
                "errors_encountered": statistics.get("errors_encountered", 0),
                "warnings_generated": statistics.get("warnings_generated", 0),
                "duration_seconds": None,  # Would calculate from start/end times
            },
            "asset_breakdown": _get_asset_breakdown(flow_state),
            "quality_metrics": {
                "data_quality_score": flow_state.get("data_quality_score", 0),
                "validation_pass_rate": _calculate_validation_rate(flow_state),
                "duplicate_removal_rate": flow_state.get("duplicate_removal_rate", 0),
            },
        }

        # Trigger post-discovery actions
        post_actions = {
            "notifications_sent": await _send_notifications(flow_id, summary_report),
            "reports_generated": await _generate_reports(flow_id, flow_state),
            "next_steps_identified": _identify_next_steps(summary_report),
        }

        finalization_result = {
            "finalized": True,
            "flow_id": flow_id,
            "finalization_time": datetime.utcnow().isoformat(),
            "summary_report": summary_report,
            "post_actions": post_actions,
            "ready_for_assessment": summary_report["summary"]["total_assets_discovered"]
            > 0,
        }

        logger.info(f"Discovery flow {flow_id} finalized successfully")
        return finalization_result

    except Exception as e:
        logger.error(f"Discovery finalization error for flow {flow_id}: {e}")
        return {
            "finalized": False,
            "flow_id": flow_id,
            "error": str(e),
            "finalization_time": datetime.utcnow().isoformat(),
        }


async def discovery_error_handler(
    flow_id: str, flow_type: str, error: Exception, context: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Handle discovery flow errors

    Implements:
    - Error classification
    - Recovery strategies
    - Rollback procedures
    - Alert generation
    """
    try:
        logger.error(f"Handling error for discovery flow {flow_id}: {error}")

        phase = kwargs.get("phase", "unknown")
        flow_state = kwargs.get("flow_state", {})

        # Classify error
        error_classification = _classify_error(error)

        # Determine recovery action
        recovery_action = _determine_recovery_action(
            error_classification, phase, flow_state
        )

        # Generate error report
        error_report = {
            "flow_id": flow_id,
            "error_time": datetime.utcnow().isoformat(),
            "error_type": error_classification["type"],
            "error_severity": error_classification["severity"],
            "error_message": str(error),
            "phase": phase,
            "recovery_action": recovery_action,
            "can_retry": error_classification.get("can_retry", True),
            "requires_manual_intervention": error_classification.get(
                "requires_manual", False
            ),
        }

        # Execute recovery procedures
        recovery_result = await _execute_recovery(flow_id, recovery_action, flow_state)

        # Send alerts if needed
        if error_classification["severity"] in ["critical", "high"]:
            await _send_error_alerts(flow_id, error_report)

        return {
            "error_handled": True,
            "flow_id": flow_id,
            "error_report": error_report,
            "recovery_result": recovery_result,
            "next_action": recovery_action,
        }

    except Exception as e:
        logger.error(f"Error handler failed for flow {flow_id}: {e}")
        return {
            "error_handled": False,
            "flow_id": flow_id,
            "handler_error": str(e),
            "original_error": str(error),
        }


async def asset_creation_completion(
    flow_id: str, phase_name: str, phase_output: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Handle asset creation phase completion

    Performs:
    - Asset validation
    - Index creation
    - Relationship mapping
    - Integration with CMDB
    """
    try:
        logger.info(f"Handling asset creation completion for flow {flow_id}")

        assets = phase_output.get("assets", [])
        phase_output.get("creation_report", {})

        # Validate created assets
        validation_results = await _validate_created_assets(assets)

        # Create asset indexes for fast lookup
        asset_indexes = _create_asset_indexes(assets)

        # Map relationships between assets
        relationships = _map_asset_relationships(assets)

        # Prepare for CMDB integration
        cmdb_ready_assets = _prepare_cmdb_format(assets)

        # Update statistics
        statistics_update = {
            "assets_created": len(assets),
            "asset_types": _count_asset_types(assets),
            "validation_passed": validation_results["passed"],
            "validation_failed": validation_results["failed"],
            "relationships_mapped": len(relationships),
        }

        completion_result = {
            "phase_completed": True,
            "flow_id": flow_id,
            "phase": phase_name,
            "completion_time": datetime.utcnow().isoformat(),
            "assets_created": len(assets),
            "validation_results": validation_results,
            "asset_indexes": asset_indexes,
            "relationships": relationships,
            "cmdb_integration": {
                "ready": len(cmdb_ready_assets) > 0,
                "asset_count": len(cmdb_ready_assets),
            },
            "statistics_update": statistics_update,
        }

        logger.info(
            f"Asset creation completed for flow {flow_id}: {len(assets)} assets created"
        )
        return completion_result

    except Exception as e:
        logger.error(f"Asset creation completion handler error for flow {flow_id}: {e}")
        return {
            "phase_completed": False,
            "flow_id": flow_id,
            "phase": phase_name,
            "error": str(e),
            "completion_time": datetime.utcnow().isoformat(),
        }


async def asset_inventory(
    flow_id: str, phase_input: Dict[str, Any], context: Any, **kwargs
) -> Dict[str, Any]:
    """
    Execute asset inventory phase

    Performs:
    - Asset classification
    - Server identification
    - Application discovery
    - Device categorization
    
    Note: This is a simplified handler that returns success to allow
    phase progression. The actual asset creation happens through
    the crew execution in execution_engine_crew.py
    """
    try:
        logger.info(f"Executing asset inventory handler for flow {flow_id}")

        # Extract relevant data from phase_input
        raw_data = phase_input.get("raw_data", [])
        field_mappings = phase_input.get("field_mappings", {})
        
        # Log what we're processing
        logger.info(f"Processing {len(raw_data) if isinstance(raw_data, list) else 0} records for asset inventory")
        
        # Return success to allow phase progression
        # The actual asset creation logic is handled by the crew execution
        return {
            "phase": "asset_inventory",
            "status": "completed",
            "flow_id": flow_id,
            "records_processed": len(raw_data) if isinstance(raw_data, list) else 0,
            "message": "Asset inventory phase completed successfully",
            "next_phase": "dependency_analysis",
        }

    except Exception as e:
        logger.error(f"Asset inventory handler error for flow {flow_id}: {e}")
        return {
            "phase": "asset_inventory",
            "status": "failed",
            "error": str(e),
            "flow_id": flow_id,
        }


async def data_import_preparation(
    flow_id: str, phase_name: str, phase_input: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Prepare for data import phase
    """
    try:
        logger.info(f"Preparing data import for flow {flow_id}")

        # Validate data sources
        raw_data = phase_input.get("raw_data", [])
        import_config = phase_input.get("import_config", {})

        preparation_result = {
            "prepared": True,
            "flow_id": flow_id,
            "phase": phase_name,
            "data_source_count": len(raw_data) if isinstance(raw_data, list) else 1,
            "import_mode": import_config.get("mode", "batch"),
            "validation_enabled": import_config.get("validate", True),
        }

        return preparation_result

    except Exception as e:
        logger.error(f"Data import preparation error: {e}")
        return {"prepared": False, "flow_id": flow_id, "error": str(e)}


async def data_import_validation(
    flow_id: str, phase_name: str, phase_output: Dict[str, Any], **kwargs
) -> Dict[str, Any]:
    """
    Validate data import results
    """
    try:
        imported_data = phase_output.get("imported_data", [])
        validation_report = phase_output.get("validation_report", {})

        return {
            "validated": True,
            "flow_id": flow_id,
            "phase": phase_name,
            "records_imported": (
                len(imported_data) if isinstance(imported_data, list) else 0
            ),
            "validation_summary": validation_report,
        }

    except Exception as e:
        logger.error(f"Data import validation error: {e}")
        return {"validated": False, "flow_id": flow_id, "error": str(e)}


# Helper functions


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
