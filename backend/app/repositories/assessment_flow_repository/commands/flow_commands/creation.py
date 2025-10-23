"""
Flow creation operations.
"""

import logging
from datetime import datetime
from typing import Any, List, Optional

from app.models.assessment_flow import AssessmentFlow
from app.models.assessment_flow_state import AssessmentFlowStatus, AssessmentPhase

logger = logging.getLogger(__name__)


async def create_assessment_flow(  # noqa: C901
    self,
    engagement_id: str,
    selected_application_ids: List[str],
    created_by: Optional[str] = None,
    collection_flow_id: Optional[str] = None,
    background_tasks: Optional[Any] = None,  # FastAPI BackgroundTasks (Phase 3.1)
) -> str:
    """
    Create new assessment flow with initial state and register with master flow system.

    ENHANCED (October 2025 - Phase 2 Days 8-9): Now populates application_asset_groups,
    enrichment_status, and readiness_summary during initialization using
    AssessmentApplicationResolver service.

    Collection → Assessment Handoff: When collection_flow_id is provided,
    automatically resolves assets to canonical applications via junction table.

    Args:
        engagement_id: Engagement UUID
        selected_application_ids: Asset IDs (DEPRECATED name, actually asset UUIDs)
        created_by: User ID who created the flow
        collection_flow_id: Optional collection flow ID for asset resolution

    Returns:
        Assessment flow ID (UUID as string)
    """
    from uuid import UUID
    from app.services.assessment.application_resolver import (
        AssessmentApplicationResolver,
    )

    # Convert string IDs to UUIDs for resolver
    try:
        asset_ids = [UUID(aid) for aid in selected_application_ids]
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid asset IDs provided: {e}")
        asset_ids = []

    # Convert collection_flow_id to UUID if provided
    collection_flow_uuid = None
    if collection_flow_id:
        try:
            collection_flow_uuid = UUID(collection_flow_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid collection_flow_id: {collection_flow_id}")

    # Step 1: Initialize AssessmentApplicationResolver
    resolver = AssessmentApplicationResolver(
        db=self.db,
        client_account_id=UUID(str(self.client_account_id)),
        engagement_id=UUID(str(engagement_id)),
    )

    # Step 2: Resolve assets to canonical applications (with grouping)
    application_groups = []
    canonical_app_ids = []
    if asset_ids:
        try:
            application_groups = await resolver.resolve_assets_to_applications(
                asset_ids=asset_ids, collection_flow_id=collection_flow_uuid
            )

            # Extract canonical application IDs
            canonical_app_ids = [
                str(group.canonical_application_id)
                for group in application_groups
                if group.canonical_application_id is not None
            ]
        except Exception as e:
            logger.error(f"Failed to resolve assets to applications: {e}")
            # Continue with flow creation even if resolution fails

    # Step 3: Calculate enrichment status
    enrichment_status = {}
    if asset_ids:
        try:
            enrichment_obj = await resolver.calculate_enrichment_status(asset_ids)
            enrichment_status = enrichment_obj.dict()
        except Exception as e:
            logger.error(f"Failed to calculate enrichment status: {e}")

    # Step 4: Calculate readiness summary
    readiness_summary = {}
    if asset_ids:
        try:
            readiness_obj = await resolver.calculate_readiness_summary(asset_ids)
            readiness_summary = readiness_obj.dict()
        except Exception as e:
            logger.error(f"Failed to calculate readiness summary: {e}")

    # Step 5: Convert application groups to dict for JSONB storage
    # PERFORMANCE FIX: Use model_dump(mode="json") instead of json.loads/dumps
    # This is more efficient and handles UUID serialization automatically
    application_groups_dict = [
        group.model_dump(mode="json") for group in application_groups
    ]

    # Step 6: Feature-flagged unmapped asset handling (Phase 1.2 - October 2025)
    from app.core.config import settings

    unmapped_count = sum(
        1 for group in application_groups if group.canonical_application_id is None
    )
    unmapped_percentage = (
        unmapped_count / len(application_groups) if application_groups else 0
    )

    # Collect unmapped asset names for error/warning messages
    unmapped_names = [
        group.canonical_application_name
        for group in application_groups
        if group.canonical_application_id is None
    ]

    # Log tenant-scoped metrics for monitoring (GPT-5 recommendation)
    if unmapped_count > 0:
        logger.info(
            f"Assessment flow unmapped asset metrics: "
            f"total={len(application_groups)}, "
            f"unmapped={unmapped_count}, "
            f"percentage={unmapped_percentage:.1%}, "
            f"client_account_id={self.client_account_id}, "
            f"engagement_id={engagement_id}"
        )

        # Feature-flagged handling based on environment configuration
        if settings.UNMAPPED_ASSET_HANDLING == "strict":
            # Always reject unmapped assets
            unmapped_list = ", ".join(unmapped_names[:5])
            more = "..." if len(unmapped_names) > 5 else ""
            raise ValueError(
                f"Assessment initialization blocked: {unmapped_count} "
                f"unmapped assets detected. "
                f"Unmapped assets: {unmapped_list}{more}. "
                f"Strict mode requires all assets mapped to canonical "
                f"applications. Use Asset Resolution workflow in "
                f"collection flow."
            )
        elif settings.UNMAPPED_ASSET_HANDLING == "block":
            # Reject if exceeds threshold
            threshold = settings.UNMAPPED_ASSET_THRESHOLD
            if unmapped_percentage > threshold:
                # Format unmapped asset list with ellipsis if needed
                unmapped_list = ", ".join(unmapped_names[:5])
                more_indicator = "..." if len(unmapped_names) > 5 else ""

                raise ValueError(
                    f"Assessment initialization blocked: "
                    f"{unmapped_percentage:.1%} unmapped assets "
                    f"exceeds threshold of {threshold:.1%}. "
                    f"Unmapped assets ({unmapped_count}): "
                    f"{unmapped_list}{more_indicator}. "
                    f"Please complete canonical application mapping to "
                    f"proceed."
                )
            else:
                logger.warning(
                    f"Assessment flow has {unmapped_count} unmapped assets "
                    f"({unmapped_percentage:.1%}) but within threshold "
                    f"({threshold:.1%}). Proceeding with banner."
                )
        else:  # "banner" mode (default)
            logger.warning(
                f"Assessment flow has {unmapped_count} unmapped assets. "
                f"Asset Resolution banner will be shown in UI."
            )

    total_enrichment = sum(enrichment_status.values()) if enrichment_status else 0
    if total_enrichment == 0 and asset_ids:
        logger.warning(
            f"Assessment flow has no enrichment data for {len(asset_ids)} assets. "
            f"Consider running enrichment pipeline."
        )

    avg_completeness = readiness_summary.get("avg_completeness_score", 0.0)
    if avg_completeness < 0.5 and asset_ids:
        logger.warning(
            f"Assessment flow has low readiness: {avg_completeness:.1%}. "
            f"Only {readiness_summary.get('ready', 0)}/{len(asset_ids)} assets ready."
        )

    # Convert string IDs to proper format for JSONB storage
    app_ids_jsonb = [str(app_id) for app_id in selected_application_ids]

    # Bug #630 Fix - ADR-012 Two-Table Pattern: Create master FIRST,
    # then child flow
    # STEP 1: Create master flow using MasterFlowOrchestrator
    from app.services.master_flow_orchestrator import MasterFlowOrchestrator
    from app.core.context import RequestContext

    # Build request context for orchestrator
    context = RequestContext(
        client_account_id=str(self.client_account_id),
        engagement_id=str(engagement_id),
        user_id=created_by or "system",
    )

    orchestrator = MasterFlowOrchestrator(self.db, context)

    # Create master flow within a transaction (don't commit yet)
    master_flow_id, _ = await orchestrator.create_flow(
        flow_type="assessment",
        flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
        configuration={
            "selected_applications": selected_application_ids,
            "assessment_type": "sixr_analysis",
            "created_by": created_by,
            "engagement_id": str(engagement_id),
            "collection_flow_id": collection_flow_id,
        },
        initial_state={
            "phase": AssessmentPhase.INITIALIZATION.value,
            "applications_count": len(selected_application_ids),
        },
        atomic=True,  # Don't commit yet, we're in a transaction
    )

    # Flush to get master_flow_id in DB for FK availability (but don't commit)
    await self.db.flush()

    logger.info(
        f"✅ Created assessment master flow: {master_flow_id}"
        + (
            f" (linked to collection flow {collection_flow_id})"
            if collection_flow_id
            else ""
        )
    )

    # STEP 2: Create child flow with correct master_flow_id FK reference
    flow_record = AssessmentFlow(
        client_account_id=self.client_account_id,
        engagement_id=engagement_id,
        master_flow_id=UUID(master_flow_id),  # Correct FK to master flow
        flow_id=UUID(master_flow_id),  # Match master flow ID for consistency
        flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
        configuration={
            "selected_application_ids": selected_application_ids,
        },
        # DEPRECATED: Keep for backward compatibility (semantic mismatch)
        selected_application_ids=app_ids_jsonb,
        # NEW: Proper semantic fields (October 2025)
        selected_asset_ids=app_ids_jsonb,
        selected_canonical_application_ids=canonical_app_ids,
        application_asset_groups=application_groups_dict,
        enrichment_status=enrichment_status,
        readiness_summary=readiness_summary,
        status=AssessmentFlowStatus.INITIALIZED.value,
        current_phase=AssessmentPhase.INITIALIZATION.value,
        progress=0.0,
        phase_progress={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    self.db.add(flow_record)

    # STEP 3: Single atomic commit for both master and child flows (ADR-012 requirement)
    await self.db.commit()
    await self.db.refresh(flow_record)

    # Log creation with metadata
    logger.info(
        f"✅ Created assessment child flow {flow_record.id} with "
        f"{len(application_groups)} application groups, "
        f"{len(asset_ids)} assets, "
        f"readiness: {readiness_summary.get('ready', 0)}/{len(asset_ids)} ready, "
        f"linked to master flow {master_flow_id}"
    )

    # Step 7: Feature-flagged auto-enrichment (Phase 3.1 - October 2025)
    if settings.AUTO_ENRICHMENT_ENABLED and asset_ids and background_tasks:
        from app.services.enrichment.auto_enrichment_pipeline import (
            trigger_auto_enrichment_background,
        )

        # Trigger background enrichment (non-blocking)
        # Per-flow lock prevents concurrent enrichment for same flow
        background_tasks.add_task(
            trigger_auto_enrichment_background,
            db=self.db,
            flow_id=str(flow_record.id),
            client_account_id=self.client_account_id,
            engagement_id=engagement_id,
            asset_ids=asset_ids,
        )

        logger.info(
            f"Auto-enrichment triggered for flow {flow_record.id} "
            f"({len(asset_ids)} assets) - background task queued"
        )
    elif settings.AUTO_ENRICHMENT_ENABLED and asset_ids and not background_tasks:
        logger.warning(
            f"Auto-enrichment enabled but no BackgroundTasks provided "
            f"for flow {flow_record.id}"
        )

    logger.info(
        f"✅ Created assessment flow {master_flow_id} for engagement {engagement_id} "
        f"(master flow and child flow linked atomically per ADR-012)"
    )
    return str(master_flow_id)
