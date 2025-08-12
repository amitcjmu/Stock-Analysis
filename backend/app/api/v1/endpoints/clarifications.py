"""
Clarifications API Endpoints

This module contains all clarification submission related endpoints,
extracted from unified_discovery.py for better modularity.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


class ClarificationSubmission(BaseModel):
    """Model for clarification submission"""

    clarifications: List[Dict[str, Any]]
    phase: str = "clarification"


@router.post("/flows/{flow_id}/clarifications/submit")
async def submit_clarifications(
    flow_id: str,
    submission: ClarificationSubmission,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Submit clarifications for a discovery flow."""
    try:
        logger.info(
            safe_log_format(
                "Submitting clarifications for flow: {flow_id}",
                flow_id=flow_id,
            )
        )

        # Verify flow exists and belongs to the current context
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Submit clarifications through the Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        # Execute the clarification phase with the submitted data
        result = await orchestrator.execute_phase(
            flow_id,
            submission.phase,
            {"clarifications": submission.clarifications},
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "message": "Clarifications submitted successfully",
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to submit clarifications: {e}",
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
