"""
6R Engine - Modular & Robust
Combines robust error handling with clean modular architecture.
"""

import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from .sixr_handlers import (
    StrategyAnalyzer,
    RiskAssessor,
    CostCalculator,
    RecommendationEngine
)

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
    """Modular 6R Decision Engine with robust error handling."""
    
    def __init__(self):
        # Initialize handlers
        self.strategy_analyzer = StrategyAnalyzer()
        self.risk_assessor = RiskAssessor()
        self.cost_calculator = CostCalculator()
        self.recommendation_engine = RecommendationEngine()
        
        # Engine state
        self.custom_assumptions = []
        logger.info("6R Decision Engine initialized with modular handlers")
    
    def is_available(self) -> bool:
        """Check if the engine is properly initialized."""
        return all([
            self.strategy_analyzer.is_available(),
            self.risk_assessor.is_available(),
            self.cost_calculator.is_available(),
            self.recommendation_engine.is_available()
        ])
    
    async def analyze_parameters(
        self, 
        parameters: SixRParameterBase,
        application_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main analysis method that coordinates all handlers.
        """
        try:
            # Convert parameters to dict
            param_dict = parameters.dict() if hasattr(parameters, 'dict') else dict(parameters)
            
            # Core strategy analysis
            strategy_result = await self.strategy_analyzer.analyze_parameters(
                param_dict, 
                application_type
            )
            
            if strategy_result.get("fallback_mode"):
                return strategy_result
            
            # Extract top strategy and parameters
            top_strategy = strategy_result["recommended_strategy"]
            param_values = self.strategy_analyzer._extract_parameter_values(param_dict)
            
            # Enhanced analysis using other handlers
            try:
                # Risk assessment
                risks = await self.risk_assessor.assess_risks(top_strategy, param_values)
                
                # Cost and effort estimation
                cost_impact = await self.cost_calculator.estimate_cost_impact(top_strategy, param_values)
                effort_estimate = await self.cost_calculator.estimate_effort(top_strategy, param_values)
                
                # Benefits and next steps
                benefits = await self.recommendation_engine.identify_benefits(top_strategy, param_values)
                next_steps = await self.recommendation_engine.generate_next_steps(top_strategy, param_dict)
                assumptions = await self.recommendation_engine.generate_assumptions(param_dict, top_strategy)
                
                # Enhanced result
                enhanced_result = strategy_result.copy()
                enhanced_result.update({
                    "risk_factors": risks,
                    "cost_impact": cost_impact,
                    "effort_estimate": effort_estimate,
                    "benefits": benefits,
                    "next_steps": next_steps,
                    "assumptions": assumptions + self.custom_assumptions,
                    "engine_status": self.get_engine_status()
                })
                
                return enhanced_result
                
            except Exception as e:
                logger.warning(f"Error in enhanced analysis, returning basic result: {e}")
                # Return basic strategy result if enhanced analysis fails
                strategy_result["enhanced_analysis_error"] = str(e)
                return strategy_result
            
        except Exception as e:
            logger.error(f"Error in analyze_parameters: {e}")
            return self._get_fallback_recommendation(parameters)
    
    def update_strategy_weights(self, strategy: str, weights: Dict[str, float]) -> None:
        """Update strategy weights in the analyzer."""
        try:
            if hasattr(self.strategy_analyzer, 'strategy_weights'):
                if strategy in self.strategy_analyzer.strategy_weights:
                    self.strategy_analyzer.strategy_weights[strategy].update(weights)
                    logger.info(f"Updated weights for strategy: {strategy}")
                else:
                    logger.warning(f"Strategy {strategy} not found")
            else:
                logger.warning("Strategy analyzer not properly initialized")
        except Exception as e:
            logger.error(f"Error updating strategy weights: {e}")
    
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
                    "strategy_analyzer": self.strategy_analyzer.is_available(),
                    "risk_assessor": self.risk_assessor.is_available(),
                    "cost_calculator": self.cost_calculator.is_available(),
                    "recommendation_engine": self.recommendation_engine.is_available()
                },
                "custom_assumptions_count": len(self.custom_assumptions),
                "version": "2.0.0"
            }
        except Exception as e:
            logger.error(f"Error getting engine status: {e}")
            return {
                "engine_available": False,
                "error": str(e),
                "version": "2.0.0"
            }
    
    def _get_fallback_recommendation(self, parameters: SixRParameterBase) -> Dict[str, Any]:
        """Provide fallback recommendation when analysis fails."""
        return {
            "recommended_strategy": "rehost",
            "confidence_score": 0.3,
            "all_strategies": [
                {"strategy": "rehost", "score": 0.6, "confidence": 0.3},
                {"strategy": "retain", "score": 0.5, "confidence": 0.3}
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
            "engine_status": self.get_engine_status()
        }

# Create default engine instance
sixr_engine = SixRDecisionEngine() 