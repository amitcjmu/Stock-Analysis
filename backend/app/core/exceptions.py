"""
Core exception classes for the AI Force Migration Platform.
"""

from typing import Optional, Dict, Any


class BaseApplicationError(Exception):
    """Base exception class for application-specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseApplicationError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field
        self.value = value


class ConfigurationError(BaseApplicationError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        self.config_key = config_key


class DatabaseError(BaseApplicationError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)
        self.operation = operation


class AuthenticationError(BaseApplicationError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(BaseApplicationError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", resource: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="AUTHORIZATION_ERROR", **kwargs)
        self.resource = resource


class DataProcessingError(BaseApplicationError):
    """Raised when data processing operations fail."""
    
    def __init__(self, message: str, stage: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="DATA_PROCESSING_ERROR", **kwargs)
        self.stage = stage


class AgentError(BaseApplicationError):
    """Raised when AI agent operations fail."""
    
    def __init__(self, message: str, agent_name: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="AGENT_ERROR", **kwargs)
        self.agent_name = agent_name


class FlowError(BaseApplicationError):
    """Raised when CrewAI flow operations fail."""
    
    def __init__(self, message: str, flow_name: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="FLOW_ERROR", **kwargs)
        self.flow_name = flow_name


class DependencyError(BaseApplicationError):
    """Raised when dependency analysis fails."""
    
    def __init__(self, message: str, dependency_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="DEPENDENCY_ERROR", **kwargs)
        self.dependency_type = dependency_type


class MigrationError(BaseApplicationError):
    """Raised when migration operations fail."""
    
    def __init__(self, message: str, migration_stage: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="MIGRATION_ERROR", **kwargs)
        self.migration_stage = migration_stage 