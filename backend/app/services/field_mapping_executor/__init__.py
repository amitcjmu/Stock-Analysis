"""
Field Mapping Executor - Modular Architecture

A modularized field mapping executor that breaks down the complex field mapping
operations into specialized, testable components while maintaining complete
backward compatibility with the original implementation.

Architecture Overview:
- base.py: Core FieldMappingExecutor class that orchestrates all components
- exceptions.py: Custom exception hierarchy for field mapping operations
- parsers.py: Composite parser with multiple parsing strategies
- validation.py: Comprehensive validation with multiple validators
- mapping_engine.py: Intelligent mapping algorithms and similarity calculations
- transformation.py: Data transformation and database persistence
- rules_engine.py: Business rules and clarification generation
- formatters.py: Response and output formatting

This modular design reduces complexity, improves maintainability, and enables
better testing while preserving the exact same public interface.
"""

# Core executor class
from .base import FieldMappingExecutor

# Exception classes
from .exceptions import (
    FieldMappingExecutorError,
    MappingParseError,
    ValidationError,
    CrewExecutionError,
    TransformationError,
    MappingEngineError,
    RulesEngineError,
    FormattingError,
)

# Parser classes
from .parsers import (
    BaseMappingParser,
    JSONMappingParser,
    PatternMappingParser,
    FallbackMappingParser,
    ClarificationParser,
    CompositeMappingParser,
)

# Validation classes
from .validation import (
    BaseValidator,
    MappingValidator,
    ConfidenceValidator,
    DataQualityValidator,
    CompositeValidator,
)

# Mapping engine classes
from .mapping_engine import (
    FieldSimilarityCalculator,
    StandardFieldRegistry,
    IntelligentMappingEngine,
    FallbackMappingEngine,
)

# Transformation classes
from .transformation import DataTransformer, DatabaseUpdater, MappingTransformer

# Rules engine classes
from .rules_engine import (
    MappingRule,
    RequiredFieldsRule,
    UniqueTargetRule,
    MinimumConfidenceRule,
    DataConsistencyRule,
    MappingRulesEngine,
    DefaultClarificationGenerator,
)

# Formatter classes
from .formatters import (
    BaseFormatter,
    MappingResponseFormatter,
    ValidationResultsFormatter,
    LoggingFormatter,
    ClarificationFormatter,
)

# Export all public classes for backward compatibility and external use
__all__ = [
    # Core executor
    "FieldMappingExecutor",
    # Exceptions
    "FieldMappingExecutorError",
    "MappingParseError",
    "ValidationError",
    "CrewExecutionError",
    "TransformationError",
    "MappingEngineError",
    "RulesEngineError",
    "FormattingError",
    # Parsers
    "BaseMappingParser",
    "JSONMappingParser",
    "PatternMappingParser",
    "FallbackMappingParser",
    "ClarificationParser",
    "CompositeMappingParser",
    # Validators
    "BaseValidator",
    "MappingValidator",
    "ConfidenceValidator",
    "DataQualityValidator",
    "CompositeValidator",
    # Mapping engine
    "FieldSimilarityCalculator",
    "StandardFieldRegistry",
    "IntelligentMappingEngine",
    "FallbackMappingEngine",
    # Transformation
    "DataTransformer",
    "DatabaseUpdater",
    "MappingTransformer",
    # Rules engine
    "MappingRule",
    "RequiredFieldsRule",
    "UniqueTargetRule",
    "MinimumConfidenceRule",
    "DataConsistencyRule",
    "MappingRulesEngine",
    "DefaultClarificationGenerator",
    # Formatters
    "BaseFormatter",
    "MappingResponseFormatter",
    "ValidationResultsFormatter",
    "LoggingFormatter",
    "ClarificationFormatter",
]

# Version information
__version__ = "1.0.0"
__author__ = "Migration UI Orchestrator Team"
__description__ = "Modular field mapping executor for unified discovery flows"


# Factory functions for easy instantiation
def create_field_mapping_executor(
    storage_manager, agent_pool, client_account_id: str, engagement_id: str
) -> FieldMappingExecutor:
    """
    Factory function to create a FieldMappingExecutor instance.

    Args:
        storage_manager: Storage manager instance
        agent_pool: Tenant-scoped agent pool
        client_account_id: Client account identifier
        engagement_id: Engagement identifier

    Returns:
        Configured FieldMappingExecutor instance
    """
    return FieldMappingExecutor(
        storage_manager=storage_manager,
        agent_pool=agent_pool,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )


def create_composite_parser() -> CompositeMappingParser:
    """
    Factory function to create a CompositeMappingParser instance.

    Returns:
        Configured CompositeMappingParser with all parsing strategies
    """
    return CompositeMappingParser()


def create_composite_validator() -> CompositeValidator:
    """
    Factory function to create a CompositeValidator instance.

    Returns:
        Configured CompositeValidator with all validation strategies
    """
    return CompositeValidator()


def create_intelligent_mapping_engine() -> IntelligentMappingEngine:
    """
    Factory function to create an IntelligentMappingEngine instance.

    Returns:
        Configured IntelligentMappingEngine with similarity calculations
    """
    return IntelligentMappingEngine()


def create_mapping_transformer(
    storage_manager, client_account_id: str, engagement_id: str
) -> MappingTransformer:
    """
    Factory function to create a MappingTransformer instance.

    Args:
        storage_manager: Storage manager instance
        client_account_id: Client account identifier
        engagement_id: Engagement identifier

    Returns:
        Configured MappingTransformer instance
    """
    return MappingTransformer(
        storage_manager=storage_manager,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )


def create_rules_engine() -> MappingRulesEngine:
    """
    Factory function to create a MappingRulesEngine instance.

    Returns:
        Configured MappingRulesEngine with default rules
    """
    return MappingRulesEngine()


def create_response_formatter() -> MappingResponseFormatter:
    """
    Factory function to create a MappingResponseFormatter instance.

    Returns:
        Configured MappingResponseFormatter for standardized responses
    """
    return MappingResponseFormatter()


# Backward compatibility aliases
# These maintain compatibility with any existing code that might import
# these classes under different names
FieldMapper = FieldMappingExecutor
MappingExecutor = FieldMappingExecutor
CompositeParser = CompositeMappingParser
CompositeValidation = CompositeValidator
