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
from app.models.discovery_asset import DiscoveryAsset

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
        
    async def _get_discovery_flow_service(self, context: Dict[str, Any]) -> DiscoveryFlowService:
        """Get or create discovery flow service with context."""
        if not self._discovery_flow_service:
            if not self.db:
                raise ValueError("Database session required for V2 Discovery Flow service")
            
            flow_repo = DiscoveryFlowRepository(self.db, context.get('client_account_id'))
            self._discovery_flow_service = DiscoveryFlowService(flow_repo)
        
        return self._discovery_flow_service
    


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
            existing_flow = await discovery_service.get_flow(flow_id)
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
                import_session_id=metadata.get('import_session_id') if metadata else None,
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
            flow = await discovery_service.get_flow(flow_id)
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
            result = await discovery_service.get_flow(flow_id)
            
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

    # Legacy compatibility methods (deprecated)
    async def get_flow_state_by_session(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: Legacy method for session-based flow lookup.
        Use get_flow_status(flow_id) instead.
        """
        logger.warning(f"⚠️ Deprecated method called: get_flow_state_by_session({session_id})")
        logger.warning("Use get_flow_status(flow_id) instead")
        
        # Treat session_id as flow_id for backward compatibility
        return await self.get_flow_status(session_id, context)

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