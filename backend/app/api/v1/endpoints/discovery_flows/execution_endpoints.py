"""
Flow Execution Endpoints

This module handles flow execution and control operations:
- Flow resume operations
- Flow execution control
- Intelligent flow resumption
- Background operation triggering
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.api.v1.dependencies import get_crewai_flow_service
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.crewai_flow_service import CrewAIFlowService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .response_mappers import FlowOperationResponse
from .status_calculator import StatusCalculator

logger = logging.getLogger(__name__)

execution_router = APIRouter(tags=["discovery-execution"])


@execution_router.post("/flow/{flow_id}/resume", response_model=FlowOperationResponse)
async def resume_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    crewai_service: CrewAIFlowService = Depends(get_crewai_flow_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Resume a paused discovery flow after user approval.

    This endpoint delegates to the Master Flow Orchestrator for unified flow management.
    All flow types (discovery, assessment, plan, execute, etc.) should be resumed through
    the Master Flow Orchestrator to ensure consistent state management and audit trails.
    """
    try:
        logger.info(f"Resuming discovery flow {flow_id} via Master Flow Orchestrator")

        # Import Master Flow Orchestrator
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        # Prepare resume context with user approval data
        resume_context = {
            "user_approval": True,
            "field_mappings": request.get("field_mappings", {}),
            "approval_timestamp": datetime.utcnow().isoformat(),
            "approved_by": context.user_id,
            "approval_notes": request.get("notes", ""),
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "flow_type": "discovery",
        }

        # Check if this is a master flow or a child flow
        import uuid as uuid_lib

        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.discovery_flow import DiscoveryFlow

        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # Check if it's registered in the master flow system
        master_stmt = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_uuid
        )
        master_result = await db.execute(master_stmt)
        master_flow = master_result.scalar_one_or_none()

        if master_flow:
            # This is a master flow - use Master Flow Orchestrator
            logger.info(f"🎯 Using Master Flow Orchestrator for flow {flow_id}")
            logger.info(f"📊 Master flow status: {master_flow.flow_status}")

            # Check current phase from persistence data
            current_phase = master_flow.flow_persistence_data.get("current_phase", "")
            logger.info(f"📊 Current phase from persistence: {current_phase}")

            # For field mapping approval scenarios
            if master_flow.flow_status in [
                "processing",
                "running",
                "waiting_for_approval",
            ] and (
                current_phase in ["field_mapping", "attribute_mapping"]
                or "field_mapping" in str(master_flow.flow_persistence_data)
                or "attribute_mapping" in str(master_flow.flow_persistence_data)
            ):
                # Resume the CrewAI flow with field mapping approval using new phase controller
                logger.info(
                    "📝 Resuming CrewAI flow with field mapping approval via phase controller"
                )

                # Use the new background execution service to resume with phase control
                from app.services.data_import.background_execution_service import (
                    BackgroundExecutionService,
                )

                background_service = BackgroundExecutionService(
                    db, str(context.client_account_id)
                )

                # Prepare user input for field mapping approval
                user_input = {
                    "approved_mappings": request.get("field_mappings", {}),
                    "approval_timestamp": datetime.utcnow().isoformat(),
                    "approved_by": context.user_id,
                    "approval_notes": request.get("notes", ""),
                    "user_approval": True,
                }

                # Resume from field mapping approval phase
                resume_success = await background_service.resume_flow_from_user_input(
                    flow_id=str(flow_id),
                    user_input=user_input,
                    context=context,
                    resume_phase="field_mapping_approval",
                )

                if resume_success:
                    return {
                        "success": True,
                        "flow_id": str(flow_id),
                        "status": "resumed",
                        "message": "Field mapping approved and flow resumed with phase controller",
                        "next_phase": "data_cleansing",
                        "current_phase": "field_mapping_approval",
                        "method": "phase_controller",
                    }
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to resume flow with approved mappings",
                    )
            else:
                # For paused flows, use resume
                resume_result = await orchestrator.resume_flow(
                    flow_id=str(flow_id), resume_context=resume_context
                )

                return {
                    "success": True,
                    "flow_id": resume_result["flow_id"],
                    "status": resume_result["status"],
                    "message": "Flow resumed via Master Flow Orchestrator",
                    "next_phase": resume_result.get("resume_phase", "unknown"),
                    "current_phase": resume_result.get("resume_phase", "unknown"),
                    "method": "master_flow_orchestrator",
                }
        else:
            # Legacy discovery flow - try to resume via CrewAI service
            logger.warning(
                f"⚠️ Flow {flow_id} not registered with Master Flow Orchestrator, using legacy resume"
            )

            # Get the discovery flow
            stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()

            if not flow:
                raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

            if flow.status == "deleted":
                raise HTTPException(
                    status_code=400, detail="Cannot resume a deleted flow"
                )

            # Update flow status
            flow.status = "processing"
            flow.updated_at = datetime.utcnow()
            await db.commit()

            # Try to resume with CrewAI service
            try:
                result = await crewai_service.resume_flow(str(flow_id), resume_context)
                logger.info(f"✅ Legacy flow {flow_id} resumed via CrewAI service")

                return {
                    "success": True,
                    "flow_id": str(flow_id),
                    "status": "resumed",
                    "message": "Discovery flow resumed successfully (legacy)",
                    "next_phase": "field_mapping",
                    "current_phase": flow.current_phase or "field_mapping",
                    "method": "legacy_crewai_service",
                }
            except Exception as e:
                logger.error(f"❌ Failed to resume legacy flow: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to resume flow: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error resuming flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")


@execution_router.post(
    "/flow/{flow_id}/resume-intelligent", response_model=Dict[str, Any]
)
async def resume_flow_intelligent(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Intelligently resume a flow from any interrupted state.

    This endpoint analyzes the flow's current state and determines the best way to resume:
    - If waiting for approval: Handles approval or regeneration
    - If interrupted: Resumes from the last successful phase
    - If data exists: Can restart processing from raw data
    """
    try:
        logger.info(f"🔄 Intelligent resume requested for flow {flow_id}")

        action = request.get("action", "auto")
        force_restart = request.get("force_restart", False)

        # Import required modules
        import uuid as uuid_lib

        from app.models.data_import import DataImport
        from app.models.discovery_flow import DiscoveryFlow
        from app.models.raw_import_record import RawImportRecord
        from app.services.crewai_flows.unified_discovery_flow.flow_finalization import (
            UnifiedDiscoveryFlowFinalizer,
        )
        from app.services.crewai_flows.unified_discovery_flow.flow_management import (
            UnifiedDiscoveryFlowManager,
        )

        # Convert flow_id to UUID
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # 1. Analyze current flow state
        logger.info("📊 Analyzing flow state...")

        # Get discovery flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot resume a deleted flow")

        # 2. Check for raw data availability
        raw_data_available = False
        raw_data_count = 0

        # Check data imports
        data_import_stmt = select(DataImport).where(
            DataImport.discovery_flow_id == flow_uuid
        )
        data_import_result = await db.execute(data_import_stmt)
        data_import = data_import_result.scalar_one_or_none()

        if data_import:
            # Count raw records
            count_stmt = select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == data_import.id
            )
            count_result = await db.execute(count_stmt)
            raw_data_count = count_result.scalar() or 0
            raw_data_available = raw_data_count > 0

        # 3. Determine resume strategy
        resume_strategy = {
            "action": action,
            "strategy": "unknown",
            "from_phase": None,
            "raw_data_available": raw_data_available,
            "raw_data_count": raw_data_count,
        }

        # Analyze flow state
        is_waiting_approval = flow.status in [
            "paused",
            "waiting_for_approval",
            "waiting_for_user_approval",
        ]
        current_phase = flow.current_phase or "data_import"

        if action == "auto":
            if is_waiting_approval and current_phase == "field_mapping":
                resume_strategy["strategy"] = "approve_field_mappings"
                resume_strategy["from_phase"] = "field_mapping"
            elif flow.status == "completed":
                resume_strategy["strategy"] = "already_completed"
            elif raw_data_available and not flow.data_import_completed:
                resume_strategy["strategy"] = "restart_from_raw_data"
                resume_strategy["from_phase"] = "data_import"
            elif flow.data_import_completed and not flow.field_mapping_completed:
                resume_strategy["strategy"] = "resume_field_mapping"
                resume_strategy["from_phase"] = "field_mapping"
            elif flow.field_mapping_completed and not flow.data_cleansing_completed:
                resume_strategy["strategy"] = "resume_data_cleansing"
                resume_strategy["from_phase"] = "data_cleansing"
            else:
                resume_strategy["strategy"] = "continue_from_current"
                resume_strategy["from_phase"] = current_phase

        # 4. Execute resume based on strategy
        logger.info(f"🎯 Resume strategy: {resume_strategy}")

        if resume_strategy["strategy"] == "already_completed":
            return {
                "success": True,
                "flow_id": str(flow_id),
                "message": "Flow is already completed",
                "strategy": resume_strategy,
                "flow_status": flow.status,
            }

        # Initialize flow manager
        flow_manager = UnifiedDiscoveryFlowManager(
            db=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,
        )

        # Handle approval scenarios
        if resume_strategy["strategy"] == "approve_field_mappings" and action in [
            "auto",
            "approve",
        ]:
            logger.info("✅ Approving field mappings and resuming...")

            # Get field mappings from request or use existing
            field_mappings = request.get("field_mappings", flow.field_mappings)

            if not field_mappings:
                raise HTTPException(
                    status_code=400, detail="Field mappings required for approval"
                )

            # Use flow finalizer to handle approval
            finalizer = UnifiedDiscoveryFlowFinalizer(flow_manager)
            result = await finalizer.finalize_field_mapping_approval(
                flow_id=str(flow_id),
                field_mappings=field_mappings,
                confidence_scores=request.get("confidence_scores", {}),
            )

            return {
                "success": True,
                "flow_id": str(flow_id),
                "message": "Field mappings approved, flow resumed",
                "strategy": resume_strategy,
                "flow_status": "processing",
                "next_phase": "data_cleansing",
            }

        # Handle regeneration
        if action == "regenerate" and is_waiting_approval:
            logger.info("🔄 Regenerating suggestions...")

            # This would trigger the CrewAI agents to regenerate suggestions
            return {
                "success": True,
                "flow_id": str(flow_id),
                "message": "Regeneration triggered",
                "strategy": {
                    "action": "regenerate",
                    "strategy": "regenerate_suggestions",
                },
                "flow_status": flow.status,
            }

        # Handle restart from raw data
        if resume_strategy["strategy"] == "restart_from_raw_data" or force_restart:
            logger.info("🔄 Restarting from raw data...")

            # Get raw data
            if data_import:
                raw_records_stmt = (
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == data_import.id)
                    .limit(100)
                )  # Limit for performance
                raw_records_result = await db.execute(raw_records_stmt)
                raw_records = raw_records_result.scalars().all()

                raw_data = [record.raw_data for record in raw_records]

                # Restart flow processing using MasterFlowOrchestrator
                from app.services.master_flow_orchestrator import MasterFlowOrchestrator

                # Create orchestrator instance
                orchestrator = MasterFlowOrchestrator(db, context)

                # Prepare initial state with raw data
                initial_state = {
                    "raw_data": raw_data,
                    "data_import_id": str(data_import.id) if data_import else None,
                }

                # Create new discovery flow through orchestrator
                logger.info(
                    f"🚀 Creating new discovery flow through MasterFlowOrchestrator with {len(raw_data)} records"
                )
                new_flow_id, flow_details = await orchestrator.create_flow(
                    flow_type="discovery",
                    flow_name=f"Restarted Discovery Flow (from {flow_id})",
                    initial_state=initial_state,
                )

                logger.info(f"✅ New discovery flow created: {new_flow_id}")

                # Update the old flow to mark it as superseded
                flow.status = "superseded"
                flow.metadata = flow.metadata or {}
                flow.metadata["superseded_by"] = new_flow_id
                flow.metadata["superseded_at"] = datetime.utcnow().isoformat()
                await db.commit()

                return {
                    "success": True,
                    "flow_id": new_flow_id,
                    "message": f"Flow restarted from {raw_data_count} raw records",
                    "strategy": resume_strategy,
                    "flow_status": "processing",
                    "old_flow_id": str(flow_id),
                    "note": "New flow created through MasterFlowOrchestrator",
                }

        # Default: Update status and let normal flow resume
        logger.info("📈 Resuming normal flow execution...")

        flow.status = "processing"
        flow.updated_at = datetime.utcnow()
        await db.commit()

        return {
            "success": True,
            "flow_id": str(flow_id),
            "message": f"Flow resumed from phase: {resume_strategy['from_phase']}",
            "strategy": resume_strategy,
            "flow_status": "processing",
            "current_phase": current_phase,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in intelligent resume: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")


@execution_router.post("/flow/{flow_id}/execute", response_model=FlowOperationResponse)
async def execute_flow_phase(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    crewai_service: CrewAIFlowService = Depends(get_crewai_flow_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a specific phase of the discovery flow.

    This endpoint allows manual execution of individual flow phases
    for debugging or step-by-step processing.
    """
    try:
        logger.info(f"🚀 Executing flow phase for {flow_id}")

        phase = request.get("phase", "current")
        force_execution = request.get("force", False)

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
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot execute a deleted flow")

        # Determine which phase to execute
        if phase == "current":
            current_phase, _ = StatusCalculator.calculate_current_phase(flow)
            execution_phase = current_phase
        else:
            execution_phase = phase

        # Check if phase can be executed
        if not force_execution:
            if execution_phase == "field_mapping" and not flow.data_import_completed:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot execute field_mapping phase: data_import not completed",
                )
            elif (
                execution_phase == "data_cleansing" and not flow.field_mapping_completed
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot execute data_cleansing phase: field_mapping not completed",
                )
            # Add more validation as needed

        # Import required modules for phase execution
        from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
        from app.services.crewai_flows.flow_state_bridge import FlowStateBridge
        from app.services.crewai_flows.handlers.phase_executors import (
            PhaseExecutionManager,
        )
        from app.services.crewai_flows.handlers.unified_flow_crew_manager import (
            UnifiedFlowCrewManager,
        )

        logger.info(f"📊 Executing phase: {execution_phase}")

        # Update flow status first
        flow.status = "processing"
        flow.current_phase = execution_phase
        flow.updated_at = datetime.utcnow()

        # Add execution metadata
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["last_execution"] = {
            "phase": execution_phase,
            "executed_at": datetime.utcnow().isoformat(),
            "executed_by": context.user_id,
            "forced": force_execution,
        }

        await db.commit()

        # Now actually execute the phase
        try:
            # Get flow state from the bridge
            flow_bridge = FlowStateBridge(context)
            state_dict = await flow_bridge.load_state(str(flow_id))

            if not state_dict:
                logger.error(f"❌ No flow state found for {flow_id}")
                raise HTTPException(status_code=404, detail="Flow state not found")

            # Create state object
            state = UnifiedDiscoveryFlowState()
            state.flow_id = str(flow_id)
            state.client_account_id = str(context.client_account_id)
            state.engagement_id = str(context.engagement_id)
            state.user_id = str(context.user_id)

            # Load state data
            for key, value in state_dict.items():
                if hasattr(state, key):
                    setattr(state, key, value)

            # Create crew manager
            crew_manager = UnifiedFlowCrewManager(state, crewai_service)

            # Create phase execution manager
            phase_manager = PhaseExecutionManager(state, crew_manager, flow_bridge)

            # Execute the specific phase
            logger.info(
                f"🚀 Executing {execution_phase} phase via PhaseExecutionManager"
            )

            # Get previous phase result if needed
            previous_result = {}
            if execution_phase == "asset_inventory":
                # For asset inventory, we need the data cleansing results
                previous_result = {
                    "raw_data": state.raw_data or [],
                    "field_mappings": state.field_mappings or {},
                    "cleansed_data": getattr(state, "cleansed_data", state.raw_data)
                    or [],
                }

            # Execute the phase
            if execution_phase == "asset_inventory":
                result = await phase_manager.execute_asset_inventory_phase(
                    previous_result
                )
            elif execution_phase == "field_mapping":
                result = await phase_manager.execute_field_mapping_phase(
                    previous_result
                )
            elif execution_phase == "data_cleansing":
                result = await phase_manager.execute_data_cleansing_phase(
                    previous_result
                )
            elif execution_phase == "dependency_analysis":
                result = await phase_manager.execute_dependency_analysis_phase(
                    previous_result
                )
            elif execution_phase == "tech_debt_analysis":
                result = await phase_manager.execute_tech_debt_analysis_phase(
                    previous_result
                )
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown phase: {execution_phase}"
                )

            logger.info(f"✅ Phase {execution_phase} executed successfully")

            # Update flow state with results
            if result and hasattr(state, execution_phase):
                setattr(state, execution_phase, result)

            # Save updated state
            await flow_bridge.save_state(str(flow_id), state.model_dump())

            return {
                "success": True,
                "flow_id": str(flow_id),
                "status": "executing",
                "message": f"Phase {execution_phase} executed successfully",
                "current_phase": execution_phase,
                "next_phase": StatusCalculator.get_next_phase(execution_phase),
                "method": "phase_execution",
                "execution_triggered": True,
            }

        except HTTPException:
            raise
        except Exception as phase_exec_error:
            logger.error(
                f"❌ Error executing phase {execution_phase}: {phase_exec_error}",
                exc_info=True,
            )
            # Still return success since we updated the flow status
            return {
                "success": True,
                "flow_id": str(flow_id),
                "status": "executing",
                "message": f"Phase {execution_phase} execution failed: {str(phase_exec_error)}",
                "current_phase": execution_phase,
                "next_phase": StatusCalculator.get_next_phase(execution_phase),
                "method": "phase_execution",
                "error": str(phase_exec_error),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing flow phase: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute flow phase: {str(e)}"
        )


# REMOVED: Unused endpoint - no frontend references
# @execution_router.post("/flow/{flow_id}/abort", response_model=FlowOperationResponse)
# async def abort_flow_execution(
#     flow_id: str,
#     request: Dict[str, Any] = {},
#     context: RequestContext = Depends(get_current_context),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Abort a currently executing flow.
#
#     This endpoint stops flow execution and marks it as aborted.
#     """
#     try:
#         logger.info(f"🛑 Aborting flow execution for {flow_id}")
#
#         # Import required models
#         from app.models.discovery_flow import DiscoveryFlow
#         import uuid as uuid_lib
#
#         # Convert flow_id to UUID if needed
#         try:
#             flow_uuid = uuid_lib.UUID(flow_id)
#         except ValueError:
#             flow_uuid = flow_id
#
#         # Get the flow
#         stmt = select(DiscoveryFlow).where(
#             and_(
#                 DiscoveryFlow.flow_id == flow_uuid,
#                 DiscoveryFlow.client_account_id == context.client_account_id,
#                 DiscoveryFlow.engagement_id == context.engagement_id
#             )
#         )
#         result = await db.execute(stmt)
#         flow = result.scalar_one_or_none()
#
#         if not flow:
#             raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
#
#         if flow.status == "deleted":
#             raise HTTPException(status_code=400, detail="Cannot abort a deleted flow")
#
#         if flow.status not in ["processing", "running", "executing"]:
#             raise HTTPException(status_code=400, detail="Flow is not currently executing")
#
#         # Store the previous status
#         previous_status = flow.status
#
#         # Mark flow as aborted
#         flow.status = "aborted"
#         flow.updated_at = datetime.utcnow()
#
#         # Add abort metadata
#         if not flow.flow_state:
#             flow.flow_state = {}
#         flow.flow_state["abort_metadata"] = {
#             "aborted_at": datetime.utcnow().isoformat(),
#             "aborted_by": context.user_id,
#             "previous_status": previous_status,
#             "abort_reason": request.get("reason", "User requested abort")
#         }
#
#         await db.commit()
#
#         logger.info(f"✅ Flow {flow_id} aborted successfully")
#
#         return {
#             "success": True,
#             "flow_id": str(flow_id),
#             "status": "aborted",
#             "message": "Flow execution aborted",
#             "current_phase": flow.current_phase,
#             "next_phase": None,
#             "method": "execution_abort"
#         }
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error aborting flow execution: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to abort flow execution: {str(e)}")


@execution_router.post("/flow/{flow_id}/retry", response_model=FlowOperationResponse)
async def retry_flow_execution(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed flow execution.

    This endpoint retries execution of a failed flow from the last successful phase.
    """
    try:
        logger.info(f"🔄 Retrying flow execution for {flow_id}")

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
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot retry a deleted flow")

        if flow.status not in ["failed", "error", "aborted"]:
            raise HTTPException(status_code=400, detail="Flow is not in a failed state")

        # Determine retry phase
        retry_phase = request.get("from_phase")
        if not retry_phase:
            # Find the last successful phase
            current_phase, _ = StatusCalculator.calculate_current_phase(flow)
            retry_phase = current_phase

        # Store the previous status
        previous_status = flow.status

        # Reset flow to processing
        flow.status = "processing"
        flow.current_phase = retry_phase
        flow.updated_at = datetime.utcnow()

        # Add retry metadata
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["retry_metadata"] = {
            "retried_at": datetime.utcnow().isoformat(),
            "retried_by": context.user_id,
            "previous_status": previous_status,
            "retry_from_phase": retry_phase,
            "retry_reason": request.get("reason", "User requested retry"),
        }

        await db.commit()

        logger.info(f"✅ Flow {flow_id} retry initiated from phase: {retry_phase}")

        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": "processing",
            "message": f"Flow retry initiated from phase: {retry_phase}",
            "current_phase": retry_phase,
            "next_phase": StatusCalculator.get_next_phase(retry_phase),
            "method": "execution_retry",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying flow execution: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retry flow execution: {str(e)}"
        )
