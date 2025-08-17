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
