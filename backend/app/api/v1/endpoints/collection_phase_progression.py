"""
Collection Phase Progression API Endpoints

Provides endpoints to fix stuck collection flows by manually triggering
phase progression when automatic mechanisms fail.
"""

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, get_request_context
from app.core.context import RequestContext
from app.models.user import User
from app.services.collection_phase_progression_service import (
    CollectionPhaseProgressionService,
)

logger = logging.getLogger(__name__)


async def fix_stuck_collection_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """Fix collection flows stuck in platform_detection phase.

    This endpoint identifies collection flows that have completed platform detection
    but are stuck waiting for the next phase to be triggered. It automatically
    advances them to the automated_collection phase.

    Returns:
        Dictionary with results of the phase progression operation
    """
    try:
        logger.info(
            f"Starting stuck collection flows fix for engagement {context.engagement_id}"
        )

        # Initialize the phase progression service
        progression_service = CollectionPhaseProgressionService(db, context)

        # Process all stuck flows
        results = await progression_service.process_stuck_flows()

        # Commit changes if any flows were advanced
        if results.get("flows_advanced", 0) > 0:
            await db.commit()
            logger.info(
                f"Committed changes for {results['flows_advanced']} advanced flows"
            )

        return {
            "status": "success",
            "message": (
                f"Phase progression complete: {results.get('flows_advanced', 0)} flows advanced, "
                f"{results.get('flows_skipped', 0)} skipped, {results.get('flows_failed', 0)} failed"
            ),
            "results": results,
            "user_id": str(current_user.id),
            "engagement_id": str(context.engagement_id),
        }

    except Exception as e:
        logger.error(f"Error fixing stuck collection flows: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to fix stuck collection flows: {str(e)}"
        )


async def advance_collection_flow_phase(
    flow_id: str,
    target_phase: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """Advance a specific collection flow to a target phase.

    Args:
        flow_id: ID of the collection flow to advance
        target_phase: Target phase to advance to (e.g., 'automated_collection', 'gap_analysis')
        force: Force advancement even if prerequisites aren't met

    Returns:
        Dictionary with the advancement result
    """
    try:
        logger.info(f"Advancing collection flow {flow_id} to phase {target_phase}")

        # Validate target phase
        valid_phases = [
            "automated_collection",
            "gap_analysis",
            "questionnaire_generation",
            "manual_collection",
            "data_validation",
            "finalization",
        ]

        if target_phase not in valid_phases:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target phase. Must be one of: {', '.join(valid_phases)}",
            )

        # Initialize the phase progression service
        progression_service = CollectionPhaseProgressionService(db, context)

        # Advance the specific flow
        result = await progression_service.advance_specific_flow(flow_id, target_phase)

        if result["status"] == "success":
            await db.commit()
            logger.info(f"Successfully advanced flow {flow_id} to {target_phase}")
        else:
            await db.rollback()

        return {
            "status": result["status"],
            "message": (
                f"Flow advancement {'successful' if result['status'] == 'success' else 'failed'}"
            ),
            "flow_id": flow_id,
            "target_phase": target_phase,
            "result": result,
            "user_id": str(current_user.id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error advancing collection flow {flow_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to advance collection flow: {str(e)}"
        )


async def get_stuck_collection_flows_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """Get analysis of collection flows that might be stuck.

    This is a read-only endpoint that identifies potentially stuck flows
    without making any changes.

    Returns:
        Dictionary with analysis of potentially stuck flows
    """
    try:
        logger.info(
            f"Analyzing stuck collection flows for engagement {context.engagement_id}"
        )

        # Initialize the phase progression service
        progression_service = CollectionPhaseProgressionService(db, context)

        # Find stuck flows
        stuck_flows = await progression_service.find_stuck_flows()

        # Analyze each flow
        analysis_results = []
        for flow in stuck_flows:
            platform_complete = (
                await progression_service.check_platform_detection_complete(flow)
            )

            analysis_results.append(
                {
                    "flow_id": str(flow.flow_id),
                    "flow_name": flow.flow_name,
                    "current_phase": flow.current_phase,
                    "status": flow.status,
                    "created_at": (
                        flow.created_at.isoformat() if flow.created_at else None
                    ),
                    "updated_at": (
                        flow.updated_at.isoformat() if flow.updated_at else None
                    ),
                    "master_flow_id": (
                        str(flow.master_flow_id) if flow.master_flow_id else None
                    ),
                    "platform_detection_complete": platform_complete,
                    "can_advance": platform_complete,
                    "recommended_action": (
                        "advance_to_automated_collection"
                        if platform_complete
                        else "wait_for_platform_detection"
                    ),
                }
            )

        return {
            "status": "success",
            "total_flows_analyzed": len(stuck_flows),
            "stuck_flows": len(
                [f for f in analysis_results if f["platform_detection_complete"]]
            ),
            "pending_flows": len(
                [f for f in analysis_results if not f["platform_detection_complete"]]
            ),
            "analysis": analysis_results,
            "engagement_id": str(context.engagement_id),
        }

    except Exception as e:
        logger.error(f"Error analyzing stuck collection flows: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze stuck collection flows: {str(e)}",
        )
