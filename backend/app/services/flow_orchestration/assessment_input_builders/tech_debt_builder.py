"""
Assessment Input Builders - Tech Debt Builder

Mixin for building tech debt assessment inputs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class TechDebtBuilderMixin:
    """Mixin for tech debt assessment input building"""

    async def build_tech_debt_input(
        self, flow_id: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build input for tech debt assessment phase.

        Includes code quality metrics, outdated technology indicators,
        security vulnerabilities, and maintenance history.

        Args:
            flow_id: Assessment flow UUID
            user_input: Optional user-provided tech debt concerns

        Returns:
            Structured input dictionary containing:
                - Code quality metrics (if available)
                - Outdated technology indicators
                - Security vulnerabilities
                - Maintenance history
                - User-provided tech debt concerns
        """
        try:
            # Fetch complexity data (tech debt builds on complexity)
            context_data = await self.data_repo.get_complexity_data(flow_id)

            # Extract user-provided tech debt concerns
            tech_debt_concerns = (user_input or {}).get("tech_debt_concerns", {})

            # Build structured input
            return {
                "flow_id": flow_id,
                "client_account_id": str(self.data_repo.client_account_id),
                "engagement_id": str(self.data_repo.engagement_id),
                "phase_name": "tech_debt_assessment",
                "user_input": user_input or {},
                "context_data": {
                    "applications": context_data.get("applications", []),
                    "complexity_indicators": context_data.get(
                        "complexity_indicators", {}
                    ),
                    "inventory_by_type": context_data.get("inventory_by_type", {}),
                },
                "tech_debt_concerns": {
                    "known_vulnerabilities": tech_debt_concerns.get(
                        "known_vulnerabilities", []
                    ),
                    "outdated_technologies": tech_debt_concerns.get(
                        "outdated_technologies", []
                    ),
                    "code_quality_issues": tech_debt_concerns.get(
                        "code_quality_issues", []
                    ),
                    "maintenance_challenges": tech_debt_concerns.get(
                        "maintenance_challenges", []
                    ),
                },
                "previous_phase_results": {
                    # Results from prior phases will be added by execution engine
                    "readiness_assessment": {},
                    "complexity_analysis": {},
                    "dependency_analysis": {},
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase_version": "1.0.0",
                    "builder": "tech_debt_assessment",
                },
            }

        except Exception as e:
            logger.error(f"Error building tech debt input: {e}")
            return self._build_fallback_input(
                flow_id, "tech_debt_assessment", user_input
            )
