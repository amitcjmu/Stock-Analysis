"""
Tech Debt Analysis Tools - Tool Implementations

This module contains all BaseTool subclasses for tech debt analysis:
- LegacySystemAnalysisTool: Analyzes legacy systems and identifies modernization opportunities
- SixRStrategyTool: Analyzes assets and recommends optimal 6R migration strategy

These tools are used by the Tech Debt Analysis Crew agents to perform
comprehensive technical debt assessment and modernization planning.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class LegacySystemAnalysisTool(BaseTool):
    """Tool for legacy system analysis and modernization assessment"""

    name: str = "legacy_system_analysis_tool"
    description: str = "Analyze legacy systems and identify modernization opportunities"

    def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """Analyze legacy system characteristics"""
        try:
            # Legacy indicators
            legacy_indicators = {
                "technology_age": {
                    "very_old": ["cobol", "fortran", "mainframe", "as400", "vb6"],
                    "old": ["java 6", "java 7", ".net 2.0", ".net 3.5", "php 5"],
                    "aging": ["java 8", ".net 4.0", "php 7", "python 2.7"],
                    "current": [
                        "java 11",
                        "java 17",
                        ".net 5",
                        ".net 6",
                        "python 3.8+",
                    ],
                },
                "architecture_patterns": {
                    "monolithic": ["monolith", "single deployment", "tightly coupled"],
                    "soa": ["soa", "service oriented", "web services", "soap"],
                    "microservices": [
                        "microservices",
                        "containerized",
                        "kubernetes",
                        "docker",
                    ],
                    "serverless": ["serverless", "lambda", "functions", "faas"],
                },
                "maintenance_indicators": {
                    "high_maintenance": [
                        "manual deployment",
                        "no automation",
                        "legacy code",
                    ],
                    "medium_maintenance": ["some automation", "mixed technologies"],
                    "low_maintenance": ["automated", "modern practices", "ci/cd"],
                },
            }

            asset_text = " ".join(
                str(value).lower() for value in asset_data.values() if value
            )

            # Assess technology age
            tech_age_score = 0
            tech_age_level = "unknown"
            for age_level, technologies in legacy_indicators["technology_age"].items():
                matches = [tech for tech in technologies if tech in asset_text]
                if matches:
                    if age_level == "very_old":
                        tech_age_score = 4
                        tech_age_level = "very_old"
                    elif age_level == "old":
                        tech_age_score = 3
                        tech_age_level = "old"
                    elif age_level == "aging":
                        tech_age_score = 2
                        tech_age_level = "aging"
                    elif age_level == "current":
                        tech_age_score = 1
                        tech_age_level = "current"
                    break

            # Assess architecture patterns
            architecture_score = 0
            architecture_type = "unknown"
            for arch_type, patterns in legacy_indicators[
                "architecture_patterns"
            ].items():
                matches = [pattern for pattern in patterns if pattern in asset_text]
                if matches:
                    if arch_type == "monolithic":
                        architecture_score = 4
                        architecture_type = "monolithic"
                    elif arch_type == "soa":
                        architecture_score = 3
                        architecture_type = "soa"
                    elif arch_type == "microservices":
                        architecture_score = 2
                        architecture_type = "microservices"
                    elif arch_type == "serverless":
                        architecture_score = 1
                        architecture_type = "serverless"
                    break

            # Assess maintenance burden
            maintenance_score = 0
            maintenance_level = "unknown"
            for maint_level, indicators in legacy_indicators[
                "maintenance_indicators"
            ].items():
                matches = [ind for ind in indicators if ind in asset_text]
                if matches:
                    if maint_level == "high_maintenance":
                        maintenance_score = 3
                        maintenance_level = "high"
                    elif maint_level == "medium_maintenance":
                        maintenance_score = 2
                        maintenance_level = "medium"
                    elif maint_level == "low_maintenance":
                        maintenance_score = 1
                        maintenance_level = "low"
                    break

            # Calculate overall legacy score
            total_legacy_score = tech_age_score + architecture_score + maintenance_score

            if total_legacy_score >= 9:
                legacy_level = "critical"
            elif total_legacy_score >= 6:
                legacy_level = "high"
            elif total_legacy_score >= 4:
                legacy_level = "medium"
            else:
                legacy_level = "low"

            return {
                "technology_age": {"level": tech_age_level, "score": tech_age_score},
                "architecture_type": {
                    "type": architecture_type,
                    "score": architecture_score,
                },
                "maintenance_burden": {
                    "level": maintenance_level,
                    "score": maintenance_score,
                },
                "overall_legacy_score": total_legacy_score,
                "legacy_level": legacy_level,
                "modernization_urgency": self._assess_modernization_urgency(
                    total_legacy_score
                ),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Legacy system analysis failed: {e}")
            return {"legacy_level": "unknown", "error": str(e)}

    def _assess_modernization_urgency(self, legacy_score: int) -> Dict[str, Any]:
        """Assess urgency of modernization based on legacy score"""
        if legacy_score >= 9:
            return {
                "urgency": "immediate",
                "timeline": "0-6 months",
                "reasoning": "Critical legacy system requiring immediate attention",
            }
        elif legacy_score >= 6:
            return {
                "urgency": "high",
                "timeline": "6-12 months",
                "reasoning": "High legacy burden requiring prioritized modernization",
            }
        elif legacy_score >= 4:
            return {
                "urgency": "medium",
                "timeline": "1-2 years",
                "reasoning": "Moderate legacy system suitable for planned modernization",
            }
        else:
            return {
                "urgency": "low",
                "timeline": "2+ years",
                "reasoning": "Low legacy burden, modernization can be deferred",
            }


class SixRStrategyTool(BaseTool):
    """Tool for 6R strategy analysis and recommendations"""

    name: str = "sixr_strategy_tool"
    description: str = "Analyze assets and recommend optimal 6R migration strategy"

    def _run(
        self, asset_data: Dict[str, Any], legacy_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze and recommend 6R strategy"""
        try:
            # 6R Strategy decision factors
            strategy_factors = {
                "rehost": {
                    "indicators": [
                        "lift and shift",
                        "minimal changes",
                        "quick migration",
                    ],
                    "suitability_factors": [
                        "low_complexity",
                        "time_pressure",
                        "minimal_changes_needed",
                    ],
                },
                "replatform": {
                    "indicators": [
                        "platform upgrade",
                        "cloud native",
                        "some optimization",
                    ],
                    "suitability_factors": [
                        "medium_complexity",
                        "cloud_benefits",
                        "platform_modernization",
                    ],
                },
                "refactor": {
                    "indicators": [
                        "code changes",
                        "architecture improvements",
                        "optimization",
                    ],
                    "suitability_factors": [
                        "high_value",
                        "performance_issues",
                        "scalability_needs",
                    ],
                },
                "rearchitect": {
                    "indicators": [
                        "complete redesign",
                        "microservices",
                        "cloud native",
                    ],
                    "suitability_factors": [
                        "legacy_architecture",
                        "scalability_critical",
                        "long_term_value",
                    ],
                },
                "retire": {
                    "indicators": ["end of life", "redundant", "unused"],
                    "suitability_factors": [
                        "no_business_value",
                        "duplicate_functionality",
                        "end_of_life",
                    ],
                },
                "retain": {
                    "indicators": ["keep as is", "no migration", "compliance reasons"],
                    "suitability_factors": [
                        "compliance_requirements",
                        "low_priority",
                        "high_risk_migration",
                    ],
                },
            }

            asset_text = " ".join(
                str(value).lower() for value in asset_data.values() if value
            )
            legacy_level = legacy_assessment.get("legacy_level", "medium")

            # Score each strategy
            strategy_scores = {}
            for strategy, config in strategy_factors.items():
                score = 0
                matches = []

                # Check for direct indicators
                for indicator in config["indicators"]:
                    if indicator in asset_text:
                        score += 2
                        matches.append(indicator)

                # Apply legacy assessment influence
                if strategy == "retire" and legacy_level == "critical":
                    score += 3
                elif strategy == "rearchitect" and legacy_level in ["critical", "high"]:
                    score += 2
                elif strategy == "refactor" and legacy_level == "medium":
                    score += 2
                elif strategy == "replatform" and legacy_level in ["medium", "low"]:
                    score += 1
                elif strategy == "rehost" and legacy_level == "low":
                    score += 1
                elif strategy == "retain" and legacy_level == "low":
                    score += 1

                if score > 0:
                    strategy_scores[strategy] = {
                        "score": score,
                        "matches": matches,
                        "suitability": self._assess_strategy_suitability(
                            strategy, asset_data, legacy_assessment
                        ),
                    }

            # Determine recommended strategy
            if strategy_scores:
                recommended_strategy = max(
                    strategy_scores.keys(), key=lambda x: strategy_scores[x]["score"]
                )
                confidence = min(
                    strategy_scores[recommended_strategy]["score"] / 5.0, 1.0
                )
            else:
                recommended_strategy = self._default_strategy_recommendation(
                    legacy_level
                )
                confidence = 0.5

            return {
                "recommended_strategy": recommended_strategy,
                "confidence": confidence,
                "strategy_scores": strategy_scores,
                "strategy_rationale": self._generate_strategy_rationale(
                    recommended_strategy, legacy_assessment
                ),
                "alternative_strategies": list(strategy_scores.keys())[:3],
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"6R strategy analysis failed: {e}")
            return {
                "recommended_strategy": "rehost",
                "confidence": 0.5,
                "error": str(e),
            }

    def _assess_strategy_suitability(
        self,
        strategy: str,
        asset_data: Dict[str, Any],
        legacy_assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess suitability of strategy for the asset"""
        suitability_matrix = {
            "rehost": {
                "pros": ["Quick migration", "Low risk", "Minimal changes"],
                "cons": ["No modernization benefits", "Technical debt remains"],
                "best_for": "Time-sensitive migrations with stable applications",
            },
            "replatform": {
                "pros": [
                    "Some cloud benefits",
                    "Moderate effort",
                    "Improved performance",
                ],
                "cons": ["Platform lock-in", "Some complexity"],
                "best_for": "Applications that can benefit from cloud platforms",
            },
            "refactor": {
                "pros": ["Code optimization", "Better performance", "Maintainability"],
                "cons": ["Higher effort", "Testing complexity"],
                "best_for": "High-value applications with performance issues",
            },
            "rearchitect": {
                "pros": ["Full modernization", "Scalability", "Long-term benefits"],
                "cons": ["High effort", "High risk", "Long timeline"],
                "best_for": "Critical applications requiring complete modernization",
            },
            "retire": {
                "pros": [
                    "Cost savings",
                    "Reduced complexity",
                    "Focus on valuable assets",
                ],
                "cons": ["Potential business impact", "Data migration needs"],
                "best_for": "End-of-life or redundant applications",
            },
            "retain": {
                "pros": [
                    "No migration risk",
                    "Preserves stability",
                    "Compliance maintained",
                ],
                "cons": ["No cloud benefits", "Ongoing maintenance"],
                "best_for": "Compliance-critical or low-priority applications",
            },
        }

        return suitability_matrix.get(
            strategy, {"pros": [], "cons": [], "best_for": "Unknown"}
        )

    def _default_strategy_recommendation(self, legacy_level: str) -> str:
        """Provide default strategy based on legacy level"""
        strategy_defaults = {
            "critical": "rearchitect",
            "high": "refactor",
            "medium": "replatform",
            "low": "rehost",
            "unknown": "rehost",
        }
        return strategy_defaults.get(legacy_level, "rehost")

    def _generate_strategy_rationale(
        self, strategy: str, legacy_assessment: Dict[str, Any]
    ) -> str:
        """Generate rationale for strategy recommendation"""
        legacy_level = legacy_assessment.get("legacy_level", "unknown")

        rationales = {
            "rehost": f"Recommended for {legacy_level} legacy systems requiring quick migration with minimal changes",
            "replatform": f"Suitable for {legacy_level} legacy systems that can benefit from cloud platform features",
            "refactor": f"Appropriate for {legacy_level} legacy systems requiring code optimization and improvements",
            "rearchitect": f"Essential for {legacy_level} legacy systems requiring complete modernization",
            "retire": f"Recommended for {legacy_level} legacy systems with minimal business value",
            "retain": f"Suitable for {legacy_level} legacy systems with compliance or stability requirements",
        }

        return rationales.get(
            strategy, "Strategy recommendation based on system analysis"
        )


# Export all tool classes
__all__ = [
    "LegacySystemAnalysisTool",
    "SixRStrategyTool",
]
