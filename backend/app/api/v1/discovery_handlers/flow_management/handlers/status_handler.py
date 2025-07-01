"""
Status Handler

Handles flow status retrieval operations.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import import RawImportRecord
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class StatusHandler:
    """Handles flow status operations"""
    
    def __init__(self, db: AsyncSession, flow_repo: DiscoveryFlowRepository):
        """Initialize with database session and flow repository"""
        self.db = db
        self.flow_repo = flow_repo
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get detailed status of a discovery flow"""
        try:
            logger.info(f"🔍 Getting flow status: {flow_id}")
            
            # Get flow from database
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            
            # Try global search if not found with current context
            if not flow:
                logger.info(f"🔍 Flow not found with current context, trying global search")
                flow = await self.flow_repo.get_by_flow_id_global(flow_id)
                
                if flow:
                    logger.info(f"✅ Flow found globally - updating context")
                    # Update repository context to match found flow
                    self.flow_repo.client_account_id = str(flow.client_account_id)
                    self.flow_repo.engagement_id = str(flow.engagement_id)
            
            if not flow:
                return self._get_not_found_status(flow_id)
            
            # Build status from flow data
            status = await self._build_flow_status(flow)
            
            logger.info(f"✅ Flow status retrieved: {flow_id}")
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get flow status: {e}")
            raise
    
    def _get_not_found_status(self, flow_id: str) -> Dict[str, Any]:
        """Return status for non-existent flow"""
        return {
            "flow_id": flow_id,
            "status": "not_found",
            "current_phase": "unknown",
            "progress_percentage": 0.0,
            "phases": {},
            "created_at": "",
            "updated_at": datetime.now().isoformat()
        }
    
    async def _build_flow_status(self, flow) -> Dict[str, Any]:
        """Build comprehensive flow status from database flow"""
        # Build phases status
        phases = {
            "data_import": flow.data_import_completed or False,
            "attribute_mapping": flow.attribute_mapping_completed or False,
            "data_cleansing": flow.data_cleansing_completed or False,
            "inventory": flow.inventory_completed or False,
            "dependencies": flow.dependencies_completed or False,
            "tech_debt": flow.tech_debt_completed or False
        }
        
        # Calculate progress
        completed_phases = sum(1 for completed in phases.values() if completed)
        total_phases = len(phases)
        progress_percentage = (completed_phases / total_phases) * 100.0 if total_phases > 0 else 0.0
        
        # Determine current phase
        current_phase = flow.get_next_phase() or "completed"
        
        # Extract data from CrewAI state
        extracted_data = self._extract_crewai_state_data(flow)
        
        # Get raw data if not in state
        if not extracted_data["raw_data"] and flow.import_session_id:
            extracted_data["raw_data"] = await self._get_import_raw_data(flow.import_session_id)
        
        # Create field mapping data if we have raw data but no mappings
        if extracted_data["raw_data"] and not extracted_data["field_mapping_data"]:
            extracted_data["field_mapping_data"] = self._create_basic_field_mapping_data(
                extracted_data["raw_data"]
            )
        
        # Build final status
        flow_status = {
            "flow_id": str(flow.flow_id),
            "data_import_id": str(flow.import_session_id) if flow.import_session_id else None,
            "status": flow.status,
            "current_phase": current_phase,
            "progress_percentage": progress_percentage,
            "phases": phases,
            "agent_insights": extracted_data["agent_insights"],
            "created_at": flow.created_at.isoformat() if flow.created_at else "",
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else datetime.now().isoformat(),
            # Processing statistics
            "records_processed": extracted_data["records_processed"],
            "records_total": extracted_data["records_total"],
            "records_valid": extracted_data["records_valid"],
            "records_failed": extracted_data["records_failed"]
        }
        
        # Add optional data if available
        if extracted_data["field_mapping_data"]:
            flow_status["field_mapping"] = extracted_data["field_mapping_data"]
        
        if extracted_data["data_cleansing_results"]:
            flow_status["data_cleansing_results"] = extracted_data["data_cleansing_results"]
        
        if extracted_data["results"]:
            flow_status["results"] = extracted_data["results"]
        
        # Include phase-specific results
        for phase in ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]:
            phase_key = f"{phase}_results"
            if extracted_data.get(phase_key):
                flow_status[phase_key] = extracted_data[phase_key]
        
        return flow_status
    
    def _extract_crewai_state_data(self, flow) -> Dict[str, Any]:
        """Extract data from CrewAI state"""
        extracted = {
            "agent_insights": [],
            "field_mapping_data": None,
            "raw_data": [],
            "data_cleansing_results": None,
            "results": None,
            "records_processed": 0,
            "records_total": 0,
            "records_valid": 0,
            "records_failed": 0
        }
        
        if not flow.crewai_state_data:
            return extracted
        
        try:
            # Parse state data
            state_data = json.loads(flow.crewai_state_data) if isinstance(
                flow.crewai_state_data, str
            ) else flow.crewai_state_data
            
            if not isinstance(state_data, dict):
                return extracted
            
            # Extract agent insights
            extracted["agent_insights"] = state_data.get("agent_insights", [])
            
            # Extract field mapping data
            extracted["field_mapping_data"] = self._extract_field_mapping_data(state_data)
            
            # Extract raw data
            extracted["raw_data"] = self._extract_raw_data(state_data)
            
            # Extract cleansing results
            extracted["data_cleansing_results"] = state_data.get("data_cleansing_results")
            extracted["results"] = state_data.get("results")
            
            # Extract processing statistics
            stats = self._extract_processing_stats(state_data)
            extracted.update(stats)
            
            # Extract phase results
            for phase in ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]:
                phase_key = f"{phase}_results"
                if phase_key in state_data:
                    extracted[phase_key] = state_data[phase_key]
            
        except Exception as e:
            logger.warning(f"Failed to extract CrewAI state data: {e}")
        
        return extracted
    
    def _extract_field_mapping_data(self, state_data: dict) -> Optional[Dict[str, Any]]:
        """Extract field mapping data from various locations in state"""
        # Check data_cleansing.legacy_data (current format)
        legacy_data = None
        
        if "data_cleansing" in state_data and isinstance(state_data["data_cleansing"], dict):
            data_cleansing = state_data["data_cleansing"]
            if "legacy_data" in data_cleansing and isinstance(data_cleansing["legacy_data"], dict):
                legacy_data = data_cleansing["legacy_data"]
        
        # Fallback: Check attribute_mapping.legacy_data
        elif "attribute_mapping" in state_data and isinstance(state_data["attribute_mapping"], dict):
            attr_mapping = state_data["attribute_mapping"]
            if "legacy_data" in attr_mapping and isinstance(attr_mapping["legacy_data"], dict):
                legacy_data = attr_mapping["legacy_data"]
        
        # Extract from legacy_data
        if legacy_data and "field_mappings" in legacy_data:
            field_mappings_raw = legacy_data["field_mappings"]
            raw_data = legacy_data.get("raw_data", [])
            
            return {
                "mappings": field_mappings_raw.get("critical_mappings", {}),
                "attributes": raw_data,
                "critical_attributes": field_mappings_raw.get("critical_mappings", {}),
                "confidence_scores": field_mappings_raw.get("mapping_confidence", {}),
                "unmapped_fields": field_mappings_raw.get("unmapped_columns", []),
                "validation_results": {"valid": True, "score": 0.8},
                "user_clarifications": legacy_data.get("user_clarifications", []),
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
        
        # Fallback: Check direct field_mappings
        elif "field_mappings" in state_data:
            field_mappings_raw = state_data["field_mappings"]
            return self._format_field_mapping_data(field_mappings_raw)
        
        return None
    
    def _extract_raw_data(self, state_data: dict) -> List[Dict[str, Any]]:
        """Extract raw data from various locations in state"""
        # Check in legacy_data first
        if "data_cleansing" in state_data and isinstance(state_data["data_cleansing"], dict):
            legacy_data = state_data["data_cleansing"].get("legacy_data", {})
            if "raw_data" in legacy_data:
                return legacy_data["raw_data"]
        
        # Direct raw_data
        if "raw_data" in state_data:
            return state_data["raw_data"]
        
        # Cleaned data as fallback
        if "cleaned_data" in state_data:
            return state_data["cleaned_data"]
        
        return []
    
    def _extract_processing_stats(self, state_data: dict) -> Dict[str, int]:
        """Extract processing statistics from state data"""
        stats = {
            "records_processed": 0,
            "records_total": 0,
            "records_valid": 0,
            "records_failed": 0
        }
        
        # Check top level
        for key in stats:
            if key in state_data:
                stats[key] = state_data[key]
        
        # Check data_import phase
        if "data_import" in state_data and isinstance(state_data["data_import"], dict):
            data_import = state_data["data_import"]
            for key in stats:
                if key in data_import and not stats[key]:
                    stats[key] = data_import[key]
        
        return stats
    
    async def _get_import_raw_data(self, import_session_id: str) -> List[Dict[str, Any]]:
        """Get raw data from import session"""
        try:
            records_query = select(RawImportRecord).where(
                RawImportRecord.data_import_id == import_session_id
            ).order_by(RawImportRecord.row_number)
            
            records_result = await self.db.execute(records_query)
            raw_records = records_result.scalars().all()
            
            return [record.raw_data for record in raw_records if record.raw_data]
            
        except Exception as e:
            logger.warning(f"Failed to get import data: {e}")
            return []
    
    def _create_basic_field_mapping_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create basic field mapping structure when no mappings exist"""
        headers = list(raw_data[0].keys()) if raw_data else []
        
        return {
            "mappings": {},
            "attributes": raw_data,
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
    
    def _format_field_mapping_data(self, field_mappings_raw: dict) -> Dict[str, Any]:
        """Format raw field mapping data for frontend"""
        return {
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