"""
6R Engine - Modular & Robust
Enhanced with CrewAI Technical Debt Crew for AI-driven strategy analysis.
"""

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel

# Use PERSISTENT technical debt wrapper for AI-driven 6R strategy analysis (Phase B1 - Nov 2025)
try:
    from .persistent_agents.technical_debt_persistent import execute_tech_debt_analysis

    CREWAI_TECHNICAL_DEBT_AVAILABLE = True
except ImportError:
    CREWAI_TECHNICAL_DEBT_AVAILABLE = False
    execute_tech_debt_analysis = None

from .sixr_handlers import CostCalculator, RecommendationEngine, RiskAssessor

logger = logging.getLogger(__name__)


class SixRParameterBase(BaseModel):
    """Base class for 6R analysis parameters."""

    technical_complexity: Optional[float] = 3
    business_criticality: Optional[float] = 3
    cost_sensitivity: Optional[float] = 3
    timeline_urgency: Optional[float] = 3
    technical_debt: Optional[float] = 3
    compliance_requirements: Optional[float] = 3
    application_type: Optional[str] = "web_application"


class SixRDecisionEngine:
    """Modular 6R Decision Engine with CrewAI Technical Debt Crew for AI-driven strategy analysis."""

    def __init__(self, crewai_service=None):
        # Use PERSISTENT technical debt wrapper for AI-driven strategy analysis
        if CREWAI_TECHNICAL_DEBT_AVAILABLE and crewai_service:
            self.technical_debt_executor = execute_tech_debt_analysis
            self.crewai_service = crewai_service
            self.ai_strategy_available = True
            logger.info(
                "6R Decision Engine initialized with PERSISTENT Technical Debt wrapper (Phase B1)"
            )
        else:
            self.technical_debt_executor = None
            self.crewai_service = None
            self.ai_strategy_available = False
            logger.debug(
                "PERSISTENT Technical Debt wrapper not available - using fallback mode"
            )

        # Initialize remaining handlers (for cost, risk, recommendations)
        self.risk_assessor = RiskAssessor()
        self.cost_calculator = CostCalculator()
        self.recommendation_engine = RecommendationEngine()

        # Engine state
        self.custom_assumptions = []
        logger.info("6R Decision Engine initialized with AI-driven strategy analysis")

    def is_available(self) -> bool:
        """Check if the engine is properly initialized."""
        return all(
            [
                self.ai_strategy_available
                or True,  # AI strategy or fallback always available
                self.risk_assessor.is_available(),
                self.cost_calculator.is_available(),
                self.recommendation_engine.is_available(),
            ]
        )

    async def analyze_parameters(
        self,
        parameters: SixRParameterBase,
        application_type: Optional[str] = None,
        asset_inventory: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main analysis method using CrewAI Technical Debt Crew for AI-driven strategy analysis.
        """
        try:
            # Convert parameters to dict
            param_dict = (
                parameters.dict() if hasattr(parameters, "dict") else dict(parameters)
            )

            # AI-driven strategy analysis using Technical Debt Crew
            if self.ai_strategy_available and asset_inventory and dependencies:
                strategy_result = await self._analyze_with_technical_debt_crew(
                    param_dict, application_type, asset_inventory, dependencies
                )
            else:
                # Fallback to basic analysis
                strategy_result = await self._fallback_strategy_analysis(
                    param_dict, application_type
                )

            if strategy_result.get("fallback_mode"):
                return strategy_result

            # Extract top strategy and parameters
            top_strategy = strategy_result["recommended_strategy"]
            param_values = self._extract_parameter_values(param_dict)

            # Enhanced analysis using other handlers
            try:
                # Risk assessment
                risks = await self.risk_assessor.assess_risks(
                    top_strategy, param_values
                )

                # Cost and effort estimation
                cost_impact = await self.cost_calculator.estimate_cost_impact(
                    top_strategy, param_values
                )
                effort_estimate = await self.cost_calculator.estimate_effort(
                    top_strategy, param_values
                )

                # Benefits and next steps
                benefits = await self.recommendation_engine.identify_benefits(
                    top_strategy, param_values
                )
                next_steps = await self.recommendation_engine.generate_next_steps(
                    top_strategy, param_dict
                )
                assumptions = await self.recommendation_engine.generate_assumptions(
                    param_dict, top_strategy
                )

                # Enhanced result
                enhanced_result = strategy_result.copy()
                enhanced_result.update(
                    {
                        "risk_factors": risks,
                        "cost_impact": cost_impact,
                        "effort_estimate": effort_estimate,
                        "benefits": benefits,
                        "next_steps": next_steps,
                        "assumptions": assumptions + self.custom_assumptions,
                        "engine_status": self.get_engine_status(),
                    }
                )

                return enhanced_result

            except Exception as e:
                logger.warning(
                    f"Error in enhanced analysis, returning basic result: {e}"
                )
                # Return basic strategy result if enhanced analysis fails
                strategy_result["enhanced_analysis_error"] = str(e)
                return strategy_result

        except Exception as e:
            logger.error(f"Error in analyze_parameters: {e}")
            return self._get_fallback_recommendation(parameters)

    async def _analyze_with_technical_debt_crew(
        self,
        param_dict: Dict[str, Any],
        application_type: Optional[str],
        asset_inventory: Dict[str, Any],
        dependencies: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze using PERSISTENT Technical Debt wrapper for AI-driven 6R strategy analysis."""
        try:
            # Execute via persistent wrapper (Phase B1 - Nov 2025)
            crew_result = await self.technical_debt_executor(
                context=None,  # Will be extracted from crewai_service
                service_registry=None,  # Will use crewai_service
                data={
                    "asset_inventory": asset_inventory,
                    "dependencies": dependencies,
                    "shared_memory": None,
                },
            )

            # Parse results for 6R strategy recommendations
            strategy_result = self._parse_crew_results(crew_result, param_dict)

            logger.info(
                "✅ PERSISTENT Technical Debt wrapper completed 6R strategy analysis"
            )
            return strategy_result

        except Exception as e:
            logger.error(f"Error in Technical Debt analysis: {e}")
            return await self._fallback_strategy_analysis(param_dict, application_type)

    def _parse_crew_results(
        self, crew_result: Any, param_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Technical Debt Crew results into 6R strategy format."""
        try:
            # Extract strategy recommendations from crew result
            # This is a simplified parser - in production, this would be more sophisticated
            result_str = str(crew_result) if crew_result else ""

            # Look for 6R strategy mentions in the result (6R canonical)
            strategies = [
                "rehost",
                "replatform",
                "refactor",
                "rearchitect",
                "replace",
                "retire",
            ]
            strategy_scores = []

            recommended_strategy = "rehost"  # Default
            confidence_score = 0.8

            # Simple parsing logic - in production, this would use structured output
            for strategy in strategies:
                if strategy.lower() in result_str.lower():
                    score = 0.8 if strategy == recommended_strategy else 0.6
                    strategy_scores.append(
                        {
                            "strategy": strategy,
                            "score": score,
                            "confidence": confidence_score,
                        }
                    )

            if not strategy_scores:
                strategy_scores = [
                    {"strategy": "rehost", "score": 0.7, "confidence": 0.7}
                ]

            return {
                "recommended_strategy": recommended_strategy,
                "confidence_score": confidence_score,
                "strategy_scores": strategy_scores,
                "rationale": "AI-driven analysis using CrewAI Technical Debt Crew",
                "key_factors": [
                    "Technical debt assessment",
                    "Modernization opportunities",
                    "Risk analysis",
                ],
                "assumptions": ["AI-driven analysis based on technical debt crew"],
                "next_steps": [
                    "Review AI recommendations",
                    "Validate with stakeholders",
                ],
                "validation_errors": [],
                "crew_analysis": (
                    result_str[:500] + "..." if len(result_str) > 500 else result_str
                ),
                "ai_driven": True,
            }

        except Exception as e:
            logger.error(f"Error parsing crew results: {e}")
            return self._get_fallback_recommendation(param_dict)

    async def _fallback_strategy_analysis(
        self, param_dict: Dict[str, Any], application_type: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback strategy analysis when CrewAI is not available."""
        logger.info("Using fallback strategy analysis")

        # Simple rule-based fallback
        technical_complexity = param_dict.get("technical_complexity", 3)
        business_criticality = param_dict.get("business_criticality", 3)

        if technical_complexity <= 2 and business_criticality >= 4:
            recommended_strategy = "rehost"
        elif technical_complexity >= 4:
            recommended_strategy = (
                "rehost"  # Changed from "retain" - prefer rehost for complex systems
            )
        else:
            recommended_strategy = "replatform"

        return {
            "recommended_strategy": recommended_strategy,
            "confidence_score": 0.6,
            "strategy_scores": [
                {"strategy": recommended_strategy, "score": 0.7, "confidence": 0.6},
                {
                    "strategy": "rehost",
                    "score": 0.5,
                    "confidence": 0.5,
                },  # Changed from "retain"
            ],
            "rationale": "Simple rule-based analysis (fallback mode)",
            "key_factors": ["Technical complexity", "Business criticality"],
            "assumptions": [
                "Limited analysis data available",
                "Using default parameters",
            ],
            "next_steps": [
                "Conduct detailed assessment",
                "Gather additional application data",
            ],
            "validation_errors": [],
            "fallback_mode": True,
        }

    def _extract_parameter_values(self, parameters: Dict[str, Any]) -> Dict[str, float]:
        """Extract and normalize parameter values."""
        param_values = {}

        # Map parameters to standardized names and normalize to 1-5 scale
        for key, value in parameters.items():
            if isinstance(value, (int, float)):
                # Normalize to 1-5 scale
                normalized_value = max(1, min(5, float(value)))
                param_values[key] = normalized_value
            elif isinstance(value, str):
                # Convert string values to numeric
                string_to_numeric = {
                    "very_low": 1,
                    "low": 2,
                    "medium": 3,
                    "high": 4,
                    "very_high": 5,
                    "minimal": 1,
                    "moderate": 3,
                    "significant": 4,
                    "critical": 5,
                }
                param_values[key] = string_to_numeric.get(value.lower(), 3)

        # Ensure all required parameters have default values
        required_params = [
            "technical_complexity",
            "business_criticality",
            "cost_sensitivity",
            "timeline_urgency",
            "technical_debt",
            "compliance_requirements",
        ]

        for param in required_params:
            if param not in param_values:
                param_values[param] = 3  # Default to medium

        return param_values

    def update_strategy_weights(self, strategy: str, weights: Dict[str, float]) -> None:
        """Update strategy weights - now managed by CrewAI agents through learning."""
        try:
            # Store custom weights for potential use in crew configuration
            if not hasattr(self, "custom_weights"):
                self.custom_weights = {}
            self.custom_weights[strategy] = weights
            logger.info(
                f"Stored custom weights for strategy: {strategy} (will be used in crew configuration)"
            )
        except Exception as e:
            logger.error(f"Error storing strategy weights: {e}")

    def add_assumption(self, assumption: str) -> None:
        """Add a custom assumption to the analysis."""
        try:
            if assumption and assumption not in self.custom_assumptions:
                self.custom_assumptions.append(assumption)
                logger.info(f"Added assumption: {assumption}")
        except Exception as e:
            logger.error(f"Error adding assumption: {e}")

    def get_engine_status(self) -> Dict[str, Any]:
        """Get the current status of the engine and its components."""
        try:
            return {
                "engine_available": self.is_available(),
                "components": {
                    "ai_strategy_analysis": self.ai_strategy_available,
                    "technical_debt_crew": CREWAI_TECHNICAL_DEBT_AVAILABLE,
                    "risk_assessor": self.risk_assessor.is_available(),
                    "cost_calculator": self.cost_calculator.is_available(),
                    "recommendation_engine": self.recommendation_engine.is_available(),
                },
                "custom_assumptions_count": len(self.custom_assumptions),
                "custom_weights_count": len(getattr(self, "custom_weights", {})),
                "version": "3.0.0",  # Updated version for CrewAI integration
            }
        except Exception as e:
            logger.error(f"Error getting engine status: {e}")
            return {"engine_available": False, "error": str(e), "version": "3.0.0"}

    def _get_fallback_recommendation(
        self, parameters: SixRParameterBase
    ) -> Dict[str, Any]:
        """Provide fallback recommendation when analysis fails."""
        return {
            "recommended_strategy": "rehost",
            "confidence_score": 0.3,
            "strategy_scores": [
                {"strategy": "rehost", "score": 0.6, "confidence": 0.3},
                {
                    "strategy": "replatform",
                    "score": 0.5,
                    "confidence": 0.3,
                },  # Changed from "retain"
            ],
            "rationale": "Default conservative recommendation due to analysis limitations.",
            "key_factors": ["Limited analysis capability"],
            "validation_errors": ["Engine analysis error"],
            "risk_factors": ["Unknown risks due to analysis limitations"],
            "cost_impact": "Medium",
            "effort_estimate": "6-12 months",
            "benefits": ["Cloud migration benefits"],
            "next_steps": ["Conduct detailed assessment", "Plan migration strategy"],
            "assumptions": ["Manual analysis required"],
            "fallback_mode": True,
            "engine_status": self.get_engine_status(),
        }


# Create default engine instance (without CrewAI service for backward compatibility)
# For CrewAI-enabled analysis, create engine with: SixRDecisionEngine(crewai_service=your_service)
# Bug #666 - Phase 1: Explicitly pass None to indicate fallback mode
sixr_engine = SixRDecisionEngine(crewai_service=None)
