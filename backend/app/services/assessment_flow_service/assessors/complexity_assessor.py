"""
Complexity assessment module for migration complexity analysis.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset as DiscoveryAsset

logger = logging.getLogger(__name__)


class ComplexityAssessor:
    """Handles migration complexity assessment for assets and flows."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def assess_migration_complexity(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess migration complexity for a collection of assets.

        Args:
            assets: List of asset data dictionaries

        Returns:
            Dict containing comprehensive complexity assessment
        """
        try:
            logger.info(f"🔍 Assessing migration complexity for {len(assets)} assets")

            if not assets:
                return self._create_empty_complexity_assessment()

            # Calculate individual asset complexities
            asset_complexities = []
            for asset in assets:
                asset_complexity = self._assess_asset_complexity_detailed(asset)
                asset_complexities.append(asset_complexity)

            # Calculate overall complexity metrics
            complexity_scores = [ac["complexity_score"] for ac in asset_complexities]
            overall_complexity_score = (
                sum(complexity_scores) / len(complexity_scores)
                if complexity_scores
                else 0.0
            )

            # Categorize complexities
            high_complexity_assets = [
                ac for ac in asset_complexities if ac["complexity_level"] == "high"
            ]
            medium_complexity_assets = [
                ac for ac in asset_complexities if ac["complexity_level"] == "medium"
            ]
            low_complexity_assets = [
                ac for ac in asset_complexities if ac["complexity_level"] == "low"
            ]

            # Calculate effort estimates
            effort_estimates = self._calculate_effort_estimates(asset_complexities)

            # Identify complexity factors
            complexity_factors = self._identify_complexity_factors(asset_complexities)

            # Generate recommendations
            recommendations = self._generate_complexity_recommendations(
                overall_complexity_score, complexity_factors
            )

            complexity_assessment = {
                "overall_complexity_score": round(overall_complexity_score, 2),
                "overall_complexity_level": self._determine_complexity_level(
                    overall_complexity_score
                ),
                "total_assets": len(assets),
                "complexity_distribution": {
                    "high": {
                        "count": len(high_complexity_assets),
                        "percentage": round(
                            len(high_complexity_assets) / len(assets) * 100, 1
                        ),
                    },
                    "medium": {
                        "count": len(medium_complexity_assets),
                        "percentage": round(
                            len(medium_complexity_assets) / len(assets) * 100, 1
                        ),
                    },
                    "low": {
                        "count": len(low_complexity_assets),
                        "percentage": round(
                            len(low_complexity_assets) / len(assets) * 100, 1
                        ),
                    },
                },
                "asset_complexities": asset_complexities,
                "effort_estimates": effort_estimates,
                "complexity_factors": complexity_factors,
                "recommendations": recommendations,
                "estimated_effort": effort_estimates["total_effort_description"],
            }

            logger.info(
                f"✅ Complexity assessment completed - Overall complexity: "
                f"{complexity_assessment['overall_complexity_level']}"
            )
            return complexity_assessment

        except Exception as e:
            logger.error(f"❌ Error assessing migration complexity: {e}")
            raise

    async def assess_flow_complexity(
        self, flow_id: str, assets: List[DiscoveryAsset]
    ) -> Dict[str, Any]:
        """
        Assess overall migration complexity for a discovery flow.

        Args:
            flow_id: Discovery flow identifier
            assets: List of DiscoveryAsset objects

        Returns:
            Dict containing flow-level complexity assessment
        """
        try:
            logger.info(f"🔍 Assessing flow-level complexity for flow: {flow_id}")

            # Convert assets to dictionaries for assessment
            asset_dicts = []
            for asset in assets:
                asset_dict = {
                    "id": str(asset.id),
                    "asset_name": asset.asset_name,
                    "asset_type": asset.asset_type,
                    "asset_subtype": asset.asset_subtype,
                    "migration_complexity": asset.migration_complexity,
                    "confidence_score": asset.confidence_score or 0.0,
                    "normalized_data": asset.normalized_data or {},
                    "raw_data": asset.raw_data or {},
                }
                asset_dicts.append(asset_dict)

            # Perform complexity assessment
            complexity_assessment = await self.assess_migration_complexity(asset_dicts)

            # Add flow-specific metrics
            complexity_assessment["flow_id"] = flow_id
            complexity_assessment["flow_complexity_factors"] = (
                self._assess_flow_specific_complexity(assets)
            )

            return complexity_assessment

        except Exception as e:
            logger.error(f"❌ Error assessing flow complexity: {e}")
            raise

    def _assess_asset_complexity_detailed(
        self, asset: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform detailed complexity assessment for a single asset."""

        # Base complexity factors
        type_complexity = self._assess_type_complexity(
            asset.get("asset_type"), asset.get("asset_subtype")
        )
        data_complexity = self._assess_data_complexity(asset.get("normalized_data", {}))
        dependency_complexity = self._assess_dependency_complexity(
            asset.get("normalized_data", {})
        )
        configuration_complexity = self._assess_configuration_complexity(
            asset.get("raw_data", {})
        )
        modernization_complexity = self._assess_modernization_complexity(
            asset.get("asset_type")
        )

        # Calculate weighted complexity score
        complexity_weights = {
            "type": 0.25,
            "data": 0.20,
            "dependency": 0.25,
            "configuration": 0.15,
            "modernization": 0.15,
        }

        complexity_score = (
            type_complexity * complexity_weights["type"]
            + data_complexity * complexity_weights["data"]
            + dependency_complexity * complexity_weights["dependency"]
            + configuration_complexity * complexity_weights["configuration"]
            + modernization_complexity * complexity_weights["modernization"]
        )

        # Determine complexity level
        complexity_level = self._determine_complexity_level(complexity_score)

        # Identify specific complexity factors
        complexity_factors = []
        if type_complexity > 0.7:
            complexity_factors.append(
                "Complex asset type requiring specialized migration approach"
            )
        if data_complexity > 0.6:
            complexity_factors.append("Complex data structures or large data volumes")
        if dependency_complexity > 0.7:
            complexity_factors.append(
                "High dependency complexity with multiple interconnections"
            )
        if configuration_complexity > 0.6:
            complexity_factors.append(
                "Complex configuration requiring manual intervention"
            )
        if modernization_complexity > 0.7:
            complexity_factors.append(
                "High modernization potential increasing migration options"
            )

        # Estimate effort
        effort_weeks = self._estimate_asset_effort(
            complexity_score, asset.get("asset_type")
        )

        return {
            "asset_id": asset.get("id"),
            "asset_name": asset.get("asset_name"),
            "complexity_score": round(complexity_score, 2),
            "complexity_level": complexity_level,
            "complexity_factors": complexity_factors,
            "estimated_effort_weeks": effort_weeks,
            "component_complexities": {
                "type": round(type_complexity, 2),
                "data": round(data_complexity, 2),
                "dependency": round(dependency_complexity, 2),
                "configuration": round(configuration_complexity, 2),
                "modernization": round(modernization_complexity, 2),
            },
        }

    def _assess_type_complexity(
        self, asset_type: Optional[str], asset_subtype: Optional[str] = None
    ) -> float:
        """Assess complexity based on asset type and subtype."""

        # Base type complexities
        type_complexities = {
            "server": 0.3,
            "application": 0.6,
            "database": 0.7,
            "legacy_system": 0.9,
            "infrastructure": 0.4,
            "network": 0.5,
            "storage": 0.4,
            "middleware": 0.7,
            "unknown": 0.8,
        }

        base_complexity = type_complexities.get(
            asset_type.lower() if asset_type else "unknown", 0.8
        )

        # Subtype modifiers
        if asset_subtype:
            subtype_modifiers = {
                "legacy": 0.2,
                "enterprise": 0.1,
                "critical": 0.15,
                "distributed": 0.1,
                "mainframe": 0.3,
                "custom": 0.2,
            }

            for modifier_key, modifier_value in subtype_modifiers.items():
                if modifier_key in asset_subtype.lower():
                    base_complexity = min(1.0, base_complexity + modifier_value)
                    break

        return base_complexity

    def _assess_data_complexity(self, normalized_data: Dict[str, Any]) -> float:
        """Assess complexity based on data characteristics."""

        complexity_score = 0.0

        # Data volume indicators
        if "data_size" in normalized_data:
            size_gb = normalized_data.get("data_size", 0)
            if size_gb > 1000:  # 1TB+
                complexity_score += 0.3
            elif size_gb > 100:  # 100GB+
                complexity_score += 0.2
            elif size_gb > 10:  # 10GB+
                complexity_score += 0.1

        # Data structure complexity
        if "schema_complexity" in normalized_data:
            schema_complexity = normalized_data.get("schema_complexity", "simple")
            if schema_complexity == "complex":
                complexity_score += 0.3
            elif schema_complexity == "medium":
                complexity_score += 0.2

        # Number of tables/collections
        if "table_count" in normalized_data:
            table_count = normalized_data.get("table_count", 0)
            if table_count > 100:
                complexity_score += 0.2
            elif table_count > 50:
                complexity_score += 0.1

        # Data consistency issues
        if normalized_data.get("data_quality_issues", False):
            complexity_score += 0.2

        # Compliance requirements
        if normalized_data.get("compliance_requirements"):
            compliance_types = len(normalized_data.get("compliance_requirements", []))
            complexity_score += min(0.3, compliance_types * 0.1)

        return min(1.0, complexity_score)

    def _assess_dependency_complexity(self, normalized_data: Dict[str, Any]) -> float:
        """Assess complexity based on asset dependencies."""

        complexity_score = 0.0

        # Number of dependencies
        dependencies = normalized_data.get("dependencies", [])
        dependency_count = len(dependencies) if isinstance(dependencies, list) else 0

        if dependency_count > 20:
            complexity_score += 0.4
        elif dependency_count > 10:
            complexity_score += 0.3
        elif dependency_count > 5:
            complexity_score += 0.2
        elif dependency_count > 0:
            complexity_score += 0.1

        # Dependency types
        if "dependency_types" in normalized_data:
            dependency_types = normalized_data.get("dependency_types", [])
            critical_types = ["database", "legacy_system", "external_service"]
            critical_count = sum(
                1 for dep_type in dependency_types if dep_type in critical_types
            )
            complexity_score += min(0.3, critical_count * 0.1)

        # Circular dependencies
        if normalized_data.get("circular_dependencies", False):
            complexity_score += 0.2

        # External dependencies
        external_deps = normalized_data.get("external_dependencies", [])
        if len(external_deps) > 0:
            complexity_score += min(0.2, len(external_deps) * 0.05)

        return min(1.0, complexity_score)

    def _assess_configuration_complexity(self, raw_data: Dict[str, Any]) -> float:
        """Assess complexity based on configuration characteristics."""

        complexity_score = 0.0

        # Configuration size (number of settings)
        config_items = 0
        for key, value in raw_data.items():
            if isinstance(value, dict):
                config_items += len(value)
            elif isinstance(value, list):
                config_items += len(value)
            else:
                config_items += 1

        if config_items > 100:
            complexity_score += 0.3
        elif config_items > 50:
            complexity_score += 0.2
        elif config_items > 20:
            complexity_score += 0.1

        # Custom configurations
        custom_indicators = ["custom", "modified", "non-standard", "proprietary"]
        for indicator in custom_indicators:
            for key in raw_data.keys():
                if indicator in key.lower():
                    complexity_score += 0.1
                    break

        # Security configurations
        security_indicators = [
            "ssl",
            "tls",
            "certificate",
            "encryption",
            "authentication",
        ]
        security_count = sum(
            1
            for indicator in security_indicators
            for key in raw_data.keys()
            if indicator in key.lower()
        )
        complexity_score += min(0.2, security_count * 0.05)

        return min(1.0, complexity_score)

    def _assess_modernization_complexity(self, asset_type: Optional[str]) -> float:
        """Assess complexity related to modernization opportunities."""

        if not asset_type:
            return 0.5

        # Modernization potential by type
        modernization_complexities = {
            "application": 0.8,  # High modernization potential, high complexity
            "database": 0.6,  # Medium modernization potential
            "server": 0.4,  # Lower modernization complexity
            "infrastructure": 0.5,  # Medium modernization options
            "legacy_system": 0.9,  # Highest modernization complexity
            "middleware": 0.7,  # High modernization potential
            "network": 0.3,  # Lower modernization complexity
            "storage": 0.4,  # Lower modernization complexity
        }

        return modernization_complexities.get(asset_type.lower(), 0.5)

    def _determine_complexity_level(self, complexity_score: float) -> str:
        """Determine categorical complexity level from numeric score."""
        if complexity_score >= 0.7:
            return "high"
        elif complexity_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _estimate_asset_effort(
        self, complexity_score: float, asset_type: Optional[str]
    ) -> int:
        """Estimate effort in weeks for asset migration."""

        # Base effort by type
        base_efforts = {
            "server": 1,
            "application": 3,
            "database": 4,
            "legacy_system": 8,
            "infrastructure": 2,
            "network": 2,
            "storage": 1,
            "middleware": 3,
            "unknown": 4,
        }

        base_effort = base_efforts.get(
            asset_type.lower() if asset_type else "unknown", 4
        )

        # Apply complexity multiplier
        if complexity_score >= 0.8:
            multiplier = 2.5
        elif complexity_score >= 0.6:
            multiplier = 2.0
        elif complexity_score >= 0.4:
            multiplier = 1.5
        else:
            multiplier = 1.0

        return max(1, int(base_effort * multiplier))

    def _calculate_effort_estimates(
        self, asset_complexities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall effort estimates."""

        total_effort_weeks = sum(
            ac["estimated_effort_weeks"] for ac in asset_complexities
        )

        # Categorize by effort
        low_effort = [
            ac for ac in asset_complexities if ac["estimated_effort_weeks"] <= 2
        ]
        medium_effort = [
            ac for ac in asset_complexities if 3 <= ac["estimated_effort_weeks"] <= 6
        ]
        high_effort = [
            ac for ac in asset_complexities if ac["estimated_effort_weeks"] > 6
        ]

        # Calculate duration description
        if total_effort_weeks <= 4:
            duration_description = f"{total_effort_weeks} weeks"
        elif total_effort_weeks <= 24:
            months = total_effort_weeks // 4
            weeks = total_effort_weeks % 4
            duration_description = f"{months} month{'s' if months > 1 else ''}"
            if weeks > 0:
                duration_description += f" {weeks} week{'s' if weeks > 1 else ''}"
        else:
            months = total_effort_weeks // 4
            duration_description = f"{months} months"

        return {
            "total_effort_weeks": total_effort_weeks,
            "total_effort_description": duration_description,
            "effort_distribution": {
                "low_effort": {
                    "count": len(low_effort),
                    "weeks": sum(ac["estimated_effort_weeks"] for ac in low_effort),
                },
                "medium_effort": {
                    "count": len(medium_effort),
                    "weeks": sum(ac["estimated_effort_weeks"] for ac in medium_effort),
                },
                "high_effort": {
                    "count": len(high_effort),
                    "weeks": sum(ac["estimated_effort_weeks"] for ac in high_effort),
                },
            },
            "parallel_execution_potential": self._assess_parallel_potential(
                asset_complexities
            ),
            "critical_path_weeks": self._estimate_critical_path(asset_complexities),
        }

    def _identify_complexity_factors(
        self, asset_complexities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify common complexity factors across assets."""

        complexity_factors = []
        total_assets = len(asset_complexities)

        if total_assets == 0:
            return complexity_factors

        # High complexity assets
        high_complexity_count = sum(
            1 for ac in asset_complexities if ac["complexity_level"] == "high"
        )
        if high_complexity_count > 0:
            complexity_factors.append(
                {
                    "factor": "High Complexity Assets",
                    "count": high_complexity_count,
                    "percentage": round(high_complexity_count / total_assets * 100, 1),
                    "impact": (
                        "high"
                        if high_complexity_count / total_assets > 0.3
                        else "medium"
                    ),
                    "description": f"{high_complexity_count} assets require specialized migration approaches",
                }
            )

        # Data complexity issues
        data_complex_count = sum(
            1 for ac in asset_complexities if ac["component_complexities"]["data"] > 0.6
        )
        if data_complex_count > 0:
            complexity_factors.append(
                {
                    "factor": "Data Complexity",
                    "count": data_complex_count,
                    "percentage": round(data_complex_count / total_assets * 100, 1),
                    "impact": "medium",
                    "description": f"{data_complex_count} assets have complex data migration requirements",
                }
            )

        # Dependency complexity
        dependency_complex_count = sum(
            1
            for ac in asset_complexities
            if ac["component_complexities"]["dependency"] > 0.7
        )
        if dependency_complex_count > 0:
            complexity_factors.append(
                {
                    "factor": "Dependency Complexity",
                    "count": dependency_complex_count,
                    "percentage": round(
                        dependency_complex_count / total_assets * 100, 1
                    ),
                    "impact": "high",
                    "description": f"{dependency_complex_count} assets have complex dependency requirements",
                }
            )

        return complexity_factors

    def _generate_complexity_recommendations(
        self, overall_complexity_score: float, complexity_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate complexity management recommendations."""

        recommendations = []

        if overall_complexity_score >= 0.7:
            recommendations.extend(
                [
                    "Consider phased migration approach for complex assets",
                    "Engage specialized migration experts for high-complexity components",
                    "Plan extended timelines for complex asset migrations",
                    "Implement comprehensive testing strategies for complex systems",
                ]
            )
        elif overall_complexity_score >= 0.4:
            recommendations.extend(
                [
                    "Plan adequate time for medium-complexity migrations",
                    "Consider pilot migrations for complex assets",
                    "Prepare detailed migration runbooks",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Standard migration approaches should be sufficient",
                    "Consider accelerated migration timelines",
                ]
            )

        # Add specific recommendations based on complexity factors
        for factor in complexity_factors:
            if (
                factor["factor"] == "High Complexity Assets"
                and factor["impact"] == "high"
            ):
                recommendations.append(
                    "Prioritize architecture reviews for complex systems"
                )
            elif factor["factor"] == "Data Complexity" and factor["percentage"] > 30:
                recommendations.append(
                    "Invest in data migration tools and validation processes"
                )
            elif (
                factor["factor"] == "Dependency Complexity"
                and factor["impact"] == "high"
            ):
                recommendations.append(
                    "Create detailed dependency maps and migration sequencing"
                )

        return list(set(recommendations))  # Remove duplicates

    def _assess_parallel_potential(
        self, asset_complexities: List[Dict[str, Any]]
    ) -> float:
        """Assess potential for parallel migration execution."""

        if not asset_complexities:
            return 0.0

        # Assets with low dependency complexity can potentially be migrated in parallel
        low_dependency_count = sum(
            1
            for ac in asset_complexities
            if ac["component_complexities"]["dependency"] < 0.4
        )

        parallel_potential = low_dependency_count / len(asset_complexities)
        return round(parallel_potential, 2)

    def _estimate_critical_path(self, asset_complexities: List[Dict[str, Any]]) -> int:
        """Estimate critical path duration assuming optimal sequencing."""

        if not asset_complexities:
            return 0

        # Sort assets by dependency complexity (high dependency assets likely on critical path)
        sorted_assets = sorted(
            asset_complexities,
            key=lambda x: x["component_complexities"]["dependency"],
            reverse=True,
        )

        # Take top 20% of assets with highest dependency complexity
        critical_path_count = max(1, len(sorted_assets) // 5)
        critical_path_assets = sorted_assets[:critical_path_count]

        # Sum effort for critical path assets
        critical_path_weeks = sum(
            ac["estimated_effort_weeks"] for ac in critical_path_assets
        )

        return critical_path_weeks

    def _assess_flow_specific_complexity(
        self, assets: List[DiscoveryAsset]
    ) -> List[Dict[str, Any]]:
        """Assess complexity factors specific to the entire flow."""

        flow_complexities = []

        # Check for asset type diversity
        asset_types = set(asset.asset_type for asset in assets if asset.asset_type)
        if len(asset_types) > 5:
            flow_complexities.append(
                {
                    "complexity": "High Asset Type Diversity",
                    "description": f"Flow contains {len(asset_types)} different asset types",
                    "impact": "Requires diverse skill sets and migration approaches",
                    "severity": "medium",
                }
            )

        # Check for scale complexity
        total_assets = len(assets)
        if total_assets > 100:
            flow_complexities.append(
                {
                    "complexity": "Large Scale Migration",
                    "description": f"Flow contains {total_assets} assets",
                    "impact": "Increased coordination and management complexity",
                    "severity": "high" if total_assets > 200 else "medium",
                }
            )

        # Check for legacy system concentration
        legacy_count = sum(1 for asset in assets if asset.asset_type == "legacy_system")
        if legacy_count > total_assets * 0.3:
            flow_complexities.append(
                {
                    "complexity": "High Legacy System Concentration",
                    "description": f"{legacy_count} legacy systems in flow",
                    "impact": "May require specialized legacy migration expertise",
                    "severity": "high",
                }
            )

        return flow_complexities

    def _create_empty_complexity_assessment(self) -> Dict[str, Any]:
        """Create empty complexity assessment for flows with no assets."""
        return {
            "overall_complexity_score": 0.0,
            "overall_complexity_level": "low",
            "total_assets": 0,
            "complexity_distribution": {
                "high": {"count": 0, "percentage": 0.0},
                "medium": {"count": 0, "percentage": 0.0},
                "low": {"count": 0, "percentage": 0.0},
            },
            "asset_complexities": [],
            "effort_estimates": {
                "total_effort_weeks": 0,
                "total_effort_description": "0 weeks",
                "effort_distribution": {
                    "low_effort": {"count": 0, "weeks": 0},
                    "medium_effort": {"count": 0, "weeks": 0},
                    "high_effort": {"count": 0, "weeks": 0},
                },
                "parallel_execution_potential": 0.0,
                "critical_path_weeks": 0,
            },
            "complexity_factors": [],
            "recommendations": [
                "Complete asset discovery before proceeding with complexity assessment"
            ],
            "estimated_effort": "0 weeks",
        }
