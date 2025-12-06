"""
Collection Asset Write-back Handlers
ADCS: Asset update and write-back operations for resolved gaps

Provides handler functions for applying resolved gap data to asset records.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .base import CollectionHandlerBase, build_field_updates_from_rows

logger = logging.getLogger(__name__)


class AssetHandlers(CollectionHandlerBase):
    """Handlers for asset write-back operations"""

    def _handle_integer_field(self, value: list, dst_field: str) -> Optional[int]:
        """Extract integer value from list for numeric fields.

        Args:
            value: List containing potential integer value
            dst_field: Target field name (for logging)

        Returns:
            Integer value or None if invalid
        """
        try:
            return int(value[0]) if value[0] else None
        except (ValueError, TypeError):
            logger.warning(f"Invalid value for {dst_field}: {value[0]}")
            return None

    def _handle_string_field(self, value: list, dst_field: str) -> Optional[Any]:
        """Extract string value from list, joining multiple values with comma.

        Args:
            value: List containing string values
            dst_field: The destination field name to check if it supports lists

        Returns:
            List for array-type fields, comma-joined string or first element for others
        """
        # For fields that are actual list types in the model, return the list
        if dst_field in ["technology_stack"]:
            return value

        if len(value) > 1:
            return ", ".join(str(v) for v in value)
        return str(value[0]) if value[0] else None

    def _process_list_value(self, value: list, dst_field: str) -> Optional[Any]:
        """Process list values based on field type.

        Args:
            value: List value to process
            dst_field: Target field name

        Returns:
            Processed value or None if invalid
        """
        if len(value) == 0:
            return None

        # Integer fields
        if dst_field in ["cpu_cores", "memory_gb", "storage_gb"]:
            return self._handle_integer_field(value, dst_field)

        # String fields that may have multiple values
        if dst_field in [
            "technology_stack",
            "business_owner",
            "department",
            "application_name",
        ]:
            return self._handle_string_field(value, dst_field)

        # Default: take first element
        return value[0]

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
                # Handle list values - extract first element for single-value fields
                if isinstance(value, list):
                    processed_value = self._process_list_value(value, dst_field)
                    if processed_value is not None:
                        update_payload[dst_field] = processed_value
                else:
                    update_payload[dst_field] = value

        # ✅ FIX 0.3: Build technical_details JSON comprehensively
        # These fields go into the technical_details JSONB column
        technical_details = {}
        technical_fields = [
            "architecture_pattern",
            "availability_requirements",
            "data_quality",
            "integration_complexity",
            "api_endpoints",
            "monitoring_enabled",
            "logging_enabled",
        ]
        for field in technical_fields:
            if field in field_updates and field_updates[field]:
                technical_details[field] = field_updates[field]

        if technical_details:
            update_payload["technical_details"] = technical_details

        # ✅ FIX 0.3: Build custom_attributes JSON comprehensively
        # These fields go into the custom_attributes JSONB column
        custom_attributes = {}
        custom_fields = [
            "stakeholder_impact",
            "vm_type",
            "custom_tags",
            "notes",
        ]
        for field in custom_fields:
            if field in field_updates and field_updates[field]:
                custom_attributes[field] = field_updates[field]

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
        # CC FIX Bug #11: Remove non-existent client_account_id and engagement_id columns
        # Tenant scoping is already enforced via collection_flow_id FK relationship
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
                "AND (g.resolution_status = 'resolved' OR r.gap_id IS NULL) "
                "AND r.response_value IS NOT NULL"
            ),
            {
                "flow_id": collection_flow_id,
            },
        )
        resolved = resolved_rows.fetchall()
        if not resolved:
            logger.warning(
                f"No resolved gaps or responses found for flow {collection_flow_id}"
            )
            return

        field_updates = build_field_updates_from_rows(resolved)
        logger.info(f"📊 Field updates extracted from responses: {field_updates}")

        # ✅ FIX 0.3: Comprehensive Whitelist (Issue #980 - Critical Bug Fix)
        # Expanded from 10 fields to ~55 fields to cover all Asset model columns
        # that can be populated via questionnaire responses
        whitelist = {
            # === IDENTIFICATION FIELDS ===
            "name": "name",
            "asset_name": "asset_name",
            "hostname": "hostname",
            "asset_type": "asset_type",
            "description": "description",
            "fqdn": "fqdn",
            # === BUSINESS CONTEXT FIELDS ===
            "environment": "environment",
            "business_criticality": "business_criticality",
            "business_owner": "business_owner",
            "business_unit": "business_unit",
            "department": "department",
            "application_name": "application_name",
            "application_type": "application_type",
            "server_role": "server_role",
            # === TECHNOLOGY STACK FIELDS ===
            "technology_stack": "technology_stack",
            "operating_system": "operating_system",
            "operating_system_version": "operating_system",  # Alias for backward compat
            "os_version": "os_version",
            "database_type": "database_type",
            "database_version": "database_version",
            # === INFRASTRUCTURE FIELDS ===
            "cpu_cores": "cpu_cores",
            "memory_gb": "memory_gb",
            "storage_gb": "storage_gb",
            "storage_used_gb": "storage_used_gb",
            "storage_free_gb": "storage_free_gb",
            "database_size_gb": "database_size_gb",
            "virtualization_platform": "virtualization_platform",
            "virtualization_type": "virtualization_type",
            # === NETWORK FIELDS ===
            "ip_address": "ip_address",
            "mac_address": "mac_address",
            # === LOCATION FIELDS ===
            "datacenter": "datacenter",
            "location": "location",
            "rack_location": "rack_location",
            "availability_zone": "availability_zone",
            "security_zone": "security_zone",
            # === COST & PERFORMANCE FIELDS ===
            "current_monthly_cost": "current_monthly_cost",
            "annual_cost_estimate": "annual_cost_estimate",
            "estimated_cloud_cost": "estimated_cloud_cost",
            "cpu_utilization_percent": "cpu_utilization_percent",
            "memory_utilization_percent": "memory_utilization_percent",
            "network_throughput_mbps": "network_throughput_mbps",
            "disk_iops": "disk_iops",
            # === ASSESSMENT FIELDS ===
            "assessment_readiness": "assessment_readiness",
            "assessment_readiness_score": "assessment_readiness_score",
            "migration_complexity": "migration_complexity",
            "migration_priority": "migration_priority",
            "six_r_strategy": "six_r_strategy",
            "wave_number": "wave_number",
            "business_logic_complexity": "business_logic_complexity",
            "configuration_complexity": "configuration_complexity",
            "change_tolerance": "change_tolerance",
            "data_volume_characteristics": "data_volume_characteristics",
            "user_load_patterns": "user_load_patterns",
            # === DATA CLASSIFICATION & COMPLIANCE ===
            "application_data_classification": "application_data_classification",
            "pii_flag": "pii_flag",
            # === LIFECYCLE & EOL FIELDS ===
            "eol_date": "eol_date",
            "eol_risk_level": "eol_risk_level",
            "eol_technology_assessment": "eol_technology_assessment",
            "lifecycle": "lifecycle",
            # === BACKUP & RESILIENCE ===
            "backup_policy": "backup_policy",
            # === DISCOVERY METADATA ===
            "discovery_source": "discovery_source",
            "discovery_method": "discovery_method",
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
            # CC FIX Bug #11: Don't commit here - let caller manage transaction atomicity
            # The caller (_commit_with_writeback) commits all changes atomically together
            try:
                await db.execute(stmt)
                # ❌ REMOVED: await db.commit() - breaks atomic transaction in caller
                logger.info(f"✅ Staged asset updates for {len(batch_ids)} asset(s)")
            except Exception:
                # ❌ REMOVED: await db.rollback() - caller will handle rollback
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
                raise  # Re-raise to let caller handle transaction rollback

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
                # CC FIX Bug #11: Don't commit - let caller manage transaction
                logger.info(
                    f"Staged compliance flags update for asset {asset_id}: {new_scopes}"
                )
            else:
                # Create new compliance flags record
                compliance_flags = AssetComplianceFlags(
                    asset_id=asset_id,
                    compliance_scopes=compliance_scopes,
                )
                db.add(compliance_flags)
                # CC FIX Bug #11: Don't commit - let caller manage transaction
                logger.info(
                    f"Staged compliance flags creation for asset {asset_id}: {compliance_scopes}"
                )


# Create singleton instance for backward compatibility
asset_handlers = AssetHandlers()


# Export functions for backward compatibility
async def apply_resolved_gaps_to_assets(*args, **kwargs):
    return await asset_handlers.apply_resolved_gaps_to_assets(*args, **kwargs)


async def _resolve_target_asset_ids(*args, **kwargs):
    return await asset_handlers._resolve_target_asset_ids(*args, **kwargs)
