"""
Confidence Assessment Service

This module provides the service for assessing confidence levels in collected data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession

from .constants import (
    CONFIDENCE_WEIGHTS,
    PLATFORM_CONFIDENCE,
    SOURCE_RELIABILITY,
    TIER_CONFIDENCE,
)
from .enums import ConfidenceLevel
from .models import ConfidenceScore, QualityScore

logger = logging.getLogger(__name__)


class ConfidenceAssessmentService:
    """
    Service for assessing confidence levels in collected data.

    This service evaluates:
    - Source reliability
    - Collection method confidence
    - Data validation results
    - Historical accuracy
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Confidence Assessment Service.

        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context

    async def assess_confidence(
        self,
        collection_metadata: Dict[str, Any],
        quality_score: QualityScore,
        validation_results: Optional[Dict[str, Any]] = None,
    ) -> ConfidenceScore:
        """
        Assess confidence level in collected data.

        Args:
            collection_metadata: Metadata about collection process
            quality_score: Quality assessment results
            validation_results: Optional validation results

        Returns:
            ConfidenceScore with detailed assessment
        """
        try:
            confidence_factors = {}

            # Assess source reliability
            source_confidence = self._assess_source_reliability(collection_metadata)
            confidence_factors["source_reliability"] = source_confidence

            # Assess collection method confidence
            method_confidence = self._assess_method_confidence(collection_metadata)
            confidence_factors["collection_method"] = method_confidence

            # Factor in quality score
            quality_confidence = self._calculate_quality_confidence(quality_score)
            confidence_factors["data_quality"] = quality_confidence

            # Assess validation confidence
            if validation_results:
                validation_confidence = self._assess_validation_confidence(
                    validation_results
                )
                confidence_factors["validation"] = validation_confidence

            # Calculate historical confidence if available
            historical_confidence = await self._assess_historical_confidence(
                collection_metadata
            )
            if historical_confidence is not None:
                confidence_factors["historical_accuracy"] = historical_confidence

            # Calculate overall confidence (weighted average)
            overall_confidence = 0.0
            total_weight = 0.0

            for factor, score in confidence_factors.items():
                if factor in CONFIDENCE_WEIGHTS:
                    overall_confidence += score * CONFIDENCE_WEIGHTS[factor]
                    total_weight += CONFIDENCE_WEIGHTS[factor]

            if total_weight > 0:
                overall_confidence = overall_confidence / total_weight

            # Determine confidence level
            confidence_level = self._determine_confidence_level(overall_confidence)

            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                confidence_factors, collection_metadata, quality_score
            )

            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                confidence_factors, risk_factors
            )

            return ConfidenceScore(
                overall_confidence=round(overall_confidence, 2),
                confidence_level=confidence_level,
                confidence_factors={
                    k: round(v, 2) for k, v in confidence_factors.items()
                },
                risk_factors=risk_factors,
                improvement_suggestions=improvement_suggestions,
                metadata={
                    "assessment_timestamp": datetime.utcnow().isoformat(),
                    "quality_score": quality_score.overall_score,
                },
            )

        except Exception as e:
            logger.error(f"Confidence assessment failed: {str(e)}")
            raise

    def _assess_source_reliability(self, metadata: Dict[str, Any]) -> float:
        """Assess reliability of data source."""
        source = metadata.get("source", "").lower()
        platform = metadata.get("platform", "").lower()

        # Get base source reliability
        base_reliability = 0.5  # Default
        for source_type, reliability in SOURCE_RELIABILITY.items():
            if source_type in source:
                base_reliability = reliability
                break

        # Apply platform confidence multiplier
        platform_multiplier = 1.0
        for plat, multiplier in PLATFORM_CONFIDENCE.items():
            if plat in platform:
                platform_multiplier = multiplier
                break

        return base_reliability * platform_multiplier

    def _assess_method_confidence(self, metadata: Dict[str, Any]) -> float:
        """Assess confidence in collection method."""
        automation_tier = metadata.get("automation_tier", "tier_1")

        # Base confidence by automation tier
        base_confidence = TIER_CONFIDENCE.get(automation_tier, 0.50)

        # Adjust based on specific method characteristics
        if "real_time" in metadata.get("characteristics", []):
            base_confidence *= 1.1
        if "authenticated" in metadata.get("characteristics", []):
            base_confidence *= 1.05
        if "encrypted" in metadata.get("characteristics", []):
            base_confidence *= 1.05

        return min(base_confidence, 1.0)

    def _calculate_quality_confidence(self, quality_score: QualityScore) -> float:
        """Calculate confidence based on quality score."""
        # Map quality score to confidence
        if quality_score.overall_score >= 90:
            return 0.95
        elif quality_score.overall_score >= 80:
            return 0.85
        elif quality_score.overall_score >= 70:
            return 0.70
        elif quality_score.overall_score >= 60:
            return 0.55
        else:
            return 0.40

    def _assess_validation_confidence(
        self, validation_results: Dict[str, Any]
    ) -> float:
        """Assess confidence based on validation results."""
        passed = validation_results.get("passed", 0)
        failed = validation_results.get("failed", 0)
        total = passed + failed

        if total == 0:
            return 0.5

        success_rate = passed / total

        # Factor in validation coverage
        coverage = validation_results.get("coverage_percentage", 100) / 100

        return success_rate * coverage

    async def _assess_historical_confidence(
        self, metadata: Dict[str, Any]
    ) -> Optional[float]:
        """Assess confidence based on historical accuracy."""
        # This would typically query historical collection accuracy
        # For now, return None to indicate no historical data
        return None

    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level based on score."""
        if confidence_score >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.70:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.CRITICAL

    def _identify_risk_factors(
        self,
        confidence_factors: Dict[str, float],
        metadata: Dict[str, Any],
        quality_score: QualityScore,
    ) -> List[Dict[str, Any]]:
        """Identify risk factors affecting confidence."""
        risk_factors = []

        # Low confidence factors
        for factor, score in confidence_factors.items():
            if score < 0.60:
                risk_factors.append(
                    {
                        "factor": factor,
                        "severity": "high" if score < 0.40 else "medium",
                        "score": score,
                        "description": f"Low confidence in {factor.replace('_', ' ')}",
                    }
                )

        # Quality issues
        high_severity_issues = [
            i for i in quality_score.issues_found if i.get("severity") == "high"
        ]
        if high_severity_issues:
            risk_factors.append(
                {
                    "factor": "data_quality",
                    "severity": "high",
                    "description": f"{len(high_severity_issues)} high severity quality issues",
                    "issue_count": len(high_severity_issues),
                }
            )

        # Collection method risks
        if metadata.get("collection_method") == "manual":
            risk_factors.append(
                {
                    "factor": "collection_method",
                    "severity": "medium",
                    "description": "Manual data collection prone to human error",
                }
            )

        # Age of data
        if "collection_timestamp" in metadata:
            try:
                collection_dt = datetime.fromisoformat(metadata["collection_timestamp"])
                age_days = (datetime.utcnow() - collection_dt).days
                if age_days > 30:
                    risk_factors.append(
                        {
                            "factor": "data_age",
                            "severity": "medium" if age_days < 90 else "high",
                            "description": f"Data is {age_days} days old",
                            "age_days": age_days,
                        }
                    )
            except Exception:
                pass

        return risk_factors

    def _generate_improvement_suggestions(
        self, confidence_factors: Dict[str, float], risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate suggestions for improving confidence."""
        suggestions = []

        # Suggestions based on low confidence factors
        if confidence_factors.get("source_reliability", 1.0) < 0.70:
            suggestions.append(
                "Consider upgrading to API-based collection for higher reliability"
            )

        if confidence_factors.get("collection_method", 1.0) < 0.70:
            suggestions.append(
                "Implement automated collection methods to improve confidence"
            )

        if confidence_factors.get("data_quality", 1.0) < 0.70:
            suggestions.append(
                "Address data quality issues to improve overall confidence"
            )

        # Suggestions based on risk factors
        manual_risks = [
            r for r in risk_factors if "manual" in r.get("description", "").lower()
        ]
        if manual_risks:
            suggestions.append(
                "Replace manual processes with automated collection where possible"
            )

        age_risks = [r for r in risk_factors if r.get("factor") == "data_age"]
        if age_risks:
            suggestions.append(
                "Implement more frequent data collection to ensure freshness"
            )

        # General suggestions
        if len(risk_factors) > 3:
            suggestions.append(
                "Consider a comprehensive review of the data collection strategy"
            )

        return list(set(suggestions))  # Remove duplicates
