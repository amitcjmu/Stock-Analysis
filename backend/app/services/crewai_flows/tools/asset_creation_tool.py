"""
Asset Creation Tool for CrewAI Agents

Provides tools for persistent agents to create assets in the database
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Import CrewAI tools
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


def create_asset_creation_tools(context_info: Dict[str, Any]) -> List:
    """
    Create tools for agents to create assets in the database

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id

    Returns:
        List of asset creation tools
    """
    logger.info("🔧 Creating asset creation tools for persistent agents")

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Asset creation tool
        asset_creator = AssetCreationTool(context_info)
        tools.append(asset_creator)

        # Bulk asset creation tool
        bulk_creator = BulkAssetCreationTool(context_info)
        tools.append(bulk_creator)

        logger.info(f"✅ Created {len(tools)} asset creation tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create asset creation tools: {e}")
        return []


# Define tool classes based on CrewAI availability


class AssetCreationToolImpl:
    """Implementation for asset creation tool"""

    def __init__(self, context_info: Dict[str, Any]):
        self._context_info = context_info
        # Store base class type for CrewAI
        self._base_class = BaseTool if CREWAI_TOOLS_AVAILABLE else object

    def get_tool_config(self) -> Dict[str, Any]:
        """Get tool configuration"""
        return {
            "name": "asset_creator",
            "description": """
        Create an asset in the database from discovery data.
        Use this tool to persist discovered assets to the inventory.

        Input: Single asset data dictionary with fields like:
        - name: Asset name (required)
        - asset_type: Type of asset (server/application/device)
        - hostname: Hostname for servers
        - ip_address: IP address
        - environment: Environment (production/development/etc)
        - other fields as discovered

        Output: Created asset ID or error message
        """,
        }

    async def execute_async(self, asset_data: Dict[str, Any]) -> str:
        """Execute asset creation asynchronously"""
        return await self._create_single_asset(asset_data)

    def execute_sync(self, asset_data: Dict[str, Any]) -> str:
        """Execute asset creation synchronously"""
        return asyncio.run(self._create_single_asset(asset_data))

    async def _create_single_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create a single asset in the database"""
        try:
            logger.info(f"🔨 Agent creating asset: {asset_data.get('name', 'unnamed')}")

            # Import dependencies
            from app.core.database import AsyncSessionLocal

            # Create database session
            async with AsyncSessionLocal() as db:
                context = self._build_context()
                asset_type = self._map_asset_type(asset_data)
                new_asset = self._build_asset(asset_data, context, asset_type)

                # Add to database
                db.add(new_asset)
                await db.commit()
                await db.refresh(new_asset)

                logger.info(f"✅ Asset created: {new_asset.name} (ID: {new_asset.id})")

                return json.dumps(
                    {
                        "success": True,
                        "asset_id": str(new_asset.id),
                        "asset_name": new_asset.name,
                        "message": f"Asset '{new_asset.name}' created successfully",
                    }
                )

        except Exception as e:
            logger.error(f"❌ Failed to create asset: {e}")
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to create asset",
                }
            )

    def _build_context(self):
        """Build request context from context info"""
        from app.core.context import RequestContext

        return RequestContext(
            client_account_id=self._context_info.get("client_account_id"),
            engagement_id=self._context_info.get("engagement_id"),
            user_id=self._context_info.get("user_id"),
            flow_id=self._context_info.get("flow_id"),
        )

    def _map_asset_type(self, asset_data: Dict[str, Any]):
        """Map asset type string to enum"""
        from app.models.asset import AssetType

        asset_type_str = asset_data.get("asset_type", "other").lower()
        asset_type_map = {
            "server": AssetType.SERVER,
            "application": AssetType.APPLICATION,
            "database": AssetType.DATABASE,
            "network": AssetType.NETWORK,
            "device": AssetType.NETWORK,
            "storage": AssetType.STORAGE,
            "virtual_machine": AssetType.VIRTUAL_MACHINE,
            "container": AssetType.CONTAINER,
        }
        return asset_type_map.get(asset_type_str, AssetType.OTHER)

    def _build_asset(self, asset_data: Dict[str, Any], context, asset_type):
        """Build asset object from data"""
        from app.models.asset import Asset, AssetStatus
        from datetime import datetime

        return Asset(
            # Multi-tenant context
            client_account_id=(
                uuid.UUID(context.client_account_id)
                if context.client_account_id
                else None
            ),
            engagement_id=(
                uuid.UUID(context.engagement_id) if context.engagement_id else None
            ),
            # Basic information
            name=asset_data.get("name", "Unknown Asset"),
            asset_name=asset_data.get("name", "Unknown Asset"),
            asset_type=asset_type,
            description=asset_data.get("description", "Discovered by persistent agent"),
            # Network information
            hostname=asset_data.get("hostname"),
            ip_address=asset_data.get("ip_address"),
            # Environment
            environment=asset_data.get("environment", "Unknown"),
            # Technical specifications
            operating_system=asset_data.get("operating_system"),
            cpu_cores=asset_data.get("cpu_cores"),
            memory_gb=asset_data.get("memory_gb"),
            storage_gb=asset_data.get("storage_gb"),
            # Business information
            criticality=asset_data.get("criticality", "Medium"),
            business_criticality=asset_data.get("business_criticality", "Medium"),
            # Migration status
            migration_status=AssetStatus.DISCOVERED,
            # Discovery metadata
            discovery_method="persistent_agent",
            discovery_source=f"Persistent Agent - {self._context_info.get('agent_type', 'unknown')}",
            discovery_timestamp=datetime.utcnow(),
            # Raw data
            raw_data=asset_data,
            # Audit
            imported_at=datetime.utcnow(),
        )


class BulkAssetCreationToolImpl:
    """Implementation for bulk asset creation tool"""

    def __init__(self, context_info: Dict[str, Any]):
        self._context_info = context_info

    def get_tool_config(self) -> Dict[str, Any]:
        """Get tool configuration"""
        return {
            "name": "bulk_asset_creator",
            "description": """
        Create multiple assets in the database in a single operation.
        Use this tool when you have multiple assets to create from discovery.

        Input: List of asset data dictionaries
        Output: Summary of created assets
        """,
        }

    async def execute_async(self, assets_data: List[Dict[str, Any]]) -> str:
        """Execute bulk asset creation asynchronously"""
        try:
            logger.info(f"🔨 Agent creating {len(assets_data)} assets in bulk")

            created_assets = []
            failed_assets = []

            # Create each asset using the single asset tool implementation
            asset_creator = AssetCreationToolImpl(self._context_info)
            for asset_data in assets_data:
                try:
                    result_str = await asset_creator.execute_async(asset_data)
                    result = json.loads(result_str)

                    if result.get("success"):
                        created_assets.append(
                            {
                                "asset_id": result.get("asset_id"),
                                "asset_name": result.get("asset_name"),
                            }
                        )
                    else:
                        failed_assets.append(
                            {
                                "asset_name": asset_data.get("name", "unknown"),
                                "error": result.get("error"),
                            }
                        )
                except Exception as e:
                    failed_assets.append(
                        {
                            "asset_name": asset_data.get("name", "unknown"),
                            "error": str(e),
                        }
                    )

            logger.info(
                f"✅ Bulk creation complete: {len(created_assets)} created, {len(failed_assets)} failed"
            )

            return json.dumps(
                {
                    "success": True,
                    "total_requested": len(assets_data),
                    "assets_created": len(created_assets),
                    "assets_failed": len(failed_assets),
                    "created": created_assets,
                    "failed": failed_assets,
                    "message": f"Created {len(created_assets)} of {len(assets_data)} assets",
                }
            )

        except Exception as e:
            logger.error(f"❌ Bulk asset creation failed: {e}")
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Bulk asset creation failed",
                }
            )

    def execute_sync(self, assets_data: List[Dict[str, Any]]) -> str:
        """Execute bulk asset creation synchronously"""
        return asyncio.run(self.execute_async(assets_data))


# CrewAI-specific tool wrappers
if CREWAI_TOOLS_AVAILABLE:

    class AssetCreationTool(BaseTool):
        """CrewAI Tool wrapper for asset creation"""

        name: str = "asset_creator"
        description: str = AssetCreationToolImpl({}).get_tool_config()["description"]

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._impl = AssetCreationToolImpl(context_info)

        async def _arun(self, asset_data: Dict[str, Any]) -> str:
            return await self._impl.execute_async(asset_data)

        def _run(self, asset_data: Dict[str, Any]) -> str:
            return self._impl.execute_sync(asset_data)

    class BulkAssetCreationTool(BaseTool):
        """CrewAI Tool wrapper for bulk asset creation"""

        name: str = "bulk_asset_creator"
        description: str = BulkAssetCreationToolImpl({}).get_tool_config()[
            "description"
        ]

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._impl = BulkAssetCreationToolImpl(context_info)

        async def _arun(self, assets_data: List[Dict[str, Any]]) -> str:
            return await self._impl.execute_async(assets_data)

        def _run(self, assets_data: List[Dict[str, Any]]) -> str:
            return self._impl.execute_sync(assets_data)

else:
    # Dummy classes if CrewAI is not available - use implementation classes directly
    class AssetCreationTool:
        def __init__(self, context_info: Dict[str, Any]):
            self._impl = AssetCreationToolImpl(context_info)

        async def _arun(self, asset_data: Dict[str, Any]) -> str:
            return await self._impl.execute_async(asset_data)

        def _run(self, asset_data: Dict[str, Any]) -> str:
            return self._impl.execute_sync(asset_data)

    class BulkAssetCreationTool:
        def __init__(self, context_info: Dict[str, Any]):
            self._impl = BulkAssetCreationToolImpl(context_info)

        async def _arun(self, assets_data: List[Dict[str, Any]]) -> str:
            return await self._impl.execute_async(assets_data)

        def _run(self, assets_data: List[Dict[str, Any]]) -> str:
            return self._impl.execute_sync(assets_data)
