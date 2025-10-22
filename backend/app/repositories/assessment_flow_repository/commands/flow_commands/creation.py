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
            raise ValueError(
                f"Assessment initialization blocked: {unmapped_count} unmapped assets detected. "
                f"Unmapped assets: {', '.join(unmapped_names[:5])}{'...' if len(unmapped_names) > 5 else ''}. "
                f"Strict mode requires all assets mapped to canonical applications. "
                f"Use Asset Resolution workflow in collection flow."
            )
        elif settings.UNMAPPED_ASSET_HANDLING == "block":
            # Reject if exceeds threshold
            if unmapped_percentage > settings.UNMAPPED_ASSET_THRESHOLD:
                # Format unmapped asset list with ellipsis if needed
                unmapped_list = ", ".join(unmapped_names[:5])
                more_indicator = "..." if len(unmapped_names) > 5 else ""

                raise ValueError(
                    f"Assessment initialization blocked: {unmapped_percentage:.1%} unmapped assets "
                    f"exceeds threshold of {settings.UNMAPPED_ASSET_THRESHOLD:.1%}. "
                    f"Unmapped assets ({unmapped_count}): {unmapped_list}{more_indicator}. "
                    f"Please complete canonical application mapping to proceed."
                )
            else:
                logger.warning(
                    f"Assessment flow has {unmapped_count} unmapped assets ({unmapped_percentage:.1%}) "
                    f"but within threshold ({settings.UNMAPPED_ASSET_THRESHOLD:.1%}). Proceeding with banner."
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

    flow_record = AssessmentFlow(
        client_account_id=self.client_account_id,
        engagement_id=engagement_id,
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
    await self.db.commit()
    await self.db.refresh(flow_record)

    # Log creation with metadata
    logger.info(
        f"Created assessment flow {flow_record.id} with "
        f"{len(application_groups)} application groups, "
        f"{len(asset_ids)} assets, "
        f"readiness: {readiness_summary.get('ready', 0)}/{len(asset_ids)} ready"
    )

    # Register with master flow system
    from app.repositories.crewai_flow_state_extensions_repository import (
        CrewAIFlowStateExtensionsRepository,
    )

    try:
        extensions_repo = CrewAIFlowStateExtensionsRepository(
            self.db,
            str(self.client_account_id),
            str(engagement_id),
            user_id=created_by,
        )

        await extensions_repo.create_master_flow(
            flow_id=str(flow_record.id),
            flow_type="assessment",  # Using 'assessment' for consistency
            user_id=created_by or "system",
            flow_name=f"Assessment Flow - {len(selected_application_ids)} Applications",
            flow_configuration={
                "selected_applications": selected_application_ids,
                "assessment_type": "sixr_analysis",
                "created_by": created_by,
                "engagement_id": str(engagement_id),
                "collection_flow_id": collection_flow_id,  # Store in config too
            },
            initial_state={
                "phase": AssessmentPhase.INITIALIZATION.value,
                "applications_count": len(selected_application_ids),
            },
            collection_flow_id=collection_flow_id,  # NEW: Link to collection flow
        )

        logger.info(
            f"Registered assessment flow {flow_record.id} with master flow system"
            + (
                f" (linked to collection flow {collection_flow_id})"
                if collection_flow_id
                else ""
            )
        )

        # FIX: Link assessment flow back to master flow (update master_flow_id)
        flow_record.master_flow_id = flow_record.id
        await self.db.commit()
        await self.db.refresh(flow_record)
        logger.info(
            f"Linked assessment flow {flow_record.id} to master flow via master_flow_id"
        )

    except Exception as e:
        logger.error(
            f"Failed to register assessment flow {flow_record.id} with master flow: {e}"
        )
        # Don't fail the entire creation if master flow registration fails
        # The flow still exists and can function, just without master coordination

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
            f"Auto-enrichment enabled but no BackgroundTasks provided for flow {flow_record.id}"
        )

    logger.info(
        f"Created assessment flow {flow_record.id} for engagement {engagement_id}"
    )
    return str(flow_record.id)
