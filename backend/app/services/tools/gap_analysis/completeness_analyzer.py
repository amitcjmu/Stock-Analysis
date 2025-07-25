"""
Completeness Analyzer Tool - Analyzes completeness of critical attributes in collected data
"""

import logging
from typing import Any, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import ATTRIBUTE_CATEGORIES

logger = logging.getLogger(__name__)


class CompletenessAnalyzerTool(AsyncBaseDiscoveryTool):
    """Analyzes completeness of critical attributes in collected data"""

    name: str = "completeness_analyzer"
    description: str = "Analyze completeness and quality of critical attributes"

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="completeness_analyzer",
            description="Analyze completeness and quality of critical attributes",
            tool_class=cls,
            categories=["gap_analysis", "data_quality"],
            required_params=["data", "attribute_mapping"],
            optional_params=[],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self, data: List[Dict[str, Any]], attribute_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze completeness of mapped attributes in data"""
        try:
            self.log_with_context(
                "info", f"Analyzing completeness for {len(data)} records"
            )

            analysis_results = {
                "total_records": len(data),
                "attribute_completeness": {},
                "category_completeness": {
                    "infrastructure": {"total": 8, "complete": 0, "percentage": 0.0},
                    "application": {"total": 6, "complete": 0, "percentage": 0.0},
                    "operational": {"total": 6, "complete": 0, "percentage": 0.0},
                    "dependencies": {"total": 4, "complete": 0, "percentage": 0.0},
                },
                "quality_issues": [],
                "recommendations": [],
            }

            # Analyze each attribute
            for attribute, field_name in attribute_mapping.items():
                completeness_info = {
                    "field_name": field_name,
                    "records_with_data": 0,
                    "completeness_percentage": 0.0,
                    "null_count": 0,
                    "empty_count": 0,
                    "quality_score": 0.0,
                }

                # Count completeness
                for record in data:
                    value = record.get(field_name)
                    if value is not None:
                        if value == "" or (
                            isinstance(value, str)
                            and value.lower() in ["null", "n/a", "unknown"]
                        ):
                            completeness_info["empty_count"] += 1
                        else:
                            completeness_info["records_with_data"] += 1
                    else:
                        completeness_info["null_count"] += 1

                # Calculate percentages
                if len(data) > 0:
                    completeness_info["completeness_percentage"] = (
                        completeness_info["records_with_data"] / len(data)
                    ) * 100
                    completeness_info["quality_score"] = self._calculate_quality_score(
                        completeness_info, len(data)
                    )

                analysis_results["attribute_completeness"][
                    attribute
                ] = completeness_info

                # Update category completeness
                for category, attributes in ATTRIBUTE_CATEGORIES.items():
                    if (
                        attribute in attributes
                        and completeness_info["completeness_percentage"] > 80
                    ):
                        analysis_results["category_completeness"][category][
                            "complete"
                        ] += 1

                # Identify quality issues
                if completeness_info["completeness_percentage"] < 50:
                    analysis_results["quality_issues"].append(
                        {
                            "attribute": attribute,
                            "issue": "Low completeness",
                            "impact": (
                                "high"
                                if attribute
                                in ["hostname", "application_name", "owner"]
                                else "medium"
                            ),
                            "recommendation": f"Prioritize collecting {attribute} data",
                        }
                    )

            # Calculate category percentages
            for category in analysis_results["category_completeness"]:
                cat_data = analysis_results["category_completeness"][category]
                cat_data["percentage"] = (
                    cat_data["complete"] / cat_data["total"]
                ) * 100

            # Generate recommendations
            analysis_results[
                "recommendations"
            ] = self._generate_completeness_recommendations(analysis_results)

            self.log_with_context("info", "Completeness analysis completed")
            return analysis_results

        except Exception as e:
            self.log_with_context("error", f"Error in completeness analysis: {e}")
            return {"error": str(e)}

    def _calculate_quality_score(
        self, completeness_info: Dict[str, Any], total_records: int
    ) -> float:
        """Calculate quality score for an attribute"""
        if total_records == 0:
            return 0.0

        # Base score on completeness
        score = completeness_info["completeness_percentage"] / 100

        # Penalize for empty/null values
        empty_ratio = completeness_info["empty_count"] / total_records
        null_ratio = completeness_info["null_count"] / total_records

        score = score * (1 - empty_ratio * 0.5) * (1 - null_ratio * 0.3)

        return round(score * 100, 2)

    def _generate_completeness_recommendations(
        self, analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on completeness analysis"""
        recommendations = []

        # Check category completeness
        for category, data in analysis["category_completeness"].items():
            if data["percentage"] < 50:
                recommendations.append(
                    f"Critical: {category} attributes are only {data['percentage']:.0f}% complete. "
                    f"Focus on collecting {category} data to improve migration readiness."
                )

        # Check for critical missing attributes
        critical_attributes = ["hostname", "application_name", "owner", "environment"]
        for attr in critical_attributes:
            if attr in analysis["attribute_completeness"]:
                if (
                    analysis["attribute_completeness"][attr]["completeness_percentage"]
                    < 80
                ):
                    recommendations.append(
                        f"High Priority: {attr} is critical but only "
                        f"{analysis['attribute_completeness'][attr]['completeness_percentage']:.0f}% complete"
                    )

        return recommendations
