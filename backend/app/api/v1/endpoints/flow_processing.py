"""
Flow Processing API endpoints for intelligent flow continuation and routing.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.context import get_current_context, RequestContext
from app.services.agents.flow_processing_agent import FlowProcessingAgent, FlowContinuationResult
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)

router = APIRouter(tags=["flow-processing"])

class FlowContinuationRequest(BaseModel):
    """Request model for flow continuation"""
    user_context: Dict[str, Any] = Field(default_factory=dict)
    user_action: str = Field(default="continue_flow")

class FlowContinuationResponse(BaseModel):
    """Response model for flow continuation"""
    success: bool
    flow_id: str
    current_phase: str
    next_action: str
    routing_context: Dict[str, Any]
    checklist_status: List[Dict[str, Any]]
    user_guidance: Dict[str, Any]
    error_message: str = None
    
    # Enhanced fields for FlowStatusWidget
    flow_type: str = "unknown"
    progress_percentage: float = 0.0
    phase_completion_status: Dict[str, Any] = Field(default_factory=dict)
    routing_decision: Dict[str, Any] = Field(default_factory=dict)

class FlowChecklistResponse(BaseModel):
    """Response model for flow checklist status"""
    flow_id: str
    phases: List[Dict[str, Any]]
    overall_completion: float
    next_required_tasks: List[str]
    blocking_issues: List[str]

@router.post("/continue/{flow_id}")
async def continue_flow_with_agent(
    flow_id: str,
    request: FlowContinuationRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> FlowContinuationResponse:
    """
    Process flow continuation using the Flow Processing Agent.
    
    This endpoint serves as the central entry point for all "Continue Flow" requests.
    The Flow Processing Agent analyzes the flow state, evaluates completion checklists,
    and determines the optimal next step for the user.
    """
    
    try:
        logger.info(f"🤖 FLOW PROCESSING API: Received continuation request for flow {flow_id}")
        
        # Initialize Flow Processing Agent with context
        flow_agent = FlowProcessingAgent(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Process the continuation request
        result = await flow_agent.process_flow_continuation(
            flow_id=flow_id,
            user_context={
                **request.user_context,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_action": request.user_action
            }
        )
        
        if result.success:
            logger.info(f"✅ FLOW PROCESSING SUCCESS: {flow_id} -> {result.routing_decision.target_page}")
            
            # Calculate progress based on current phase
            phase_progress_map = {
                "data_import": 10,
                "attribute_mapping": 25,
                "data_cleansing": 45,
                "inventory": 65,
                "dependencies": 80,
                "tech_debt": 95,
                "completed": 100
            }
            
            overall_progress = phase_progress_map.get(result.current_phase, 0)
            
            # Build phase completion status
            phase_completion_status = {
                "data_import": {"completed": result.current_phase not in ["data_import"], "confidence": 0.9},
                "attribute_mapping": {"completed": result.current_phase not in ["data_import", "attribute_mapping"], "confidence": 0.9},
                "data_cleansing": {"completed": result.current_phase not in ["data_import", "attribute_mapping", "data_cleansing"], "confidence": 0.9},
                "inventory": {"completed": result.current_phase not in ["data_import", "attribute_mapping", "data_cleansing", "inventory"], "confidence": 0.9},
                "dependencies": {"completed": result.current_phase not in ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies"], "confidence": 0.9},
                "tech_debt": {"completed": result.current_phase == "completed", "confidence": 0.9}
            }
            
            return FlowContinuationResponse(
                success=True,
                flow_id=flow_id,
                current_phase=result.current_phase,
                next_action=result.routing_decision.reasoning,
                routing_context={
                    "target_page": result.routing_decision.target_page,
                    "context_data": result.routing_decision.context_data,
                    "specific_task": getattr(result.routing_decision, 'specific_task', None)
                },
                checklist_status=[],  # Keep for backward compatibility
                user_guidance={
                    "summary": result.user_guidance.get("summary", "Flow analysis complete"),
                    "next_steps": result.user_guidance.get("next_steps", []),
                    "estimated_time_to_complete": result.user_guidance.get("estimated_time_to_complete"),
                    "blockers": result.user_guidance.get("blockers", [])
                },
                # Enhanced fields for FlowStatusWidget
                flow_type=result.flow_type,
                progress_percentage=overall_progress,
                phase_completion_status=phase_completion_status,
                routing_decision={
                    "recommended_page": result.routing_decision.target_page,
                    "reasoning": result.routing_decision.reasoning,
                    "specific_task": getattr(result.routing_decision, 'specific_task', None),
                    "urgency_level": getattr(result.routing_decision, 'urgency_level', 'medium')
                }
            )
        else:
            logger.error(f"❌ FLOW PROCESSING FAILED: {flow_id} - {result.error_message}")
            
            return FlowContinuationResponse(
                success=False,
                flow_id=flow_id,
                current_phase=result.current_phase,
                next_action="error_recovery",
                routing_context={
                    "target_page": "/discovery/enhanced-dashboard",
                    "context_data": {"error": result.error_message}
                },
                checklist_status=[],
                user_guidance={"error": result.error_message},
                error_message=result.error_message
            )
        
    except Exception as e:
        logger.error(f"❌ FLOW PROCESSING API ERROR: {flow_id} - {str(e)}")
        
        return FlowContinuationResponse(
            success=False,
            flow_id=flow_id,
            current_phase="error",
            next_action="error_recovery",
            routing_context={
                "target_page": "/discovery/enhanced-dashboard",
                "context_data": {"error": str(e)}
            },
            checklist_status=[],
            user_guidance={"error": f"Flow processing failed: {str(e)}"},
            error_message=str(e)
        )

@router.get("/checklist/{flow_id}")
async def get_flow_checklist_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> FlowChecklistResponse:
    """
    Get detailed checklist status for a flow.
    
    This endpoint provides comprehensive information about what tasks have been
    completed and what still needs to be done for each phase of the flow.
    """
    
    try:
        logger.info(f"📋 CHECKLIST API: Getting status for flow {flow_id}")
        
        # Use the intelligent flow validation approach
        phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
        phase_results = []
        total_completion = 0
        next_required_tasks = []
        blocking_issues = []
        
        for phase in phases:
            try:
                # Call the validation endpoint for each phase
                validation = await validate_phase_data(flow_id, phase, db, context)
                
                is_complete = validation.get("complete", False)
                completion_percentage = 100 if is_complete else 50
                total_completion += completion_percentage
                
                if not is_complete:
                    next_required_tasks.append(f"Complete {phase.replace('_', ' ')} phase")
                    if "ERROR" in validation.get("status", ""):
                        blocking_issues.append(f"{phase}: {validation.get('message', 'Unknown error')}")
                
                phase_results.append({
                    "phase": phase,
                    "status": "completed" if is_complete else "in_progress",
                    "completion_percentage": completion_percentage,
                    "tasks": [{
                        "task_id": f"{phase}_validation",
                        "task_name": f"Validate {phase.replace('_', ' ')} completion",
                        "status": "completed" if is_complete else "pending",
                        "confidence": 0.9 if is_complete else 0.5,
                        "evidence": [validation.get("message", "No details")],
                        "next_steps": [] if is_complete else [f"Complete {phase.replace('_', ' ')} requirements"]
                    }],
                    "ready_for_next_phase": is_complete,
                    "next_required_actions": [] if is_complete else [f"Complete {phase.replace('_', ' ')} phase"]
                })
                
            except Exception as e:
                logger.error(f"Error validating phase {phase}: {e}")
                blocking_issues.append(f"{phase}: Validation error - {str(e)}")
                phase_results.append({
                    "phase": phase,
                    "status": "error",
                    "completion_percentage": 0,
                    "tasks": [],
                    "ready_for_next_phase": False,
                    "next_required_actions": [f"Fix validation error for {phase}"]
                })
        
        overall_completion = total_completion / len(phases) if phases else 0
        
        return FlowChecklistResponse(
            flow_id=flow_id,
            phases=phase_results,
            overall_completion=overall_completion,
            next_required_tasks=next_required_tasks[:5],
            blocking_issues=blocking_issues
        )
        
    except Exception as e:
        logger.error(f"❌ CHECKLIST API ERROR: {flow_id} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get checklist status: {str(e)}"
        )

@router.post("/analyze/{flow_id}")
async def analyze_flow_state(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed analysis of flow state for debugging and monitoring.
    
    This endpoint provides comprehensive information about the flow's current state,
    including all data sources that the Flow Processing Agent uses for decision making.
    """
    
    try:
        logger.info(f"🔍 ANALYSIS API: Analyzing flow state for {flow_id}")
        
        # Initialize Flow Processing Agent
        flow_agent = FlowProcessingAgent(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Get comprehensive flow analysis
        result = await flow_agent.process_flow_continuation(
            flow_id=flow_id,
            user_context={"analysis_mode": True}
        )
        
        return {
            "flow_id": flow_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "flow_state": {
                    "flow_type": result.flow_type,
                    "current_phase": result.current_phase,
                    "success": result.success
                },
                "routing_decision": {
                    "target_page": result.routing_decision.target_page,
                    "phase": result.routing_decision.phase,
                    "reasoning": result.routing_decision.reasoning,
                    "confidence": result.routing_decision.confidence
                },
                "user_guidance": result.user_guidance
            }
        }
        
    except Exception as e:
        logger.error(f"❌ ANALYSIS API ERROR: {flow_id} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze flow state: {str(e)}"
        )

@router.get("/validate-phase/{flow_id}/{phase}")
async def validate_phase_data(
    flow_id: str,
    phase: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Fast API endpoint for validating phase completion based on actual data.
    Used by flow processing agents to check if phases are truly complete.
    """
    try:
        # Get the flow
        flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.id == flow_id,
            DiscoveryFlow.client_account_id == context.client_account_id
        )
        result = await db.execute(flow_query)
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Phase-specific validation
        if phase == "data_import":
            return await _validate_data_import_phase(flow, db)
        elif phase == "attribute_mapping":
            return await _validate_attribute_mapping_phase(flow, db)
        elif phase == "data_cleansing":
            return await _validate_data_cleansing_phase(flow, db)
        elif phase == "inventory":
            return await _validate_inventory_phase(flow, db)
        elif phase == "dependencies":
            return await _validate_dependencies_phase(flow, db)
        elif phase == "tech_debt":
            return await _validate_tech_debt_phase(flow, db)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown phase: {phase}")
            
    except Exception as e:
        logger.error(f"Phase validation error for {phase}: {e}")
        return {
            "phase": phase,
            "status": "ERROR",
            "message": f"Validation error: {str(e)}",
            "complete": False
        }

async def _validate_data_import_phase(flow, db: AsyncSession) -> Dict[str, Any]:
    """Validate data import phase by checking for raw import records"""
    from sqlalchemy import select, func
    from app.models.data_import import DataImport, RawImportRecord
    
    # Count import sessions for this flow
    import_query = select(func.count(DataImport.id)).where(
        DataImport.engagement_id == flow.engagement_id,
        DataImport.client_account_id == flow.client_account_id
    )
    result = await db.execute(import_query)
    import_count = result.scalar() or 0
    
    # Count raw records
    raw_query = select(func.count(RawImportRecord.id)).join(
        DataImport, RawImportRecord.data_import_id == DataImport.id
    ).where(
        DataImport.engagement_id == flow.engagement_id,
        DataImport.client_account_id == flow.client_account_id
    )
    result = await db.execute(raw_query)
    raw_count = result.scalar() or 0
    
    complete = import_count > 0 and raw_count >= 5  # Minimum threshold
    
    return {
        "phase": "data_import",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "message": f"Found {import_count} import sessions with {raw_count} raw records",
        "complete": complete,
        "data": {
            "import_sessions": import_count,
            "raw_records": raw_count,
            "threshold_met": raw_count >= 5
        }
    }

async def _validate_attribute_mapping_phase(flow, db: AsyncSession) -> Dict[str, Any]:
    """Validate attribute mapping phase by checking field mappings"""
    from sqlalchemy import select, func
    from app.models.data_import import ImportFieldMapping
    
    # Count approved field mappings
    mapping_query = select(func.count(ImportFieldMapping.id)).where(
        ImportFieldMapping.status == "approved"
    )
    result = await db.execute(mapping_query)
    mapping_count = result.scalar() or 0
    
    # Count high-confidence mappings
    confidence_query = select(func.count(ImportFieldMapping.id)).where(
        ImportFieldMapping.confidence_score >= 0.7
    )
    result = await db.execute(confidence_query)
    confidence_count = result.scalar() or 0
    
    complete = mapping_count >= 3 and confidence_count >= 3  # Minimum thresholds
    
    return {
        "phase": "attribute_mapping",
        "status": "COMPLETE" if complete else "INCOMPLETE", 
        "message": f"Found {mapping_count} approved mappings, {confidence_count} high-confidence",
        "complete": complete,
        "data": {
            "approved_mappings": mapping_count,
            "high_confidence_mappings": confidence_count,
            "threshold_met": mapping_count >= 3 and confidence_count >= 3
        }
    }

async def _validate_data_cleansing_phase(flow, db: AsyncSession) -> Dict[str, Any]:
    """Validate data cleansing phase by checking asset data quality"""
    from sqlalchemy import select, func
    from app.models.asset import Asset
    
    # Count assets from this flow
    assets_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id
    )
    result = await db.execute(assets_query)
    asset_count = result.scalar() or 0
    
    # Count assets with complete data (name, type, environment)
    complete_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.name.isnot(None),
        Asset.asset_type.isnot(None),
        Asset.environment.isnot(None)
    )
    result = await db.execute(complete_query)
    complete_count = result.scalar() or 0
    
    completion_rate = complete_count / max(asset_count, 1)
    complete = asset_count >= 5 and completion_rate >= 0.8
    
    return {
        "phase": "data_cleansing",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "message": f"Found {complete_count}/{asset_count} assets with complete data ({completion_rate:.1%})",
        "complete": complete,
        "data": {
            "total_assets": asset_count,
            "complete_assets": complete_count,
            "completion_rate": completion_rate,
            "threshold_met": complete
        }
    }

async def _validate_inventory_phase(flow, db: AsyncSession) -> Dict[str, Any]:
    """Validate inventory phase by checking populated asset inventory"""
    from sqlalchemy import select, func
    from app.models.asset import Asset
    
    # Count assets with detailed information
    detailed_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.name.isnot(None),
        Asset.asset_type.isnot(None),
        Asset.environment.isnot(None),
        Asset.ip_address.isnot(None)
    )
    result = await db.execute(detailed_query)
    detailed_count = result.scalar() or 0
    
    # Count assets with business context
    business_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.business_owner.isnot(None)
    )
    result = await db.execute(business_query)
    business_count = result.scalar() or 0
    
    complete = detailed_count >= 5 and business_count >= 2
    
    return {
        "phase": "inventory",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "message": f"Found {detailed_count} detailed assets, {business_count} with business context",
        "complete": complete,
        "data": {
            "detailed_assets": detailed_count,
            "business_context_assets": business_count,
            "threshold_met": complete
        }
    }

async def _validate_dependencies_phase(flow, db: AsyncSession) -> Dict[str, Any]:
    """Validate dependencies phase by checking dependency analysis"""
    from sqlalchemy import select, func
    from app.models.asset import Asset, AssetDependency
    
    # Count assets with dependency data
    deps_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.dependencies.isnot(None)
    )
    result = await db.execute(deps_query)
    deps_count = result.scalar() or 0
    
    # Count formal dependency relationships
    formal_deps_query = select(func.count(AssetDependency.id)).join(
        Asset, AssetDependency.asset_id == Asset.id
    ).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id
    )
    result = await db.execute(formal_deps_query)
    formal_count = result.scalar() or 0
    
    complete = deps_count >= 3 or formal_count >= 2
    
    return {
        "phase": "dependencies",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "message": f"Found {deps_count} assets with dependencies, {formal_count} formal relationships",
        "complete": complete,
        "data": {
            "assets_with_dependencies": deps_count,
            "formal_relationships": formal_count,
            "threshold_met": complete
        }
    }

async def _validate_tech_debt_phase(flow, db: AsyncSession) -> Dict[str, Any]:
    """Validate tech debt phase by checking migration strategies and assessments"""
    from sqlalchemy import select, func
    from app.models.asset import Asset
    
    # Count assets with 6R strategy
    sixr_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.six_r_strategy.isnot(None)
    )
    result = await db.execute(sixr_query)
    sixr_count = result.scalar() or 0
    
    # Count assets with complexity assessment
    complexity_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.migration_complexity.isnot(None)
    )
    result = await db.execute(complexity_query)
    complexity_count = result.scalar() or 0
    
    # Count assets with business criticality
    criticality_query = select(func.count(Asset.id)).where(
        Asset.discovery_flow_id == flow.id,
        Asset.client_account_id == flow.client_account_id,
        Asset.business_criticality.isnot(None)
    )
    result = await db.execute(criticality_query)
    criticality_count = result.scalar() or 0
    
    complete = sixr_count >= 3 and complexity_count >= 3 and criticality_count >= 3
    
    return {
        "phase": "tech_debt", 
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "message": f"Found {sixr_count} 6R strategies, {complexity_count} complexity, {criticality_count} criticality assessments",
        "complete": complete,
        "data": {
            "sixr_strategies": sixr_count,
            "complexity_assessments": complexity_count,
            "criticality_assessments": criticality_count,
            "threshold_met": complete
        }
    }

@router.get("/validate-flow/{flow_id}")
async def validate_flow_phases(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Fast fail-first validation that stops at the first incomplete phase.
    Returns the current phase that needs attention.
    """
    try:
        phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
        
        for phase in phases:
            validation = await validate_phase_data(flow_id, phase, db, context)
            
            if not validation["complete"]:
                return {
                    "flow_id": flow_id,
                    "current_phase": phase,
                    "status": "INCOMPLETE",
                    "next_action": f"Complete {phase.replace('_', ' ')} phase",
                    "validation_details": validation,
                    "route_to": f"/discovery/{phase.replace('_', '-')}?flow_id={flow_id}",
                    "fail_fast": True
                }
        
        # All phases complete
        return {
            "flow_id": flow_id,
            "current_phase": "completed",
            "status": "COMPLETE",
            "next_action": "Proceed to assessment phase",
            "route_to": f"/assess?flow_id={flow_id}",
            "all_phases_complete": True
        }
        
    except Exception as e:
        logger.error(f"Flow validation error: {e}")
        return {
            "flow_id": flow_id,
            "status": "ERROR",
            "message": f"Validation error: {str(e)}",
            "route_to": "/discovery/enhanced-dashboard"
        } 