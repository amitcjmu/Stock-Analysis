"""
Field Mapping Retrieval Service
Handles GET operations for field mappings
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import ImportFieldMapping
from app.utils.json_utils import safe_json_dumps

from ..models.mapping_schemas import FieldMappingResponse

logger = logging.getLogger(__name__)


class MappingRetrievalService:
    """Service for retrieving field mappings"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def get_field_mappings(
        self, import_id: str
    ) -> List[FieldMappingResponse]:  # noqa: C901
        """Get all field mappings for an import."""

        # Convert string UUIDs to UUID objects if needed
        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for import_id: {import_id}")

        # CRITICAL FIX: Handle both direct import_id lookup AND discovery flow lookup
        # First try direct import_id lookup
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()

        # If no mappings found, the import_id might be a flow_id - try discovery flow lookup
        if not mappings:
            logger.info(
                f"🔍 No mappings found for direct import_id {import_id}, trying discovery flow lookup..."
            )
            mappings = await self._lookup_via_discovery_flow(
                import_uuid, client_account_uuid
            )

        # Filter test data and serialize
        return await self._filter_and_serialize_mappings(mappings, import_id)

    async def _lookup_via_discovery_flow(
        self, flow_uuid: UUID, client_account_uuid: UUID
    ) -> list:
        """Try to find mappings via discovery flow"""
        from app.models.discovery_flow import DiscoveryFlow

        # Look for discovery flow with this flow_id
        flow_query = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == client_account_uuid,
            )
        )
        flow_result = await self.db.execute(flow_query)
        discovery_flow = flow_result.scalar_one_or_none()

        if discovery_flow and discovery_flow.data_import_id:
            logger.info(
                f"✅ Found discovery flow, using data_import_id: {discovery_flow.data_import_id}"
            )

            # Try again with the actual data_import_id from discovery flow
            query = select(ImportFieldMapping).where(
                and_(
                    ImportFieldMapping.data_import_id == discovery_flow.data_import_id,
                    ImportFieldMapping.client_account_id == client_account_uuid,
                )
            )
            result = await self.db.execute(query)
            return result.scalars().all()

        # If still no mappings, try master_flow_id lookup as last resort
        if discovery_flow and discovery_flow.master_flow_id:
            return await self._lookup_via_master_flow(
                discovery_flow.master_flow_id, client_account_uuid
            )

        return []

    async def _lookup_via_master_flow(
        self, master_flow_id: UUID, client_account_uuid: UUID
    ) -> list:
        """Try to find mappings via master_flow_id"""
        logger.info(f"🔍 Trying master_flow_id lookup: {master_flow_id}")

        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.data_import import DataImport

        # Get the database ID for this master_flow_id (FK references id, not flow_id)
        db_id_query = select(CrewAIFlowStateExtensions.id).where(
            CrewAIFlowStateExtensions.flow_id == master_flow_id
        )
        db_id_result = await self.db.execute(db_id_query)
        flow_db_id = db_id_result.scalar_one_or_none()

        if not flow_db_id:
            return []

        # Look for data imports with this master_flow_id
        import_query = (
            select(DataImport)
            .where(
                and_(
                    DataImport.master_flow_id == flow_db_id,
                    DataImport.client_account_id == client_account_uuid,
                )
            )
            .order_by(DataImport.created_at.desc())
            .limit(1)
        )

        import_result = await self.db.execute(import_query)
        data_import = import_result.scalar_one_or_none()

        if not data_import:
            return []

        logger.info(f"✅ Found data import via master_flow_id: {data_import.id}")

        # Final attempt with the found data import ID
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == data_import.id,
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _filter_and_serialize_mappings(
        self, mappings: list, import_id: str
    ) -> List[FieldMappingResponse]:
        """Filter test data and serialize mappings"""
        # CRITICAL SECURITY FIX: Prevent test data contamination
        production_mappings = []
        test_data_filtered = 0

        for mapping in mappings:
            # Check for test data patterns that should never appear in production
            is_test_data = mapping.source_field and (
                str(mapping.source_field).startswith("__test_")
                or str(mapping.source_field).startswith("_test_")
                or str(mapping.source_field)
                in ["_mock_data", "test_field", "sample_data"]
            )

            if is_test_data:
                logger.warning(
                    f"🚫 Filtering out test data field mapping: {mapping.source_field} "
                    f"(ID: {mapping.id}, Import: {import_id})"
                )
                test_data_filtered += 1
                continue

            production_mappings.append(mapping)

        if test_data_filtered > 0:
            logger.error(
                f"❌ CRITICAL: Found {test_data_filtered} test data field mappings in production! "
                f"Import ID: {import_id}. These have been filtered out."
            )

        logger.info(
            f"🔍 Field mapping validation: {len(mappings)} total, "
            f"{len(production_mappings)} production, {test_data_filtered} test data filtered"
        )

        # Serialize to response models
        valid_mappings = []
        for mapping in production_mappings:
            # Convert JSON transformation_rules to string, handle None values
            transformation_rule_str = None
            if mapping.transformation_rules:
                if isinstance(mapping.transformation_rules, dict):
                    transformation_rule_str = safe_json_dumps(
                        mapping.transformation_rules
                    )
                elif isinstance(mapping.transformation_rules, str):
                    transformation_rule_str = mapping.transformation_rules
                else:
                    transformation_rule_str = str(mapping.transformation_rules)

            valid_mappings.append(
                FieldMappingResponse(
                    id=mapping.id,
                    source_field=str(mapping.source_field),
                    target_field=str(mapping.target_field),
                    transformation_rule=transformation_rule_str,
                    validation_rule=None,
                    is_required=getattr(mapping, "is_required", False),
                    is_approved=mapping.status == "approved",
                    confidence=(
                        float(mapping.confidence_score)
                        if mapping.confidence_score is not None
                        else 0.0
                    ),
                    created_at=mapping.created_at,
                    updated_at=mapping.updated_at,
                )
            )

        logger.info(
            f"✅ Returning {len(valid_mappings)} field mappings for import {import_id}"
        )
        return valid_mappings
