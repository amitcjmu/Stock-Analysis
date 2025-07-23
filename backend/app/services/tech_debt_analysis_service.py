"""
Modular Tech Debt Analysis Service
Refactored to use a modular handler architecture.
"""

import logging
from typing import Any, Dict, List, Optional

from .tech_debt_handlers import (AppAnalysisHandler, InfraAnalysisHandler,
                                 OSAnalysisHandler, RiskAssessmentHandler,
                                 SecurityAnalysisHandler)

logger = logging.getLogger(__name__)


class TechDebtAnalysisService:
    def __init__(self, config=None):
        self.config = config
        self.os_handler = OSAnalysisHandler(config)
        self.app_handler = AppAnalysisHandler(config)
        self.infra_handler = InfraAnalysisHandler(config)
        self.security_handler = SecurityAnalysisHandler(config)
        self.risk_handler = RiskAssessmentHandler(config)

    async def analyze_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes a list of assets for technical debt."""
        # This is a simplified analysis. A real implementation would involve more complex logic.
        items = []
        summary = {
            "totalItems": len(assets),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "endOfLife": 0,
            "deprecated": 0,
        }
        for asset in assets:
            # Dummy analysis logic
            risk = "low"
            if "server" in asset.name.lower():
                risk = "medium"
            if "db" in asset.name.lower():
                risk = "high"

            items.append(
                {
                    "id": str(asset.id),
                    "assetId": str(asset.id),
                    "assetName": asset.name,
                    "component": "os",
                    "technology": "Unknown",
                    "currentVersion": "1.0",
                    "latestVersion": "2.0",
                    "supportStatus": "supported",
                    "securityRisk": risk,
                    "migrationEffort": "medium",
                    "businessImpact": "medium",
                    "recommendedAction": "Update",
                    "dependencies": [],
                }
            )
            summary[risk] += 1

        return {"items": items, "summary": summary}

    async def analyze_tech_debt(
        self,
        assets: List[Dict[str, Any]],
        stakeholder_context: Optional[Dict[str, Any]] = None,
        migration_timeline: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Performs comprehensive tech debt analysis using modular handlers."""
        os_analysis = await self.os_handler.analyze(assets)
        app_analysis = await self.app_handler.analyze(assets)
        infra_analysis = await self.infra_handler.analyze(assets)
        security_analysis = await self.security_handler.analyze(assets)

        technical_analysis = {
            "os_analysis": os_analysis,
            "app_analysis": app_analysis,
            "infra_analysis": infra_analysis,
            "security_analysis": security_analysis,
        }

        business_risk = await self.risk_handler.assess_business_risk(
            technical_analysis, stakeholder_context, migration_timeline
        )

        return {
            "tech_debt_analysis": technical_analysis,
            "business_risk_assessment": business_risk,
        }


tech_debt_analysis_service = TechDebtAnalysisService()
