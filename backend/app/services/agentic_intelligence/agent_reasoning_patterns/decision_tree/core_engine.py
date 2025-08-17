"""
Core Reasoning Engine Module

This module contains the main AgentReasoningEngine that coordinates
all the specialized analyzers for business value, risk, and modernization.
"""

import logging
import uuid
from typing import Any, Dict

from ..logical_patterns import (
    BusinessValueReasoningPattern,
    RiskAssessmentReasoningPattern,
    ModernizationReasoningPattern,
)
from ..causal_patterns import (
    BusinessValueCausalPattern,
    RiskCausalPattern,
    ModernizationCausalPattern,
)
from ..temporal_patterns import AssetLifecyclePattern, PerformanceTrendPattern
from ..probabilistic import ProbabilisticBusinessValuePattern, ProbabilisticRiskPattern
from ..learning_patterns import PatternDiscoveryEngine, AdaptiveReasoningEngine
from ..base import AgentReasoning
from .business_value_analyzer import BusinessValueAnalyzer
from .risk_analyzer import RiskAnalyzer
from .modernization_analyzer import ModernizationAnalyzer

logger = logging.getLogger(__name__)


class AgentReasoningEngine:
    """
    Main engine that powers agent reasoning using discovered patterns and evidence.
    This replaces hard-coded rules with dynamic, learning-based intelligence.
    """

    def __init__(
        self, memory_manager, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.logger = logger

        # Initialize reasoning pattern components
        self.business_value_pattern = BusinessValueReasoningPattern()
        self.risk_pattern = RiskAssessmentReasoningPattern()
        self.modernization_pattern = ModernizationReasoningPattern()

        # Initialize causal reasoning patterns
        self.business_causal = BusinessValueCausalPattern()
        self.risk_causal = RiskCausalPattern()
        self.modernization_causal = ModernizationCausalPattern()

        # Initialize temporal reasoning patterns
        self.lifecycle_pattern = AssetLifecyclePattern()
        self.performance_pattern = PerformanceTrendPattern()

        # Initialize probabilistic reasoning patterns
        self.probabilistic_business = ProbabilisticBusinessValuePattern()
        self.probabilistic_risk = ProbabilisticRiskPattern()

        # Initialize learning-based patterns
        self.pattern_discovery = PatternDiscoveryEngine(
            memory_manager, client_account_id, engagement_id
        )
        self.adaptive_reasoning = AdaptiveReasoningEngine(
            memory_manager, client_account_id, engagement_id
        )

        # Initialize specialized analyzers
        self.business_value_analyzer = BusinessValueAnalyzer(
            memory_manager,
            client_account_id,
            engagement_id,
            self.business_value_pattern,
            self.business_causal,
            self.lifecycle_pattern,
            self.pattern_discovery,
        )

        self.risk_analyzer = RiskAnalyzer(
            memory_manager,
            client_account_id,
            engagement_id,
            self.risk_pattern,
            self.risk_causal,
            self.lifecycle_pattern,
            self.pattern_discovery,
        )

        self.modernization_analyzer = ModernizationAnalyzer(
            memory_manager,
            client_account_id,
            engagement_id,
            self.modernization_pattern,
            self.modernization_causal,
            self.lifecycle_pattern,
            self.pattern_discovery,
        )

    async def analyze_asset_business_value(
        self, asset_data: Dict[str, Any], agent_name: str
    ) -> AgentReasoning:
        """
        Analyze business value using agent reasoning instead of rules.
        Delegates to the specialized BusinessValueAnalyzer.
        """
        return await self.business_value_analyzer.analyze_asset_business_value(
            asset_data, agent_name
        )

    async def analyze_asset_risk_assessment(
        self, asset_data: Dict[str, Any], agent_name: str
    ) -> AgentReasoning:
        """
        Analyze risk factors using agent reasoning and pattern matching.
        Delegates to the specialized RiskAnalyzer.
        """
        return await self.risk_analyzer.analyze_asset_risk_assessment(
            asset_data, agent_name
        )

    async def analyze_modernization_potential(
        self, asset_data: Dict[str, Any], agent_name: str
    ) -> AgentReasoning:
        """
        Analyze modernization opportunities using agent reasoning.
        Delegates to the specialized ModernizationAnalyzer.
        """
        return await self.modernization_analyzer.analyze_modernization_potential(
            asset_data, agent_name
        )
