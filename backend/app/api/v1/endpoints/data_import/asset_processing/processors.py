"""
Asset processing logic.
Handles raw record processing, agentic intelligence, and fallback processing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.asset import Asset
from app.models.data_import import RawImportRecord

from .utils import determine_asset_type_agentic

logger = logging.getLogger(__name__)


async def process_single_raw_record_agentic(
    record: RawImportRecord,
    field_mappings: Dict[str, str],
    asset_classifications: List[Dict[str, Any]],
    context: RequestContext,
) -> Dict[str, Any]:
    """Process a single raw record using agentic CrewAI intelligence."""

    raw_data = record.raw_data

    # Apply agentic field mappings
    mapped_data = {}
    for source_field, canonical_field in field_mappings.items():
        if source_field in raw_data:
            mapped_data[canonical_field.lower().replace(" ", "_")] = raw_data[
                source_field
            ]

    # Find agentic asset classification for this record
    asset_classification = None
    for classification in asset_classifications:
        # Match by hostname, name, or other identifier
        if (
            classification.get("hostname") == raw_data.get("hostname")
            or classification.get("name") == raw_data.get("name")
            or classification.get("asset_name") == raw_data.get("asset_name")
        ):
            asset_classification = classification
            break

    # Build CMDBAsset data using agentic intelligence
    asset_data = {
        "id": uuid.uuid4(),
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        # Core identification using agentic field mapping
        "name": (
            mapped_data.get("asset_name")
            or mapped_data.get("hostname")
            or raw_data.get("hostname")
            or raw_data.get("name")
            or f"Asset_{record.row_number}"
        ),
        "hostname": mapped_data.get("hostname") or raw_data.get("hostname"),
        "asset_type": determine_asset_type_agentic(raw_data, asset_classification),
        # Infrastructure details from agentic mapping
        "ip_address": mapped_data.get("ip_address") or raw_data.get("ip_address"),
        "operating_system": mapped_data.get("operating_system") or raw_data.get("os"),
        "environment": mapped_data.get("environment") or raw_data.get("environment"),
        # Business information from agentic analysis
        "business_owner": mapped_data.get("business_owner")
        or raw_data.get("business_owner"),
        "department": mapped_data.get("department") or raw_data.get("department"),
        # Migration assessment from agentic intelligence
        "sixr_ready": (
            asset_classification.get("sixr_readiness")
            if asset_classification
            else "Pending Analysis"
        ),
        "migration_complexity": (
            asset_classification.get("migration_complexity")
            if asset_classification
            else "Unknown"
        ),
        # Source and processing metadata
        "discovery_source": "agentic_cmdb_import",
        "discovery_method": "crewai_flow",
        "discovery_timestamp": datetime.utcnow(),
        "imported_by": context.user_id,
        "imported_at": datetime.utcnow(),
        "source_filename": f"import_session_{record.data_import_id}",
        "raw_data": raw_data,
        "field_mappings_used": field_mappings,
        # Audit
        "created_at": datetime.utcnow(),
        "created_by": context.user_id,
        "is_mock": False,
    }

    return asset_data


async def fallback_raw_to_assets_processing(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> dict:
    """
    Fallback asset processing when CrewAI Flow is not available.
    Creates basic assets without AI intelligence.
    """
    logger.warning("🔄 Using fallback processing - CrewAI Flow not available")

    try:
        # Get raw records
        raw_records_query = await db.execute(
            select(RawImportRecord).where(RawImportRecord.data_import_id == flow_id)
        )
        raw_records = raw_records_query.scalars().all()

        if not raw_records:
            return {
                "status": "error",
                "message": "No raw import records found",
                "flow_id": flow_id,
            }

        processed_count = 0
        created_assets = []

        for record in raw_records:
            if record.asset_id is not None:
                continue  # Already processed

            # Simple asset creation without AI
            raw_data = record.raw_data

            asset = Asset(
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                name=raw_data.get(
                    "NAME", raw_data.get("name", f"Asset_{record.row_number}")
                ),
                hostname=raw_data.get("hostname"),
                asset_type=raw_data.get("CITYPE", "server").lower(),
                ip_address=raw_data.get("IP_ADDRESS"),
                operating_system=raw_data.get("OS"),
                environment=raw_data.get("ENVIRONMENT", "Unknown"),
                discovery_source="fallback_cmdb_import",
                discovery_method="basic_mapping",
                discovered_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )

            db.add(asset)
            await db.flush()

            record.asset_id = asset.id
            record.is_processed = True
            record.processed_at = datetime.utcnow()
            record.processing_notes = (
                f"Processed by fallback method (non-agentic) - CrewAI Flow was not available. "
                f"Created basic asset with CITYPE: {raw_data.get('CITYPE', 'server')}"
            )

            created_assets.append(str(asset.id))
            processed_count += 1

        await db.commit()

        logger.info(
            f"✅ Fallback processing completed: {processed_count} assets created"
        )

        return {
            "status": "success",
            "message": (
                f"⚠️ Fallback processing completed. Created {processed_count} basic assets without AI intelligence. "
                f"Consider enabling CrewAI Flow for enhanced classification."
            ),
            "processed_count": processed_count,
            "flow_id": "fallback_processing",
            "processing_status": "completed",
            "progress_percentage": 100.0,
            "agentic_intelligence": {
                "crewai_flow_active": False,
                "unified_service": False,
                "modular_handlers": False,
                "database_integration": True,
                "workflow_progression": False,
                "state_management": False,
                "processing_method": "fallback_basic_mapping",
            },
            "classification_results": {
                "applications": 0,
                "servers": processed_count,  # Default to servers
                "databases": 0,
                "other_assets": 0,
            },
            "processed_asset_ids": created_assets,
            "completed_at": datetime.utcnow().isoformat(),
            "duplicate_detection": {
                "detection_active": False,
                "duplicates_found": False,
                "detection_method": "none",
            },
        }

    except Exception as e:
        await db.rollback()
        logger.error(safe_log_format("Fallback processing failed: {e}", e=e))
        raise HTTPException(
            status_code=500, detail=f"Fallback processing failed: {str(e)}"
        )
