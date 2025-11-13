"""
Collection Flow Readiness Assessment Service

This service implements the validation logic required by the Collection Flow
validation checklist, including:
- Collection completeness >= 70% threshold check
- Critical gaps validation
- Data quality score >= 65% check
- Field mappings validation
- Blocking errors check
- Assessment readiness determination
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionGapAnalysis
from app.models.collection_data_gap import CollectionDataGap
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class ReadinessThresholds(BaseModel):
    """Configurable thresholds for collection readiness assessment"""

    collection_completeness: float = 0.70  # 70%
    data_quality_score: float = 0.65  # 65%
    confidence_score: float = 0.60  # 60%
    max_critical_gaps: int = 5  # Maximum critical gaps allowed
    max_blocking_errors: int = 0  # No blocking errors allowed


class ReadinessAssessmentResult(BaseModel):
    """Result of collection readiness assessment"""

    is_ready: bool
    overall_score: float
    confidence: float
    reason: str

    # Detailed metrics
    collection_completeness: float
    data_quality_score: Optional[float]
    critical_gaps_count: int
    blocking_errors_count: int
    field_mappings_complete: bool
    applications_ready: int
    total_applications: int

    # Validation details
    thresholds_used: ReadinessThresholds
    missing_requirements: List[str]
    recommendations: List[str]

    # Metadata
    assessed_at: datetime
    assessed_by: str = "collection_readiness_service"


class CollectionReadinessService:
    """Service for assessing collection flow readiness for assessment transition"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.thresholds = ReadinessThresholds()

    async def assess_readiness(self, flow_id: UUID) -> ReadinessAssessmentResult:
        """
        Perform comprehensive readiness assessment for collection flow.

        Implements all validation requirements from the checklist:
        - Section 6: Readiness Assessment Logic
        - Collection completeness >= 70%
        - Critical gaps addressed
        - Data quality score >= 65%
        - Field mappings validation
        - No blocking errors
        """
        logger.info(f"Starting readiness assessment for collection flow {flow_id}")

        # Get collection flow with tenant scoping
        collection_flow = await self._get_collection_flow(flow_id)
        if not collection_flow:
            raise ValueError(f"Collection flow {flow_id} not found or access denied")

        # Run all assessment checks in parallel where possible
        (
            completeness_metrics,
            gaps_analysis,
            applications_data,
            field_mappings_result,
            blocking_errors,
        ) = await self._gather_assessment_data(collection_flow)

        # Calculate individual scores
        completeness_score = (
            completeness_metrics.get("completeness_percentage", 0.0) / 100.0
        )
        data_quality = (
            gaps_analysis.get("data_quality_score") if gaps_analysis else None
        )
        critical_gaps_count = (
            len(gaps_analysis.get("critical_gaps", [])) if gaps_analysis else 0
        )
        blocking_errors_count = len(blocking_errors)

        # Validate field mappings
        field_mappings_complete = await self._validate_field_mappings(collection_flow)

        # Application readiness
        apps_ready, total_apps = applications_data

        # Determine overall readiness
        is_ready, overall_score, reason, missing_requirements, recommendations = (
            await self._determine_readiness(
                completeness_score,
                data_quality,
                critical_gaps_count,
                blocking_errors_count,
                field_mappings_complete,
                apps_ready,
                total_apps,
            )
        )

        # Use agent for final confidence assessment if available
        confidence = await self._get_agent_confidence(
            collection_flow, completeness_score, data_quality, critical_gaps_count
        )

        result = ReadinessAssessmentResult(
            is_ready=is_ready,
            overall_score=overall_score,
            confidence=confidence,
            reason=reason,
            collection_completeness=completeness_score,
            data_quality_score=data_quality,
            critical_gaps_count=critical_gaps_count,
            blocking_errors_count=blocking_errors_count,
            field_mappings_complete=field_mappings_complete,
            applications_ready=apps_ready,
            total_applications=total_apps,
            thresholds_used=self.thresholds,
            missing_requirements=missing_requirements,
            recommendations=recommendations,
            assessed_at=datetime.utcnow(),
        )

        logger.info(
            f"Readiness assessment complete for flow {flow_id}: "
            f"ready={is_ready}, score={overall_score:.2f}, confidence={confidence:.2f}"
        )

        return result

    async def _get_collection_flow(self, flow_id: UUID) -> Optional[CollectionFlow]:
        """Get collection flow with tenant scoping"""
        result = await self.db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id == self.context.client_account_id,
                    CollectionFlow.engagement_id == self.context.engagement_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _gather_assessment_data(
        self, collection_flow: CollectionFlow
    ) -> Tuple[
        Dict[str, Any], Optional[Dict[str, Any]], Tuple[int, int], bool, List[str]
    ]:
        """Gather all data needed for assessment in parallel where possible"""

        # 1. Collection completeness metrics
        completeness_metrics = await self._calculate_completeness_metrics(
            collection_flow
        )

        # 2. Gap analysis data
        gaps_analysis = await self._get_gap_analysis_data(collection_flow)

        # 3. Application readiness data
        applications_data = await self._get_application_readiness_data(collection_flow)

        # 4. Field mappings validation
        field_mappings_result = await self._validate_field_mappings(collection_flow)

        # 5. Blocking errors
        blocking_errors = await self._get_blocking_errors(collection_flow)

        return (
            completeness_metrics,
            gaps_analysis,
            applications_data,
            field_mappings_result,
            blocking_errors,
        )

    async def _calculate_completeness_metrics(
        self, collection_flow: CollectionFlow
    ) -> Dict[str, Any]:
        """Calculate collection completeness percentage"""

        # Check if there's a gap analysis record with completeness data
        gap_analysis_result = await self.db.execute(
            select(CollectionGapAnalysis).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )
        gap_analysis = gap_analysis_result.scalar_one_or_none()

        if gap_analysis:
            return {
                "completeness_percentage": gap_analysis.completeness_percentage,
                "total_fields_required": gap_analysis.total_fields_required,
                "fields_collected": gap_analysis.fields_collected,
                "fields_missing": gap_analysis.fields_missing,
                "source": "gap_analysis_table",
            }

        # Fallback: Calculate from collection data
        # Per ADR-028: phase_state removed, use gap_analysis_results instead
        gap_results = collection_flow.gap_analysis_results or {}
        field_mappings = gap_results.get("field_mappings", {})

        if field_mappings:
            total_fields = field_mappings.get("total_fields", 0)
            mapped_fields = field_mappings.get("mapped_fields", 0)

            if total_fields > 0:
                completeness = (mapped_fields / total_fields) * 100
                return {
                    "completeness_percentage": completeness,
                    "total_fields_required": total_fields,
                    "fields_collected": mapped_fields,
                    "fields_missing": total_fields - mapped_fields,
                    "source": "gap_analysis_results",
                }

        # Final fallback: Use progress percentage
        progress = collection_flow.progress_percentage or 0.0
        return {
            "completeness_percentage": progress,
            "total_fields_required": 100,
            "fields_collected": int(progress),
            "fields_missing": int(100 - progress),
            "source": "progress_percentage",
        }

    async def _get_gap_analysis_data(
        self, collection_flow: CollectionFlow
    ) -> Optional[Dict[str, Any]]:
        """Get gap analysis data from database or flow state"""

        # First check for gap analysis record
        gap_analysis_result = await self.db.execute(
            select(CollectionGapAnalysis).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )
        gap_analysis = gap_analysis_result.scalar_one_or_none()

        if gap_analysis:
            return {
                "data_quality_score": gap_analysis.data_quality_score,
                "confidence_level": gap_analysis.confidence_level,
                "critical_gaps": gap_analysis.critical_gaps or [],
                "optional_gaps": gap_analysis.optional_gaps or [],
                "gap_categories": gap_analysis.gap_categories or {},
                "source": "gap_analysis_table",
            }

        # Fallback: Check collection flow gap_analysis_results
        gap_results = collection_flow.gap_analysis_results or {}
        if gap_results:
            return {
                "data_quality_score": gap_results.get("data_quality_score"),
                "confidence_level": gap_results.get("confidence_level"),
                "critical_gaps": gap_results.get("critical_gaps", []),
                "optional_gaps": gap_results.get("optional_gaps", []),
                "gap_categories": gap_results.get("gap_categories", {}),
                "source": "flow_state",
            }

        # Check individual gap records
        gaps_result = await self.db.execute(
            select(CollectionDataGap).where(
                CollectionDataGap.collection_flow_id == collection_flow.id
            )
        )
        gaps = gaps_result.scalars().all()

        if gaps:
            critical_gaps = []
            optional_gaps = []

            for gap in gaps:
                gap_data = {
                    "field_name": gap.field_name,
                    "gap_type": gap.gap_type,
                    "severity": gap.severity,
                    "description": gap.description,
                }

                if gap.severity in ["critical", "high"]:
                    critical_gaps.append(gap_data)
                else:
                    optional_gaps.append(gap_data)

            return {
                "data_quality_score": None,
                "confidence_level": None,
                "critical_gaps": critical_gaps,
                "optional_gaps": optional_gaps,
                "gap_categories": {},
                "source": "individual_gaps",
            }

        return None

    async def _get_application_readiness_data(
        self, collection_flow: CollectionFlow
    ) -> Tuple[int, int]:
        """Get application readiness statistics"""

        # Get applications linked to this collection flow
        apps_result = await self.db.execute(
            select(CollectionFlowApplication).where(
                CollectionFlowApplication.collection_flow_id == collection_flow.id
            )
        )
        apps = apps_result.scalars().all()

        total_apps = len(apps)
        apps_ready = 0

        # Check each application's readiness
        for app in apps:
            # An application is considered ready if it has:
            # - Complete CMDB data (based on data_completeness_score)
            # - Technical stack identified
            # - Dependencies mapped
            # - Migration complexity calculated

            completeness_score = getattr(app, "data_completeness_score", 0) or 0
            has_tech_stack = bool(getattr(app, "technology_stack", None))
            has_dependencies = bool(getattr(app, "dependencies_data", None))
            has_complexity = getattr(app, "migration_complexity", None) is not None

            if (
                completeness_score >= 0.7
                and has_tech_stack
                and has_dependencies
                and has_complexity
            ):
                apps_ready += 1

        return apps_ready, total_apps

    async def _validate_field_mappings(self, collection_flow: CollectionFlow) -> bool:
        """Validate that field mappings are complete and accurate"""

        # Per ADR-028: phase_state removed, use gap_analysis_results instead
        gap_results = collection_flow.gap_analysis_results or {}
        field_mappings = gap_results.get("field_mappings", {})

        if not field_mappings:
            return False

        # Check for mapping completion indicators
        mapping_status = field_mappings.get("status", "incomplete")
        mapping_accuracy = field_mappings.get("accuracy_score", 0.0)

        # Field mappings are valid if:
        # 1. Status is "complete" or "validated"
        # 2. Accuracy score is >= 80%
        is_complete = mapping_status in ["complete", "validated", "approved"]
        is_accurate = mapping_accuracy >= 0.8

        return is_complete and is_accurate

    async def _get_blocking_errors(self, collection_flow: CollectionFlow) -> List[str]:
        """Get blocking errors that prevent assessment transition"""

        blocking_errors = []

        # Check error_message and error_details fields
        if collection_flow.error_message:
            # Classify errors as blocking or non-blocking
            error_msg = collection_flow.error_message.lower()
            blocking_keywords = [
                "critical",
                "fatal",
                "blocked",
                "failed",
                "timeout",
                "access_denied",
                "authentication",
                "authorization",
            ]

            if any(keyword in error_msg for keyword in blocking_keywords):
                blocking_errors.append(collection_flow.error_message)

        # Check error_details for structured errors
        if collection_flow.error_details:
            error_details = collection_flow.error_details
            if isinstance(error_details, dict):
                errors = error_details.get("errors", [])
                for error in errors:
                    if isinstance(error, dict) and error.get("severity") in [
                        "critical",
                        "fatal",
                    ]:
                        blocking_errors.append(
                            error.get("message", "Unknown critical error")
                        )

        # Check for flow-level blocking conditions
        if collection_flow.status in ["failed", "cancelled"]:
            blocking_errors.append(f"Flow status is {collection_flow.status}")

        return blocking_errors

    async def _determine_readiness(
        self,
        completeness_score: float,
        data_quality_score: Optional[float],
        critical_gaps_count: int,
        blocking_errors_count: int,
        field_mappings_complete: bool,
        apps_ready: int,
        total_apps: int,
    ) -> Tuple[bool, float, str, List[str], List[str]]:
        """Determine overall readiness based on all metrics"""

        missing_requirements = []
        recommendations = []
        reasons = []

        # Check collection completeness >= 70%
        if completeness_score < self.thresholds.collection_completeness:
            missing_requirements.append(
                f"Collection completeness is {completeness_score:.1%}, "
                f"needs to be >= {self.thresholds.collection_completeness:.1%}"
            )
            reasons.append("insufficient_completeness")

        # Check data quality score >= 65%
        if (
            data_quality_score is not None
            and data_quality_score < self.thresholds.data_quality_score
        ):
            missing_requirements.append(
                f"Data quality score is {data_quality_score:.1%}, "
                f"needs to be >= {self.thresholds.data_quality_score:.1%}"
            )
            reasons.append("low_data_quality")

        # Check critical gaps
        if critical_gaps_count > self.thresholds.max_critical_gaps:
            missing_requirements.append(
                f"Too many critical gaps ({critical_gaps_count}), "
                f"maximum allowed is {self.thresholds.max_critical_gaps}"
            )
            reasons.append("too_many_critical_gaps")

        # Check for blocking errors
        if blocking_errors_count > self.thresholds.max_blocking_errors:
            missing_requirements.append(
                f"Blocking errors present ({blocking_errors_count}), "
                f"all blocking errors must be resolved"
            )
            reasons.append("blocking_errors_present")

        # Check field mappings
        if not field_mappings_complete:
            missing_requirements.append("Field mappings are not complete or validated")
            reasons.append("field_mappings_incomplete")

        # Check application readiness
        if total_apps > 0 and apps_ready < (
            total_apps * 0.8
        ):  # 80% of apps should be ready
            missing_requirements.append(
                f"Only {apps_ready}/{total_apps} applications are ready for assessment"
            )
            reasons.append("applications_not_ready")
            recommendations.append(
                "Complete CMDB data collection for remaining applications"
            )

        # Calculate overall score
        scores = []
        weights = []

        scores.append(completeness_score)
        weights.append(0.4)  # 40% weight for completeness

        if data_quality_score is not None:
            scores.append(data_quality_score)
            weights.append(0.3)  # 30% weight for data quality

        # Field mappings score (binary: 1.0 if complete, 0.0 if not)
        scores.append(1.0 if field_mappings_complete else 0.0)
        weights.append(0.2)  # 20% weight for field mappings

        # Application readiness score
        app_readiness_score = (apps_ready / total_apps) if total_apps > 0 else 1.0
        scores.append(app_readiness_score)
        weights.append(0.1)  # 10% weight for app readiness

        # Weighted average
        overall_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        # Adjust score for blocking conditions
        if blocking_errors_count > 0:
            overall_score *= 0.5  # Halve score if blocking errors present

        if critical_gaps_count > self.thresholds.max_critical_gaps:
            overall_score *= 0.7  # Reduce score for too many critical gaps

        # Determine readiness
        is_ready = (
            len(missing_requirements) == 0
            and overall_score >= 0.7  # Overall score threshold
            and completeness_score >= self.thresholds.collection_completeness
        )

        # Generate reason
        if is_ready:
            reason = f"Collection is ready for assessment (score: {overall_score:.2f})"
        else:
            main_reason = reasons[0] if reasons else "requirements_not_met"
            reason = f"Collection not ready: {main_reason} (score: {overall_score:.2f})"

        # Generate recommendations
        if not is_ready:
            if completeness_score < self.thresholds.collection_completeness:
                recommendations.append(
                    "Continue data collection to reach minimum completeness threshold"
                )

            if critical_gaps_count > 0:
                recommendations.append(
                    "Address critical data gaps through manual collection"
                )

            if not field_mappings_complete:
                recommendations.append("Complete and validate field mappings")

        return is_ready, overall_score, reason, missing_requirements, recommendations

    async def _get_agent_confidence(
        self,
        collection_flow: CollectionFlow,
        completeness_score: float,
        data_quality_score: Optional[float],
        critical_gaps_count: int,
    ) -> float:
        """Use tenant-scoped agent to assess confidence in readiness"""

        try:
            # Get readiness assessment agent
            agent = await TenantScopedAgentPool.get_agent(
                self.context, "readiness_assessor", service_registry=None
            )

            # Create assessment prompt
            prompt = f"""
            Assess confidence in collection flow readiness for assessment phase transition.

            Metrics:
            - Collection completeness: {completeness_score:.1%}
            - Data quality score: {data_quality_score:.1% if data_quality_score else 'Not available'}
            - Critical gaps: {critical_gaps_count}
            - Flow status: {collection_flow.status}
            - Progress: {collection_flow.progress_percentage}%

            Return a confidence score between 0.0 and 1.0 based on:
            1. Data completeness and quality
            2. Risk of assessment phase failures
            3. Likelihood of successful migration planning

            Consider tenant-specific requirements and risk tolerance.
            """

            result = await agent.execute(prompt)

            # Parse confidence from agent response
            if isinstance(result, dict) and "confidence" in result:
                confidence = float(result["confidence"])
            elif isinstance(result, (int, float)):
                confidence = float(result)
            else:
                # Try to extract number from string response
                import re

                match = re.search(r"(\d+(?:\.\d+)?)", str(result))
                if match:
                    confidence = float(match.group(1))
                    if confidence > 1.0:
                        confidence = confidence / 100.0  # Convert percentage
                else:
                    confidence = 0.7  # Default fallback

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.warning(
                f"Agent confidence assessment failed: {e}, using fallback calculation"
            )

            # Fallback calculation based on metrics
            confidence = completeness_score

            if data_quality_score is not None:
                confidence = (confidence + data_quality_score) / 2

            # Reduce confidence for critical gaps
            if critical_gaps_count > 0:
                confidence *= 1 - min(0.3, critical_gaps_count * 0.05)

            return max(0.0, min(1.0, confidence))

    def update_thresholds(self, **kwargs) -> None:
        """Update readiness thresholds (for tenant-specific configuration)"""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
            else:
                logger.warning(f"Unknown threshold parameter: {key}")
