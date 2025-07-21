"""
Collection Strategy Planner

Plans optimal collection strategies based on automation tier and requirements.
"""

import logging
from typing import Dict, Any, List, Optional

from app.services.tools.base_tool import BaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from .base import BaseCollectionTool

logger = logging.getLogger(__name__)


class CollectionStrategyPlanner(BaseDiscoveryTool, BaseCollectionTool):
    """Plans optimal collection workflows based on automation tier"""
    
    name: str = "CollectionStrategyPlanner"
    description: str = "Design optimal collection workflows based on automation tier"
    
    def __init__(self):
        super().__init__()
        self.name = "CollectionStrategyPlanner"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="CollectionStrategyPlanner",
            description="Plans collection strategies based on tier and requirements",
            tool_class=cls,
            categories=["collection", "planning", "strategy"],
            required_params=["automation_tier", "platforms"],
            optional_params=["requirements", "constraints", "priorities"],
            context_aware=True,
            async_tool=False
        )
    
    def run(
        self,
        automation_tier: str,
        platforms: List[Dict[str, Any]],
        requirements: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        priorities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Plan collection strategy based on tier and requirements.
        
        Args:
            automation_tier: Selected automation tier (tier_1 to tier_3)
            platforms: List of detected platforms
            requirements: Collection requirements (sixR, quality thresholds)
            constraints: Constraints (time limits, resource limits)
            priorities: Priority order for collection
            
        Returns:
            Collection strategy plan
        """
        strategy = self._create_base_strategy(automation_tier)
        
        try:
            if automation_tier == "tier_1":
                self._plan_tier1_strategy(strategy, platforms, constraints)
            elif automation_tier == "tier_2":
                self._plan_tier2_strategy(strategy, platforms, priorities, constraints)
            elif automation_tier == "tier_3":
                self._plan_tier3_strategy(strategy, platforms)
            else:
                strategy["errors"].append(f"Unknown automation tier: {automation_tier}")
                return strategy
            
            # Add resource allocation and quality requirements
            self._add_resource_allocation(strategy, automation_tier, len(platforms), constraints)
            self._add_quality_requirements(strategy, requirements)
            
            strategy["success"] = len(strategy.get("errors", [])) == 0
            return strategy
            
        except Exception as e:
            strategy["errors"].append(str(e))
            strategy["success"] = False
            return strategy
    
    def _create_base_strategy(self, automation_tier: str) -> Dict[str, Any]:
        """Create base strategy structure"""
        return self._create_base_result("plan_strategy") | {
            "automation_tier": automation_tier,
            "phases": [],
            "parallelization": {},
            "checkpoints": [],
            "resource_allocation": {}
        }
    
    def _plan_tier1_strategy(self, strategy: Dict[str, Any], platforms: List[Dict[str, Any]], constraints: Optional[Dict[str, Any]]):
        """Full automation - parallel execution"""
        strategy["execution_mode"] = "parallel"
        strategy["phases"] = [
            {
                "name": "parallel_collection",
                "description": "Execute all platform collections in parallel",
                "platforms": [p["name"] for p in platforms],
                "timeout": 3600,
                "retry_policy": {"max_retries": 3, "backoff": "exponential"}
            }
        ]
        strategy["parallelization"] = {
            "max_concurrent": len(platforms),
            "batch_size": 10,
            "throttling": False
        }
    
    def _plan_tier2_strategy(self, strategy: Dict[str, Any], platforms: List[Dict[str, Any]], priorities: Optional[List[str]], constraints: Optional[Dict[str, Any]]):
        """Semi-automated with checkpoints"""
        strategy["execution_mode"] = "sequential_batched"
        
        # Group platforms by criticality
        critical_platforms = []
        standard_platforms = []
        
        for platform in platforms:
            if priorities and platform["name"] in priorities[:3]:
                critical_platforms.append(platform)
            else:
                standard_platforms.append(platform)
        
        strategy["phases"] = [
            {
                "name": "critical_collection",
                "description": "Collect from critical platforms first",
                "platforms": [p["name"] for p in critical_platforms],
                "timeout": 1800,
                "validation_checkpoint": True
            },
            {
                "name": "standard_collection", 
                "description": "Collect from remaining platforms",
                "platforms": [p["name"] for p in standard_platforms],
                "timeout": 2400,
                "validation_checkpoint": True
            }
        ]
        
        strategy["checkpoints"] = [
            {
                "after_phase": "critical_collection",
                "validation": ["quality_check", "completeness_check"],
                "approval_required": False
            },
            {
                "after_phase": "standard_collection",
                "validation": ["full_validation"],
                "approval_required": True
            }
        ]
    
    def _plan_tier3_strategy(self, strategy: Dict[str, Any], platforms: List[Dict[str, Any]]):
        """Guided collection with manual oversight"""
        strategy["execution_mode"] = "guided_sequential"
        
        strategy["phases"] = []
        for i, platform in enumerate(platforms):
            strategy["phases"].append({
                "name": f"collect_{platform['name']}",
                "description": f"Guided collection for {platform['name']}",
                "platforms": [platform["name"]],
                "timeout": 1200,
                "manual_review": True,
                "approval_required": True
            })
        
        strategy["checkpoints"] = [
            {
                "after_each_platform": True,
                "validation": ["manual_review", "quality_assessment"],
                "approval_required": True,
                "notification": True
            }
        ]
    
    def _add_resource_allocation(self, strategy: Dict[str, Any], tier: str, platform_count: int, constraints: Optional[Dict[str, Any]]):
        """Add resource allocation configuration"""
        strategy["resource_allocation"] = {
            "cpu_limit": constraints.get("cpu_limit", 80) if constraints else 80,
            "memory_limit": constraints.get("memory_limit", 70) if constraints else 70,
            "concurrent_connections": self._calculate_connections(tier, platform_count),
            "rate_limiting": self._calculate_rate_limits(tier)
        }
    
    def _add_quality_requirements(self, strategy: Dict[str, Any], requirements: Optional[Dict[str, Any]]):
        """Add quality requirements if specified"""
        if requirements:
            strategy["quality_requirements"] = {
                "minimum_quality_score": requirements.get("quality_threshold", 0.8),
                "completeness_threshold": requirements.get("completeness", 0.9),
                "validation_rules": requirements.get("validation_rules", [])
            }
    
    def _calculate_connections(self, tier: str, platform_count: int) -> int:
        """Calculate concurrent connections based on tier"""
        tier_limits = {
            "tier_1": min(platform_count * 5, 50),
            "tier_2": min(platform_count * 3, 30),
            "tier_3": min(platform_count * 2, 20)
        }
        return tier_limits.get(tier, 30)
    
    def _calculate_rate_limits(self, tier: str) -> Dict[str, Any]:
        """Calculate rate limits based on tier"""
        return {
            "tier_1": {"requests_per_second": 100, "burst": 200},
            "tier_2": {"requests_per_second": 50, "burst": 100},
            "tier_3": {"requests_per_second": 20, "burst": 40}
        }.get(tier, {"requests_per_second": 50, "burst": 100})