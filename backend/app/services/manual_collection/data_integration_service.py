"""
Data Integration Service for Manual and Automated Data

Integrates data collected from manual forms, bulk uploads, and automated adapters
into a unified dataset for 6R analysis. Handles data merging, conflict resolution,
and quality scoring.

Agent Team B3 - Task B3.6
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import numpy as np

from ..collection_flow.data_transformation import DataTransformationService
from ..collection_flow.quality_scoring import (
    ConfidenceAssessmentService,
    QualityAssessmentService,
)
from .validation_service import FormValidationResult


class DataSource(str, Enum):
    """Sources of collected data"""

    AUTOMATED_ADAPTER = "automated_adapter"
    MANUAL_FORM = "manual_form"
    BULK_UPLOAD = "bulk_upload"
    TEMPLATE_APPLICATION = "template_application"
    LEGACY_IMPORT = "legacy_import"
    EXTERNAL_API = "external_api"


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving data conflicts"""

    HIGHEST_CONFIDENCE = "highest_confidence"
    MOST_RECENT = "most_recent"
    MANUAL_OVERRIDE = "manual_override"
    AUTOMATED_PRIORITY = "automated_priority"
    MERGE_VALUES = "merge_values"
    USER_REVIEW = "user_review"


class DataQualityLevel(str, Enum):
    """Data quality classification levels"""

    EXCELLENT = "excellent"  # >90% confidence
    GOOD = "good"  # 70-90% confidence
    FAIR = "fair"  # 50-70% confidence
    POOR = "poor"  # 30-50% confidence
    INSUFFICIENT = "insufficient"  # <30% confidence


@dataclass
class DataPoint:
    """Individual data point with metadata"""

    attribute_name: str
    value: Any
    source: DataSource
    confidence_score: float
    collected_at: datetime
    source_id: str  # ID of source (form_id, adapter_id, etc.)
    validation_status: str
    metadata: Dict[str, Any]
    normalized_value: Optional[Any] = None


@dataclass
class DataConflict:
    """Conflict between data sources"""

    attribute_name: str
    conflicting_values: List[DataPoint]
    resolution_strategy: ConflictResolutionStrategy
    resolved_value: Optional[DataPoint] = None
    resolution_confidence: float = 0.0
    requires_user_review: bool = False
    resolution_metadata: Optional[Dict[str, Any]] = None


@dataclass
class IntegratedDataset:
    """Integrated dataset for an application"""

    application_id: UUID
    collection_flow_id: str
    data_points: Dict[str, DataPoint]  # attribute_name -> DataPoint
    conflicts: List[DataConflict]
    data_sources: Dict[DataSource, List[str]]  # source_type -> source_ids
    overall_confidence_score: float
    completeness_score: float
    quality_level: DataQualityLevel
    integration_timestamp: datetime
    critical_attributes_coverage: float
    readiness_for_6r_analysis: bool
    integration_metadata: Dict[str, Any]


@dataclass
class DataSourceSummary:
    """Summary of data from a specific source"""

    source_type: DataSource
    source_id: str
    attributes_contributed: List[str]
    data_quality_score: float
    confidence_score: float
    collection_timestamp: datetime
    record_count: int
    metadata: Dict[str, Any]


@dataclass
class IntegrationReport:
    """Report on data integration process"""

    application_id: UUID
    total_attributes_collected: int
    critical_attributes_coverage: int
    data_sources_used: List[DataSourceSummary]
    conflicts_detected: int
    conflicts_resolved: int
    overall_quality_score: float
    recommendations: List[str]
    next_actions: List[str]
    integration_duration_seconds: float


class DataIntegrationService:
    """Service for integrating manual and automated data collection results"""

    # Critical attributes framework (from ADCS specifications)
    CRITICAL_ATTRIBUTES = {
        # Infrastructure (6 attributes)
        "os_version": {"weight": 0.05, "category": "infrastructure"},
        "specifications": {"weight": 0.05, "category": "infrastructure"},
        "network_config": {"weight": 0.04, "category": "infrastructure"},
        "virtualization": {"weight": 0.04, "category": "infrastructure"},
        "performance_baseline": {"weight": 0.04, "category": "infrastructure"},
        "availability_requirements": {"weight": 0.03, "category": "infrastructure"},
        # Application (8 attributes)
        "technology_stack": {"weight": 0.08, "category": "application"},
        "architecture_pattern": {"weight": 0.07, "category": "application"},
        "integration_dependencies": {"weight": 0.06, "category": "application"},
        "data_characteristics": {"weight": 0.06, "category": "application"},
        "user_load_patterns": {"weight": 0.05, "category": "application"},
        "business_logic_complexity": {"weight": 0.05, "category": "application"},
        "configuration_complexity": {"weight": 0.04, "category": "application"},
        "security_requirements": {"weight": 0.04, "category": "application"},
        # Business Context (4 attributes)
        "business_criticality": {"weight": 0.08, "category": "business"},
        "change_tolerance": {"weight": 0.05, "category": "business"},
        "compliance_constraints": {"weight": 0.04, "category": "business"},
        "stakeholder_impact": {"weight": 0.03, "category": "business"},
        # Technical Debt (4 attributes)
        "code_quality": {"weight": 0.03, "category": "technical_debt"},
        "security_vulnerabilities": {"weight": 0.03, "category": "technical_debt"},
        "eol_technology": {"weight": 0.02, "category": "technical_debt"},
        "documentation_quality": {"weight": 0.02, "category": "technical_debt"},
    }

    # Source reliability scores for conflict resolution
    SOURCE_RELIABILITY = {
        DataSource.AUTOMATED_ADAPTER: 0.9,
        DataSource.MANUAL_FORM: 0.8,
        DataSource.BULK_UPLOAD: 0.7,
        DataSource.TEMPLATE_APPLICATION: 0.6,
        DataSource.LEGACY_IMPORT: 0.5,
        DataSource.EXTERNAL_API: 0.8,
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_transformation_service = DataTransformationService()
        self.quality_service = QualityAssessmentService()
        self.confidence_service = ConfidenceAssessmentService()
        self._integrated_datasets = {}  # application_id -> IntegratedDataset

    async def integrate_data_sources(
        self,
        application_id: UUID,
        collection_flow_id: str,
        data_sources: Dict[DataSource, List[Dict[str, Any]]],
        conflict_resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.HIGHEST_CONFIDENCE,
    ) -> IntegratedDataset:
        """
        Integrate data from multiple sources into unified dataset.

        Core implementation of B3.6 - data integration services for manual and automated data.
        Merges data from automated adapters, manual forms, bulk uploads, and templates.
        """
        start_time = datetime.now()

        self.logger.info(f"Integrating data sources for application {application_id}")

        # Extract and normalize data points from all sources
        all_data_points = await self._extract_data_points(data_sources)

        # Group data points by attribute
        grouped_data = self._group_data_by_attribute(all_data_points)

        # Detect and resolve conflicts
        conflicts = await self._detect_conflicts(grouped_data)
        resolved_data = await self._resolve_conflicts(
            conflicts, conflict_resolution_strategy
        )

        # Calculate confidence and completeness scores
        overall_confidence = await self._calculate_overall_confidence(resolved_data)
        completeness_score = await self._calculate_completeness_score(resolved_data)
        critical_coverage = await self._calculate_critical_attributes_coverage(
            resolved_data
        )

        # Determine data quality level
        quality_level = self._determine_quality_level(
            overall_confidence, completeness_score
        )

        # Assess readiness for 6R analysis
        readiness = await self._assess_6r_readiness(
            resolved_data, overall_confidence, completeness_score
        )

        # Create integrated dataset
        dataset = IntegratedDataset(
            application_id=application_id,
            collection_flow_id=collection_flow_id,
            data_points=resolved_data,
            conflicts=conflicts,
            data_sources=self._summarize_data_sources(data_sources),
            overall_confidence_score=overall_confidence,
            completeness_score=completeness_score,
            quality_level=quality_level,
            integration_timestamp=datetime.now(),
            critical_attributes_coverage=critical_coverage,
            readiness_for_6r_analysis=readiness,
            integration_metadata={
                "integration_duration_seconds": (
                    datetime.now() - start_time
                ).total_seconds(),
                "total_data_points": len(all_data_points),
                "conflicts_detected": len(conflicts),
                "resolution_strategy": conflict_resolution_strategy.value,
            },
        )

        # Store integrated dataset
        self._integrated_datasets[str(application_id)] = dataset

        self.logger.info(
            f"Data integration completed for {application_id}: "
            f"confidence={overall_confidence:.2f}, completeness={completeness_score:.1f}%, "
            f"quality={quality_level.value}"
        )

        return dataset

    async def merge_manual_and_automated_data(
        self,
        application_id: UUID,
        automated_data: Dict[str, Any],
        manual_data: Dict[str, Any],
        form_validation: Optional[FormValidationResult] = None,
    ) -> IntegratedDataset:
        """
        Merge automated adapter data with manual form responses.

        Specialized integration for the common case of combining automated
        collection with manual gap-filling.
        """
        self.logger.info(f"Merging manual and automated data for {application_id}")

        # Prepare data sources
        data_sources = {}

        if automated_data:
            data_sources[DataSource.AUTOMATED_ADAPTER] = [automated_data]

        if manual_data:
            # Enhance manual data with validation results
            enhanced_manual_data = manual_data.copy()
            if form_validation:
                enhanced_manual_data["_validation_metadata"] = {
                    "overall_confidence": form_validation.overall_confidence_score,
                    "completion_percentage": form_validation.completion_percentage,
                    "field_validations": {
                        field_id: {
                            "is_valid": result.is_valid,
                            "confidence_score": result.confidence_score,
                        }
                        for field_id, result in form_validation.field_results.items()
                    },
                }
            data_sources[DataSource.MANUAL_FORM] = [enhanced_manual_data]

        # Use automated data priority for conflicts (automated is typically more reliable)
        return await self.integrate_data_sources(
            application_id=application_id,
            collection_flow_id=f"merge_{uuid4()}",
            data_sources=data_sources,
            conflict_resolution_strategy=ConflictResolutionStrategy.AUTOMATED_PRIORITY,
        )

    async def add_bulk_data_to_integration(
        self,
        application_id: UUID,
        bulk_data: List[Dict[str, Any]],
        existing_dataset: Optional[IntegratedDataset] = None,
    ) -> IntegratedDataset:
        """Add bulk upload data to existing integration"""

        if existing_dataset:
            # Re-integrate with additional bulk data
            current_sources = existing_dataset.data_sources.copy()
            current_sources[DataSource.BULK_UPLOAD] = [f"bulk_{uuid4()}"]

            # Convert existing data points back to source format for re-integration
            existing_data = {}
            for source_type, source_ids in existing_dataset.data_sources.items():
                if source_type != DataSource.BULK_UPLOAD:
                    source_data = {}
                    for attr_name, data_point in existing_dataset.data_points.items():
                        if data_point.source == source_type:
                            source_data[attr_name] = data_point.value
                    existing_data[source_type] = [source_data] if source_data else []

            # Add bulk data
            existing_data[DataSource.BULK_UPLOAD] = bulk_data

            return await self.integrate_data_sources(
                application_id=application_id,
                collection_flow_id=existing_dataset.collection_flow_id,
                data_sources=existing_data,
            )
        else:
            # Create new integration with bulk data only
            return await self.integrate_data_sources(
                application_id=application_id,
                collection_flow_id=f"bulk_{uuid4()}",
                data_sources={DataSource.BULK_UPLOAD: bulk_data},
            )

    async def get_integration_report(
        self, application_id: UUID
    ) -> Optional[IntegrationReport]:
        """Generate comprehensive integration report"""

        dataset = self._integrated_datasets.get(str(application_id))
        if not dataset:
            return None

        # Calculate metrics
        total_attributes = len(dataset.data_points)
        critical_coverage = sum(
            1
            for attr_name in dataset.data_points.keys()
            if attr_name in self.CRITICAL_ATTRIBUTES
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations(dataset)
        next_actions = await self._generate_next_actions(dataset)

        # Summarize data sources
        source_summaries = []
        for source_type, source_ids in dataset.data_sources.items():
            for source_id in source_ids:
                contributed_attrs = [
                    attr_name
                    for attr_name, data_point in dataset.data_points.items()
                    if data_point.source == source_type
                    and data_point.source_id == source_id
                ]

                summary = DataSourceSummary(
                    source_type=source_type,
                    source_id=source_id,
                    attributes_contributed=contributed_attrs,
                    data_quality_score=self.SOURCE_RELIABILITY[source_type],
                    confidence_score=(
                        np.mean(
                            [
                                dataset.data_points[attr].confidence_score
                                for attr in contributed_attrs
                            ]
                        )
                        if contributed_attrs
                        else 0.0
                    ),
                    collection_timestamp=datetime.now(),  # Would be actual timestamp
                    record_count=len(contributed_attrs),
                    metadata={},
                )
                source_summaries.append(summary)

        return IntegrationReport(
            application_id=application_id,
            total_attributes_collected=total_attributes,
            critical_attributes_coverage=critical_coverage,
            data_sources_used=source_summaries,
            conflicts_detected=len(dataset.conflicts),
            conflicts_resolved=len([c for c in dataset.conflicts if c.resolved_value]),
            overall_quality_score=dataset.overall_confidence_score,
            recommendations=recommendations,
            next_actions=next_actions,
            integration_duration_seconds=dataset.integration_metadata.get(
                "integration_duration_seconds", 0.0
            ),
        )

    async def get_data_gaps(self, application_id: UUID) -> List[Dict[str, Any]]:
        """Identify missing critical attributes for an application"""

        dataset = self._integrated_datasets.get(str(application_id))
        if not dataset:
            return []

        gaps = []
        collected_attributes = set(dataset.data_points.keys())

        for attr_name, attr_config in self.CRITICAL_ATTRIBUTES.items():
            if attr_name not in collected_attributes:
                gaps.append(
                    {
                        "attribute_name": attr_name,
                        "category": attr_config["category"],
                        "weight": attr_config["weight"],
                        "impact_on_confidence": attr_config["weight"],
                        "priority": (
                            "high" if attr_config["weight"] >= 0.05 else "medium"
                        ),
                        "collection_methods": self._suggest_collection_methods(
                            attr_name
                        ),
                    }
                )

        # Sort by weight (impact)
        gaps.sort(key=lambda x: x["weight"], reverse=True)
        return gaps

    async def export_integrated_data(
        self, application_id: UUID, format: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """Export integrated dataset in specified format"""

        dataset = self._integrated_datasets.get(str(application_id))
        if not dataset:
            return {} if format == "json" else ""

        if format == "json":
            return {
                "application_id": str(dataset.application_id),
                "collection_flow_id": dataset.collection_flow_id,
                "integration_timestamp": dataset.integration_timestamp.isoformat(),
                "overall_confidence_score": dataset.overall_confidence_score,
                "completeness_score": dataset.completeness_score,
                "quality_level": dataset.quality_level.value,
                "readiness_for_6r_analysis": dataset.readiness_for_6r_analysis,
                "data_points": {
                    attr_name: {
                        "value": point.value,
                        "normalized_value": point.normalized_value,
                        "source": point.source.value,
                        "confidence_score": point.confidence_score,
                        "collected_at": point.collected_at.isoformat(),
                        "validation_status": point.validation_status,
                    }
                    for attr_name, point in dataset.data_points.items()
                },
                "conflicts": [
                    {
                        "attribute_name": conflict.attribute_name,
                        "conflicting_values": len(conflict.conflicting_values),
                        "resolution_strategy": conflict.resolution_strategy.value,
                        "resolved": conflict.resolved_value is not None,
                        "requires_user_review": conflict.requires_user_review,
                    }
                    for conflict in dataset.conflicts
                ],
            }

        return json.dumps(dataset, default=str, indent=2)

    async def _extract_data_points(
        self, data_sources: Dict[DataSource, List[Dict[str, Any]]]
    ) -> List[DataPoint]:
        """Extract and normalize data points from all sources"""

        all_points = []

        for source_type, source_data_list in data_sources.items():
            for idx, source_data in enumerate(source_data_list):
                source_id = f"{source_type.value}_{idx}"

                # Extract validation metadata if present
                validation_metadata = source_data.get("_validation_metadata", {})

                for field_name, value in source_data.items():
                    if field_name.startswith("_"):  # Skip metadata fields
                        continue

                    # Determine attribute name (remove field_ prefix if present)
                    attr_name = (
                        field_name.replace("field_", "")
                        if field_name.startswith("field_")
                        else field_name
                    )

                    # Calculate confidence score
                    confidence_score = self._calculate_data_point_confidence(
                        source_type,
                        value,
                        validation_metadata.get("field_validations", {}).get(
                            field_name, {}
                        ),
                    )

                    # Normalize value
                    normalized_value = (
                        await self.data_transformation_service.normalize_collected_data(
                            {attr_name: value}
                        )
                    )

                    data_point = DataPoint(
                        attribute_name=attr_name,
                        value=value,
                        source=source_type,
                        confidence_score=confidence_score,
                        collected_at=datetime.now(),
                        source_id=source_id,
                        validation_status="valid",  # Would come from actual validation
                        metadata={"original_field_name": field_name},
                        normalized_value=normalized_value.get(attr_name, value),
                    )

                    all_points.append(data_point)

        return all_points

    def _group_data_by_attribute(
        self, data_points: List[DataPoint]
    ) -> Dict[str, List[DataPoint]]:
        """Group data points by attribute name"""
        grouped = defaultdict(list)
        for point in data_points:
            grouped[point.attribute_name].append(point)
        return dict(grouped)

    async def _detect_conflicts(
        self, grouped_data: Dict[str, List[DataPoint]]
    ) -> List[DataConflict]:
        """Detect conflicts between data sources"""

        conflicts = []

        for attr_name, data_points in grouped_data.items():
            if len(data_points) <= 1:
                continue  # No conflict possible

            # Check if values are significantly different
            unique_values = set(
                str(point.normalized_value or point.value).lower().strip()
                for point in data_points
            )

            if len(unique_values) > 1:
                # Conflict detected
                conflict = DataConflict(
                    attribute_name=attr_name,
                    conflicting_values=data_points,
                    resolution_strategy=ConflictResolutionStrategy.HIGHEST_CONFIDENCE,
                    requires_user_review=self._requires_user_review(
                        attr_name, data_points
                    ),
                )
                conflicts.append(conflict)

        return conflicts

    async def _resolve_conflicts(
        self, conflicts: List[DataConflict], strategy: ConflictResolutionStrategy
    ) -> Dict[str, DataPoint]:
        """Resolve conflicts using specified strategy"""

        resolved_data = {}

        for conflict in conflicts:
            if strategy == ConflictResolutionStrategy.HIGHEST_CONFIDENCE:
                resolved_point = max(
                    conflict.conflicting_values, key=lambda p: p.confidence_score
                )
            elif strategy == ConflictResolutionStrategy.MOST_RECENT:
                resolved_point = max(
                    conflict.conflicting_values, key=lambda p: p.collected_at
                )
            elif strategy == ConflictResolutionStrategy.AUTOMATED_PRIORITY:
                # Prefer automated sources
                automated_points = [
                    p
                    for p in conflict.conflicting_values
                    if p.source == DataSource.AUTOMATED_ADAPTER
                ]
                if automated_points:
                    resolved_point = max(
                        automated_points, key=lambda p: p.confidence_score
                    )
                else:
                    resolved_point = max(
                        conflict.conflicting_values, key=lambda p: p.confidence_score
                    )
            elif strategy == ConflictResolutionStrategy.MANUAL_OVERRIDE:
                # Prefer manual sources
                manual_points = [
                    p
                    for p in conflict.conflicting_values
                    if p.source == DataSource.MANUAL_FORM
                ]
                if manual_points:
                    resolved_point = max(
                        manual_points, key=lambda p: p.confidence_score
                    )
                else:
                    resolved_point = max(
                        conflict.conflicting_values, key=lambda p: p.confidence_score
                    )
            else:
                # Default to highest confidence
                resolved_point = max(
                    conflict.conflicting_values, key=lambda p: p.confidence_score
                )

            conflict.resolved_value = resolved_point
            conflict.resolution_confidence = resolved_point.confidence_score
            resolved_data[conflict.attribute_name] = resolved_point

        return resolved_data

    async def _calculate_overall_confidence(
        self, data_points: Dict[str, DataPoint]
    ) -> float:
        """Calculate overall confidence score using critical attributes weighting"""

        if not data_points:
            return 0.0

        total_weight = 0.0
        weighted_confidence = 0.0

        for attr_name, data_point in data_points.items():
            if attr_name in self.CRITICAL_ATTRIBUTES:
                weight = self.CRITICAL_ATTRIBUTES[attr_name]["weight"]
                total_weight += weight
                weighted_confidence += data_point.confidence_score * weight
            else:
                # Non-critical attributes get minimal weight
                total_weight += 0.001
                weighted_confidence += data_point.confidence_score * 0.001

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    async def _calculate_completeness_score(
        self, data_points: Dict[str, DataPoint]
    ) -> float:
        """Calculate completeness score based on critical attributes coverage"""

        critical_attributes_collected = sum(
            1
            for attr_name in data_points.keys()
            if attr_name in self.CRITICAL_ATTRIBUTES
        )

        total_critical_attributes = len(self.CRITICAL_ATTRIBUTES)

        return (critical_attributes_collected / total_critical_attributes) * 100

    async def _calculate_critical_attributes_coverage(
        self, data_points: Dict[str, DataPoint]
    ) -> float:
        """Calculate critical attributes coverage percentage"""

        total_weight = sum(attr["weight"] for attr in self.CRITICAL_ATTRIBUTES.values())
        collected_weight = sum(
            self.CRITICAL_ATTRIBUTES[attr_name]["weight"]
            for attr_name in data_points.keys()
            if attr_name in self.CRITICAL_ATTRIBUTES
        )

        return (collected_weight / total_weight) * 100 if total_weight > 0 else 0.0

    def _determine_quality_level(
        self, confidence_score: float, completeness_score: float
    ) -> DataQualityLevel:
        """Determine overall data quality level"""

        # Combined score considers both confidence and completeness
        combined_score = confidence_score * 0.7 + completeness_score / 100 * 0.3

        if combined_score >= 0.9:
            return DataQualityLevel.EXCELLENT
        elif combined_score >= 0.7:
            return DataQualityLevel.GOOD
        elif combined_score >= 0.5:
            return DataQualityLevel.FAIR
        elif combined_score >= 0.3:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.INSUFFICIENT

    async def _assess_6r_readiness(
        self,
        data_points: Dict[str, DataPoint],
        confidence_score: float,
        completeness_score: float,
    ) -> bool:
        """Assess if data is ready for 6R analysis"""

        # Minimum thresholds for 6R readiness
        min_confidence = 0.7
        min_completeness = 60.0  # 60% of critical attributes
        min_high_impact_attributes = 3  # At least 3 high-impact attributes

        # Check high-impact attributes (weight >= 0.05)
        high_impact_collected = sum(
            1
            for attr_name in data_points.keys()
            if attr_name in self.CRITICAL_ATTRIBUTES
            and self.CRITICAL_ATTRIBUTES[attr_name]["weight"] >= 0.05
        )

        return (
            confidence_score >= min_confidence
            and completeness_score >= min_completeness
            and high_impact_collected >= min_high_impact_attributes
        )

    def _calculate_data_point_confidence(
        self, source_type: DataSource, value: Any, validation_info: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for individual data point"""

        base_confidence = self.SOURCE_RELIABILITY[source_type]

        # Adjust based on validation results
        if validation_info:
            if validation_info.get("is_valid", True):
                validation_confidence = validation_info.get("confidence_score", 0.8)
                base_confidence = (base_confidence + validation_confidence) / 2
            else:
                base_confidence *= 0.5  # Reduce confidence for invalid data

        # Adjust based on value quality
        if value and str(value).strip():
            value_str = str(value).strip()
            if len(value_str) > 10:  # Detailed values get higher confidence
                base_confidence += 0.1
            if len(value_str) < 3:  # Very short values get lower confidence
                base_confidence -= 0.1
        else:
            base_confidence = 0.0  # Empty values have no confidence

        return max(0.0, min(1.0, base_confidence))

    def _requires_user_review(
        self, attr_name: str, data_points: List[DataPoint]
    ) -> bool:
        """Determine if conflict requires user review"""

        # High-impact attributes always require review
        if (
            attr_name in self.CRITICAL_ATTRIBUTES
            and self.CRITICAL_ATTRIBUTES[attr_name]["weight"] >= 0.06
        ):
            return True

        # Check confidence difference
        confidences = [point.confidence_score for point in data_points]
        if max(confidences) - min(confidences) < 0.2:  # Close confidence scores
            return True

        # Check source types
        sources = {point.source for point in data_points}
        if (
            DataSource.MANUAL_FORM in sources
            and DataSource.AUTOMATED_ADAPTER in sources
        ):
            return True  # Manual vs automated always requires review

        return False

    def _summarize_data_sources(
        self, data_sources: Dict[DataSource, List[Dict[str, Any]]]
    ) -> Dict[DataSource, List[str]]:
        """Summarize data sources"""
        summary = {}
        for source_type, source_data_list in data_sources.items():
            source_ids = [
                f"{source_type.value}_{idx}" for idx in range(len(source_data_list))
            ]
            summary[source_type] = source_ids
        return summary

    async def _generate_recommendations(self, dataset: IntegratedDataset) -> List[str]:
        """Generate recommendations based on integration results"""

        recommendations = []

        if dataset.overall_confidence_score < 0.7:
            recommendations.append(
                "Consider collecting additional manual data to improve confidence scores"
            )

        if dataset.completeness_score < 70:
            recommendations.append(
                "Focus on collecting missing critical attributes for better 6R analysis"
            )

        if len(dataset.conflicts) > 0:
            unresolved_conflicts = [
                c for c in dataset.conflicts if not c.resolved_value
            ]
            if unresolved_conflicts:
                recommendations.append(
                    f"Review and resolve {len(unresolved_conflicts)} data conflicts"
                )

        if not dataset.readiness_for_6r_analysis:
            recommendations.append(
                "Data quality needs improvement before proceeding with 6R analysis"
            )

        return recommendations

    async def _generate_next_actions(self, dataset: IntegratedDataset) -> List[str]:
        """Generate next action items"""

        actions = []

        if dataset.readiness_for_6r_analysis:
            actions.append("Proceed with 6R analysis using integrated dataset")
        else:
            actions.append("Continue data collection to meet 6R analysis requirements")

        # Check for specific gaps
        critical_gaps = []
        for attr_name, attr_config in self.CRITICAL_ATTRIBUTES.items():
            if attr_name not in dataset.data_points and attr_config["weight"] >= 0.05:
                critical_gaps.append(attr_name)

        if critical_gaps:
            actions.append(
                f"Collect data for high-impact attributes: {', '.join(critical_gaps[:3])}"
            )

        return actions

    def _suggest_collection_methods(self, attr_name: str) -> List[str]:
        """Suggest collection methods for missing attribute"""

        methods = ["manual_form"]  # Always possible

        if attr_name in ["os_version", "specifications", "network_config"]:
            methods.append("automated_scan")

        if attr_name in ["technology_stack", "architecture_pattern"]:
            methods.append("code_analysis")

        methods.append("bulk_upload")

        return methods
