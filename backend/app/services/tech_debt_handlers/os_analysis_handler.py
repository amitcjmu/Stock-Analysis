"""
OS Analysis Handler for Tech Debt
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class OSAnalysisHandler:
    def __init__(self, config=None):
        self.config = config

    async def analyze(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes operating system versions and lifecycle status."""
        os_analysis = {
            "os_inventory": {},
            "lifecycle_status": {},
            "risk_assessment": {},
        }

        for asset in assets:
            os_info = self._extract_os_information(asset)
            if os_info:
                os_name = os_info.get("os_name", "unknown")
                os_version = os_info.get("os_version", "unknown")
                os_key = f"{os_name}_{os_version}"

                if os_key not in os_analysis["os_inventory"]:
                    os_analysis["os_inventory"][os_key] = {
                        "os_name": os_name,
                        "os_version": os_version,
                        "asset_count": 0,
                    }
                os_analysis["os_inventory"][os_key]["asset_count"] += 1

        return os_analysis

    def _extract_os_information(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts OS information from asset data."""
        # This would contain the logic from the original service's method.
        return {"os_name": asset.get("os"), "os_version": asset.get("os_version")} 