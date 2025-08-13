"""
Asset Creation Tool for CrewAI Agents

Provides tools for persistent agents to create assets in the database
"""

import asyncio
import json
import logging
import os
import warnings
from typing import Any, Dict, List, Optional

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


def create_asset_creation_tools(
    context_info: Dict[str, Any], registry: Optional[Any] = None
) -> List:
    """
    Create tools for agents to create assets in the database

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id
        registry: Optional ServiceRegistry for new service pattern

    Returns:
        List of asset creation tools
    """
    logger.info("🔧 Creating asset creation tools for persistent agents")

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        # Check feature flag for service registry pattern
        use_service_registry = (
            os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
        )

        tools = []

        if use_service_registry and registry is not None:
            # Use new ServiceRegistry pattern
            logger.info("✅ Using ServiceRegistry pattern for asset creation tools")
            asset_creator = AssetCreationToolWithService(registry)
            tools.append(asset_creator)

            bulk_creator = BulkAssetCreationToolWithService(registry)
            tools.append(bulk_creator)
        else:
            # Use legacy pattern with deprecation warning
            if not use_service_registry:
                warnings.warn(
                    "Legacy asset creation tools are deprecated and will be removed on 2025-02-01. "
                    "Set USE_SERVICE_REGISTRY=true to use the new ServiceRegistry pattern.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            logger.info("⚠️ Using legacy asset creation tools (deprecated)")
            # Import legacy tools only when needed
            from .asset_creation_tool_legacy import (
                AssetCreationTool as LegacyAssetCreationTool,
                BulkAssetCreationTool as LegacyBulkAssetCreationTool,
            )

            asset_creator = LegacyAssetCreationTool(context_info)
            tools.append(asset_creator)

            bulk_creator = LegacyBulkAssetCreationTool(context_info)
            tools.append(bulk_creator)

        logger.info(f"✅ Created {len(tools)} asset creation tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create asset creation tools: {e}")
        return []


# ServiceRegistry-based tool implementations (no direct database access)
class AssetCreationToolWithServiceImpl:
    """ServiceRegistry-based implementation for asset creation tool"""

    def __init__(self, registry):
        """
        Initialize with ServiceRegistry

        Args:
            registry: ServiceRegistry instance for dependency injection
        """
        self._registry = registry
        # Never import AsyncSessionLocal or models when using service pattern

    def get_tool_config(self) -> Dict[str, Any]:
        """Get tool configuration"""
        return {
            "name": "asset_creator",
            "description": """
        Create an asset in the database from discovery data using ServiceRegistry pattern.
        Use this tool to persist discovered assets to the inventory.

        Input: Single asset data dictionary with fields like:
        - name: Asset name (required)
        - asset_type: Type of asset (server/application/device)
        - hostname: Hostname for servers
        - ip_address: IP address
        - environment: Environment (production/development/etc)
        - other fields as discovered

        Output: JSON response with success status and asset information
        """,
        }

    async def execute_async(self, asset_data: Dict[str, Any]) -> str:
        """Execute asset creation asynchronously using ServiceRegistry"""
        return await self._create_single_asset(asset_data)

    def execute_sync(self, asset_data: Dict[str, Any]) -> str:
        """Execute asset creation synchronously using ServiceRegistry"""
        return asyncio.run(self._create_single_asset(asset_data))

    async def _create_single_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create a single asset using AssetService from registry"""
        try:
            logger.info(
                f"🔨 Agent creating asset via ServiceRegistry: {asset_data.get('name', 'unnamed')}"
            )

            # Get AssetService from registry - no imports needed
            from app.services.asset_service import AssetService

            asset_service = self._registry.get_service(AssetService)

            # Get audit logger from registry
            audit_logger = self._registry.get_audit_logger()

            # Log tool execution start
            if audit_logger:
                await audit_logger.log_tool_execution(
                    tool_name="asset_creator",
                    operation="create_asset",
                    parameters={"asset_name": asset_data.get("name", "unnamed")},
                )

            # Create asset via service
            created_asset = await asset_service.create_asset(asset_data)

            if not created_asset:
                error_msg = "Asset service returned None - creation failed"
                logger.error(f"❌ {error_msg}")

                # Log failure
                if audit_logger:
                    await audit_logger.log_tool_execution(
                        tool_name="asset_creator",
                        operation="create_asset",
                        parameters={"asset_name": asset_data.get("name", "unnamed")},
                        error=error_msg,
                    )

                return json.dumps(
                    {
                        "success": False,
                        "error": error_msg,
                        "message": "Failed to create asset via service",
                    }
                )

            logger.info(
                f"✅ Asset created via ServiceRegistry: {created_asset.name} (ID: {created_asset.id})"
            )

            # Log success
            if audit_logger:
                await audit_logger.log_tool_execution(
                    tool_name="asset_creator",
                    operation="create_asset",
                    parameters={"asset_name": asset_data.get("name", "unnamed")},
                    result={
                        "asset_id": str(created_asset.id),
                        "asset_name": created_asset.name,
                    },
                )

            return json.dumps(
                {
                    "success": True,
                    "asset_id": str(created_asset.id),
                    "asset_name": created_asset.name,
                    "message": f"Asset '{created_asset.name}' created successfully via ServiceRegistry",
                }
            )

        except Exception as e:
            logger.error(f"❌ Failed to create asset via ServiceRegistry: {e}")

            # Log error
            audit_logger = self._registry.get_audit_logger()
            if audit_logger:
                await audit_logger.log_tool_execution(
                    tool_name="asset_creator",
                    operation="create_asset",
                    parameters={"asset_name": asset_data.get("name", "unnamed")},
                    error=str(e),
                )

            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to create asset via ServiceRegistry",
                }
            )


class BulkAssetCreationToolWithServiceImpl:
    """ServiceRegistry-based implementation for bulk asset creation tool"""

    def __init__(self, registry):
        """
        Initialize with ServiceRegistry

        Args:
            registry: ServiceRegistry instance for dependency injection
        """
        self._registry = registry
        # Never import AsyncSessionLocal or models when using service pattern

    def get_tool_config(self) -> Dict[str, Any]:
        """Get tool configuration"""
        return {
            "name": "bulk_asset_creator",
            "description": """
        Create multiple assets in the database in a single operation using ServiceRegistry pattern.
        Use this tool when you have multiple assets to create from discovery.

        Input: List of asset data dictionaries
        Output: JSON response with summary of created assets
        """,
        }

    async def execute_async(self, assets_data: List[Dict[str, Any]]) -> str:
        """Execute bulk asset creation asynchronously using ServiceRegistry"""
        try:
            logger.info(
                f"🔨 Agent creating {len(assets_data)} assets in bulk via ServiceRegistry"
            )

            # Get AssetService from registry
            from app.services.asset_service import AssetService

            asset_service = self._registry.get_service(AssetService)

            # Get audit logger from registry
            audit_logger = self._registry.get_audit_logger()

            # Log bulk operation start
            if audit_logger:
                await audit_logger.log_tool_execution(
                    tool_name="bulk_asset_creator",
                    operation="bulk_create_assets",
                    parameters={"asset_count": len(assets_data)},
                )

            created_assets = []
            failed_assets = []

            # Use service for bulk creation
            try:
                service_created = await asset_service.bulk_create_assets(assets_data)

                for asset in service_created:
                    created_assets.append(
                        {
                            "asset_id": str(asset.id),
                            "asset_name": asset.name,
                        }
                    )

            except Exception as service_error:
                # If bulk service fails, try individual creation
                logger.warning(
                    f"Bulk service failed, falling back to individual creation: {service_error}"
                )

                for asset_data in assets_data:
                    try:
                        asset = await asset_service.create_asset(asset_data)
                        if asset:
                            created_assets.append(
                                {
                                    "asset_id": str(asset.id),
                                    "asset_name": asset.name,
                                }
                            )
                        else:
                            failed_assets.append(
                                {
                                    "asset_name": asset_data.get("name", "unknown"),
                                    "error": "Service returned None",
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
                f"✅ Bulk creation via ServiceRegistry complete: "
                f"{len(created_assets)} created, {len(failed_assets)} failed"
            )

            # Log operation result
            if audit_logger:
                await audit_logger.log_tool_execution(
                    tool_name="bulk_asset_creator",
                    operation="bulk_create_assets",
                    parameters={"asset_count": len(assets_data)},
                    result={
                        "assets_created": len(created_assets),
                        "assets_failed": len(failed_assets),
                    },
                )

            return json.dumps(
                {
                    "success": True,
                    "total_requested": len(assets_data),
                    "assets_created": len(created_assets),
                    "assets_failed": len(failed_assets),
                    "created": created_assets,
                    "failed": failed_assets,
                    "message": f"Created {len(created_assets)} of {len(assets_data)} assets via ServiceRegistry",
                }
            )

        except Exception as e:
            logger.error(f"❌ Bulk asset creation via ServiceRegistry failed: {e}")

            # Log error
            audit_logger = self._registry.get_audit_logger()
            if audit_logger:
                await audit_logger.log_tool_execution(
                    tool_name="bulk_asset_creator",
                    operation="bulk_create_assets",
                    parameters={"asset_count": len(assets_data) if assets_data else 0},
                    error=str(e),
                )

            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Bulk asset creation via ServiceRegistry failed",
                }
            )

    def execute_sync(self, assets_data: List[Dict[str, Any]]) -> str:
        """Execute bulk asset creation synchronously using ServiceRegistry"""
        return asyncio.run(self.execute_async(assets_data))


# CrewAI-specific tool wrappers for ServiceRegistry pattern
if CREWAI_TOOLS_AVAILABLE:  # noqa: C901

    class AssetCreationToolWithService(BaseTool):
        """CrewAI Tool wrapper for ServiceRegistry-based asset creation"""

        name: str = "asset_creator"
        description: str = AssetCreationToolWithServiceImpl(None).get_tool_config()[
            "description"
        ]

        def __init__(self, registry):
            super().__init__()
            self._impl = AssetCreationToolWithServiceImpl(registry)

        async def _arun(self, asset_data: Dict[str, Any]) -> str:
            return await self._impl.execute_async(asset_data)

        def _run(self, asset_data: Dict[str, Any]) -> str:
            return self._impl.execute_sync(asset_data)

    class BulkAssetCreationToolWithService(BaseTool):
        """CrewAI Tool wrapper for ServiceRegistry-based bulk asset creation"""

        name: str = "bulk_asset_creator"
        description: str = BulkAssetCreationToolWithServiceImpl(None).get_tool_config()[
            "description"
        ]

        def __init__(self, registry):
            super().__init__()
            self._impl = BulkAssetCreationToolWithServiceImpl(registry)

        async def _arun(self, assets_data: List[Dict[str, Any]]) -> str:
            return await self._impl.execute_async(assets_data)

        def _run(self, assets_data: List[Dict[str, Any]]) -> str:
            return self._impl.execute_sync(assets_data)

else:
    # Dummy classes if CrewAI is not available - use implementation classes directly
    class AssetCreationToolWithService:
        """Dummy ServiceRegistry-based tool when CrewAI not available"""

        def __init__(self, registry):
            self._impl = AssetCreationToolWithServiceImpl(registry)

        async def _arun(self, asset_data: Dict[str, Any]) -> str:
            return await self._impl.execute_async(asset_data)

        def _run(self, asset_data: Dict[str, Any]) -> str:
            return self._impl.execute_sync(asset_data)

    class BulkAssetCreationToolWithService:
        """Dummy ServiceRegistry-based bulk tool when CrewAI not available"""

        def __init__(self, registry):
            self._impl = BulkAssetCreationToolWithServiceImpl(registry)

        async def _arun(self, assets_data: List[Dict[str, Any]]) -> str:
            return await self._impl.execute_async(assets_data)

        def _run(self, assets_data: List[Dict[str, Any]]) -> str:
            return self._impl.execute_sync(assets_data)
