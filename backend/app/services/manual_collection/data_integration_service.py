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
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .data_integration_models import (
    DataSource,
    DataPoint,
    IntegratedDataset,
    DataSourceSummary,
    IntegrationReport,
)
from .data_conflict_resolver import DataConflictResolver
from .data_quality_assessor import DataQualityAssessor

logger = logging.getLogger(__name__)


class DataIntegrationService:
    """
    Centralized service for integrating data from multiple collection sources.

    Handles merging, conflict resolution, quality assessment, and unified dataset creation.
    """

    def __init__(self):
        """Initialize integration service with modular components."""
        self.logger = logging.getLogger(__name__)

        # Initialize modular components
        self.conflict_resolver = DataConflictResolver()
        self.quality_assessor = DataQualityAssessor()

        # Integration storage (in production, this would be persistent)
        self._integrated_datasets = {}

    async def integrate_data_sources(
        self,
        application_id: UUID,
        collection_flow_id: str,
        data_sources: Dict[DataSource, Dict[str, Any]],
        integration_config: Optional[Dict[str, Any]] = None,
    ) -> IntegratedDataset:
        """
        Integrate data from multiple sources into unified dataset.

        Args:
            application_id: Target application UUID
            collection_flow_id: Flow identifier for tracking
            data_sources: Dict mapping source types to their data
            integration_config: Optional configuration for integration behavior

        Returns:
            IntegratedDataset with merged and resolved data
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Starting data integration for application {application_id}")

        try:
            # Extract data points from all sources
            all_data_points = await self._extract_data_points(data_sources)

            # Group data points by attribute
            grouped_data = self._group_data_by_attribute(all_data_points)

            # Detect conflicts
            conflicts = await self.conflict_resolver.detect_conflicts(grouped_data)

            # Resolve conflicts
            resolved_conflicts = await self.conflict_resolver.resolve_conflicts(
                conflicts
            )

            # Create final dataset
            final_data_points = {}
            for attr_name, points in grouped_data.items():
                # Check if this attribute has a resolved conflict
                resolved_conflict = next(
                    (c for c in resolved_conflicts if c.attribute_name == attr_name),
                    None,
                )

                if resolved_conflict and resolved_conflict.resolved_value:
                    final_data_points[attr_name] = resolved_conflict.resolved_value
                else:
                    # Use highest confidence data point
                    final_data_points[attr_name] = max(
                        points, key=lambda dp: dp.confidence_score
                    )

            # Calculate quality metrics
            data_points_list = list(final_data_points.values())
            overall_confidence = (
                await self.quality_assessor.calculate_overall_confidence(
                    data_points_list
                )
            )
            completeness_score = (
                await self.quality_assessor.calculate_completeness_score(
                    data_points_list
                )
            )
            critical_coverage = (
                await self.quality_assessor.calculate_critical_attributes_coverage(
                    data_points_list
                )
            )
            quality_level = self.quality_assessor.determine_quality_level(
                completeness_score, overall_confidence, critical_coverage
            )

            # Create integrated dataset
            dataset = IntegratedDataset(
                application_id=application_id,
                data_points=data_points_list,
                conflicts=resolved_conflicts,
                completeness_score=completeness_score,
                quality_level=quality_level,
                critical_attributes_coverage=critical_coverage,
                confidence_score=overall_confidence,
                sixr_readiness_score=0.0,  # Will be calculated
                created_at=start_time,
                last_updated=datetime.utcnow(),
            )

            # Calculate 6R readiness
            dataset.sixr_readiness_score = (
                await self.quality_assessor.assess_6r_readiness(dataset)
            )

            # Store dataset
            self._integrated_datasets[str(application_id)] = dataset

            self.logger.info(
                f"Integration completed for {application_id}. "
                f"Quality: {quality_level.value}, Completeness: {completeness_score:.1f}%"
            )

            return dataset

        except Exception as e:
            self.logger.error(f"Data integration failed for {application_id}: {e}")
            raise

    async def merge_manual_and_automated_data(
        self,
        application_id: UUID,
        manual_data: Dict[str, Any],
        automated_data: Dict[str, Any],
        merge_strategy: str = "prefer_manual",
    ) -> IntegratedDataset:
        """Merge manual collection with automated discovery data."""
        data_sources = {
            DataSource.MANUAL_COLLECTION: manual_data,
            DataSource.AUTOMATED_DISCOVERY: automated_data,
        }

        return await self.integrate_data_sources(
            application_id=application_id,
            collection_flow_id=f"manual_auto_merge_{uuid4()}",
            data_sources=data_sources,
            integration_config={"merge_strategy": merge_strategy},
        )

    async def add_bulk_data_to_integration(
        self,
        application_id: UUID,
        bulk_data: List[Dict[str, Any]],
        existing_dataset: Optional[IntegratedDataset] = None,
    ) -> IntegratedDataset:
        """Add bulk upload data to existing integration."""
        # Convert bulk data to data points
        bulk_data_points = []
        for row in bulk_data:
            for attr_name, value in row.items():
                if value is not None:
                    data_point = DataPoint(
                        attribute_name=attr_name,
                        value=value,
                        source=DataSource.BULK_UPLOAD,
                        confidence_score=0.8,  # Default confidence for bulk data
                        timestamp=datetime.utcnow(),
                        collection_method="bulk_upload",
                        validation_status="pending",
                        metadata={"row_index": bulk_data.index(row)},
                    )
                    bulk_data_points.append(data_point)

        if existing_dataset:
            # Merge with existing data
            all_data_points = existing_dataset.data_points + bulk_data_points

            # Re-run integration process
            grouped_data = self._group_data_by_attribute(all_data_points)
            conflicts = await self.conflict_resolver.detect_conflicts(grouped_data)
            resolved_conflicts = await self.conflict_resolver.resolve_conflicts(
                conflicts
            )

            # Update existing dataset
            existing_dataset.data_points = all_data_points
            existing_dataset.conflicts = resolved_conflicts
            existing_dataset.last_updated = datetime.utcnow()

            # Recalculate metrics
            existing_dataset.confidence_score = (
                await self.quality_assessor.calculate_overall_confidence(
                    all_data_points
                )
            )
            existing_dataset.completeness_score = (
                await self.quality_assessor.calculate_completeness_score(
                    all_data_points
                )
            )
            existing_dataset.critical_attributes_coverage = (
                await self.quality_assessor.calculate_critical_attributes_coverage(
                    all_data_points
                )
            )
            existing_dataset.quality_level = (
                self.quality_assessor.determine_quality_level(
                    existing_dataset.completeness_score,
                    existing_dataset.confidence_score,
                    existing_dataset.critical_attributes_coverage,
                )
            )
            existing_dataset.sixr_readiness_score = (
                await self.quality_assessor.assess_6r_readiness(existing_dataset)
            )

            return existing_dataset
        else:
            # Create new integration with bulk data only
            return await self.integrate_data_sources(
                application_id=application_id,
                collection_flow_id=f"bulk_only_{uuid4()}",
                data_sources={
                    DataSource.BULK_UPLOAD: {"data_points": bulk_data_points}
                },
            )

    async def get_integration_report(
        self, application_id: UUID
    ) -> Optional[IntegrationReport]:
        """Get comprehensive integration report for an application."""
        dataset = self._integrated_datasets.get(str(application_id))
        if not dataset:
            return None

        # Generate recommendations and next actions
        recommendations = await self.quality_assessor.generate_recommendations(dataset)
        next_actions = await self.quality_assessor.generate_next_actions(dataset)

        # Summarize data sources
        sources_summary = self._summarize_data_sources(dataset)

        return IntegrationReport(
            application_id=application_id,
            sources_integrated=sources_summary,
            total_conflicts=len(dataset.conflicts),
            resolved_conflicts=len([c for c in dataset.conflicts if c.resolved_value]),
            pending_conflicts=len(
                [c for c in dataset.conflicts if not c.resolved_value]
            ),
            data_quality_level=dataset.quality_level,
            completeness_score=dataset.completeness_score,
            recommendations=recommendations,
            next_actions=next_actions,
            integration_timestamp=dataset.last_updated,
        )

    async def get_data_gaps(self, application_id: UUID) -> List[Dict[str, Any]]:
        """Get data gaps for an application."""
        dataset = self._integrated_datasets.get(str(application_id))
        if not dataset:
            return []

        return await self.quality_assessor.get_data_gaps(
            application_id, dataset.data_points
        )

    async def export_integrated_data(
        self,
        application_id: UUID,
        export_format: str = "json",
        include_metadata: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """Export integrated data in specified format."""
        dataset = self._integrated_datasets.get(str(application_id))
        if not dataset:
            return {} if export_format == "json" else ""

        # Create export data structure
        export_data = {
            "application_id": str(application_id),
            "integration_timestamp": dataset.last_updated.isoformat(),
            "data_quality": {
                "level": dataset.quality_level.value,
                "completeness_score": dataset.completeness_score,
                "confidence_score": dataset.confidence_score,
                "critical_coverage": dataset.critical_attributes_coverage,
                "sixr_readiness": dataset.sixr_readiness_score,
            },
            "data": {},
        }

        # Add data points
        for dp in dataset.data_points:
            export_data["data"][dp.attribute_name] = dp.value

            if include_metadata:
                export_data["data"][f"{dp.attribute_name}_metadata"] = {
                    "source": dp.source.value,
                    "confidence": dp.confidence_score,
                    "collected_at": dp.timestamp.isoformat(),
                    "validation_status": dp.validation_status,
                }

        if export_format == "json":
            return export_data
        elif export_format == "json_string":
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    async def _extract_data_points(
        self, data_sources: Dict[DataSource, Dict[str, Any]]
    ) -> List[DataPoint]:
        """Extract data points from various source formats."""
        all_data_points = []

        for source_type, source_data in data_sources.items():
            if source_type == DataSource.AUTOMATED_DISCOVERY:
                # Handle automated discovery data
                for attr_name, value in source_data.items():
                    if value is not None:
                        data_point = DataPoint(
                            attribute_name=attr_name,
                            value=value,
                            source=source_type,
                            confidence_score=0.7,  # Default for automated
                            timestamp=datetime.utcnow(),
                            collection_method="automated_discovery",
                            validation_status="auto_validated",
                            metadata={
                                "source_adapter": source_data.get(
                                    "adapter_type", "unknown"
                                )
                            },
                        )
                        all_data_points.append(data_point)

            elif source_type == DataSource.MANUAL_COLLECTION:
                # Handle manual collection data
                for attr_name, value in source_data.items():
                    if value is not None:
                        data_point = DataPoint(
                            attribute_name=attr_name,
                            value=value,
                            source=source_type,
                            confidence_score=0.9,  # Higher confidence for manual
                            timestamp=datetime.utcnow(),
                            collection_method="manual_form",
                            validation_status="user_validated",
                            metadata={"form_id": source_data.get("form_id", "unknown")},
                        )
                        all_data_points.append(data_point)

            elif source_type == DataSource.BULK_UPLOAD:
                # Handle bulk upload data (already converted to data points)
                if "data_points" in source_data:
                    all_data_points.extend(source_data["data_points"])

        return all_data_points

    def _group_data_by_attribute(
        self, data_points: List[DataPoint]
    ) -> Dict[str, List[DataPoint]]:
        """Group data points by attribute name."""
        grouped = defaultdict(list)
        for dp in data_points:
            grouped[dp.attribute_name].append(dp)
        return dict(grouped)

    def _summarize_data_sources(
        self, dataset: IntegratedDataset
    ) -> List[DataSourceSummary]:
        """Create summary of data sources used in integration."""
        source_stats = defaultdict(
            lambda: {"count": 0, "confidence_sum": 0.0, "timestamps": []}
        )

        for dp in dataset.data_points:
            stats = source_stats[dp.source]
            stats["count"] += 1
            stats["confidence_sum"] += dp.confidence_score
            stats["timestamps"].append(dp.timestamp)

        summaries = []
        for source, stats in source_stats.items():
            avg_confidence = (
                stats["confidence_sum"] / stats["count"] if stats["count"] > 0 else 0.0
            )
            latest_timestamp = (
                max(stats["timestamps"]) if stats["timestamps"] else datetime.utcnow()
            )

            summary = DataSourceSummary(
                source=source,
                total_attributes=stats["count"],
                coverage_percentage=(stats["count"] / len(dataset.data_points)) * 100,
                average_confidence=avg_confidence,
                collection_timestamp=latest_timestamp,
                method_details={"attribute_count": stats["count"]},
            )
            summaries.append(summary)

        return summaries
