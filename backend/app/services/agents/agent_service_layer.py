"""
Agent Service Layer
Provides synchronous, direct access to backend services for AI agents.
No HTTP calls, no authentication needed, just clean service interfaces.

For detailed documentation, see: /docs/agents/agent-service-layer.md
"""

import logging
import time
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import concurrent.futures
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler

logger = logging.getLogger(__name__)

class AgentServiceLayer:
    """
    Synchronous service layer for AI agents.
    Provides clean, direct access to backend services without HTTP/auth complexity.
    """
    
    def __init__(self, client_account_id: str, engagement_id: str, user_id: Optional[str] = None):
        """Initialize with multi-tenant context"""
        self.context = RequestContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            session_id=None
        )
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._metrics = {
            "calls_made": 0,
            "errors": 0,
            "total_time": 0.0,
            "last_error": None
        }
    
    def _log_call(self, method_name: str, duration: float, success: bool, error: Optional[str] = None):
        """Log service call metrics"""
        self._metrics["calls_made"] += 1
        self._metrics["total_time"] += duration
        
        if not success:
            self._metrics["errors"] += 1
            self._metrics["last_error"] = error
        
        logger.info(f"AgentService.{method_name}", extra={
            "duration_ms": duration * 1000,
            "success": success,
            "client_account_id": str(self.context.client_account_id),
            "engagement_id": str(self.context.engagement_id),
            "error": error
        })
    
    def _handle_service_error(self, method_name: str, error: Exception) -> Dict[str, Any]:
        """Standardized error handling"""
        error_msg = str(error)
        error_type = "system"
        
        # Categorize errors
        if "not found" in error_msg.lower():
            error_type = "not_found"
        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
            error_type = "permission"
        elif "validation" in error_msg.lower():
            error_type = "validation"
        
        return {
            "status": "error",
            "error": error_msg,
            "error_type": error_type,
            "method": method_name,
            "timestamp": datetime.utcnow().isoformat(),
            "guidance": self._get_error_guidance(error_type)
        }
    
    def _get_error_guidance(self, error_type: str) -> str:
        """Get user guidance based on error type"""
        guidance_map = {
            "not_found": "Resource not found. Please check the ID and try again.",
            "permission": "Access denied. Please verify your permissions.",
            "validation": "Invalid data provided. Please check your input.",
            "system": "System error occurred. Please try again or contact support."
        }
        return guidance_map.get(error_type, "An error occurred. Please try again.")
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow status - synchronous wrapper for agents"""
        start_time = time.time()
        method_name = "get_flow_status"
        
        try:
            future = self.executor.submit(asyncio.run, self._async_get_flow_status(flow_id))
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except concurrent.futures.TimeoutError:
            duration = time.time() - start_time
            error_msg = "Service call timed out after 30 seconds"
            self._log_call(method_name, duration, False, error_msg)
            return self._handle_service_error(method_name, Exception(error_msg))
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Async implementation - uses direct repository access"""
        async with AsyncSessionLocal() as db:
            try:
                # Direct repository access - no HTTP, no auth needed
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                # Get real flow data
                flow = await flow_repo.get_by_flow_id(flow_id)
                
                if not flow:
                    return {
                        "status": "not_found",
                        "flow_exists": False,
                        "message": "Flow not found in database"
                    }
                
                # Get active flows to provide context
                active_flows = await flow_repo.get_active_flows()
                
                return {
                    "status": "success",
                    "flow_exists": True,
                    "flow": {
                        "flow_id": str(flow.flow_id),
                        "status": flow.status,
                        "current_phase": flow.get_current_phase(),
                        "next_phase": flow.get_next_phase(),
                        "progress": flow.progress_percentage,
                        "phases_completed": {
                            "data_import": flow.data_import_completed,
                            "attribute_mapping": flow.attribute_mapping_completed,
                            "data_cleansing": flow.data_cleansing_completed,
                            "inventory": flow.inventory_completed,
                            "dependencies": flow.dependencies_completed,
                            "tech_debt": flow.tech_debt_completed
                        }
                    },
                    "active_flows_count": len(active_flows),
                    "has_incomplete_flows": any(not f.is_complete() for f in active_flows)
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_flow_status: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "flow_exists": False
                }
    
    def get_navigation_guidance(self, flow_id: str, current_phase: str) -> Dict[str, Any]:
        """Get navigation guidance for a flow"""
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_navigation_guidance(flow_id, current_phase)
            )
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"Error getting navigation guidance: {e}")
            return {
                "status": "error",
                "error": str(e),
                "guidance": []
            }
    
    async def _async_get_navigation_guidance(self, flow_id: str, current_phase: str) -> Dict[str, Any]:
        """Get navigation guidance using flow management handler"""
        async with AsyncSessionLocal() as db:
            try:
                handler = FlowManagementHandler(db, self.context)
                
                # Direct service call - no HTTP needed
                flow_status = await handler.get_flow_status(flow_id)
                
                if not flow_status:
                    return {
                        "status": "not_found",
                        "guidance": ["No flow found. User needs to upload data first."]
                    }
                
                # Generate guidance based on flow state
                guidance = []
                next_phase = flow_status.get("next_phase")
                
                if next_phase:
                    phase_routes = {
                        "data_import": "/discovery/data-import",
                        "attribute_mapping": "/discovery/attribute-mapping",
                        "data_cleansing": "/discovery/data-cleansing",
                        "inventory": "/discovery/inventory-building",
                        "dependencies": "/discovery/dependency-analysis",
                        "tech_debt": "/discovery/tech-debt-analysis"
                    }
                    
                    if next_phase in phase_routes:
                        guidance.append(f"Navigate to {phase_routes[next_phase]}")
                        guidance.append(f"Complete the {next_phase.replace('_', ' ').title()} phase")
                
                return {
                    "status": "success",
                    "current_phase": current_phase,
                    "next_phase": next_phase,
                    "guidance": guidance,
                    "flow_status": flow_status
                }
                
            except Exception as e:
                logger.error(f"Error in _async_get_navigation_guidance: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "guidance": []
                }
    
    def validate_phase_completion(self, flow_id: str, phase: str) -> Dict[str, Any]:
        """Validate if a phase can be marked complete"""
        # Add validation logic here
        return {
            "status": "success",
            "phase": phase,
            "can_complete": True,
            "validation_messages": []
        }
    
    def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active flows for the client/engagement"""
        start_time = time.time()
        method_name = "get_active_flows"
        
        try:
            future = self.executor.submit(asyncio.run, self._async_get_active_flows())
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_active_flows(self) -> List[Dict[str, Any]]:
        """Get active flows from repository"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flows = await flow_repo.get_active_flows()
                
                return [
                    {
                        "flow_id": str(flow.flow_id),
                        "status": flow.status,
                        "current_phase": flow.get_current_phase(),
                        "next_phase": flow.get_next_phase(),
                        "progress": flow.progress_percentage,
                        "is_complete": flow.is_complete(),
                        "created_at": flow.created_at.isoformat() if flow.created_at else None,
                        "phases_completed": {
                            "data_import": flow.data_import_completed,
                            "attribute_mapping": flow.attribute_mapping_completed,
                            "data_cleansing": flow.data_cleansing_completed,
                            "inventory": flow.inventory_completed,
                            "dependencies": flow.dependencies_completed,
                            "tech_debt": flow.tech_debt_completed
                        }
                    }
                    for flow in flows
                ]
                
            except Exception as e:
                logger.error(f"Database error in _async_get_active_flows: {e}")
                raise
    
    def validate_phase_transition(self, flow_id: str, from_phase: str, to_phase: str) -> Dict[str, Any]:
        """Validate if a phase transition is allowed"""
        start_time = time.time()
        method_name = "validate_phase_transition"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_validate_phase_transition(flow_id, from_phase, to_phase)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_validate_phase_transition(self, flow_id: str, from_phase: str, to_phase: str) -> Dict[str, Any]:
        """Validate phase transition logic"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                
                if not flow:
                    return {
                        "status": "not_found",
                        "can_transition": False,
                        "error": "Flow not found",
                        "guidance": "Flow does not exist. User must upload data first."
                    }
                
                # Define valid phase transitions
                valid_transitions = {
                    "data_import": ["attribute_mapping"],
                    "attribute_mapping": ["data_cleansing"],
                    "data_cleansing": ["inventory"],
                    "inventory": ["dependencies"],
                    "dependencies": ["tech_debt"],
                    "tech_debt": []  # Final phase
                }
                
                # Check if transition is valid
                allowed_next_phases = valid_transitions.get(from_phase, [])
                can_transition = to_phase in allowed_next_phases
                
                # Check if prerequisites are met
                prerequisites_met = True
                missing_requirements = []
                
                if to_phase == "attribute_mapping" and not flow.data_import_completed:
                    prerequisites_met = False
                    missing_requirements.append("Data import must be completed")
                elif to_phase == "data_cleansing" and not flow.attribute_mapping_completed:
                    prerequisites_met = False
                    missing_requirements.append("Attribute mapping must be completed")
                elif to_phase == "inventory" and not flow.data_cleansing_completed:
                    prerequisites_met = False
                    missing_requirements.append("Data cleansing must be completed")
                elif to_phase == "dependencies" and not flow.inventory_completed:
                    prerequisites_met = False
                    missing_requirements.append("Inventory must be completed")
                elif to_phase == "tech_debt" and not flow.dependencies_completed:
                    prerequisites_met = False
                    missing_requirements.append("Dependencies must be completed")
                
                return {
                    "status": "success",
                    "can_transition": can_transition and prerequisites_met,
                    "valid_transition": can_transition,
                    "prerequisites_met": prerequisites_met,
                    "missing_requirements": missing_requirements,
                    "current_phase": flow.get_current_phase(),
                    "target_phase": to_phase,
                    "guidance": "Transition allowed" if (can_transition and prerequisites_met) else f"Cannot transition: {', '.join(missing_requirements)}"
                }
                
            except Exception as e:
                logger.error(f"Error in _async_validate_phase_transition: {e}")
                raise
    
    # === Phase 3: Data Services ===
    
    def get_import_data(self, flow_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get raw import data for a flow"""
        start_time = time.time()
        method_name = "get_import_data"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_import_data(flow_id, limit)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_import_data(self, flow_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get import data from database"""
        async with AsyncSessionLocal() as db:
            try:
                from app.models.data_import import DataImport, RawImportRecord
                from sqlalchemy import select
                
                # First get the flow to find the data_import_id
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "error": "Flow not found",
                        "guidance": "Flow does not exist"
                    }
                
                # Get data import records
                if flow.data_import_id:
                    # Get raw import records
                    stmt = select(RawImportRecord).where(
                        RawImportRecord.data_import_id == flow.data_import_id
                    )
                    if limit:
                        stmt = stmt.limit(limit)
                    
                    result = await db.execute(stmt)
                    records = result.scalars().all()
                    
                    return {
                        "status": "success",
                        "flow_id": flow_id,
                        "total_records": len(records),
                        "raw_data": [
                            {
                                "id": str(record.id),
                                "raw_data": record.raw_data,
                                "source_system": record.source_system,
                                "import_timestamp": record.import_timestamp.isoformat() if record.import_timestamp else None
                            }
                            for record in records
                        ]
                    }
                else:
                    # No data import linked
                    return {
                        "status": "success",
                        "flow_id": flow_id,
                        "total_records": 0,
                        "raw_data": [],
                        "message": "No import data linked to this flow"
                    }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_import_data: {e}")
                raise
    
    def get_field_mappings(self, flow_id: str) -> Dict[str, Any]:
        """Get field mapping configuration for a flow"""
        start_time = time.time()
        method_name = "get_field_mappings"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_field_mappings(flow_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_field_mappings(self, flow_id: str) -> Dict[str, Any]:
        """Get field mappings from database"""
        async with AsyncSessionLocal() as db:
            try:
                from app.models.data_import import ImportFieldMapping
                from sqlalchemy import select
                
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "error": "Flow not found",
                        "guidance": "Flow does not exist"
                    }
                
                if flow.data_import_id:
                    # Get field mappings
                    stmt = select(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == flow.data_import_id
                    )
                    
                    result = await db.execute(stmt)
                    mappings = result.scalars().all()
                    
                    return {
                        "status": "success",
                        "flow_id": flow_id,
                        "total_mappings": len(mappings),
                        "mappings": [
                            {
                                "id": str(mapping.id),
                                "source_field": mapping.source_field,
                                "target_field": mapping.target_field,
                                "mapping_type": mapping.mapping_type,
                                "confidence_score": mapping.confidence_score,
                                "is_user_defined": mapping.is_user_defined,
                                "status": mapping.status
                            }
                            for mapping in mappings
                        ]
                    }
                else:
                    return {
                        "status": "success",
                        "flow_id": flow_id,
                        "total_mappings": 0,
                        "mappings": [],
                        "message": "No import data linked - no mappings available"
                    }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_field_mappings: {e}")
                raise
    
    def validate_mappings(self, flow_id: str, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate field mappings"""
        start_time = time.time()
        method_name = "validate_mappings"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_validate_mappings(flow_id, mappings)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_validate_mappings(self, flow_id: str, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate field mappings logic"""
        try:
            # Basic validation logic
            validation_issues = []
            valid_mappings = []
            
            for mapping in mappings.get("mappings", []):
                source_field = mapping.get("source_field", "")
                target_field = mapping.get("target_field", "")
                
                if not source_field:
                    validation_issues.append("Source field cannot be empty")
                    continue
                    
                if not target_field:
                    validation_issues.append(f"Target field missing for source field '{source_field}'")
                    continue
                
                # Check for duplicate target fields
                duplicate_targets = [m for m in valid_mappings if m.get("target_field") == target_field]
                if duplicate_targets:
                    validation_issues.append(f"Duplicate target field '{target_field}'")
                    continue
                
                valid_mappings.append(mapping)
            
            is_valid = len(validation_issues) == 0
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "is_valid": is_valid,
                "valid_mappings_count": len(valid_mappings),
                "total_mappings": len(mappings.get("mappings", [])),
                "validation_issues": validation_issues,
                "guidance": "All mappings are valid" if is_valid else f"Found {len(validation_issues)} validation issues"
            }
            
        except Exception as e:
            logger.error(f"Error in _async_validate_mappings: {e}")
            raise
    
    def get_cleansing_results(self, flow_id: str) -> Dict[str, Any]:
        """Get data cleansing analysis results"""
        start_time = time.time()
        method_name = "get_cleansing_results"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_cleansing_results(flow_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_cleansing_results(self, flow_id: str) -> Dict[str, Any]:
        """Get data cleansing results from flow state"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "error": "Flow not found",
                        "guidance": "Flow does not exist"
                    }
                
                # Extract cleansing results from CrewAI state data
                cleansing_data = {}
                if flow.crewai_state_data:
                    cleansing_data = flow.crewai_state_data.get("data_cleansing", {})
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "cleansing_completed": flow.data_cleansing_completed,
                    "issues_found": cleansing_data.get("issues_found", []),
                    "quality_score": cleansing_data.get("quality_score", 0.0),
                    "records_processed": cleansing_data.get("records_processed", 0),
                    "records_cleaned": cleansing_data.get("records_cleaned", 0),
                    "suggestions": cleansing_data.get("suggestions", []),
                    "summary": cleansing_data.get("summary", "No cleansing results available")
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_cleansing_results: {e}")
                raise
    
    def get_validation_issues(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get data validation issues"""
        start_time = time.time()
        method_name = "get_validation_issues"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_validation_issues(flow_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_validation_issues(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get validation issues from flow data"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "issues": [],
                        "error": "Flow not found"
                    }
                
                # Collect validation issues from different phases
                all_issues = []
                
                if flow.crewai_state_data:
                    # Data import issues
                    import_data = flow.crewai_state_data.get("data_import", {})
                    import_issues = import_data.get("validation_issues", [])
                    for issue in import_issues:
                        all_issues.append({
                            "phase": "data_import",
                            "severity": issue.get("severity", "warning"),
                            "message": issue.get("message", ""),
                            "field": issue.get("field"),
                            "record_count": issue.get("record_count", 0)
                        })
                    
                    # Field mapping issues
                    mapping_data = flow.crewai_state_data.get("attribute_mapping", {})
                    mapping_issues = mapping_data.get("validation_issues", [])
                    for issue in mapping_issues:
                        all_issues.append({
                            "phase": "attribute_mapping",
                            "severity": issue.get("severity", "warning"),
                            "message": issue.get("message", ""),
                            "source_field": issue.get("source_field"),
                            "target_field": issue.get("target_field")
                        })
                    
                    # Data cleansing issues
                    cleansing_data = flow.crewai_state_data.get("data_cleansing", {})
                    cleansing_issues = cleansing_data.get("issues_found", [])
                    for issue in cleansing_issues:
                        all_issues.append({
                            "phase": "data_cleansing",
                            "severity": issue.get("severity", "warning"),
                            "message": issue.get("message", ""),
                            "field": issue.get("field"),
                            "suggestion": issue.get("suggestion")
                        })
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "total_issues": len(all_issues),
                    "issues": all_issues,
                    "issues_by_severity": {
                        "error": len([i for i in all_issues if i.get("severity") == "error"]),
                        "warning": len([i for i in all_issues if i.get("severity") == "warning"]),
                        "info": len([i for i in all_issues if i.get("severity") == "info"])
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_validation_issues: {e}")
                raise
    
    # === Phase 4: Asset Services ===
    
    def get_discovered_assets(self, flow_id: str, asset_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all discovered assets for a flow"""
        start_time = time.time()
        method_name = "get_discovered_assets"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_discovered_assets(flow_id, asset_type)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_discovered_assets(self, flow_id: str, asset_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get discovered assets from database"""
        async with AsyncSessionLocal() as db:
            try:
                from app.models.asset import Asset
                from sqlalchemy import select, and_
                
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "assets": [],
                        "error": "Flow not found"
                    }
                
                # Query assets linked to this discovery flow
                stmt = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == flow.flow_id,
                        Asset.client_account_id == flow.client_account_id,
                        Asset.engagement_id == flow.engagement_id
                    )
                )
                
                if asset_type:
                    stmt = stmt.where(Asset.asset_type == asset_type)
                
                result = await db.execute(stmt)
                assets = result.scalars().all()
                
                asset_list = []
                for asset in assets:
                    asset_data = {
                        "id": str(asset.id),
                        "name": asset.name,
                        "type": asset.asset_type,
                        "subtype": asset.asset_subtype,
                        "description": asset.description,
                        "status": asset.status,
                        "risk_score": asset.risk_score,
                        "complexity_score": asset.complexity_score,
                        "migration_strategy": asset.migration_strategy,
                        "discovery_phase": getattr(asset, 'discovered_in_phase', 'unknown'),
                        "confidence_score": getattr(asset, 'confidence_score', 0.0),
                        "created_at": asset.created_at.isoformat() if asset.created_at else None
                    }
                    
                    # Add asset-specific metadata if available
                    if hasattr(asset, 'metadata') and asset.metadata:
                        asset_data["metadata"] = asset.metadata
                    
                    asset_list.append(asset_data)
                
                # Group assets by type for summary
                asset_types = {}
                for asset in asset_list:
                    asset_type_key = asset["type"]
                    if asset_type_key not in asset_types:
                        asset_types[asset_type_key] = 0
                    asset_types[asset_type_key] += 1
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "total_assets": len(asset_list),
                    "assets": asset_list,
                    "asset_types": asset_types,
                    "discovery_completed": flow.inventory_completed
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_discovered_assets: {e}")
                raise
    
    def get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
        """Get dependency analysis results"""
        start_time = time.time()
        method_name = "get_asset_dependencies"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_asset_dependencies(flow_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
        """Get dependency analysis from flow state"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "error": "Flow not found",
                        "guidance": "Flow does not exist"
                    }
                
                # Extract dependency analysis from CrewAI state data
                dependencies_data = {}
                if flow.crewai_state_data:
                    dependencies_data = flow.crewai_state_data.get("dependencies", {})
                
                # Get dependency graph structure
                dependency_graph = dependencies_data.get("dependency_graph", {})
                nodes = dependency_graph.get("nodes", [])
                edges = dependency_graph.get("edges", [])
                
                # Calculate dependency metrics
                critical_paths = dependencies_data.get("critical_paths", [])
                circular_dependencies = dependencies_data.get("circular_dependencies", [])
                orphaned_assets = dependencies_data.get("orphaned_assets", [])
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "dependencies_completed": flow.dependencies_completed,
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "dependency_graph": {
                        "nodes": nodes,
                        "edges": edges
                    },
                    "analysis": {
                        "critical_paths": critical_paths,
                        "critical_path_count": len(critical_paths),
                        "circular_dependencies": circular_dependencies,
                        "circular_dependency_count": len(circular_dependencies),
                        "orphaned_assets": orphaned_assets,
                        "orphaned_asset_count": len(orphaned_assets)
                    },
                    "recommendations": dependencies_data.get("recommendations", []),
                    "summary": dependencies_data.get("summary", "No dependency analysis available")
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_asset_dependencies: {e}")
                raise
    
    def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get technical debt analysis results"""
        start_time = time.time()
        method_name = "get_tech_debt_analysis"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_tech_debt_analysis(flow_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get tech debt analysis from flow state"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "not_found",
                        "error": "Flow not found",
                        "guidance": "Flow does not exist"
                    }
                
                # Extract tech debt analysis from CrewAI state data
                tech_debt_data = {}
                if flow.crewai_state_data:
                    tech_debt_data = flow.crewai_state_data.get("tech_debt", {})
                
                # Parse tech debt findings
                debt_items = tech_debt_data.get("debt_items", [])
                total_score = tech_debt_data.get("total_score", 0.0)
                risk_categories = tech_debt_data.get("risk_categories", {})
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "tech_debt_completed": flow.tech_debt_completed,
                    "total_debt_score": total_score,
                    "debt_items_count": len(debt_items),
                    "debt_items": debt_items,
                    "risk_categories": risk_categories,
                    "high_risk_items": [
                        item for item in debt_items 
                        if item.get("risk_level", "").lower() == "high"
                    ],
                    "recommendations": tech_debt_data.get("recommendations", []),
                    "migration_blockers": tech_debt_data.get("migration_blockers", []),
                    "priority_actions": tech_debt_data.get("priority_actions", []),
                    "summary": tech_debt_data.get("summary", "No tech debt analysis available")
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_tech_debt_analysis: {e}")
                raise
    
    def validate_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset data quality"""
        start_time = time.time()
        method_name = "validate_asset_data"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_validate_asset_data(asset_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_validate_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset data quality"""
        async with AsyncSessionLocal() as db:
            try:
                from app.models.asset import Asset
                from sqlalchemy import select, and_
                
                # Get asset
                stmt = select(Asset).where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == uuid.UUID(str(self.context.client_account_id)),
                        Asset.engagement_id == uuid.UUID(str(self.context.engagement_id))
                    )
                )
                
                result = await db.execute(stmt)
                asset = result.scalar_one_or_none()
                
                if not asset:
                    return {
                        "status": "not_found",
                        "error": "Asset not found",
                        "guidance": "Asset does not exist"
                    }
                
                # Validate asset data
                validation_issues = []
                validation_score = 100.0
                
                # Check required fields
                if not asset.name or asset.name.strip() == "":
                    validation_issues.append("Asset name is required")
                    validation_score -= 20
                
                if not asset.asset_type or asset.asset_type.strip() == "":
                    validation_issues.append("Asset type is required")
                    validation_score -= 20
                
                # Check risk scores
                if asset.risk_score is None or asset.risk_score < 0 or asset.risk_score > 10:
                    validation_issues.append("Risk score should be between 0 and 10")
                    validation_score -= 10
                
                if asset.complexity_score is None or asset.complexity_score < 0 or asset.complexity_score > 10:
                    validation_issues.append("Complexity score should be between 0 and 10")
                    validation_score -= 10
                
                # Check migration strategy
                valid_strategies = ["rehost", "replatform", "repurchase", "refactor", "retire", "retain"]
                if asset.migration_strategy and asset.migration_strategy.lower() not in valid_strategies:
                    validation_issues.append(f"Invalid migration strategy. Must be one of: {', '.join(valid_strategies)}")
                    validation_score -= 15
                
                # Additional metadata checks
                if hasattr(asset, 'metadata') and asset.metadata:
                    if not isinstance(asset.metadata, dict):
                        validation_issues.append("Asset metadata should be a valid JSON object")
                        validation_score -= 5
                
                validation_score = max(validation_score, 0.0)
                is_valid = len(validation_issues) == 0
                
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "is_valid": is_valid,
                    "validation_score": validation_score,
                    "validation_issues": validation_issues,
                    "asset_summary": {
                        "name": asset.name,
                        "type": asset.asset_type,
                        "risk_score": asset.risk_score,
                        "complexity_score": asset.complexity_score,
                        "migration_strategy": asset.migration_strategy
                    },
                    "guidance": "Asset data is valid" if is_valid else f"Found {len(validation_issues)} validation issues"
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_validate_asset_data: {e}")
                raise
    
    def get_asset_relationships(self, asset_id: str) -> Dict[str, Any]:
        """Get asset relationships and dependencies"""
        start_time = time.time()
        method_name = "get_asset_relationships"
        
        try:
            future = self.executor.submit(
                asyncio.run, 
                self._async_get_asset_relationships(asset_id)
            )
            result = future.result(timeout=30)
            
            duration = time.time() - start_time
            self._log_call(method_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    async def _async_get_asset_relationships(self, asset_id: str) -> Dict[str, Any]:
        """Get asset relationships from database"""
        async with AsyncSessionLocal() as db:
            try:
                from app.models.asset import Asset
                from sqlalchemy import select, and_, or_
                
                # Get the target asset
                stmt = select(Asset).where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == uuid.UUID(str(self.context.client_account_id)),
                        Asset.engagement_id == uuid.UUID(str(self.context.engagement_id))
                    )
                )
                
                result = await db.execute(stmt)
                asset = result.scalar_one_or_none()
                
                if not asset:
                    return {
                        "status": "not_found",
                        "error": "Asset not found",
                        "guidance": "Asset does not exist"
                    }
                
                # For now, return basic relationship structure
                # In a full implementation, this would query relationship tables
                relationships = {
                    "depends_on": [],  # Assets this asset depends on
                    "dependents": [],  # Assets that depend on this asset
                    "related": []      # Related assets (same type, etc.)
                }
                
                # Get assets in the same discovery flow for basic relationships
                flow_assets_stmt = select(Asset).where(
                    and_(
                        Asset.discovery_flow_id == asset.discovery_flow_id,
                        Asset.client_account_id == asset.client_account_id,
                        Asset.engagement_id == asset.engagement_id,
                        Asset.id != asset.id  # Exclude the target asset
                    )
                )
                
                flow_result = await db.execute(flow_assets_stmt)
                flow_assets = flow_result.scalars().all()
                
                # Basic relationship detection based on asset types and names
                for related_asset in flow_assets:
                    relationship_data = {
                        "id": str(related_asset.id),
                        "name": related_asset.name,
                        "type": related_asset.asset_type,
                        "relationship_type": "unknown"
                    }
                    
                    # Simple heuristics for relationship detection
                    if asset.asset_type == related_asset.asset_type:
                        relationship_data["relationship_type"] = "same_type"
                        relationships["related"].append(relationship_data)
                    elif "database" in asset.asset_type.lower() and "application" in related_asset.asset_type.lower():
                        relationship_data["relationship_type"] = "data_dependency"
                        relationships["dependents"].append(relationship_data)
                    elif "application" in asset.asset_type.lower() and "database" in related_asset.asset_type.lower():
                        relationship_data["relationship_type"] = "data_dependency"
                        relationships["depends_on"].append(relationship_data)
                
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type,
                    "relationships": relationships,
                    "total_relationships": (
                        len(relationships["depends_on"]) + 
                        len(relationships["dependents"]) + 
                        len(relationships["related"])
                    ),
                    "relationship_summary": {
                        "dependencies": len(relationships["depends_on"]),
                        "dependents": len(relationships["dependents"]),
                        "related": len(relationships["related"])
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in _async_get_asset_relationships: {e}")
                raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service layer performance metrics"""
        avg_time = self._metrics["total_time"] / max(self._metrics["calls_made"], 1)
        error_rate = self._metrics["errors"] / max(self._metrics["calls_made"], 1)
        
        return {
            "calls_made": self._metrics["calls_made"],
            "errors": self._metrics["errors"],
            "error_rate": error_rate,
            "avg_response_time": avg_time,
            "last_error": self._metrics["last_error"],
            "context": {
                "client_account_id": str(self.context.client_account_id),
                "engagement_id": str(self.context.engagement_id)
            }
        }
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Singleton instance for common use cases
_default_agent_service = None

def get_agent_service(client_account_id: str, engagement_id: str, user_id: Optional[str] = None) -> AgentServiceLayer:
    """Get or create agent service instance"""
    global _default_agent_service
    
    # For now, create new instance each time
    # Could implement caching by context if needed
    return AgentServiceLayer(client_account_id, engagement_id, user_id)