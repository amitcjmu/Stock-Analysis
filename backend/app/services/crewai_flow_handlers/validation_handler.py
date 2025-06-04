"""
Validation Handler for CrewAI Flow Service
Handles input validation, data quality checks, and validation workflows.
"""

import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class DiscoveryFlowState(BaseModel):
    """Structured state for Discovery phase workflow with validation."""
    # Input data
    cmdb_data: Dict[str, Any] = {}
    filename: str = ""
    headers: List[str] = []
    sample_data: List[Dict[str, Any]] = []
    
    # Analysis progress
    data_validation_complete: bool = False
    field_mapping_complete: bool = False
    asset_classification_complete: bool = False
    dependency_analysis_complete: bool = False
    readiness_assessment_complete: bool = False
    
    # Analysis results
    validated_structure: Dict[str, Any] = {}
    suggested_field_mappings: Dict[str, str] = {}
    asset_classifications: List[Dict[str, Any]] = []
    dependency_map: Dict[str, List[str]] = {}
    readiness_scores: Dict[str, float] = {}
    
    # Workflow metrics
    progress_percentage: float = 0.0
    current_phase: str = "initialization"
    started_at: Any = None  # Optional[datetime] 
    completed_at: Any = None  # Optional[datetime]
    
    # Agent outputs
    agent_insights: Dict[str, Any] = {}
    recommendations: List[str] = []
    
    @validator('headers')
    def headers_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Headers cannot be empty')
        return v
    
    @validator('sample_data')
    def sample_data_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Sample data cannot be empty')
        return v

class ValidationHandler:
    """Handler for input validation and data quality operations."""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for different data types."""
        return {
            "required_fields": ["headers", "sample_data"],
            "min_headers": 1,
            "min_sample_records": 1,
            "max_sample_records": 100,
            "supported_file_types": [".csv", ".xlsx", ".json"],
            "critical_attributes": [
                "asset_name", "ci_type", "environment", "business_owner",
                "technical_owner", "location", "dependencies", "risk_level"
            ]
        }
    
    def validate_input_data(self, cmdb_data: Dict[str, Any]) -> None:
        """Comprehensive input validation before processing."""
        if not isinstance(cmdb_data, dict):
            raise ValueError("cmdb_data must be a dictionary")
        
        # Check required fields
        for field in self.validation_rules["required_fields"]:
            if not cmdb_data.get(field):
                raise ValueError(f"cmdb_data must contain '{field}' field")
        
        headers = cmdb_data['headers']
        sample_data = cmdb_data['sample_data']
        
        # Validate headers
        self._validate_headers(headers)
        
        # Validate sample data
        self._validate_sample_data(sample_data, headers)
        
        # Validate file metadata
        self._validate_file_metadata(cmdb_data)
        
        logger.info(f"Input validation passed: {len(headers)} headers, {len(sample_data)} records")
    
    def _validate_headers(self, headers: List[str]) -> None:
        """Validate headers structure and content."""
        if not isinstance(headers, list):
            raise ValueError("headers must be a list")
        
        if len(headers) < self.validation_rules["min_headers"]:
            raise ValueError(f"headers must contain at least {self.validation_rules['min_headers']} header(s)")
        
        # Check for duplicate headers
        if len(headers) != len(set(headers)):
            raise ValueError("headers must not contain duplicates")
        
        # Check for empty or invalid headers
        for i, header in enumerate(headers):
            if not isinstance(header, str) or not header.strip():
                raise ValueError(f"headers[{i}] must be a non-empty string")
    
    def _validate_sample_data(self, sample_data: List[Dict[str, Any]], headers: List[str]) -> None:
        """Validate sample data structure and content."""
        if not isinstance(sample_data, list):
            raise ValueError("sample_data must be a list")
        
        min_records = self.validation_rules["min_sample_records"]
        max_records = self.validation_rules["max_sample_records"]
        
        if len(sample_data) < min_records:
            raise ValueError(f"sample_data must contain at least {min_records} record(s)")
        
        if len(sample_data) > max_records:
            raise ValueError(f"sample_data must not exceed {max_records} records")
        
        # Validate each record
        for i, record in enumerate(sample_data[:5]):  # Check first 5 records
            if not isinstance(record, dict):
                raise ValueError(f"sample_data[{i}] must be a dictionary")
            
            # Check if record has values for headers
            missing_headers = [h for h in headers if h not in record]
            if missing_headers and len(missing_headers) > len(headers) * 0.5:  # Allow up to 50% missing
                logger.warning(f"Record {i} missing many headers: {missing_headers}")
    
    def _validate_file_metadata(self, cmdb_data: Dict[str, Any]) -> None:
        """Validate file metadata and format."""
        filename = cmdb_data.get('filename', '')
        
        if filename:
            # Check file extension if provided
            supported_types = self.validation_rules["supported_file_types"]
            if not any(filename.lower().endswith(ext) for ext in supported_types):
                logger.warning(f"File type may not be supported. Supported: {supported_types}")
    
    def assess_data_quality(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data quality for migration readiness."""
        headers = cmdb_data.get('headers', [])
        sample_data = cmdb_data.get('sample_data', [])
        
        quality_metrics = {
            "completeness_score": self._calculate_completeness(sample_data, headers),
            "consistency_score": self._calculate_consistency(sample_data),
            "critical_field_coverage": self._assess_critical_field_coverage(headers),
            "data_format_quality": self._assess_data_format_quality(sample_data),
            "overall_quality_score": 0.0
        }
        
        # Calculate weighted overall score
        quality_metrics["overall_quality_score"] = (
            quality_metrics["completeness_score"] * 0.3 +
            quality_metrics["consistency_score"] * 0.25 +
            quality_metrics["critical_field_coverage"] * 0.3 +
            quality_metrics["data_format_quality"] * 0.15
        )
        
        return quality_metrics
    
    def _calculate_completeness(self, sample_data: List[Dict[str, Any]], headers: List[str]) -> float:
        """Calculate data completeness score (0-10)."""
        if not sample_data or not headers:
            return 0.0
        
        total_cells = len(sample_data) * len(headers)
        filled_cells = 0
        
        for record in sample_data:
            for header in headers:
                value = record.get(header)
                if value is not None and str(value).strip():
                    filled_cells += 1
        
        completeness_ratio = filled_cells / max(total_cells, 1)
        return completeness_ratio * 10.0
    
    def _calculate_consistency(self, sample_data: List[Dict[str, Any]]) -> float:
        """Calculate data consistency score (0-10)."""
        if len(sample_data) < 2:
            return 8.0  # Assume good consistency for small datasets
        
        consistency_issues = 0
        total_checks = 0
        
        # Check for consistent data types within columns
        for record in sample_data[:10]:  # Check first 10 records
            for key, value in record.items():
                if value is not None:
                    # Check if similar keys have similar data types
                    total_checks += 1
                    # Simple consistency check - could be enhanced
        
        # Placeholder logic - could be enhanced with more sophisticated checks
        consistency_ratio = max(0.0, 1.0 - (consistency_issues / max(total_checks, 1)))
        return consistency_ratio * 10.0
    
    def _assess_critical_field_coverage(self, headers: List[str]) -> float:
        """Assess coverage of critical migration attributes (0-10)."""
        critical_attrs = self.validation_rules["critical_attributes"]
        headers_lower = [h.lower() for h in headers]
        
        covered_attributes = 0
        for attr in critical_attrs:
            # Check for exact matches or partial matches
            if any(attr.lower() in header_lower or header_lower in attr.lower() 
                   for header_lower in headers_lower):
                covered_attributes += 1
        
        coverage_ratio = covered_attributes / len(critical_attrs)
        return coverage_ratio * 10.0
    
    def _assess_data_format_quality(self, sample_data: List[Dict[str, Any]]) -> float:
        """Assess data format quality (0-10)."""
        if not sample_data:
            return 0.0
        
        format_issues = 0
        total_values = 0
        
        for record in sample_data[:5]:  # Check first 5 records
            for key, value in record.items():
                if value is not None:
                    total_values += 1
                    value_str = str(value).strip()
                    
                    # Check for common format issues
                    if not value_str:  # Empty after strip
                        format_issues += 1
                    elif len(value_str) > 1000:  # Extremely long values
                        format_issues += 1
                    elif value_str.lower() in ['null', 'n/a', 'none', 'undefined']:
                        format_issues += 1
        
        format_quality = max(0.0, 1.0 - (format_issues / max(total_values, 1)))
        return format_quality * 10.0
    
    def create_flow_state(self, cmdb_data: Dict[str, Any], flow_id: str) -> DiscoveryFlowState:
        """Create and validate flow state from input data."""
        try:
            from datetime import datetime
            
            flow_state = DiscoveryFlowState(
                cmdb_data=cmdb_data,
                filename=cmdb_data.get('filename', 'unknown'),
                headers=cmdb_data.get('headers', []),
                sample_data=cmdb_data.get('sample_data', []),
                started_at=datetime.now(),
                current_phase="initialization"
            )
            
            logger.info(f"Flow state created successfully for {flow_id}")
            return flow_state
            
        except Exception as e:
            logger.error(f"Failed to create flow state: {e}")
            raise ValueError(f"Flow state creation failed: {e}")
    
    def validate_phase_transition(self, flow_state: DiscoveryFlowState, target_phase: str) -> bool:
        """Validate if flow can transition to target phase."""
        phase_dependencies = {
            "data_validation": [],
            "field_mapping": ["data_validation"],
            "asset_classification": ["data_validation"],  # Can run parallel with field_mapping
            "readiness_assessment": ["data_validation", "field_mapping", "asset_classification"]
        }
        
        required_phases = phase_dependencies.get(target_phase, [])
        
        for required_phase in required_phases:
            phase_complete = getattr(flow_state, f"{required_phase}_complete", False)
            if not phase_complete:
                logger.warning(f"Cannot transition to {target_phase}: {required_phase} not complete")
                return False
        
        return True
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation handler summary."""
        return {
            "handler": "validation_handler",
            "version": "1.0.0",
            "validation_rules": self.validation_rules,
            "supported_operations": [
                "input_validation",
                "data_quality_assessment", 
                "flow_state_creation",
                "phase_transition_validation"
            ]
        } 