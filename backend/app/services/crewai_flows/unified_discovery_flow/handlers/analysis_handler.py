"""
Analysis phase handler.
Handles parallel analysis phases of the unified discovery flow.
"""

import asyncio
import logging

from .communication_utils import CommunicationUtils
from .state_utils import StateUtils

logger = logging.getLogger(__name__)


class AnalysisHandler:
    """Handles analysis phase operations."""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance."""
        self.flow = flow_instance
        self.logger = logger
        self.communication = CommunicationUtils(flow_instance)
        self.state_utils = StateUtils(flow_instance)

    async def execute_parallel_analysis(self, asset_promotion_result):
        """Execute parallel analysis phases"""
        self.logger.info(
            f"🔄 [ECHO] Starting parallel analysis for flow {self.flow._flow_id}"
        )

        try:
            # Update flow status
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import (
                    PostgresFlowStateStore,
                )

                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(
                        self.flow._flow_id, "processing_parallel_analysis"
                    )

            # Execute dependency analysis and tech debt assessment in parallel
            dependency_task = self.flow.dependency_analysis_phase.execute(
                asset_promotion_result  # Pass asset promotion result from previous phase
            )

            tech_debt_task = self.flow.tech_debt_assessment_phase.execute(
                asset_promotion_result  # Pass asset promotion result from previous phase
            )

            # Wait for both tasks to complete
            dependency_result, tech_debt_result = await asyncio.gather(
                dependency_task, tech_debt_task, return_exceptions=True
            )

            # Process results
            analysis_result = {
                "dependency_analysis": (
                    dependency_result
                    if not isinstance(dependency_result, Exception)
                    else {"error": str(dependency_result)}
                ),
                "tech_debt_assessment": (
                    tech_debt_result
                    if not isinstance(tech_debt_result, Exception)
                    else {"error": str(tech_debt_result)}
                ),
                "status": "completed",
            }

            # Send agent insight
            await self.communication.send_phase_insight(
                phase="parallel_analysis",
                title="Parallel Analysis Completed",
                description="Dependency analysis and tech debt assessment have been completed",
                progress=90,
                data=analysis_result,
            )

            # Update state with analysis results
            self.flow.state.dependency_analysis = analysis_result["dependency_analysis"]
            self.flow.state.tech_debt_assessment = analysis_result[
                "tech_debt_assessment"
            ]

            return analysis_result

        except Exception as e:
            self.logger.error(f"❌ Parallel analysis phase failed: {e}")
            await self.communication.send_phase_error("parallel_analysis", str(e))
            raise
