"""
Collection-Specific Exceptions
Custom exception classes for collection flow operations.

Generated with CC for backend collection handler modularization.
"""

from typing import Any, Dict, List, Optional


class CollectionFlowError(Exception):
    """Base exception for collection flow errors"""

    def __init__(
        self,
        message: str,
        flow_id: Optional[str] = None,
        context: Optional[Dict[Any, Any]] = None,
    ):
        self.flow_id = flow_id
        self.context = context or {}
        super().__init__(message)


class CollectionFlowNotFoundError(CollectionFlowError):
    """Exception raised when a collection flow is not found"""

    pass


class CollectionInitializationError(CollectionFlowError):
    """Exception raised during collection flow initialization"""

    pass


class CollectionFinalizationError(CollectionFlowError):
    """Exception raised during collection flow finalization"""

    pass


class PlatformDetectionError(CollectionFlowError):
    """Exception raised during platform detection phase"""

    pass


class AdapterPreparationError(CollectionFlowError):
    """Exception raised during adapter preparation"""

    pass


class DataCollectionError(CollectionFlowError):
    """Exception raised during data collection operations"""

    pass


class DataNormalizationError(CollectionFlowError):
    """Exception raised during data normalization"""

    pass


class GapAnalysisError(CollectionFlowError):
    """Exception raised during gap analysis operations"""

    pass


class QuestionnaireGenerationError(CollectionFlowError):
    """Exception raised during questionnaire generation"""

    pass


class ResponseProcessingError(CollectionFlowError):
    """Exception raised during response processing"""

    pass


class DataSynthesisError(CollectionFlowError):
    """Exception raised during data synthesis operations"""

    pass


class ValidationError(CollectionFlowError):
    """Exception raised during validation operations"""

    def __init__(
        self, message: str, validation_errors: Optional[List[Any]] = None, **kwargs
    ):
        self.validation_errors = validation_errors or []
        super().__init__(message, **kwargs)


class AdapterError(CollectionFlowError):
    """Exception raised by platform adapters"""

    def __init__(
        self,
        message: str,
        adapter_name: Optional[str] = None,
        platform: Optional[str] = None,
        **kwargs
    ):
        self.adapter_name = adapter_name
        self.platform = platform
        super().__init__(message, **kwargs)


class CrewAIExecutionError(CollectionFlowError):
    """Exception raised during CrewAI flow execution"""

    def __init__(self, message: str, crew_error: Optional[Exception] = None, **kwargs):
        self.crew_error = crew_error
        super().__init__(message, **kwargs)


class WriteBackError(CollectionFlowError):
    """Exception raised during asset write-back operations"""

    def __init__(self, message: str, asset_ids: Optional[List[Any]] = None, **kwargs):
        self.asset_ids = asset_ids or []
        super().__init__(message, **kwargs)


class RollbackError(CollectionFlowError):
    """Exception raised during rollback operations"""

    def __init__(self, message: str, rollback_phase: Optional[str] = None, **kwargs):
        self.rollback_phase = rollback_phase
        super().__init__(message, **kwargs)


class CheckpointError(CollectionFlowError):
    """Exception raised during checkpoint operations"""

    pass


class ConfigurationError(CollectionFlowError):
    """Exception raised for invalid collection configuration"""

    def __init__(
        self, message: str, config_errors: Optional[List[Any]] = None, **kwargs
    ):
        self.config_errors = config_errors or []
        super().__init__(message, **kwargs)


class TenantContextError(CollectionFlowError):
    """Exception raised for missing or invalid tenant context"""

    pass


class DataQualityError(CollectionFlowError):
    """Exception raised for data quality issues"""

    def __init__(self, message: str, quality_score: Optional[float] = None, **kwargs):
        self.quality_score = quality_score
        super().__init__(message, **kwargs)


# Utility function to create error context
def create_error_context(
    operation: str,
    phase: Optional[str] = None,
    platform: Optional[str] = None,
    **kwargs
) -> dict:
    """Create standardized error context for collection exceptions"""
    context = {
        "operation": operation,
        "timestamp": kwargs.get("timestamp"),
        "user_id": kwargs.get("user_id"),
        "engagement_id": kwargs.get("engagement_id"),
    }

    if phase:
        context["phase"] = phase
    if platform:
        context["platform"] = platform

    # Add any additional context
    context.update({k: v for k, v in kwargs.items() if v is not None})

    return context
