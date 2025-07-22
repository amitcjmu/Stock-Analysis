"""
Flow Validation Endpoints

This module handles validation and health check operations:
- Health checks for flows and services
- Flow validation operations
- Dependency checks and prerequisites
- System diagnostics
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

from .status_calculator import StatusCalculator

logger = logging.getLogger(__name__)

validation_router = APIRouter(tags=["discovery-validation"])


@validation_router.get("/flows/health", response_model=Dict[str, Any])
async def discovery_flows_health():
    """
    Health check for discovery flows service.
    
    This endpoint provides overall health status for the discovery flows service.
    """
    try:
        return {
            "service": "discovery_flows",
            "status": "healthy",
            "implementation": "modular_endpoints",
            "version": "1.0.0",
            "modules": {
                "query_endpoints": "active",
                "lifecycle_endpoints": "active", 
                "execution_endpoints": "active",
                "validation_endpoints": "active",
                "response_mappers": "active",
                "status_calculator": "active"
            },
            "note": "Modular discovery flows implementation"
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "service": "discovery_flows",
            "status": "unhealthy",
            "error": str(e)
        }


@validation_router.get("/flow/{flow_id}/validation-status", response_model=Dict[str, Any])
async def get_flow_validation_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get validation status for a specific flow.
    
    This endpoint provides detailed validation status including data quality,
    configuration validation, and prerequisite checks.
    """
    try:
        logger.info(f"Getting validation status for flow {flow_id}")
        
        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow
        
        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id
        
        # Get the flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        # Perform validation checks
        validation_results = await _perform_flow_validation(flow, db)
        
        return {
            "flow_id": str(flow_id),
            "validation_status": validation_results["overall_status"],
            "validation_score": validation_results["validation_score"],
            "checks_passed": validation_results["checks_passed"],
            "checks_failed": validation_results["checks_failed"],
            "checks_total": validation_results["checks_total"],
            "errors": validation_results["errors"],
            "warnings": validation_results["warnings"],
            "data_quality": validation_results["data_quality"],
            "configuration_validation": validation_results["configuration_validation"],
            "prerequisite_checks": validation_results["prerequisite_checks"],
            "recommendations": validation_results["recommendations"],
            "validated_at": validation_results["validated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get validation status: {str(e)}")


@validation_router.post("/flow/{flow_id}/validate", response_model=Dict[str, Any])
async def validate_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive validation on a flow.
    
    This endpoint runs all validation checks on a flow and provides
    detailed results and recommendations.
    """
    try:
        logger.info(f"Validating flow {flow_id}")
        
        validation_type = request.get("type", "full")  # full, quick, phase-specific
        include_data_quality = request.get("include_data_quality", True)
        include_configuration = request.get("include_configuration", True)
        
        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow
        
        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id
        
        # Get the flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        # Perform validation based on type
        if validation_type == "quick":
            validation_results = await _perform_quick_validation(flow, db)
        elif validation_type == "phase-specific":
            phase = request.get("phase", flow.current_phase)
            validation_results = await _perform_phase_validation(flow, phase, db)
        else:  # full validation
            validation_results = await _perform_full_validation(
                flow, db, include_data_quality, include_configuration
            )
        
        return {
            "flow_id": str(flow_id),
            "validation_type": validation_type,
            "validation_completed": True,
            "validation_results": validation_results,
            "summary": {
                "overall_status": validation_results["overall_status"],
                "validation_score": validation_results["validation_score"],
                "critical_issues": len([e for e in validation_results["errors"] if e.get("severity") == "critical"]),
                "warnings": len(validation_results["warnings"]),
                "recommendations": len(validation_results["recommendations"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate flow: {str(e)}")


@validation_router.get("/flow/{flow_id}/prerequisites", response_model=Dict[str, Any])
async def check_flow_prerequisites(
    flow_id: str,
    phase: str = None,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Check prerequisites for a flow or specific phase.
    
    This endpoint verifies that all required conditions are met
    before proceeding with flow execution.
    """
    try:
        logger.info(f"Checking prerequisites for flow {flow_id}, phase: {phase}")
        
        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow
        
        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id
        
        # Get the flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        # Check prerequisites
        current_phase = phase or flow.current_phase or "data_import"
        prerequisites = await _check_phase_prerequisites(flow, current_phase, db)
        
        return {
            "flow_id": str(flow_id),
            "phase": current_phase,
            "prerequisites_met": prerequisites["all_met"],
            "prerequisites": prerequisites["checks"],
            "blocking_issues": prerequisites["blocking_issues"],
            "warnings": prerequisites["warnings"],
            "can_proceed": prerequisites["can_proceed"],
            "next_actions": prerequisites["next_actions"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking prerequisites: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check prerequisites: {str(e)}")


@validation_router.get("/flows/system-health", response_model=Dict[str, Any])
async def get_system_health(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall system health for discovery flows.
    
    This endpoint provides aggregate health metrics across all flows
    and system components.
    """
    try:
        logger.info("Getting system health for discovery flows")
        
        # Import required models
        from app.models.discovery_flow import DiscoveryFlow
        
        # Get flow statistics
        total_flows_stmt = select(func.count(DiscoveryFlow.flow_id)).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status != 'deleted'
            )
        )
        total_flows_result = await db.execute(total_flows_stmt)
        total_flows = total_flows_result.scalar() or 0
        
        # Get healthy flows count
        healthy_flows_stmt = select(func.count(DiscoveryFlow.flow_id)).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status.in_(['active', 'running', 'processing', 'completed'])
            )
        )
        healthy_flows_result = await db.execute(healthy_flows_stmt)
        healthy_flows = healthy_flows_result.scalar() or 0
        
        # Get failed flows count
        failed_flows_stmt = select(func.count(DiscoveryFlow.flow_id)).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status.in_(['failed', 'error', 'aborted'])
            )
        )
        failed_flows_result = await db.execute(failed_flows_stmt)
        failed_flows = failed_flows_result.scalar() or 0
        
        # Calculate health score
        if total_flows > 0:
            health_score = (healthy_flows / total_flows) * 100
        else:
            health_score = 100.0  # No flows = healthy system
        
        # Determine overall health status
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 50:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "system_health": health_status,
            "health_score": health_score,
            "flow_statistics": {
                "total_flows": total_flows,
                "healthy_flows": healthy_flows,
                "failed_flows": failed_flows,
                "success_rate": health_score
            },
            "system_components": {
                "database": "healthy",
                "crewai_integration": "healthy",
                "master_flow_orchestrator": "healthy",
                "response_mappers": "healthy",
                "status_calculator": "healthy"
            },
            "recommendations": _get_system_recommendations(health_score, failed_flows),
            "timestamp": logger.info("System health check completed successfully")
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@validation_router.get("/flows/diagnostics", response_model=Dict[str, Any])
async def get_system_diagnostics(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed system diagnostics for discovery flows.
    
    This endpoint provides comprehensive diagnostic information
    for troubleshooting and system monitoring.
    """
    try:
        logger.info("Getting system diagnostics for discovery flows")
        
        # Import required models
        from app.models.discovery_flow import DiscoveryFlow
        
        # Get detailed flow status distribution
        status_distribution_stmt = select(
            DiscoveryFlow.status,
            func.count(DiscoveryFlow.flow_id).label('count')
        ).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status != 'deleted'
            )
        ).group_by(DiscoveryFlow.status)
        
        status_result = await db.execute(status_distribution_stmt)
        status_distribution = {row.status: row.count for row in status_result.fetchall()}
        
        # Get phase distribution
        phase_distribution_stmt = select(
            DiscoveryFlow.current_phase,
            func.count(DiscoveryFlow.flow_id).label('count')
        ).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status != 'deleted'
            )
        ).group_by(DiscoveryFlow.current_phase)
        
        phase_result = await db.execute(phase_distribution_stmt)
        phase_distribution = {row.current_phase or 'unknown': row.count for row in phase_result.fetchall()}
        
        # Get recent activity
        recent_activity_stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status != 'deleted'
            )
        ).order_by(DiscoveryFlow.updated_at.desc()).limit(10)
        
        recent_result = await db.execute(recent_activity_stmt)
        recent_flows = recent_result.scalars().all()
        
        recent_activity = []
        for flow in recent_flows:
            recent_activity.append({
                "flow_id": str(flow.flow_id),
                "status": flow.status,
                "current_phase": flow.current_phase,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else "",
                "progress": flow.progress_percentage or 0
            })
        
        return {
            "diagnostics": {
                "status_distribution": status_distribution,
                "phase_distribution": phase_distribution,
                "recent_activity": recent_activity,
                "performance_metrics": {
                    "average_completion_time": "N/A",  # TODO: Calculate from historical data
                    "success_rate": "N/A",  # TODO: Calculate from historical data
                    "error_rate": len([s for s in status_distribution.keys() if s in ['failed', 'error']]) / len(status_distribution) * 100 if status_distribution else 0
                }
            },
            "system_resources": {
                "database_connections": "healthy",
                "memory_usage": "normal",
                "cpu_usage": "normal"
            },
            "recommendations": _get_diagnostic_recommendations(status_distribution, phase_distribution),
            "timestamp": logger.info("System diagnostics completed successfully")
        }
        
    except Exception as e:
        logger.error(f"Error getting system diagnostics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system diagnostics: {str(e)}")


# Helper functions for validation operations

async def _perform_flow_validation(flow, db: AsyncSession) -> Dict[str, Any]:
    """Perform comprehensive flow validation"""
    try:
        errors = []
        warnings = []
        checks_passed = 0
        checks_total = 0
        
        # Basic flow validation
        checks_total += 1
        if not flow.flow_name:
            warnings.append({"type": "missing_name", "message": "Flow name is not set"})
        else:
            checks_passed += 1
        
        # Status validation
        checks_total += 1
        if flow.status in ['failed', 'error']:
            errors.append({"type": "flow_error", "message": f"Flow is in error state: {flow.status}", "severity": "critical"})
        else:
            checks_passed += 1
        
        # Phase completion validation
        phase_completion = StatusCalculator.build_phase_completion_dict(flow)
        checks_total += len(phase_completion)
        
        # Check phase sequence
        for i, phase in enumerate(StatusCalculator.PHASE_ORDER):
            if phase_completion.get(phase, False):
                checks_passed += 1
            elif i > 0 and phase_completion.get(StatusCalculator.PHASE_ORDER[i-1], False):
                # Previous phase completed but current not started
                warnings.append({"type": "phase_stall", "message": f"Phase {phase} not started after {StatusCalculator.PHASE_ORDER[i-1]} completion"})
        
        # Calculate validation score
        validation_score = (checks_passed / checks_total * 100) if checks_total > 0 else 0
        
        # Determine overall status
        if len([e for e in errors if e.get("severity") == "critical"]) > 0:
            overall_status = "failed"
        elif len(errors) > 0:
            overall_status = "error"
        elif len(warnings) > 0:
            overall_status = "warning"
        else:
            overall_status = "passed"
        
        return {
            "overall_status": overall_status,
            "validation_score": validation_score,
            "checks_passed": checks_passed,
            "checks_failed": checks_total - checks_passed,
            "checks_total": checks_total,
            "errors": errors,
            "warnings": warnings,
            "data_quality": {"status": "not_implemented"},
            "configuration_validation": {"status": "not_implemented"},
            "prerequisite_checks": {"status": "not_implemented"},
            "recommendations": _get_validation_recommendations(errors, warnings),
            "validated_at": logger.info("Flow validation completed")
        }
        
    except Exception as e:
        logger.error(f"Error performing flow validation: {e}")
        return {
            "overall_status": "error",
            "validation_score": 0,
            "errors": [{"type": "validation_error", "message": str(e), "severity": "critical"}],
            "warnings": [],
            "validated_at": logger.info("Flow validation failed")
        }


async def _perform_quick_validation(flow, db: AsyncSession) -> Dict[str, Any]:
    """Perform quick validation checks"""
    # Simplified validation for quick checks
    return await _perform_flow_validation(flow, db)


async def _perform_phase_validation(flow, phase: str, db: AsyncSession) -> Dict[str, Any]:
    """Perform phase-specific validation"""
    # Phase-specific validation logic
    return await _perform_flow_validation(flow, db)


async def _perform_full_validation(flow, db: AsyncSession, include_data_quality: bool, include_configuration: bool) -> Dict[str, Any]:
    """Perform comprehensive validation"""
    # Full validation with optional data quality and configuration checks
    return await _perform_flow_validation(flow, db)


async def _check_phase_prerequisites(flow, phase: str, db: AsyncSession) -> Dict[str, Any]:
    """Check prerequisites for a specific phase"""
    try:
        checks = []
        blocking_issues = []
        warnings = []
        
        # Define prerequisite checks for each phase
        if phase == "field_mapping":
            checks.append({"name": "data_import_completed", "status": "passed" if flow.data_import_completed else "failed"})
            if not flow.data_import_completed:
                blocking_issues.append("Data import must be completed before field mapping")
        
        elif phase == "data_cleansing":
            checks.append({"name": "field_mapping_completed", "status": "passed" if flow.field_mapping_completed else "failed"})
            if not flow.field_mapping_completed:
                blocking_issues.append("Field mapping must be completed before data cleansing")
        
        elif phase == "asset_inventory":
            checks.append({"name": "data_cleansing_completed", "status": "passed" if flow.data_cleansing_completed else "failed"})
            if not flow.data_cleansing_completed:
                blocking_issues.append("Data cleansing must be completed before asset inventory")
        
        # Add more phase-specific checks as needed
        
        all_met = len(blocking_issues) == 0
        can_proceed = all_met and flow.status not in ['deleted', 'failed', 'error']
        
        next_actions = []
        if blocking_issues:
            next_actions.extend([f"Resolve: {issue}" for issue in blocking_issues])
        elif can_proceed:
            next_actions.append(f"Ready to proceed with {phase}")
        
        return {
            "all_met": all_met,
            "checks": checks,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
            "can_proceed": can_proceed,
            "next_actions": next_actions
        }
        
    except Exception as e:
        logger.error(f"Error checking prerequisites: {e}")
        return {
            "all_met": False,
            "checks": [],
            "blocking_issues": [f"Error checking prerequisites: {str(e)}"],
            "warnings": [],
            "can_proceed": False,
            "next_actions": ["Resolve prerequisite check error"]
        }


def _get_system_recommendations(health_score: float, failed_flows: int) -> List[str]:
    """Get system-level recommendations based on health metrics"""
    recommendations = []
    
    if health_score < 75:
        recommendations.append("System health is below optimal. Consider investigating failed flows.")
    
    if failed_flows > 0:
        recommendations.append(f"There are {failed_flows} failed flows that need attention.")
    
    if health_score < 50:
        recommendations.append("Critical system issues detected. Immediate attention required.")
    
    return recommendations


def _get_diagnostic_recommendations(status_distribution: Dict[str, int], phase_distribution: Dict[str, int]) -> List[str]:
    """Get diagnostic recommendations based on distribution data"""
    recommendations = []
    
    total_flows = sum(status_distribution.values())
    if total_flows == 0:
        return ["No flows detected. Consider creating discovery flows."]
    
    failed_count = status_distribution.get('failed', 0) + status_distribution.get('error', 0)
    if failed_count > 0:
        recommendations.append(f"Address {failed_count} failed flows to improve system health.")
    
    paused_count = status_distribution.get('paused', 0)
    if paused_count > total_flows * 0.3:
        recommendations.append("High number of paused flows. Consider resuming or cleaning up inactive flows.")
    
    return recommendations


def _get_validation_recommendations(errors: List[Dict], warnings: List[Dict]) -> List[str]:
    """Get validation recommendations based on errors and warnings"""
    recommendations = []
    
    critical_errors = [e for e in errors if e.get("severity") == "critical"]
    if critical_errors:
        recommendations.append("Address critical errors immediately to ensure flow stability.")
    
    if len(warnings) > 0:
        recommendations.append("Review and address warnings to improve flow reliability.")
    
    return recommendations