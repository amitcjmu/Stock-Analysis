"""
Data handler for agent service layer data management operations.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.data_import import DataImport
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class DataHandler:
    """Handles data management operations for the agent service layer."""
    
    def __init__(self, context: RequestContext):
        self.context = context
    
    async def get_import_data(self, flow_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get imported data for a flow"""
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
                        "status": "error",
                        "error": "Flow not found",
                        "data": []
                    }
                
                # Get raw data from flow
                raw_data = flow.raw_data or []
                
                # Apply limit if specified
                if limit and len(raw_data) > limit:
                    limited_data = raw_data[:limit]
                    truncated = True
                else:
                    limited_data = raw_data
                    truncated = False
                
                # Analyze data structure
                data_analysis = self._analyze_raw_data(raw_data)
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "data": limited_data,
                    "metadata": {
                        "total_records": len(raw_data),
                        "returned_records": len(limited_data),
                        "truncated": truncated,
                        "data_import_completed": flow.data_import_completed,
                        "import_timestamp": flow.created_at.isoformat() if flow.created_at else None
                    },
                    "analysis": data_analysis
                }
                
            except Exception as e:
                logger.error(f"Database error in get_import_data: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "data": []
                }
    
    async def get_field_mappings(self, flow_id: str) -> Dict[str, Any]:
        """Get field mappings for a flow"""
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
                        "status": "error",
                        "error": "Flow not found",
                        "mappings": {}
                    }
                
                # Get attribute mapping data
                attribute_mapping_data = getattr(flow, 'attribute_mapping_data', {}) or {}
                field_mappings = attribute_mapping_data.get('field_mappings', {})
                
                # Analyze mapping completeness
                raw_data = flow.raw_data or []
                if raw_data:
                    sample_record = raw_data[0] if isinstance(raw_data, list) and raw_data else {}
                    source_fields = list(sample_record.keys()) if isinstance(sample_record, dict) else []
                else:
                    source_fields = []
                
                mapped_fields = list(field_mappings.keys())
                unmapped_fields = [field for field in source_fields if field not in mapped_fields]
                
                mapping_stats = {
                    "total_source_fields": len(source_fields),
                    "mapped_fields": len(mapped_fields),
                    "unmapped_fields": len(unmapped_fields),
                    "mapping_completeness": (len(mapped_fields) / len(source_fields) * 100) if source_fields else 0
                }
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "mappings": field_mappings,
                    "metadata": {
                        "attribute_mapping_completed": flow.attribute_mapping_completed,
                        "mapping_timestamp": flow.updated_at.isoformat() if flow.updated_at else None
                    },
                    "analysis": {
                        "source_fields": source_fields,
                        "mapped_fields": mapped_fields,
                        "unmapped_fields": unmapped_fields,
                        "statistics": mapping_stats
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in get_field_mappings: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "mappings": {}
                }
    
    async def validate_mappings(self, flow_id: str, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate field mappings"""
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
                        "status": "error",
                        "error": "Flow not found",
                        "is_valid": False
                    }
                
                # Get source data for validation
                raw_data = flow.raw_data or []
                if not raw_data:
                    return {
                        "status": "error",
                        "error": "No source data available for validation",
                        "is_valid": False
                    }
                
                sample_record = raw_data[0] if isinstance(raw_data, list) and raw_data else {}
                source_fields = set(sample_record.keys()) if isinstance(sample_record, dict) else set()
                
                # Validate mappings
                validation_results = []
                is_valid = True
                
                for source_field, target_mapping in mappings.items():
                    field_validation = {
                        "source_field": source_field,
                        "target_mapping": target_mapping,
                        "issues": []
                    }
                    
                    # Check if source field exists
                    if source_field not in source_fields:
                        field_validation["issues"].append("Source field not found in data")
                        is_valid = False
                    
                    # Validate target mapping structure
                    if not isinstance(target_mapping, dict):
                        field_validation["issues"].append("Target mapping must be a dictionary")
                        is_valid = False
                    else:
                        required_keys = ["target_field", "data_type"]
                        for key in required_keys:
                            if key not in target_mapping:
                                field_validation["issues"].append(f"Missing required key: {key}")
                                is_valid = False
                    
                    validation_results.append(field_validation)
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "is_valid": is_valid,
                    "validation_results": validation_results,
                    "summary": {
                        "total_mappings": len(mappings),
                        "valid_mappings": len([r for r in validation_results if not r["issues"]]),
                        "invalid_mappings": len([r for r in validation_results if r["issues"]])
                    }
                }
                
            except Exception as e:
                logger.error(f"Error validating mappings: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "is_valid": False
                }
    
    async def get_cleansing_results(self, flow_id: str) -> Dict[str, Any]:
        """Get data cleansing results"""
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
                        "status": "error",
                        "error": "Flow not found",
                        "results": {}
                    }
                
                # Get data cleansing results
                cleansing_data = getattr(flow, 'data_cleansing_data', {}) or {}
                cleansing_results = cleansing_data.get('cleansing_results', {})
                
                # Extract cleansing statistics
                stats = cleansing_results.get('statistics', {})
                issues_found = cleansing_results.get('issues_found', [])
                corrections_applied = cleansing_results.get('corrections_applied', [])
                
                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "results": cleansing_results,
                    "metadata": {
                        "data_cleansing_completed": flow.data_cleansing_completed,
                        "cleansing_timestamp": flow.updated_at.isoformat() if flow.updated_at else None
                    },
                    "summary": {
                        "total_issues_found": len(issues_found),
                        "corrections_applied": len(corrections_applied),
                        "cleansing_statistics": stats
                    }
                }
                
            except Exception as e:
                logger.error(f"Database error in get_cleansing_results: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "results": {}
                }
    
    async def get_validation_issues(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get validation issues for a flow"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id)
                )
                
                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return [{
                        "issue_type": "system_error",
                        "message": "Flow not found",
                        "severity": "high",
                        "field": None,
                        "suggestions": ["Verify the flow ID and try again"]
                    }]
                
                validation_issues = []
                
                # Check data import validation
                if not flow.data_import_completed:
                    raw_data = flow.raw_data or []
                    if not raw_data:
                        validation_issues.append({
                            "issue_type": "missing_data",
                            "message": "No raw data imported",
                            "severity": "high",
                            "field": "raw_data",
                            "suggestions": ["Import data through the data import interface"]
                        })
                    else:
                        # Validate data structure
                        if isinstance(raw_data, list) and raw_data:
                            sample = raw_data[0]
                            if not isinstance(sample, dict):
                                validation_issues.append({
                                    "issue_type": "data_structure",
                                    "message": "Invalid data structure - expected dictionary records",
                                    "severity": "high",
                                    "field": "raw_data",
                                    "suggestions": ["Ensure data is in proper JSON format"]
                                })
                
                # Check attribute mapping validation
                if not flow.attribute_mapping_completed:
                    validation_issues.append({
                        "issue_type": "incomplete_mapping",
                        "message": "Attribute mapping not completed",
                        "severity": "medium",
                        "field": "attribute_mapping",
                        "suggestions": ["Complete field mapping in the attribute mapping phase"]
                    })
                
                # Check data cleansing validation
                if not flow.data_cleansing_completed:
                    validation_issues.append({
                        "issue_type": "incomplete_cleansing",
                        "message": "Data cleansing not completed",
                        "severity": "medium",
                        "field": "data_cleansing",
                        "suggestions": ["Run data cleansing process to identify and fix data quality issues"]
                    })
                
                # Check progress validation
                if flow.progress_percentage and flow.progress_percentage < 50:
                    validation_issues.append({
                        "issue_type": "low_progress",
                        "message": f"Flow progress is only {flow.progress_percentage}%",
                        "severity": "low",
                        "field": "progress",
                        "suggestions": ["Continue with the discovery phases to increase progress"]
                    })
                
                return validation_issues
                
            except Exception as e:
                logger.error(f"Database error in get_validation_issues: {e}")
                return [{
                    "issue_type": "system_error",
                    "message": str(e),
                    "severity": "high",
                    "field": None,
                    "suggestions": ["Contact system administrator"]
                }]
    
    def _analyze_raw_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze raw data structure and quality"""
        if not raw_data:
            return {
                "record_count": 0,
                "field_analysis": {},
                "data_quality": {
                    "completeness": 0,
                    "consistency": 0,
                    "issues": ["No data available"]
                }
            }
        
        # Analyze first few records to understand structure
        sample_size = min(10, len(raw_data))
        sample_records = raw_data[:sample_size]
        
        # Field analysis
        all_fields = set()
        field_types = {}
        field_presence = {}
        
        for record in sample_records:
            if isinstance(record, dict):
                for field, value in record.items():
                    all_fields.add(field)
                    
                    # Track field presence
                    field_presence[field] = field_presence.get(field, 0) + 1
                    
                    # Track field types
                    value_type = type(value).__name__
                    if field not in field_types:
                        field_types[field] = {}
                    field_types[field][value_type] = field_types[field].get(value_type, 0) + 1
        
        # Calculate completeness
        completeness = {}
        for field in all_fields:
            completeness[field] = (field_presence.get(field, 0) / sample_size) * 100
        
        # Overall data quality assessment
        avg_completeness = sum(completeness.values()) / len(completeness) if completeness else 0
        
        issues = []
        if avg_completeness < 80:
            issues.append("Low data completeness detected")
        if len(all_fields) < 3:
            issues.append("Limited number of fields detected")
        
        return {
            "record_count": len(raw_data),
            "sample_size": sample_size,
            "field_analysis": {
                "total_fields": len(all_fields),
                "fields": list(all_fields),
                "field_types": field_types,
                "field_completeness": completeness
            },
            "data_quality": {
                "completeness": round(avg_completeness, 2),
                "consistency": 100,  # Simplified for now
                "issues": issues
            }
        }