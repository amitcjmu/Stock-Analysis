"""
Priority Ranker Tool - Ranks gaps by business priority
"""

from typing import Dict, Any, List
from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
import logging

logger = logging.getLogger(__name__)


class PriorityRankerTool(AsyncBaseDiscoveryTool):
    """Ranks gaps by business priority"""
    
    name: str = "priority_ranker"
    description: str = "Rank and prioritize gaps based on business impact and collection feasibility"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="priority_ranker",
            description="Rank and prioritize gaps based on business impact and collection feasibility",
            tool_class=cls,
            categories=["gap_analysis", "prioritization"],
            required_params=["gaps", "ranking_criteria"],
            optional_params=[],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(self, gaps: List[Dict[str, Any]], ranking_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Rank gaps using multi-criteria decision analysis"""
        try:
            self.log_with_context('info', f"Ranking {len(gaps)} gaps")
            
            ranking_results = {
                "ranked_gaps": [],
                "ranking_methodology": "multi_criteria_weighted_scoring",
                "criteria_weights": {},
                "priority_groups": {
                    "immediate_action": [],
                    "next_sprint": [],
                    "backlog": [],
                    "nice_to_have": []
                }
            }
            
            # Define criteria weights
            weights = ranking_criteria.get("weights", {
                "business_impact": 0.35,
                "strategy_alignment": 0.25,
                "collection_feasibility": 0.20,
                "cost_benefit": 0.20
            })
            ranking_results["criteria_weights"] = weights
            
            # Score each gap
            scored_gaps = []
            for gap in gaps:
                scores = {
                    "business_impact": self._score_business_impact(gap),
                    "strategy_alignment": self._score_strategy_alignment(gap, ranking_criteria),
                    "collection_feasibility": self._score_feasibility(gap),
                    "cost_benefit": self._score_cost_benefit(gap)
                }
                
                # Calculate weighted score
                total_score = sum(scores[criteria] * weights[criteria] 
                                for criteria in scores)
                
                gap["priority_score"] = round(total_score, 2)
                gap["score_breakdown"] = scores
                scored_gaps.append(gap)
            
            # Sort by priority score
            scored_gaps.sort(key=lambda x: x["priority_score"], reverse=True)
            ranking_results["ranked_gaps"] = scored_gaps
            
            # Group into priority buckets
            for i, gap in enumerate(scored_gaps):
                if gap["priority_score"] >= 80 or gap.get("priority") == "critical":
                    ranking_results["priority_groups"]["immediate_action"].append(gap)
                elif gap["priority_score"] >= 60 or i < len(gaps) * 0.3:
                    ranking_results["priority_groups"]["next_sprint"].append(gap)
                elif gap["priority_score"] >= 40 or i < len(gaps) * 0.6:
                    ranking_results["priority_groups"]["backlog"].append(gap)
                else:
                    ranking_results["priority_groups"]["nice_to_have"].append(gap)
            
            self.log_with_context('info', "Gap ranking completed")
            return ranking_results
            
        except Exception as e:
            self.log_with_context('error', f"Error in priority ranking: {e}")
            return {"error": str(e)}
    
    def _score_business_impact(self, gap: Dict[str, Any]) -> float:
        """Score business impact (0-100)"""
        impact_level = gap.get("business_impact", "medium")
        priority = gap.get("priority", "medium")
        
        base_scores = {
            "critical": 100,
            "high": 80,
            "medium": 50,
            "low": 20
        }
        
        score = base_scores.get(impact_level, 50)
        
        # Adjust for priority
        if priority == "critical":
            score = min(100, score * 1.2)
        
        # Adjust for specific impacts
        if gap.get("blocks_decision", False):
            score = min(100, score + 20)
        if gap.get("impacts_timeline", False):
            score = min(100, score + 10)
        
        return score
    
    def _score_strategy_alignment(self, gap: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Score alignment with migration strategy (0-100)"""
        primary_strategy = criteria.get("primary_strategy", "rehost")
        affected_strategies = gap.get("affects_strategies", [])
        
        if primary_strategy in affected_strategies:
            return 100
        elif len(affected_strategies) > 3:
            return 80
        elif len(affected_strategies) > 1:
            return 60
        elif affected_strategies:
            return 40
        else:
            return 20
    
    def _score_feasibility(self, gap: Dict[str, Any]) -> float:
        """Score collection feasibility (0-100, higher is easier)"""
        difficulty = gap.get("collection_difficulty", "medium")
        
        feasibility_scores = {
            "easy": 100,
            "medium": 70,
            "hard": 40,
            "very_hard": 20
        }
        
        score = feasibility_scores.get(difficulty, 50)
        
        # Adjust for automation potential
        if gap.get("automation_potential", False):
            score = min(100, score * 1.2)
        
        return score
    
    def _score_cost_benefit(self, gap: Dict[str, Any]) -> float:
        """Score cost-benefit ratio (0-100)"""
        # Estimate based on impact vs effort
        impact = self._score_business_impact(gap)
        feasibility = self._score_feasibility(gap)
        
        # High impact + high feasibility = best cost-benefit
        # Low impact + low feasibility = worst cost-benefit
        cost_benefit = (impact * 0.6 + feasibility * 0.4)
        
        return cost_benefit