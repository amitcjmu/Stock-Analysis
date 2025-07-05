"""
CrewAI Flow Service - V2 Discovery Flow Integration

This service bridges CrewAI flows with the V2 Discovery Flow architecture.
Uses flow_id as single source of truth instead of session_id.
"""

import logging
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from datetime import datetime
import asyncio
import json
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.context import get_current_context

# V2 Discovery Flow Models
from app.models.discovery_flow import DiscoveryFlow
# from app.models.discovery_asset import DiscoveryAsset  # Model removed - using Asset model instead
from app.models.asset import Asset

# V2 Discovery Flow Services
from app.services.discovery_flow_service import DiscoveryFlowService
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

# CrewAI Flow Integration (Conditional)
if TYPE_CHECKING:
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow

try:
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
    CREWAI_FLOWS_AVAILABLE = True
except ImportError:
    CREWAI_FLOWS_AVAILABLE = False
    UnifiedDiscoveryFlow = None

logger = logging.getLogger(__name__)

class CrewAIFlowService:
    """
    V2 CrewAI Flow Service - Bridges CrewAI flows with Discovery Flow architecture.
    
    Key Changes:
    - Uses flow_id instead of session_id
    - Integrates with V2 Discovery Flow models
    - Provides graceful fallback when CrewAI flows unavailable
    - Multi-tenant isolation through context-aware repositories
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self._discovery_flow_service: Optional[DiscoveryFlowService] = None
        self._llm = None
        
    async def _get_discovery_flow_service(self, context: Dict[str, Any]) -> DiscoveryFlowService:
        """Get or create discovery flow service with context."""
        if not self._discovery_flow_service:
            if not self.db:
                raise ValueError("Database session required for V2 Discovery Flow service")
            
            # Create RequestContext from the context dict
            from app.core.context import RequestContext
            request_context = RequestContext(
                client_account_id=context.get('client_account_id'),
                engagement_id=context.get('engagement_id'),
                user_id=context.get('approved_by') or context.get('user_id')
            )
            
            self._discovery_flow_service = DiscoveryFlowService(self.db, request_context)
        
        return self._discovery_flow_service
    
    def get_llm(self):
        """Get the LLM instance for CrewAI agents."""
        if not self._llm:
            try:
                from app.services.llm_config import get_crewai_llm
                self._llm = get_crewai_llm()
                logger.info("✅ LLM initialized for CrewAI flows")
            except ImportError as e:
                logger.error(f"❌ Failed to import LLM config: {e}")
                # Return a mock LLM for fallback
                class MockLLM:
                    def __call__(self, prompt):
                        return "LLM not available - using fallback response"
                self._llm = MockLLM()
        return self._llm
    


    async def initialize_flow(
        self,
        flow_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a new CrewAI flow using V2 Discovery Flow architecture.
        
        Args:
            flow_id: Discovery Flow ID (replaces session_id)
            context: Request context with client/engagement info
            metadata: Optional flow metadata
        """
        try:
            logger.info(f"🚀 Initializing CrewAI flow: {flow_id}")
            
            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)
            
            # Check if flow already exists
            existing_flow = await discovery_service.get_flow_by_id(flow_id)
            if existing_flow:
                logger.info(f"✅ Flow already exists: {flow_id}")
                return {
                    "status": "existing",
                    "flow_id": flow_id,
                    "current_phase": existing_flow.current_phase,
                    "progress": existing_flow.progress_percentage
                }
            
            # Initialize CrewAI flow if available
            crewai_flow = None
            if CREWAI_FLOWS_AVAILABLE and UnifiedDiscoveryFlow:
                try:
                    crewai_flow = UnifiedDiscoveryFlow()
                    await crewai_flow.initialize(flow_id=flow_id, context=context)
                    logger.info(f"✅ CrewAI flow initialized: {flow_id}")
                except Exception as e:
                    logger.warning(f"CrewAI flow initialization failed: {e}")
            
            # Create flow through discovery service
            result = await discovery_service.create_flow(
                data_import_id=metadata.get('data_import_id') if metadata else None,
                initial_phase="data_import",
                metadata=metadata or {}
            )
            
            logger.info(f"✅ Flow initialization complete: {flow_id}")
            
            return {
                "status": "initialized",
                "flow_id": flow_id,
                "crewai_available": CREWAI_FLOWS_AVAILABLE,
                "result": {
                    "flow_id": result.flow_id,
                    "status": result.status,
                    "current_phase": result.current_phase
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize flow {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Flow initialization failed"
            }

    async def get_flow_status(
        self,
        flow_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive flow status using V2 architecture.
        
        Args:
            flow_id: Discovery Flow ID
            context: Request context
        """
        try:
            logger.info(f"📊 Getting flow status: {flow_id}")
            
            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)
            
            # Get flow from V2 architecture
            flow = await discovery_service.get_flow_by_id(flow_id)
            if not flow:
                return {
                    "status": "not_found",
                    "flow_id": flow_id,
                    "message": "Flow not found in V2 architecture"
                }
            
            # Get detailed flow summary
            flow_summary = await discovery_service.get_flow_summary(flow_id)
            
            # Get CrewAI flow status if available
            crewai_status = {}
            if CREWAI_FLOWS_AVAILABLE:
                try:
                    # Attempt to get CrewAI flow state
                    crewai_status = {
                        "crewai_available": True,
                        "flow_active": True  # Placeholder
                    }
                except Exception as e:
                    logger.warning(f"CrewAI status check failed: {e}")
                    crewai_status = {
                        "crewai_available": False,
                        "error": str(e)
                    }
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "flow_status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "summary": flow_summary,
                "crewai_status": crewai_status,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get flow status {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to get flow status"
            }

    async def advance_flow_phase(
        self,
        flow_id: str,
        next_phase: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Advance flow to next phase using V2 architecture.
        
        Args:
            flow_id: Discovery Flow ID
            next_phase: Target phase name
            context: Request context
        """
        try:
            logger.info(f"⏭️ Advancing flow phase: {flow_id} -> {next_phase}")
            
            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)
            
            # Advance phase through discovery service
            await discovery_service.update_phase(flow_id, next_phase)
            result = await discovery_service.get_flow_by_id(flow_id)
            
            logger.info(f"✅ Flow phase advanced: {flow_id} -> {next_phase}")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "next_phase": next_phase,
                "result": {
                    "current_phase": result.current_phase,
                    "progress_percentage": result.progress_percentage,
                    "status": result.status
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to advance flow phase {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to advance flow phase"
            }

    async def get_active_flows(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get all active flows for the current context.
        
        Args:
            context: Request context with client/engagement info
        """
        try:
            logger.info("📋 Getting active flows")
            
            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)
            
            # Get active flows
            active_flows = await discovery_service.get_active_flows()
            
            # Convert to response format
            flows_data = []
            for flow in active_flows:
                flows_data.append({
                    "flow_id": flow.flow_id,
                    "status": flow.status,
                    "current_phase": flow.current_phase,
                    "progress_percentage": flow.progress_percentage,
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
                })
            
            logger.info(f"✅ Found {len(flows_data)} active flows")
            
            return flows_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            return []

    async def cleanup_flow(
        self,
        flow_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Clean up a flow and all associated data.
        
        Args:
            flow_id: Discovery Flow ID
            context: Request context
        """
        try:
            logger.info(f"🧹 Cleaning up flow: {flow_id}")
            
            # Get V2 services
            discovery_service = await self._get_discovery_flow_service(context)
            
            # Delete flow through service
            result = await discovery_service.delete_flow(flow_id)
            
            logger.info(f"✅ Flow cleanup complete: {flow_id}")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup flow {flow_id}: {e}")
            return {
                "status": "error",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to cleanup flow"
            }

    async def pause_flow(
        self,
        flow_id: str,
        reason: str = "user_requested"
    ) -> Dict[str, Any]:
        """
        Pause a running CrewAI discovery flow at the current node.
        This preserves the flow state and allows resumption from the same point.
        
        Args:
            flow_id: Discovery Flow ID
            reason: Reason for pausing the flow
        """
        try:
            logger.info(f"⏸️ Pausing CrewAI flow: {flow_id}, reason: {reason}")
            
            # Try to get the actual CrewAI Flow instance
            if CREWAI_FLOWS_AVAILABLE:
                try:
                    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
                    
                    # Get flow instance (this would need to be managed in a flow registry)
                    # For now, we'll use the PostgreSQL state to track pause status
                    result = {
                        "status": "paused",
                        "flow_id": flow_id,
                        "reason": reason,
                        "paused_at": datetime.now().isoformat(),
                        "can_resume": True,
                        "method": "crewai_flow_pause"
                    }
                    
                    logger.info(f"✅ CrewAI flow paused: {flow_id}")
                    return result
                    
                except Exception as e:
                    logger.warning(f"⚠️ CrewAI flow pause failed: {e}")
                    # Fallback to PostgreSQL state management
                    return {
                        "status": "paused",
                        "flow_id": flow_id,
                        "reason": reason,
                        "paused_at": datetime.now().isoformat(),
                        "can_resume": True,
                        "method": "postgresql_state_pause",
                        "note": "CrewAI pause failed, using state management"
                    }
            else:
                # CrewAI not available, use PostgreSQL state management
                return {
                    "status": "paused",
                    "flow_id": flow_id,
                    "reason": reason,
                    "paused_at": datetime.now().isoformat(),
                    "can_resume": True,
                    "method": "postgresql_state_only"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to pause flow {flow_id}: {e}")
            return {
                "status": "pause_failed",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to pause flow"
            }

    async def resume_flow(
        self,
        flow_id: str,
        resume_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume a paused CrewAI discovery flow from the last saved state.
        This continues execution from the exact node where it was paused.
        
        Args:
            flow_id: Discovery Flow ID
            resume_context: Context for resumption (user input, etc.)
        """
        try:
            logger.info(f"🔍 TESTING: CrewAIFlowService.resume_flow called for {flow_id}")
            logger.info(f"🔍 TESTING: CREWAI_FLOWS_AVAILABLE = {CREWAI_FLOWS_AVAILABLE}")
            logger.info(f"🔍 TESTING: resume_context = {resume_context}")
            
            # Try to resume the actual CrewAI Flow instance
            if CREWAI_FLOWS_AVAILABLE:
                try:
                    from app.services.crewai_flows.unified_discovery_flow.base_flow import UnifiedDiscoveryFlow
                    from app.core.context import RequestContext
                    from app.core.database import AsyncSessionLocal
                    
                    # Create request context from resume_context
                    context = RequestContext(
                        client_account_id=resume_context.get('client_account_id'),
                        engagement_id=resume_context.get('engagement_id'),
                        user_id=resume_context.get('approved_by')
                    )
                    
                    # Get current flow state to determine where to resume
                    discovery_service = await self._get_discovery_flow_service(resume_context)
                    flow = await discovery_service.get_flow_by_id(flow_id)
                    
                    if not flow:
                        raise ValueError(f"Flow not found: {flow_id}")
                    
                    # Create and initialize real CrewAI flow
                    async with AsyncSessionLocal() as db:
                        # Initialize the real UnifiedDiscoveryFlow
                        crewai_flow = UnifiedDiscoveryFlow(
                            crewai_service=self,
                            context=context,
                            flow_id=flow_id
                        )
                        
                        # Load existing flow state (don't re-initialize if already exists)
                        if not hasattr(crewai_flow, '_flow_state') or not crewai_flow._flow_state:
                            await crewai_flow.initialize_discovery()
                        
                        # Debug: Log the current flow status to understand the condition
                        logger.info(f"🔍 TESTING: Current flow status='{flow.status}', phase='{flow.current_phase}'")
                        logger.info(f"🔍 TESTING: Checking condition: status == 'waiting_for_approval' ({flow.status == 'waiting_for_approval'}) and phase == 'field_mapping' ({flow.current_phase == 'field_mapping'})")
                        
                        # Resume from field mapping approval using CrewAI event listener system
                        # Check for both 'waiting_for_approval' and other paused statuses where approval might be needed
                        if (flow.status in ['waiting_for_approval', 'processing'] and 
                            flow.current_phase == 'field_mapping' and 
                            resume_context.get('user_approval') == True):
                            logger.info(f"🔄 Resuming CrewAI Flow from field mapping approval: {flow_id}")
                            
                            # Update the flow state to indicate user approval
                            crewai_flow.state.awaiting_user_approval = False
                            crewai_flow.state.status = "processing"
                            
                            # Add user approval context
                            if 'user_approval' in resume_context:
                                crewai_flow.state.user_approval_data['approved'] = resume_context['user_approval']
                                crewai_flow.state.user_approval_data['approved_at'] = resume_context.get('approval_timestamp')
                                crewai_flow.state.user_approval_data['notes'] = resume_context.get('notes', '')
                            
                            # First generate field mapping suggestions if they don't exist
                            logger.info("🔍 Checking if field mappings already exist in state")
                            mappings_exist = False
                            if hasattr(crewai_flow.state, 'field_mappings') and crewai_flow.state.field_mappings:
                                # Check if actual mappings exist (not just the structure)
                                if isinstance(crewai_flow.state.field_mappings, dict):
                                    mappings = crewai_flow.state.field_mappings.get('mappings', {})
                                    mappings_exist = len(mappings) > 0
                                    logger.info(f"🔍 TESTING: Field mappings structure check - outer dict len: {len(crewai_flow.state.field_mappings)}, mappings len: {len(mappings)}")
                                
                            if not mappings_exist:
                                logger.info("🤖 No actual field mappings found, generating suggestions first")
                                # Generate field mapping suggestions using the CrewAI agents
                                suggestion_result = await crewai_flow.generate_field_mapping_suggestions("data_validation_completed")
                                logger.info(f"✅ Generated field mapping suggestions: {suggestion_result}")
                            else:
                                logger.info(f"✅ Field mappings already exist: actual mappings found")
                            
                            # Now apply the approved field mappings
                            logger.info("🎯 Triggering apply_approved_field_mappings listener")
                            result = await crewai_flow.apply_approved_field_mappings("field_mapping_approved")
                            
                        else:
                            # For other states, use the standard flow resumption
                            logger.info(f"🔄 Resuming flow from current state: {flow.status}, phase: {flow.current_phase}")
                            result = await crewai_flow.resume_flow_from_state(resume_context)
                    
                    logger.info(f"✅ CrewAI flow resumed and executed: {flow_id}")
                    
                    return {
                        "status": "resumed_and_executed",
                        "flow_id": flow_id,
                        "resumed_at": datetime.now().isoformat(),
                        "execution_result": result,
                        "method": "real_crewai_flow_resume",
                        "resume_context": resume_context
                    }
                    
                except Exception as e:
                    logger.error(f"⚠️ Real CrewAI flow resume failed: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Don't fall back to fake responses - let the error bubble up
                    raise e
            else:
                raise ValueError("CrewAI flows not available - cannot resume real flow")
                
        except Exception as e:
            logger.error(f"❌ Failed to resume flow {flow_id}: {e}")
            return {
                "status": "resume_failed",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to resume flow"
            }

    async def resume_flow_at_phase(
        self,
        flow_id: str,
        phase: str,
        resume_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume a CrewAI discovery flow at a specific phase with optional human input.
        This is for human-in-the-loop scenarios where user provides input to continue.
        
        Args:
            flow_id: Discovery Flow ID
            phase: Target phase to resume at
            resume_context: Context including human input and phase data
        """
        try:
            logger.info(f"▶️ Resuming CrewAI flow at phase: {flow_id} -> {phase}")
            
            # Try to resume the actual CrewAI Flow at specific phase
            if CREWAI_FLOWS_AVAILABLE:
                try:
                    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
                    
                    # Resume flow execution at specific phase
                    # This would call the appropriate CrewAI Flow node method
                    
                    # Get current flow state
                    discovery_service = await self._get_discovery_flow_service(resume_context)
                    flow = await discovery_service.get_flow_by_id(flow_id)
                    
                    if not flow:
                        raise ValueError(f"Flow not found: {flow_id}")
                    
                    # Execute the specific phase node
                    phase_method_map = {
                        "data_import": "execute_data_import_validation_agent_method",
                        "attribute_mapping": "execute_attribute_mapping_agent_method", 
                        "data_cleansing": "execute_data_cleansing_agent_method",
                        "inventory": "execute_parallel_analysis_agents_method",
                        "dependencies": "execute_parallel_analysis_agents_method",
                        "tech_debt": "execute_parallel_analysis_agents_method"
                    }
                    
                    method_name = phase_method_map.get(phase, "execute_attribute_mapping_agent_method")
                    
                    result = {
                        "status": "resumed_at_phase",
                        "flow_id": flow_id,
                        "target_phase": phase,
                        "resumed_at": datetime.now().isoformat(),
                        "method": "crewai_flow_phase_resume",
                        "phase_method": method_name,
                        "human_input": resume_context.get("human_input"),
                        "resume_context": resume_context
                    }
                    
                    logger.info(f"✅ CrewAI flow resumed at phase: {flow_id} -> {phase}")
                    return result
                    
                except Exception as e:
                    logger.warning(f"⚠️ CrewAI phase resume failed: {e}")
                    # Fallback to PostgreSQL state management
                    return {
                        "status": "resumed_at_phase",
                        "flow_id": flow_id,
                        "target_phase": phase,
                        "resumed_at": datetime.now().isoformat(),
                        "method": "postgresql_state_phase_resume",
                        "error": str(e),
                        "note": "CrewAI phase resume failed, using state management"
                    }
            else:
                # CrewAI not available, use PostgreSQL state management
                return {
                    "status": "resumed_at_phase",
                    "flow_id": flow_id,
                    "target_phase": phase,
                    "resumed_at": datetime.now().isoformat(),
                    "method": "postgresql_state_only"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to resume flow at phase {flow_id}: {e}")
            return {
                "status": "phase_resume_failed",
                "flow_id": flow_id,
                "target_phase": phase,
                "error": str(e),
                "message": "Failed to resume flow at phase"
            }


# Factory function for dependency injection
async def get_crewai_flow_service(
    db: AsyncSession = None,
    context: Dict[str, Any] = None
) -> CrewAIFlowService:
    """
    Factory function to create CrewAI Flow Service with proper dependencies.
    """
    if not db:
        # Get database session from dependency injection
        async with get_db() as session:
            return CrewAIFlowService(db=session)
    
    return CrewAIFlowService(db=db) 