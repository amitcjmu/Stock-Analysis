"""
Asset Validation Handler
Handles the validation of asset data.
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class AssetValidationHandler:
    def __init__(self, config=None):
        self.config = config

    def validate_asset(self, asset_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """Validates the data for a single asset."""
        errors = {}
        if not asset_data.get("name"):
            errors["name"] = "Asset name is required."
        if not asset_data.get("asset_type"):
            errors["asset_type"] = "Asset type is required."

        is_valid = not errors
        return is_valid, errors
