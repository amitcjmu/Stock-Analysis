"""
Collection Asset Write-back Handlers
ADCS: Asset update and write-back operations for resolved gaps

Provides handler functions for applying resolved gap data to asset records.
"""

import logging
import uuid
from typing import Any, Dict, List

from sqlalchemy import update, and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .base import CollectionHandlerBase, build_field_updates_from_rows

logger = logging.getLogger(__name__)


class AssetHandlers(CollectionHandlerBase):
    """Handlers for asset write-back operations"""

    def _build_update_payload(
        self, field_updates: Dict[str, Any], whitelist: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build update payload from field updates.

        Args:
            field_updates: Dict of field updates from questionnaire responses
            whitelist: Dict mapping source fields to target Asset fields

        Returns:
            Update payload dictionary
        """
        update_payload: Dict[str, Any] = {}

        # Apply whitelisted direct field mappings
        for src_field, dst_field in whitelist.items():
            if src_field in field_updates and field_updates[src_field] not in (
                None,
                "",
            ):
                value = field_updates[src_field]
                # CRITICAL FIX: Handle list values - extract first element for single-value fields
                if isinstance(value, list):
                    if len(value) == 0:
                        continue  # Skip empty lists
                    # For integer fields (cpu_cores, memory_gb, storage_gb), extract first element
                    if dst_field in ["cpu_cores", "memory_gb", "storage_gb"]:
                        try:
                            update_payload[dst_field] = (
                                int(value[0]) if value[0] else None
                            )
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid value for {dst_field}: {value[0]}")
                            continue
                    # For string fields (technology_stack, business_owner), join list or take first
                    elif dst_field in [
                        "technology_stack",
                        "business_owner",
                        "department",
                        "application_name",
                    ]:
                        # Join list with comma for multi-value fields, or take first element
                        if len(value) > 1:
                            update_payload[dst_field] = ", ".join(str(v) for v in value)
                        else:
                            update_payload[dst_field] = (
                                str(value[0]) if value[0] else None
                            )
                    else:
                        # Default: take first element
                        update_payload[dst_field] = value[0]
                else:
                    update_payload[dst_field] = value

        # Build technical_details JSON for architecture and availability
        technical_details = {}
        if (
            "architecture_pattern" in field_updates
            and field_updates["architecture_pattern"]
        ):
            technical_details["architecture_pattern"] = field_updates[
                "architecture_pattern"
            ]
        if (
            "availability_requirements" in field_updates
            and field_updates["availability_requirements"]
        ):
            technical_details["availability_requirements"] = field_updates[
                "availability_requirements"
            ]

        if technical_details:
            update_payload["technical_details"] = technical_details

        # Build custom_attributes JSON for stakeholder impact
        custom_attributes = {}
        if (
            "stakeholder_impact" in field_updates
            and field_updates["stakeholder_impact"]
        ):
            custom_attributes["stakeholder_impact"] = field_updates[
                "stakeholder_impact"
            ]

        if custom_attributes:
            update_payload["custom_attributes"] = custom_attributes

        # Set assessment readiness if minimum fields are present
        if {"environment", "business_criticality"}.issubset(field_updates.keys()):
            update_payload["assessment_readiness"] = "ready"

        return update_payload

    async def apply_resolved_gaps_to_assets(
        self, db: AsyncSession, collection_flow_id: uuid.UUID, context: Dict[str, Any]
    ) -> None:
        """Map resolved questionnaire gaps to Asset fields and set assessment readiness.

        Implementation highlights:
        - Tenant-scoped and UUID-typed filtering
        - Expanded whitelist mapping with parsing logic
        - JSON field handling for technical_details and custom_attributes
        - Compliance flags upsert to asset_compliance_flags table
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

        # CRITICAL FIX: Also query responses that don't have gap_id linked
        # This handles cases where responses were created but gap_id wasn't set
        resolved_rows = await db.execute(
            text(
                "SELECT DISTINCT "
                "COALESCE(g.field_name, r.question_id) AS field_name, "
                "r.response_value, "
                "r.asset_id, "
                "(g.metadata->>'asset_id') AS asset_id_hint, "
                "(g.metadata->>'application_name') AS app_name_hint "
                "FROM migration.collection_questionnaire_responses r "
                "LEFT JOIN migration.collection_data_gaps g ON g.id = r.gap_id "
                "WHERE r.collection_flow_id = :flow_id "
                "AND (g.resolution_status = 'resolved' OR r.gap_id IS NULL)"
                "AND r.response_value IS NOT NULL"
            ),
            {"flow_id": collection_flow_id},
        )
        resolved = resolved_rows.fetchall()
        if not resolved:
            logger.warning(
                f"No resolved gaps or responses found for flow {collection_flow_id}"
            )
            return

        field_updates = build_field_updates_from_rows(resolved)
        logger.info(f"📊 Field updates extracted from responses: {field_updates}")

        # Expanded whitelist with direct field mappings
        whitelist = {
            "environment": "environment",
            "business_criticality": "business_criticality",
            "business_owner": "business_owner",
            "department": "department",
            "application_name": "application_name",
            "technology_stack": "technology_stack",
            "operating_system_version": "operating_system",  # Map to operating_system column
            "cpu_cores": "cpu_cores",
            "memory_gb": "memory_gb",
            "storage_gb": "storage_gb",
        }

        asset_ids = await self._resolve_target_asset_ids(db, resolved, context)
        logger.info(f"🎯 Resolved asset IDs for write-back: {asset_ids}")
        if not asset_ids:
            logger.warning("⚠️ No asset IDs found, skipping write-back")
            return

        # Batch update assets
        for i in range(0, len(asset_ids), BATCH_SIZE):
            batch_ids = asset_ids[i : i + BATCH_SIZE]

            # Build update payload
            update_payload = self._build_update_payload(field_updates, whitelist)

            if not update_payload or not batch_ids:
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

            # Handle compliance_constraints separately for asset_compliance_flags table
            if (
                "compliance_constraints" in field_updates
                and field_updates["compliance_constraints"]
            ):
                compliance_scopes = field_updates["compliance_constraints"]
                if isinstance(compliance_scopes, str):
                    compliance_scopes = [compliance_scopes]

                await self._upsert_compliance_flags(
                    db, batch_ids, compliance_scopes, client_uuid, engagement_uuid
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
        """Resolve target asset IDs from gap metadata hints (asset_id/app_name) or response asset_id."""
        from app.models.asset import Asset

        hinted_asset_ids = set()
        for row in resolved_rows:
            # CRITICAL FIX: Check both asset_id from responses and asset_id_hint from gaps
            asset_id_from_response = getattr(row, "asset_id", None)
            if asset_id_from_response:
                hinted_asset_ids.add(str(asset_id_from_response))

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

    async def _upsert_compliance_flags(
        self,
        db: AsyncSession,
        asset_ids: List[uuid.UUID],
        compliance_scopes: List[str],
        client_uuid: UUID,
        engagement_uuid: UUID,
    ) -> None:
        """Upsert compliance flags for assets.

        Args:
            db: Database session
            asset_ids: List of asset IDs to update
            compliance_scopes: List of compliance requirements (e.g., ["GDPR", "HIPAA"])
            client_uuid: Client account UUID
            engagement_uuid: Engagement UUID
        """
        from app.models.asset_resilience import AssetComplianceFlags

        for asset_id in asset_ids:
            # Check if compliance flags record exists
            result = await db.execute(
                select(AssetComplianceFlags).where(
                    AssetComplianceFlags.asset_id == asset_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing record with new scopes (merge, not replace)
                existing_scopes = set(existing.compliance_scopes or [])
                new_scopes = existing_scopes.union(set(compliance_scopes))
                existing.compliance_scopes = list(new_scopes)
                await db.commit()
                logger.info(
                    f"Updated compliance flags for asset {asset_id}: {new_scopes}"
                )
            else:
                # Create new compliance flags record
                compliance_flags = AssetComplianceFlags(
                    asset_id=asset_id,
                    compliance_scopes=compliance_scopes,
                )
                db.add(compliance_flags)
                await db.commit()
                logger.info(
                    f"Created compliance flags for asset {asset_id}: {compliance_scopes}"
                )


# Create singleton instance for backward compatibility
asset_handlers = AssetHandlers()


# Export functions for backward compatibility
async def apply_resolved_gaps_to_assets(*args, **kwargs):
    return await asset_handlers.apply_resolved_gaps_to_assets(*args, **kwargs)


async def _resolve_target_asset_ids(*args, **kwargs):
    return await asset_handlers._resolve_target_asset_ids(*args, **kwargs)
