"""
Collection Data Processing Handlers
ADCS: Data normalization, gap analysis, and synthesis handlers

Provides handler functions for data processing operations including normalization,
gap analysis preparation, gap prioritization, and synthesis preparation.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .base import (
    CollectionHandlerBase,
    normalize_platform_data,
    build_field_updates_from_rows,
)

logger = logging.getLogger(__name__)


class DataHandlers(CollectionHandlerBase):
    """Handlers for data processing and normalization"""

    async def collection_data_normalization(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize collected data after automated collection"""
        try:
            crew_results = phase_results.get("crew_results", {})
            collected_data = crew_results.get("collected_data", {})

            logger.info(f"🔄 Normalizing data from {len(collected_data)} platforms")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Store collected data in inventory
            for platform_id, platform_data in collected_data.items():
                inventory_data = {
                    "id": uuid.uuid4(),
                    "collection_flow_id": collection_flow["id"],
                    "platform": platform_id,
                    "collection_method": "automated",
                    "raw_data": platform_data,
                    "normalized_data": normalize_platform_data(platform_data),
                    "data_type": platform_data.get("data_type", "mixed"),
                    "resource_count": len(platform_data.get("resources", [])),
                    "quality_score": crew_results.get("quality_scores", {}).get(
                        platform_id, 0.0
                    ),
                    "validation_status": "validated",
                    "metadata": {
                        "collection_timestamp": datetime.utcnow().isoformat(),
                        "adapter_used": platform_data.get("adapter_name"),
                    },
                    "collected_at": datetime.utcnow(),
                }

                # Insert into collected_data_inventory
                insert_query = """
                    INSERT INTO collected_data_inventory
                    (id, collection_flow_id, platform, collection_method, raw_data,
                     normalized_data, data_type, resource_count, quality_score,
                     validation_status, metadata, collected_at)
                    VALUES
                    (:id, :collection_flow_id, :platform, :collection_method, :raw_data::jsonb,
                     :normalized_data::jsonb, :data_type, :resource_count, :quality_score,
                     :validation_status, :metadata::jsonb, :collected_at)
                """

                await db.execute(insert_query, inventory_data)

            await db.commit()

            return {
                "success": True,
                "platforms_normalized": len(collected_data),
                "total_resources": sum(
                    len(d.get("resources", [])) for d in collected_data.values()
                ),
            }

        except Exception as e:
            logger.error(f"❌ Data normalization failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def gap_analysis_preparation(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_input: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare for gap analysis"""
        try:
            logger.info("🔍 Preparing gap analysis")

            # Load collected data from inventory
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Query collected data
            query = """
                SELECT platform, normalized_data, quality_score, resource_count
                FROM collected_data_inventory
                WHERE collection_flow_id = :collection_flow_id
            """

            result = await db.execute(
                query, {"collection_flow_id": collection_flow["id"]}
            )
            collected_data = result.fetchall()

            # Prepare data for gap analysis
            analysis_data = {
                "platforms": {},
                "total_resources": 0,
                "average_quality": 0.0,
            }

            quality_scores = []
            for row in collected_data:
                analysis_data["platforms"][row.platform] = {
                    "data": row.normalized_data,
                    "quality_score": row.quality_score,
                    "resource_count": row.resource_count,
                }
                analysis_data["total_resources"] += row.resource_count
                quality_scores.append(row.quality_score)

            if quality_scores:
                analysis_data["average_quality"] = sum(quality_scores) / len(
                    quality_scores
                )

            return {
                "success": True,
                "analysis_data": analysis_data,
                "platform_count": len(analysis_data["platforms"]),
            }

        except Exception as e:
            logger.error(f"❌ Gap analysis preparation failed: {e}")
            return {"success": False, "error": str(e)}

    async def gap_prioritization(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prioritize identified gaps"""
        try:
            crew_results = phase_results.get("crew_results", {})
            identified_gaps = crew_results.get("data_gaps", [])

            logger.info(f"📊 Prioritizing {len(identified_gaps)} identified gaps")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Store gaps in database
            for gap in identified_gaps:
                gap_data = {
                    "id": uuid.uuid4(),
                    "collection_flow_id": collection_flow["id"],
                    "gap_type": gap.get("type", "missing_data"),
                    "gap_category": gap.get("category", "general"),
                    "field_name": gap.get("field_name", "unknown"),
                    "description": gap.get("description", ""),
                    "impact_on_sixr": gap.get("sixr_impact", "medium"),
                    "priority": gap.get("priority", 5),
                    "suggested_resolution": gap.get("resolution", ""),
                    "resolution_status": "pending",
                    "metadata": {
                        "platform": gap.get("platform"),
                        "resource_type": gap.get("resource_type"),
                        "detection_method": gap.get("detection_method", "ai_analysis"),
                    },
                    "created_at": datetime.utcnow(),
                }

                insert_query = """
                    INSERT INTO collection_data_gaps
                    (id, collection_flow_id, gap_type, gap_category, field_name,
                     description, impact_on_sixr, priority, suggested_resolution,
                     resolution_status, metadata, created_at)
                    VALUES
                    (:id, :collection_flow_id, :gap_type, :gap_category, :field_name,
                     :description, :impact_on_sixr, :priority, :suggested_resolution,
                     :resolution_status, :metadata::jsonb, :created_at)
                """

                await db.execute(insert_query, gap_data)

            await db.commit()

            # Calculate gap statistics
            high_priority_gaps = len(
                [g for g in identified_gaps if g.get("priority", 0) >= 8]
            )
            critical_sixr_gaps = len(
                [g for g in identified_gaps if g.get("sixr_impact") == "high"]
            )

            return {
                "success": True,
                "total_gaps": len(identified_gaps),
                "high_priority_gaps": high_priority_gaps,
                "critical_sixr_gaps": critical_sixr_gaps,
            }

        except Exception as e:
            logger.error(f"❌ Gap prioritization failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def synthesis_preparation(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_input: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare data for synthesis"""
        try:
            logger.info("🔄 Preparing data synthesis")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Load all collected data
            collected_query = """
                SELECT platform, collection_method, normalized_data, quality_score
                FROM collected_data_inventory
                WHERE collection_flow_id = :collection_flow_id
            """

            result = await db.execute(
                collected_query, {"collection_flow_id": collection_flow["id"]}
            )
            collected_data = result.fetchall()

            # Load resolved gaps
            gaps_query = """
                SELECT g.field_name, g.platform, r.response_value, r.confidence_score
                FROM collection_data_gaps g
                JOIN collection_questionnaire_responses r ON g.id = r.gap_id
                WHERE g.collection_flow_id = :collection_flow_id
                AND g.resolution_status = 'resolved'
            """

            result = await db.execute(
                gaps_query, {"collection_flow_id": collection_flow["id"]}
            )
            resolved_gaps = result.fetchall()

            # Prepare synthesis input
            synthesis_data = {
                "automated_data": {},
                "manual_data": {},
                "platform_summary": {},
            }

            # Process automated collection data
            for row in collected_data:
                if row.collection_method == "automated":
                    synthesis_data["automated_data"][row.platform] = {
                        "data": row.normalized_data,
                        "quality_score": row.quality_score,
                    }

            # Process manual collection data
            for gap in resolved_gaps:
                platform = gap.platform or "general"
                if platform not in synthesis_data["manual_data"]:
                    synthesis_data["manual_data"][platform] = {}

                synthesis_data["manual_data"][platform][gap.field_name] = {
                    "value": gap.response_value,
                    "confidence": gap.confidence_score,
                }

            return {
                "success": True,
                "synthesis_data": synthesis_data,
                "automated_platforms": len(synthesis_data["automated_data"]),
                "manual_fields": sum(
                    len(fields) for fields in synthesis_data["manual_data"].values()
                ),
            }

        except Exception as e:
            logger.error(f"❌ Synthesis preparation failed: {e}")
            return {"success": False, "error": str(e)}


# Create singleton instance for backward compatibility
data_handlers = DataHandlers()


# Export functions for backward compatibility
async def collection_data_normalization(*args, **kwargs):
    return await data_handlers.collection_data_normalization(*args, **kwargs)


async def gap_analysis_preparation(*args, **kwargs):
    return await data_handlers.gap_analysis_preparation(*args, **kwargs)


async def gap_prioritization(*args, **kwargs):
    return await data_handlers.gap_prioritization(*args, **kwargs)


async def synthesis_preparation(*args, **kwargs):
    return await data_handlers.synthesis_preparation(*args, **kwargs)
