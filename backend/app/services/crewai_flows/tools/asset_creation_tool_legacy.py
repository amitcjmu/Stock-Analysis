"""
Legacy Asset Creation Tool for CrewAI Agents

This file contains the deprecated legacy implementation that uses AsyncSessionLocal directly.
This code will be removed on 2025-02-01.

DO NOT USE THIS IN NEW CODE - Use AssetCreationToolWithService from asset_creation_tool.py instead.
"""

import asyncio
import json
import logging
from typing import Any, Dict

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


class AssetCreationTool(BaseTool if CREWAI_TOOLS_AVAILABLE else object):
    """Legacy asset creation tool that uses AsyncSessionLocal directly"""

    name: str = "create_asset_in_database"
    description: str = (
        "Create an asset in the database with the provided information. "
        "This tool allows persistent agents to create server, application, database, or network assets. "
        "Returns the created asset with its ID."
    )

    def __init__(self, context_info: Dict[str, Any]):
        """Initialize with context information"""
        self._context_info = context_info
        super().__init__()

    def _run(self, asset_data: str, **kwargs) -> str:
        """Synchronous wrapper for async _execute"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running (e.g., in Jupyter), create task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._execute(asset_data))
                    result = future.result()
            else:
                # Normal execution
                result = loop.run_until_complete(self._execute(asset_data))
            return result
        except Exception as e:
            logger.error(f"Failed to execute asset creation: {e}")
            return json.dumps({"error": str(e)})

    async def _execute(self, asset_data: str) -> str:
        """Execute asset creation using legacy AsyncSessionLocal pattern"""
        try:
            data = json.loads(asset_data) if isinstance(asset_data, str) else asset_data

            # Import dependencies (legacy pattern - to be removed)
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext
            from app.repositories.asset_repository import AssetRepository

            # Create database session (legacy pattern)
            async with AsyncSessionLocal() as db:
                context = RequestContext(
                    client_account_id=self._context_info.get("client_account_id"),
                    engagement_id=self._context_info.get("engagement_id"),
                    user_id=self._context_info.get("user_id"),
                    flow_id=self._context_info.get("flow_id"),
                    request_id=self._context_info.get("request_id"),
                )

                # Create repository with context
                repository = AssetRepository(db, context)

                # Create asset using repository
                asset = await repository.create(**data)

                # Commit the transaction (legacy behavior)
                await db.commit()

                return json.dumps(
                    {
                        "success": True,
                        "asset_id": str(asset.id),
                        "message": f"Created {asset.asset_type} asset: {asset.asset_name}",
                        "asset": {
                            "id": str(asset.id),
                            "asset_name": asset.asset_name,
                            "asset_type": asset.asset_type,
                            "hostname": asset.hostname,
                            "ip_address": asset.ip_address,
                            "environment": asset.environment,
                            "criticality": asset.criticality,
                            "business_owner": asset.business_owner,
                        },
                    }
                )

        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            return json.dumps({"success": False, "error": str(e)})


class BulkAssetCreationTool(BaseTool if CREWAI_TOOLS_AVAILABLE else object):
    """Legacy bulk asset creation tool that uses AsyncSessionLocal directly"""

    name: str = "create_multiple_assets_in_database"
    description: str = (
        "Create multiple assets in the database in a single transaction. "
        "Accepts a list of asset data dictionaries. "
        "Returns the created assets with their IDs."
    )

    def __init__(self, context_info: Dict[str, Any]):
        """Initialize with context information"""
        self._context_info = context_info
        super().__init__()

    def _run(self, assets_data: str, **kwargs) -> str:
        """Synchronous wrapper for async _execute"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._execute(assets_data))
                    result = future.result()
            else:
                result = loop.run_until_complete(self._execute(assets_data))
            return result
        except Exception as e:
            logger.error(f"Failed to execute bulk asset creation: {e}")
            return json.dumps({"error": str(e)})

    async def _execute(self, assets_data: str) -> str:
        """Execute bulk asset creation using legacy AsyncSessionLocal pattern"""
        try:
            data = (
                json.loads(assets_data) if isinstance(assets_data, str) else assets_data
            )

            if not isinstance(data, list):
                data = [data]

            # Import dependencies (legacy pattern - to be removed)
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext
            from app.repositories.asset_repository import AssetRepository

            # Create database session (legacy pattern)
            async with AsyncSessionLocal() as db:
                context = RequestContext(
                    client_account_id=self._context_info.get("client_account_id"),
                    engagement_id=self._context_info.get("engagement_id"),
                    user_id=self._context_info.get("user_id"),
                    flow_id=self._context_info.get("flow_id"),
                    request_id=self._context_info.get("request_id"),
                )

                # Create repository with context
                repository = AssetRepository(db, context)

                created_assets = []
                for asset_data in data:
                    asset = await repository.create(**asset_data)
                    created_assets.append(
                        {
                            "id": str(asset.id),
                            "asset_name": asset.asset_name,
                            "asset_type": asset.asset_type,
                            "hostname": asset.hostname,
                            "ip_address": asset.ip_address,
                            "environment": asset.environment,
                        }
                    )

                # Commit all in one transaction (legacy behavior)
                await db.commit()

                return json.dumps(
                    {
                        "success": True,
                        "created_count": len(created_assets),
                        "message": f"Created {len(created_assets)} assets successfully",
                        "assets": created_assets,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to create assets in bulk: {e}")
            return json.dumps({"success": False, "error": str(e)})
