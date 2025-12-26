"""
Agent insights utilities for discovery status handlers.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

# REMOVED: Unused imports - data import functionality was removed
# from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


def _get_fallback_agent_insights() -> List[Dict[str, Any]]:
    """Get fallback insights when dynamic insights are unavailable."""
    return [
        {
            "id": f"fallback-discovery-{datetime.utcnow().timestamp()}",
            "agent_id": "discovery-coordinator",
            "agent_name": "Discovery Coordinator",
            "insight_type": "system_status",
            "title": "Discovery System Ready",
            "description": "System is ready for data discovery and analysis",
            "confidence": "high",
            "supporting_data": {"system_ready": True, "components_active": 3},
            "actionable": True,
            "page": "home",
            "created_at": datetime.utcnow().isoformat(),
            "agent": "Discovery Coordinator",
            "insight": "System is ready for data discovery and analysis",
            "priority": "medium",
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "fallback_system_status",
        }
    ]


def _get_cached_agent_insights(
    client_account_id: str = None, engagement_id: str = None
):
    """Get cached fallback insights scoped by context."""
    # Return fresh fallback per context to avoid cross-tenant leakage
    return _get_fallback_agent_insights()


def _create_field_mapping_insight(mappings, latest_import) -> Dict[str, Any]:
    """Create field mapping insight from mapping data."""
    mapped_fields = len([m for m in mappings if m.target_field])
    total_fields = len(mappings)
    mapping_percentage = (mapped_fields / total_fields * 100) if total_fields > 0 else 0

    confidence_score = 0.9 if mapping_percentage > 80 else 0.7
    confidence_level = (
        "high"
        if confidence_score > 0.8
        else "medium" if confidence_score > 0.6 else "low"
    )

    return {
        "id": f"field-mapping-{datetime.utcnow().timestamp()}",
        "agent_id": "field-mapping-expert",
        "agent_name": "Field Mapping Expert",
        "insight_type": "migration_readiness",
        "title": "Field Mapping Progress",
        "description": (
            f"{mapped_fields} of {total_fields} fields mapped "
            f"({mapping_percentage:.0f}% completion)"
        ),
        "confidence": confidence_level,
        "supporting_data": {
            "mapped_fields": mapped_fields,
            "total_fields": total_fields,
            "percentage": mapping_percentage,
        },
        "actionable": mapping_percentage < 100,
        "page": "attribute-mapping",
        "created_at": datetime.utcnow().isoformat(),
        "agent": "Field Mapping Expert",
        "insight": (
            f"{mapped_fields} of {total_fields} fields mapped "
            f"({mapping_percentage:.0f}% completion)"
        ),
        "priority": "high" if mapping_percentage < 50 else "medium",
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": "actual_import_analysis",
    }


def _create_data_quality_insight(latest_import) -> Dict[str, Any]:
    """Create data quality insight from import data."""
    quality_score = (
        (latest_import.processed_records / latest_import.total_records * 100)
        if latest_import.total_records > 0
        else 0
    )
    quality_confidence = (
        "high" if quality_score > 90 else "medium" if quality_score > 70 else "low"
    )

    return {
        "id": f"data-quality-{datetime.utcnow().timestamp()}",
        "agent_id": "data-quality-analyst",
        "agent_name": "Data Quality Analyst",
        "insight_type": "quality_assessment",
        "title": "Data Processing Quality",
        "description": (
            f"{latest_import.processed_records} of {latest_import.total_records} "
            f"records processed successfully ({quality_score:.0f}% quality)"
        ),
        "confidence": quality_confidence,
        "supporting_data": {
            "processed_records": latest_import.processed_records,
            "total_records": latest_import.total_records,
            "quality_score": quality_score,
        },
        "actionable": quality_score < 90,
        "page": "attribute-mapping",
        "created_at": datetime.utcnow().isoformat(),
        "agent": "Data Quality Analyst",
        "insight": (
            f"{latest_import.processed_records} of {latest_import.total_records} "
            f"records processed successfully ({quality_score:.0f}% quality)"
        ),
        "priority": "high" if quality_score < 90 else "medium",
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": "actual_import_quality",
    }


def _create_asset_classification_insight(latest_import) -> Dict[str, Any]:
    """Create asset classification insight from import data."""
    return {
        "id": f"asset-classification-{datetime.utcnow().timestamp()}",
        "agent_id": "asset-classification-specialist",
        "agent_name": "Asset Classification Specialist",
        "insight_type": "organizational_patterns",
        "title": "Asset Classification Readiness",
        "description": (
            f"Ready to classify {latest_import.total_records} assets "
            f"from '{latest_import.import_name}'"
        ),
        "confidence": "high",
        "supporting_data": {
            "total_assets": latest_import.total_records,
            "import_name": latest_import.import_name,
            "classification_ready": True,
        },
        "actionable": True,
        "page": "asset-inventory",
        "created_at": datetime.utcnow().isoformat(),
        "agent": "Asset Classification Specialist",
        "insight": (
            f"Ready to classify {latest_import.total_records} assets "
            f"from '{latest_import.import_name}'"
        ),
        "priority": "high",
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": "import_summary",
    }


async def _get_dynamic_agent_insights(
    db: AsyncSession, context: RequestContext
) -> List[Dict[str, Any]]:
    """Get dynamic agent insights based on actual imported data."""
    try:
        if not context or not context.client_account_id or not context.engagement_id:
            return _get_fallback_agent_insights()

        # REMOVED: Data import functionality - models were removed
        # import uuid
        # from app.models.data_import import DataImport
        #
        # latest_import_query = (
        #     select(DataImport)
        #     .where(
        #         and_(
        #             DataImport.client_account_id
        #             == uuid.UUID(context.client_account_id),
        #             DataImport.engagement_id == uuid.UUID(context.engagement_id),
        #         )
        #     )
        #     .order_by(
        #         DataImport.total_records.desc(),
        #         DataImport.created_at.desc(),
        #     )
        #     .limit(1)
        # )
        #
        # result = await db.execute(latest_import_query)
        # latest_import = result.scalar_one_or_none()
        #
        # if not latest_import:
        #     return _get_fallback_agent_insights()
        #
        # # Get field mappings for this import
        # from app.models.data_import import ImportFieldMapping
        #
        # mappings_query = select(ImportFieldMapping).where(
        #     ImportFieldMapping.data_import_id == latest_import.id
        # )
        # mappings_result = await db.execute(mappings_query)
        # mappings = mappings_result.scalars().all()

        # Return fallback since data import is removed
        return _get_fallback_agent_insights()

    except Exception as e:
        logger.error(f"Error generating dynamic agent insights: {e}")
        return _get_fallback_agent_insights()
