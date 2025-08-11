"""
Force Re-run Phase Endpoint for Unified Discovery Flow

This endpoint allows forcing a specific phase to re-run with existing data.
Solves the issue where flows get stuck and "Trigger Analysis" doesn't help.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.core.logging import safe_log_format
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.crewai_flows.unified_discovery_flow.field_mapping_executor import (
    FieldMappingExecutor,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ForceRerunRequest(BaseModel):
    """Request model for forcing phase re-run"""

    phase: str  # e.g., "field_mapping", "data_cleansing", etc.
    force: bool = True
    use_existing_data: bool = True
    reason: Optional[str] = None


@router.post("/flow/{flow_id}/force-rerun-phase")
async def force_rerun_phase(
    flow_id: str,
    request: ForceRerunRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Force re-run a specific phase of the discovery flow.

    This is the fix for the issue where flows get stuck and the UI shows
    raw data but no field mappings, and "Trigger Analysis" doesn't help.
    """
    try:
        logger.info(
            safe_log_format(
                "🔄 Force re-running phase {phase} for flow {flow_id}",
                phase=request.phase,
                flow_id=flow_id,
            )
        )

        # Get the master flow orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        # Get the current flow state
        flow_status = await orchestrator.get_flow_status(flow_id)
        if not flow_status or flow_status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Flow not found")

        # Extract the flow persistence data
        flow_data = flow_status.get("persistence_data", {})
        raw_data = flow_data.get("raw_data")

        # Check if we have the necessary data
        if request.phase == "field_mapping":
            if not raw_data:
                # Try to get raw data from the data import
                from app.models.data_import import DataImport, RawImportRecord
                from sqlalchemy import select

                # Find data import linked to this flow
                data_import_query = select(DataImport).where(
                    DataImport.master_flow_id == flow_id
                )
                result = await db.execute(data_import_query)
                data_import = result.scalar_one_or_none()

                if data_import:
                    # Get raw records
                    raw_records_query = select(RawImportRecord.raw_data).where(
                        RawImportRecord.data_import_id == data_import.id
                    )
                    raw_result = await db.execute(raw_records_query)
                    raw_records = raw_result.scalars().all()

                    if raw_records:
                        raw_data = raw_records
                        logger.info(
                            f"✅ Found {len(raw_data)} raw records from data import"
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="No raw data available to run field mapping",
                        )
                else:
                    raise HTTPException(
                        status_code=400, detail="No data import found for this flow"
                    )

            # Now force run the field mapping phase
            logger.info("🎯 Force running field mapping phase with existing data")

            # Create a minimal flow state with the raw data
            from app.services.crewai_flows.unified_discovery_flow.base_flow import (
                UnifiedDiscoveryFlowState,
            )
            from app.services.crewai_flow_service import CrewAIFlowService
            from app.services.crewai_flows.crews.crew_manager import CrewManager

            # Initialize the state with raw data
            state = UnifiedDiscoveryFlowState(
                flow_id=flow_id,
                client_account_id=str(context.client_account_id),
                engagement_id=str(context.engagement_id),
                user_id=context.user_id or "system",
                raw_data=raw_data,
                current_phase="field_mapping",
                status="running",
            )

            # Create the field mapping executor
            crewai_service = CrewAIFlowService()
            crew_manager = CrewManager(crewai_service)

            executor = FieldMappingExecutor(
                state=state,
                crew_manager=crew_manager,
                notification_utils=None,  # Not needed for force run
                state_manager=None,  # We'll update manually
            )

            # Execute the field mapping phase
            logger.info("🚀 Executing field mapping with CrewAI agents...")
            crew_input = executor._prepare_crew_input()

            # Force execution with crew
            result = await executor.execute_with_crew(crew_input)

            logger.info(f"✅ Field mapping completed: {result}")

            # Update the flow state with the results
            update_result = await orchestrator.update_flow_state(
                flow_id=flow_id,
                phase_data={"field_mappings": result},
                current_phase="field_mapping",
                phase_status="completed",
            )

            return {
                "success": True,
                "flow_id": flow_id,
                "phase": request.phase,
                "result": result,
                "message": f"Successfully force re-ran {request.phase} phase",
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Force re-run not implemented for phase: {request.phase}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Failed to force re-run phase: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to force re-run phase: {str(e)}"
        )
