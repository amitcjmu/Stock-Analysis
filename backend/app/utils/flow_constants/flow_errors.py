"""
Flow error definitions and management utilities.
Provides standardized error types, codes, and error handling patterns.
"""

from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

class FlowErrorType(str, Enum):
    """Types of flow errors."""
    VALIDATION_ERROR = "validation_error"
    DATA_ERROR = "data_error"
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SYSTEM_ERROR = "system_error"
    AGENT_ERROR = "agent_error"
    CREW_ERROR = "crew_error"
    TASK_ERROR = "task_error"
    DEPENDENCY_ERROR = "dependency_error"
    INTEGRATION_ERROR = "integration_error"

class FlowErrorSeverity(str, Enum):
    """Severity levels for flow errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"

class FlowErrorCode(str, Enum):
    """Specific error codes for flow operations."""
    # Data Import Errors
    IMPORT_FILE_NOT_FOUND = "IMPORT_FILE_NOT_FOUND"
    IMPORT_INVALID_FORMAT = "IMPORT_INVALID_FORMAT"
    IMPORT_PARSING_ERROR = "IMPORT_PARSING_ERROR"
    IMPORT_SIZE_LIMIT_EXCEEDED = "IMPORT_SIZE_LIMIT_EXCEEDED"
    IMPORT_VALIDATION_FAILED = "IMPORT_VALIDATION_FAILED"
    
    # Field Mapping Errors
    MAPPING_FIELD_NOT_FOUND = "MAPPING_FIELD_NOT_FOUND"
    MAPPING_TYPE_MISMATCH = "MAPPING_TYPE_MISMATCH"
    MAPPING_VALIDATION_FAILED = "MAPPING_VALIDATION_FAILED"
    MAPPING_REQUIRED_FIELD_MISSING = "MAPPING_REQUIRED_FIELD_MISSING"
    
    # Data Cleansing Errors
    CLEANSING_INVALID_DATA = "CLEANSING_INVALID_DATA"
    CLEANSING_TRANSFORMATION_FAILED = "CLEANSING_TRANSFORMATION_FAILED"
    CLEANSING_QUALITY_CHECK_FAILED = "CLEANSING_QUALITY_CHECK_FAILED"
    
    # Asset Inventory Errors
    INVENTORY_DUPLICATE_ASSET = "INVENTORY_DUPLICATE_ASSET"
    INVENTORY_MISSING_METADATA = "INVENTORY_MISSING_METADATA"
    INVENTORY_CLASSIFICATION_FAILED = "INVENTORY_CLASSIFICATION_FAILED"
    
    # Dependency Analysis Errors
    DEPENDENCY_CIRCULAR_REFERENCE = "DEPENDENCY_CIRCULAR_REFERENCE"
    DEPENDENCY_MISSING_REFERENCE = "DEPENDENCY_MISSING_REFERENCE"
    DEPENDENCY_ANALYSIS_TIMEOUT = "DEPENDENCY_ANALYSIS_TIMEOUT"
    
    # Tech Debt Analysis Errors
    TECH_DEBT_ANALYSIS_FAILED = "TECH_DEBT_ANALYSIS_FAILED"
    TECH_DEBT_SCORING_ERROR = "TECH_DEBT_SCORING_ERROR"
    TECH_DEBT_INSUFFICIENT_DATA = "TECH_DEBT_INSUFFICIENT_DATA"
    
    # Agent/Crew Errors
    AGENT_INITIALIZATION_FAILED = "AGENT_INITIALIZATION_FAILED"
    AGENT_EXECUTION_FAILED = "AGENT_EXECUTION_FAILED"
    AGENT_COMMUNICATION_ERROR = "AGENT_COMMUNICATION_ERROR"
    CREW_COLLABORATION_FAILED = "CREW_COLLABORATION_FAILED"
    CREW_DELEGATION_ERROR = "CREW_DELEGATION_ERROR"
    
    # System Errors
    SYSTEM_RESOURCE_EXHAUSTED = "SYSTEM_RESOURCE_EXHAUSTED"
    SYSTEM_TIMEOUT = "SYSTEM_TIMEOUT"
    SYSTEM_CONFIGURATION_ERROR = "SYSTEM_CONFIGURATION_ERROR"
    SYSTEM_DATABASE_ERROR = "SYSTEM_DATABASE_ERROR"
    
    # Authentication/Authorization Errors
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    
    # External Service Errors
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_RATE_LIMITED = "EXTERNAL_SERVICE_RATE_LIMITED"
    
    # Generic Errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    OPERATION_CANCELLED = "OPERATION_CANCELLED"
    OPERATION_TIMEOUT = "OPERATION_TIMEOUT"

@dataclass
class FlowError:
    """Comprehensive flow error information."""
    error_type: FlowErrorType
    error_code: FlowErrorCode
    severity: FlowErrorSeverity
    message: str
    phase: Optional[str] = None
    component: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    recoverable: bool = True
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def is_critical(self) -> bool:
        """Check if error is critical."""
        return self.severity in {FlowErrorSeverity.CRITICAL, FlowErrorSeverity.FATAL}
    
    def is_recoverable(self) -> bool:
        """Check if error is recoverable."""
        return self.recoverable and self.retry_count < self.max_retries
    
    def can_retry(self) -> bool:
        """Check if error can be retried."""
        return self.recoverable and self.retry_count < self.max_retries and self.severity != FlowErrorSeverity.FATAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "error_type": self.error_type.value,
            "error_code": self.error_code.value,
            "severity": self.severity.value,
            "message": self.message,
            "phase": self.phase,
            "component": self.component,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

# Error message templates
FLOW_ERROR_MESSAGES: Dict[FlowErrorCode, str] = {
    # Data Import Errors
    FlowErrorCode.IMPORT_FILE_NOT_FOUND: "Import file not found: {file_path}",
    FlowErrorCode.IMPORT_INVALID_FORMAT: "Invalid file format: {format}. Expected: {expected_format}",
    FlowErrorCode.IMPORT_PARSING_ERROR: "Error parsing import file: {error_detail}",
    FlowErrorCode.IMPORT_SIZE_LIMIT_EXCEEDED: "File size {size} exceeds limit of {limit}",
    FlowErrorCode.IMPORT_VALIDATION_FAILED: "Import validation failed: {validation_errors}",
    
    # Field Mapping Errors
    FlowErrorCode.MAPPING_FIELD_NOT_FOUND: "Field not found: {field_name}",
    FlowErrorCode.MAPPING_TYPE_MISMATCH: "Type mismatch for field {field_name}: expected {expected_type}, got {actual_type}",
    FlowErrorCode.MAPPING_VALIDATION_FAILED: "Mapping validation failed: {validation_errors}",
    FlowErrorCode.MAPPING_REQUIRED_FIELD_MISSING: "Required field missing: {field_name}",
    
    # Data Cleansing Errors
    FlowErrorCode.CLEANSING_INVALID_DATA: "Invalid data detected in field {field_name}: {value}",
    FlowErrorCode.CLEANSING_TRANSFORMATION_FAILED: "Data transformation failed: {transformation_rule}",
    FlowErrorCode.CLEANSING_QUALITY_CHECK_FAILED: "Quality check failed: {quality_rule}",
    
    # Asset Inventory Errors
    FlowErrorCode.INVENTORY_DUPLICATE_ASSET: "Duplicate asset detected: {asset_id}",
    FlowErrorCode.INVENTORY_MISSING_METADATA: "Missing required metadata for asset: {asset_id}",
    FlowErrorCode.INVENTORY_CLASSIFICATION_FAILED: "Asset classification failed: {classification_error}",
    
    # Dependency Analysis Errors
    FlowErrorCode.DEPENDENCY_CIRCULAR_REFERENCE: "Circular dependency detected: {dependency_chain}",
    FlowErrorCode.DEPENDENCY_MISSING_REFERENCE: "Missing dependency reference: {reference_id}",
    FlowErrorCode.DEPENDENCY_ANALYSIS_TIMEOUT: "Dependency analysis timed out after {timeout} seconds",
    
    # Tech Debt Analysis Errors
    FlowErrorCode.TECH_DEBT_ANALYSIS_FAILED: "Tech debt analysis failed: {analysis_error}",
    FlowErrorCode.TECH_DEBT_SCORING_ERROR: "Tech debt scoring error: {scoring_error}",
    FlowErrorCode.TECH_DEBT_INSUFFICIENT_DATA: "Insufficient data for tech debt analysis: {missing_data}",
    
    # Agent/Crew Errors
    FlowErrorCode.AGENT_INITIALIZATION_FAILED: "Agent initialization failed: {agent_name}",
    FlowErrorCode.AGENT_EXECUTION_FAILED: "Agent execution failed: {execution_error}",
    FlowErrorCode.AGENT_COMMUNICATION_ERROR: "Agent communication error: {communication_error}",
    FlowErrorCode.CREW_COLLABORATION_FAILED: "Crew collaboration failed: {collaboration_error}",
    FlowErrorCode.CREW_DELEGATION_ERROR: "Crew delegation error: {delegation_error}",
    
    # System Errors
    FlowErrorCode.SYSTEM_RESOURCE_EXHAUSTED: "System resource exhausted: {resource_type}",
    FlowErrorCode.SYSTEM_TIMEOUT: "System timeout after {timeout} seconds",
    FlowErrorCode.SYSTEM_CONFIGURATION_ERROR: "System configuration error: {config_error}",
    FlowErrorCode.SYSTEM_DATABASE_ERROR: "Database error: {database_error}",
    
    # Authentication/Authorization Errors
    FlowErrorCode.AUTH_TOKEN_EXPIRED: "Authentication token expired",
    FlowErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: "Insufficient permissions for operation: {operation}",
    FlowErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid credentials provided",
    
    # External Service Errors
    FlowErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: "External service unavailable: {service_name}",
    FlowErrorCode.EXTERNAL_SERVICE_TIMEOUT: "External service timeout: {service_name}",
    FlowErrorCode.EXTERNAL_SERVICE_RATE_LIMITED: "Rate limited by external service: {service_name}",
    
    # Generic Errors
    FlowErrorCode.UNKNOWN_ERROR: "Unknown error occurred: {error_detail}",
    FlowErrorCode.OPERATION_CANCELLED: "Operation was cancelled",
    FlowErrorCode.OPERATION_TIMEOUT: "Operation timed out after {timeout} seconds"
}

# Error severity mappings
ERROR_SEVERITY_MAP: Dict[FlowErrorCode, FlowErrorSeverity] = {
    # Critical errors that stop flow execution
    FlowErrorCode.SYSTEM_RESOURCE_EXHAUSTED: FlowErrorSeverity.CRITICAL,
    FlowErrorCode.SYSTEM_DATABASE_ERROR: FlowErrorSeverity.CRITICAL,
    FlowErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: FlowErrorSeverity.CRITICAL,
    FlowErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: FlowErrorSeverity.CRITICAL,
    
    # Error-level issues that may be recoverable
    FlowErrorCode.IMPORT_FILE_NOT_FOUND: FlowErrorSeverity.ERROR,
    FlowErrorCode.IMPORT_INVALID_FORMAT: FlowErrorSeverity.ERROR,
    FlowErrorCode.MAPPING_VALIDATION_FAILED: FlowErrorSeverity.ERROR,
    FlowErrorCode.AGENT_EXECUTION_FAILED: FlowErrorSeverity.ERROR,
    FlowErrorCode.CREW_COLLABORATION_FAILED: FlowErrorSeverity.ERROR,
    
    # Warning-level issues
    FlowErrorCode.INVENTORY_DUPLICATE_ASSET: FlowErrorSeverity.WARNING,
    FlowErrorCode.CLEANSING_INVALID_DATA: FlowErrorSeverity.WARNING,
    FlowErrorCode.TECH_DEBT_INSUFFICIENT_DATA: FlowErrorSeverity.WARNING,
    
    # Info-level issues
    FlowErrorCode.OPERATION_CANCELLED: FlowErrorSeverity.INFO,
}

# Recoverable error types
RECOVERABLE_ERROR_CODES = {
    FlowErrorCode.SYSTEM_TIMEOUT,
    FlowErrorCode.EXTERNAL_SERVICE_TIMEOUT,
    FlowErrorCode.EXTERNAL_SERVICE_RATE_LIMITED,
    FlowErrorCode.AGENT_COMMUNICATION_ERROR,
    FlowErrorCode.OPERATION_TIMEOUT,
    FlowErrorCode.DEPENDENCY_ANALYSIS_TIMEOUT
}

# Helper functions
def create_flow_error(
    error_type: FlowErrorType,
    error_code: FlowErrorCode,
    message: Optional[str] = None,
    severity: Optional[FlowErrorSeverity] = None,
    phase: Optional[str] = None,
    component: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs
) -> FlowError:
    """Create a flow error with appropriate defaults."""
    if message is None:
        message = get_error_message(error_code, **kwargs)
    
    if severity is None:
        severity = get_error_severity(error_code)
    
    recoverable = error_code in RECOVERABLE_ERROR_CODES
    
    return FlowError(
        error_type=error_type,
        error_code=error_code,
        severity=severity,
        message=message,
        phase=phase,
        component=component,
        details=details,
        recoverable=recoverable
    )

def get_error_message(error_code: FlowErrorCode, **kwargs) -> str:
    """Get error message template and format with provided arguments."""
    template = FLOW_ERROR_MESSAGES.get(error_code, "Unknown error: {error_code}")
    try:
        return template.format(error_code=error_code.value, **kwargs)
    except KeyError as e:
        return f"Error formatting message for {error_code.value}: missing argument {e}"

def get_error_severity(error_code: FlowErrorCode) -> FlowErrorSeverity:
    """Get the default severity for an error code."""
    return ERROR_SEVERITY_MAP.get(error_code, FlowErrorSeverity.ERROR)

def is_recoverable_error(error_code: FlowErrorCode) -> bool:
    """Check if an error is recoverable."""
    return error_code in RECOVERABLE_ERROR_CODES

def is_critical_error(error_code: FlowErrorCode) -> bool:
    """Check if an error is critical."""
    severity = get_error_severity(error_code)
    return severity in {FlowErrorSeverity.CRITICAL, FlowErrorSeverity.FATAL}

def get_error_type_for_code(error_code: FlowErrorCode) -> FlowErrorType:
    """Get the appropriate error type for an error code."""
    code_to_type_map = {
        # Data Import Errors
        FlowErrorCode.IMPORT_FILE_NOT_FOUND: FlowErrorType.DATA_ERROR,
        FlowErrorCode.IMPORT_INVALID_FORMAT: FlowErrorType.DATA_ERROR,
        FlowErrorCode.IMPORT_PARSING_ERROR: FlowErrorType.DATA_ERROR,
        FlowErrorCode.IMPORT_SIZE_LIMIT_EXCEEDED: FlowErrorType.VALIDATION_ERROR,
        FlowErrorCode.IMPORT_VALIDATION_FAILED: FlowErrorType.VALIDATION_ERROR,
        
        # Field Mapping Errors
        FlowErrorCode.MAPPING_FIELD_NOT_FOUND: FlowErrorType.DATA_ERROR,
        FlowErrorCode.MAPPING_TYPE_MISMATCH: FlowErrorType.VALIDATION_ERROR,
        FlowErrorCode.MAPPING_VALIDATION_FAILED: FlowErrorType.VALIDATION_ERROR,
        FlowErrorCode.MAPPING_REQUIRED_FIELD_MISSING: FlowErrorType.VALIDATION_ERROR,
        
        # System Errors
        FlowErrorCode.SYSTEM_RESOURCE_EXHAUSTED: FlowErrorType.SYSTEM_ERROR,
        FlowErrorCode.SYSTEM_TIMEOUT: FlowErrorType.TIMEOUT_ERROR,
        FlowErrorCode.SYSTEM_CONFIGURATION_ERROR: FlowErrorType.CONFIGURATION_ERROR,
        FlowErrorCode.SYSTEM_DATABASE_ERROR: FlowErrorType.SYSTEM_ERROR,
        
        # Agent/Crew Errors
        FlowErrorCode.AGENT_INITIALIZATION_FAILED: FlowErrorType.AGENT_ERROR,
        FlowErrorCode.AGENT_EXECUTION_FAILED: FlowErrorType.AGENT_ERROR,
        FlowErrorCode.AGENT_COMMUNICATION_ERROR: FlowErrorType.AGENT_ERROR,
        FlowErrorCode.CREW_COLLABORATION_FAILED: FlowErrorType.CREW_ERROR,
        FlowErrorCode.CREW_DELEGATION_ERROR: FlowErrorType.CREW_ERROR,
        
        # Authentication/Authorization Errors
        FlowErrorCode.AUTH_TOKEN_EXPIRED: FlowErrorType.AUTHENTICATION_ERROR,
        FlowErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: FlowErrorType.AUTHORIZATION_ERROR,
        FlowErrorCode.AUTH_INVALID_CREDENTIALS: FlowErrorType.AUTHENTICATION_ERROR,
        
        # External Service Errors
        FlowErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: FlowErrorType.EXTERNAL_SERVICE_ERROR,
        FlowErrorCode.EXTERNAL_SERVICE_TIMEOUT: FlowErrorType.EXTERNAL_SERVICE_ERROR,
        FlowErrorCode.EXTERNAL_SERVICE_RATE_LIMITED: FlowErrorType.EXTERNAL_SERVICE_ERROR,
    }
    
    return code_to_type_map.get(error_code, FlowErrorType.SYSTEM_ERROR)