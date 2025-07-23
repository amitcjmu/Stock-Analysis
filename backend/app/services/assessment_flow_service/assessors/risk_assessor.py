"""
Risk assessment module for migration risk analysis.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset as DiscoveryAsset

logger = logging.getLogger(__name__)


class RiskAssessor:
    """Handles migration risk assessment for assets and flows."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def assess_migration_risks(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess migration risks for a collection of assets.

        Args:
            assets: List of asset data dictionaries

        Returns:
            Dict containing comprehensive risk assessment
        """
        try:
            logger.info(f"🔍 Assessing migration risks for {len(assets)} assets")

            if not assets:
                return self._create_empty_risk_assessment()

            # Calculate individual asset risks
            asset_risks = []
            for asset in assets:
                asset_risk = self._assess_asset_risk_detailed(asset)
                asset_risks.append(asset_risk)

            # Calculate overall risk metrics
            risk_scores = [ar["risk_score"] for ar in asset_risks]
            overall_risk_score = (
                sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            )

            # Categorize risks
            high_risk_assets = [ar for ar in asset_risks if ar["risk_level"] == "high"]
            medium_risk_assets = [
                ar for ar in asset_risks if ar["risk_level"] == "medium"
            ]
            low_risk_assets = [ar for ar in asset_risks if ar["risk_level"] == "low"]

            # Identify risk factors
            risk_factors = self._identify_risk_factors(asset_risks)

            # Generate mitigation strategies
            mitigation_strategies = self._generate_mitigation_strategies(
                risk_factors, asset_risks
            )

            risk_assessment = {
                "overall_risk_score": round(overall_risk_score, 2),
                "overall_risk_level": self._determine_risk_level(overall_risk_score),
                "total_assets": len(assets),
                "risk_distribution": {
                    "high": {
                        "count": len(high_risk_assets),
                        "percentage": round(
                            len(high_risk_assets) / len(assets) * 100, 1
                        ),
                    },
                    "medium": {
                        "count": len(medium_risk_assets),
                        "percentage": round(
                            len(medium_risk_assets) / len(assets) * 100, 1
                        ),
                    },
                    "low": {
                        "count": len(low_risk_assets),
                        "percentage": round(
                            len(low_risk_assets) / len(assets) * 100, 1
                        ),
                    },
                },
                "asset_risks": asset_risks,
                "risk_factors": risk_factors,
                "mitigation_strategies": mitigation_strategies,
                "recommendations": self._generate_risk_recommendations(
                    overall_risk_score, risk_factors
                ),
            }

            logger.info(
                f"✅ Risk assessment completed - Overall risk: {risk_assessment['overall_risk_level']}"
            )
            return risk_assessment

        except Exception as e:
            logger.error(f"❌ Error assessing migration risks: {e}")
            raise

    async def assess_flow_risk(
        self, flow_id: str, assets: List[DiscoveryAsset]
    ) -> Dict[str, Any]:
        """
        Assess overall migration risk for a discovery flow.

        Args:
            flow_id: Discovery flow identifier
            assets: List of DiscoveryAsset objects

        Returns:
            Dict containing flow-level risk assessment
        """
        try:
            logger.info(f"🔍 Assessing flow-level risks for flow: {flow_id}")

            # Convert assets to dictionaries for assessment
            asset_dicts = []
            for asset in assets:
                asset_dict = {
                    "id": str(asset.id),
                    "asset_name": asset.asset_name,
                    "asset_type": asset.asset_type,
                    "migration_complexity": asset.migration_complexity,
                    "confidence_score": asset.confidence_score or 0.0,
                    "validation_status": asset.validation_status,
                    "migration_ready": asset.migration_ready,
                    "migration_priority": asset.migration_priority or 3,
                    "normalized_data": asset.normalized_data or {},
                }
                asset_dicts.append(asset_dict)

            # Perform risk assessment
            risk_assessment = await self.assess_migration_risks(asset_dicts)

            # Add flow-specific metrics
            risk_assessment["flow_id"] = flow_id
            risk_assessment["flow_risk_factors"] = self._assess_flow_specific_risks(
                assets
            )

            return risk_assessment

        except Exception as e:
            logger.error(f"❌ Error assessing flow risks: {e}")
            raise

    def _assess_asset_risk_detailed(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed risk assessment for a single asset."""

        # Base risk factors
        complexity_risk = self._assess_complexity_risk(
            asset.get("migration_complexity", "medium")
        )
        confidence_risk = self._assess_confidence_risk(
            asset.get("confidence_score", 0.5)
        )
        validation_risk = self._assess_validation_risk(
            asset.get("validation_status", "pending")
        )
        type_risk = self._assess_type_risk(asset.get("asset_type", "unknown"))
        priority_risk = self._assess_priority_risk(asset.get("migration_priority", 3))

        # Calculate weighted risk score
        risk_weights = {
            "complexity": 0.30,
            "confidence": 0.25,
            "validation": 0.20,
            "type": 0.15,
            "priority": 0.10,
        }

        risk_score = (
            complexity_risk * risk_weights["complexity"]
            + confidence_risk * risk_weights["confidence"]
            + validation_risk * risk_weights["validation"]
            + type_risk * risk_weights["type"]
            + priority_risk * risk_weights["priority"]
        )

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Identify specific risk factors
        risk_factors = []
        if complexity_risk > 0.7:
            risk_factors.append("High migration complexity")
        if confidence_risk > 0.6:
            risk_factors.append("Low confidence in asset data")
        if validation_risk > 0.5:
            risk_factors.append("Asset validation issues")
        if type_risk > 0.6:
            risk_factors.append("Asset type migration challenges")

        return {
            "asset_id": asset.get("id"),
            "asset_name": asset.get("asset_name"),
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "component_risks": {
                "complexity": round(complexity_risk, 2),
                "confidence": round(confidence_risk, 2),
                "validation": round(validation_risk, 2),
                "type": round(type_risk, 2),
                "priority": round(priority_risk, 2),
            },
        }

    def _assess_complexity_risk(self, complexity: str) -> float:
        """Assess risk based on migration complexity."""
        complexity_risks = {"low": 0.2, "medium": 0.5, "high": 0.9, "unknown": 0.7}
        return complexity_risks.get(
            complexity.lower() if complexity else "unknown", 0.7
        )

    def _assess_confidence_risk(self, confidence_score: float) -> float:
        """Assess risk based on confidence score (inverse relationship)."""
        if confidence_score >= 0.9:
            return 0.1
        elif confidence_score >= 0.8:
            return 0.2
        elif confidence_score >= 0.7:
            return 0.4
        elif confidence_score >= 0.6:
            return 0.6
        else:
            return 0.8

    def _assess_validation_risk(self, validation_status: str) -> float:
        """Assess risk based on validation status."""
        validation_risks = {
            "approved": 0.1,
            "pending": 0.5,
            "rejected": 0.8,
            "needs_review": 0.6,
            "unknown": 0.7,
        }
        return validation_risks.get(
            validation_status.lower() if validation_status else "unknown", 0.7
        )

    def _assess_type_risk(self, asset_type: str) -> float:
        """Assess risk based on asset type."""
        type_risks = {
            "server": 0.3,
            "application": 0.5,
            "database": 0.7,
            "legacy_system": 0.8,
            "infrastructure": 0.4,
            "network": 0.6,
            "unknown": 0.8,
        }
        return type_risks.get(asset_type.lower() if asset_type else "unknown", 0.8)

    def _assess_priority_risk(self, priority: int) -> float:
        """Assess risk based on migration priority (1=highest, 5=lowest)."""
        if priority <= 1:
            return 0.2  # High priority = lower risk tolerance
        elif priority <= 2:
            return 0.3
        elif priority <= 3:
            return 0.5
        elif priority <= 4:
            return 0.7
        else:
            return 0.8

    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine categorical risk level from numeric score."""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _identify_risk_factors(
        self, asset_risks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify common risk factors across assets."""

        risk_factors = []
        total_assets = len(asset_risks)

        if total_assets == 0:
            return risk_factors

        # High complexity assets
        high_complexity_count = sum(
            1 for ar in asset_risks if ar["component_risks"]["complexity"] > 0.7
        )
        if high_complexity_count > 0:
            risk_factors.append(
                {
                    "factor": "High Complexity Assets",
                    "count": high_complexity_count,
                    "percentage": round(high_complexity_count / total_assets * 100, 1),
                    "severity": (
                        "high"
                        if high_complexity_count / total_assets > 0.3
                        else "medium"
                    ),
                    "description": f"{high_complexity_count} assets have high migration complexity",
                }
            )

        # Low confidence assets
        low_confidence_count = sum(
            1 for ar in asset_risks if ar["component_risks"]["confidence"] > 0.6
        )
        if low_confidence_count > 0:
            risk_factors.append(
                {
                    "factor": "Low Confidence Data",
                    "count": low_confidence_count,
                    "percentage": round(low_confidence_count / total_assets * 100, 1),
                    "severity": (
                        "medium" if low_confidence_count / total_assets > 0.2 else "low"
                    ),
                    "description": f"{low_confidence_count} assets have low confidence scores",
                }
            )

        # Validation issues
        validation_issues_count = sum(
            1 for ar in asset_risks if ar["component_risks"]["validation"] > 0.5
        )
        if validation_issues_count > 0:
            risk_factors.append(
                {
                    "factor": "Validation Issues",
                    "count": validation_issues_count,
                    "percentage": round(
                        validation_issues_count / total_assets * 100, 1
                    ),
                    "severity": (
                        "high"
                        if validation_issues_count / total_assets > 0.4
                        else "medium"
                    ),
                    "description": f"{validation_issues_count} assets have validation concerns",
                }
            )

        return risk_factors

    def _generate_mitigation_strategies(
        self, risk_factors: List[Dict[str, Any]], asset_risks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate mitigation strategies based on identified risks."""

        strategies = []

        # Strategy for high complexity assets
        high_complexity_assets = [
            ar for ar in asset_risks if ar["component_risks"]["complexity"] > 0.7
        ]
        if high_complexity_assets:
            strategies.append(
                {
                    "strategy": "Complexity Mitigation",
                    "priority": "high",
                    "affected_assets": len(high_complexity_assets),
                    "actions": [
                        "Conduct detailed technical assessment for complex assets",
                        "Consider proof-of-concept migrations",
                        "Engage specialized migration expertise",
                        "Plan additional time and resources",
                    ],
                    "estimated_effort": "2-4 weeks additional planning per asset",
                }
            )

        # Strategy for low confidence data
        low_confidence_assets = [
            ar for ar in asset_risks if ar["component_risks"]["confidence"] > 0.6
        ]
        if low_confidence_assets:
            strategies.append(
                {
                    "strategy": "Data Quality Improvement",
                    "priority": "medium",
                    "affected_assets": len(low_confidence_assets),
                    "actions": [
                        "Perform additional discovery activities",
                        "Validate asset configurations and dependencies",
                        "Implement data quality checks",
                        "Engage asset owners for verification",
                    ],
                    "estimated_effort": "1-2 weeks per asset group",
                }
            )

        # Strategy for validation issues
        validation_issues_assets = [
            ar for ar in asset_risks if ar["component_risks"]["validation"] > 0.5
        ]
        if validation_issues_assets:
            strategies.append(
                {
                    "strategy": "Validation Resolution",
                    "priority": "high",
                    "affected_assets": len(validation_issues_assets),
                    "actions": [
                        "Review and resolve validation errors",
                        "Update asset classifications",
                        "Verify compliance requirements",
                        "Obtain stakeholder approvals",
                    ],
                    "estimated_effort": "3-5 days per asset",
                }
            )

        return strategies

    def _generate_risk_recommendations(
        self, overall_risk_score: float, risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate high-level risk management recommendations."""

        recommendations = []

        if overall_risk_score >= 0.7:
            recommendations.extend(
                [
                    "Consider phased migration approach to reduce risk exposure",
                    "Implement comprehensive testing and rollback procedures",
                    "Establish dedicated risk management team",
                    "Plan for extended migration timeline",
                ]
            )
        elif overall_risk_score >= 0.4:
            recommendations.extend(
                [
                    "Implement standard risk mitigation practices",
                    "Plan regular risk assessment checkpoints",
                    "Prepare contingency plans for high-risk assets",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Proceed with standard migration practices",
                    "Monitor for emerging risks during execution",
                ]
            )

        # Add specific recommendations based on risk factors
        for factor in risk_factors:
            if (
                factor["factor"] == "High Complexity Assets"
                and factor["severity"] == "high"
            ):
                recommendations.append(
                    "Prioritize architecture reviews for complex systems"
                )
            elif (
                factor["factor"] == "Low Confidence Data" and factor["percentage"] > 30
            ):
                recommendations.append(
                    "Invest in additional discovery tools and processes"
                )
            elif (
                factor["factor"] == "Validation Issues" and factor["severity"] == "high"
            ):
                recommendations.append(
                    "Establish clear validation criteria and approval workflows"
                )

        return list(set(recommendations))  # Remove duplicates

    def _assess_flow_specific_risks(
        self, assets: List[DiscoveryAsset]
    ) -> List[Dict[str, Any]]:
        """Assess risks specific to the entire flow."""

        flow_risks = []

        # Check for asset type diversity
        asset_types = set(asset.asset_type for asset in assets if asset.asset_type)
        if len(asset_types) > 5:
            flow_risks.append(
                {
                    "risk": "High Asset Diversity",
                    "description": f"Flow contains {len(asset_types)} different asset types",
                    "impact": "May require diverse skill sets and migration approaches",
                    "severity": "medium",
                }
            )

        # Check for dependency complexity
        total_assets = len(assets)
        if total_assets > 50:
            flow_risks.append(
                {
                    "risk": "Large Asset Volume",
                    "description": f"Flow contains {total_assets} assets",
                    "impact": "Increased coordination and management complexity",
                    "severity": "medium" if total_assets < 100 else "high",
                }
            )

        # Check for validation completeness
        unvalidated_count = sum(
            1 for asset in assets if asset.validation_status != "approved"
        )
        if unvalidated_count > total_assets * 0.2:
            flow_risks.append(
                {
                    "risk": "Incomplete Validation",
                    "description": f"{unvalidated_count} assets require validation",
                    "impact": "May delay migration start or cause execution issues",
                    "severity": (
                        "high" if unvalidated_count > total_assets * 0.4 else "medium"
                    ),
                }
            )

        return flow_risks

    def _create_empty_risk_assessment(self) -> Dict[str, Any]:
        """Create empty risk assessment for flows with no assets."""
        return {
            "overall_risk_score": 0.0,
            "overall_risk_level": "low",
            "total_assets": 0,
            "risk_distribution": {
                "high": {"count": 0, "percentage": 0.0},
                "medium": {"count": 0, "percentage": 0.0},
                "low": {"count": 0, "percentage": 0.0},
            },
            "asset_risks": [],
            "risk_factors": [],
            "mitigation_strategies": [],
            "recommendations": [
                "Complete asset discovery before proceeding with risk assessment"
            ],
        }
