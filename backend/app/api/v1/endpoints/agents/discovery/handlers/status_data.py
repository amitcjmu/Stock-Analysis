"""
Data classification utilities for discovery status handlers.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


def _create_good_data_classification(
    latest_import, success_rate: float
) -> Dict[str, Any]:
    """Create classification for high quality data."""
    if success_rate >= 90:
        return {
            "id": f"good-data-{datetime.utcnow().timestamp()}",
            "type": "good_data",
            "title": "High Quality Records",
            "count": latest_import.processed_records,
            "percentage": success_rate,
            "description": (
                f"{latest_import.processed_records} records processed successfully "
                f"with {success_rate:.0f}% quality"
            ),
            "confidence": "high",
            "actionable": False,
            "agent_name": "Data Quality Analyst",
        }
    elif success_rate >= 70:
        return {
            "id": f"good-data-{datetime.utcnow().timestamp()}",
            "type": "good_data",
            "title": "Acceptable Quality Records",
            "count": latest_import.processed_records,
            "percentage": success_rate,
            "description": (
                f"{latest_import.processed_records} records with "
                f"{success_rate:.0f}% quality - good for migration"
            ),
            "confidence": "medium",
            "actionable": False,
            "agent_name": "Data Quality Analyst",
        }
    return None


def _create_needs_clarification_classification(
    latest_import, failed_records: int
) -> Dict[str, Any]:
    """Create classification for records needing review."""
    return {
        "id": f"needs-clarification-{datetime.utcnow().timestamp()}",
        "type": "needs_clarification",
        "title": "Records Requiring Review",
        "count": failed_records,
        "percentage": (
            (failed_records / latest_import.total_records * 100)
            if latest_import.total_records > 0
            else 0
        ),
        "description": f"{failed_records} records need data quality review before migration",
        "confidence": "high",
        "actionable": True,
        "agent_name": "Data Quality Analyst",
        "recommendations": [
            "Review data format",
            "Check for missing fields",
            "Validate data consistency",
            "Consider data cleansing steps",
        ],
    }


def _create_migration_ready_classification(latest_import) -> Dict[str, Any]:
    """Create classification for migration-ready assets."""
    return {
        "id": f"migration-ready-{datetime.utcnow().timestamp()}",
        "type": "migration_ready",
        "title": "Migration Ready Assets",
        "count": latest_import.processed_records,
        "percentage": 100.0,
        "description": f"All {latest_import.processed_records} processed records are ready for migration planning",
        "confidence": "high",
        "actionable": True,
        "agent_name": "Migration Readiness Analyst",
        "next_steps": [
            "Begin wave planning",
            "Assess migration complexity",
            "Review dependencies",
        ],
    }


async def _get_data_classifications(
    db: AsyncSession, context: RequestContext
) -> List[Dict[str, Any]]:
    """
    Get data classifications based on actual imported data quality.
    """
    try:
        if not context or not context.client_account_id or not context.engagement_id:
            return []

        # REMOVED: Data import functionality - models were removed
        # from app.models.data_import.core import DataImport
        #
        # query = (
        #     select(DataImport)
        #     .where(
        #         DataImport.client_account_id == uuid.UUID(context.client_account_id),
        #         DataImport.engagement_id == uuid.UUID(context.engagement_id),
        #     )
        #     .order_by(DataImport.created_at.desc())
        #     .limit(1)
        # )

        # Return empty list since data import is removed
        return []

    except Exception as e:
        logger.error(f"Error getting data classifications: {e}")
        return []


async def get_asset_count_by_status(
    db: AsyncSession, context: RequestContext
) -> Dict[str, int]:
    """Get asset counts grouped by status for the current context."""
    try:
        if not context or not context.client_account_id or not context.engagement_id:
            return {"discovered": 0, "pending": 0, "classified": 0}

        from app.models.asset import Asset

        # Count assets by status
        query = select(Asset).where(
            Asset.client_account_id == uuid.UUID(context.client_account_id),
            Asset.engagement_id == uuid.UUID(context.engagement_id),
        )

        result = await db.execute(query)
        assets = result.scalars().all()

        status_counts = {"discovered": 0, "pending": 0, "classified": 0}

        for asset in assets:
            if asset.status == "discovered":
                status_counts["discovered"] += 1
            elif asset.status == "pending":
                status_counts["pending"] += 1
            elif asset.asset_type and asset.asset_type != "unknown":
                status_counts["classified"] += 1

        return status_counts

    except Exception as e:
        logger.error(f"Error getting asset count by status: {e}")
        return {"discovered": 0, "pending": 0, "classified": 0}
