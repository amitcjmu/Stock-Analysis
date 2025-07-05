"""
Discovery orchestration service for coordinating CrewAI and PostgreSQL layers.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from .flow_coordinator import FlowCoordinator
from .compatibility_service import CompatibilityService

logger = logging.getLogger(__name__)

# Import handlers with fallbacks
try:
    from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
    FLOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    FLOW_MANAGEMENT_AVAILABLE = False
    FlowManagementHandler = None

try:
    from app.api.v1.discovery_handlers.crewai_execution import CrewAIExecutionHandler
    CREWAI_EXECUTION_AVAILABLE = True
except ImportError:
    CREWAI_EXECUTION_AVAILABLE = False
    CrewAIExecutionHandler = None


class DiscoveryOrchestrator:
    """
    Main orchestration service for unified discovery operations.
    
    Coordinates between CrewAI execution and PostgreSQL management layers
    to provide a unified discovery experience.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.flow_coordinator = FlowCoordinator(db, context)
        self.compatibility_service = CompatibilityService(db, context)
    
    async def initialize_discovery_flow(
        self,
        execution_mode: str = "hybrid",
        raw_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        data_import_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize unified discovery flow with hybrid CrewAI + PostgreSQL architecture.
        
        Args:
            execution_mode: 'crewai', 'database', or 'hybrid'
            raw_data: Optional raw data for analysis
            metadata: Optional metadata for the flow
            data_import_id: Optional existing data import ID
            
        Returns:
            Dictionary with flow initialization results
        """
        
        logger.info(f"🚀 Initializing unified discovery flow, mode: {execution_mode}")
        
        # Generate flow ID
        flow_id = f"flow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Initialize flow result structure
        flow_result = {
            "flow_id": flow_id,
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id,
            "user_id": self.context.user_id,
            "status": "initializing",
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "phases": {
                "data_import": False,
                "field_mapping": False,
                "data_cleansing": False,
                "asset_inventory": False,
                "dependency_analysis": False,
                "tech_debt_analysis": False
            },
            "crewai_status": "pending",
            "database_status": "pending",
            "agent_insights": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Initialize CrewAI execution if requested
        if execution_mode in ["crewai", "hybrid"]:
            crewai_result = await self._initialize_crewai_execution(
                flow_id, raw_data, metadata
            )
            flow_result["crewai_status"] = crewai_result.get("status", "failed")
            flow_result["agent_insights"] = crewai_result.get("agent_insights", [])
        
        # Initialize PostgreSQL management if requested
        if execution_mode in ["database", "hybrid"]:
            db_result = await self._initialize_database_management(
                flow_id, raw_data, metadata, data_import_id
            )
            flow_result["database_status"] = db_result.get("status", "failed")
            flow_result.update(db_result.get("flow_data", {}))
        
        # Update overall status
        flow_result["status"] = self._determine_overall_status(flow_result)
        if flow_result["status"] == "initialized":
            flow_result["current_phase"] = "data_import"
        
        logger.info(f"✅ Discovery flow initialized: {flow_id}")
        return flow_result
    
    async def get_discovery_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get unified discovery flow status from both CrewAI and PostgreSQL layers.
        """
        
        logger.info(f"🔍 Getting discovery flow status: {flow_id}")
        
        # Get status from both layers
        crewai_status = await self._get_crewai_status(flow_id)
        database_status = await self._get_database_status(flow_id)
        
        # Merge status information
        unified_status = await self._merge_status_information(
            flow_id, crewai_status, database_status
        )
        
        return unified_status
    
    async def execute_discovery_flow(
        self,
        flow_id: str,
        execution_mode: str = "hybrid",
        phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute discovery flow with specified mode and optional phase.
        """
        
        logger.info(f"🚀 Executing discovery flow: {flow_id}, mode: {execution_mode}")
        
        # Get current flow status
        current_status = await self.get_discovery_flow_status(flow_id)
        
        # Execute based on mode
        execution_result = {
            "flow_id": flow_id,
            "execution_mode": execution_mode,
            "started_at": datetime.now().isoformat(),
            "status": "executing"
        }
        
        if execution_mode in ["crewai", "hybrid"]:
            crewai_result = await self._execute_crewai_flow(flow_id, phase)
            execution_result["crewai_execution"] = crewai_result
        
        if execution_mode in ["database", "hybrid"]:
            db_result = await self._execute_database_flow(flow_id, phase)
            execution_result["database_execution"] = db_result
        
        # Update execution status
        execution_result["completed_at"] = datetime.now().isoformat()
        execution_result["status"] = "completed"
        
        logger.info(f"✅ Discovery flow execution completed: {flow_id}")
        return execution_result
    
    async def get_active_discovery_flows(
        self,
        limit: int = 50,
        include_completed: bool = False
    ) -> Dict[str, Any]:
        """Get list of active discovery flows for the current context."""
        
        logger.info(f"📋 Getting active discovery flows (limit: {limit})")
        
        # Get flows from both systems
        active_flows = []
        
        # Get from database management layer
        if FLOW_MANAGEMENT_AVAILABLE:
            db_flows = await self._get_database_flows(limit, include_completed)
            active_flows.extend(db_flows)
        
        # Get from CrewAI layer if available
        if CREWAI_EXECUTION_AVAILABLE:
            crewai_flows = await self._get_crewai_flows(limit, include_completed)
            # Merge with database flows (avoid duplicates)
            active_flows = self._merge_flow_lists(active_flows, crewai_flows)
        
        return {
            "flows": active_flows,
            "total_count": len(active_flows),
            "active_count": len([f for f in active_flows if f.get("status") != "completed"]),
            "context": {
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            }
        }
    
    async def _initialize_crewai_execution(
        self,
        flow_id: str,
        raw_data: Optional[List[Dict[str, Any]]],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Initialize CrewAI execution layer."""
        
        if not CREWAI_EXECUTION_AVAILABLE:
            logger.warning("⚠️ CrewAI execution not available")
            return {"status": "unavailable", "message": "CrewAI not available"}
        
        try:
            crewai_handler = CrewAIExecutionHandler(self.db, self.context)
            result = await crewai_handler.initialize_flow(
                flow_id=flow_id,
                raw_data=raw_data,
                metadata=metadata
            )
            logger.info("✅ CrewAI execution initialized")
            return {"status": "initialized", **result}
        except Exception as e:
            logger.warning(f"⚠️ CrewAI initialization failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _initialize_database_management(
        self,
        flow_id: str,
        raw_data: Optional[List[Dict[str, Any]]],
        metadata: Optional[Dict[str, Any]],
        data_import_id: Optional[str]
    ) -> Dict[str, Any]:
        """Initialize PostgreSQL management layer."""
        
        if not FLOW_MANAGEMENT_AVAILABLE:
            logger.warning("⚠️ Flow management not available")
            return {"status": "unavailable", "message": "Flow management not available"}
        
        try:
            flow_handler = FlowManagementHandler(self.db, self.context)
            result = await flow_handler.create_flow(
                flow_id=flow_id,
                raw_data=raw_data,
                metadata=metadata,
                data_import_id=data_import_id
            )
            logger.info("✅ PostgreSQL management initialized")
            return {"status": "initialized", "flow_data": result}
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _determine_overall_status(self, flow_result: Dict[str, Any]) -> str:
        """Determine overall flow status based on component statuses."""
        
        crewai_status = flow_result.get("crewai_status", "pending")
        database_status = flow_result.get("database_status", "pending")
        
        # If either system is initialized, consider the flow initialized
        if crewai_status == "initialized" or database_status == "initialized":
            return "initialized"
        elif crewai_status == "failed" and database_status == "failed":
            return "failed"
        else:
            return "initializing"
    
    async def _get_crewai_status(self, flow_id: str) -> Dict[str, Any]:
        """Get status from CrewAI execution layer."""
        
        if not CREWAI_EXECUTION_AVAILABLE:
            return {"available": False, "status": "unavailable"}
        
        try:
            crewai_handler = CrewAIExecutionHandler(self.db, self.context)
            status = await crewai_handler.get_flow_status(flow_id)
            return {"available": True, "status": "available", **status}
        except Exception as e:
            logger.warning(f"Failed to get CrewAI status: {e}")
            return {"available": True, "status": "error", "error": str(e)}
    
    async def _get_database_status(self, flow_id: str) -> Dict[str, Any]:
        """Get status from PostgreSQL management layer."""
        
        if not FLOW_MANAGEMENT_AVAILABLE:
            return {"available": False, "status": "unavailable"}
        
        try:
            flow_handler = FlowManagementHandler(self.db, self.context)
            status = await flow_handler.get_flow_status(flow_id)
            return {"available": True, "status": "available", **status}
        except Exception as e:
            logger.warning(f"Failed to get database status: {e}")
            return {"available": True, "status": "error", "error": str(e)}
    
    async def _merge_status_information(
        self,
        flow_id: str,
        crewai_status: Dict[str, Any],
        database_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge status information from both layers."""
        
        # Start with base flow information
        merged_status = {
            "flow_id": flow_id,
            "client_account_id": str(self.context.client_account_id),
            "engagement_id": str(self.context.engagement_id),
            "layers": {
                "crewai": crewai_status,
                "database": database_status
            }
        }
        
        # Use database status as primary source if available
        if database_status.get("available") and database_status.get("status") == "available":
            merged_status.update(database_status)
            # Overlay CrewAI insights
            if crewai_status.get("available"):
                merged_status["agent_insights"] = crewai_status.get("agent_insights", [])
                merged_status["crewai_status"] = crewai_status.get("execution_status", "unknown")
        elif crewai_status.get("available") and crewai_status.get("status") == "available":
            merged_status.update(crewai_status)
        
        return merged_status
    
    async def _execute_crewai_flow(self, flow_id: str, phase: Optional[str]) -> Dict[str, Any]:
        """Execute CrewAI flow."""
        
        if not CREWAI_EXECUTION_AVAILABLE:
            return {"status": "unavailable", "message": "CrewAI not available"}
        
        try:
            crewai_handler = CrewAIExecutionHandler(self.db, self.context)
            result = await crewai_handler.execute_flow(flow_id, phase)
            return {"status": "completed", **result}
        except Exception as e:
            logger.error(f"CrewAI execution failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_database_flow(self, flow_id: str, phase: Optional[str]) -> Dict[str, Any]:
        """Execute database flow."""
        
        if not FLOW_MANAGEMENT_AVAILABLE:
            return {"status": "unavailable", "message": "Flow management not available"}
        
        try:
            flow_handler = FlowManagementHandler(self.db, self.context)
            result = await flow_handler.execute_flow_phase(flow_id, phase)
            return {"status": "completed", **result}
        except Exception as e:
            logger.error(f"Database flow execution failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _get_database_flows(self, limit: int, include_completed: bool) -> List[Dict[str, Any]]:
        """Get flows from database management layer."""
        
        if not FLOW_MANAGEMENT_AVAILABLE:
            return []
        
        try:
            flow_handler = FlowManagementHandler(self.db, self.context)
            flows = await flow_handler.get_flows(limit, include_completed)
            return flows
        except Exception as e:
            logger.warning(f"Failed to get database flows: {e}")
            return []
    
    async def _get_crewai_flows(self, limit: int, include_completed: bool) -> List[Dict[str, Any]]:
        """Get flows from CrewAI layer."""
        
        if not CREWAI_EXECUTION_AVAILABLE:
            return []
        
        try:
            crewai_handler = CrewAIExecutionHandler(self.db, self.context)
            flows = await crewai_handler.get_flows(limit, include_completed)
            return flows
        except Exception as e:
            logger.warning(f"Failed to get CrewAI flows: {e}")
            return []
    
    def _merge_flow_lists(self, db_flows: List[Dict], crewai_flows: List[Dict]) -> List[Dict]:
        """Merge flow lists, avoiding duplicates."""
        
        # Create lookup of database flows by flow_id
        db_flow_ids = {flow.get("flow_id") for flow in db_flows}
        
        # Add CrewAI flows that aren't already in database flows
        merged_flows = db_flows.copy()
        for crewai_flow in crewai_flows:
            if crewai_flow.get("flow_id") not in db_flow_ids:
                merged_flows.append(crewai_flow)
        
        # Sort by creation time (most recent first)
        merged_flows.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return merged_flows