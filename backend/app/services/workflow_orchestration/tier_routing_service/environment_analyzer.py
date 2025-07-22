"""
Environment Analysis Module
Team C1 - Task C1.3

Environment complexity analysis and platform coverage assessment.
"""

import logging
from typing import Any, Dict

from app.core.logging import get_logger

from .enums import EnvironmentComplexity

logger = get_logger(__name__)


class EnvironmentAnalyzer:
    """Handles environment complexity and platform analysis"""
    
    def __init__(self):
        """Initialize the Environment Analyzer"""
        self.platform_compatibility = {
            "aws": {"tier_1": 0.95, "tier_2": 0.98, "tier_3": 0.99, "tier_4": 1.0},
            "azure": {"tier_1": 0.90, "tier_2": 0.95, "tier_3": 0.98, "tier_4": 1.0},
            "gcp": {"tier_1": 0.85, "tier_2": 0.92, "tier_3": 0.97, "tier_4": 1.0},
            "vmware": {"tier_1": 0.70, "tier_2": 0.85, "tier_3": 0.95, "tier_4": 1.0},
            "kubernetes": {"tier_1": 0.80, "tier_2": 0.90, "tier_3": 0.95, "tier_4": 1.0},
            "on_premise": {"tier_1": 0.60, "tier_2": 0.80, "tier_3": 0.95, "tier_4": 1.0}
        }
    
    async def analyze_environment_complexity(
        self,
        environment_config: Dict[str, Any],
        base_analysis: Dict[str, Any]
    ) -> EnvironmentComplexity:
        """Analyze environment complexity level"""
        try:
            complexity_score = 0
            
            # Platform diversity
            platforms = environment_config.get("platforms", [])
            platform_count = len(platforms)
            if platform_count > 5:
                complexity_score += 3
            elif platform_count > 2:
                complexity_score += 2
            elif platform_count > 1:
                complexity_score += 1
            
            # Integration complexity
            integrations = environment_config.get("integrations", [])
            if len(integrations) > 10:
                complexity_score += 3
            elif len(integrations) > 5:
                complexity_score += 2
            elif len(integrations) > 0:
                complexity_score += 1
            
            # Custom configurations
            custom_configs = environment_config.get("custom_configurations", {})
            if len(custom_configs) > 20:
                complexity_score += 3
            elif len(custom_configs) > 10:
                complexity_score += 2
            elif len(custom_configs) > 0:
                complexity_score += 1
            
            # Data volume
            estimated_resources = environment_config.get("estimated_resource_count", 0)
            if estimated_resources > 10000:
                complexity_score += 3
            elif estimated_resources > 1000:
                complexity_score += 2
            elif estimated_resources > 100:
                complexity_score += 1
            
            # Determine complexity level
            if complexity_score >= 9:
                return EnvironmentComplexity.ENTERPRISE
            elif complexity_score >= 6:
                return EnvironmentComplexity.COMPLEX
            elif complexity_score >= 3:
                return EnvironmentComplexity.MODERATE
            else:
                return EnvironmentComplexity.SIMPLE
                
        except Exception as e:
            logger.warning(f"Environment complexity analysis failed: {e}")
            return EnvironmentComplexity.MODERATE
    
    async def analyze_platform_coverage(
        self,
        environment_config: Dict[str, Any],
        complexity: EnvironmentComplexity
    ) -> Dict[str, float]:
        """Analyze platform coverage and adapter compatibility"""
        coverage = {}
        
        platforms = environment_config.get("platforms", [])
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            
            # Get adapter compatibility
            if platform_type in self.platform_compatibility:
                coverage[platform_type] = self.platform_compatibility[platform_type]
            else:
                # Unknown platform - conservative coverage
                coverage[platform_type] = {
                    "tier_1": 0.5, "tier_2": 0.7, "tier_3": 0.9, "tier_4": 1.0
                }
        
        return coverage