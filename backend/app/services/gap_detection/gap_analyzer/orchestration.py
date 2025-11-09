"""
GapAnalyzer orchestration - Main analyze_asset logic.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gap_detection.schemas import (
    ComprehensiveGapReport,
    FieldGap,
    GapPriority,
)

logger = logging.getLogger(__name__)


class OrchestrationMixin:
    """Mixin for main orchestration logic."""

    async def analyze_asset(
        self,
        asset: Any,
        application: Optional[Any],
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,
    ) -> ComprehensiveGapReport:
        """
        Orchestrate all inspectors to analyze a single asset.

        This method runs all 5 inspectors in parallel using asyncio.gather() for
        optimal performance, then aggregates results into a comprehensive report.

        Steps:
        1. Get context-aware requirements from RequirementsEngine
        2. Run all 5 inspectors in parallel (asyncio.gather)
        3. Calculate weighted completeness score
        4. Prioritize gaps by business impact (priority 1/2/3)
        5. Determine assessment readiness (ready if completeness >= threshold)
        6. Return comprehensive report

        Args:
            asset: Asset SQLAlchemy model to analyze
            application: Optional CanonicalApplication model
            client_account_id: Tenant client account UUID (for standards query)
            engagement_id: Engagement UUID (for standards query)
            db: AsyncSession for StandardsInspector database queries

        Returns:
            ComprehensiveGapReport with:
            - All 5 inspector reports
            - Weighted completeness score
            - Prioritized gaps (critical/high/medium)
            - Assessment readiness determination
            - Readiness blockers if not ready

        Raises:
            ValueError: If asset is None
            Exception: If inspectors fail or database errors occur

        Performance:
            - Target: <50ms per asset
            - Parallel execution with asyncio.gather()
            - RequirementsEngine uses LRU cache (<1ms lookups)
        """
        if asset is None:
            raise ValueError("Asset cannot be None")

        logger.info(
            f"Starting gap analysis for asset {asset.id}",
            extra={
                "asset_id": str(asset.id),
                "asset_name": getattr(asset, "asset_name", "unknown"),
                "asset_type": getattr(asset, "asset_type", "unknown"),
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )

        # Step 1: Get context-aware requirements
        requirements = await self._get_requirements(asset)

        # Step 2: Run all 5 inspectors in parallel
        (
            column_gaps,
            enrichment_gaps,
            jsonb_gaps,
            application_gaps,
            standards_gaps,
        ) = await asyncio.gather(
            self.column_inspector.inspect(
                asset=asset,
                application=application,
                requirements=requirements,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=None,  # ColumnInspector doesn't need DB
            ),
            self.enrichment_inspector.inspect(
                asset=asset,
                application=application,
                requirements=requirements,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=None,  # EnrichmentInspector uses eager-loaded relationships
            ),
            self.jsonb_inspector.inspect(
                asset=asset,
                application=application,
                requirements=requirements,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=None,  # JSONBInspector doesn't need DB
            ),
            self.application_inspector.inspect(
                asset=asset,
                application=application,
                requirements=requirements,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=None,  # ApplicationInspector doesn't need DB
            ),
            self.standards_inspector.inspect(
                asset=asset,
                application=application,
                requirements=requirements,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=db,  # StandardsInspector queries database
            ),
        )

        logger.debug(
            f"All inspectors completed for asset {asset.id}",
            extra={
                "asset_id": str(asset.id),
                "column_completeness": column_gaps.completeness_score,
                "enrichment_completeness": enrichment_gaps.completeness_score,
                "jsonb_completeness": jsonb_gaps.completeness_score,
                "application_completeness": application_gaps.completeness_score,
                "standards_completeness": standards_gaps.completeness_score,
            },
        )

        # Step 3: Calculate weighted completeness
        overall_completeness, weighted_scores = self._calculate_weighted_completeness(
            column_gaps=column_gaps,
            enrichment_gaps=enrichment_gaps,
            jsonb_gaps=jsonb_gaps,
            application_gaps=application_gaps,
            standards_gaps=standards_gaps,
            requirements=requirements,
        )

        # Step 4: Prioritize gaps by business impact
        critical_gaps, high_priority_gaps, medium_priority_gaps = self._prioritize_gaps(
            column_gaps=column_gaps,
            enrichment_gaps=enrichment_gaps,
            jsonb_gaps=jsonb_gaps,
            application_gaps=application_gaps,
            standards_gaps=standards_gaps,
        )

        # Step 5: Determine assessment readiness
        is_ready, readiness_blockers = self._determine_readiness(
            overall_completeness=overall_completeness,
            threshold=requirements.completeness_threshold,
            critical_gaps=critical_gaps,
            standards_gaps=standards_gaps,
        )

        # Step 5.5: Aggregate all gaps from inspector reports into FieldGap objects
        all_gaps = self._aggregate_all_gaps(
            column_gaps=column_gaps,
            enrichment_gaps=enrichment_gaps,
            jsonb_gaps=jsonb_gaps,
            application_gaps=application_gaps,
            standards_gaps=standards_gaps,
        )

        # Step 6: Build comprehensive report
        report = ComprehensiveGapReport(
            # Inspector reports
            column_gaps=column_gaps,
            enrichment_gaps=enrichment_gaps,
            jsonb_gaps=jsonb_gaps,
            application_gaps=application_gaps,
            standards_gaps=standards_gaps,
            # Weighted completeness
            overall_completeness=overall_completeness,
            weighted_scores=weighted_scores,
            # Prioritized gaps
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            medium_priority_gaps=medium_priority_gaps,
            all_gaps=all_gaps,  # ✅ Populated from inspector aggregation
            # Assessment readiness
            is_ready_for_assessment=is_ready,
            readiness_blockers=readiness_blockers,
            completeness_threshold=requirements.completeness_threshold,
            # Metadata
            asset_id=str(asset.id),
            asset_name=getattr(asset, "name", getattr(asset, "asset_name", "Unknown")),
            asset_type=getattr(asset, "asset_type", "other"),
            analyzed_at=datetime.utcnow().isoformat() + "Z",
        )

        logger.info(
            f"Gap analysis complete for asset {asset.id}",
            extra={
                "asset_id": str(asset.id),
                "overall_completeness": overall_completeness,
                "is_ready_for_assessment": is_ready,
                "critical_gaps_count": len(critical_gaps),
                "high_priority_gaps_count": len(high_priority_gaps),
                "medium_priority_gaps_count": len(medium_priority_gaps),
                "all_gaps_count": len(all_gaps),
            },
        )

        return report

    def _aggregate_all_gaps(
        self,
        column_gaps,
        enrichment_gaps,
        jsonb_gaps,
        application_gaps,
        standards_gaps,
    ):
        """
        Aggregate all gaps from inspector reports into FieldGap objects.

        Converts string-based gap lists from each inspector into structured
        FieldGap objects with priority levels and reasons.

        Args:
            column_gaps: ColumnGapReport
            enrichment_gaps: EnrichmentGapReport
            jsonb_gaps: JSONBGapReport
            application_gaps: ApplicationGapReport
            standards_gaps: StandardsGapReport

        Returns:
            List[FieldGap]: Complete list of all gaps across all layers
        """
        all_gaps = []

        # From column gaps (CRITICAL - missing attributes are blockers)
        for field in column_gaps.missing_attributes:
            all_gaps.append(
                FieldGap(
                    field_name=field,
                    layer="column",
                    priority=GapPriority.CRITICAL,
                    reason="Required column missing or not present",
                )
            )

        # From column gaps (HIGH - empty attributes are important)
        for field in column_gaps.empty_attributes:
            all_gaps.append(
                FieldGap(
                    field_name=field,
                    layer="column",
                    priority=GapPriority.HIGH,
                    reason="Column exists but has empty value",
                )
            )

        # From column gaps (MEDIUM - null attributes can often be optional)
        for field in column_gaps.null_attributes:
            all_gaps.append(
                FieldGap(
                    field_name=field,
                    layer="column",
                    priority=GapPriority.MEDIUM,
                    reason="Column has NULL value",
                )
            )

        # From enrichment gaps (HIGH - missing tables block comprehensive assessment)
        for table in enrichment_gaps.missing_tables:
            all_gaps.append(
                FieldGap(
                    field_name=table,
                    layer="enrichment",
                    priority=GapPriority.HIGH,
                    reason="Enrichment table not populated",
                )
            )

        # From enrichment gaps (MEDIUM - incomplete tables)
        for table, fields in enrichment_gaps.incomplete_tables.items():
            for field in fields:
                all_gaps.append(
                    FieldGap(
                        field_name=f"{table}.{field}",
                        layer="enrichment",
                        priority=GapPriority.MEDIUM,
                        reason=f"Field missing in {table} enrichment table",
                    )
                )

        # From JSONB gaps (MEDIUM - required keys missing)
        for jsonb_field, keys in jsonb_gaps.missing_keys.items():
            for key in keys:
                all_gaps.append(
                    FieldGap(
                        field_name=f"{jsonb_field}.{key}",
                        layer="jsonb",
                        priority=GapPriority.MEDIUM,
                        reason=f"Required JSONB key missing in {jsonb_field}",
                    )
                )

        # From JSONB gaps (LOW - empty values can often be acceptable)
        for jsonb_field, keys in jsonb_gaps.empty_values.items():
            for key in keys:
                all_gaps.append(
                    FieldGap(
                        field_name=f"{jsonb_field}.{key}",
                        layer="jsonb",
                        priority=GapPriority.LOW,
                        reason=f"JSONB key has empty value in {jsonb_field}",
                    )
                )

        # From application gaps (HIGH - application metadata important for assessment)
        for field in application_gaps.missing_metadata:
            all_gaps.append(
                FieldGap(
                    field_name=field,
                    layer="application",
                    priority=GapPriority.HIGH,
                    reason="Application metadata incomplete",
                )
            )

        # From standards gaps (CRITICAL - mandatory violations block assessment)
        for standard_name in standards_gaps.missing_mandatory_data:
            all_gaps.append(
                FieldGap(
                    field_name=standard_name,
                    layer="standards",
                    priority=GapPriority.CRITICAL,
                    reason="Mandatory architecture standard violated",
                )
            )

        # From standards gaps (HIGH/MEDIUM - violated standards)
        for violation in standards_gaps.violated_standards:
            priority = (
                GapPriority.HIGH if violation.is_mandatory else GapPriority.MEDIUM
            )
            all_gaps.append(
                FieldGap(
                    field_name=violation.standard_name,
                    layer="standards",
                    priority=priority,
                    reason=violation.violation_details,
                )
            )

        logger.debug(
            f"Aggregated {len(all_gaps)} gaps across all layers",
            extra={
                "total_gaps": len(all_gaps),
                "critical": len(
                    [g for g in all_gaps if g.priority == GapPriority.CRITICAL]
                ),
                "high": len([g for g in all_gaps if g.priority == GapPriority.HIGH]),
                "medium": len(
                    [g for g in all_gaps if g.priority == GapPriority.MEDIUM]
                ),
                "low": len([g for g in all_gaps if g.priority == GapPriority.LOW]),
            },
        )

        return all_gaps
