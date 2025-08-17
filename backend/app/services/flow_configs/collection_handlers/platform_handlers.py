"""
Collection Platform and Adapter Handlers
ADCS: Platform detection, inventory management, and adapter preparation handlers

Provides handler functions for platform detection, inventory creation, and adapter preparation operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from .base import CollectionHandlerBase, get_adapter_by_name

logger = logging.getLogger(__name__)


class PlatformHandlers(CollectionHandlerBase):
    """Handlers for platform detection and adapter management"""

    async def platform_inventory_creation(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create platform inventory after detection"""
        try:
            crew_results = phase_results.get("crew_results", {})
            detected_platforms = crew_results.get("platforms", [])

            logger.info(
                f"📋 Creating platform inventory for {len(detected_platforms)} platforms"
            )

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Store platform inventory in metadata
            update_query = """
                UPDATE collection_flows
                SET metadata = metadata || :platform_data::jsonb,
                    updated_at = :updated_at
                WHERE master_flow_id = :master_flow_id
            """

            platform_data = {
                "platform_inventory": {
                    "detected_at": datetime.utcnow().isoformat(),
                    "platforms": detected_platforms,
                    "recommended_adapters": crew_results.get(
                        "recommended_adapters", {}
                    ),
                    "platform_metadata": crew_results.get("platform_metadata", {}),
                }
            }

            await db.execute(
                update_query,
                {
                    "platform_data": platform_data,
                    "updated_at": datetime.utcnow(),
                    "master_flow_id": flow_id,
                },
            )

            await db.commit()

            return {
                "success": True,
                "platforms_detected": len(detected_platforms),
                "adapters_recommended": len(
                    crew_results.get("recommended_adapters", {})
                ),
            }

        except Exception as e:
            logger.error(f"❌ Platform inventory creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def adapter_preparation(
        self,
        db: AsyncSession,
        flow_id: str,
        phase_input: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare adapters for automated collection"""
        try:
            logger.info("🔧 Preparing adapters for collection")

            # Get available adapters from registry
            adapter_configs = phase_input.get("adapter_configs", {})

            # Validate and prepare each adapter
            prepared_adapters = {}
            for platform_id, config in adapter_configs.items():
                # Check adapter availability
                adapter_name = config.get("adapter_name")
                if adapter_name:
                    # Verify adapter exists in platform_adapters table
                    adapter = await get_adapter_by_name(db, adapter_name)
                    if adapter:
                        prepared_adapters[platform_id] = {
                            "adapter_id": str(adapter["id"]),
                            "adapter_name": adapter_name,
                            "status": "ready",
                            "config": config,
                        }
                    else:
                        logger.warning(
                            f"Adapter {adapter_name} not found for platform {platform_id}"
                        )

            return {
                "success": True,
                "prepared_adapters": prepared_adapters,
                "adapter_count": len(prepared_adapters),
            }

        except Exception as e:
            logger.error(f"❌ Adapter preparation failed: {e}")
            return {"success": False, "error": str(e)}


# Create singleton instance for backward compatibility
platform_handlers = PlatformHandlers()


# Export functions for backward compatibility
async def platform_inventory_creation(*args, **kwargs):
    return await platform_handlers.platform_inventory_creation(*args, **kwargs)


async def adapter_preparation(*args, **kwargs):
    return await platform_handlers.adapter_preparation(*args, **kwargs)
