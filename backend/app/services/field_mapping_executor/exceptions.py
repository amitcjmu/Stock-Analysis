"""
Field Mapping Executor Exceptions
Custom exceptions for field mapping operations.
"""


class FieldMappingError(Exception):
    """Base exception for field mapping operations"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.context = kwargs


class FieldMappingExecutorError(FieldMappingError):
    """Main executor exception - alias for backward compatibility"""

    pass


class MappingParseError(FieldMappingError):
    """Exception raised when mapping parsing fails"""

    def __init__(self, message: str, raw_text: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.raw_text = raw_text


class MappingValidationError(FieldMappingError):
    """Exception raised when mapping validation fails"""

    def __init__(self, message: str, mappings: dict = None, **kwargs):
        super().__init__(message, **kwargs)
        self.mappings = mappings or {}


class ValidationError(MappingValidationError):
    """Validation error - alias for backward compatibility"""

    pass


class TransformationError(FieldMappingError):
    """Exception raised when transformation fails"""

    def __init__(self, message: str, transformation_type: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.transformation_type = transformation_type


class CrewExecutionError(FieldMappingError):
    """Exception raised when CrewAI execution fails"""

    def __init__(self, message: str, crew_type: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.crew_type = crew_type


class DatabaseUpdateError(FieldMappingError):
    """Exception raised when database updates fail"""

    def __init__(self, message: str, operation: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.operation = operation


class FallbackNotAllowedError(FieldMappingError):
    """Exception raised when fallback is attempted but not allowed"""

    def __init__(self, message: str = "Fallback field mapping not allowed", **kwargs):
        super().__init__(message, **kwargs)


class ConfigurationError(FieldMappingError):
    """Exception raised when configuration is invalid"""

    def __init__(self, message: str, config_key: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key


class TimeoutError(FieldMappingError):
    """Exception raised when operation times out"""

    def __init__(self, message: str, timeout_seconds: int = 0, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds


class MappingEngineError(FieldMappingError):
    """Exception raised when mapping engine operations fail"""

    def __init__(self, message: str, engine_type: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.engine_type = engine_type


class RulesEngineError(FieldMappingError):
    """Exception raised when rules engine operations fail"""

    def __init__(self, message: str, rule_name: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.rule_name = rule_name


class FormattingError(FieldMappingError):
    """Exception raised when formatting operations fail"""

    def __init__(self, message: str, format_type: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.format_type = format_type
