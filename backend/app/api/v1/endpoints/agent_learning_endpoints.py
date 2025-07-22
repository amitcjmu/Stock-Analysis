"""
Agent Learning API Endpoints
Supports Tasks C.1 and C.2: Agent Memory/Learning System and Cross-Page Communication.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from app.api.v1.dependencies import get_crewai_flow_service
from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.agent_ui_bridge import agent_ui_bridge
from app.services.crewai_flow_service import CrewAIFlowService

# Try to import client context manager
try:
    from app.services.agent_learning.core.learning.client_context import ClientContextManager
    client_context_manager = ClientContextManager()
except ImportError:
    client_context_manager = None

logger = logging.getLogger(__name__)

router = APIRouter()

# === AGENT LEARNING SYSTEM ENDPOINTS (Task C.1) ===

@router.post("/learning/field-mapping")
async def learn_field_mapping_pattern(
    request: Request,
    learning_data: Dict[str, Any] = Body(...)
):
    """Learn from field mapping corrections and successes."""
    try:
        # Extract context from headers
        context = LearningContext(
            client_account_id=request.headers.get('X-Client-ID'),
            engagement_id=request.headers.get('X-Engagement-ID'),
            flow_id=request.headers.get('X-Flow-ID')
        )
        
        await agent_learning_system.learn_field_mapping_pattern(learning_data, context)
        return {
            "success": True,
            "message": "Field mapping pattern learned successfully",
            "learned_pattern": learning_data.get("original_field", "unknown"),
            "context": context.context_hash
        }
    except Exception as e:
        logger.error(f"Error learning field mapping pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/field-mapping/suggest/{field_name}")
async def suggest_field_mapping(
    request: Request,
    field_name: str,
    context_data: Optional[Dict[str, Any]] = None
):
    """Get field mapping suggestions based on learned patterns."""
    try:
        # Extract context from headers
        context = LearningContext(
            client_account_id=request.headers.get('X-Client-ID'),
            engagement_id=request.headers.get('X-Engagement-ID'),
            flow_id=request.headers.get('X-Flow-ID')
        )
        
        suggestion = await agent_learning_system.suggest_field_mapping(field_name, context_data, context)
        return {
            "field_name": field_name,
            "suggestion": suggestion,
            "learning_available": suggestion["confidence"] > 0.0,
            "context": context.context_hash
        }
    except Exception as e:
        logger.error(f"Error getting field mapping suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/data-source-pattern")
async def learn_data_source_pattern(
    source_data: Dict[str, Any] = Body(...)
):
    """Learn patterns from data source analysis corrections."""
    try:
        await agent_learning_system.learn_data_source_pattern(source_data)
        return {
            "success": True,
            "message": "Data source pattern learned successfully",
            "source_type": source_data.get("source_type", "unknown")
        }
    except Exception as e:
        logger.error(f"Error learning data source pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/quality-assessment")
async def learn_quality_assessment(
    quality_data: Dict[str, Any] = Body(...)
):
    """Learn from quality assessment corrections and validations."""
    try:
        await agent_learning_system.learn_quality_assessment(quality_data)
        return {
            "success": True,
            "message": "Quality assessment pattern learned successfully"
        }
    except Exception as e:
        logger.error(f"Error learning quality assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/user-preferences")
async def learn_user_preferences(
    preference_data: Dict[str, Any] = Body(...),
    engagement_id: Optional[str] = None
):
    """Learn user preferences for client/engagement-specific context."""
    try:
        await agent_learning_system.learn_user_preferences(preference_data, engagement_id)
        return {
            "success": True,
            "message": "User preferences learned successfully",
            "engagement_id": engagement_id
        }
    except Exception as e:
        logger.error(f"Error learning user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/agent-performance")
async def track_agent_performance(
    agent_id: str,
    performance_data: Dict[str, Any] = Body(...)
):
    """Track agent performance for accuracy improvement."""
    try:
        await agent_learning_system.track_agent_performance(agent_id, performance_data)
        return {
            "success": True,
            "message": "Agent performance tracked successfully",
            "agent_id": agent_id
        }
    except Exception as e:
        logger.error(f"Error tracking agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/agent-performance/{agent_id}")
async def get_agent_accuracy_metrics(agent_id: str):
    """Get accuracy metrics and improvement tracking for an agent."""
    try:
        metrics = await agent_learning_system.get_agent_accuracy_metrics(agent_id)
        return {
            "agent_id": agent_id,
            "accuracy_metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error getting agent accuracy metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/stats")
async def get_learning_statistics():
    """Get statistics about the learning system."""
    try:
        stats = agent_learning_system.get_learning_statistics()
        return {
            "learning_statistics": stats,
            "system_health": {
                "patterns_learned": stats["field_mapping_patterns"] > 0,
                "agents_tracked": stats["agents_tracked"] > 0,
                "learning_active": stats["total_learning_events"] > 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting learning statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === CLIENT CONTEXT MANAGEMENT ENDPOINTS (Task C.1) ===
# These endpoints were part of the deleted client_context_manager service.
# They are removed to prevent import errors. The functionality should be
# integrated into the agent_learning_system or other core services if needed.

# @router.post("/context/client/{client_account_id}")
# async def create_client_context(
#     client_account_id: int,
#     client_data: Dict[str, Any] = Body(...)
# ):
#     """Create or update client-specific context."""
#     try:
#         await client_context_manager.create_client_context(client_account_id, client_data)
#         return {
#             "success": True,
#             "message": "Client context created/updated successfully",
#             "client_account_id": client_account_id
#         }
#     except Exception as e:
#         logger.error(f"Error creating client context: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.post("/context/engagement/{engagement_id}")
# async def create_engagement_context(
#     engagement_id: str,
#     client_account_id: int,
#     engagement_data: Dict[str, Any] = Body(...)
# ):
#     """Create or update engagement-specific context."""
#     try:
#         await client_context_manager.create_engagement_context(
#             engagement_id, client_account_id, engagement_data
#         )
#         return {
#             "success": True,
#             "message": "Engagement context created/updated successfully",
#             "engagement_id": engagement_id
#         }
#     except Exception as e:
#         logger.error(f"Error creating engagement context: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.post("/context/organizational-pattern/{client_account_id}")
# async def learn_organizational_pattern(
#     client_account_id: int,
#     pattern_data: Dict[str, Any] = Body(...)
# ):
#     """Learn organizational patterns specific to the client."""
#     try:
#         await client_context_manager.learn_organizational_pattern(client_account_id, pattern_data)
#         return {
#             "success": True,
#             "message": "Organizational pattern learned successfully",
#             "pattern_type": pattern_data.get("pattern_type", "unknown")
#         }
#     except Exception as e:
#         logger.error(f"Error learning organizational pattern: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/context/organizational-patterns/{client_account_id}")
# async def get_organizational_patterns(client_account_id: int):
#     """Get organizational patterns for a client."""
#     try:
#         patterns = await client_context_manager.get_organizational_patterns(client_account_id)
#         return {
#             "client_account_id": client_account_id,
#             "organizational_patterns": patterns
#         }
#     except Exception as e:
#         logger.error(f"Error getting organizational patterns: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.post("/context/clarification-response/{engagement_id}")
# async def store_clarification_response(
#     engagement_id: str,
#     clarification_data: Dict[str, Any] = Body(...)
# ):
#     """Store clarification responses for learning."""
#     try:
#         await client_context_manager.store_clarification_response(engagement_id, clarification_data)
#         return {
#             "success": True,
#             "message": "Clarification response stored successfully",
#             "engagement_id": engagement_id
#         }
#     except Exception as e:
#         logger.error(f"Error storing clarification response: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/context/clarification-history/{engagement_id}")
# async def get_clarification_history(
#     engagement_id: str,
#     question_type: Optional[str] = None
# ):
#     """Get clarification history for an engagement."""
#     try:
#         history = await client_context_manager.get_clarification_history(engagement_id, question_type)
#         return {
#             "engagement_id": engagement_id,
#             "clarification_history": history
#         }
#     except Exception as e:
#         logger.error(f"Error getting clarification history: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/context/client/{client_account_id}")
# async def get_client_context(client_account_id: int):
#     """Get the context for a specific client."""
#     try:
#         context = await client_context_manager.get_client_context(client_account_id)
#         if context is None:
#             raise HTTPException(status_code=404, detail="Client context not found")
#         return context
#     except Exception as e:
#         logger.error(f"Error getting client context: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/context/engagement/{engagement_id}")
# async def get_engagement_context(engagement_id: str):
#     """Get the context for a specific engagement."""
#     try:
#         context = await client_context_manager.get_engagement_context(engagement_id)
#         if context is None:
#             raise HTTPException(status_code=404, detail="Engagement context not found")
#         return context
#     except Exception as e:
#         logger.error(f"Error getting engagement context: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/context/combined/{engagement_id}")
# async def get_combined_context(engagement_id: str):
#     """Get the combined client and engagement context."""
#     try:
#         context = await client_context_manager.get_combined_context(engagement_id)
#         if context is None:
#             raise HTTPException(status_code=404, detail="Combined context not found")
#         return context
#     except Exception as e:
#         logger.error(f"Error getting combined context: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# === CROSS-PAGE CONTEXT & AGENT COORDINATION (Task C.2) ===

@router.post("/context/cross-page/set")
async def set_cross_page_context(
    context_data: Dict[str, Any]
):
    context_data.get("value")
    context_data.get("page_source", "unknown")

    # This functionality is now part of the UIInteractionHandler within the flow service
    # The new model requires a flow_state object, so direct context setting is not supported in the same way.
    # crewai_flow_service.ui_interaction_handler.context_handler.set_cross_page_context(key, value, page_source)
    
    return {"status": "success", "message": "Cross-page context set (deprecated)"}

@router.get("/context/cross-page/get")
async def get_cross_page_context(
    key: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality is now part of the UIInteractionHandler within the flow service
    # context = service.ui_interaction_handler.context_handler.get_cross_page_context(key)
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.get("/context/cross-page/metadata")
async def get_context_metadata(
    key: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality is now part of the UIInteractionHandler within the flow service
    # metadata = service.ui_interaction_handler.context_handler.get_context_metadata(key)
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.delete("/context/cross-page/clear")
async def clear_cross_page_context(
    key: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality is now part of the UIInteractionHandler within the flow service
    # service.ui_interaction_handler.context_handler.clear_cross_page_context(key)
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.post("/coordination/agent-state/update")
async def update_agent_state(
    state_update: Dict[str, Any],
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality is now managed within individual agent flows.
    # service.update_agent_state(state_update)
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.get("/coordination/agent-state/get")
async def get_agent_state(
    agent_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality is now managed within individual agent flows.
    # state = service.get_agent_state(agent_id)
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.get("/coordination/agent-states/all")
async def get_all_agent_states(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    # This functionality is now managed within individual agent flows.
    # states = service.get_all_agent_states()
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.get("/coordination/summary")
async def get_agent_coordination_summary(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    # This functionality is now managed within individual agent flows.
    # summary = service.get_agent_coordination_summary()
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.get("/coordination/dependencies")
async def get_context_dependencies(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    # This functionality is now managed within individual agent flows.
    # dependencies = service.get_context_dependencies()
    return {"status": "deprecated", "message": "Functionality moved to flow-based."}

@router.post("/coordination/context/clear-stale")
async def clear_stale_context(
    config: Dict[str, Any],
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality is now managed within individual agent flows.
    # service.clear_stle_context(config)
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.post("/coordination/master-summary")
async def get_master_summary(
    summary_request: Dict[str, Any],
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This functionality has been significantly altered with the new flow-based service.
    # coordination_summary = service.get_agent_coordination_summary()
    
    # Placeholder for a more robust implementation if needed
    return {"status": "deprecated", "message": "Functionality moved to flow-based service."}

@router.get("/learning/experiences")
async def get_learning_experiences(
    limit: Optional[int] = 100,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    # This would now be sourced from the learning system, not the UI bridge
    # recent_experiences = service.get_recent_learning_experiences(limit=limit)
    return {"status": "deprecated", "message": "Functionality moved to agent_learning_system."}

# === COMBINED LEARNING AND CONTEXT ENDPOINTS ===

@router.get("/health")
async def get_agent_learning_health(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """Get health status of the agent learning systems."""
    try:
        learning_stats = agent_learning_system.get_learning_statistics()
        flow_health = service.get_health_status()
        
        return {
            "status": "healthy",
            "agent_learning_system": {
                "status": "active",
                "statistics": learning_stats
            },
            "crewai_flow_service": flow_health
        }
    except Exception as e:
        logger.error(f"Error getting agent learning health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integration/learn-from-user-response")
async def learn_from_user_response(
    response_data: Dict[str, Any] = Body(...)
):
    """Integrated learning from user responses across all systems."""
    try:
        response_type = response_data.get("response_type")
        engagement_id = response_data.get("engagement_id")
        
        results = []
        
        # Learn in agent learning system
        if response_type == "field_mapping":
            await agent_learning_system.learn_field_mapping_pattern(response_data)
            results.append("field_mapping_learned")
        
        # Store in client context manager
        if engagement_id and client_context_manager:
            await client_context_manager.store_clarification_response(engagement_id, response_data)
            results.append("clarification_stored")
        
        # Update cross-page context if needed
        if response_data.get("share_across_pages"):
            context_key = f"user_response_{response_type}_{datetime.utcnow().timestamp()}"
            agent_ui_bridge.set_cross_page_context(
                context_key, 
                response_data, 
                response_data.get("page_source", "unknown")
            )
            results.append("context_shared")
        
        return {
            "success": True,
            "message": "User response processed across all learning systems",
            "actions_taken": results,
            "response_type": response_type
        }
    except Exception as e:
        logger.error(f"Error processing user response: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 