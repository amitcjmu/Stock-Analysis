"""
Assessment Input Builders - Risk Builder

Mixin for building risk assessment inputs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class RiskBuilderMixin:
    """Mixin for risk assessment input building"""

    async def build_risk_input(
        self, flow_id: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build input for risk assessment phase.

        Aggregates results from readiness, complexity, dependency, and tech debt
        phases along with business impact data for comprehensive risk evaluation.

        Args:
            flow_id: Assessment flow UUID
            user_input: Optional user-provided risk factors

        Returns:
            Structured input dictionary containing:
                - Results from readiness phase
                - Results from complexity phase
                - Results from dependency phase
                - Results from tech debt phase
                - Business impact data
                - User-provided risk factors
        """
        try:
            # Fetch risk data (includes all prior phase results)
            context_data = await self.data_repo.get_risk_data(flow_id)

            # Extract user-provided risk factors
            risk_factors = (user_input or {}).get("risk_factors", {})

            # Build structured input
            return {
                "flow_id": flow_id,
                "client_account_id": str(self.data_repo.client_account_id),
                "engagement_id": str(self.data_repo.engagement_id),
                "phase_name": "risk_assessment",
                "user_input": user_input or {},
                "context_data": {
                    "applications": context_data.get("applications", []),
                    "business_impact_data": context_data.get(
                        "business_impact_data", {}
                    ),
                },
                "risk_factors": {
                    "risk_tolerance": risk_factors.get("risk_tolerance", "medium"),
                    "downtime_tolerance": risk_factors.get("downtime_tolerance", "low"),
                    "data_loss_tolerance": risk_factors.get(
                        "data_loss_tolerance", "zero"
                    ),
                    "compliance_risks": risk_factors.get("compliance_risks", []),
                },
                "previous_phase_results": {
                    "readiness_assessment": context_data.get("readiness_results", {}),
                    "complexity_analysis": context_data.get("complexity_results", {}),
                    "dependency_analysis": context_data.get("dependency_results", {}),
                    "tech_debt_assessment": {},  # Will be added by execution engine
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase_version": "1.0.0",
                    "builder": "risk_assessment",
                },
            }

        except Exception as e:
            logger.error(f"Error building risk input: {e}")
            return self._build_fallback_input(flow_id, "risk_assessment", user_input)
