"""
Data Flow Validator for ADCS End-to-End Integration

This service validates data flow integrity across Collection → Discovery → Assessment phases,
ensuring data consistency, completeness, and quality throughout the workflow.

Generated with CC for ADCS end-to-end integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import UUID
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.monitoring.metrics import track_performance
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.models.assessment_flow import AssessmentFlow
from app.models.collection_flow import CollectionFlow
from app.models.dependency import Dependency

logger = get_logger(__name__)

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class ValidationCategory(Enum):
    """Categories of validation checks"""
    DATA_INTEGRITY = "data_integrity"
    DATA_COMPLETENESS = "data_completeness"
    DATA_CONSISTENCY = "data_consistency"
    CROSS_PHASE_ALIGNMENT = "cross_phase_alignment"
    BUSINESS_LOGIC = "business_logic"

@dataclass
class ValidationIssue:
    """Represents a validation issue found during data flow validation"""
    id: str
    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    description: str
    affected_assets: List[UUID]
    metadata: Dict[str, Any]
    remediation_suggestions: List[str]
    created_at: datetime

@dataclass
class ValidationResult:
    """Result of data flow validation"""
    engagement_id: UUID
    validation_id: str
    overall_score: float
    issues: List[ValidationIssue]
    phase_scores: Dict[str, float]
    summary: Dict[str, Any]
    recommendations: List[str]
    validated_at: datetime

class DataFlowValidator:
    """
    Validates data flow integrity across the complete ADCS workflow
    """
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for different phases and transitions"""
        return {
            "collection_validation": {
                "required_fields": [
                    "name", "type", "environment", "business_criticality"
                ],
                "optional_fields": [
                    "technical_fit_score", "complexity_score", "risk_score"
                ],
                "min_confidence_threshold": 0.6
            },
            "discovery_validation": {
                "required_enrichments": [
                    "dependencies", "technical_details", "business_context"
                ],
                "min_dependency_coverage": 0.7,
                "min_confidence_improvement": 0.1
            },
            "assessment_validation": {
                "required_analyses": [
                    "sixr_recommendation", "migration_complexity", "business_value"
                ],
                "min_assessment_coverage": 0.8,
                "consistency_checks": True
            },
            "cross_phase_validation": {
                "asset_count_consistency": True,
                "dependency_integrity": True,
                "confidence_progression": True
            }
        }
        
    @track_performance("validation.data_flow.full")
    async def validate_end_to_end_data_flow(
        self,
        engagement_id: UUID,
        validation_scope: Optional[Set[str]] = None
    ) -> ValidationResult:
        """
        Perform comprehensive end-to-end data flow validation
        """
        
        logger.info(
            "Starting end-to-end data flow validation",
            extra={
                "engagement_id": str(engagement_id),
                "validation_scope": list(validation_scope) if validation_scope else "all"
            }
        )
        
        validation_id = f"validation_{engagement_id}_{int(datetime.utcnow().timestamp())}"
        issues: List[ValidationIssue] = []
        phase_scores: Dict[str, float] = {}
        
        try:
            async with AsyncSessionLocal() as session:
                # Get all flows and assets
                flows_data = await self._get_flows_data(session, engagement_id)
                assets = await self._get_assets_with_dependencies(session, engagement_id)
                
                # Phase-specific validations
                if not validation_scope or "collection" in validation_scope:
                    collection_issues, collection_score = await self._validate_collection_phase(
                        session, flows_data, assets
                    )
                    issues.extend(collection_issues)
                    phase_scores["collection"] = collection_score
                    
                if not validation_scope or "discovery" in validation_scope:
                    discovery_issues, discovery_score = await self._validate_discovery_phase(
                        session, flows_data, assets
                    )
                    issues.extend(discovery_issues)
                    phase_scores["discovery"] = discovery_score
                    
                if not validation_scope or "assessment" in validation_scope:
                    assessment_issues, assessment_score = await self._validate_assessment_phase(
                        session, flows_data, assets
                    )
                    issues.extend(assessment_issues)
                    phase_scores["assessment"] = assessment_score
                    
                # Cross-phase validations
                if not validation_scope or "cross_phase" in validation_scope:
                    cross_phase_issues, cross_phase_score = await self._validate_cross_phase_consistency(
                        session, flows_data, assets
                    )
                    issues.extend(cross_phase_issues)
                    phase_scores["cross_phase"] = cross_phase_score
                    
                # Calculate overall score
                overall_score = sum(phase_scores.values()) / len(phase_scores) if phase_scores else 0.0
                
                # Generate summary and recommendations
                summary = self._generate_validation_summary(issues, phase_scores, assets)
                recommendations = self._generate_recommendations(issues, phase_scores)
                
                result = ValidationResult(
                    engagement_id=engagement_id,
                    validation_id=validation_id,
                    overall_score=overall_score,
                    issues=issues,
                    phase_scores=phase_scores,
                    summary=summary,
                    recommendations=recommendations,
                    validated_at=datetime.utcnow()
                )
                
                logger.info(
                    "End-to-end data flow validation completed",
                    extra={
                        "engagement_id": str(engagement_id),
                        "validation_id": validation_id,
                        "overall_score": overall_score,
                        "issues_count": len(issues),
                        "critical_issues": len([i for i in issues if i.severity == ValidationSeverity.CRITICAL])
                    }
                )
                
                return result
                
        except Exception as e:
            logger.error(
                "Error during data flow validation",
                extra={
                    "engagement_id": str(engagement_id),
                    "validation_id": validation_id,
                    "error": str(e)
                }
            )
            raise
            
    async def _get_flows_data(self, session: AsyncSession, engagement_id: UUID) -> Dict[str, Any]:
        """Get all flow data for the engagement"""
        
        # Get collection flow
        collection_result = await session.execute(
            select(CollectionFlow).where(CollectionFlow.engagement_id == engagement_id)
        )
        collection_flow = collection_result.scalar_one_or_none()
        
        # Get discovery flow
        discovery_result = await session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.engagement_id == engagement_id)
        )
        discovery_flow = discovery_result.scalar_one_or_none()
        
        # Get assessment flow
        assessment_result = await session.execute(
            select(AssessmentFlow).where(AssessmentFlow.engagement_id == engagement_id)
        )
        assessment_flow = assessment_result.scalar_one_or_none()
        
        return {
            "collection_flow": collection_flow,
            "discovery_flow": discovery_flow,
            "assessment_flow": assessment_flow
        }
        
    async def _get_assets_with_dependencies(self, session: AsyncSession, engagement_id: UUID) -> List[Asset]:
        """Get all assets with their dependencies for the engagement"""
        
        result = await session.execute(
            select(Asset)
            .where(Asset.engagement_id == engagement_id)
            .options(selectinload(Asset.dependencies))
        )
        return result.scalars().all()
        
    async def _validate_collection_phase(
        self,
        session: AsyncSession,
        flows_data: Dict[str, Any],
        assets: List[Asset]
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate collection phase data integrity"""
        
        issues: List[ValidationIssue] = []
        collection_flow = flows_data.get("collection_flow")
        
        if not collection_flow:
            issues.append(ValidationIssue(
                id="collection_flow_missing",
                category=ValidationCategory.DATA_INTEGRITY,
                severity=ValidationSeverity.CRITICAL,
                title="Collection Flow Missing",
                description="No collection flow found for this engagement",
                affected_assets=[],
                metadata={},
                remediation_suggestions=["Initiate collection flow for this engagement"],
                created_at=datetime.utcnow()
            ))
            return issues, 0.0
            
        # Validate required fields
        required_fields = self.validation_rules["collection_validation"]["required_fields"]
        field_completion_scores = []
        
        for asset in assets:
            missing_fields = []
            for field in required_fields:
                if not getattr(asset, field, None):
                    missing_fields.append(field)
                    
            if missing_fields:
                issues.append(ValidationIssue(
                    id=f"asset_missing_fields_{asset.id}",
                    category=ValidationCategory.DATA_COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    title=f"Missing Required Fields for Asset {asset.name}",
                    description=f"Asset is missing required fields: {', '.join(missing_fields)}",
                    affected_assets=[asset.id],
                    metadata={"missing_fields": missing_fields},
                    remediation_suggestions=[f"Provide values for: {', '.join(missing_fields)}"],
                    created_at=datetime.utcnow()
                ))
                
            completion_score = 1.0 - (len(missing_fields) / len(required_fields))
            field_completion_scores.append(completion_score)
            
        # Validate confidence scores
        min_confidence = self.validation_rules["collection_validation"]["min_confidence_threshold"]
        low_confidence_assets = []
        
        for asset in assets:
            if asset.confidence_score and asset.confidence_score < min_confidence:
                low_confidence_assets.append(asset)
                
        if low_confidence_assets:
            issues.append(ValidationIssue(
                id="low_confidence_assets",
                category=ValidationCategory.DATA_COMPLETENESS,
                severity=ValidationSeverity.WARNING,
                title="Assets with Low Confidence Scores",
                description=f"{len(low_confidence_assets)} assets have confidence scores below {min_confidence}",
                affected_assets=[asset.id for asset in low_confidence_assets],
                metadata={"min_threshold": min_confidence, "affected_count": len(low_confidence_assets)},
                remediation_suggestions=["Review and enhance data collection for low-confidence assets"],
                created_at=datetime.utcnow()
            ))
            
        # Calculate collection phase score
        avg_completion = sum(field_completion_scores) / len(field_completion_scores) if field_completion_scores else 0.0
        confidence_penalty = len(low_confidence_assets) / len(assets) if assets else 0.0
        collection_score = max(0.0, avg_completion - (confidence_penalty * 0.2))
        
        return issues, collection_score
        
    async def _validate_discovery_phase(
        self,
        session: AsyncSession,
        flows_data: Dict[str, Any],
        assets: List[Asset]
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate discovery phase data enrichment"""
        
        issues: List[ValidationIssue] = []
        discovery_flow = flows_data.get("discovery_flow")
        
        if not discovery_flow:
            # Discovery not required if collection is incomplete
            return issues, 1.0
            
        # Validate dependency coverage
        min_dependency_coverage = self.validation_rules["discovery_validation"]["min_dependency_coverage"]
        assets_with_dependencies = [asset for asset in assets if asset.dependencies]
        dependency_coverage = len(assets_with_dependencies) / len(assets) if assets else 0.0
        
        if dependency_coverage < min_dependency_coverage:
            issues.append(ValidationIssue(
                id="low_dependency_coverage",
                category=ValidationCategory.DATA_COMPLETENESS,
                severity=ValidationSeverity.WARNING,
                title="Low Dependency Discovery Coverage",
                description=f"Only {dependency_coverage:.1%} of assets have discovered dependencies (target: {min_dependency_coverage:.1%})",
                affected_assets=[asset.id for asset in assets if not asset.dependencies],
                metadata={"current_coverage": dependency_coverage, "target_coverage": min_dependency_coverage},
                remediation_suggestions=["Run dependency discovery analysis", "Review network topology"],
                created_at=datetime.utcnow()
            ))
            
        # Validate technical details enrichment
        assets_missing_details = []
        for asset in assets:
            if not asset.technical_details or not asset.technical_details.get("discovery_enriched"):
                assets_missing_details.append(asset)
                
        if assets_missing_details:
            issues.append(ValidationIssue(
                id="missing_discovery_enrichment",
                category=ValidationCategory.DATA_COMPLETENESS,
                severity=ValidationSeverity.INFO,
                title="Assets Missing Discovery Enrichment",
                description=f"{len(assets_missing_details)} assets lack discovery-phase enrichment",
                affected_assets=[asset.id for asset in assets_missing_details],
                metadata={"missing_count": len(assets_missing_details)},
                remediation_suggestions=["Run discovery enrichment analysis"],
                created_at=datetime.utcnow()
            ))
            
        # Calculate discovery score
        discovery_score = dependency_coverage * 0.7 + (1.0 - len(assets_missing_details) / len(assets)) * 0.3
        
        return issues, discovery_score
        
    async def _validate_assessment_phase(
        self,
        session: AsyncSession,
        flows_data: Dict[str, Any],
        assets: List[Asset]
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate assessment phase completeness"""
        
        issues: List[ValidationIssue] = []
        assessment_flow = flows_data.get("assessment_flow")
        
        if not assessment_flow:
            # Assessment not required if discovery is incomplete
            return issues, 1.0
            
        # Validate 6R recommendations
        assets_without_sixr = []
        for asset in assets:
            if not asset.sixr_recommendation:
                assets_without_sixr.append(asset)
                
        if assets_without_sixr:
            issues.append(ValidationIssue(
                id="missing_sixr_recommendations",
                category=ValidationCategory.DATA_COMPLETENESS,
                severity=ValidationSeverity.CRITICAL,
                title="Assets Missing 6R Recommendations",
                description=f"{len(assets_without_sixr)} assets lack 6R strategy recommendations",
                affected_assets=[asset.id for asset in assets_without_sixr],
                metadata={"missing_count": len(assets_without_sixr)},
                remediation_suggestions=["Run 6R analysis for all assets"],
                created_at=datetime.utcnow()
            ))
            
        # Validate business value calculations
        assets_without_value = []
        for asset in assets:
            if not asset.business_value_score:
                assets_without_value.append(asset)
                
        if assets_without_value:
            issues.append(ValidationIssue(
                id="missing_business_value",
                category=ValidationCategory.DATA_COMPLETENESS,
                severity=ValidationSeverity.WARNING,
                title="Assets Missing Business Value Assessment",
                description=f"{len(assets_without_value)} assets lack business value scores",
                affected_assets=[asset.id for asset in assets_without_value],
                metadata={"missing_count": len(assets_without_value)},
                remediation_suggestions=["Calculate business value for all assets"],
                created_at=datetime.utcnow()
            ))
            
        # Calculate assessment score
        sixr_coverage = 1.0 - (len(assets_without_sixr) / len(assets)) if assets else 1.0
        value_coverage = 1.0 - (len(assets_without_value) / len(assets)) if assets else 1.0
        assessment_score = sixr_coverage * 0.7 + value_coverage * 0.3
        
        return issues, assessment_score
        
    async def _validate_cross_phase_consistency(
        self,
        session: AsyncSession,
        flows_data: Dict[str, Any],
        assets: List[Asset]
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate consistency across workflow phases"""
        
        issues: List[ValidationIssue] = []
        consistency_scores = []
        
        # Validate asset count consistency
        if flows_data.get("collection_flow") and flows_data.get("discovery_flow"):
            # Asset counts should be consistent between phases
            collection_metadata = flows_data["collection_flow"].metadata or {}
            discovery_metadata = flows_data["discovery_flow"].metadata or {}
            
            collection_count = collection_metadata.get("asset_count", len(assets))
            discovery_count = discovery_metadata.get("asset_count", len(assets))
            
            if abs(collection_count - discovery_count) > 2:  # Allow small variance
                issues.append(ValidationIssue(
                    id="asset_count_inconsistency",
                    category=ValidationCategory.CROSS_PHASE_ALIGNMENT,
                    severity=ValidationSeverity.WARNING,
                    title="Asset Count Inconsistency",
                    description=f"Asset count differs between collection ({collection_count}) and discovery ({discovery_count})",
                    affected_assets=[],
                    metadata={"collection_count": collection_count, "discovery_count": discovery_count},
                    remediation_suggestions=["Verify asset creation and deletion logs", "Resync asset counts"],
                    created_at=datetime.utcnow()
                ))
                consistency_scores.append(0.7)
            else:
                consistency_scores.append(1.0)
                
        # Validate confidence progression
        if assets:
            confidence_issues = 0
            for asset in assets:
                if asset.confidence_score:
                    # Confidence should generally increase through phases
                    initial_confidence = asset.metadata.get("initial_confidence", asset.confidence_score)
                    if asset.confidence_score < initial_confidence:
                        confidence_issues += 1
                        
            if confidence_issues > len(assets) * 0.2:  # More than 20% of assets
                issues.append(ValidationIssue(
                    id="confidence_regression",
                    category=ValidationCategory.CROSS_PHASE_ALIGNMENT,
                    severity=ValidationSeverity.WARNING,
                    title="Confidence Score Regression",
                    description=f"{confidence_issues} assets show decreased confidence through workflow phases",
                    affected_assets=[],
                    metadata={"affected_count": confidence_issues},
                    remediation_suggestions=["Review confidence calculation algorithms", "Investigate data quality issues"],
                    created_at=datetime.utcnow()
                ))
                consistency_scores.append(0.6)
            else:
                consistency_scores.append(1.0)
                
        # Calculate cross-phase score
        cross_phase_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0
        
        return issues, cross_phase_score
        
    def _generate_validation_summary(
        self,
        issues: List[ValidationIssue],
        phase_scores: Dict[str, float],
        assets: List[Asset]
    ) -> Dict[str, Any]:
        """Generate validation summary"""
        
        critical_count = len([i for i in issues if i.severity == ValidationSeverity.CRITICAL])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        info_count = len([i for i in issues if i.severity == ValidationSeverity.INFO])
        
        return {
            "total_assets": len(assets),
            "total_issues": len(issues),
            "issues_by_severity": {
                "critical": critical_count,
                "warning": warning_count,
                "info": info_count
            },
            "phase_scores": phase_scores,
            "validation_status": "PASSED" if critical_count == 0 else "FAILED",
            "workflow_health": "EXCELLENT" if sum(phase_scores.values()) / len(phase_scores) > 0.9
                              else "GOOD" if sum(phase_scores.values()) / len(phase_scores) > 0.7
                              else "NEEDS_ATTENTION"
        }
        
    def _generate_recommendations(
        self,
        issues: List[ValidationIssue],
        phase_scores: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Critical issues
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            recommendations.append("🚨 Address critical issues immediately before proceeding")
            for issue in critical_issues[:3]:  # Top 3 critical issues
                recommendations.extend(issue.remediation_suggestions)
                
        # Phase-specific recommendations
        if phase_scores.get("collection", 1.0) < 0.7:
            recommendations.append("📊 Improve collection data quality before proceeding to discovery")
            
        if phase_scores.get("discovery", 1.0) < 0.7:
            recommendations.append("🔍 Complete discovery analysis before proceeding to assessment")
            
        if phase_scores.get("assessment", 1.0) < 0.7:
            recommendations.append("⚖️ Complete assessment analysis for all assets")
            
        # General recommendations
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        if warning_count > 5:
            recommendations.append("⚠️ Review and address warning-level issues to improve workflow quality")
            
        return recommendations[:10]  # Limit to top 10 recommendations
        
    @track_performance("validation.issues.remediate")
    async def remediate_validation_issues(
        self,
        engagement_id: UUID,
        issue_ids: List[str],
        remediation_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Attempt automatic remediation of validation issues"""
        
        logger.info(
            "Starting validation issue remediation",
            extra={
                "engagement_id": str(engagement_id),
                "issue_ids": issue_ids,
                "config": remediation_config
            }
        )
        
        # This would implement automatic remediation logic
        # For now, return a placeholder response
        return {
            "engagement_id": str(engagement_id),
            "remediated_issues": [],
            "failed_remediations": issue_ids,
            "recommendations": ["Manual intervention required for these issues"]
        }