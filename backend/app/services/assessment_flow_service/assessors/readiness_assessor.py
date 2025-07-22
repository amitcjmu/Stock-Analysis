"""
Readiness assessment module for migration readiness analysis.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset as DiscoveryAsset
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class ReadinessAssessor:
    """Handles migration readiness assessment for assets and flows."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
    
    async def assess_flow_readiness(self, flow: DiscoveryFlow, assets: List[DiscoveryAsset]) -> Dict[str, Any]:
        """
        Assess overall migration readiness for a discovery flow.
        
        Args:
            flow: DiscoveryFlow object
            assets: List of DiscoveryAsset objects
            
        Returns:
            Dict containing comprehensive readiness assessment
        """
        try:
            logger.info(f"🔍 Assessing flow readiness: {flow.flow_id}")
            
            # Assess flow-level readiness
            flow_readiness = self._assess_flow_level_readiness(flow)
            
            # Assess asset-level readiness
            asset_readiness = await self._assess_assets_readiness(assets)
            
            # Calculate overall readiness
            overall_readiness = self._calculate_overall_readiness(flow_readiness, asset_readiness)
            
            # Identify readiness gaps
            readiness_gaps = self._identify_readiness_gaps(flow_readiness, asset_readiness)
            
            # Generate readiness recommendations
            recommendations = self._generate_readiness_recommendations(overall_readiness, readiness_gaps)
            
            readiness_assessment = {
                "flow_id": str(flow.flow_id),
                "is_ready": overall_readiness["is_ready"],
                "readiness_score": overall_readiness["readiness_score"],
                "readiness_level": overall_readiness["readiness_level"],
                "flow_readiness": flow_readiness,
                "asset_readiness": asset_readiness,
                "readiness_gaps": readiness_gaps,
                "recommendations": recommendations,
                "next_steps": self._generate_next_steps(overall_readiness, readiness_gaps)
            }
            
            logger.info(f"✅ Flow readiness assessment completed - Ready: {readiness_assessment['is_ready']}")
            return readiness_assessment
            
        except Exception as e:
            logger.error(f"❌ Error assessing flow readiness: {e}")
            raise
    
    async def assess_asset_migration_readiness(self, asset: DiscoveryAsset) -> Dict[str, Any]:
        """
        Assess migration readiness for a single asset.
        
        Args:
            asset: DiscoveryAsset object
            
        Returns:
            Dict containing asset readiness assessment
        """
        try:
            logger.info(f"🔍 Assessing asset readiness: {asset.asset_name}")
            
            readiness_factors = self._assess_asset_readiness_factors(asset)
            readiness_score = self._calculate_asset_readiness_score(readiness_factors)
            readiness_level = self._determine_readiness_level(readiness_score)
            
            asset_readiness = {
                "asset_id": str(asset.id),
                "asset_name": asset.asset_name,
                "is_ready": readiness_score >= 0.7,
                "readiness_score": round(readiness_score, 2),
                "readiness_level": readiness_level,
                "readiness_factors": readiness_factors,
                "blocking_issues": self._identify_blocking_issues(readiness_factors),
                "recommendations": self._generate_asset_recommendations(readiness_factors)
            }
            
            return asset_readiness
            
        except Exception as e:
            logger.error(f"❌ Error assessing asset readiness: {e}")
            raise
    
    def _assess_flow_level_readiness(self, flow: DiscoveryFlow) -> Dict[str, Any]:
        """Assess readiness at the flow level."""
        
        readiness_checks = {
            "discovery_completion": {
                "passed": flow.status == "completed",
                "score": 1.0 if flow.status == "completed" else 0.0,
                "description": "Discovery flow completion status",
                "weight": 0.25
            },
            "phase_completion": {
                "passed": self._check_phase_completion(flow),
                "score": self._calculate_phase_completion_score(flow),
                "description": "All required discovery phases completed",
                "weight": 0.30
            },
            "data_quality": {
                "passed": (flow.progress_percentage or 0) >= 90,
                "score": min(1.0, (flow.progress_percentage or 0) / 100),
                "description": "Overall data quality and completeness",
                "weight": 0.25
            },
            "validation_status": {
                "passed": flow.assessment_ready or False,
                "score": 1.0 if flow.assessment_ready else 0.0,
                "description": "Flow validation and approval status",
                "weight": 0.20
            }
        }
        
        # Calculate weighted readiness score
        total_score = sum(check["score"] * check["weight"] for check in readiness_checks.values())
        all_passed = all(check["passed"] for check in readiness_checks.values())
        
        return {
            "is_ready": all_passed and total_score >= 0.8,
            "readiness_score": round(total_score, 2),
            "readiness_checks": readiness_checks,
            "critical_issues": [
                name for name, check in readiness_checks.items() 
                if not check["passed"] and check["weight"] >= 0.25
            ]
        }
    
    async def _assess_assets_readiness(self, assets: List[DiscoveryAsset]) -> Dict[str, Any]:
        """Assess readiness across all assets."""
        
        if not assets:
            return self._create_empty_asset_readiness()
        
        asset_assessments = []
        for asset in assets:
            asset_assessment = await self.assess_asset_migration_readiness(asset)
            asset_assessments.append(asset_assessment)
        
        # Calculate summary statistics
        total_assets = len(asset_assessments)
        ready_assets = [a for a in asset_assessments if a["is_ready"]]
        
        # Categorize by readiness level
        high_readiness = [a for a in asset_assessments if a["readiness_level"] == "high"]
        medium_readiness = [a for a in asset_assessments if a["readiness_level"] == "medium"]
        low_readiness = [a for a in asset_assessments if a["readiness_level"] == "low"]
        
        # Calculate average readiness score
        avg_readiness_score = sum(a["readiness_score"] for a in asset_assessments) / total_assets
        
        # Identify common blocking issues
        all_blocking_issues = []
        for assessment in asset_assessments:
            all_blocking_issues.extend(assessment["blocking_issues"])
        
        blocking_issue_counts = {}
        for issue in all_blocking_issues:
            blocking_issue_counts[issue] = blocking_issue_counts.get(issue, 0) + 1
        
        return {
            "total_assets": total_assets,
            "ready_assets": len(ready_assets),
            "readiness_percentage": round(len(ready_assets) / total_assets * 100, 1),
            "average_readiness_score": round(avg_readiness_score, 2),
            "readiness_distribution": {
                "high": {
                    "count": len(high_readiness),
                    "percentage": round(len(high_readiness) / total_assets * 100, 1)
                },
                "medium": {
                    "count": len(medium_readiness),
                    "percentage": round(len(medium_readiness) / total_assets * 100, 1)
                },
                "low": {
                    "count": len(low_readiness),
                    "percentage": round(len(low_readiness) / total_assets * 100, 1)
                }
            },
            "asset_assessments": asset_assessments,
            "common_blocking_issues": [
                {"issue": issue, "count": count, "percentage": round(count / total_assets * 100, 1)}
                for issue, count in sorted(blocking_issue_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        }
    
    def _assess_asset_readiness_factors(self, asset: DiscoveryAsset) -> Dict[str, Any]:
        """Assess various readiness factors for an asset."""
        
        factors = {
            "data_completeness": {
                "score": self._assess_data_completeness(asset),
                "weight": 0.25,
                "description": "Completeness of asset data and metadata"
            },
            "validation_status": {
                "score": self._assess_validation_readiness(asset),
                "weight": 0.20,
                "description": "Asset validation and approval status"
            },
            "confidence_level": {
                "score": self._assess_confidence_readiness(asset),
                "weight": 0.20,
                "description": "Confidence in asset discovery accuracy"
            },
            "migration_classification": {
                "score": self._assess_migration_classification(asset),
                "weight": 0.15,
                "description": "Asset migration complexity classification"
            },
            "dependency_mapping": {
                "score": self._assess_dependency_readiness(asset),
                "weight": 0.10,
                "description": "Asset dependency identification and mapping"
            },
            "compliance_readiness": {
                "score": self._assess_compliance_readiness(asset),
                "weight": 0.10,
                "description": "Compliance and security requirement assessment"
            }
        }
        
        return factors
    
    def _assess_data_completeness(self, asset: DiscoveryAsset) -> float:
        """Assess data completeness for an asset."""
        
        score = 0.0
        
        # Required fields
        if asset.asset_name and asset.asset_name.strip():
            score += 0.3
        if asset.asset_type and asset.asset_type.strip():
            score += 0.3
        
        # Additional data
        if asset.asset_subtype:
            score += 0.1
        if asset.normalized_data and len(asset.normalized_data) > 0:
            score += 0.2
        if asset.raw_data and len(asset.raw_data) > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_validation_readiness(self, asset: DiscoveryAsset) -> float:
        """Assess validation readiness for an asset."""
        
        validation_scores = {
            "approved": 1.0,
            "pending": 0.3,
            "needs_review": 0.2,
            "rejected": 0.0,
            "unknown": 0.1
        }
        
        validation_status = asset.validation_status or "unknown"
        return validation_scores.get(validation_status.lower(), 0.1)
    
    def _assess_confidence_readiness(self, asset: DiscoveryAsset) -> float:
        """Assess confidence readiness for an asset."""
        
        confidence_score = asset.confidence_score or 0.0
        
        # Linear mapping of confidence to readiness
        if confidence_score >= 0.9:
            return 1.0
        elif confidence_score >= 0.8:
            return 0.8
        elif confidence_score >= 0.7:
            return 0.6
        elif confidence_score >= 0.6:
            return 0.4
        else:
            return 0.2
    
    def _assess_migration_classification(self, asset: DiscoveryAsset) -> float:
        """Assess migration classification readiness."""
        
        score = 0.0
        
        # Migration complexity classification
        if asset.migration_complexity:
            score += 0.4
        
        # Migration priority
        if asset.migration_priority and asset.migration_priority > 0:
            score += 0.3
        
        # Migration readiness flag
        if asset.migration_ready:
            score += 0.3
        
        return min(1.0, score)
    
    def _assess_dependency_readiness(self, asset: DiscoveryAsset) -> float:
        """Assess dependency mapping readiness."""
        
        score = 0.5  # Base score for assets without complex dependencies
        
        # Check for dependency information in normalized data
        normalized_data = asset.normalized_data or {}
        
        if "dependencies" in normalized_data:
            dependencies = normalized_data["dependencies"]
            if isinstance(dependencies, list) and len(dependencies) > 0:
                score = 0.8  # Has dependency information
            elif isinstance(dependencies, list) and len(dependencies) == 0:
                score = 1.0  # No dependencies (ready)
        
        # Check for dependency mapping completeness
        if "dependency_mapping_complete" in normalized_data:
            if normalized_data["dependency_mapping_complete"]:
                score = 1.0
            else:
                score = max(score, 0.3)
        
        return score
    
    def _assess_compliance_readiness(self, asset: DiscoveryAsset) -> float:
        """Assess compliance and security readiness."""
        
        score = 0.7  # Default score for assets without special compliance needs
        
        normalized_data = asset.normalized_data or {}
        
        # Check for compliance requirements
        if "compliance_requirements" in normalized_data:
            requirements = normalized_data["compliance_requirements"]
            if isinstance(requirements, list):
                if len(requirements) == 0:
                    score = 1.0  # No special compliance needs
                else:
                    # Has compliance requirements - check if assessed
                    if "compliance_assessment_complete" in normalized_data:
                        score = 1.0 if normalized_data["compliance_assessment_complete"] else 0.3
                    else:
                        score = 0.4  # Requirements identified but not assessed
        
        # Check for security classification
        if "security_classification" in normalized_data:
            if normalized_data["security_classification"]:
                score = max(score, 0.8)
        
        return score
    
    def _calculate_asset_readiness_score(self, readiness_factors: Dict[str, Any]) -> float:
        """Calculate weighted readiness score for an asset."""
        
        total_score = sum(
            factor["score"] * factor["weight"] 
            for factor in readiness_factors.values()
        )
        
        return total_score
    
    def _determine_readiness_level(self, readiness_score: float) -> str:
        """Determine categorical readiness level from numeric score."""
        if readiness_score >= 0.8:
            return "high"
        elif readiness_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _identify_blocking_issues(self, readiness_factors: Dict[str, Any]) -> List[str]:
        """Identify blocking issues preventing migration readiness."""
        
        blocking_issues = []
        
        for factor_name, factor_data in readiness_factors.items():
            if factor_data["score"] < 0.5 and factor_data["weight"] >= 0.15:
                # Critical factor with low score
                if factor_name == "data_completeness":
                    blocking_issues.append("Incomplete asset data and metadata")
                elif factor_name == "validation_status":
                    blocking_issues.append("Asset validation pending or failed")
                elif factor_name == "confidence_level":
                    blocking_issues.append("Low confidence in asset discovery accuracy")
                elif factor_name == "migration_classification":
                    blocking_issues.append("Asset migration classification incomplete")
        
        return blocking_issues
    
    def _generate_asset_recommendations(self, readiness_factors: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving asset readiness."""
        
        recommendations = []
        
        for factor_name, factor_data in readiness_factors.items():
            if factor_data["score"] < 0.7:
                if factor_name == "data_completeness":
                    recommendations.append("Complete missing asset data and metadata")
                elif factor_name == "validation_status":
                    recommendations.append("Complete asset validation and approval process")
                elif factor_name == "confidence_level":
                    recommendations.append("Perform additional discovery to improve confidence")
                elif factor_name == "migration_classification":
                    recommendations.append("Complete migration complexity and priority assessment")
                elif factor_name == "dependency_mapping":
                    recommendations.append("Complete dependency mapping and analysis")
                elif factor_name == "compliance_readiness":
                    recommendations.append("Complete compliance and security assessment")
        
        return recommendations
    
    def _check_phase_completion(self, flow: DiscoveryFlow) -> bool:
        """Check if all required phases are completed."""
        
        required_phases = [
            "data_import_completed",
            "attribute_mapping_completed",
            "data_cleansing_completed",
            "inventory_completed"
        ]
        
        completed_phases = []
        for phase in required_phases:
            if getattr(flow, phase, False):
                completed_phases.append(phase)
        
        return len(completed_phases) == len(required_phases)
    
    def _calculate_phase_completion_score(self, flow: DiscoveryFlow) -> float:
        """Calculate phase completion score."""
        
        required_phases = [
            "data_import_completed",
            "attribute_mapping_completed", 
            "data_cleansing_completed",
            "inventory_completed"
        ]
        
        completed_count = sum(1 for phase in required_phases if getattr(flow, phase, False))
        return completed_count / len(required_phases)
    
    def _calculate_overall_readiness(self, flow_readiness: Dict[str, Any], asset_readiness: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall readiness combining flow and asset readiness."""
        
        # Weight flow vs asset readiness
        flow_weight = 0.4
        asset_weight = 0.6
        
        overall_score = (
            flow_readiness["readiness_score"] * flow_weight +
            asset_readiness["average_readiness_score"] * asset_weight
        )
        
        # Overall readiness requires both flow and asset readiness
        is_ready = (
            flow_readiness["is_ready"] and 
            asset_readiness["readiness_percentage"] >= 80 and
            overall_score >= 0.75
        )
        
        readiness_level = self._determine_readiness_level(overall_score)
        
        return {
            "is_ready": is_ready,
            "readiness_score": round(overall_score, 2),
            "readiness_level": readiness_level
        }
    
    def _identify_readiness_gaps(self, flow_readiness: Dict[str, Any], asset_readiness: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify gaps preventing overall readiness."""
        
        gaps = []
        
        # Flow-level gaps
        for issue in flow_readiness.get("critical_issues", []):
            gaps.append({
                "type": "flow",
                "category": issue,
                "description": f"Flow-level issue: {issue}",
                "severity": "high",
                "affected_count": 1
            })
        
        # Asset-level gaps
        for issue_data in asset_readiness.get("common_blocking_issues", []):
            if issue_data["percentage"] > 20:  # Issues affecting >20% of assets
                gaps.append({
                    "type": "asset",
                    "category": issue_data["issue"],
                    "description": f"Asset issue affecting {issue_data['count']} assets",
                    "severity": "high" if issue_data["percentage"] > 40 else "medium",
                    "affected_count": issue_data["count"]
                })
        
        # Overall readiness gaps
        if asset_readiness["readiness_percentage"] < 80:
            gaps.append({
                "type": "overall",
                "category": "asset_readiness_threshold",
                "description": f"Only {asset_readiness['readiness_percentage']}% of assets are ready (minimum 80% required)",
                "severity": "high",
                "affected_count": asset_readiness["total_assets"] - asset_readiness["ready_assets"]
            })
        
        return gaps
    
    def _generate_readiness_recommendations(self, overall_readiness: Dict[str, Any], readiness_gaps: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for achieving readiness."""
        
        recommendations = []
        
        if overall_readiness["is_ready"]:
            recommendations.append("Flow is ready for migration assessment phase")
            return recommendations
        
        # Recommendations based on gaps
        for gap in readiness_gaps:
            if gap["type"] == "flow":
                if gap["category"] == "discovery_completion":
                    recommendations.append("Complete discovery flow execution")
                elif gap["category"] == "phase_completion":
                    recommendations.append("Complete all required discovery phases")
                elif gap["category"] == "validation_status":
                    recommendations.append("Complete flow validation and approval")
            elif gap["type"] == "asset":
                if "validation" in gap["category"].lower():
                    recommendations.append("Resolve asset validation issues")
                elif "completeness" in gap["category"].lower():
                    recommendations.append("Complete missing asset data")
                elif "confidence" in gap["category"].lower():
                    recommendations.append("Improve asset discovery confidence through additional validation")
        
        # Overall readiness recommendations
        if overall_readiness["readiness_score"] < 0.6:
            recommendations.append("Conduct comprehensive readiness review before proceeding")
        elif overall_readiness["readiness_score"] < 0.75:
            recommendations.append("Address critical readiness gaps before migration assessment")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_next_steps(self, overall_readiness: Dict[str, Any], readiness_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable next steps based on readiness assessment."""
        
        next_steps = []
        
        if overall_readiness["is_ready"]:
            next_steps.append({
                "action": "Proceed to Assessment Phase",
                "description": "Generate assessment package and transition to migration assessment",
                "priority": "high",
                "estimated_effort": "1-2 days"
            })
            return next_steps
        
        # Prioritize steps based on gaps
        high_priority_gaps = [g for g in readiness_gaps if g["severity"] == "high"]
        medium_priority_gaps = [g for g in readiness_gaps if g["severity"] == "medium"]
        
        for gap in high_priority_gaps:
            if gap["type"] == "flow":
                next_steps.append({
                    "action": f"Resolve Flow Issue: {gap['category']}",
                    "description": gap["description"],
                    "priority": "high",
                    "estimated_effort": "2-5 days"
                })
            elif gap["type"] == "asset":
                next_steps.append({
                    "action": f"Address Asset Issues: {gap['category']}",
                    "description": f"Resolve {gap['category']} for {gap['affected_count']} assets",
                    "priority": "high",
                    "estimated_effort": "1-3 weeks"
                })
        
        for gap in medium_priority_gaps:
            next_steps.append({
                "action": f"Improve: {gap['category']}",
                "description": gap["description"],
                "priority": "medium",
                "estimated_effort": "3-7 days"
            })
        
        if not next_steps:
            next_steps.append({
                "action": "Comprehensive Readiness Review",
                "description": "Conduct detailed review of all readiness factors",
                "priority": "medium",
                "estimated_effort": "1 week"
            })
        
        return next_steps
    
    def _create_empty_asset_readiness(self) -> Dict[str, Any]:
        """Create empty asset readiness assessment."""
        return {
            "total_assets": 0,
            "ready_assets": 0,
            "readiness_percentage": 0.0,
            "average_readiness_score": 0.0,
            "readiness_distribution": {
                "high": {"count": 0, "percentage": 0.0},
                "medium": {"count": 0, "percentage": 0.0},
                "low": {"count": 0, "percentage": 0.0}
            },
            "asset_assessments": [],
            "common_blocking_issues": []
        }