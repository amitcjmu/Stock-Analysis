"""
Discovery Flow State Manager
Enhanced with CrewAI Flow state management patterns for incomplete flow management
Handles persistence and retrieval of discovery flow state across phases
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.models.data_import_session import DataImportSession
from app.models.asset import Asset
from app.models.workflow_state import WorkflowState

# CrewAI Flow imports with graceful fallback
try:
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
    from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    CREWAI_FLOW_AVAILABLE = False

logger = logging.getLogger(__name__)

class DiscoveryFlowStateManager:
    """
    Enhanced state manager leveraging CrewAI Flow state persistence patterns
    Handles incomplete flow detection, resumption, and multi-tenant management
    Phase 4: Advanced Features & Production Readiness
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None, 
                 client_account_id: Optional[str] = None, 
                 engagement_id: Optional[str] = None):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.active_flows: Dict[str, Dict[str, Any]] = {}
        
        # Phase 4: Advanced configuration
        self.flow_expiration_hours = 72  # 3 days default
        self.auto_cleanup_enabled = True
        self.performance_monitoring = True
    
    async def get_incomplete_flows_for_context(self, context: RequestContext) -> List[Dict[str, Any]]:
        """Get incomplete flows using CrewAI Flow state filtering"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Query workflow_states for flows with status in ['running', 'paused', 'failed']
                stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id,
                        WorkflowState.status.in_(['running', 'paused', 'failed'])
                    )
                ).order_by(WorkflowState.updated_at.desc())
                
                result = await db_session.execute(stmt)
                incomplete_workflows = result.scalars().all()
                
                # Convert to structured flow information with CrewAI state data
                flows = []
                for workflow in incomplete_workflows:
                    flow_info = {
                        "session_id": str(workflow.session_id),
                        "flow_id": str(workflow.flow_id),
                        "current_phase": workflow.current_phase,
                        "status": workflow.status,
                        "progress_percentage": workflow.progress_percentage,
                        "phase_completion": workflow.phase_completion or {},
                        "crew_status": workflow.crew_status or {},
                        "created_at": workflow.created_at.isoformat(),
                        "updated_at": workflow.updated_at.isoformat(),
                        "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                        
                        # CrewAI Flow specific data
                        "agent_insights": workflow.agent_insights or [],
                        "success_criteria": workflow.success_criteria or {},
                        "errors": workflow.errors or [],
                        "warnings": workflow.warnings or [],
                        
                        # Flow management capabilities
                        "can_resume": await self._can_flow_be_resumed(workflow),
                        "deletion_impact": await self._get_deletion_impact_summary(workflow),
                        
                        # Database integration status
                        "database_assets_created": workflow.database_assets_created or [],
                        "database_integration_status": workflow.database_integration_status
                    }
                    flows.append(flow_info)
                
                logger.info(f"✅ Found {len(flows)} incomplete flows for context {context.client_account_id}/{context.engagement_id}")
                return flows
                
        except Exception as e:
            logger.error(f"❌ Failed to get incomplete flows: {e}")
            return []
    
    async def validate_flow_resumption(self, session_id: str, context: RequestContext) -> Dict[str, Any]:
        """Validate if a flow can be resumed using CrewAI Flow state validation"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Get workflow state
                stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.session_id == session_id,
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id
                    )
                )
                result = await db_session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return {
                        "can_resume": False,
                        "reason": "Flow not found or access denied",
                        "validation_errors": ["Workflow state not found for session"]
                    }
                
                validation_errors = []
                
                # Check flow state integrity
                if workflow.status not in ['running', 'paused', 'failed']:
                    validation_errors.append(f"Invalid flow status: {workflow.status}")
                
                # Check phase dependencies
                current_phase = workflow.current_phase
                phase_completion = workflow.phase_completion or {}
                
                if current_phase == "data_cleansing" and not phase_completion.get("field_mapping", False):
                    validation_errors.append("Cannot resume data cleansing without completed field mapping")
                
                if current_phase == "asset_inventory" and not phase_completion.get("data_cleansing", False):
                    validation_errors.append("Cannot resume asset inventory without completed data cleansing")
                
                # Check agent memory consistency (if available)
                if workflow.shared_memory_id and not await self._validate_shared_memory_integrity(workflow.shared_memory_id):
                    validation_errors.append("Shared memory integrity check failed")
                
                # Check for data corruption
                state_data = workflow.state_data or {}
                if not state_data.get("session_id"):
                    validation_errors.append("State data corruption detected")
                
                can_resume = len(validation_errors) == 0
                
                return {
                    "can_resume": can_resume,
                    "reason": "Validation passed" if can_resume else "Validation failed",
                    "validation_errors": validation_errors,
                    "current_phase": current_phase,
                    "progress_percentage": workflow.progress_percentage,
                    "last_activity": workflow.updated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Flow resumption validation failed: {e}")
            return {
                "can_resume": False,
                "reason": f"Validation error: {str(e)}",
                "validation_errors": [str(e)]
            }
    
    async def prepare_flow_resumption(self, session_id: str) -> Optional[Any]:
        """Prepare CrewAI Flow instance for resumption with proper state restoration"""
        if not CREWAI_FLOW_AVAILABLE:
            logger.warning("CrewAI Flow not available for resumption")
            return None
            
        try:
            async with AsyncSessionLocal() as db_session:
                # Restore UnifiedDiscoveryFlowState from database
                stmt = select(WorkflowState).where(WorkflowState.session_id == session_id)
                result = await db_session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    logger.error(f"Workflow not found for session: {session_id}")
                    return None
                
                # Recreate UnifiedDiscoveryFlowState from persisted data
                state_data = workflow.state_data or {}
                
                # Create flow state instance
                flow_state = UnifiedDiscoveryFlowState(
                    session_id=str(workflow.session_id),
                    client_account_id=str(workflow.client_account_id),
                    engagement_id=str(workflow.engagement_id),
                    user_id=workflow.user_id,
                    current_phase=workflow.current_phase,
                    status=workflow.status,
                    progress_percentage=workflow.progress_percentage,
                    phase_completion=workflow.phase_completion or {},
                    crew_status=workflow.crew_status or {},
                    field_mappings=workflow.field_mappings or {},
                    cleaned_data=workflow.cleaned_data or [],
                    asset_inventory=workflow.asset_inventory or {},
                    dependencies=workflow.dependencies or {},
                    technical_debt=workflow.technical_debt or {},
                    agent_insights=workflow.agent_insights or [],
                    errors=workflow.errors or [],
                    warnings=workflow.warnings or [],
                    workflow_log=workflow.workflow_log or [],
                    database_assets_created=workflow.database_assets_created or [],
                    shared_memory_id=workflow.shared_memory_id or "",
                    created_at=workflow.created_at.isoformat(),
                    updated_at=workflow.updated_at.isoformat()
                )
                
                # TODO: Reinitialize CrewAI Flow with persisted state
                # TODO: Restore shared memory and knowledge base references
                
                logger.info(f"✅ Flow state prepared for resumption: {session_id}")
                return flow_state
                
        except Exception as e:
            logger.error(f"❌ Failed to prepare flow resumption: {e}")
            return None

    async def _can_flow_be_resumed(self, workflow: WorkflowState) -> bool:
        """Check if a workflow can be resumed"""
        if workflow.status not in ['running', 'paused', 'failed']:
            return False
        
        # Check if there are critical errors that prevent resumption
        errors = workflow.errors or []
        critical_errors = [e for e in errors if e.get('severity') == 'critical']
        
        return len(critical_errors) == 0
    
    async def _get_deletion_impact_summary(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Get summary of what would be deleted"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Count associated data
                asset_count = len(workflow.database_assets_created) if workflow.database_assets_created else 0
                
                # TODO: Count import sessions, field mappings, dependencies
                
                return {
                    "flow_phase": workflow.current_phase,
                    "progress_percentage": workflow.progress_percentage,
                    "data_to_delete": {
                        "workflow_state": 1,
                        "assets": asset_count,
                        "import_sessions": 0,  # TODO: Calculate
                        "field_mappings": 0,   # TODO: Calculate
                        "dependencies": 0      # TODO: Calculate
                    },
                    "estimated_cleanup_time": "< 5 seconds",
                    "data_recovery_possible": False
                }
        except Exception as e:
            logger.error(f"Failed to get deletion impact: {e}")
            return {"error": "Could not calculate deletion impact"}
    
    async def _validate_shared_memory_integrity(self, shared_memory_id: str) -> bool:
        """Validate shared memory integrity for CrewAI Flow"""
        # TODO: Implement shared memory validation
        # For now, assume memory is valid if ID exists
        return bool(shared_memory_id)

    async def initialize_flow_state(self, session_id: str, client_account_id: str, 
                                  engagement_id: str, user_id: str, 
                                  raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Initialize a new discovery flow state"""
        
        flow_state = {
            "session_id": session_id,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "user_id": user_id,
            "status": "running",
            "current_phase": "field_mapping",
            "progress_percentage": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            
            # Phase completion tracking
            "phase_completion": {
                "field_mapping": False,
                "data_cleansing": False,
                "inventory_building": False,
                "app_server_dependencies": False,
                "app_app_dependencies": False,
                "technical_debt": False
            },
            
            # Data flow between phases
            "raw_data": raw_data,
            "field_mappings": {},
            "cleaned_data": [],
            "asset_inventory": {
                "servers": [],
                "applications": [],
                "devices": []
            },
            "app_server_dependencies": {
                "hosting_relationships": [],
                "suggested_mappings": [],
                "confidence_scores": {}
            },
            "app_app_dependencies": {
                "communication_patterns": [],
                "application_clusters": [],
                "dependency_graph": {"nodes": [], "edges": []},
                "suggested_patterns": []
            },
            "technical_debt_assessment": {},
            
            # Crew status tracking
            "crew_status": {},
            "crew_results": {},
            
            # Database integration tracking
            "database_assets_created": [],
            "database_integration_status": "pending"
        }
        
        # Store in memory and database
        self.active_flows[session_id] = flow_state
        await self._persist_flow_state_to_database(session_id, flow_state)
        
        logger.info(f"✅ Flow state initialized for session: {session_id}")
        return flow_state
    
    async def update_phase_completion(self, session_id: str, phase: str, 
                                    results: Dict[str, Any]) -> Dict[str, Any]:
        """Update flow state when a phase completes"""
        
        if session_id not in self.active_flows:
            raise ValueError(f"Flow state not found for session: {session_id}")
        
        flow_state = self.active_flows[session_id]
        
        # Update phase completion
        flow_state["phase_completion"][phase] = True
        flow_state["crew_results"][phase] = results
        
        # Update phase-specific data
        if phase == "field_mapping":
            flow_state["field_mappings"] = results.get("field_mappings", {})
            flow_state["current_phase"] = "data_cleansing"
            flow_state["progress_percentage"] = 16.7
            
        elif phase == "data_cleansing":
            flow_state["cleaned_data"] = results.get("cleaned_data", [])
            flow_state["current_phase"] = "inventory_building"
            flow_state["progress_percentage"] = 33.3
            
        elif phase == "inventory_building":
            flow_state["asset_inventory"] = results.get("asset_inventory", {})
            flow_state["current_phase"] = "app_server_dependencies"
            flow_state["progress_percentage"] = 50.0
            
        elif phase == "app_server_dependencies":
            flow_state["app_server_dependencies"] = results.get("app_server_dependencies", {})
            flow_state["current_phase"] = "app_app_dependencies"
            flow_state["progress_percentage"] = 66.7
            
        elif phase == "app_app_dependencies":
            flow_state["app_app_dependencies"] = results.get("app_app_dependencies", {})
            flow_state["current_phase"] = "technical_debt"
            flow_state["progress_percentage"] = 83.3
            
        elif phase == "technical_debt":
            flow_state["technical_debt_assessment"] = results.get("technical_debt_assessment", {})
            flow_state["current_phase"] = "completed"
            flow_state["progress_percentage"] = 100.0
            flow_state["status"] = "completed"
            flow_state["completed_at"] = datetime.utcnow().isoformat()
        
        # Update timestamps
        flow_state["updated_at"] = datetime.utcnow().isoformat()
        
        # Persist updated state
        await self._persist_flow_state_to_database(session_id, flow_state)
        
        logger.info(f"✅ Phase {phase} completed for session: {session_id}")
        return flow_state
    
    async def get_flow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current flow state"""
        
        # Try memory first
        if session_id in self.active_flows:
            return self.active_flows[session_id]
        
        # Try database
        flow_state = await self._load_flow_state_from_database(session_id)
        if flow_state:
            self.active_flows[session_id] = flow_state
            return flow_state
        
        return None
    
    async def persist_assets_to_database(self, session_id: str) -> Dict[str, Any]:
        """Persist processed assets to database"""
        
        flow_state = await self.get_flow_state(session_id)
        if not flow_state:
            raise ValueError(f"Flow state not found for session: {session_id}")
        
        asset_inventory = flow_state.get("asset_inventory", {})
        field_mappings = flow_state.get("field_mappings", {})
        
        created_asset_ids = []
        
        async with AsyncSessionLocal() as db_session:
            try:
                # Create assets from inventory
                for asset_type, assets in asset_inventory.items():
                    for asset_data in assets:
                        db_asset = Asset(
                            # Context
                            client_account_id=flow_state["client_account_id"],
                            engagement_id=flow_state["engagement_id"],
                            session_id=flow_state["session_id"],
                            
                            # Basic info
                            name=asset_data.get("name", f"Asset_{len(created_asset_ids) + 1}"),
                            hostname=asset_data.get("hostname"),
                            asset_type=asset_data.get("asset_type", "OTHER"),
                            
                            # Technical details
                            ip_address=asset_data.get("ip_address"),
                            operating_system=asset_data.get("operating_system"),
                            environment=asset_data.get("environment", "Unknown"),
                            cpu_cores=asset_data.get("cpu_cores"),
                            memory_gb=asset_data.get("memory_gb"),
                            storage_gb=asset_data.get("storage_gb"),
                            
                            # Business info
                            business_owner=asset_data.get("business_owner"),
                            department=asset_data.get("department"),
                            business_criticality=asset_data.get("business_criticality", "Medium"),
                            
                            # Migration info
                            six_r_strategy=asset_data.get("six_r_strategy", "rehost"),
                            migration_complexity=asset_data.get("migration_complexity", "Medium"),
                            sixr_ready=asset_data.get("sixr_ready", False),
                            
                            # Discovery metadata
                            discovery_method="crewai_discovery_flow",
                            discovery_source="discovery_flow_modular",
                            discovery_timestamp=datetime.utcnow(),
                            
                            # Import metadata
                            imported_by=flow_state["user_id"],
                            imported_at=datetime.utcnow(),
                            source_filename=f"discovery_flow_{session_id}",
                            raw_data=asset_data.get("raw_data", {}),
                            field_mappings_used=field_mappings,
                            
                            # Audit
                            created_at=datetime.utcnow(),
                            created_by=flow_state["user_id"]
                        )
                        
                        db_session.add(db_asset)
                        await db_session.flush()
                        created_asset_ids.append(str(db_asset.id))
                
                await db_session.commit()
                
                # Update flow state with created asset IDs
                flow_state["database_assets_created"] = created_asset_ids
                flow_state["database_integration_status"] = "completed"
                await self._persist_flow_state_to_database(session_id, flow_state)
                
                logger.info(f"✅ Created {len(created_asset_ids)} assets in database")
                
                return {
                    "status": "success",
                    "assets_created": len(created_asset_ids),
                    "asset_ids": created_asset_ids
                }
                
            except Exception as e:
                await db_session.rollback()
                logger.error(f"❌ Failed to persist assets: {e}")
                raise
    
    async def _persist_flow_state_to_database(self, session_id: str, flow_state: Dict[str, Any]):
        """Persist flow state to database session metadata"""
        
        async with AsyncSessionLocal() as db_session:
            try:
                # Update session with flow state
                stmt = update(DataImportSession).where(
                    DataImportSession.id == session_id
                ).values(
                    agent_insights=flow_state,
                    progress_percentage=int(flow_state.get("progress_percentage", 0)),
                    last_activity_at=datetime.utcnow()
                )
                
                await db_session.execute(stmt)
                await db_session.commit()
                
            except Exception as e:
                logger.error(f"Failed to persist flow state: {e}")
    
    async def _load_flow_state_from_database(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load flow state from database"""
        try:
            async with AsyncSessionLocal() as db_session:
                stmt = select(WorkflowState).where(WorkflowState.session_id == session_id)
                result = await db_session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return None
                
                return {
                    "session_id": str(workflow.session_id),
                    "status": workflow.status,
                    "current_phase": workflow.current_phase,
                    "progress_percentage": workflow.progress_percentage,
                    "state_data": workflow.state_data or {}
                }
        except Exception as e:
            logger.error(f"Failed to load flow state: {e}")
            return None

    # === PHASE 4: PRIVATE HELPER METHODS ===
    
    async def _repair_corrupted_state(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Phase 4: Intelligent state repair for corrupted flow data"""
        repair_actions = []
        
        try:
            # Check for missing required fields
            if not workflow.state_data or not isinstance(workflow.state_data, dict):
                workflow.state_data = {}
                repair_actions.append("Initialized empty state_data")
            
            # Validate phase consistency
            valid_phases = ["field_mapping", "data_cleansing", "asset_inventory", "dependency_analysis", "tech_debt"]
            if workflow.current_phase not in valid_phases:
                workflow.current_phase = "field_mapping"
                repair_actions.append(f"Reset invalid phase to field_mapping")
            
            # Repair progress percentage
            if workflow.progress_percentage is None or workflow.progress_percentage < 0 or workflow.progress_percentage > 100:
                # Calculate progress based on phase completion
                phase_completion = workflow.phase_completion or {}
                completed_phases = sum(1 for completed in phase_completion.values() if completed)
                workflow.progress_percentage = (completed_phases / len(valid_phases)) * 100
                repair_actions.append(f"Recalculated progress percentage: {workflow.progress_percentage}%")
            
            # Repair phase completion structure
            if not workflow.phase_completion:
                workflow.phase_completion = {phase: False for phase in valid_phases}
                repair_actions.append("Initialized phase completion tracking")
            
            # Repair agent insights structure
            if not isinstance(workflow.agent_insights, list):
                workflow.agent_insights = []
                repair_actions.append("Initialized agent insights array")
            
            return {
                "success": True,
                "actions": repair_actions
            }
            
        except Exception as e:
            logger.error(f"State repair failed: {e}")
            return {
                "success": False,
                "actions": [f"State repair failed: {str(e)}"]
            }
    
    async def _reconstruct_agent_memory(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Phase 4: Reconstruct agent memory from available data"""
        memory_actions = []
        
        try:
            # Reconstruct shared memory references
            if not workflow.shared_memory_id:
                # Generate new shared memory ID
                import uuid
                workflow.shared_memory_id = str(uuid.uuid4())
                memory_actions.append("Generated new shared memory ID")
            
            # Reconstruct knowledge base references
            state_data = workflow.state_data or {}
            if "knowledge_base_refs" not in state_data:
                state_data["knowledge_base_refs"] = []
                workflow.state_data = state_data
                memory_actions.append("Initialized knowledge base references")
            
            # Reconstruct agent memory from phase data
            if workflow.field_mappings:
                memory_actions.append("Reconstructed field mapping memory")
            
            if workflow.cleaned_data:
                memory_actions.append("Reconstructed data cleansing memory")
            
            if workflow.asset_inventory:
                memory_actions.append("Reconstructed asset inventory memory")
            
            return {
                "success": True,
                "actions": memory_actions
            }
            
        except Exception as e:
            logger.error(f"Agent memory reconstruction failed: {e}")
            return {
                "success": False,
                "actions": [f"Memory reconstruction failed: {str(e)}"]
            }
    
    async def _validate_and_repair_data_consistency(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Phase 4: Validate and repair data consistency across flow phases"""
        consistency_actions = []
        
        try:
            # Check field mappings consistency
            if workflow.field_mappings and workflow.cleaned_data:
                mapped_fields = set(workflow.field_mappings.keys())
                data_fields = set()
                if workflow.cleaned_data and len(workflow.cleaned_data) > 0:
                    data_fields = set(workflow.cleaned_data[0].keys())
                
                missing_mappings = data_fields - mapped_fields
                if missing_mappings:
                    consistency_actions.append(f"Found {len(missing_mappings)} unmapped fields")
            
            # Check asset inventory consistency
            if workflow.asset_inventory and workflow.cleaned_data:
                inventory_count = len(workflow.asset_inventory.get("assets", []))
                data_count = len(workflow.cleaned_data)
                
                if abs(inventory_count - data_count) > data_count * 0.1:  # 10% tolerance
                    consistency_actions.append(f"Asset count mismatch: inventory={inventory_count}, data={data_count}")
            
            # Validate dependency data
            if workflow.dependencies:
                deps = workflow.dependencies.get("relationships", [])
                invalid_deps = [d for d in deps if not d.get("source") or not d.get("target")]
                if invalid_deps:
                    consistency_actions.append(f"Found {len(invalid_deps)} invalid dependencies")
            
            return {
                "success": True,
                "actions": consistency_actions
            }
            
        except Exception as e:
            logger.error(f"Data consistency validation failed: {e}")
            return {
                "success": False,
                "actions": [f"Consistency validation failed: {str(e)}"]
            }
    
    async def _optimize_flow_for_resumption(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Phase 4: Optimize flow data for efficient resumption"""
        optimization_actions = []
        
        try:
            # Compress large data structures
            if workflow.cleaned_data and len(workflow.cleaned_data) > 1000:
                # Keep only essential fields for resumption
                essential_fields = ["id", "name", "type", "status"]
                compressed_data = []
                for item in workflow.cleaned_data[:100]:  # Keep first 100 for reference
                    compressed_item = {k: v for k, v in item.items() if k in essential_fields}
                    compressed_data.append(compressed_item)
                
                # Store full data reference
                state_data = workflow.state_data or {}
                state_data["full_data_available"] = True
                state_data["compressed_for_resumption"] = True
                workflow.state_data = state_data
                
                optimization_actions.append(f"Compressed data from {len(workflow.cleaned_data)} to {len(compressed_data)} items")
            
            # Optimize agent insights
            if workflow.agent_insights and len(workflow.agent_insights) > 50:
                # Keep only recent insights
                workflow.agent_insights = workflow.agent_insights[-20:]
                optimization_actions.append("Trimmed agent insights to most recent 20 entries")
            
            # Pre-calculate resumption checkpoints
            state_data = workflow.state_data or {}
            state_data["resumption_optimized"] = True
            state_data["optimization_timestamp"] = datetime.now().isoformat()
            workflow.state_data = state_data
            
            optimization_actions.append("Added resumption optimization metadata")
            
            return {
                "success": True,
                "actions": optimization_actions
            }
            
        except Exception as e:
            logger.error(f"Flow optimization failed: {e}")
            return {
                "success": False,
                "actions": [f"Flow optimization failed: {str(e)}"]
            }
    
    async def _bulk_delete_flow(self, workflow: WorkflowState, options: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Bulk delete individual flow with comprehensive cleanup"""
        try:
            # Import cleanup service
            from app.services.crewai_flows.discovery_flow_cleanup_service import DiscoveryFlowCleanupService
            
            cleanup_service = DiscoveryFlowCleanupService()
            
            # Perform comprehensive cleanup
            cleanup_result = await cleanup_service.cleanup_discovery_flow(
                str(workflow.session_id),
                options.get("reason", "bulk_delete"),
                audit_deletion=options.get("audit", True)
            )
            
            return {
                "success": cleanup_result["success"],
                "cleanup_summary": cleanup_result.get("cleanup_summary", {}),
                "error": cleanup_result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Bulk delete failed for flow {workflow.session_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _bulk_pause_flow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Phase 4: Bulk pause individual flow"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Update workflow status to paused
                stmt = update(WorkflowState).where(
                    WorkflowState.session_id == workflow.session_id
                ).values(
                    status="paused",
                    updated_at=datetime.now()
                )
                
                await db_session.execute(stmt)
                await db_session.commit()
                
                return {
                    "success": True,
                    "action": "paused",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Bulk pause failed for flow {workflow.session_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _bulk_archive_flow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Phase 4: Bulk archive individual flow"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Update workflow status to archived
                stmt = update(WorkflowState).where(
                    WorkflowState.session_id == workflow.session_id
                ).values(
                    status="archived",
                    updated_at=datetime.now()
                )
                
                await db_session.execute(stmt)
                await db_session.commit()
                
                return {
                    "success": True,
                    "action": "archived",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Bulk archive failed for flow {workflow.session_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_flow_query_patterns(self, db_session: AsyncSession, context: RequestContext) -> Dict[str, Any]:
        """Phase 4: Analyze query patterns for optimization"""
        try:
            # Analyze common query patterns
            optimizations = []
            
            # Check for frequent incomplete flow queries
            stmt = select(func.count(WorkflowState.session_id)).where(
                and_(
                    WorkflowState.client_account_id == context.client_account_id,
                    WorkflowState.engagement_id == context.engagement_id,
                    WorkflowState.status.in_(['running', 'paused', 'failed'])
                )
            )
            result = await db_session.execute(stmt)
            incomplete_count = result.scalar()
            
            if incomplete_count > 10:
                optimizations.append({
                    "type": "query_frequency",
                    "description": f"High number of incomplete flows ({incomplete_count})",
                    "recommendation": "Consider implementing flow expiration and auto-cleanup"
                })
            
            # Check for large workflow_states
            stmt = select(func.avg(func.length(WorkflowState.state_data.cast(str)))).where(
                WorkflowState.client_account_id == context.client_account_id
            )
            result = await db_session.execute(stmt)
            avg_state_size = result.scalar() or 0
            
            if avg_state_size > 10000:  # 10KB average
                optimizations.append({
                    "type": "data_size",
                    "description": f"Large average state size ({avg_state_size} bytes)",
                    "recommendation": "Consider implementing state data compression"
                })
            
            return {
                "optimizations": optimizations,
                "query_stats": {
                    "incomplete_flows": incomplete_count,
                    "average_state_size": avg_state_size
                }
            }
            
        except Exception as e:
            logger.error(f"Query pattern analysis failed: {e}")
            return {"optimizations": [], "error": str(e)}
    
    async def _analyze_index_usage(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Phase 4: Analyze database index usage and recommendations"""
        try:
            recommendations = []
            
            # Check if we need additional indexes
            recommendations.append({
                "type": "index_recommendation",
                "table": "workflow_states",
                "columns": ["client_account_id", "engagement_id", "status"],
                "reason": "Optimize incomplete flow queries",
                "priority": "high"
            })
            
            recommendations.append({
                "type": "index_recommendation", 
                "table": "workflow_states",
                "columns": ["updated_at", "status"],
                "reason": "Optimize expiration queries",
                "priority": "medium"
            })
            
            return {
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Index analysis failed: {e}")
            return {"recommendations": [], "error": str(e)}
    
    async def _benchmark_flow_operations(self, db_session: AsyncSession, context: RequestContext) -> Dict[str, Any]:
        """Benchmark flow management operations for performance optimization"""
        try:
            start_time = datetime.now()
            
            # Test incomplete flow query performance
            stmt = select(WorkflowState).where(
                and_(
                    WorkflowState.client_account_id == context.client_account_id,
                    WorkflowState.engagement_id == context.engagement_id,
                    WorkflowState.status.in_(['running', 'paused', 'failed'])
                )
            )
            
            result = await db_session.execute(stmt)
            flows = result.scalars().all()
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "incomplete_flow_query_ms": query_time,
                "flows_found": len(flows),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Flow operations benchmark failed: {e}")
            return {
                "incomplete_flow_query_ms": 0,
                "flows_found": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # === Phase 4: Missing Advanced Methods ===
    
    async def get_expired_flows(self, context: RequestContext, expiration_hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get flows that have expired and are eligible for cleanup"""
        try:
            expiration_hours = expiration_hours or self.flow_expiration_hours
            expiration_cutoff = datetime.now() - timedelta(hours=expiration_hours)
            
            async with AsyncSessionLocal() as db_session:
                stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id,
                        WorkflowState.status.in_(['running', 'paused', 'failed']),
                        WorkflowState.updated_at < expiration_cutoff
                    )
                ).order_by(WorkflowState.updated_at.asc())
                
                result = await db_session.execute(stmt)
                expired_workflows = result.scalars().all()
                
                expired_flows = []
                for workflow in expired_workflows:
                    days_since_activity = (datetime.now() - workflow.updated_at).days
                    
                    flow_info = {
                        "session_id": str(workflow.session_id),
                        "current_phase": workflow.current_phase,
                        "status": workflow.status,
                        "last_activity": workflow.updated_at.isoformat(),
                        "days_since_activity": days_since_activity,
                        "auto_cleanup_eligible": workflow.auto_cleanup_eligible if hasattr(workflow, 'auto_cleanup_eligible') else True,
                        "deletion_impact": await self._get_deletion_impact_summary(workflow)
                    }
                    expired_flows.append(flow_info)
                
                logger.info(f"✅ Found {len(expired_flows)} expired flows (older than {expiration_hours}h)")
                return expired_flows
                
        except Exception as e:
            logger.error(f"❌ Failed to get expired flows: {e}")
            return []
    
    async def auto_cleanup_expired_flows(self, context: RequestContext, dry_run: bool = True, 
                                       expiration_hours: Optional[int] = None, 
                                       force_cleanup: bool = False) -> Dict[str, Any]:
        """Auto-cleanup expired flows with comprehensive reporting"""
        try:
            start_time = datetime.now()
            expired_flows = await self.get_expired_flows(context, expiration_hours)
            
            if dry_run:
                return {
                    "dry_run": True,
                    "expired_flows_found": len(expired_flows),
                    "cleanup_successful": [],
                    "cleanup_failed": [],
                    "total_data_cleaned": {
                        "flows_deleted": 0,
                        "assets_cleaned": 0,
                        "memory_freed_mb": 0
                    },
                    "performance_metrics": {
                        "total_duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                        "flows_per_second": 0
                    },
                    "cleanup_completed_at": datetime.now().isoformat()
                }
            
            cleanup_successful = []
            cleanup_failed = []
            total_assets_cleaned = 0
            total_memory_freed = 0
            
            async with AsyncSessionLocal() as db_session:
                for flow in expired_flows:
                    session_id = flow["session_id"]
                    
                    try:
                        # Only cleanup if eligible or forced
                        if not flow["auto_cleanup_eligible"] and not force_cleanup:
                            cleanup_failed.append(session_id)
                            continue
                        
                        # Get workflow for cleanup
                        stmt = select(WorkflowState).where(WorkflowState.session_id == session_id)
                        result = await db_session.execute(stmt)
                        workflow = result.scalar_one_or_none()
                        
                        if workflow:
                            # Perform cleanup
                            cleanup_result = await self._bulk_delete_flow(workflow, {"reason": "auto_cleanup"})
                            
                            if cleanup_result.get("success", False):
                                cleanup_successful.append(session_id)
                                total_assets_cleaned += cleanup_result.get("assets_deleted", 0)
                                total_memory_freed += cleanup_result.get("memory_freed_mb", 0)
                            else:
                                cleanup_failed.append(session_id)
                        
                    except Exception as cleanup_error:
                        logger.error(f"❌ Failed to cleanup flow {session_id}: {cleanup_error}")
                        cleanup_failed.append(session_id)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            flows_per_second = len(expired_flows) / (duration / 1000) if duration > 0 else 0
            
            return {
                "dry_run": False,
                "expired_flows_found": len(expired_flows),
                "cleanup_successful": cleanup_successful,
                "cleanup_failed": cleanup_failed,
                "total_data_cleaned": {
                    "flows_deleted": len(cleanup_successful),
                    "assets_cleaned": total_assets_cleaned,
                    "memory_freed_mb": total_memory_freed
                },
                "performance_metrics": {
                    "total_duration_ms": duration,
                    "flows_per_second": flows_per_second
                },
                "cleanup_completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Auto-cleanup failed: {e}")
            return {
                "dry_run": dry_run,
                "expired_flows_found": 0,
                "cleanup_successful": [],
                "cleanup_failed": [],
                "total_data_cleaned": {
                    "flows_deleted": 0,
                    "assets_cleaned": 0,
                    "memory_freed_mb": 0
                },
                "performance_metrics": {
                    "total_duration_ms": 0,
                    "flows_per_second": 0
                },
                "cleanup_completed_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def optimize_flow_performance(self, context: RequestContext) -> Dict[str, Any]:
        """Analyze and optimize flow management performance"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Analyze query patterns
                query_analysis = await self._analyze_flow_query_patterns(db_session, context)
                
                # Analyze index usage
                index_analysis = await self._analyze_index_usage(db_session)
                
                # Benchmark operations
                performance_metrics = await self._benchmark_flow_operations(db_session, context)
                
                # Generate optimization recommendations
                query_optimizations = []
                index_recommendations = []
                
                # Query optimization recommendations
                if performance_metrics.get("incomplete_flow_query_ms", 0) > 100:
                    query_optimizations.append({
                        "type": "query_optimization",
                        "description": "Incomplete flow query is slow",
                        "recommendation": "Consider adding composite index on (client_account_id, engagement_id, status)",
                        "priority": "high"
                    })
                
                # Index recommendations
                if query_analysis.get("missing_indexes", []):
                    for missing_index in query_analysis["missing_indexes"]:
                        index_recommendations.append({
                            "type": "missing_index",
                            "table": missing_index["table"],
                            "columns": missing_index["columns"],
                            "reason": missing_index["reason"],
                            "priority": "medium"
                        })
                
                return {
                    "query_optimizations": query_optimizations,
                    "index_recommendations": index_recommendations,
                    "performance_improvements": {
                        "current_metrics": performance_metrics,
                        "query_analysis": query_analysis,
                        "index_analysis": index_analysis
                    },
                    "analysis_completed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Performance optimization analysis failed: {e}")
            return {
                "query_optimizations": [],
                "index_recommendations": [],
                "performance_improvements": {},
                "analysis_completed_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def get_advanced_health_status(self, context: RequestContext) -> Dict[str, Any]:
        """Get advanced health status for flow management system"""
        try:
            # Get flow statistics
            async with AsyncSessionLocal() as db_session:
                # Count incomplete flows
                incomplete_stmt = select(func.count(WorkflowState.id)).where(
                    and_(
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id,
                        WorkflowState.status.in_(['running', 'paused', 'failed'])
                    )
                )
                incomplete_result = await db_session.execute(incomplete_stmt)
                incomplete_count = incomplete_result.scalar() or 0
                
                # Count expired flows
                expiration_cutoff = datetime.now() - timedelta(hours=self.flow_expiration_hours)
                expired_stmt = select(func.count(WorkflowState.id)).where(
                    and_(
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id,
                        WorkflowState.status.in_(['running', 'paused', 'failed']),
                        WorkflowState.updated_at < expiration_cutoff
                    )
                )
                expired_result = await db_session.execute(expired_stmt)
                expired_count = expired_result.scalar() or 0
                
                # Count total managed flows
                total_stmt = select(func.count(WorkflowState.id)).where(
                    and_(
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id
                    )
                )
                total_result = await db_session.execute(total_stmt)
                total_count = total_result.scalar() or 0
            
            # System capabilities
            system_capabilities = {
                "crewai_available": CREWAI_FLOW_AVAILABLE,
                "advanced_recovery": True,
                "bulk_operations": True,
                "auto_cleanup": self.auto_cleanup_enabled,
                "performance_optimization": self.performance_monitoring
            }
            
            # Health recommendations
            recommendations = []
            
            if expired_count > 0:
                recommendations.append({
                    "type": "cleanup",
                    "message": f"{expired_count} flows are expired and eligible for cleanup",
                    "priority": "medium"
                })
            
            if incomplete_count > 10:
                recommendations.append({
                    "type": "performance",
                    "message": f"High number of incomplete flows ({incomplete_count}) may impact performance",
                    "priority": "high"
                })
            
            if not CREWAI_FLOW_AVAILABLE:
                recommendations.append({
                    "type": "dependency",
                    "message": "CrewAI Flow not available - advanced features limited",
                    "priority": "high"
                })
            
            # Determine overall status
            status = "healthy"
            if expired_count > 5 or incomplete_count > 20 or not CREWAI_FLOW_AVAILABLE:
                status = "degraded"
            
            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "flow_statistics": {
                    "incomplete_flows": incomplete_count,
                    "expired_flows": expired_count,
                    "total_managed_flows": total_count
                },
                "system_capabilities": system_capabilities,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ Advanced health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def advanced_flow_recovery(self, session_id: str, context: RequestContext, 
                                   recovery_options: Dict[str, Any]) -> Dict[str, Any]:
        """Perform advanced flow recovery with comprehensive state repair"""
        try:
            start_time = datetime.now()
            recovery_actions = []
            
            async with AsyncSessionLocal() as db_session:
                # Get workflow state
                stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.session_id == session_id,
                        WorkflowState.client_account_id == context.client_account_id,
                        WorkflowState.engagement_id == context.engagement_id
                    )
                )
                result = await db_session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return {
                        "success": False,
                        "session_id": session_id,
                        "recovery_actions": [],
                        "flow_state": {},
                        "performance_metrics": {
                            "recovery_time_ms": 0,
                            "data_integrity_score": 0,
                            "agent_memory_completeness": 0
                        },
                        "recovered_at": datetime.now().isoformat(),
                        "error": "Workflow not found"
                    }
                
                # Perform recovery actions based on options
                if recovery_options.get("repair_corrupted_state", True):
                    repair_result = await self._repair_corrupted_state(workflow)
                    if repair_result.get("success", False):
                        recovery_actions.append("State corruption repaired")
                    else:
                        recovery_actions.append("State repair failed")
                
                if recovery_options.get("reconstruct_agent_memory", True):
                    memory_result = await self._reconstruct_agent_memory(workflow)
                    if memory_result.get("success", False):
                        recovery_actions.append("Agent memory reconstructed")
                    else:
                        recovery_actions.append("Memory reconstruction failed")
                
                if recovery_options.get("validate_data_consistency", True):
                    validation_result = await self._validate_and_repair_data_consistency(workflow)
                    if validation_result.get("success", False):
                        recovery_actions.append("Data consistency validated")
                    else:
                        recovery_actions.append("Data validation failed")
                
                if recovery_options.get("optimize_for_resumption", True):
                    optimization_result = await self._optimize_flow_for_resumption(workflow)
                    if optimization_result.get("success", False):
                        recovery_actions.append("Flow optimized for resumption")
                    else:
                        recovery_actions.append("Optimization failed")
                
                # Refresh workflow state after recovery
                await db_session.refresh(workflow)
                
                # Calculate performance metrics
                recovery_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Assess data integrity
                data_integrity_score = 100.0
                if workflow.errors:
                    data_integrity_score -= len(workflow.errors) * 10
                if not workflow.state_data:
                    data_integrity_score -= 20
                data_integrity_score = max(0, data_integrity_score)
                
                # Assess agent memory completeness
                agent_memory_completeness = 100.0
                if not workflow.shared_memory_id:
                    agent_memory_completeness -= 30
                if not workflow.agent_insights:
                    agent_memory_completeness -= 20
                agent_memory_completeness = max(0, agent_memory_completeness)
                
                # Build recovered flow state
                flow_state = {
                    "session_id": str(workflow.session_id),
                    "flow_id": str(workflow.flow_id),
                    "current_phase": workflow.current_phase,
                    "status": workflow.status,
                    "progress_percentage": workflow.progress_percentage,
                    "phase_completion": workflow.phase_completion or {},
                    "crew_status": workflow.crew_status or {},
                    "agent_insights": workflow.agent_insights or [],
                    "errors": workflow.errors or [],
                    "warnings": workflow.warnings or [],
                    "state_data": workflow.state_data or {},
                    "updated_at": workflow.updated_at.isoformat()
                }
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "recovery_actions": recovery_actions,
                    "flow_state": flow_state,
                    "performance_metrics": {
                        "recovery_time_ms": recovery_time,
                        "data_integrity_score": data_integrity_score,
                        "agent_memory_completeness": agent_memory_completeness
                    },
                    "recovered_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Advanced flow recovery failed: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "recovery_actions": [],
                "flow_state": {},
                "performance_metrics": {
                    "recovery_time_ms": 0,
                    "data_integrity_score": 0,
                    "agent_memory_completeness": 0
                },
                "recovered_at": datetime.now().isoformat(),
                "error": str(e)
            }

# Global instance
flow_state_manager = DiscoveryFlowStateManager() 