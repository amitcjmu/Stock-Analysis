"""
Asset Creation Tools Executor

Extracted from execution_engine_crew_discovery.py to reduce file length.
Contains logic for executing asset creation using agent tools.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AssetCreationToolsExecutor:
    """Handles asset creation using agent tools."""

    @staticmethod
    async def execute_asset_creation_with_tools(
        agent, input_data: Dict[str, Any], task_description: str
    ) -> Dict[str, Any]:
        """Execute asset creation using the agent's asset creation tools."""
        try:
            # Check if agent has tools available
            if not hasattr(agent, "tools") or not agent.tools:
                logger.warning("Agent has no tools available for asset creation")
                return {
                    "status": "completed",
                    "message": "No asset creation tools available",
                    "assets_created": 0,
                }

            # Find asset creation tools
            asset_creation_tools = []
            bulk_creation_tools = []

            for tool in agent.tools:
                if hasattr(tool, "name"):
                    if tool.name == "asset_creator":
                        asset_creation_tools.append(tool)
                    elif tool.name == "bulk_asset_creator":
                        bulk_creation_tools.append(tool)

            if not asset_creation_tools and not bulk_creation_tools:
                logger.warning("No asset creation tools found in agent's toolset")
                return {
                    "status": "completed",
                    "message": "Asset creation tools not found in agent",
                    "assets_created": 0,
                }

            # Get raw data for asset creation
            raw_data = input_data.get("raw_data", [])
            if not raw_data:
                logger.info("No raw data available for asset creation")
                return {
                    "status": "completed",
                    "message": "No raw data to process",
                    "assets_created": 0,
                }

            logger.info(f"Processing {len(raw_data)} records for asset creation")

            # Try bulk creation first if available
            if bulk_creation_tools:
                result = await AssetCreationToolsExecutor._execute_bulk_creation(
                    bulk_creation_tools[0], raw_data
                )
                if result:
                    return result

            # Fall back to individual asset creation
            if asset_creation_tools:
                return await AssetCreationToolsExecutor._execute_individual_creation(
                    asset_creation_tools[0], raw_data
                )

            return {
                "status": "completed",
                "message": "No suitable asset creation tools available",
                "assets_created": 0,
            }

        except Exception as e:
            logger.error(f"Asset creation with tools failed: {e}")
            return {
                "status": "error",
                "message": f"Asset creation failed: {str(e)}",
                "assets_created": 0,
                "error": str(e),
            }

    @staticmethod
    async def _execute_bulk_creation(
        bulk_tool, raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute bulk asset creation."""
        try:
            # Use the bulk asset creation tool
            if hasattr(bulk_tool, "_arun"):
                # Async execution
                result_json = await bulk_tool._arun(raw_data)
            else:
                # Sync execution
                result_json = bulk_tool._run(raw_data)

            # Parse the JSON response
            result = (
                json.loads(result_json) if isinstance(result_json, str) else result_json
            )

            logger.info(
                f"Bulk asset creation completed: {result.get('assets_created', 0)} assets created"
            )
            return {
                "status": "completed",
                "message": f"Bulk created {result.get('assets_created', 0)} assets",
                "assets_created": result.get("assets_created", 0),
                "tool_results": result,
            }

        except Exception as e:
            logger.warning(
                f"Bulk asset creation failed: {e}, falling back to individual creation"
            )
            return None

    @staticmethod
    async def _execute_individual_creation(
        asset_tool, raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute individual asset creation."""
        created_count = 0

        for record in raw_data:
            try:
                # Use individual asset creation tool
                if hasattr(asset_tool, "_arun"):
                    # Async execution
                    result_json = await asset_tool._arun(record)
                else:
                    # Sync execution
                    result_json = asset_tool._run(record)

                # Parse the JSON response
                result = (
                    json.loads(result_json)
                    if isinstance(result_json, str)
                    else result_json
                )

                if result.get("success", False):
                    created_count += 1

            except Exception as e:
                logger.warning(f"Failed to create asset for record: {e}")
                continue

        logger.info(
            f"Individual asset creation completed: {created_count} assets created"
        )
        return {
            "status": "completed",
            "message": f"Created {created_count} assets individually",
            "assets_created": created_count,
        }
