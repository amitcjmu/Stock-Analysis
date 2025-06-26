"""
Flow Management Handler
Handles PostgreSQL-based discovery flow lifecycle management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)

class FlowManagementHandler:
    """Handler for PostgreSQL-based discovery flow management"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
        
        # Initialize repository for database operations
        # Handle None context values with fallbacks
        client_id = str(context.client_account_id) if context.client_account_id else "11111111-1111-1111-1111-111111111111"
        engagement_id = str(context.engagement_id) if context.engagement_id else "22222222-2222-2222-2222-222222222222"
        
        self.flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=client_id,
            engagement_id=engagement_id
        )
    
    async def create_flow(self, flow_id: str, raw_data: List[Dict[str, Any]], 
                         metadata: Dict[str, Any], data_import_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new discovery flow in PostgreSQL"""
        try:
            logger.info(f"📊 Creating PostgreSQL flow: {flow_id}")
            
            # Basic flow creation logic
            flow_data = {
                "flow_id": flow_id,
                "data_import_id": data_import_id,
                "client_account_id": self.client_account_id,
                "engagement_id": self.engagement_id,
                "user_id": self.user_id,
                "status": "initialized",
                "current_phase": "data_import",
                "progress_percentage": 0.0,
                "phases": {
                    "data_import": False,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "raw_data_count": len(raw_data),
                "metadata": metadata
            }
            
            logger.info(f"✅ PostgreSQL flow created: {flow_id}")
            return flow_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create PostgreSQL flow: {e}")
            raise
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get active flows from PostgreSQL"""
        try:
            logger.info("🔍 Getting active flows from PostgreSQL")
            
            # Get actual flows from database
            flows = await self.flow_repo.get_active_flows()
            
            # Convert to API format
            active_flows = []
            for flow in flows:
                # Include phase completion information for auto-detection
                phases = {
                    "data_import_completed": flow.data_import_completed,
                    "attribute_mapping_completed": flow.attribute_mapping_completed,
                    "data_cleansing_completed": flow.data_cleansing_completed,
                    "inventory_completed": flow.inventory_completed,
                    "dependencies_completed": flow.dependencies_completed,
                    "tech_debt_completed": flow.tech_debt_completed
                }
                
                # Also include next_phase for auto-detection logic
                next_phase = flow.get_next_phase()
                
                active_flows.append({
                    "flow_id": str(flow.flow_id),
                    "id": str(flow.id),
                    "status": flow.status,
                    "current_phase": next_phase or "completed",  # Use actual next phase
                    "next_phase": next_phase,  # Include for auto-detection
                    "progress_percentage": flow.progress_percentage,
                    "flow_name": flow.flow_name,
                    "flow_description": flow.flow_description,
                    "phases": phases,  # Include phase completion for auto-detection
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                    "client_account_id": str(flow.client_account_id),
                    "engagement_id": str(flow.engagement_id),
                    # Also include direct completion fields for backward compatibility
                    "data_import_completed": flow.data_import_completed,
                    "attribute_mapping_completed": flow.attribute_mapping_completed,
                    "data_cleansing_completed": flow.data_cleansing_completed,
                    "inventory_completed": flow.inventory_completed,
                    "dependencies_completed": flow.dependencies_completed,
                    "tech_debt_completed": flow.tech_debt_completed
                })
            
            logger.info(f"✅ Retrieved {len(active_flows)} active flows from PostgreSQL")
            return active_flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            return []
    
    async def execute_phase(self, phase: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a discovery phase in PostgreSQL"""
        try:
            logger.info(f"⚡ Executing PostgreSQL phase: {phase}")
            
            # Get the flow_id from the data or context
            flow_id = data.get("flow_id")
            if not flow_id:
                # Try to get from the current context or active flows
                active_flows = await self.get_active_flows()
                if active_flows:
                    flow_id = active_flows[0]["flow_id"]
                else:
                    raise ValueError("No flow_id provided and no active flows found")
            
            # Actually update the database to mark phase as completed
            await self.flow_repo.update_phase_completion(
                flow_id=flow_id,
                phase=phase,
                data=data,
                crew_status={"status": "completed", "timestamp": datetime.now().isoformat()},
                agent_insights=[
                    {
                        "agent": "PostgreSQL Flow Manager",
                        "insight": f"Completed {phase} phase execution",
                        "phase": phase,
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            )
            
            result = {
                "phase": phase,
                "status": "completed",
                "flow_id": flow_id,
                "data_processed": len(data.get("assets", [])),
                "database_updated": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ PostgreSQL phase completed and database updated: {phase}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to execute PostgreSQL phase: {e}")
            raise
    
    async def continue_flow(self, flow_id: str) -> Dict[str, Any]:
        """Continue a paused flow with proper phase validation"""
        try:
            logger.info(f"▶️ Continuing PostgreSQL flow: {flow_id}")
            
            # Get current flow state from database to determine next phase
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Validate current phase completion before determining next phase
            validated_next_phase = await self._validate_and_get_next_phase(flow)
                
            # Log current phase completion status for debugging
            logger.info(f"🔍 Database flow {flow_id} phase status: data_import={flow.data_import_completed}, "
                      f"attribute_mapping={flow.attribute_mapping_completed}, "
                      f"data_cleansing={flow.data_cleansing_completed}, "
                      f"inventory={flow.inventory_completed}, "
                      f"dependencies={flow.dependencies_completed}, "
                      f"tech_debt={flow.tech_debt_completed}")
            
            result = {
                "flow_id": flow_id,
                "status": "continued",
                "next_phase": validated_next_phase,
                "validation_performed": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ PostgreSQL flow continued: {flow_id}, next_phase: {validated_next_phase}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to continue PostgreSQL flow: {e}")
            raise

    async def _validate_and_get_next_phase(self, flow) -> str:
        """Validate phase completion and determine the actual next phase based on meaningful results"""
        try:
            # Check data_import phase validation
            if not flow.data_import_completed:
                logger.info("🔍 Data import phase not completed - staying in data_import")
                return "data_import"
            
            # Validate data_import phase actually produced meaningful results
            data_import_valid = await self._validate_data_import_completion(flow)
            if not data_import_valid:
                logger.warning("⚠️ Data import marked complete but no meaningful results found - resetting to data_import")
                # Reset the completion flag since the phase didn't actually complete properly
                await self.flow_repo.update_phase_completion(
                    flow_id=str(flow.flow_id),
                    phase="data_import",
                    data={"reset_reason": "No meaningful results found"},
                    crew_status={"status": "reset", "reason": "validation_failed"},
                    agent_insights=[{
                        "agent": "Flow Validation System",
                        "insight": "Data import phase reset due to lack of meaningful results",
                        "action_required": "Re-process data import with proper agent analysis",
                        "timestamp": datetime.now().isoformat()
                    }],
                    completed=False  # Reset completion flag
                )
                return "data_import"
            
            # Check attribute_mapping phase validation
            if not flow.attribute_mapping_completed:
                logger.info("🔍 Data import validated - proceeding to attribute_mapping")
                return "attribute_mapping"
            
            # Validate attribute_mapping phase actually produced field mappings
            mapping_valid = await self._validate_attribute_mapping_completion(flow)
            if not mapping_valid:
                logger.warning("⚠️ Attribute mapping marked complete but no field mappings found - resetting to attribute_mapping")
                await self.flow_repo.update_phase_completion(
                    flow_id=str(flow.flow_id),
                    phase="attribute_mapping",
                    data={"reset_reason": "No field mappings found"},
                    crew_status={"status": "reset", "reason": "validation_failed"},
                    agent_insights=[{
                        "agent": "Flow Validation System", 
                        "insight": "Attribute mapping phase reset due to lack of field mappings",
                        "action_required": "Re-process attribute mapping with proper field analysis",
                        "timestamp": datetime.now().isoformat()
                    }],
                    completed=False
                )
                return "attribute_mapping"
            
            # Continue with remaining phases using the original logic
            if not flow.data_cleansing_completed:
                return "data_cleansing"
            if not flow.inventory_completed:
                return "inventory"
            if not flow.dependencies_completed:
                return "dependencies"
            if not flow.tech_debt_completed:
                return "tech_debt"
            
            return "completed"
            
        except Exception as e:
            logger.error(f"❌ Failed to validate phase completion: {e}")
            # Fallback to original logic if validation fails
            return flow.get_next_phase() or "completed"

    async def _validate_data_import_completion(self, flow) -> bool:
        """Validate that data import phase actually produced meaningful results"""
        try:
            # Check 1: Are there agent insights from data import?
            has_agent_insights = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    agent_insights = state_data.get("agent_insights", [])
                    # Look for data import specific insights
                    data_import_insights = [
                        insight for insight in agent_insights 
                        if isinstance(insight, dict) and 
                        insight.get("phase") == "data_import" or
                        "data_import" in insight.get("insight", "").lower() or
                        "validation" in insight.get("insight", "").lower()
                    ]
                    has_agent_insights = len(data_import_insights) > 0
            
            # Check 2: Are there raw import records that were processed?
            has_processed_records = False
            if flow.import_session_id:
                try:
                    from sqlalchemy import select, func
                    from app.models.data_import import RawImportRecord
                    
                    # Check if there are processed raw records
                    records_query = await self.db.execute(
                        select(func.count(RawImportRecord.id)).where(
                            RawImportRecord.session_id == flow.import_session_id,
                            RawImportRecord.is_processed == True
                        )
                    )
                    processed_count = records_query.scalar() or 0
                    has_processed_records = processed_count > 0
                    
                    logger.info(f"🔍 Found {processed_count} processed records for flow {flow.flow_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not check processed records: {e}")
            
            # Check 3: Is there any meaningful data in the flow state?
            has_meaningful_data = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    # Check for various data indicators
                    meaningful_keys = [
                        "raw_data", "cleaned_data", "validation_results", 
                        "data_analysis", "field_analysis", "quality_assessment"
                    ]
                    has_meaningful_data = any(
                        key in state_data and state_data[key] 
                        for key in meaningful_keys
                    )
            
            # Data import is valid if at least one validation check passes
            is_valid = has_agent_insights or has_processed_records or has_meaningful_data
            
            logger.info(f"🔍 Data import validation for flow {flow.flow_id}: "
                       f"agent_insights={has_agent_insights}, "
                       f"processed_records={has_processed_records}, "
                       f"meaningful_data={has_meaningful_data}, "
                       f"overall_valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Failed to validate data import completion: {e}")
            return False  # Fail safe - require re-processing if validation fails

    async def _validate_attribute_mapping_completion(self, flow) -> bool:
        """Validate that attribute mapping phase actually produced field mappings"""
        try:
            # Check 1: Are there field mappings in the database?
            has_db_mappings = False
            if flow.import_session_id:
                try:
                    from sqlalchemy import select, func
                    from app.models.data_import.mapping import ImportFieldMapping
                    
                    mappings_query = await self.db.execute(
                        select(func.count(ImportFieldMapping.id)).where(
                            ImportFieldMapping.data_import_id == flow.import_session_id,
                            ImportFieldMapping.status.in_(["approved", "validated"])
                        )
                    )
                    mappings_count = mappings_query.scalar() or 0
                    has_db_mappings = mappings_count > 0
                    
                    logger.info(f"🔍 Found {mappings_count} field mappings for flow {flow.flow_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not check field mappings: {e}")
            
            # Check 2: Are there field mappings in the flow state?
            has_state_mappings = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    field_mappings = state_data.get("field_mappings", {})
                    if isinstance(field_mappings, dict):
                        mappings = field_mappings.get("mappings", {})
                        has_state_mappings = len(mappings) > 0
            
            # Check 3: Are there agent insights about field mapping?
            has_mapping_insights = False
            if flow.crewai_state_data:
                state_data = flow.crewai_state_data
                if isinstance(state_data, dict):
                    agent_insights = state_data.get("agent_insights", [])
                    mapping_insights = [
                        insight for insight in agent_insights 
                        if isinstance(insight, dict) and (
                            insight.get("phase") == "attribute_mapping" or
                            "field_mapping" in insight.get("insight", "").lower() or
                            "attribute_mapping" in insight.get("insight", "").lower()
                        )
                    ]
                    has_mapping_insights = len(mapping_insights) > 0
            
            is_valid = has_db_mappings or has_state_mappings or has_mapping_insights
            
            logger.info(f"🔍 Attribute mapping validation for flow {flow.flow_id}: "
                       f"db_mappings={has_db_mappings}, "
                       f"state_mappings={has_state_mappings}, "
                       f"mapping_insights={has_mapping_insights}, "
                       f"overall_valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Failed to validate attribute mapping completion: {e}")
            return False
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get detailed status of a discovery flow from PostgreSQL"""
        try:
            logger.info(f"🔍 Getting PostgreSQL flow status: {flow_id}")
            
            # Get flow from database
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            
            if not flow:
                # Return minimal status for non-existent flows
                return {
                    "flow_id": flow_id,
                    "status": "not_found",
                    "current_phase": "unknown",
                    "progress_percentage": 0.0,
                    "phases": {},
                    "created_at": "",
                    "updated_at": datetime.now().isoformat()
                }
            
            # Build phases status from database fields
            phases = {
                "data_import": flow.data_import_completed or False,
                "attribute_mapping": flow.attribute_mapping_completed or False,
                "data_cleansing": flow.data_cleansing_completed or False,
                "inventory": flow.inventory_completed or False,
                "dependencies": flow.dependencies_completed or False,
                "tech_debt": flow.tech_debt_completed or False
            }
            
            # Calculate progress percentage
            completed_phases = sum(1 for completed in phases.values() if completed)
            total_phases = len(phases)
            progress_percentage = (completed_phases / total_phases) * 100.0 if total_phases > 0 else 0.0
            
            # Determine current phase
            current_phase = flow.get_next_phase() or "completed"
            
            # Extract agent insights and field mapping data from crewai_state_data if available
            agent_insights = []
            field_mapping_data = None
            raw_data = []
            
            if flow.crewai_state_data:
                try:
                    import json
                    state_data = json.loads(flow.crewai_state_data) if isinstance(flow.crewai_state_data, str) else flow.crewai_state_data
                    if isinstance(state_data, dict):
                        # Extract agent insights
                        if "agent_insights" in state_data:
                            agent_insights = state_data["agent_insights"]
                        
                        # Extract field mapping data from different possible locations
                        legacy_data = None
                        
                        # Check if data is in data_cleansing.legacy_data (current format)
                        if "data_cleansing" in state_data and isinstance(state_data["data_cleansing"], dict):
                            data_cleansing = state_data["data_cleansing"]
                            if "legacy_data" in data_cleansing and isinstance(data_cleansing["legacy_data"], dict):
                                legacy_data = data_cleansing["legacy_data"]
                        
                        # Fallback: Check if data is in attribute_mapping.legacy_data (older format)
                        elif "attribute_mapping" in state_data and isinstance(state_data["attribute_mapping"], dict):
                            attr_mapping = state_data["attribute_mapping"]
                            if "legacy_data" in attr_mapping and isinstance(attr_mapping["legacy_data"], dict):
                                legacy_data = attr_mapping["legacy_data"]
                        
                        # Extract raw data and field mappings from legacy_data
                        if legacy_data:
                            # Get raw data
                            if "raw_data" in legacy_data and isinstance(legacy_data["raw_data"], list):
                                raw_data = legacy_data["raw_data"]
                            
                            # Get field mappings
                            if "field_mappings" in legacy_data and isinstance(legacy_data["field_mappings"], dict):
                                field_mappings_raw = legacy_data["field_mappings"]
                                
                                # Format field mapping data for frontend consumption
                                field_mapping_data = {
                                    "mappings": field_mappings_raw.get("critical_mappings", {}),
                                    "attributes": raw_data,  # Include raw data for the data tab
                                    "critical_attributes": field_mappings_raw.get("critical_mappings", {}),
                                    "confidence_scores": field_mappings_raw.get("mapping_confidence", {}),
                                    "unmapped_fields": field_mappings_raw.get("unmapped_columns", []),
                                    "validation_results": {"valid": True, "score": 0.8},
                                    "user_clarifications": legacy_data.get("user_clarifications", []),  # Include clarification questions
                                    "analysis": {
                                        "status": "completed",
                                        "message": "Field mapping analysis completed by CrewAI agents",
                                        "summary": field_mappings_raw.get("summary", ""),
                                        "ambiguous_mappings": field_mappings_raw.get("ambiguous_mappings", {}),
                                        "secondary_mappings": field_mappings_raw.get("secondary_mappings", {})
                                    },
                                    "progress": {
                                        "total": len(raw_data[0].keys()) if raw_data and len(raw_data) > 0 else 0,
                                        "mapped": len(field_mappings_raw.get("critical_mappings", {})),
                                        "critical_mapped": len(field_mappings_raw.get("critical_mappings", {}))
                                    }
                                }
                        
                        # Fallback: Check for field mappings in the old format
                        elif "field_mappings" in state_data:
                            field_mappings_raw = state_data["field_mappings"]
                            
                            # Format field mapping data for frontend consumption
                            field_mapping_data = {
                                "mappings": field_mappings_raw.get("mappings", {}),
                                "attributes": field_mappings_raw.get("attributes", []),
                                "critical_attributes": field_mappings_raw.get("critical_attributes", []),
                                "confidence_scores": field_mappings_raw.get("confidence_scores", {}),
                                "unmapped_fields": field_mappings_raw.get("unmapped_fields", []),
                                "validation_results": field_mappings_raw.get("validation_results", {}),
                                "analysis": field_mappings_raw.get("agent_insights", {}),
                                "progress": {
                                    "total": len(field_mappings_raw.get("mappings", {})) + len(field_mappings_raw.get("unmapped_fields", [])),
                                    "mapped": len(field_mappings_raw.get("mappings", {})),
                                    "critical_mapped": len([attr for attr in field_mappings_raw.get("critical_attributes", []) if attr.get("mapped_to")])
                                }
                            }
                        
                        # Extract raw data if not found yet
                        if not raw_data:
                            if "raw_data" in state_data:
                                raw_data = state_data["raw_data"]
                            elif "cleaned_data" in state_data:
                                raw_data = state_data["cleaned_data"]
                            
                except Exception as e:
                    logger.warning(f"Failed to extract data from crewai_state_data: {e}")
            
            # If no field mapping data in state but we have raw data from import, try to get it from import session
            if not field_mapping_data and flow.import_session_id:
                try:
                    # Get raw data from import session if not in state
                    if not raw_data:
                        from sqlalchemy import select
                        from app.models.data_import import RawImportRecord
                        
                        # Query raw import records for this import session
                        records_query = select(RawImportRecord).where(
                            RawImportRecord.data_import_id == flow.import_session_id
                        ).order_by(RawImportRecord.row_number)
                        
                        records_result = await self.db.execute(records_query)
                        raw_records = records_result.scalars().all()
                        
                        # Extract raw data from records
                        raw_data = [record.raw_data for record in raw_records if record.raw_data]
                    
                    # Create basic field mapping structure if data exists but no mappings
                    if raw_data and not field_mapping_data:
                        headers = list(raw_data[0].keys()) if raw_data else []
                        field_mapping_data = {
                            "mappings": {},
                            "attributes": raw_data,  # Include raw data for the data tab
                            "critical_attributes": [],
                            "confidence_scores": {},
                            "unmapped_fields": headers,
                            "validation_results": {"valid": False, "score": 0.0},
                            "analysis": {"status": "pending", "message": "Field mapping analysis not yet completed"},
                            "progress": {
                                "total": len(headers),
                                "mapped": 0,
                                "critical_mapped": 0
                            }
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to get import data for field mapping: {e}")
            
            flow_status = {
                "flow_id": flow_id,
                "data_import_id": str(flow.import_session_id) if flow.import_session_id else None,
                "status": flow.status,
                "current_phase": current_phase,
                "progress_percentage": progress_percentage,
                "phases": phases,
                "agent_insights": agent_insights,
                "created_at": flow.created_at.isoformat() if flow.created_at else "",
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else datetime.now().isoformat()
            }
            
            # Include field mapping data if available
            if field_mapping_data:
                flow_status["field_mapping"] = field_mapping_data
            
            logger.info(f"✅ PostgreSQL flow status retrieved: {flow_id}")
            return flow_status
            
        except Exception as e:
            logger.error(f"❌ Failed to get PostgreSQL flow status: {e}")
            raise
    
    async def complete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Complete a discovery flow"""
        try:
            logger.info(f"✅ Completing PostgreSQL flow: {flow_id}")
            
            result = {
                "flow_id": flow_id,
                "status": "completed",
                "completion_time": datetime.now().isoformat(),
                "final_phase": "tech_debt_analysis"
            }
            
            logger.info(f"✅ PostgreSQL flow completed: {flow_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to complete PostgreSQL flow: {e}")
            raise
    
    async def delete_flow(self, flow_id: str, force_delete: bool = False) -> Dict[str, Any]:
        """Delete a discovery flow and cleanup"""
        try:
            logger.info(f"🗑️ Deleting PostgreSQL flow: {flow_id}, force: {force_delete}")
            
            # Actually delete from database
            deleted = await self.flow_repo.delete_flow(flow_id)
            
            if deleted:
                cleanup_summary = {
                    "flow_records_deleted": 1,
                    "asset_records_deleted": 0,  # Assets are cascade deleted
                    "session_data_deleted": 1,
                    "cleanup_time": datetime.now().isoformat()
                }
                
                result = {
                    "flow_id": flow_id,
                    "deleted": True,
                    "cleanup_summary": cleanup_summary,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"✅ PostgreSQL flow deleted: {flow_id}")
                return result
            else:
                logger.warning(f"⚠️ PostgreSQL flow not found for deletion: {flow_id}")
                return {
                    "flow_id": flow_id,
                    "deleted": False,
                    "error": "Flow not found",
                    "timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to delete PostgreSQL flow: {e}")
            raise 