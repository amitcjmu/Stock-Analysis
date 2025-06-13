"""
Strategy Analyzer Handler
Handles core 6R strategy analysis and scoring operations.
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
from app.models.asset import SixRStrategy

logger = logging.getLogger(__name__)



class ApplicationType(str, Enum):
    WEB_APPLICATION = "web_application"
    DATABASE = "database"
    LEGACY_SYSTEM = "legacy_system"
    MICROSERVICE = "microservice"
    MONOLITH = "monolith"
    API_SERVICE = "api_service"
    BATCH_PROCESSING = "batch_processing"

class StrategyAnalyzer:
    """Handles 6R strategy analysis with graceful fallbacks."""
    
    def __init__(self):
        self.strategy_weights = self._initialize_strategy_weights()
        self.parameter_weights = self._initialize_parameter_weights()
        self.scoring_rules = self._initialize_scoring_rules()
        self.service_available = True
        logger.info("Strategy analyzer initialized successfully")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def analyze_parameters(self, parameters: Dict[str, Any], application_type: ApplicationType = None) -> Dict[str, Any]:
        """
        Main strategy analysis method.
        """
        try:
            # Extract parameter values
            param_values = self._extract_parameter_values(parameters)
            
            # Get available strategies based on application type
            available_strategies = self._get_available_strategies(application_type or ApplicationType.WEB_APPLICATION)
            
            # Calculate scores for each strategy
            strategy_scores = []
            for strategy in available_strategies:
                score_info = self._calculate_strategy_score(strategy, param_values, parameters)
                strategy_scores.append(score_info)
            
            # Sort by score (highest first)
            strategy_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Calculate confidence
            confidence = self._calculate_confidence_score(strategy_scores, param_values)
            
            # Generate rationale for top strategy
            top_strategy = SixRStrategy(strategy_scores[0]['strategy'])
            rationale = self._generate_rationale(top_strategy, param_values, parameters)
            
            return {
                "recommended_strategy": strategy_scores[0]['strategy'],
                "confidence_score": confidence,
                "all_strategies": strategy_scores,
                "rationale": rationale,
                "key_factors": self._identify_key_factors(parameters, strategy_scores),
                "validation_errors": self._validate_parameters(parameters)
            }
            
        except Exception as e:
            logger.error(f"Error in strategy analysis: {e}")
            return self._get_fallback_recommendation(parameters)
    
    def _initialize_strategy_weights(self) -> Dict[SixRStrategy, Dict[str, float]]:
        """Initialize strategy-specific parameter weights."""
        return {
            SixRStrategy.REHOST: {
                "technical_complexity": 0.15,
                "business_criticality": 0.20,
                "cost_sensitivity": 0.15,
                "timeline_urgency": 0.20,
                "technical_debt": 0.10,
                "compliance_requirements": 0.20
            },
            SixRStrategy.REPLATFORM: {
                "technical_complexity": 0.25,
                "business_criticality": 0.15,
                "cost_sensitivity": 0.20,
                "timeline_urgency": 0.15,
                "technical_debt": 0.15,
                "compliance_requirements": 0.10
            },
            SixRStrategy.REFACTOR: {
                "technical_complexity": 0.30,
                "business_criticality": 0.10,
                "cost_sensitivity": 0.20,
                "timeline_urgency": 0.05,
                "technical_debt": 0.25,
                "compliance_requirements": 0.10
            },
            SixRStrategy.REPURCHASE: {
                "technical_complexity": 0.10,
                "business_criticality": 0.25,
                "cost_sensitivity": 0.25,
                "timeline_urgency": 0.20,
                "technical_debt": 0.05,
                "compliance_requirements": 0.15
            },
            SixRStrategy.RETAIN: {
                "technical_complexity": 0.05,
                "business_criticality": 0.30,
                "cost_sensitivity": 0.25,
                "timeline_urgency": 0.10,
                "technical_debt": 0.05,
                "compliance_requirements": 0.25
            },
            SixRStrategy.RETIRE: {
                "technical_complexity": 0.05,
                "business_criticality": 0.10,
                "cost_sensitivity": 0.30,
                "timeline_urgency": 0.05,
                "technical_debt": 0.05,
                "compliance_requirements": 0.05
            }
        }
    
    def _initialize_parameter_weights(self) -> Dict[str, float]:
        """Initialize global parameter weights."""
        return {
            "technical_complexity": 0.20,
            "business_criticality": 0.25,
            "cost_sensitivity": 0.15,
            "timeline_urgency": 0.15,
            "technical_debt": 0.15,
            "compliance_requirements": 0.10
        }
    
    def _initialize_scoring_rules(self) -> Dict[SixRStrategy, Dict[str, Any]]:
        """Initialize scoring rules for each strategy."""
        return {
            SixRStrategy.REHOST: {
                "optimal_ranges": {
                    "technical_complexity": (1, 3),
                    "business_criticality": (3, 5),
                    "timeline_urgency": (4, 5)
                },
                "penalties": {
                    "high_complexity": {"technical_complexity": (4, 5), "penalty": -0.3},
                    "low_criticality": {"business_criticality": (1, 2), "penalty": -0.2}
                }
            },
            SixRStrategy.REPLATFORM: {
                "optimal_ranges": {
                    "technical_complexity": (2, 4),
                    "business_criticality": (2, 4),
                    "technical_debt": (3, 5)
                },
                "penalties": {
                    "high_complexity": {"technical_complexity": (5, 5), "penalty": -0.4}
                }
            },
            SixRStrategy.REFACTOR: {
                "optimal_ranges": {
                    "technical_complexity": (3, 5),
                    "technical_debt": (4, 5),
                    "business_criticality": (3, 5)
                },
                "penalties": {
                    "low_complexity": {"technical_complexity": (1, 2), "penalty": -0.5},
                    "urgent_timeline": {"timeline_urgency": (4, 5), "penalty": -0.6}
                }
            },
            SixRStrategy.REPURCHASE: {
                "optimal_ranges": {
                    "business_criticality": (3, 5),
                    "cost_sensitivity": (1, 3),
                    "timeline_urgency": (3, 5)
                },
                "penalties": {
                    "high_cost_sensitivity": {"cost_sensitivity": (4, 5), "penalty": -0.4}
                }
            },
            SixRStrategy.RETAIN: {
                "optimal_ranges": {
                    "business_criticality": (4, 5),
                    "cost_sensitivity": (4, 5),
                    "compliance_requirements": (4, 5)
                },
                "penalties": {
                    "low_criticality": {"business_criticality": (1, 3), "penalty": -0.7}
                }
            },
            SixRStrategy.RETIRE: {
                "optimal_ranges": {
                    "business_criticality": (1, 2),
                    "cost_sensitivity": (4, 5),
                    "technical_debt": (1, 3)
                },
                "penalties": {
                    "high_criticality": {"business_criticality": (4, 5), "penalty": -0.8}
                }
            }
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
                    'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5,
                    'minimal': 1, 'moderate': 3, 'significant': 4, 'critical': 5
                }
                param_values[key] = string_to_numeric.get(value.lower(), 3)
        
        # Ensure all required parameters have default values
        required_params = [
            'technical_complexity', 'business_criticality', 'cost_sensitivity',
            'timeline_urgency', 'technical_debt', 'compliance_requirements'
        ]
        
        for param in required_params:
            if param not in param_values:
                param_values[param] = 3  # Default to medium
        
        return param_values
    
    def _get_available_strategies(self, application_type: ApplicationType) -> List[SixRStrategy]:
        """Get available strategies based on application type."""
        strategy_map = {
            ApplicationType.WEB_APPLICATION: list(SixRStrategy),
            ApplicationType.DATABASE: [
                SixRStrategy.REHOST, SixRStrategy.REPLATFORM,
                SixRStrategy.REPURCHASE, SixRStrategy.RETAIN
            ],
            ApplicationType.LEGACY_SYSTEM: [
                SixRStrategy.REHOST, SixRStrategy.REPURCHASE,
                SixRStrategy.RETAIN, SixRStrategy.RETIRE
            ],
            ApplicationType.MICROSERVICE: [
                SixRStrategy.REHOST, SixRStrategy.REPLATFORM,
                SixRStrategy.REFACTOR
            ],
            ApplicationType.MONOLITH: list(SixRStrategy),
            ApplicationType.API_SERVICE: [
                SixRStrategy.REHOST, SixRStrategy.REPLATFORM,
                SixRStrategy.REFACTOR, SixRStrategy.RETAIN
            ],
            ApplicationType.BATCH_PROCESSING: [
                SixRStrategy.REHOST, SixRStrategy.REPLATFORM,
                SixRStrategy.REFACTOR, SixRStrategy.RETAIN, SixRStrategy.RETIRE
            ]
        }
        
        return strategy_map.get(application_type, list(SixRStrategy))
    
    def _calculate_strategy_score(self, strategy: SixRStrategy, param_values: Dict[str, float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate score for a specific strategy."""
        try:
            strategy_weights = self.strategy_weights.get(strategy, {})
            scoring_rules = self.scoring_rules.get(strategy, {})
            
            # Calculate base score
            base_score = 0
            for param, value in param_values.items():
                weight = strategy_weights.get(param, 0)
                optimal_range = scoring_rules.get("optimal_ranges", {}).get(param, (1, 5))
                param_score = self._calculate_parameter_score(value, optimal_range)
                base_score += param_score * weight
            
            # Apply penalties
            penalties = self._calculate_penalties(strategy, param_values, scoring_rules)
            final_score = max(0, base_score + penalties)
            
            # Calculate strategy-specific confidence
            confidence = self._calculate_strategy_confidence(strategy, param_values)
            
            return {
                "strategy": strategy.value,
                "score": round(final_score, 3),
                "confidence": confidence,
                "base_score": round(base_score, 3),
                "penalties": round(penalties, 3)
            }
            
        except Exception as e:
            logger.warning(f"Error calculating score for strategy {strategy}: {e}")
            return {
                "strategy": strategy.value,
                "score": 0.5,
                "confidence": 0.3,
                "base_score": 0.5,
                "penalties": 0,
                "error": str(e)
            }
    
    def _calculate_parameter_score(self, value: float, optimal_range: Tuple[float, float]) -> float:
        """Calculate score for a parameter based on optimal range."""
        min_optimal, max_optimal = optimal_range
        
        if min_optimal <= value <= max_optimal:
            return 1.0  # Perfect score within optimal range
        elif value < min_optimal:
            # Linear decay below optimal range
            distance = min_optimal - value
            return max(0, 1.0 - (distance / min_optimal))
        else:
            # Linear decay above optimal range
            distance = value - max_optimal
            return max(0, 1.0 - (distance / (5 - max_optimal)))
    
    def _calculate_penalties(self, strategy: SixRStrategy, param_values: Dict[str, float], scoring_rules: Dict[str, Any]) -> float:
        """Calculate penalties for a strategy."""
        total_penalty = 0
        penalties = scoring_rules.get("penalties", {})
        
        for penalty_name, penalty_config in penalties.items():
            if self._check_penalty_condition(penalty_name, param_values, penalty_config):
                total_penalty += penalty_config.get("penalty", 0)
        
        return total_penalty
    
    def _check_penalty_condition(self, penalty_name: str, param_values: Dict[str, float], penalty_config: Dict[str, Any]) -> bool:
        """Check if penalty condition is met."""
        try:
            for param, condition_range in penalty_config.items():
                if param == "penalty":
                    continue
                
                value = param_values.get(param, 3)
                if isinstance(condition_range, tuple) and len(condition_range) == 2:
                    min_val, max_val = condition_range
                    if min_val <= value <= max_val:
                        return True
            
            return False
        except Exception:
            return False
    
    def _calculate_confidence_score(self, strategy_scores: List[Dict[str, Any]], param_values: Dict[str, float]) -> float:
        """Calculate overall confidence in the analysis."""
        if not strategy_scores:
            return 0.3
        
        # Base confidence from score separation
        top_score = strategy_scores[0]['score']
        second_score = strategy_scores[1]['score'] if len(strategy_scores) > 1 else 0
        score_separation = top_score - second_score
        
        confidence = min(1.0, 0.5 + score_separation)
        
        # Adjust based on parameter completeness
        required_params = ['technical_complexity', 'business_criticality', 'cost_sensitivity']
        param_completeness = sum(1 for param in required_params if param in param_values) / len(required_params)
        confidence *= param_completeness
        
        return round(confidence, 3)
    
    def _calculate_strategy_confidence(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> float:
        """Calculate confidence for a specific strategy."""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on parameter alignment with strategy
        strategy_weights = self.strategy_weights.get(strategy, {})
        for param, weight in strategy_weights.items():
            if param in param_values:
                # Higher weight parameters contribute more to confidence
                confidence += weight * 0.1
        
        return min(1.0, confidence)
    
    def _generate_rationale(self, strategy: SixRStrategy, param_values: Dict[str, float], parameters: Dict[str, Any]) -> str:
        """Generate rationale for the recommended strategy."""
        try:
            rationale_templates = {
                SixRStrategy.REHOST: "Lift-and-shift migration is recommended due to {factors}. This approach minimizes risk while achieving cloud benefits.",
                SixRStrategy.REPLATFORM: "Platform modernization is recommended to {benefits} while maintaining core functionality.",
                SixRStrategy.REFACTOR: "Application refactoring is recommended to {benefits} and address technical debt.",
                SixRStrategy.REPURCHASE: "Replacing with SaaS solution is recommended due to {factors}.",
                SixRStrategy.RETAIN: "Keeping on-premises is recommended due to {factors}.",
                SixRStrategy.RETIRE: "Decommissioning is recommended as {factors}."
            }
            
            # Identify key factors driving the recommendation
            factors = []
            if param_values.get('business_criticality', 3) >= 4:
                factors.append("high business criticality")
            if param_values.get('technical_complexity', 3) <= 2:
                factors.append("low technical complexity")
            if param_values.get('timeline_urgency', 3) >= 4:
                factors.append("urgent timeline requirements")
            if param_values.get('cost_sensitivity', 3) >= 4:
                factors.append("high cost sensitivity")
            
            factors_text = ", ".join(factors) if factors else "current application characteristics"
            
            template = rationale_templates.get(strategy, "This strategy is recommended based on the analysis.")
            return template.format(factors=factors_text, benefits=factors_text)
            
        except Exception as e:
            logger.warning(f"Error generating rationale: {e}")
            return f"Strategy {strategy.value} is recommended based on the parameter analysis."
    
    def _identify_key_factors(self, parameters: Dict[str, Any], strategy_scores: List[Dict[str, Any]]) -> List[str]:
        """Identify key factors influencing the recommendation."""
        factors = []
        
        try:
            # Analyze parameter values
            param_values = self._extract_parameter_values(parameters)
            
            for param, value in param_values.items():
                if value >= 4:
                    factors.append(f"High {param.replace('_', ' ')}")
                elif value <= 2:
                    factors.append(f"Low {param.replace('_', ' ')}")
            
            # Add score-based factors
            if len(strategy_scores) > 1:
                score_diff = strategy_scores[0]['score'] - strategy_scores[1]['score']
                if score_diff > 0.3:
                    factors.append("Clear strategy preference")
                elif score_diff < 0.1:
                    factors.append("Multiple viable strategies")
        
        except Exception as e:
            logger.warning(f"Error identifying key factors: {e}")
            factors = ["Parameter analysis completed"]
        
        return factors[:5]  # Return top 5 factors
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []
        
        required_fields = ['technical_complexity', 'business_criticality']
        for field in required_fields:
            if field not in parameters:
                errors.append(f"Missing required parameter: {field}")
        
        # Check value ranges
        for key, value in parameters.items():
            if isinstance(value, (int, float)):
                if not 1 <= value <= 5:
                    errors.append(f"Parameter {key} should be between 1 and 5")
        
        return errors
    
    def _get_fallback_recommendation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback recommendation when analysis fails."""
        return {
            "recommended_strategy": "rehost",
            "confidence_score": 0.3,
            "all_strategies": [
                {"strategy": "rehost", "score": 0.6, "confidence": 0.3},
                {"strategy": "retain", "score": 0.5, "confidence": 0.3}
            ],
            "rationale": "Default recommendation based on conservative approach due to analysis limitations.",
            "key_factors": ["Limited parameter data"],
            "validation_errors": ["Analysis error occurred"],
            "fallback_mode": True
        } 