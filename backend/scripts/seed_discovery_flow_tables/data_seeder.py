"""
Data seeding operations for discovery flow tables.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from .constants import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    SAMPLE_DISCOVERY_FLOWS,
    SAMPLE_ASSETS,
)

logger = logging.getLogger(__name__)


async def seed_demo_data():
    """Seed the tables with demo data for testing"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🌱 Seeding demo data...")

            # Seed discovery flows
            for flow_data in SAMPLE_DISCOVERY_FLOWS:
                insert_flow_sql = """
                INSERT INTO discovery_flows (
                    flow_id, client_account_id, engagement_id, name, description,
                    current_phase, progress_percentage, status, raw_data,
                    field_mappings, asset_inventory, completion_timestamp
                ) VALUES (
                    :flow_id, :client_account_id, :engagement_id, :name, :description,
                    :current_phase, :progress_percentage, :status, :raw_data,
                    :field_mappings, :asset_inventory, :completion_timestamp
                )
                """

                await session.execute(
                    text(insert_flow_sql),
                    {
                        "flow_id": str(flow_data["flow_id"]),
                        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
                        "engagement_id": DEMO_ENGAGEMENT_ID,
                        "name": flow_data["name"],
                        "description": flow_data["description"],
                        "current_phase": flow_data["current_phase"],
                        "progress_percentage": flow_data["progress_percentage"],
                        "status": flow_data["status"],
                        "raw_data": flow_data.get("raw_data"),
                        "field_mappings": flow_data.get("field_mappings"),
                        "asset_inventory": flow_data.get("asset_inventory"),
                        "completion_timestamp": datetime.now(timezone.utc),
                    },
                )

            # Get the flow primary key for assets
            flow_pk_result = await session.execute(
                text("SELECT id FROM discovery_flows WHERE flow_id = :flow_id"),
                {"flow_id": str(SAMPLE_DISCOVERY_FLOWS[0]["flow_id"])},
            )
            flow_pk = flow_pk_result.scalar()

            # Seed discovery assets
            for asset_data in SAMPLE_ASSETS:
                insert_asset_sql = """
                INSERT INTO discovery_assets (
                    id, discovery_flow_id, client_account_id, name, asset_type,
                    asset_subtype, description, status, criticality,
                    quality_score, confidence_score, validation_status,
                    tech_debt_score, modernization_priority, six_r_recommendation,
                    migration_ready
                ) VALUES (
                    :id, :discovery_flow_id, :client_account_id, :name, :asset_type,
                    :asset_subtype, :description, :status, :criticality,
                    :quality_score, :confidence_score, :validation_status,
                    :tech_debt_score, :modernization_priority, :six_r_recommendation,
                    :migration_ready
                )
                """

                await session.execute(
                    text(insert_asset_sql),
                    {
                        "id": str(asset_data["id"]),
                        "discovery_flow_id": flow_pk,
                        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
                        "name": asset_data["name"],
                        "asset_type": asset_data["asset_type"],
                        "asset_subtype": asset_data.get("asset_subtype"),
                        "description": asset_data.get("description"),
                        "status": asset_data["status"],
                        "criticality": asset_data.get("criticality", "medium"),
                        "quality_score": asset_data.get("quality_score", 0.0),
                        "confidence_score": asset_data.get("confidence_score", 0.0),
                        "validation_status": asset_data.get(
                            "validation_status", "pending"
                        ),
                        "tech_debt_score": asset_data.get("tech_debt_score", 0.0),
                        "modernization_priority": asset_data.get(
                            "modernization_priority"
                        ),
                        "six_r_recommendation": asset_data.get("six_r_recommendation"),
                        "migration_ready": asset_data.get("migration_ready", False),
                    },
                )

            await session.commit()
            logger.info("✅ Demo data seeded successfully")

        except Exception as e:
            logger.error(f"❌ Error seeding data: {e}")
            await session.rollback()
            raise
