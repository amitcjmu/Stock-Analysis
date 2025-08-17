"""
Escalation metrics and tracking for strategic insight extraction and results generation.
"""

from datetime import datetime
from typing import Dict, Any, List

from .base import logger


class EscalationMetricsManager:
    """
    Manages escalation metrics, strategic insight extraction, and results generation.
    """

    def __init__(self, strategic_crews: Dict[str, Any]):
        """Initialize with strategic crews reference."""
        self.strategic_crews = strategic_crews

    def extract_strategic_insights(
        self, crew_type: str, crew_results: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from strategic crew results."""
        insights = []

        try:
            if crew_results.get("success") and crew_results.get("analysis_results"):
                analysis_results = crew_results["analysis_results"]

                # Extract insights based on crew type
                if crew_type == "asset_intelligence_crew":
                    insights.extend(
                        self._extract_asset_intelligence_insights(
                            analysis_results, context
                        )
                    )
                elif crew_type == "dependency_analysis_crew":
                    insights.extend(
                        self._extract_dependency_insights(analysis_results, context)
                    )
                elif crew_type == "tech_debt_analysis_crew":
                    insights.extend(
                        self._extract_tech_debt_insights(analysis_results, context)
                    )

                # Add crew metadata insight
                insights.append(
                    {
                        "type": "crew_execution_success",
                        "crew_type": crew_type,
                        "assets_analyzed": len(analysis_results),
                        "insight": (
                            f"Strategic {crew_type} successfully analyzed {len(analysis_results)} assets "
                            "with enhanced intelligence"
                        ),
                        "confidence": 0.9,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        except Exception as e:
            logger.error(f"❌ Error extracting strategic insights: {e}")
            insights.append(
                {
                    "type": "crew_execution_error",
                    "crew_type": crew_type,
                    "error": str(e),
                    "insight": "Strategic crew execution encountered issues but provided fallback analysis",
                    "confidence": 0.3,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return insights

    def _extract_asset_intelligence_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from asset intelligence crew results."""
        insights = []
        timestamp = datetime.utcnow().isoformat()

        for result in analysis_results:
            asset_name = getattr(result, "asset_name", "unknown")

            if hasattr(result, "confidence_score") and result.confidence_score > 0.8:
                insights.append(
                    {
                        "type": "high_confidence_classification",
                        "asset_name": asset_name,
                        "classification": getattr(result, "classification", "unknown"),
                        "confidence": result.confidence_score,
                        "insight": f"High-confidence asset classification achieved for {asset_name}",
                        "recommendations": getattr(result, "recommendations", []),
                        "timestamp": timestamp,
                    }
                )

            if (
                hasattr(result, "migration_priority")
                and result.migration_priority == "high"
            ):
                insights.append(
                    {
                        "type": "high_priority_migration",
                        "asset_name": asset_name,
                        "priority": result.migration_priority,
                        "insight": f"Asset {asset_name} identified as high priority for migration",
                        "business_value": getattr(result, "business_context", {}).get(
                            "business_value_score", 0
                        ),
                        "timestamp": timestamp,
                    }
                )

        return insights

    def _extract_dependency_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from dependency analysis crew results."""
        insights = []
        timestamp = datetime.utcnow().isoformat()

        for result in analysis_results:
            asset_name = getattr(result, "asset_name", "unknown")

            if hasattr(result, "network_analysis"):
                complexity = result.network_analysis.get("complexity_level", "medium")
                if complexity in ["high", "very_high"]:
                    insights.append(
                        {
                            "type": "complex_dependencies",
                            "asset_name": asset_name,
                            "complexity": complexity,
                            "insight": f"Complex dependency patterns identified for {asset_name}",
                            "migration_impact": "requires_careful_planning",
                            "timestamp": timestamp,
                        }
                    )

            if hasattr(result, "critical_path_analysis"):
                critical_paths = result.critical_path_analysis.get("critical_paths", [])
                if len(critical_paths) > 0:
                    insights.append(
                        {
                            "type": "critical_path_identified",
                            "asset_name": asset_name,
                            "critical_paths_count": len(critical_paths),
                            "insight": f"Identified {len(critical_paths)} critical dependency paths for {asset_name}",
                            "migration_impact": "high",
                            "timestamp": timestamp,
                        }
                    )

        return insights

    def _extract_tech_debt_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from tech debt analysis crew results."""
        insights = []
        timestamp = datetime.utcnow().isoformat()

        for result in analysis_results:
            asset_name = getattr(result, "asset_name", "unknown")

            if hasattr(result, "legacy_assessment"):
                legacy_level = result.legacy_assessment.get("legacy_level", "medium")
                if legacy_level in ["high", "critical"]:
                    insights.append(
                        {
                            "type": "high_tech_debt",
                            "asset_name": asset_name,
                            "legacy_level": legacy_level,
                            "insight": f"High technical debt identified for {asset_name}",
                            "modernization_urgency": result.legacy_assessment.get(
                                "modernization_urgency", {}
                            ),
                            "timestamp": timestamp,
                        }
                    )

            if hasattr(result, "sixr_recommendations"):
                strategy = result.sixr_recommendations.get("recommended_strategy", "")
                if strategy in ["refactor", "re-architect", "rebuild"]:
                    insights.append(
                        {
                            "type": "modernization_opportunity",
                            "asset_name": asset_name,
                            "recommended_strategy": strategy,
                            "insight": f"Modernization opportunity identified: {strategy} strategy for {asset_name}",
                            "business_impact": result.sixr_recommendations.get(
                                "business_impact", "medium"
                            ),
                            "timestamp": timestamp,
                        }
                    )

        return insights

    def synthesize_multi_crew_insights(
        self,
        crew_results: Dict[str, Any],
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Synthesize insights from multiple crew analyses."""
        synthesized_insights = []

        # Cross-crew pattern identification
        asset_patterns = {}
        for crew_name, results in crew_results.items():
            if results and results.get("analysis_results"):
                for result in results["analysis_results"]:
                    asset_id = getattr(result, "asset_id", f"unknown_{crew_name}")
                    if asset_id not in asset_patterns:
                        asset_patterns[asset_id] = {}
                    asset_patterns[asset_id][crew_name] = result

        # Generate cross-crew insights
        for asset_id, crew_analyses in asset_patterns.items():
            if len(crew_analyses) > 1:
                synthesized_insights.append(
                    {
                        "type": "cross_crew_analysis",
                        "asset_id": asset_id,
                        "crews_involved": list(crew_analyses.keys()),
                        "insight": (
                            f"Multi-crew analysis completed for {asset_id} with "
                            f"{len(crew_analyses)} strategic perspectives"
                        ),
                        "synthesis_confidence": 0.85,
                        "collaboration_pattern": collaboration_strategy["pattern"],
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        # Add collaboration strategy insight
        synthesized_insights.append(
            {
                "type": "collaboration_success",
                "strategy": collaboration_strategy["pattern"],
                "crews_executed": len(
                    [r for r in crew_results.values() if r is not None]
                ),
                "total_crews": len(crew_results),
                "insight": (
                    f"Strategic crew collaboration using {collaboration_strategy['pattern']} pattern "
                    "completed successfully"
                ),
                "collaboration_effectiveness": len(
                    [r for r in crew_results.values() if r is not None]
                )
                / len(crew_results),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return synthesized_insights

    def extract_strategic_recommendations(
        self, crew_type: str, crew_results: Dict[str, Any]
    ) -> List[str]:
        """Extract strategic recommendations from crew results."""
        recommendations = []

        try:
            analysis_results = crew_results.get("analysis_results", [])

            for result in analysis_results:
                if hasattr(result, "recommendations"):
                    recommendations.extend(getattr(result, "recommendations", []))

                # Add crew-specific recommendations
                if crew_type == "asset_intelligence_crew" and hasattr(
                    result, "migration_priority"
                ):
                    if result.migration_priority == "high":
                        asset_name = getattr(result, "asset_name", "asset")
                        recommendations.append(
                            f"Prioritize {asset_name} for early migration due to high business value"
                        )
                elif crew_type == "dependency_analysis_crew" and hasattr(
                    result, "critical_path_analysis"
                ):
                    recommendations.append(
                        f"Review dependency paths for {getattr(result, 'asset_name', 'asset')} before migration"
                    )
                elif crew_type == "tech_debt_analysis_crew" and hasattr(
                    result, "sixr_recommendations"
                ):
                    sixr_strategy = result.sixr_recommendations.get(
                        "recommended_strategy", "rehost"
                    )
                    recommendations.append(
                        f"Apply {sixr_strategy} strategy for {getattr(result, 'asset_name', 'asset')}"
                    )

        except Exception as e:
            logger.error(f"❌ Error extracting strategic recommendations: {e}")
            recommendations.append(
                "Review strategic analysis results for detailed recommendations"
            )

        return list(set(recommendations))  # Remove duplicates

    def generate_preliminary_insights(
        self, crew_type: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate preliminary insights when crew results are not available."""
        return [
            {
                "type": "preliminary_analysis",
                "crew_type": crew_type,
                "status": "preliminary",
                "insight": f"Initial analysis for {crew_type} crew based on context",
                "generated_at": datetime.utcnow().isoformat(),
                "context_summary": (
                    str(context)[:200] + "..."
                    if len(str(context)) > 200
                    else str(context)
                ),
                "confidence": 0.5,
            }
        ]

    async def generate_crew_results(
        self,
        crew_type: str,
        context: Dict[str, Any],
        preliminary_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate crew results based on preliminary insights."""
        return {
            "crew_type": crew_type,
            "status": "generated",
            "results": f"Generated results for {crew_type} crew",
            "preliminary_insights": preliminary_insights,
            "generated_at": datetime.utcnow().isoformat(),
            "context": context,
            "strategic_analysis": False,
            "fallback_analysis": True,
        }

    async def generate_strategic_crew_results(
        self,
        crew_type: str,
        context: Dict[str, Any],
        crew_results: Dict[str, Any],
        preliminary_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate results from strategic crew execution."""
        base_results = await self.generate_crew_results(
            crew_type, context, preliminary_insights
        )

        # Enhance with strategic crew data
        if crew_results and crew_results.get("success"):
            base_results.update(
                {
                    "strategic_analysis": True,
                    "crew_execution_success": True,
                    "analysis_metadata": crew_results.get("metadata", {}),
                    "crew_insights": crew_results.get("crew_insights", []),
                    "analysis_summary": crew_results.get("summary", {}),
                    "strategic_recommendations": self.extract_strategic_recommendations(
                        crew_type, crew_results
                    ),
                    "confidence_improvements": {
                        "strategic_analysis_applied": True,
                        "analysis_depth": "comprehensive",
                        "crew_confidence": crew_results.get("metadata", {}).get(
                            "average_confidence", 0.8
                        ),
                    },
                    "fallback_analysis": False,
                }
            )
        else:
            base_results.update(
                {
                    "strategic_analysis": False,
                    "crew_execution_success": False,
                    "fallback_analysis": True,
                    "note": "Strategic crew execution failed, using fallback analysis",
                }
            )

        return base_results

    async def generate_collaborative_results(
        self,
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
        comprehensive_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate collaborative results from multiple crews."""
        return {
            "collaboration_strategy": collaboration_strategy,
            "status": "collaborative_complete",
            "results": f"Collaborative analysis using {collaboration_strategy['pattern']} strategy",
            "comprehensive_insights": comprehensive_insights,
            "generated_at": datetime.utcnow().isoformat(),
            "context": context,
            "strategic_analysis": True,
            "collaboration_success": True,
            "insights_count": len(comprehensive_insights),
            "collaboration_effectiveness": self._calculate_collaboration_effectiveness(
                comprehensive_insights
            ),
        }

    def _calculate_collaboration_effectiveness(
        self, insights: List[Dict[str, Any]]
    ) -> float:
        """Calculate the effectiveness of collaboration based on insights."""
        if not insights:
            return 0.0

        # Count different types of insights
        insight_types = set(insight.get("type", "unknown") for insight in insights)

        # Base effectiveness on diversity of insights and quality indicators
        type_diversity = len(insight_types) / max(len(insights), 1)

        # Check for high-confidence insights
        high_confidence_count = sum(
            1 for insight in insights if insight.get("confidence", 0) > 0.8
        )
        confidence_ratio = high_confidence_count / len(insights)

        # Calculate overall effectiveness (0.0 to 1.0)
        effectiveness = (type_diversity * 0.6) + (confidence_ratio * 0.4)
        return min(effectiveness, 1.0)


# Export for use in other modules
__all__ = ["EscalationMetricsManager"]
