"""
Collection Flow Handler Extensions

Additional handlers for collection flow that are defined outside the main
collection_handlers module. This includes handlers from other services that
need to be registered for collection flow phases.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def register_collection_extension_handlers(handler_registry) -> Dict[str, Any]:
    """
    Register extension handlers for collection flow phases.

    This function registers handlers that are defined outside the main
    collection_handlers module but are needed for collection flow phases.

    Args:
        handler_registry: The handler registry instance to register handlers with

    Returns:
        Dict containing registration results
    """
    results = {"registered": [], "errors": []}

    # REMOVED: Collection service - collection functionality was removed
    # try:
    #     # Import asset selection bootstrap handler
    #     from app.services.collection.asset_selection_bootstrap import (
    #         handle_asset_selection_preparation,
    #     )
    #
    #     # Register the asset selection preparation handler
    #     handler_registry.register_handler(
    #         "asset_selection_preparation",
    #         handle_asset_selection_preparation,
    #         description="Bootstrap handler for asset selection phase",
    #     )
    #     results["registered"].append("asset_selection_preparation")
    #     logger.info("✅ Registered asset_selection_preparation handler")
    #
    # except Exception as e:
    #     logger.error(f"Failed to register asset_selection_preparation: {e}")
    #     results["errors"].append(f"asset_selection_preparation: {str(e)}")

    # Collection service removed - skip registration
    logger.warning(
        "⚠️ Collection service removed - asset_selection_preparation handler not registered"
    )

    return results
