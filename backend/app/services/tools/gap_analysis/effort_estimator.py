"""
Effort Estimator Tool - Estimates effort required for gap resolution
"""

import logging
from typing import Any, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import EFFORT_MATRIX

logger = logging.getLogger(__name__)


class EffortEstimatorTool(AsyncBaseDiscoveryTool):
    """Estimates effort required for gap resolution"""
    
    name: str = "effort_estimator"
    description: str = "Estimate time and resources needed to collect missing attributes"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="effort_estimator",
            description="Estimate time and resources needed to collect missing attributes",
            tool_class=cls,
            categories=["gap_analysis", "planning"],
            required_params=["gaps", "resources"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, gaps: List[Dict[str, Any]], resources: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate effort for collecting missing attributes"""
        try:
            self.log_with_context('info', f"Estimating effort for {len(gaps)} gaps")
            
            estimation_results = {
                "total_effort_hours": 0,
                "effort_by_priority": {},
                "effort_by_method": {},
                "resource_allocation": {},
                "timeline_estimate": {},
                "optimization_opportunities": []
            }
            
            # Process each gap
            for gap in gaps:
                difficulty = gap.get("collection_difficulty", "medium")
                priority = gap.get("priority", "medium")
                
                # Calculate effort
                effort = EFFORT_MATRIX.get(difficulty, EFFORT_MATRIX["medium"])
                total_gap_effort = sum(effort.values())
                
                # Adjust for priority
                if priority == "critical":
                    total_gap_effort *= 1.2  # Add overhead for critical items
                
                # Track by priority
                if priority not in estimation_results["effort_by_priority"]:
                    estimation_results["effort_by_priority"][priority] = 0
                estimation_results["effort_by_priority"][priority] += total_gap_effort
                
                # Track by collection method
                method = gap.get("recommended_source", "manual_collection")
                if method not in estimation_results["effort_by_method"]:
                    estimation_results["effort_by_method"][method] = 0
                estimation_results["effort_by_method"][method] += total_gap_effort
                
                estimation_results["total_effort_hours"] += total_gap_effort
            
            # Calculate resource allocation
            estimation_results["resource_allocation"] = self._calculate_resource_allocation(
                gaps, resources, estimation_results["total_effort_hours"]
            )
            
            # Estimate timeline
            estimation_results["timeline_estimate"] = self._estimate_timeline(
                estimation_results["total_effort_hours"],
                resources
            )
            
            # Identify optimization opportunities
            estimation_results["optimization_opportunities"] = self._identify_optimizations(gaps)
            
            self.log_with_context(
                'info', 
                f"Total effort estimated: {estimation_results['total_effort_hours']:.1f} hours"
            )
            
            return estimation_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in effort estimation: {e}")
            return {"error": str(e)}
    
    def _calculate_resource_allocation(self, gaps: List[Dict[str, Any]], 
                                     resources: Dict[str, Any], 
                                     total_hours: float) -> Dict[str, Any]:
        """Calculate optimal resource allocation"""
        available_resources = resources.get("available_team_members", 2)
        resources.get("hours_per_week", 40)
        
        # Categorize work by skill requirement
        skill_requirements = {
            "technical": 0,
            "business": 0,
            "data_analyst": 0,
            "stakeholder_coordination": 0
        }
        
        for gap in gaps:
            category = gap.get("category", "unknown")
            if category == "infrastructure":
                skill_requirements["technical"] += 1
            elif category == "application":
                skill_requirements["technical"] += 0.5
                skill_requirements["business"] += 0.5
            elif category == "operational":
                skill_requirements["business"] += 0.7
                skill_requirements["stakeholder_coordination"] += 0.3
            else:  # dependencies
                skill_requirements["data_analyst"] += 0.6
                skill_requirements["technical"] += 0.4
        
        # Normalize to percentages
        total_work = sum(skill_requirements.values())
        if total_work > 0:
            for skill in skill_requirements:
                skill_requirements[skill] = (skill_requirements[skill] / total_work) * 100
        
        return {
            "recommended_team_composition": skill_requirements,
            "minimum_team_size": max(2, len([s for s in skill_requirements.values() if s > 20])),
            "optimal_team_size": min(available_resources, 4),
            "parallel_work_possible": total_hours > 80,
            "skill_gaps": [skill for skill, pct in skill_requirements.items() if pct > 30]
        }
    
    def _estimate_timeline(self, total_hours: float, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate project timeline"""
        team_size = resources.get("available_team_members", 2)
        hours_per_week = resources.get("hours_per_week", 40)
        efficiency_factor = resources.get("efficiency_factor", 0.7)  # Account for meetings, overhead
        
        effective_hours_per_week = team_size * hours_per_week * efficiency_factor
        weeks_required = total_hours / effective_hours_per_week
        
        # Add buffer for dependencies and unknowns
        buffer_factor = 1.2 if total_hours > 200 else 1.1
        weeks_with_buffer = weeks_required * buffer_factor
        
        return {
            "estimated_weeks": round(weeks_required, 1),
            "weeks_with_buffer": round(weeks_with_buffer, 1),
            "estimated_completion_date": f"In {round(weeks_with_buffer, 1)} weeks",
            "confidence_level": "medium" if total_hours < 200 else "low",
            "critical_path_items": "Focus on critical priority gaps first",
            "parallelization_savings": f"{round((1 - 1/team_size) * 100)}% with {team_size} team members"
        }
    
    def _identify_optimizations(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        optimizations = []
        
        # Group by collection method
        method_groups = {}
        for gap in gaps:
            method = gap.get("recommended_source", "manual")
            if method not in method_groups:
                method_groups[method] = []
            method_groups[method].append(gap)
        
        # Batch collection opportunities
        for method, method_gaps in method_groups.items():
            if len(method_gaps) > 3:
                optimizations.append({
                    "type": "batch_collection",
                    "method": method,
                    "gap_count": len(method_gaps),
                    "potential_savings": f"{len(method_gaps) * 10}% time reduction",
                    "implementation": f"Collect all {method} data in single effort"
                })
        
        # Automation opportunities
        easy_gaps = [g for g in gaps if g.get("collection_difficulty") == "easy"]
        if easy_gaps:
            optimizations.append({
                "type": "automation",
                "gap_count": len(easy_gaps),
                "potential_savings": f"{len(easy_gaps) * 2} hours",
                "implementation": "Deploy discovery tools for infrastructure attributes"
            })
        
        # Template opportunities
        similar_gaps = [g for g in gaps if g.get("category") == "operational"]
        if len(similar_gaps) > 5:
            optimizations.append({
                "type": "standardization",
                "gap_count": len(similar_gaps),
                "potential_savings": "30% reduction in collection time",
                "implementation": "Create standardized collection templates"
            })
        
        return optimizations