"""
MFO Execute Phase Pattern Template

CRITICAL: Use this template for ANY endpoint that executes MFO phases.
This prevents the recurring master vs child flow ID bug.

Copy this file and replace:
- {FlowType} with AssessmentFlow, DiscoveryFlow, or CollectionFlow
- {phase_name} with actual phase name
- {flow_type_str} with "assessment", "discovery", or "collection"
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.{flow_type} import {FlowType}  # e.g., AssessmentFlow
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

router = APIRouter()


@router.post("/execute/{flow_id}")
async def execute_{phase_name}(
    flow_id: str,  # ← This is CHILD flow ID from URL
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Execute {phase_name} phase for {flow_type_str} flow.

    CRITICAL PATTERN:
    - flow_id in URL = child flow ID ({FlowType}.id)
    - MFO.execute_phase() expects MASTER flow ID
    - phase_input["flow_id"] = child flow ID for persistence

    Args:
        flow_id: Child flow UUID from URL path
        db: Database session
        context: Request context with tenant IDs

    Returns:
        Dict with success status, flow_id (child), and result

    Raises:
        HTTPException 404: Flow not found
        HTTPException 400: Flow not registered with MFO
        HTTPException 500: Execution error
    """
    try:
        # ============================================
        # STEP 1: Query child flow table using CHILD ID
        # ============================================
        stmt = select({FlowType}).where(
            and_(
                {FlowType}.id == UUID(flow_id),  # ← PRIMARY KEY (child ID)
                {FlowType}.client_account_id == context.client_account_id,
                {FlowType}.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        child_flow = result.scalar_one_or_none()

        # Validate flow exists
        if not child_flow:
            raise HTTPException(
                status_code=404,
                detail="{FlowType} flow not found"
            )

        # Validate MFO registration
        if not child_flow.master_flow_id:
            raise HTTPException(
                status_code=400,
                detail="Flow not properly registered with MFO"
            )

        # ============================================
        # STEP 2: Extract MASTER flow ID from child row
        # ============================================
        master_flow_id = child_flow.master_flow_id  # ← FK to master flow

        # ============================================
        # STEP 3: Call MFO with MASTER ID
        # ============================================
        orchestrator = MasterFlowOrchestrator(db, context)

        execution_result = await orchestrator.execute_phase(
            str(master_flow_id),  # ← MASTER flow ID (MFO routing)
            "{phase_name}",       # ← Phase name from config
            {
                # CRITICAL: Include CHILD flow ID for persistence!
                "flow_id": flow_id,  # ← PhaseResultsPersistence uses this

                # Optional: Add other phase-specific data
                "trigger": "manual",
                "source": "{flow_type_str}_ui",
                # "additional_context": {...}
            }
        )

        # ============================================
        # STEP 4: Return response with CHILD ID
        # ============================================
        return {
            "success": True,
            "flow_id": flow_id,  # ← Return child ID (user expects this)
            "master_flow_id": str(master_flow_id),  # ← For debugging
            "result": execution_result,
            "message": "{phase_name} execution started"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Log and convert other exceptions
        logger.error(f"Failed to execute {phase_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# VALIDATION CHECKLIST
# ============================================
# Before committing, verify:
# [ ] URL receives child flow ID (from user)
# [ ] Query uses {FlowType}.id (primary key, not flow_id)
# [ ] Extracted master_flow_id from child_flow.master_flow_id
# [ ] Passed master_flow_id to orchestrator.execute_phase()
# [ ] Included child flow_id in phase_input dict
# [ ] Returned child flow_id to user (not master_flow_id)
# [ ] Used get_current_context_dependency (not get_current_context)
# [ ] Added try/except for HTTPException passthrough


# ============================================
# EXAMPLE USAGE (for different flow types)
# ============================================

# Assessment Flow Example:
"""
from app.models.assessment_flow import AssessmentFlow

@router.post("/execute/{flow_id}")
async def execute_dependency_analysis(flow_id: str, db: AsyncSession, context: RequestContext):
    stmt = select(AssessmentFlow).where(
        AssessmentFlow.id == UUID(flow_id),
        AssessmentFlow.client_account_id == context.client_account_id,
        AssessmentFlow.engagement_id == context.engagement_id,
    )
    result = await db.execute(stmt)
    assessment_flow = result.scalar_one_or_none()

    if not assessment_flow or not assessment_flow.master_flow_id:
        raise HTTPException(status_code=404, detail="Assessment flow not found")

    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(assessment_flow.master_flow_id),  # Master ID
        "dependency_analysis",
        {"flow_id": flow_id}  # Child ID
    )

    return {"success": True, "flow_id": flow_id, "result": result}
"""

# Discovery Flow Example:
"""
from app.models.discovery_flow import DiscoveryFlow

@router.post("/execute/{flow_id}")
async def execute_asset_inventory(flow_id: str, db: AsyncSession, context: RequestContext):
    stmt = select(DiscoveryFlow).where(
        DiscoveryFlow.id == UUID(flow_id),
        DiscoveryFlow.client_account_id == context.client_account_id,
        DiscoveryFlow.engagement_id == context.engagement_id,
    )
    result = await db.execute(stmt)
    discovery_flow = result.scalar_one_or_none()

    if not discovery_flow or not discovery_flow.master_flow_id:
        raise HTTPException(status_code=404, detail="Discovery flow not found")

    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(discovery_flow.master_flow_id),  # Master ID
        "asset_inventory",
        {"flow_id": flow_id}  # Child ID
    )

    return {"success": True, "flow_id": flow_id, "result": result}
"""

# Collection Flow Example:
"""
from app.models.collection_flow import CollectionFlow

@router.post("/execute/{flow_id}")
async def execute_gap_analysis(flow_id: str, db: AsyncSession, context: RequestContext):
    stmt = select(CollectionFlow).where(
        CollectionFlow.id == UUID(flow_id),
        CollectionFlow.client_account_id == context.client_account_id,
        CollectionFlow.engagement_id == context.engagement_id,
    )
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if not collection_flow or not collection_flow.master_flow_id:
        raise HTTPException(status_code=404, detail="Collection flow not found")

    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(collection_flow.master_flow_id),  # Master ID
        "gap_analysis",
        {"flow_id": flow_id}  # Child ID
    )

    return {"success": True, "flow_id": flow_id, "result": result}
"""
