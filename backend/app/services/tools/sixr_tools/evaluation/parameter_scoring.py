"""
Parameter Scoring Tool for 6R Migration Strategy Analysis.
Scores 6R parameters against specific migration strategies.
"""

from typing import Dict

from ..core.base import BaseTool, BaseModel, Field, logger, json, get_sixr_imports


class ParameterScoringInput(BaseModel):
    """Input schema for parameter scoring tool."""

    parameters: Dict[str, float] = Field(..., description="6R parameters to score")
    strategy: str = Field(..., description="6R strategy to score against")


class ParameterScoringTool(BaseTool):
    """Tool for scoring parameters against specific 6R strategies."""

    name: str = "parameter_scoring_tool"
    description: str = "Score 6R parameters against a specific migration strategy"
    args_schema: type[BaseModel] = ParameterScoringInput

    def __init__(self, crewai_service=None):
        """
        Initialize parameter scoring tool.

        Args:
            crewai_service: Optional CrewAI service for AI-powered analysis.
                           If None, engine uses fallback heuristic mode.
                           Reference: Bug #666 - Phase 1 fix
        """
        super().__init__()
        # Lazy import to avoid circular dependencies
        _, _, _, SixRDecisionEngine = get_sixr_imports()
        if SixRDecisionEngine:
            # Bug #666 - Phase 1: Pass crewai_service to enable AI-powered analysis
            self.decision_engine = SixRDecisionEngine(crewai_service=crewai_service)
        else:
            self.decision_engine = None

    def _run(self, parameters: Dict[str, float], strategy: str) -> str:
        """Score parameters against a specific strategy."""
        try:
            # Get required classes using lazy imports
            SixRParameterBase, SixRStrategy, _, _ = get_sixr_imports()

            if not SixRParameterBase or not SixRStrategy or not self.decision_engine:
                return json.dumps(
                    {"error": "SixR dependencies not available", "status": "failed"}
                )

            # Convert parameters to SixRParameterBase
            param_obj = SixRParameterBase(**parameters)

            # Get strategy enum
            strategy_enum = SixRStrategy(strategy.lower())

            # Calculate score for the specific strategy
            score_data = self.decision_engine._calculate_strategy_score(
                strategy_enum, param_obj, None
            )

            return json.dumps(score_data, indent=2)

        except Exception as e:
            logger.error(f"Parameter scoring failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})
