"""
Confidence Scoring Algorithms - B2.3
ADCS AI Analysis & Intelligence Service

This service implements sophisticated confidence scoring algorithms that assess
the reliability and completeness of collected data for 6R migration recommendations.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfidenceFactorType(str, Enum):
    """Types of factors that influence confidence scoring"""

    DATA_COMPLETENESS = "data_completeness"
    DATA_QUALITY = "data_quality"
    SOURCE_RELIABILITY = "source_reliability"
    VALIDATION_STATUS = "validation_status"
    BUSINESS_CONTEXT = "business_context"
    TEMPORAL_FRESHNESS = "temporal_freshness"
    CROSS_VALIDATION = "cross_validation"
    EXPERT_VALIDATION = "expert_validation"


class SixRStrategy(str, Enum):
    """5R cloud migration strategy framework"""

    # Migration Lift and Shift
    REHOST = "rehost"
    
    # Legacy Modernization Treatments
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    REARCHITECT = "rearchitect"
    
    # Cloud Native
    REPLACE = "replace"
    REWRITE = "rewrite"


@dataclass
class ConfidenceFactor:
    """Individual factor contributing to overall confidence score"""

    factor_type: ConfidenceFactorType
    weight: float  # 0.0 to 1.0
    score: float  # 0.0 to 100.0
    evidence: Dict[str, Any]
    description: str


@dataclass
class ConfidenceAssessment:
    """Complete confidence assessment for an asset or collection"""

    overall_score: float  # 0.0 to 100.0
    strategy_scores: Dict[SixRStrategy, float]
    contributing_factors: List[ConfidenceFactor]
    critical_gaps: List[str]
    recommendations: List[str]
    last_updated: datetime
    assessment_metadata: Dict[str, Any]


class ConfidenceScorer:
    """
    Advanced confidence scoring system for ADCS data collection and 6R recommendations.

    Uses multiple algorithms and weighting factors to provide accurate confidence
    assessments that improve over time through learning and validation.
    """

    def __init__(self):
        """Initialize confidence scorer with default weights and parameters"""
        self.factor_weights = self._initialize_factor_weights()
        self.strategy_requirements = self._initialize_strategy_requirements()
        self.quality_thresholds = self._initialize_quality_thresholds()

    def _initialize_factor_weights(self) -> Dict[ConfidenceFactorType, float]:
        """Initialize default weights for confidence factors"""
        return {
            ConfidenceFactorType.DATA_COMPLETENESS: 0.25,  # 25% - How complete is the data
            ConfidenceFactorType.DATA_QUALITY: 0.20,  # 20% - Quality of the data
            ConfidenceFactorType.SOURCE_RELIABILITY: 0.15,  # 15% - How reliable is the source
            ConfidenceFactorType.VALIDATION_STATUS: 0.15,  # 15% - Has data been validated
            ConfidenceFactorType.BUSINESS_CONTEXT: 0.10,  # 10% - Business context completeness
            ConfidenceFactorType.TEMPORAL_FRESHNESS: 0.08,  # 8% - How recent is the data
            ConfidenceFactorType.CROSS_VALIDATION: 0.04,  # 4% - Cross-validation with other sources
            ConfidenceFactorType.EXPERT_VALIDATION: 0.03,  # 3% - Expert review and validation
        }

    def _initialize_strategy_requirements(self) -> Dict[SixRStrategy, Dict[str, Any]]:
        """Initialize data requirements for each 6R strategy"""
        return {
            SixRStrategy.REHOST: {
                "critical_attributes": [
                    "hostname",
                    "os_type",
                    "os_version",
                    "cpu_cores",
                    "memory_gb",
                    "storage_gb",
                    "network_zone",
                    "environment",
                    "dependencies",
                ],
                "importance_weights": {
                    "infrastructure": 0.6,
                    "operational": 0.25,
                    "application": 0.1,
                    "dependencies": 0.05,
                },
                "minimum_confidence_threshold": 75.0,
            },
            SixRStrategy.REPLATFORM: {
                "critical_attributes": [
                    "application_type",
                    "technology_stack",
                    "os_type",
                    "database_type",
                    "integration_points",
                    "data_flows",
                    "performance_requirements",
                ],
                "importance_weights": {
                    "application": 0.4,
                    "infrastructure": 0.3,
                    "dependencies": 0.2,
                    "operational": 0.1,
                },
                "minimum_confidence_threshold": 80.0,
            },
            SixRStrategy.REFACTOR: {
                "critical_attributes": [
                    "application_name",
                    "technology_stack",
                    "code_complexity",
                    "application_dependencies",
                    "data_classification",
                    "integration_points",
                    "business_logic_complexity",
                    "technical_debt_score",
                ],
                "importance_weights": {
                    "application": 0.5,
                    "dependencies": 0.3,
                    "infrastructure": 0.1,
                    "operational": 0.1,
                },
                "minimum_confidence_threshold": 85.0,
            },
            SixRStrategy.REARCHITECT: {
                "critical_attributes": [
                    "application_name",
                    "technology_stack",
                    "architecture_complexity",
                    "microservices_suitability",
                    "cloud_native_requirements",
                    "integration_points",
                    "data_flows",
                    "scalability_requirements",
                ],
                "importance_weights": {
                    "application": 0.5,
                    "dependencies": 0.3,
                    "infrastructure": 0.1,
                    "operational": 0.1,
                },
                "minimum_confidence_threshold": 85.0,
            },
            SixRStrategy.REPLACE: {
                "critical_attributes": [
                    "business_function",
                    "user_count",
                    "business_criticality",
                    "compliance_scope",
                    "cost_center",
                    "vendor_relationship",
                    "licensing_model",
                    "integration_complexity",
                ],
                "importance_weights": {
                    "application": 0.3,
                    "operational": 0.4,
                    "dependencies": 0.2,
                    "infrastructure": 0.1,
                },
                "minimum_confidence_threshold": 70.0,
            },
            SixRStrategy.REWRITE: {
                "critical_attributes": [
                    "application_name",
                    "business_logic_complexity",
                    "technology_stack",
                    "cloud_native_requirements",
                    "development_resources",
                    "time_to_market",
                    "legacy_constraints",
                    "modernization_goals",
                ],
                "importance_weights": {
                    "application": 0.6,
                    "operational": 0.2,
                    "dependencies": 0.1,
                    "infrastructure": 0.1,
                },
                "minimum_confidence_threshold": 80.0,
            },
        }

    def _initialize_quality_thresholds(self) -> Dict[str, float]:
        """Initialize quality assessment thresholds"""
        return {
            "excellent": 90.0,
            "good": 75.0,
            "acceptable": 60.0,
            "poor": 40.0,
            "critical": 25.0,
        }

    def calculate_overall_confidence(
        self,
        asset_data: Dict[str, Any],
        collection_metadata: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None,
    ) -> ConfidenceAssessment:
        """
        Calculate overall confidence score for an asset's data.

        Args:
            asset_data: Collected asset data
            collection_metadata: Metadata about data collection process
            business_context: Business context information

        Returns:
            Complete confidence assessment
        """
        try:
            # Calculate individual confidence factors
            factors = []

            # Data Completeness Factor
            completeness_factor = self._calculate_completeness_factor(asset_data)
            factors.append(completeness_factor)

            # Data Quality Factor
            quality_factor = self._calculate_quality_factor(
                asset_data, collection_metadata
            )
            factors.append(quality_factor)

            # Source Reliability Factor
            reliability_factor = self._calculate_reliability_factor(collection_metadata)
            factors.append(reliability_factor)

            # Validation Status Factor
            validation_factor = self._calculate_validation_factor(
                asset_data, collection_metadata
            )
            factors.append(validation_factor)

            # Business Context Factor
            if business_context:
                context_factor = self._calculate_business_context_factor(
                    asset_data, business_context
                )
                factors.append(context_factor)

            # Temporal Freshness Factor
            freshness_factor = self._calculate_freshness_factor(collection_metadata)
            factors.append(freshness_factor)

            # Cross-validation Factor
            cross_val_factor = self._calculate_cross_validation_factor(
                asset_data, collection_metadata
            )
            factors.append(cross_val_factor)

            # Calculate weighted overall score
            overall_score = self._calculate_weighted_score(factors)

            # Calculate strategy-specific confidence scores
            strategy_scores = self._calculate_strategy_scores(asset_data, factors)

            # Identify critical gaps
            critical_gaps = self._identify_critical_gaps(asset_data, factors)

            # Generate recommendations
            recommendations = self._generate_confidence_recommendations(
                factors, strategy_scores, critical_gaps
            )

            return ConfidenceAssessment(
                overall_score=overall_score,
                strategy_scores=strategy_scores,
                contributing_factors=factors,
                critical_gaps=critical_gaps,
                recommendations=recommendations,
                last_updated=datetime.now(timezone.utc),
                assessment_metadata={
                    "algorithm_version": "confidence_v1.0",
                    "factor_count": len(factors),
                    "calculation_method": "weighted_composite",
                },
            )

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return self._create_error_assessment(str(e))

    def _calculate_completeness_factor(
        self, asset_data: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate data completeness confidence factor"""
        try:
            # Define critical attributes across all categories
            all_critical_attributes = set()
            for strategy_data in self.strategy_requirements.values():
                all_critical_attributes.update(strategy_data["critical_attributes"])

            # Calculate completeness
            available_attributes = set(
                key
                for key, value in asset_data.items()
                if value is not None and value != "" and value != []
            )

            critical_available = available_attributes.intersection(
                all_critical_attributes
            )
            completeness_percentage = (
                len(critical_available) / len(all_critical_attributes)
            ) * 100

            # Apply quality scoring
            if completeness_percentage >= 90:
                score = 95 + (completeness_percentage - 90) * 0.5
            elif completeness_percentage >= 75:
                score = 80 + (completeness_percentage - 75) * 1.0
            elif completeness_percentage >= 50:
                score = 60 + (completeness_percentage - 50) * 0.8
            else:
                score = completeness_percentage * 1.2

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.DATA_COMPLETENESS,
                weight=self.factor_weights[ConfidenceFactorType.DATA_COMPLETENESS],
                score=min(100.0, max(0.0, score)),
                evidence={
                    "total_critical_attributes": len(all_critical_attributes),
                    "available_attributes": len(critical_available),
                    "completeness_percentage": completeness_percentage,
                    "missing_critical": list(
                        all_critical_attributes - critical_available
                    ),
                },
                description=f"Data completeness: {len(critical_available)}/{len(all_critical_attributes)} critical attributes",
            )

        except Exception as e:
            logger.error(f"Error calculating completeness factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.DATA_COMPLETENESS, str(e)
            )

    def _calculate_quality_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate data quality confidence factor"""
        try:
            quality_indicators = []

            # Check for data validation
            validation_score = collection_metadata.get("validation_score", 0)
            quality_indicators.append(("validation", validation_score))

            # Check for data consistency
            consistency_score = self._assess_data_consistency(asset_data)
            quality_indicators.append(("consistency", consistency_score))

            # Check for data format quality
            format_score = self._assess_data_format_quality(asset_data)
            quality_indicators.append(("format", format_score))

            # Check for data richness (depth of information)
            richness_score = self._assess_data_richness(asset_data)
            quality_indicators.append(("richness", richness_score))

            # Calculate weighted quality score
            total_weight = len(quality_indicators)
            weighted_score = (
                sum(score for _, score in quality_indicators) / total_weight
                if total_weight > 0
                else 0
            )

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.DATA_QUALITY,
                weight=self.factor_weights[ConfidenceFactorType.DATA_QUALITY],
                score=weighted_score,
                evidence={
                    "validation_score": validation_score,
                    "consistency_score": consistency_score,
                    "format_score": format_score,
                    "richness_score": richness_score,
                    "quality_indicators": dict(quality_indicators),
                },
                description=f"Data quality assessment: {weighted_score:.1f}% overall quality",
            )

        except Exception as e:
            logger.error(f"Error calculating quality factor: {e}")
            return self._create_error_factor(ConfidenceFactorType.DATA_QUALITY, str(e))

    def _calculate_reliability_factor(
        self, collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate source reliability confidence factor"""
        try:
            # Source type reliability scores
            source_reliability_scores = {
                "api_automated": 90,
                "database_export": 85,
                "configuration_file": 80,
                "monitoring_system": 85,
                "cmdb_system": 75,
                "manual_expert": 70,
                "manual_survey": 60,
                "documentation": 50,
                "estimation": 30,
            }

            collection_method = collection_metadata.get(
                "collection_method", "manual_survey"
            )
            base_reliability = source_reliability_scores.get(collection_method, 50)

            # Adjust based on collection metadata
            automation_tier = collection_metadata.get("automation_tier", "tier_3")
            tier_multipliers = {
                "tier_1": 1.1,  # Fully automated - bonus
                "tier_2": 1.05,  # Hybrid - slight bonus
                "tier_3": 1.0,  # Manual with some automation
                "tier_4": 0.95,  # Mostly manual - slight penalty
            }

            reliability_score = base_reliability * tier_multipliers.get(
                automation_tier, 1.0
            )

            # Consider data source credibility
            source_credibility = collection_metadata.get("source_credibility", "medium")
            credibility_adjustments = {
                "high": 1.1,
                "medium": 1.0,
                "low": 0.9,
                "unknown": 0.85,
            }

            reliability_score *= credibility_adjustments.get(source_credibility, 1.0)

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.SOURCE_RELIABILITY,
                weight=self.factor_weights[ConfidenceFactorType.SOURCE_RELIABILITY],
                score=min(100.0, max(0.0, reliability_score)),
                evidence={
                    "collection_method": collection_method,
                    "automation_tier": automation_tier,
                    "source_credibility": source_credibility,
                    "base_reliability": base_reliability,
                },
                description=f"Source reliability: {collection_method} with {automation_tier} automation",
            )

        except Exception as e:
            logger.error(f"Error calculating reliability factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.SOURCE_RELIABILITY, str(e)
            )

    def _calculate_validation_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate validation status confidence factor"""
        try:
            validation_score = 0
            validation_evidence = {}

            # Check for automated validation
            if collection_metadata.get("automated_validation_passed", False):
                validation_score += 40
                validation_evidence["automated_validation"] = True

            # Check for business validation
            if collection_metadata.get("business_validation_passed", False):
                validation_score += 30
                validation_evidence["business_validation"] = True

            # Check for technical validation
            if collection_metadata.get("technical_validation_passed", False):
                validation_score += 20
                validation_evidence["technical_validation"] = True

            # Check for cross-reference validation
            if collection_metadata.get("cross_reference_validated", False):
                validation_score += 10
                validation_evidence["cross_reference_validation"] = True

            # Penalty for validation failures
            validation_failures = collection_metadata.get("validation_failures", [])
            if validation_failures:
                failure_penalty = min(30, len(validation_failures) * 10)
                validation_score -= failure_penalty
                validation_evidence["validation_failures"] = validation_failures

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.VALIDATION_STATUS,
                weight=self.factor_weights[ConfidenceFactorType.VALIDATION_STATUS],
                score=min(100.0, max(0.0, validation_score)),
                evidence=validation_evidence,
                description=f"Validation status: {len(validation_evidence)} validation types completed",
            )

        except Exception as e:
            logger.error(f"Error calculating validation factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.VALIDATION_STATUS, str(e)
            )

    def _calculate_business_context_factor(
        self, asset_data: Dict[str, Any], business_context: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate business context confidence factor"""
        try:
            context_score = 0
            context_evidence = {}

            # Business criticality defined
            if business_context.get("business_criticality"):
                context_score += 25
                context_evidence["business_criticality"] = business_context[
                    "business_criticality"
                ]

            # Cost center and ownership
            if business_context.get("cost_center") or asset_data.get("cost_center"):
                context_score += 20
                context_evidence["cost_center"] = True

            # Compliance and regulatory context
            if business_context.get("compliance_requirements") or asset_data.get(
                "compliance_scope"
            ):
                context_score += 20
                context_evidence["compliance_context"] = True

            # Business function and purpose
            if business_context.get("business_function") or asset_data.get(
                "business_function"
            ):
                context_score += 15
                context_evidence["business_function"] = True

            # Stakeholder information
            if business_context.get("stakeholders") or business_context.get(
                "business_owner"
            ):
                context_score += 10
                context_evidence["stakeholder_info"] = True

            # Strategic importance
            if business_context.get("strategic_importance"):
                context_score += 10
                context_evidence["strategic_importance"] = business_context[
                    "strategic_importance"
                ]

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.BUSINESS_CONTEXT,
                weight=self.factor_weights[ConfidenceFactorType.BUSINESS_CONTEXT],
                score=context_score,
                evidence=context_evidence,
                description=f"Business context completeness: {len(context_evidence)} context elements",
            )

        except Exception as e:
            logger.error(f"Error calculating business context factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.BUSINESS_CONTEXT, str(e)
            )

    def _calculate_freshness_factor(
        self, collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate temporal freshness confidence factor"""
        try:
            collection_timestamp = collection_metadata.get("collection_timestamp")
            if not collection_timestamp:
                collection_timestamp = collection_metadata.get("created_at")

            if isinstance(collection_timestamp, str):
                try:
                    collection_time = datetime.fromisoformat(
                        collection_timestamp.replace("Z", "+00:00")
                    )
                except Exception:
                    collection_time = datetime.now(timezone.utc)
            elif isinstance(collection_timestamp, datetime):
                collection_time = collection_timestamp
            else:
                collection_time = datetime.now(timezone.utc)

            # Calculate age in days
            age_days = (datetime.now(timezone.utc) - collection_time).days

            # Freshness scoring based on age
            if age_days <= 1:
                freshness_score = 100
            elif age_days <= 7:
                freshness_score = 95 - (age_days - 1) * 2
            elif age_days <= 30:
                freshness_score = 88 - (age_days - 7) * 1.5
            elif age_days <= 90:
                freshness_score = 55 - (age_days - 30) * 0.5
            else:
                freshness_score = max(20, 25 - (age_days - 90) * 0.1)

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.TEMPORAL_FRESHNESS,
                weight=self.factor_weights[ConfidenceFactorType.TEMPORAL_FRESHNESS],
                score=freshness_score,
                evidence={
                    "collection_timestamp": collection_time.isoformat(),
                    "age_days": age_days,
                    "freshness_category": self._categorize_freshness(age_days),
                },
                description=f"Data freshness: {age_days} days old",
            )

        except Exception as e:
            logger.error(f"Error calculating freshness factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.TEMPORAL_FRESHNESS, str(e)
            )

    def _calculate_cross_validation_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate cross-validation confidence factor"""
        try:
            cross_val_score = 0
            cross_val_evidence = {}

            # Multiple source validation
            source_count = collection_metadata.get("source_count", 1)
            if source_count > 1:
                cross_val_score += min(40, source_count * 15)
                cross_val_evidence["multiple_sources"] = source_count

            # Cross-reference with known systems
            if collection_metadata.get("cmdb_cross_reference", False):
                cross_val_score += 25
                cross_val_evidence["cmdb_cross_reference"] = True

            # Consistency across collection methods
            consistency_score = collection_metadata.get("cross_method_consistency", 0)
            if consistency_score > 0:
                cross_val_score += consistency_score * 0.3
                cross_val_evidence["cross_method_consistency"] = consistency_score

            # Historical data comparison
            if collection_metadata.get("historical_comparison", False):
                cross_val_score += 15
                cross_val_evidence["historical_comparison"] = True

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.CROSS_VALIDATION,
                weight=self.factor_weights[ConfidenceFactorType.CROSS_VALIDATION],
                score=min(100.0, cross_val_score),
                evidence=cross_val_evidence,
                description=f"Cross-validation: {len(cross_val_evidence)} validation types",
            )

        except Exception as e:
            logger.error(f"Error calculating cross-validation factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.CROSS_VALIDATION, str(e)
            )

    def _calculate_weighted_score(self, factors: List[ConfidenceFactor]) -> float:
        """Calculate weighted overall confidence score"""
        try:
            total_weighted_score = 0
            total_weight = 0

            for factor in factors:
                weighted_contribution = factor.score * factor.weight
                total_weighted_score += weighted_contribution
                total_weight += factor.weight

            if total_weight == 0:
                return 0.0

            # Normalize to 0-100 scale
            overall_score = total_weighted_score / total_weight

            return min(100.0, max(0.0, overall_score))

        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}")
            return 0.0

    def _calculate_strategy_scores(
        self, asset_data: Dict[str, Any], factors: List[ConfidenceFactor]
    ) -> Dict[SixRStrategy, float]:
        """Calculate confidence scores for each 6R strategy"""
        strategy_scores = {}

        try:
            # Get base confidence from factors
            base_confidence = self._calculate_weighted_score(factors)

            for strategy, requirements in self.strategy_requirements.items():
                # Check availability of critical attributes for this strategy
                critical_attrs = requirements["critical_attributes"]
                available_attrs = [
                    attr
                    for attr in critical_attrs
                    if attr in asset_data
                    and asset_data[attr] is not None
                    and asset_data[attr] != ""
                ]

                # Calculate attribute completeness for this strategy
                attr_completeness = (
                    len(available_attrs) / len(critical_attrs) if critical_attrs else 0
                )

                # Apply strategy-specific adjustments
                strategy_confidence = (
                    base_confidence * 0.7 + (attr_completeness * 100) * 0.3
                )

                # Apply minimum threshold consideration
                min_threshold = requirements.get("minimum_confidence_threshold", 70.0)
                if strategy_confidence < min_threshold:
                    # Reduce confidence more aggressively if below minimum
                    strategy_confidence *= 0.8

                strategy_scores[strategy] = min(100.0, max(0.0, strategy_confidence))

        except Exception as e:
            logger.error(f"Error calculating strategy scores: {e}")
            # Return default scores on error
            for strategy in SixRStrategy:
                strategy_scores[strategy] = 50.0

        return strategy_scores

    def _identify_critical_gaps(
        self, asset_data: Dict[str, Any], factors: List[ConfidenceFactor]
    ) -> List[str]:
        """Identify critical gaps affecting confidence"""
        gaps = []

        try:
            # Check for low-scoring factors
            for factor in factors:
                if factor.score < 60:  # Critical threshold
                    gaps.append(f"Low {factor.factor_type.value}: {factor.description}")

            # Check for missing critical attributes
            all_critical_attrs = set()
            for strategy_data in self.strategy_requirements.values():
                all_critical_attrs.update(strategy_data["critical_attributes"])

            missing_attrs = [
                attr
                for attr in all_critical_attrs
                if attr not in asset_data or not asset_data[attr]
            ]

            if missing_attrs:
                gaps.append(
                    f"Missing critical attributes: {', '.join(missing_attrs[:5])}"
                )
                if len(missing_attrs) > 5:
                    gaps.append(
                        f"... and {len(missing_attrs) - 5} more missing attributes"
                    )

        except Exception as e:
            logger.error(f"Error identifying critical gaps: {e}")
            gaps.append(f"Error in gap analysis: {str(e)}")

        return gaps

    def _generate_confidence_recommendations(
        self,
        factors: List[ConfidenceFactor],
        strategy_scores: Dict[SixRStrategy, float],
        critical_gaps: List[str],
    ) -> List[str]:
        """Generate recommendations to improve confidence"""
        recommendations = []

        try:
            # Factor-based recommendations
            for factor in factors:
                if factor.score < 70:
                    if factor.factor_type == ConfidenceFactorType.DATA_COMPLETENESS:
                        recommendations.append(
                            "Collect missing critical attributes through targeted questionnaires"
                        )
                    elif factor.factor_type == ConfidenceFactorType.DATA_QUALITY:
                        recommendations.append(
                            "Improve data quality through validation and standardization"
                        )
                    elif factor.factor_type == ConfidenceFactorType.SOURCE_RELIABILITY:
                        recommendations.append(
                            "Verify data with more reliable sources or additional collection methods"
                        )
                    elif factor.factor_type == ConfidenceFactorType.VALIDATION_STATUS:
                        recommendations.append(
                            "Implement comprehensive data validation processes"
                        )

            # Strategy-specific recommendations
            low_confidence_strategies = [
                strategy for strategy, score in strategy_scores.items() if score < 75
            ]
            if low_confidence_strategies:
                recommendations.append(
                    f"Focus data collection on requirements for: {', '.join(low_confidence_strategies)}"
                )

            # Gap-based recommendations
            if len(critical_gaps) > 3:
                recommendations.append(
                    "Prioritize filling critical data gaps before proceeding with migration planning"
                )
            elif critical_gaps:
                recommendations.append(
                    "Address identified data gaps to improve migration confidence"
                )

            # General recommendations
            overall_score = self._calculate_weighted_score(factors)
            if overall_score < 60:
                recommendations.append(
                    "Consider additional data collection phases before finalizing migration strategy"
                )
            elif overall_score < 80:
                recommendations.append(
                    "Validate current data with subject matter experts"
                )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(
                "Review data collection process and consider additional validation"
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    # Helper methods
    def _assess_data_consistency(self, asset_data: Dict[str, Any]) -> float:
        """Assess internal data consistency"""
        # Simplified consistency check
        consistency_score = 80.0  # Default reasonable score

        # Check for obvious inconsistencies
        if (
            asset_data.get("environment") == "production"
            and asset_data.get("business_criticality") == "low"
        ):
            consistency_score -= 10

        return consistency_score

    def _assess_data_format_quality(self, asset_data: Dict[str, Any]) -> float:
        """Assess data format quality"""
        format_score = 85.0  # Default score

        # Check for standardized formats
        numeric_fields = ["cpu_cores", "memory_gb", "storage_gb"]
        for field in numeric_fields:
            if field in asset_data:
                try:
                    float(asset_data[field])
                except (ValueError, TypeError):
                    format_score -= 5

        return max(0, format_score)

    def _assess_data_richness(self, asset_data: Dict[str, Any]) -> float:
        """Assess depth and richness of data"""
        richness_score = 0

        # Count non-empty fields
        populated_fields = sum(
            1
            for value in asset_data.values()
            if value is not None and value != "" and value != []
        )

        # Score based on field count
        if populated_fields >= 20:
            richness_score = 95
        elif populated_fields >= 15:
            richness_score = 85
        elif populated_fields >= 10:
            richness_score = 70
        elif populated_fields >= 5:
            richness_score = 50
        else:
            richness_score = 30

        return richness_score

    def _categorize_freshness(self, age_days: int) -> str:
        """Categorize data freshness"""
        if age_days <= 1:
            return "very_fresh"
        elif age_days <= 7:
            return "fresh"
        elif age_days <= 30:
            return "recent"
        elif age_days <= 90:
            return "aging"
        else:
            return "stale"

    def _create_error_factor(
        self, factor_type: ConfidenceFactorType, error_msg: str
    ) -> ConfidenceFactor:
        """Create error factor for failed calculations"""
        return ConfidenceFactor(
            factor_type=factor_type,
            weight=self.factor_weights.get(factor_type, 0.1),
            score=0.0,
            evidence={"error": error_msg},
            description=f"Error calculating {factor_type.value}",
        )

    def _create_error_assessment(self, error_msg: str) -> ConfidenceAssessment:
        """Create error assessment for failed confidence calculations"""
        return ConfidenceAssessment(
            overall_score=0.0,
            strategy_scores={strategy: 0.0 for strategy in SixRStrategy},
            contributing_factors=[],
            critical_gaps=[f"Confidence calculation error: {error_msg}"],
            recommendations=[
                "Review data collection process",
                "Retry confidence assessment",
            ],
            last_updated=datetime.now(timezone.utc),
            assessment_metadata={"error": True, "error_message": error_msg},
        )


# Convenience functions for easy integration
def calculate_collection_confidence(
    collected_assets: List[Dict[str, Any]],
    collection_metadata: Dict[str, Any],
    business_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate confidence scores for a collection of assets.

    Args:
        collected_assets: List of collected asset data
        collection_metadata: Metadata about the collection process
        business_context: Business context information

    Returns:
        Aggregated confidence assessment for the collection
    """
    try:
        scorer = ConfidenceScorer()
        asset_assessments = []

        for asset in collected_assets:
            assessment = scorer.calculate_overall_confidence(
                asset, collection_metadata, business_context
            )
            asset_assessments.append(assessment)

        # Aggregate assessments
        if not asset_assessments:
            return {"error": "No assets to assess"}

        # Calculate aggregate metrics
        overall_scores = [a.overall_score for a in asset_assessments]
        avg_overall_score = sum(overall_scores) / len(overall_scores)

        # Aggregate strategy scores
        aggregate_strategy_scores = {}
        for strategy in SixRStrategy:
            strategy_scores = [
                a.strategy_scores.get(strategy, 0) for a in asset_assessments
            ]
            aggregate_strategy_scores[strategy] = sum(strategy_scores) / len(
                strategy_scores
            )

        # Collect all critical gaps
        all_gaps = []
        for assessment in asset_assessments:
            all_gaps.extend(assessment.critical_gaps)

        # Count gap occurrences
        gap_frequency = {}
        for gap in all_gaps:
            gap_frequency[gap] = gap_frequency.get(gap, 0) + 1

        # Get most common gaps
        common_gaps = sorted(gap_frequency.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        return {
            "collection_confidence": {
                "overall_score": round(avg_overall_score, 2),
                "strategy_scores": {
                    k.value: round(v, 2) for k, v in aggregate_strategy_scores.items()
                },
                "asset_count": len(asset_assessments),
                "confidence_distribution": {
                    "excellent": len([s for s in overall_scores if s >= 90]),
                    "good": len([s for s in overall_scores if 75 <= s < 90]),
                    "acceptable": len([s for s in overall_scores if 60 <= s < 75]),
                    "poor": len([s for s in overall_scores if s < 60]),
                },
            },
            "common_gaps": [
                {"gap": gap, "frequency": freq} for gap, freq in common_gaps
            ],
            "recommendations": [
                "Focus on addressing the most common gaps across assets",
                "Implement consistent data collection standards",
                "Validate data with subject matter experts",
                "Consider additional collection phases for low-confidence assets",
            ],
            "assessment_metadata": {
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm_version": "confidence_v1.0",
                "asset_assessments_count": len(asset_assessments),
            },
        }

    except Exception as e:
        logger.error(f"Error calculating collection confidence: {e}")
        return {
            "error": str(e),
            "collection_confidence": {"overall_score": 0, "asset_count": 0},
            "assessment_metadata": {
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True,
            },
        }
