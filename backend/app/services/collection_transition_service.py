"""
Collection to Assessment Transition Service

Service for managing the transition from collection flows to assessment flows.
Uses agent-driven readiness assessment and creates assessment flows via MFO pattern.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.services.gap_analysis_summary_service import GapAnalysisSummaryService
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.schemas.collection_transition import ReadinessResult, TransitionResult

logger = logging.getLogger(__name__)


class CollectionTransitionService:
    """
    Service for collection to assessment transitions.
    Uses agent-driven readiness assessment, NOT hardcoded thresholds.
    """

    def __init__(self, db_session: AsyncSession, context: RequestContext):
        self.db = db_session
        self.context = context
        self.gap_service = GapAnalysisSummaryService(db_session)

    async def validate_readiness(self, flow_id: UUID) -> ReadinessResult:
        """
        Agent-driven readiness validation.
        Uses TenantScopedAgentPool for intelligent assessment.
        """
        # Get flow with tenant-scoped query
        flow = await self._get_collection_flow(flow_id)

        # CRITICAL: Check assessment_ready flag first - overrides gap analysis
        if flow.assessment_ready:
            logger.info(
                f"✅ Flow {flow_id} has assessment_ready=true - bypassing gap analysis"
            )
            return ReadinessResult(
                is_ready=True,
                confidence=1.0,
                reason="Collection marked as ready for assessment (assessment_ready=true)",
                missing_requirements=[],
                thresholds_used=await self._get_tenant_thresholds(),
            )

        # Get gap analysis summary (existing service)
        gap_summary = await self.gap_service.get_gap_analysis_summary(
            str(flow.id), self.context
        )

        # Use TenantScopedAgentPool to get a readiness assessment agent
        agent = await TenantScopedAgentPool.get_agent(
            self.context, "readiness_assessor", service_registry=None
        )

        # Create readiness assessment task
        task_description = f"""
        Assess readiness for transition from collection to assessment phase.

        Collection Flow ID: {flow_id}
        Current Status: {flow.status}
        Progress: {flow.progress_percentage}%

        Gap Analysis Summary:
        - Total Fields Required: {gap_summary.total_fields_required if gap_summary else 0}
        - Fields Collected: {gap_summary.fields_collected if gap_summary else 0}
        - Fields Missing: {gap_summary.fields_missing if gap_summary else 0}
        - Completeness: {gap_summary.completeness_percentage if gap_summary else 0}%
        - Critical Gaps: {len(gap_summary.critical_gaps) if gap_summary else 0}
        - Data Quality Score: {gap_summary.data_quality_score if gap_summary else 'N/A'}
        - Confidence Level: {gap_summary.confidence_level if gap_summary else 'N/A'}

        Determine:
        1. Is the collection ready for assessment? (true/false)
        2. Confidence level (0.0-1.0)
        3. Reason for decision
        4. Missing requirements (if any)

        Use tenant preferences for thresholds but make intelligent assessment based on data quality.
        """

        try:
            # Execute task using agent - handle different agent types
            if hasattr(agent, "execute_async"):
                result = await agent.execute_async(inputs={"task": task_description})
            elif hasattr(agent, "execute"):
                # Use sync execute method
                result = agent.execute(task=task_description)
            else:
                raise AttributeError("Agent has no execute method available")

            # Parse agent response
            if isinstance(result, dict):
                assessment = result
            else:
                # Try to parse string response
                import json

                try:
                    assessment = json.loads(str(result))
                except Exception:
                    # Fallback to basic calculation if agent fails
                    fields_collected = (
                        gap_summary.fields_collected if gap_summary else 0
                    )
                    total_fields = (
                        gap_summary.total_fields_required if gap_summary else 0
                    )
                    confidence = (
                        (fields_collected / total_fields) if total_fields > 0 else 1.0
                    )
                    assessment = {
                        "is_ready": confidence >= 0.7,
                        "confidence": confidence,
                        "reason": f"Collection {int(confidence * 100)}% complete",
                        "missing_requirements": [],
                    }

            return ReadinessResult(
                is_ready=assessment.get("is_ready", False),
                confidence=assessment.get("confidence", 0.0),
                reason=assessment.get("reason", "Assessment incomplete"),
                missing_requirements=assessment.get("missing_requirements", []),
                thresholds_used=await self._get_tenant_thresholds(),
            )

        except (AttributeError, TypeError) as e:
            # Handle case where agent doesn't have execute method
            logger.warning(
                f"Agent execute not available: {e}, falling back to calculation"
            )

            # Fallback to calculated readiness
            fields_collected = gap_summary.fields_collected if gap_summary else 0
            total_fields = gap_summary.total_fields_required if gap_summary else 0
            fields_missing = gap_summary.fields_missing if gap_summary else 0

            if total_fields == 0 or fields_missing == 0:
                confidence = 1.0
                is_ready = True
                reason = "No data gaps identified - collection complete"
                missing_requirements = []
            else:
                confidence = (
                    (fields_collected / total_fields) if total_fields > 0 else 0
                )
                thresholds = await self._get_tenant_thresholds()
                readiness_threshold = thresholds.get("readiness_threshold", 0.7)
                is_ready = confidence >= readiness_threshold

                if is_ready:
                    reason = f"Collection {int(confidence * 100)}% complete - meets threshold"
                else:
                    threshold_pct = int(readiness_threshold * 100)
                    reason = f"Collection {int(confidence * 100)}% complete - below {threshold_pct}% threshold"

                # Extract missing requirements from critical gaps
                missing_requirements = []
                if gap_summary and gap_summary.critical_gaps:
                    for gap in gap_summary.critical_gaps[:5]:
                        if isinstance(gap, dict):
                            missing_requirements.append(
                                gap.get("field_name", "Unknown field")
                            )

            return ReadinessResult(
                is_ready=is_ready,
                confidence=confidence,
                reason=reason,
                missing_requirements=missing_requirements,
                thresholds_used=await self._get_tenant_thresholds(),
            )

    async def create_assessment_flow(self, collection_flow_id: UUID):  # noqa: C901
        """
        Bug #630 Fix: Create assessment with proper two-table pattern (ADR-012).
        Creates both master flow AND child flow atomically in a single transaction.
        """

        try:
            # Get collection flow
            collection_flow = await self._get_collection_flow(collection_flow_id)

            # Bug #666 Fix - Extract asset and canonical app IDs from collection flow
            # Use deduplication_results directly instead of resolver to avoid junction table dependency
            asset_ids = []
            canonical_app_ids = []
            application_groups_dict = []
            dedup_results = []  # Initialize to avoid UnboundLocalError

            if (
                hasattr(collection_flow, "collection_config")
                and collection_flow.collection_config
            ):
                config = collection_flow.collection_config

                # Extract from deduplication_results (most reliable source)
                dedup_results = config.get("deduplication_results", [])
                if dedup_results:
                    for result in dedup_results:
                        asset_id = result.get("asset_id")
                        canonical_app_id = result.get("canonical_application_id")
                        app_name = result.get("application_name", "Unknown")

                        if asset_id:
                            try:
                                asset_ids.append(
                                    UUID(asset_id)
                                    if isinstance(asset_id, str)
                                    else asset_id
                                )
                            except (ValueError, TypeError) as e:
                                logger.warning(
                                    f"Invalid asset ID in deduplication_results: {asset_id}: {e}"
                                )

                        if canonical_app_id:
                            canonical_app_ids.append(str(canonical_app_id))

                            # Build application_asset_group structure
                            application_groups_dict.append(
                                {
                                    "canonical_application_id": str(canonical_app_id),
                                    "canonical_application_name": app_name,
                                    "asset_ids": [str(asset_id)] if asset_id else [],
                                    "asset_count": 1,
                                    "confidence_score": result.get(
                                        "confidence_score", 1.0
                                    ),
                                }
                            )

                # Fallback: Try selected_application_ids if dedup_results is empty
                if not asset_ids:
                    config_asset_ids = config.get("asset_ids", [])
                    config_selected_apps = config.get("selected_application_ids", [])
                    raw_ids = (
                        config_asset_ids if config_asset_ids else config_selected_apps
                    )

                    for aid in raw_ids:
                        try:
                            if isinstance(aid, str):
                                asset_ids.append(UUID(aid))
                            elif isinstance(aid, UUID):
                                asset_ids.append(aid)
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                f"Invalid asset ID in collection config: {aid}: {e}"
                            )

            logger.info(
                f"✅ Extracted {len(asset_ids)} assets and "
                f"{len(canonical_app_ids)} canonical applications from collection flow"
            )

            # Bug #763 Fix - Enrich canonical_applications with data from assets
            enrichment_stats = await self._enrich_canonical_applications(
                canonical_app_ids=canonical_app_ids,
                dedup_results=dedup_results,
                collection_flow=collection_flow,
            )

            logger.info(
                f"✅ Enriched {enrichment_stats['enriched']} of {enrichment_stats['total']} "
                f"canonical applications with asset data"
            )

            # Bug #630 Fix - STEP 1: Create master flow first
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator

            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Bug #668 Fix: Use correct parameter names and rely on context for tenant info
            # MasterFlowOrchestrator.create_flow() extracts client_account_id, engagement_id,
            # and user_id from self.context automatically (see flow_creation_operations.py:172-173)
            master_flow_id, _ = await orchestrator.create_flow(
                flow_type="assessment",
                flow_name=f"Assessment for {collection_flow.flow_name or 'Collection'}",
                configuration={
                    "source_collection_flow_id": str(collection_flow.id),
                    "transition_type": "collection_to_assessment",
                },
            )

            # Flush to get master_flow_id in DB (but don't commit yet)
            await self.db.flush()

            logger.info(f"✅ Created assessment master flow: {master_flow_id}")

            # Bug #630 Fix - STEP 2: Create child flow with master_flow_id FK
            from app.models.assessment_flow.core_models import AssessmentFlow
            from uuid import uuid4

            # Get selected application IDs from collection config
            selected_app_ids = []
            if (
                hasattr(collection_flow, "collection_config")
                and collection_flow.collection_config
                and collection_flow.collection_config.get("selected_application_ids")
            ):
                selected_app_ids = collection_flow.collection_config[
                    "selected_application_ids"
                ]

            # Create child flow record with master_flow_id FK
            assessment_flow = AssessmentFlow(
                id=uuid4(),
                master_flow_id=master_flow_id,  # ✅ Link to master flow (ADR-012)
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                flow_name=f"Assessment for {collection_flow.flow_name or 'Collection'}",
                description=f"Assessment created from collection flow {collection_flow.flow_id}",
                status="initialized",
                current_phase="initialization",
                progress=0.0,
                # Bug #666 Fix - Populate application context fields
                selected_canonical_application_ids=canonical_app_ids,
                selected_asset_ids=[str(aid) for aid in asset_ids],
                application_asset_groups=application_groups_dict,
                configuration={
                    "collection_flow_id": str(collection_flow.id),
                    "selected_application_ids": [
                        str(app_id) for app_id in selected_app_ids
                    ],
                    "transition_date": datetime.utcnow().isoformat(),
                    "transition_type": "collection_to_assessment",
                },
                flow_metadata={
                    "source": "collection_transition",
                    "created_by_service": "collection_transition_service",
                    "source_collection": {
                        "collection_flow_id": str(collection_flow.id),
                        "collection_master_flow_id": str(collection_flow.flow_id),
                        "transitioned_from": datetime.utcnow().isoformat(),
                    },
                },
                started_at=datetime.utcnow(),
            )

            self.db.add(assessment_flow)

            # Flush to get child flow ID
            await self.db.flush()

            logger.info(
                f"✅ Created assessment child flow: {assessment_flow.id} linked to master {master_flow_id}"
            )

            # Update collection flow linkage and mark as completed
            if hasattr(collection_flow, "assessment_flow_id"):
                collection_flow.assessment_flow_id = assessment_flow.id
                collection_flow.assessment_transition_date = datetime.utcnow()

            # Mark collection flow as completed now that assessment has been created
            collection_flow.status = "completed"
            collection_flow.completed_at = datetime.utcnow()
            collection_flow.progress_percentage = 100.0

            logger.info(
                f"✅ Marked collection flow {collection_flow.flow_id} as completed"
            )

            # Store bidirectional references in collection metadata
            current_metadata = getattr(collection_flow, "flow_metadata", {}) or {}
            collection_flow.flow_metadata = {
                **current_metadata,
                "assessment_handoff": {
                    "assessment_flow_id": str(assessment_flow.id),
                    "assessment_master_flow_id": str(master_flow_id),
                    "transitioned_at": datetime.utcnow().isoformat(),
                    "transitioned_by": (
                        str(self.context.user_id) if self.context.user_id else None
                    ),
                },
            }

            # Bug #630 Fix - STEP 3: Single atomic commit for both master and child
            # This is the final commit that makes both flows permanent
            # Note: The endpoint already has a transaction context, so this commit applies to all changes
            logger.info(
                f"✅ Assessment flow creation complete - master={master_flow_id}, child={assessment_flow.id}"
            )

            return TransitionResult(
                assessment_flow_id=assessment_flow.id,
                assessment_flow=assessment_flow,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            # Roll back entire transaction on any error
            await self.db.rollback()
            logger.error(
                f"Failed to create assessment flow (two-table pattern): {e}",
                exc_info=True,
            )
            raise

    async def _get_collection_flow(self, flow_id: UUID) -> CollectionFlow:
        """
        Get collection flow with proper tenant scoping.
        """
        query = select(CollectionFlow).where(
            CollectionFlow.flow_id == flow_id,
            CollectionFlow.client_account_id == self.context.client_account_id,
            CollectionFlow.engagement_id == self.context.engagement_id,
        )
        result = await self.db.execute(query)
        flow = result.scalar_one_or_none()

        if not flow:
            raise ValueError(f"Collection flow {flow_id} not found or access denied")

        return flow

    def _create_readiness_task(self, flow: CollectionFlow, gap_summary: Any) -> Dict:
        """Create task for readiness assessment - kept for compatibility."""
        # This method is no longer used but kept to avoid breaking changes
        # Safe attribute access for flow fields
        flow_id = getattr(flow, "flow_id", None)
        progress_percentage = getattr(flow, "progress_percentage", 0) or 0
        current_phase = getattr(flow, "current_phase", "unknown") or "unknown"

        # Safe gap summary processing
        gaps_count = 0
        if gap_summary and hasattr(gap_summary, "gaps"):
            gaps_count = len(gap_summary.gaps) if gap_summary.gaps else 0
        elif gap_summary and hasattr(gap_summary, "critical_gaps"):
            # Alternative field name
            critical_gaps = getattr(gap_summary, "critical_gaps", []) or []
            optional_gaps = getattr(gap_summary, "optional_gaps", []) or []
            gaps_count = len(critical_gaps) + len(optional_gaps)

        return {
            "flow_id": str(flow_id) if flow_id else "unknown",
            "gaps_count": gaps_count,
            "collection_progress": progress_percentage,
            "current_phase": current_phase,
        }

    async def _get_tenant_thresholds(self) -> Dict[str, float]:
        """Get tenant-specific readiness thresholds from engagement preferences."""
        # Default thresholds - can be overridden by engagement preferences
        return {
            "collection_completeness": 0.7,
            "data_quality": 0.65,
            "confidence_score": 0.6,
        }

    def _build_canonical_to_assets_mapping(
        self, dedup_results: list
    ) -> Dict[str, list]:
        """
        Build mapping from canonical application IDs to their source asset IDs.

        Args:
            dedup_results: Deduplication results with canonical_app -> asset mappings

        Returns:
            Dict mapping canonical_app_id (str) -> list of asset UUIDs
        """
        canonical_to_assets = {}
        for result in dedup_results:
            can_id = result.get("canonical_application_id")
            asset_id = result.get("asset_id")
            if can_id and asset_id:
                if can_id not in canonical_to_assets:
                    canonical_to_assets[can_id] = []
                # Convert asset_id to UUID for query
                try:
                    asset_uuid = (
                        UUID(asset_id) if isinstance(asset_id, str) else asset_id
                    )
                    canonical_to_assets[can_id].append(asset_uuid)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid asset_id in dedup_results: {asset_id}: {e}"
                    )

        logger.info(
            f"Built mapping for {len(canonical_to_assets)} canonical applications "
            f"to their source assets"
        )
        return canonical_to_assets

    async def _get_source_asset_for_enrichment(
        self, asset_ids: list
    ) -> Any:  # Returns Asset or None
        """
        Query first available asset for enrichment data with tenant scoping.

        Args:
            asset_ids: List of asset UUIDs to query

        Returns:
            Asset model instance or None if not found
        """
        from app.models.asset import Asset

        asset_query = select(Asset).where(
            Asset.id.in_(asset_ids),
            Asset.client_account_id == self.context.client_account_id,
            Asset.engagement_id == self.context.engagement_id,
        )
        asset_query = asset_query.limit(1)

        asset_result = await self.db.execute(asset_query)
        return asset_result.scalar_one_or_none()

    def _apply_enrichment_data(
        self, canonical_app: Any, asset: Any
    ) -> bool:  # canonical_app: CanonicalApplication, asset: Asset
        """
        Copy enrichment data from asset to canonical application (defensive - don't overwrite).

        Args:
            canonical_app: CanonicalApplication instance to enrich
            asset: Source Asset with enrichment data

        Returns:
            True if any field was enriched, False otherwise
        """
        enriched = False

        if asset.criticality and not canonical_app.business_criticality:
            canonical_app.business_criticality = asset.criticality
            enriched = True

        if asset.description and not canonical_app.description:
            canonical_app.description = asset.description
            enriched = True

        if asset.technology_stack and not canonical_app.technology_stack:
            # Convert string to JSONB if needed
            if isinstance(asset.technology_stack, str):
                canonical_app.technology_stack = {"stack": asset.technology_stack}
            else:
                canonical_app.technology_stack = asset.technology_stack
            enriched = True

        return enriched

    async def _enrich_canonical_applications(
        self,
        canonical_app_ids: list,
        dedup_results: list,
        collection_flow: CollectionFlow,
    ) -> Dict[str, int]:
        """
        Enrich canonical_applications with data from assets.

        Bug #763 Fix: Maps canonical applications to their source assets and copies
        enrichment data to prevent assessment agent from spinning due to missing data.

        Enrichment fields:
        - business_criticality: Copied from assets.criticality
        - description: Copied from assets.description
        - technology_stack: Copied from assets.technology_stack (converted to JSONB)

        Args:
            canonical_app_ids: List of canonical application IDs to enrich
            dedup_results: Deduplication results mapping canonical apps to assets
            collection_flow: Source collection flow (for tenant scoping)

        Returns:
            Dict with enrichment statistics: {'enriched': int, 'total': int}
        """
        from app.models.canonical_applications import CanonicalApplication

        enriched_count = 0

        # Build mapping: canonical_app_id -> asset_ids
        canonical_to_assets = self._build_canonical_to_assets_mapping(dedup_results)

        # Enrich each canonical application
        for can_id_str in canonical_app_ids:
            try:
                can_id = UUID(can_id_str) if isinstance(can_id_str, str) else can_id_str

                # Get canonical application with tenant scoping
                canonical_app = await self.db.get(CanonicalApplication, can_id)
                if not canonical_app:
                    logger.warning(
                        f"Canonical application {can_id} not found - skipping enrichment"
                    )
                    continue

                # Get associated assets
                asset_ids = canonical_to_assets.get(can_id_str, [])
                if not asset_ids:
                    logger.debug(
                        f"No assets found for canonical application {can_id} - skipping enrichment"
                    )
                    continue

                # Get source asset for enrichment
                asset = await self._get_source_asset_for_enrichment(asset_ids)
                if not asset:
                    logger.warning(
                        f"No accessible assets found for canonical app {can_id} - "
                        f"tenant scoping may have filtered them"
                    )
                    continue

                # Apply enrichment data
                if self._apply_enrichment_data(canonical_app, asset):
                    enriched_count += 1
                    logger.debug(
                        f"Enriched canonical application {canonical_app.canonical_name} "
                        f"from asset {asset.name}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to enrich canonical application {can_id_str}: {e}",
                    exc_info=True,
                )
                # Continue with other applications even if one fails
                continue

        # Flush changes within transaction (don't commit - parent method handles commit)
        await self.db.flush()

        logger.info(
            f"✅ Enrichment complete: {enriched_count}/{len(canonical_app_ids)} applications enriched"
        )

        return {"enriched": enriched_count, "total": len(canonical_app_ids)}
