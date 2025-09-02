"""
Collected Data Inventory Service

Populates the collected_data_inventory table with data collected during
automated and manual collection phases.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RequestContext
from app.models.collected_data_inventory import CollectedDataInventory
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


class CollectedDataInventoryService:
    """Service for managing collected data in the collected_data_inventory table"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def populate_collected_data(
        self,
        collection_flow_id: str,
        collected_data: List[Dict[str, Any]],
        collection_method: str,
        context: RequestContext,
        adapter_id: Optional[str] = None,
    ) -> List[CollectedDataInventory]:
        """
        Populate the collected_data_inventory table with collected data.

        Args:
            collection_flow_id: The collection flow UUID
            collected_data: List of collected data items
            collection_method: Method used (automated, manual, hybrid)
            context: Request context for tenant scoping
            adapter_id: Optional adapter ID for automated collection

        Returns:
            List of created CollectedDataInventory records
        """
        try:
            # Convert string flow ID to UUID if needed
            if isinstance(collection_flow_id, str):
                collection_flow_uuid = UUID(collection_flow_id)
            else:
                collection_flow_uuid = collection_flow_id

            logger.info(
                f"Populating collected data inventory for collection flow {collection_flow_uuid} "
                f"with {len(collected_data)} items using {collection_method} method"
            )

            created_records = []

            for data_item in collected_data:
                # Extract platform and data type information
                platform = data_item.get("platform", "unknown")
                data_type = data_item.get("data_type", data_item.get("type", "unknown"))

                # Handle different data structures
                raw_data = data_item.get("raw_data", data_item)
                normalized_data = data_item.get("normalized_data")

                # Calculate resource count
                resource_count = 0
                if isinstance(raw_data, list):
                    resource_count = len(raw_data)
                elif isinstance(raw_data, dict):
                    # Try to extract count from common patterns
                    resource_count = (
                        raw_data.get("count", 0)
                        or raw_data.get("total", 0)
                        or len(raw_data.get("items", []))
                    )
                    if resource_count == 0 and raw_data:
                        resource_count = 1

                # Extract quality metrics
                quality_score = data_item.get("quality_score")
                validation_status = data_item.get("validation_status", "pending")
                validation_errors = data_item.get("validation_errors")

                # Build metadata
                metadata = {
                    "collection_timestamp": datetime.utcnow().isoformat(),
                    "collection_method": collection_method,
                    "source_adapter": adapter_id,
                    "data_size": len(str(raw_data)) if raw_data else 0,
                }

                # Add any additional metadata from the data item
                if "metadata" in data_item:
                    metadata.update(data_item["metadata"])

                # Create inventory record
                inventory_record = CollectedDataInventory(
                    collection_flow_id=collection_flow_uuid,
                    adapter_id=UUID(adapter_id) if adapter_id else None,
                    platform=platform,
                    collection_method=collection_method,
                    raw_data=raw_data,
                    normalized_data=normalized_data,
                    data_type=data_type,
                    resource_count=resource_count,
                    quality_score=quality_score,
                    validation_status=validation_status,
                    validation_errors=validation_errors,
                    inventory_metadata=metadata,
                    collected_at=datetime.utcnow(),
                )

                self.db.add(inventory_record)
                created_records.append(inventory_record)

            # Use atomic transaction pattern
            await self.db.flush()

            logger.info(
                f"Created {len(created_records)} collected data inventory records "
                f"for collection flow {collection_flow_uuid}"
            )

            return created_records

        except Exception as e:
            logger.error(f"Failed to populate collected data inventory: {str(e)}")
            # Re-raise to let caller handle transaction rollback
            raise

    async def get_collected_data_summary(
        self, collection_flow_id: str, context: RequestContext
    ) -> Dict[str, Any]:
        """
        Get summary of collected data for a collection flow.

        Args:
            collection_flow_id: The collection flow UUID
            context: Request context for tenant scoping

        Returns:
            Summary statistics of collected data
        """
        try:
            # Convert string flow ID to UUID if needed
            if isinstance(collection_flow_id, str):
                collection_flow_uuid = UUID(collection_flow_id)
            else:
                collection_flow_uuid = collection_flow_id

            # Get all inventory records for this flow
            result = await self.db.execute(
                select(CollectedDataInventory).where(
                    CollectedDataInventory.collection_flow_id == collection_flow_uuid
                )
            )

            inventory_records = result.scalars().all()

            if not inventory_records:
                return {
                    "total_records": 0,
                    "total_resources": 0,
                    "platforms": [],
                    "data_types": [],
                    "collection_methods": [],
                    "quality_score_avg": 0.0,
                    "validation_status_summary": {},
                }

            # Calculate summary statistics
            total_records = len(inventory_records)
            total_resources = sum(record.resource_count for record in inventory_records)

            platforms = list(set(record.platform for record in inventory_records))
            data_types = list(set(record.data_type for record in inventory_records))
            collection_methods = list(
                set(record.collection_method for record in inventory_records)
            )

            # Calculate average quality score
            quality_scores = [
                record.quality_score
                for record in inventory_records
                if record.quality_score is not None
            ]
            quality_score_avg = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            )

            # Validation status summary
            validation_status_counts = {}
            for record in inventory_records:
                status = record.validation_status
                validation_status_counts[status] = (
                    validation_status_counts.get(status, 0) + 1
                )

            return {
                "total_records": total_records,
                "total_resources": total_resources,
                "platforms": platforms,
                "data_types": data_types,
                "collection_methods": collection_methods,
                "quality_score_avg": round(quality_score_avg, 2),
                "validation_status_summary": validation_status_counts,
            }

        except Exception as e:
            logger.error(f"Failed to get collected data summary: {str(e)}")
            return {}

    async def update_validation_status(
        self,
        inventory_record_id: str,
        validation_status: str,
        validation_errors: Optional[Dict[str, Any]] = None,
        quality_score: Optional[float] = None,
    ) -> Optional[CollectedDataInventory]:
        """
        Update validation status and quality score for an inventory record.

        Args:
            inventory_record_id: The inventory record UUID
            validation_status: New validation status (pending, valid, invalid)
            validation_errors: Optional validation error details
            quality_score: Optional updated quality score

        Returns:
            Updated CollectedDataInventory record or None
        """
        try:
            # Convert string ID to UUID if needed
            if isinstance(inventory_record_id, str):
                record_uuid = UUID(inventory_record_id)
            else:
                record_uuid = inventory_record_id

            # Get existing record
            result = await self.db.execute(
                select(CollectedDataInventory).where(
                    CollectedDataInventory.id == record_uuid
                )
            )
            record = result.scalar_one_or_none()

            if not record:
                logger.warning(
                    f"Collected data inventory record {inventory_record_id} not found"
                )
                return None

            # Update fields
            record.validation_status = validation_status
            if validation_errors is not None:
                record.validation_errors = validation_errors
            if quality_score is not None:
                record.quality_score = quality_score
            record.processed_at = datetime.utcnow()

            # Use atomic transaction pattern
            await self.db.flush()

            logger.info(
                f"Updated validation status for inventory record {inventory_record_id} to {validation_status}"
            )

            return record

        except Exception as e:
            logger.error(f"Failed to update validation status: {str(e)}")
            return None
