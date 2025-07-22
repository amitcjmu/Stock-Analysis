"""
Gap Identifier Tool - Identifies gaps in critical attributes
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import ATTRIBUTE_CATEGORIES, DIFFICULTY_MAP, PRIORITY_MAP, SOURCE_MAP, STRATEGY_REQUIREMENTS

logger = logging.getLogger(__name__)


class GapIdentifierTool(AsyncBaseDiscoveryTool):
    """Identifies gaps in critical attributes"""
    
    name: str = "gap_identifier"
    description: str = "Identify missing critical attributes and their impact"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="gap_identifier",
            description="Identify missing critical attributes and their impact",
            tool_class=cls,
            categories=["gap_analysis", "gap_identification"],
            required_params=["attribute_mapping", "completeness_analysis"],
            optional_params=["business_context"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, 
                  attribute_mapping: Dict[str, str], 
                  completeness_analysis: Dict[str, Any],
                  business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Identify and categorize gaps in critical attributes"""
        try:
            self.log_with_context('info', "Identifying critical attribute gaps")
            
            gap_results = {
                "total_gaps": 0,
                "gaps_by_category": {
                    "infrastructure": [],
                    "application": [],
                    "operational": [],
                    "dependencies": []
                },
                "gaps_by_priority": {
                    "critical": [],
                    "high": [],
                    "medium": [],
                    "low": []
                },
                "business_impact_summary": {},
                "collection_difficulty": {}
            }
            
            # Identify gaps
            for category, attributes in ATTRIBUTE_CATEGORIES.items():
                for attribute in attributes:
                    if attribute not in attribute_mapping:
                        # This is a gap
                        gap_info = self._create_gap_info(
                            attribute, category, completeness_analysis, business_context
                        )
                        
                        gap_results["gaps_by_category"][category].append(gap_info)
                        gap_results["gaps_by_priority"][gap_info["priority"]].append(gap_info)
                        gap_results["total_gaps"] += 1
                    
                    elif attribute in completeness_analysis.get("attribute_completeness", {}):
                        # Check if mapped but has poor completeness
                        attr_completeness = completeness_analysis["attribute_completeness"][attribute]
                        if attr_completeness["completeness_percentage"] < 50:
                            gap_info = self._create_gap_info(
                                attribute, category, completeness_analysis, business_context,
                                partial=True, completeness=attr_completeness["completeness_percentage"]
                            )
                            
                            gap_results["gaps_by_category"][category].append(gap_info)
                            gap_results["gaps_by_priority"][gap_info["priority"]].append(gap_info)
                            gap_results["total_gaps"] += 1
            
            # Summarize business impact
            gap_results["business_impact_summary"] = self._summarize_business_impact(gap_results)
            
            # Assess collection difficulty
            gap_results["collection_difficulty"] = self._assess_collection_difficulty(gap_results)
            
            self.log_with_context(
                'info', 
                f"Identified {gap_results['total_gaps']} gaps "
                f"({len(gap_results['gaps_by_priority']['critical'])} critical)"
            )
            
            return gap_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in gap identification: {e}")
            return {"error": str(e)}
    
    def _create_gap_info(self, attribute: str, category: str, 
                        completeness_analysis: Dict[str, Any],
                        business_context: Optional[Dict[str, Any]] = None,
                        partial: bool = False,
                        completeness: float = 0.0) -> Dict[str, Any]:
        """Create detailed gap information"""
        gap_info = {
            "attribute": attribute,
            "category": category,
            "gap_type": "partial" if partial else "missing",
            "completeness": completeness if partial else 0.0,
            "priority": PRIORITY_MAP.get(attribute, "medium"),
            "collection_difficulty": DIFFICULTY_MAP.get(attribute, "medium"),
            "business_impact": self._determine_business_impact(attribute, category),
            "affects_strategies": self._determine_affected_strategies(attribute),
            "recommended_source": SOURCE_MAP.get(attribute, "manual_collection"),
            "automation_potential": DIFFICULTY_MAP.get(attribute) in ["easy", "medium"]
        }
        
        # Add context-specific information
        if business_context:
            if business_context.get("migration_timeline") == "urgent":
                if gap_info["priority"] == "medium":
                    gap_info["priority"] = "high"
            
            if business_context.get("compliance_required", False):
                if attribute in ["data_classification", "compliance_scope"]:
                    gap_info["priority"] = "critical"
        
        return gap_info
    
    def _determine_business_impact(self, attribute: str, category: str) -> str:
        """Determine business impact of missing attribute"""
        critical_impact = [
            "hostname", "application_name", "owner", "environment",
            "technology_stack", "application_dependencies"
        ]
        high_impact = [
            "os_type", "criticality_level", "data_classification",
            "database_dependencies", "integration_points"
        ]
        
        if attribute in critical_impact:
            return "critical"
        elif attribute in high_impact:
            return "high"
        elif category in ["infrastructure", "application"]:
            return "medium"
        else:
            return "low"
    
    def _determine_affected_strategies(self, attribute: str) -> List[str]:
        """Determine which 6R strategies are affected by this gap"""
        affected = []
        for strategy, required_attrs in STRATEGY_REQUIREMENTS.items():
            if attribute in required_attrs:
                affected.append(strategy)
        
        return affected if affected else ["general"]
    
    def _summarize_business_impact(self, gap_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize overall business impact of gaps"""
        critical_count = len(gap_results["gaps_by_priority"]["critical"])
        high_count = len(gap_results["gaps_by_priority"]["high"])
        
        if critical_count >= 3:
            overall_impact = "severe"
            risk_level = "high"
            recommendation = "Address critical gaps immediately before proceeding with migration planning"
        elif critical_count >= 1 or high_count >= 3:
            overall_impact = "significant"
            risk_level = "medium-high"
            recommendation = "Prioritize critical and high-priority gaps in the next sprint"
        elif high_count >= 1:
            overall_impact = "moderate"
            risk_level = "medium"
            recommendation = "Plan gap resolution activities alongside migration assessment"
        else:
            overall_impact = "minor"
            risk_level = "low"
            recommendation = "Address gaps as part of normal migration discovery process"
        
        return {
            "overall_impact": overall_impact,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "critical_gaps": critical_count,
            "high_priority_gaps": high_count,
            "decision_readiness": "blocked" if critical_count > 0 else "proceed_with_caution"
        }
    
    def _assess_collection_difficulty(self, gap_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall collection difficulty"""
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0, "very_hard": 0}
        total_effort_hours = 0
        
        # Count difficulties and estimate effort
        for priority_gaps in gap_results["gaps_by_priority"].values():
            for gap in priority_gaps:
                difficulty = gap["collection_difficulty"]
                difficulty_counts[difficulty] += 1
                
                # Estimate hours
                effort_map = {"easy": 2, "medium": 8, "hard": 24, "very_hard": 40}
                total_effort_hours += effort_map.get(difficulty, 8)
        
        return {
            "difficulty_distribution": difficulty_counts,
            "estimated_total_effort_hours": total_effort_hours,
            "automated_collection_possible": difficulty_counts["easy"] + difficulty_counts["medium"],
            "manual_collection_required": difficulty_counts["hard"] + difficulty_counts["very_hard"],
            "recommended_approach": "hybrid" if difficulty_counts["easy"] > 0 and difficulty_counts["hard"] > 0 else "manual"
        }