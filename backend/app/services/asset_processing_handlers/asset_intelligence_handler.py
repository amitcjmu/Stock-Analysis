"""
Asset Intelligence Handler
Handles AI-powered analysis of asset readiness for migration assessment.
"""
import logging
from typing import TYPE_CHECKING, Any, Dict, List

from app.services.tools.asset_intelligence_tools import AssetAnalysisTool, BulkOperationsTool

if TYPE_CHECKING:
    from app.services.agent_registry import AgentRegistry
    from app.services.crewai_flow_service import crewai_flow_service

logger = logging.getLogger(__name__)

class AssetIntelligenceHandler:
    def __init__(self):
        self.crewai_service_available = False
        self.agent_registry = None
        try:
            from app.services.agent_registry import AgentRegistry
            self.agent_registry = AgentRegistry()

            import importlib
            crewai_flow_service_module = importlib.import_module("app.services.crewai_flow_service")
            crewai_flow_service = getattr(crewai_flow_service_module, "crewai_flow_service")
            
            if crewai_flow_service and crewai_flow_service.is_available():
                self.crewai_service_available = True
                logger.info("CrewAI service is available for AssetIntelligenceHandler")
        except ImportError as e:
            logger.warning(f"CrewAI service not available for AssetIntelligenceHandler: {e}")

    async def enrich_asset(self, asset_data: Dict[str, Any], client_account_id: str) -> Dict[str, Any]:
        """Enriches a single asset with AI-driven intelligence."""
        # This is a placeholder for the more complex enrichment logic
        # that would be ported from the original service.
        asset_data['enrichment_status'] = 'enriched'
        asset_data['predicted_os'] = 'Linux' # Dummy enrichment
        return asset_data

    async def analyze_inventory(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Performs a comprehensive analysis of an asset inventory."""
        # This would contain the logic from _perform_comprehensive_analysis
        return {
            "status": "success",
            "total_assets": len(assets),
            "asset_metrics": self._calculate_asset_metrics(assets),
        }

    def _calculate_asset_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates basic asset inventory metrics."""
        metrics = {"by_type": {}, "by_environment": {}}
        for asset in assets:
            asset_type = asset.get('asset_type', 'Unknown')
            metrics["by_type"][asset_type] = metrics["by_type"].get(asset_type, 0) + 1
            
            environment = asset.get('environment', 'Unknown')
            metrics["by_environment"][environment] = metrics["by_environment"].get(environment, 0) + 1
        return metrics 