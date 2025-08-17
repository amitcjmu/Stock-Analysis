"""
Collection Data Processing Pipelines
Handles data processing operations including normalization, preparation, and synthesis.

Generated with CC for backend collection handler modularization.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CollectionHandlerBase, normalize_platform_data

logger = logging.getLogger(__name__)


class DataProcessors(CollectionHandlerBase):
    """Data processing pipeline handlers for collection flows"""

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

    async def response_processing(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process questionnaire responses"""
        try:
            crew_results = phase_results.get("crew_results", {})
            responses = crew_results.get("responses", {})

            logger.info(f"✅ Processing {len(responses)} questionnaire responses")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Update questionnaire responses
            for gap_id, response in responses.items():
                update_query = """
                    UPDATE collection_questionnaire_responses
                    SET response_value = :response_value::jsonb,
                        confidence_score = :confidence_score,
                        validation_status = :validation_status,
                        responded_by = :responded_by,
                        responded_at = :responded_at,
                        updated_at = :updated_at
                    WHERE collection_flow_id = :collection_flow_id
                    AND gap_id = :gap_id
                """

                await db.execute(
                    update_query,
                    {
                        "response_value": response.get("value", {}),
                        "confidence_score": response.get("confidence", 0.0),
                        "validation_status": (
                            "validated"
                            if response.get("is_valid", False)
                            else "pending"
                        ),
                        "responded_by": context["user_id"],
                        "responded_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "collection_flow_id": collection_flow["id"],
                        "gap_id": gap_id,
                    },
                )

                # Update gap resolution status
                if response.get("is_valid", False):
                    gap_update_query = """
                        UPDATE collection_data_gaps
                        SET resolution_status = 'resolved',
                            resolved_at = :resolved_at,
                            resolved_by = 'manual_collection'
                        WHERE id = :gap_id
                    """

                    await db.execute(
                        gap_update_query,
                        {"resolved_at": datetime.utcnow(), "gap_id": gap_id},
                    )

            await db.commit()

            # Apply resolved gaps to assets (always on)
            try:
                from .transformers import apply_resolved_gaps_to_assets

                await apply_resolved_gaps_to_assets(db, collection_flow["id"], context)
            except Exception as e:
                logger.error(f"❌ Write-back of resolved gaps failed: {e}")

            return {
                "success": True,
                "responses_processed": len(responses),
                "gaps_resolved": len(
                    [r for r in responses.values() if r.get("is_valid", False)]
                ),
            }

        except Exception as e:
            logger.error(f"❌ Response processing failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}


# Create singleton instance for backward compatibility
data_processors = DataProcessors()


# Export functions for backward compatibility
async def collection_data_normalization(*args, **kwargs):
    return await data_processors.collection_data_normalization(*args, **kwargs)


async def synthesis_preparation(*args, **kwargs):
    return await data_processors.synthesis_preparation(*args, **kwargs)


async def response_processing(*args, **kwargs):
    return await data_processors.response_processing(*args, **kwargs)
