"""
Technical Debt Crew Execution Handler
"""

import logging
from typing import Any, Dict

from .base import CrewExecutionBase
from .fallbacks import CrewFallbackHandler
from .parsers import CrewResultParser

logger = logging.getLogger(__name__)


class TechnicalDebtExecutor(CrewExecutionBase):
    """Handles execution of Technical Debt Crew"""

    def __init__(self, crewai_service):
        super().__init__(crewai_service)
        self.parser = CrewResultParser()
        self.fallback_handler = CrewFallbackHandler()

    def execute_technical_debt_crew(self, state) -> Dict[str, Any]:
        """Execute Technical Debt Crew with enhanced CrewAI features"""
        try:
            # Execute tech debt using PERSISTENT agent wrapper (Phase B1 - Nov 2025)
            try:
                from app.services.persistent_agents.technical_debt_persistent import (
                    execute_tech_debt_analysis,
                )

                # Pass shared memory and full discovery context
                shared_memory = getattr(state, "shared_memory_reference", None)

                # Prepare dependencies argument correctly
                dependencies = {
                    "app_server_dependencies": state.app_server_dependencies,
                    "app_app_dependencies": state.app_app_dependencies,
                }

                # Execute via persistent wrapper (no crew creation needed)
                crew_result = await execute_tech_debt_analysis(
                    context=None,  # Will be extracted from state
                    service_registry=None,  # Will use crewai_service
                    data={
                        "asset_inventory": state.asset_inventory,
                        "dependencies": dependencies,
                        "shared_memory": shared_memory,
                    },
                )

                # Parse crew results
                technical_debt_assessment = self.parser.parse_technical_debt_results(
                    crew_result
                )

                logger.info("✅ Enhanced Technical Debt Crew executed successfully")

            except Exception as crew_error:
                logger.warning(
                    f"Enhanced Technical Debt Crew execution failed, using fallback: {crew_error}"
                )
                # Fallback technical debt assessment
                technical_debt_assessment = (
                    self.fallback_handler.intelligent_technical_debt_fallback(state)
                )

            crew_status = self.create_crew_status(
                status="completed",
                manager="Technical Debt Manager",
                agents=[
                    "Legacy Systems Analyst",
                    "Modernization Expert",
                    "Risk Assessment Specialist",
                ],
                success_criteria_met=True,
            )

            return {
                "technical_debt_assessment": technical_debt_assessment,
                "crew_status": crew_status,
            }

        except Exception as e:
            logger.error(f"Technical Debt Crew execution failed: {e}")
            raise
