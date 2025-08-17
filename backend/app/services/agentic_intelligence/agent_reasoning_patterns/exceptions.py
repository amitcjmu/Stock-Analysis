"""
Reasoning-specific exceptions for Agent Intelligence Architecture

This module defines custom exceptions used throughout the agent reasoning patterns
to provide clear error handling and debugging capabilities.
"""


class ReasoningError(Exception):
    """Base exception for agent reasoning errors"""

    def __init__(
        self, message: str, reasoning_dimension: str = None, asset_id: str = None
    ):
        self.reasoning_dimension = reasoning_dimension
        self.asset_id = asset_id
        super().__init__(message)


class PatternMatchingError(ReasoningError):
    """Exception raised when pattern matching fails"""

    def __init__(self, message: str, pattern_id: str = None, **kwargs):
        self.pattern_id = pattern_id
        super().__init__(message, **kwargs)


class EvidenceAnalysisError(ReasoningError):
    """Exception raised during evidence analysis"""

    def __init__(self, message: str, evidence_type: str = None, **kwargs):
        self.evidence_type = evidence_type
        super().__init__(message, **kwargs)


class ConfidenceCalculationError(ReasoningError):
    """Exception raised when confidence calculation fails"""

    def __init__(self, message: str, confidence_factors: list = None, **kwargs):
        self.confidence_factors = confidence_factors or []
        super().__init__(message, **kwargs)


class ReasoningEngineError(ReasoningError):
    """Exception raised by the reasoning engine"""

    def __init__(self, message: str, engine_state: str = None, **kwargs):
        self.engine_state = engine_state
        super().__init__(message, **kwargs)


class PatternDiscoveryError(ReasoningError):
    """Exception raised during pattern discovery"""

    def __init__(self, message: str, discovery_context: dict = None, **kwargs):
        self.discovery_context = discovery_context or {}
        super().__init__(message, **kwargs)


class MemoryIntegrationError(ReasoningError):
    """Exception raised during memory system integration"""

    def __init__(self, message: str, memory_operation: str = None, **kwargs):
        self.memory_operation = memory_operation
        super().__init__(message, **kwargs)
