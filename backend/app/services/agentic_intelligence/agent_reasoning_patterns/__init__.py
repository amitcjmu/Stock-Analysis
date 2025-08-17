"""
Agent Reasoning Patterns - Core Intelligence Architecture

This module provides the complete agent reasoning patterns system that enables
CrewAI agents to analyze assets and discover business value, risk factors,
and modernization opportunities using dynamic, learning-based intelligence.

Exports all public classes and functions to maintain backward compatibility
with the original monolithic agent_reasoning_patterns.py file.
"""

# Core enums and data structures from base module
from .base import (
    ReasoningDimension,
    ConfidenceLevel,
    EvidenceType,
    ReasoningEvidence,
    AgentReasoning,
    BaseReasoningPattern,
    BaseEvidenceAnalyzer,
    BasePatternRepository,
)

# Reasoning-specific exceptions
from .exceptions import (
    ReasoningError,
    PatternMatchingError,
    EvidenceAnalysisError,
    ConfidenceCalculationError,
    ReasoningEngineError,
    PatternDiscoveryError,
    MemoryIntegrationError,
)

# Logical reasoning patterns and repositories
from .logical_patterns import (
    AssetReasoningPatterns,
    BusinessValueReasoningPattern,
    RiskAssessmentReasoningPattern,
    ModernizationReasoningPattern,
)

# Causal reasoning patterns
from .causal_patterns import (
    CausalRelationship,
    BusinessValueCausalPattern,
    RiskCausalPattern,
    ModernizationCausalPattern,
    CausalChainAnalyzer,
)

# Temporal reasoning patterns
from .temporal_patterns import (
    TemporalPoint,
    TemporalTrend,
    AssetLifecyclePattern,
    PerformanceTrendPattern,
    TechnicalDebtAccumulationPattern,
)

# Probabilistic reasoning patterns
from .probabilistic import (
    ProbabilityDistribution,
    BayesianInference,
    ProbabilisticBusinessValuePattern,
    ProbabilisticRiskPattern,
    UncertaintyQuantification,
)

# Learning and adaptation patterns
from .learning_patterns import (
    PatternDiscoveryEngine,
    AdaptiveReasoningEngine,
    ContinuousLearningManager,
)

# Main reasoning engine and decision trees
from .decision_trees import (
    AgentReasoningEngine,
)

# Maintain backward compatibility by exposing the original module structure
# This ensures that existing imports continue to work without changes

__all__ = [
    # Core enums and data structures
    "ReasoningDimension",
    "ConfidenceLevel",
    "EvidenceType",
    "ReasoningEvidence",
    "AgentReasoning",
    # Base classes
    "BaseReasoningPattern",
    "BaseEvidenceAnalyzer",
    "BasePatternRepository",
    # Exceptions
    "ReasoningError",
    "PatternMatchingError",
    "EvidenceAnalysisError",
    "ConfidenceCalculationError",
    "ReasoningEngineError",
    "PatternDiscoveryError",
    "MemoryIntegrationError",
    # Logical reasoning patterns
    "AssetReasoningPatterns",
    "BusinessValueReasoningPattern",
    "RiskAssessmentReasoningPattern",
    "ModernizationReasoningPattern",
    # Causal reasoning patterns
    "CausalRelationship",
    "BusinessValueCausalPattern",
    "RiskCausalPattern",
    "ModernizationCausalPattern",
    "CausalChainAnalyzer",
    # Temporal reasoning patterns
    "TemporalPoint",
    "TemporalTrend",
    "AssetLifecyclePattern",
    "PerformanceTrendPattern",
    "TechnicalDebtAccumulationPattern",
    # Probabilistic reasoning patterns
    "ProbabilityDistribution",
    "BayesianInference",
    "ProbabilisticBusinessValuePattern",
    "ProbabilisticRiskPattern",
    "UncertaintyQuantification",
    # Learning and adaptation patterns
    "PatternDiscoveryEngine",
    "AdaptiveReasoningEngine",
    "ContinuousLearningManager",
    # Main reasoning engine
    "AgentReasoningEngine",
]

# Version information
__version__ = "1.0.0"
__author__ = "CC (Claude Code)"
__description__ = (
    "Modularized Agent Reasoning Patterns for Agentic Intelligence Architecture"
)
