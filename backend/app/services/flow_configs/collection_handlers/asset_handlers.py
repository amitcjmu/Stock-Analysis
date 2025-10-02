"""
Collection Asset Write-back Handlers
ADCS: Asset update and write-back operations for resolved gaps

Provides handler functions for applying resolved gap data to asset records.
"""

import logging
import uuid
from typing import Any, Dict, List

from sqlalchemy import update, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .base import CollectionHandlerBase, build_field_updates_from_rows

logger = logging.getLogger(__name__)


class AssetHandlers(CollectionHandlerBase):
    """Handlers for asset write-back operations"""

    async def apply_resolved_gaps_to_assets(
        self, db: AsyncSession, collection_flow_id: uuid.UUID, context: Dict[str, Any]
    ) -> None:
        """Map resolved questionnaire gaps to Asset fields and set assessment readiness.

        Implementation highlights:
        - Tenant-scoped and UUID-typed filtering
        - Conservative whitelist mapping
        - Batched updates with rollback on failure
        - Best-effort audit logging behind a feature flag
        """
        from app.models.asset import Asset

        BATCH_SIZE = int((context or {}).get("batch_size", 300))
        client_id_raw = (context or {}).get("client_account_id")
        engagement_id_raw = (context or {}).get("engagement_id")

        client_id = str(client_id_raw).strip() if client_id_raw is not None else None
        engagement_id = (
            str(engagement_id_raw).strip() if engagement_id_raw is not None else None
        )

        if not client_id or not engagement_id:
            logger.error("Missing tenant context; aborting write-back")
            raise RuntimeError(
                "Tenant context (client_account_id, engagement_id) required for write-back"
            )

        # Normalize tenant IDs to UUID for reliable comparisons
        try:
            client_uuid = UUID(client_id)
            engagement_uuid = UUID(engagement_id)
        except Exception:
            logger.error("Invalid tenant identifiers; aborting write-back")
            raise RuntimeError("Invalid tenant identifiers for write-back scope")
        audit_enabled = True

        resolved_rows = await db.execute(
            (
                "SELECT g.field_name, r.response_value, "
                "(g.metadata->>'asset_id') AS asset_id_hint, "
                "(g.metadata->>'application_name') AS app_name_hint "
                "FROM migration.collection_data_gaps g "
                "JOIN migration.collection_questionnaire_responses r ON g.id = r.gap_id "
                "WHERE g.collection_flow_id = :flow_id "
                "AND g.resolution_status = 'resolved'"
            ),
            {"flow_id": collection_flow_id},
        )
        resolved = resolved_rows.fetchall()
        if not resolved:
            return

        field_updates = build_field_updates_from_rows(resolved)

        # Whitelist fields we allow to update on Asset
        whitelist = {
            "environment": "environment",
            "business_criticality": "business_criticality",
            "business_owner": "business_owner",
            "department": "department",
            "application_name": "application_name",
            "technology_stack": "technology_stack",
        }

        asset_ids = await self._resolve_target_asset_ids(db, resolved, context)
        if not asset_ids:
            return

        # Batch update assets
        for i in range(0, len(asset_ids), BATCH_SIZE):
            batch_ids = asset_ids[i : i + BATCH_SIZE]

            update_payload: Dict[str, Any] = {}
            for src_field, dst_field in whitelist.items():
                if src_field in field_updates and field_updates[src_field] not in (
                    None,
                    "",
                ):
                    update_payload[dst_field] = field_updates[src_field]

            # Set assessment readiness if minimum fields are present
            if {"environment", "business_criticality"}.issubset(field_updates.keys()):
                update_payload["assessment_readiness"] = "ready"

            if not update_payload:
                continue

            if not batch_ids:
                continue

            stmt = (
                update(Asset)
                .where(
                    and_(
                        Asset.id.in_(batch_ids),
                        Asset.client_account_id == client_uuid,
                        Asset.engagement_id == engagement_uuid,
                    )
                )
                .values(**update_payload)
            )
            try:
                await db.execute(stmt)
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(
                    "Write-back batch failed",
                    extra={
                        "range_start": i,
                        "range_end": i + len(batch_ids) - 1,
                        "batch_ids": batch_ids,
                        "client_account_id": str(client_uuid),
                        "engagement_id": str(engagement_uuid),
                    },
                )

            if audit_enabled:
                logger.info(
                    {
                        "event": "collection_writeback",
                        "flow_id": str(collection_flow_id),
                        "batch": {"start": i, "end": i + len(batch_ids) - 1},
                        "fields": list(update_payload.keys()),
                    }
                )

    async def _resolve_target_asset_ids(
        self, db: AsyncSession, resolved_rows, context: Dict[str, Any]
    ) -> List[uuid.UUID]:
        """Resolve target asset IDs from gap metadata hints (asset_id/app_name)."""
        from app.models.asset import Asset

        hinted_asset_ids = set()
        for row in resolved_rows:
            hint = getattr(row, "asset_id_hint", None)
            if hint:
                hinted_asset_ids.add(hint)

        asset_ids: List[uuid.UUID] = []
        if hinted_asset_ids:
            # Filter valid UUIDs and convert them
            valid_asset_uuids = []
            for hint in hinted_asset_ids:
                if hint:
                    try:
                        valid_asset_uuids.append(uuid.UUID(hint))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid UUID format in asset_id_hint: {hint}")
                        continue

            if valid_asset_uuids:
                result = await db.execute(
                    select(Asset.id)
                    .where(
                        Asset.id.in_(valid_asset_uuids),
                        Asset.engagement_id == context.get("engagement_id"),
                    )
                    .execution_options(populate_existing=True)
                )
                asset_ids = [r.id for r in result.fetchall()]
        else:
            app_names = set()
            for row in resolved_rows:
                name_hint = getattr(row, "app_name_hint", None)
                if name_hint:
                    app_names.add(name_hint)
            if app_names:
                result = await db.execute(
                    select(Asset.id)
                    .where(
                        Asset.application_name.in_([a for a in app_names if a]),
                        Asset.engagement_id == context.get("engagement_id"),
                    )
                    .execution_options(populate_existing=True)
                )
                asset_ids = [r.id for r in result.fetchall()]
            else:
                logger.warning(
                    "No asset/application hints present in resolved gaps; skipping write-back to avoid broad updates"
                )
        return asset_ids


# Create singleton instance for backward compatibility
asset_handlers = AssetHandlers()


# Export functions for backward compatibility
async def apply_resolved_gaps_to_assets(*args, **kwargs):
    return await asset_handlers.apply_resolved_gaps_to_assets(*args, **kwargs)


async def _resolve_target_asset_ids(*args, **kwargs):
    return await asset_handlers._resolve_target_asset_ids(*args, **kwargs)
