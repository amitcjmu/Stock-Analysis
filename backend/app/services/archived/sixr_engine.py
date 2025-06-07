"""
6R Decision Engine for migration strategy analysis and recommendations.
Implements weighted decision matrix and scoring algorithms for each 6R strategy.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math

try:
    from app.schemas.sixr_analysis import (
        SixRStrategy, SixRParameterBase, SixRRecommendation, 
        SixRRecommendationScore, ApplicationType
    )
except ImportError:
    # Fallback for testing
    from enum import Enum
    
    class SixRStrategy(str, Enum):
        REHOST = "rehost"
        REPLATFORM = "replatform"
        REFACTOR = "refactor"
        REARCHITECT = "rearchitect"
        REWRITE = "rewrite"
        REPLACE = "replace"
        RETIRE = "retire"
    
    class ApplicationType(str, Enum):
        CUSTOM = "custom"
        COTS = "cots"
        HYBRID = "hybrid"

logger = logging.getLogger(__name__)


class SixRDecisionEngine:
    """Core 6R decision engine with weighted scoring matrix."""
    
    def __init__(self):
        self.strategy_weights = self._initialize_strategy_weights()
        self.parameter_weights = self._initialize_parameter_weights()
        self.scoring_rules = self._initialize_scoring_rules()
        self.assumptions = []
        
    def _initialize_strategy_weights(self) -> Dict[SixRStrategy, Dict[str, float]]:
        """Initialize strategy-specific parameter weights."""
        return {
            SixRStrategy.REHOST: {
                "business_value": 0.15,
                "technical_complexity": 0.20,
                "migration_urgency": 0.25,
                "compliance_requirements": 0.15,
                "cost_sensitivity": 0.15,
                "risk_tolerance": 0.05,
                "innovation_priority": 0.05
            },
            SixRStrategy.REPLATFORM: {
                "business_value": 0.20,
                "technical_complexity": 0.15,
                "migration_urgency": 0.15,
                "compliance_requirements": 0.15,
                "cost_sensitivity": 0.15,
                "risk_tolerance": 0.10,
                "innovation_priority": 0.10
            },
            SixRStrategy.REFACTOR: {
                "business_value": 0.25,
                "technical_complexity": 0.10,
                "migration_urgency": 0.05,
                "compliance_requirements": 0.15,
                "cost_sensitivity": 0.10,
                "risk_tolerance": 0.15,
                "innovation_priority": 0.20
            },
            SixRStrategy.REARCHITECT: {
                "business_value": 0.30,
                "technical_complexity": 0.05,
                "migration_urgency": 0.05,
                "compliance_requirements": 0.10,
                "cost_sensitivity": 0.05,
                "risk_tolerance": 0.20,
                "innovation_priority": 0.25
            },
            SixRStrategy.RETIRE: {
                "business_value": 0.05,
                "technical_complexity": 0.30,
                "migration_urgency": 0.20,
                "compliance_requirements": 0.20,
                "cost_sensitivity": 0.20,
                "risk_tolerance": 0.03,
                "innovation_priority": 0.02
            },
            SixRStrategy.REWRITE: {
                "business_value": 0.35,
                "technical_complexity": 0.05,
                "migration_urgency": 0.05,
                "compliance_requirements": 0.10,
                "cost_sensitivity": 0.05,
                "risk_tolerance": 0.15,
                "innovation_priority": 0.25
            },
            SixRStrategy.REPLACE: {
                "business_value": 0.20,
                "technical_complexity": 0.25,
                "migration_urgency": 0.15,
                "compliance_requirements": 0.15,
                "cost_sensitivity": 0.15,
                "risk_tolerance": 0.05,
                "innovation_priority": 0.05
            }
        }
    
    def _initialize_parameter_weights(self) -> Dict[str, float]:
        """Initialize global parameter weights for normalization."""
        # Weights should sum to 1.0 for proper normalization
        return {
            "business_value": 0.20,          # 20% - Business impact
            "technical_complexity": 0.15,    # 15% - Technical difficulty
            "migration_urgency": 0.15,       # 15% - Timeline pressure
            "compliance_requirements": 0.10, # 10% - Regulatory constraints
            "cost_sensitivity": 0.15,        # 15% - Budget constraints
            "risk_tolerance": 0.15,          # 15% - Risk appetite
            "innovation_priority": 0.10      # 10% - Innovation focus
        }
    
    def _initialize_scoring_rules(self) -> Dict[SixRStrategy, Dict[str, Any]]:
        """Initialize scoring rules for each strategy."""
        return {
            SixRStrategy.REHOST: {
                "optimal_ranges": {
                    "business_value": (3, 7),
                    "technical_complexity": (1, 5),
                    "migration_urgency": (7, 10),
                    "compliance_requirements": (1, 6),
                    "cost_sensitivity": (7, 10),
                    "risk_tolerance": (1, 4),
                    "innovation_priority": (1, 4)
                },
                "penalty_factors": {
                    "high_complexity": 0.8,
                    "low_urgency": 0.7,
                    "high_innovation_need": 0.6
                }
            },
            SixRStrategy.REPLATFORM: {
                "optimal_ranges": {
                    "business_value": (5, 8),
                    "technical_complexity": (3, 7),
                    "migration_urgency": (5, 8),
                    "compliance_requirements": (3, 7),
                    "cost_sensitivity": (4, 8),
                    "risk_tolerance": (3, 7),
                    "innovation_priority": (4, 7)
                },
                "penalty_factors": {
                    "very_high_complexity": 0.7,
                    "very_low_urgency": 0.8,
                    "very_high_cost_sensitivity": 0.8
                }
            },
            SixRStrategy.REFACTOR: {
                "optimal_ranges": {
                    "business_value": (6, 10),
                    "technical_complexity": (4, 8),
                    "migration_urgency": (3, 7),
                    "compliance_requirements": (4, 8),
                    "cost_sensitivity": (3, 7),
                    "risk_tolerance": (5, 8),
                    "innovation_priority": (6, 9)
                },
                "penalty_factors": {
                    "high_urgency": 0.7,
                    "low_risk_tolerance": 0.6,
                    "low_innovation_priority": 0.5
                }
            },
            SixRStrategy.REARCHITECT: {
                "optimal_ranges": {
                    "business_value": (8, 10),
                    "technical_complexity": (5, 10),
                    "migration_urgency": (1, 5),
                    "compliance_requirements": (3, 8),
                    "cost_sensitivity": (1, 5),
                    "risk_tolerance": (7, 10),
                    "innovation_priority": (8, 10)
                },
                "penalty_factors": {
                    "high_urgency": 0.5,
                    "high_cost_sensitivity": 0.6,
                    "low_risk_tolerance": 0.4,
                    "low_innovation_priority": 0.3
                }
            },
            SixRStrategy.RETIRE: {
                "optimal_ranges": {
                    "business_value": (1, 3),
                    "technical_complexity": (7, 10),
                    "migration_urgency": (5, 10),
                    "compliance_requirements": (1, 8),
                    "cost_sensitivity": (7, 10),
                    "risk_tolerance": (1, 5),
                    "innovation_priority": (1, 3)
                },
                "penalty_factors": {
                    "high_business_value": 0.3,
                    "low_complexity": 0.7,
                    "high_innovation_priority": 0.4
                }
            },
            SixRStrategy.REWRITE: {
                "optimal_ranges": {
                    "business_value": (8, 10),
                    "technical_complexity": (1, 10),
                    "migration_urgency": (1, 6),
                    "compliance_requirements": (1, 8),
                    "cost_sensitivity": (1, 6),
                    "risk_tolerance": (6, 10),
                    "innovation_priority": (8, 10)
                },
                "penalty_factors": {
                    "high_urgency": 0.4,
                    "high_cost_sensitivity": 0.5,
                    "low_risk_tolerance": 0.3,
                    "low_innovation_priority": 0.2,
                    "low_business_value": 0.4
                }
            },
            SixRStrategy.REPLACE: {
                "optimal_ranges": {
                    "business_value": (4, 8),
                    "technical_complexity": (6, 10),
                    "migration_urgency": (5, 9),
                    "compliance_requirements": (1, 8),
                    "cost_sensitivity": (4, 8),
                    "risk_tolerance": (3, 7),
                    "innovation_priority": (3, 7)
                },
                "penalty_factors": {
                    "low_complexity": 0.7,
                    "low_urgency": 0.8,
                    "high_cost_sensitivity": 0.8,
                    "low_business_value": 0.6
                }
            }
        }
    
    def analyze_parameters(self, parameters: SixRParameterBase, 
                          application_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze 6R parameters and return comprehensive recommendation.
        
        Args:
            parameters: 6R analysis parameters
            application_context: Additional application context data
            
        Returns:
            Dictionary containing complete analysis results
        """
        try:
            # Validate parameters
            validation_errors = self._validate_parameters(parameters)
            if validation_errors:
                logger.warning(f"Parameter validation warnings: {validation_errors}")
            
            # Convert parameters to dict for processing
            param_values = {
                "business_value": parameters.business_value,
                "technical_complexity": parameters.technical_complexity,
                "migration_urgency": parameters.migration_urgency,
                "compliance_requirements": parameters.compliance_requirements,
                "cost_sensitivity": parameters.cost_sensitivity,
                "risk_tolerance": parameters.risk_tolerance,
                "innovation_priority": parameters.innovation_priority
            }
            
            # Calculate scores for each strategy
            strategy_scores = []
            strategy_details = {}
            
            # Get available strategies based on application type
            available_strategies = self._get_available_strategies(parameters.application_type)
            
            for strategy in available_strategies:
                score_data = self._calculate_strategy_score(strategy, parameters, application_context)
                strategy_scores.append(score_data)
                strategy_details[strategy] = score_data
            
            # Sort strategies by score (highest first)
            strategy_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Get top recommendation
            recommended_strategy = strategy_scores[0]['strategy']
            
            # Calculate overall confidence
            confidence_score = self._calculate_confidence_score(strategy_scores, parameters)
            
            # Generate analysis insights
            key_factors = self._identify_key_factors(parameters, strategy_scores)
            assumptions = self._generate_assumptions(parameters, application_context)
            next_steps = self._generate_next_steps(recommended_strategy, parameters)
            
            # Estimate effort, timeline, and cost impact
            effort_estimate = self._estimate_effort(recommended_strategy, param_values)
            timeline_estimate = self._estimate_timeline(recommended_strategy, param_values)
            cost_impact = self._estimate_cost_impact(recommended_strategy, param_values)
            
            # Format strategy scores for response
            formatted_scores = []
            for score_data in strategy_scores:
                formatted_score = {
                    'strategy': score_data['strategy'],
                    'score': round(score_data['score'], 1),
                    'confidence': round(score_data['confidence'], 2),
                    'rationale': score_data['rationale'],
                    'risk_factors': score_data['risk_factors'],
                    'benefits': score_data['benefits']
                }
                formatted_scores.append(formatted_score)
            
            # Build comprehensive response
            result = {
                'recommended_strategy': recommended_strategy,
                'confidence_score': round(confidence_score, 2),
                'strategy_scores': formatted_scores,
                'key_factors': key_factors,
                'assumptions': assumptions,
                'next_steps': next_steps,
                'estimated_effort': effort_estimate,
                'estimated_timeline': timeline_estimate,
                'estimated_cost_impact': cost_impact,
                'risk_factors': strategy_details[recommended_strategy]['risk_factors'],
                'business_benefits': self._identify_business_benefits(recommended_strategy, param_values),
                'technical_benefits': self._identify_technical_benefits(recommended_strategy, param_values),
                'analysis_metadata': {
                    'engine_version': '1.0',
                    'analysis_timestamp': datetime.now().isoformat(),
                    'parameter_hash': self._calculate_parameter_hash(param_values),
                    'application_type': parameters.application_type
                }
            }
            
            logger.info(f"Analysis completed: {recommended_strategy} with {confidence_score:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return fallback recommendation
            return self._get_fallback_recommendation(parameters)
    
    def _get_available_strategies(self, application_type: ApplicationType) -> List[SixRStrategy]:
        """Get available strategies based on application type."""
        base_strategies = [
            SixRStrategy.REHOST,
            SixRStrategy.REPLATFORM,
            SixRStrategy.REFACTOR,
            SixRStrategy.REARCHITECT,
            SixRStrategy.RETIRE
        ]
        
        if application_type == ApplicationType.CUSTOM:
            # Custom applications can use REWRITE
            base_strategies.append(SixRStrategy.REWRITE)
        elif application_type == ApplicationType.COTS:
            # COTS applications can use REPLACE instead of REWRITE
            base_strategies.append(SixRStrategy.REPLACE)
        else:  # HYBRID
            # Hybrid applications can use both
            base_strategies.extend([SixRStrategy.REWRITE, SixRStrategy.REPLACE])
        
        return base_strategies
    
    def _estimate_effort(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> str:
        """Estimate effort level based on strategy and parameters."""
        base_effort = {
            SixRStrategy.REHOST: 1,
            SixRStrategy.REPLATFORM: 2,
            SixRStrategy.REFACTOR: 3,
            SixRStrategy.REARCHITECT: 4,
            SixRStrategy.REWRITE: 5,
            SixRStrategy.REPLACE: 2,
            SixRStrategy.RETIRE: 1
        }
        
        effort_score = base_effort.get(strategy, 3)
        
        # Adjust based on complexity
        complexity_factor = param_values['technical_complexity'] / 10.0
        effort_score += complexity_factor * 2
        
        # Adjust based on compliance requirements
        compliance_factor = param_values['compliance_requirements'] / 10.0
        effort_score += compliance_factor * 1.5
        
        if effort_score <= 2:
            return 'low'
        elif effort_score <= 3.5:
            return 'medium'
        elif effort_score <= 4.5:
            return 'high'
        else:
            return 'very_high'
    
    def _estimate_timeline(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> str:
        """Estimate timeline based on strategy and parameters."""
        base_timeline = {
            SixRStrategy.REHOST: '1-3 months',
            SixRStrategy.REPLATFORM: '2-4 months',
            SixRStrategy.REFACTOR: '4-8 months',
            SixRStrategy.REARCHITECT: '8-18 months',
            SixRStrategy.REWRITE: '12-24 months',
            SixRStrategy.REPLACE: '3-6 months',
            SixRStrategy.RETIRE: '1-2 months'
        }
        
        timeline = base_timeline.get(strategy, '3-6 months')
        
        # Adjust for urgency
        urgency = param_values['migration_urgency']
        if urgency >= 8:
            # High urgency - compress timeline
            timeline_map = {
                '1-3 months': '1-2 months',
                '2-4 months': '2-3 months',
                '4-8 months': '3-6 months',
                '8-18 months': '6-12 months',
                '12-24 months': '8-18 months',
                '3-6 months': '2-4 months',
                '1-2 months': '1 month'
            }
            timeline = timeline_map.get(timeline, timeline)
        elif urgency <= 3:
            # Low urgency - extend timeline
            timeline_map = {
                '1-3 months': '2-4 months',
                '2-4 months': '3-6 months',
                '4-8 months': '6-12 months',
                '8-18 months': '12-24 months',
                '12-24 months': '18-36 months',
                '3-6 months': '4-8 months',
                '1-2 months': '2-3 months'
            }
            timeline = timeline_map.get(timeline, timeline)
        
        return timeline
    
    def _estimate_cost_impact(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> str:
        """Estimate cost impact based on strategy and parameters."""
        base_cost = {
            SixRStrategy.REHOST: 1,
            SixRStrategy.REPLATFORM: 2,
            SixRStrategy.REFACTOR: 3,
            SixRStrategy.REARCHITECT: 4,
            SixRStrategy.REWRITE: 5,
            SixRStrategy.REPLACE: 3,
            SixRStrategy.RETIRE: 1
        }
        
        cost_score = base_cost.get(strategy, 3)
        
        # Adjust based on cost sensitivity
        cost_sensitivity = param_values['cost_sensitivity']
        if cost_sensitivity >= 8:
            cost_score -= 1  # More cost-conscious approach
        elif cost_sensitivity <= 3:
            cost_score += 1  # Less cost-conscious
        
        # Adjust based on complexity
        complexity_factor = param_values['technical_complexity'] / 10.0
        cost_score += complexity_factor * 1.5
        
        if cost_score <= 1.5:
            return 'low'
        elif cost_score <= 2.5:
            return 'moderate'
        elif cost_score <= 3.5:
            return 'high'
        else:
            return 'very_high'
    
    def _identify_business_benefits(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> List[str]:
        """Identify business benefits for the recommended strategy."""
        benefits = {
            SixRStrategy.REHOST: [
                'Fastest time to cloud migration',
                'Immediate infrastructure cost savings',
                'Minimal business disruption',
                'Quick realization of cloud benefits'
            ],
            SixRStrategy.REPLATFORM: [
                'Improved operational efficiency',
                'Better cloud service integration',
                'Enhanced scalability and reliability',
                'Moderate modernization benefits'
            ],
            SixRStrategy.REFACTOR: [
                'Significant performance improvements',
                'Better cloud-native integration',
                'Reduced technical debt',
                'Enhanced maintainability and agility'
            ],
            SixRStrategy.REARCHITECT: [
                'Maximum cloud-native benefits',
                'Future-proof architecture',
                'Optimal performance and scalability',
                'Strategic competitive advantage'
            ],
            SixRStrategy.REWRITE: [
                'Latest technology adoption',
                'Optimal cloud architecture',
                'No legacy constraints',
                'Maximum innovation potential'
            ],
            SixRStrategy.REPLACE: [
                'Modern SaaS capabilities',
                'Reduced maintenance overhead',
                'Vendor-supported features',
                'Quick access to new functionality'
            ],
            SixRStrategy.RETIRE: [
                'Eliminated maintenance costs',
                'Simplified IT landscape',
                'Reduced security risks',
                'Resource reallocation opportunities'
            ]
        }
        
        base_benefits = benefits.get(strategy, [])
        
        # Add parameter-specific benefits
        if param_values['business_value'] >= 7:
            base_benefits.append('High business value preservation')
        
        if param_values['innovation_priority'] >= 7:
            base_benefits.append('Enhanced innovation capabilities')
        
        if param_values['cost_sensitivity'] >= 7:
            base_benefits.append('Cost optimization opportunities')
        
        return base_benefits[:6]  # Limit to top 6 benefits
    
    def _identify_technical_benefits(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> List[str]:
        """Identify technical benefits for the recommended strategy."""
        benefits = {
            SixRStrategy.REHOST: [
                'Infrastructure modernization',
                'Improved backup and disaster recovery',
                'Better monitoring and management tools'
            ],
            SixRStrategy.REPLATFORM: [
                'Managed service adoption',
                'Improved security posture',
                'Better operational tools',
                'Enhanced monitoring capabilities'
            ],
            SixRStrategy.REFACTOR: [
                'Code modernization',
                'Improved architecture patterns',
                'Better testing and deployment',
                'Enhanced performance optimization'
            ],
            SixRStrategy.REARCHITECT: [
                'Microservices architecture',
                'Container and orchestration adoption',
                'API-first design',
                'Cloud-native patterns implementation'
            ],
            SixRStrategy.REWRITE: [
                'Modern development frameworks',
                'Cloud-native architecture',
                'Serverless computing adoption',
                'Advanced DevOps practices'
            ],
            SixRStrategy.REPLACE: [
                'Modern application architecture',
                'Vendor-managed infrastructure',
                'Automatic updates and patches',
                'Built-in security features'
            ],
            SixRStrategy.RETIRE: [
                'Reduced technical debt',
                'Simplified architecture',
                'Lower security attack surface'
            ]
        }
        
        return benefits.get(strategy, [])
    
    def _calculate_parameter_hash(self, param_values: Dict[str, float]) -> str:
        """Calculate hash of parameters for caching and comparison."""
        import hashlib
        param_str = str(sorted(param_values.items()))
        return hashlib.md5(param_str.encode()).hexdigest()[:8]
    
    def _get_fallback_recommendation(self, parameters: SixRParameterBase) -> Dict[str, Any]:
        """Return fallback recommendation in case of analysis failure."""
        return {
            'recommended_strategy': 'replatform',
            'confidence_score': 0.5,
            'strategy_scores': [
                {
                    'strategy': 'replatform',
                    'score': 6.0,
                    'confidence': 0.5,
                    'rationale': ['Fallback recommendation due to analysis error'],
                    'risk_factors': ['Analysis incomplete'],
                    'benefits': ['Basic cloud migration']
                }
            ],
            'key_factors': ['Analysis error occurred'],
            'assumptions': ['Fallback analysis used'],
            'next_steps': ['Retry analysis with valid parameters'],
            'estimated_effort': 'medium',
            'estimated_timeline': '3-6 months',
            'estimated_cost_impact': 'moderate',
            'risk_factors': ['Analysis incomplete'],
            'business_benefits': ['Basic cloud benefits'],
            'technical_benefits': ['Infrastructure modernization'],
            'analysis_metadata': {
                'engine_version': '1.0',
                'analysis_timestamp': datetime.now().isoformat(),
                'parameter_hash': 'fallback',
                'application_type': parameters.application_type
            }
        }
    
    def _calculate_strategy_score(self, strategy: SixRStrategy, 
                                 parameters: SixRParameterBase,
                                 application_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate score for a specific strategy."""
        
        # Get parameter values
        param_values = {
            "business_value": parameters.business_value,
            "technical_complexity": parameters.technical_complexity,
            "migration_urgency": parameters.migration_urgency,
            "compliance_requirements": parameters.compliance_requirements,
            "cost_sensitivity": parameters.cost_sensitivity,
            "risk_tolerance": parameters.risk_tolerance,
            "innovation_priority": parameters.innovation_priority
        }
        
        # Get strategy weights and scoring rules
        weights = self.strategy_weights[strategy]
        rules = self.scoring_rules[strategy]
        
        # Calculate base score using weighted parameters
        base_score = 0.0
        parameter_contributions = {}
        
        for param_name, value in param_values.items():
            weight = weights[param_name]
            optimal_range = rules["optimal_ranges"][param_name]
            
            # Calculate parameter score based on optimal range
            param_score = self._calculate_parameter_score(value, optimal_range)
            weighted_contribution = param_score * weight * 100  # Scale to 0-100
            
            base_score += weighted_contribution
            parameter_contributions[param_name] = {
                "value": value,
                "optimal_range": optimal_range,
                "score": param_score,
                "weight": weight,
                "contribution": weighted_contribution
            }
        
        # Apply application context adjustments
        context_adjustment = 1.0
        context_insights = []
        
        if application_context:
            context_adjustment, context_insights = self._apply_application_context_adjustments(
                strategy, application_context, param_values
            )
        
        # Apply penalty factors
        penalties = self._calculate_penalties(strategy, param_values, rules)
        final_score = base_score * penalties["total_penalty_factor"] * context_adjustment
        
        # Ensure score doesn't exceed 100 (safety cap)
        final_score = min(final_score, 100.0)
        
        # Generate rationale
        rationale = self._generate_rationale(strategy, param_values, parameter_contributions, penalties)
        
        # Add context-based rationale
        if context_insights:
            rationale.extend(context_insights)
        
        # Identify risk factors and benefits
        risk_factors = self._identify_risk_factors(strategy, param_values)
        benefits = self._identify_benefits(strategy, param_values)
        
        # Add context-specific risks and benefits
        if application_context:
            context_risks, context_benefits = self._analyze_context_risks_benefits(strategy, application_context)
            risk_factors.extend(context_risks)
            benefits.extend(context_benefits)
        
        return {
            "strategy": strategy,
            "score": round(final_score, 2),
            "confidence": self._calculate_strategy_confidence(strategy, param_values),
            "rationale": rationale,
            "risk_factors": risk_factors,
            "benefits": benefits,
            "parameter_contributions": parameter_contributions,
            "penalties": penalties,
            "context_adjustment": context_adjustment
        }
    
    def _calculate_parameter_score(self, value: float, optimal_range: Tuple[float, float]) -> float:
        """Calculate score for a parameter based on its optimal range."""
        min_optimal, max_optimal = optimal_range
        
        if min_optimal <= value <= max_optimal:
            # Value is in optimal range
            return 1.0
        elif value < min_optimal:
            # Value is below optimal range
            distance = min_optimal - value
            max_distance = min_optimal - 1.0  # Minimum possible value is 1
            if max_distance == 0:
                return 0.8  # Slight penalty if already at minimum
            penalty = distance / max_distance
            return max(0.0, 1.0 - penalty * 0.5)  # Maximum 50% penalty
        else:
            # Value is above optimal range
            distance = value - max_optimal
            max_distance = 10.0 - max_optimal  # Maximum possible value is 10
            if max_distance == 0:
                return 0.8  # Slight penalty if already at maximum
            penalty = distance / max_distance
            return max(0.0, 1.0 - penalty * 0.5)  # Maximum 50% penalty
    
    def _calculate_penalties(self, strategy: SixRStrategy, param_values: Dict[str, float],
                           rules: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate penalty factors for strategy."""
        penalty_factors = rules.get("penalty_factors", {})
        applied_penalties = {}
        total_penalty_factor = 1.0
        
        # Check each penalty condition
        for penalty_name, penalty_factor in penalty_factors.items():
            if self._check_penalty_condition(penalty_name, param_values):
                applied_penalties[penalty_name] = penalty_factor
                total_penalty_factor *= penalty_factor
        
        return {
            "applied_penalties": applied_penalties,
            "total_penalty_factor": total_penalty_factor,
            "penalty_impact": round((1.0 - total_penalty_factor) * 100, 1)
        }
    
    def _check_penalty_condition(self, penalty_name: str, param_values: Dict[str, float]) -> bool:
        """Check if a penalty condition is met."""
        conditions = {
            "high_complexity": param_values["technical_complexity"] >= 8,
            "very_high_complexity": param_values["technical_complexity"] >= 9,
            "low_urgency": param_values["migration_urgency"] <= 3,
            "very_low_urgency": param_values["migration_urgency"] <= 2,
            "high_urgency": param_values["migration_urgency"] >= 8,
            "high_innovation_need": param_values["innovation_priority"] >= 8,
            "low_innovation_priority": param_values["innovation_priority"] <= 3,
            "very_high_cost_sensitivity": param_values["cost_sensitivity"] >= 9,
            "high_cost_sensitivity": param_values["cost_sensitivity"] >= 8,
            "low_cost_sensitivity": param_values["cost_sensitivity"] <= 3,
            "low_risk_tolerance": param_values["risk_tolerance"] <= 3,
            "high_business_value": param_values["business_value"] >= 8,
            "low_business_value": param_values["business_value"] <= 3,
            "low_complexity": param_values["technical_complexity"] <= 3,
            "low_compliance": param_values["compliance_requirements"] <= 3
        }
        
        return conditions.get(penalty_name, False)
    
    def _calculate_confidence_score(self, strategy_scores: List[Dict[str, Any]], 
                                   parameters: SixRParameterBase) -> float:
        """Calculate overall confidence in the recommendation."""
        if not strategy_scores:
            return 0.0
        
        # Sort scores
        sorted_scores = sorted(strategy_scores, key=lambda x: x["score"], reverse=True)
        top_score = sorted_scores[0]["score"]
        second_score = sorted_scores[1]["score"] if len(sorted_scores) > 1 else 0
        
        # Calculate score separation (higher separation = higher confidence)
        score_separation = (top_score - second_score) / 100.0
        
        # Calculate parameter consistency (less extreme values = higher confidence)
        param_values = [
            parameters.business_value, parameters.technical_complexity,
            parameters.migration_urgency, parameters.compliance_requirements,
            parameters.cost_sensitivity, parameters.risk_tolerance,
            parameters.innovation_priority
        ]
        
        # Calculate standard deviation of parameters (normalized)
        mean_value = sum(param_values) / len(param_values)
        variance = sum((x - mean_value) ** 2 for x in param_values) / len(param_values)
        std_dev = math.sqrt(variance)
        consistency_factor = max(0.0, 1.0 - (std_dev / 5.0))  # Normalize by max possible std dev
        
        # Calculate top score quality
        score_quality = min(1.0, top_score / 80.0)  # Scores above 80 are high quality
        
        # Combine factors
        confidence = (score_separation * 0.4 + consistency_factor * 0.3 + score_quality * 0.3)
        
        return round(min(1.0, max(0.0, confidence)), 3)
    
    def _generate_rationale(self, strategy: SixRStrategy, param_values: Dict[str, float],
                           parameter_contributions: Dict[str, Any], 
                           penalties: Dict[str, Any]) -> List[str]:
        """Generate rationale for strategy recommendation."""
        rationale = []
        
        # Strategy-specific rationale
        strategy_rationales = {
            SixRStrategy.REHOST: [
                "Lift-and-shift approach minimizes changes and reduces migration risk",
                "Quick migration timeline with minimal application modifications",
                "Cost-effective for applications with high migration urgency"
            ],
            SixRStrategy.REPLATFORM: [
                "Balanced approach with moderate cloud optimization",
                "Leverages some cloud-native services while maintaining core architecture",
                "Good compromise between speed and cloud benefits"
            ],
            SixRStrategy.REFACTOR: [
                "Significant code changes to optimize for cloud-native architecture",
                "Improves application performance and scalability",
                "Requires substantial development effort but delivers long-term benefits"
            ],
            SixRStrategy.REARCHITECT: [
                "Complete redesign using cloud-native patterns and services",
                "Maximizes cloud benefits and innovation opportunities",
                "Highest effort but delivers transformational business value"
            ],
            SixRStrategy.RETIRE: [
                "Application provides minimal business value",
                "High complexity makes migration cost-prohibitive",
                "Decommissioning reduces technical debt and operational costs"
            ],
            SixRStrategy.REWRITE: [
                "Complete rebuild using cloud-native services and functions",
                "Maximizes innovation and modernization opportunities",
                "Delivers transformational business capabilities and scalability"
            ],
            SixRStrategy.REPLACE: [
                "Replace COTS application with cloud-native alternative or SaaS solution",
                "Eliminates licensing and maintenance overhead of legacy COTS",
                "Leverages modern SaaS capabilities and cloud-native features"
            ]
        }
        
        rationale.extend(strategy_rationales.get(strategy, []))
        
        # Add parameter-specific rationale
        top_contributors = sorted(
            parameter_contributions.items(),
            key=lambda x: x[1]["contribution"],
            reverse=True
        )[:3]
        
        for param_name, contrib in top_contributors:
            if contrib["contribution"] > 10:  # Significant contribution
                rationale.append(
                    f"{param_name.replace('_', ' ').title()} score of {contrib['value']} "
                    f"strongly supports this strategy"
                )
        
        # Add penalty rationale
        if penalties["applied_penalties"]:
            penalty_names = list(penalties["applied_penalties"].keys())
            rationale.append(
                f"Score reduced by {penalties['penalty_impact']}% due to: "
                f"{', '.join(penalty_names)}"
            )
        
        return rationale
    
    def _identify_risk_factors(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> List[str]:
        """Identify risk factors for the strategy."""
        risk_factors = []
        
        # Common risk factors based on parameters
        if param_values["technical_complexity"] >= 8:
            risk_factors.append("High technical complexity increases implementation risk")
        
        if param_values["migration_urgency"] >= 8 and strategy in [SixRStrategy.REFACTOR, SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
            risk_factors.append("Tight timeline conflicts with extensive development requirements")
        
        if param_values["risk_tolerance"] <= 3 and strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REFACTOR, SixRStrategy.REWRITE]:
            risk_factors.append("Low risk tolerance conflicts with transformational approach")
        
        if param_values["cost_sensitivity"] >= 8 and strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REFACTOR, SixRStrategy.REWRITE]:
            risk_factors.append("High cost sensitivity may conflict with development investment")
        
        # Strategy-specific risks
        strategy_risks = {
            SixRStrategy.REHOST: [
                "Limited cloud optimization may result in higher operational costs",
                "Technical debt carried forward to cloud environment"
            ],
            SixRStrategy.REPLATFORM: [
                "Partial optimization may not deliver expected cloud benefits",
                "Integration complexity with cloud services"
            ],
            SixRStrategy.REFACTOR: [
                "Significant development effort and timeline risk",
                "Potential for scope creep and budget overruns"
            ],
            SixRStrategy.REARCHITECT: [
                "Highest complexity and longest timeline",
                "Risk of over-engineering and feature creep"
            ],
            SixRStrategy.RETIRE: [
                "Data migration and archival requirements",
                "Potential business disruption during decommissioning"
            ],
            SixRStrategy.REWRITE: [
                "Highest complexity and longest development timeline",
                "Risk of over-engineering with cloud-native services",
                "Significant learning curve for serverless and cloud-native patterns"
            ]
        }
        
        risk_factors.extend(strategy_risks.get(strategy, []))
        
        return risk_factors
    
    def _identify_benefits(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> List[str]:
        """Identify benefits of the strategy."""
        benefits = []
        
        # Strategy-specific benefits
        strategy_benefits = {
            SixRStrategy.REHOST: [
                "Fastest migration approach with minimal risk",
                "Immediate cloud infrastructure benefits",
                "Lower upfront development costs"
            ],
            SixRStrategy.REPLATFORM: [
                "Moderate cloud optimization with manageable effort",
                "Improved scalability and performance",
                "Balanced cost-benefit ratio"
            ],
            SixRStrategy.REFACTOR: [
                "Significant performance and scalability improvements",
                "Better cloud cost optimization",
                "Enhanced maintainability and developer productivity"
            ],
            SixRStrategy.REARCHITECT: [
                "Maximum cloud-native benefits and innovation",
                "Transformational business capabilities",
                "Future-proof architecture and technology stack"
            ],
            SixRStrategy.RETIRE: [
                "Eliminates maintenance costs and technical debt",
                "Reduces security and compliance risks",
                "Frees up resources for strategic initiatives"
            ],
            SixRStrategy.REWRITE: [
                "Maximum cloud-native benefits and serverless capabilities",
                "Optimal performance, scalability, and cost efficiency",
                "Future-proof architecture with latest technologies and patterns"
            ],
            SixRStrategy.REPLACE: [
                "Modern SaaS solution with built-in cloud capabilities",
                "Reduced operational overhead and maintenance burden",
                "Access to vendor innovation and feature updates",
                "Improved security and compliance through managed services"
            ]
        }
        
        benefits.extend(strategy_benefits.get(strategy, []))
        
        return benefits
    
    def _calculate_strategy_confidence(self, strategy: SixRStrategy, param_values: Dict[str, float]) -> float:
        """Calculate confidence for individual strategy."""
        # This is a simplified confidence calculation
        # In practice, this could be more sophisticated
        return 0.8  # Placeholder
    
    def _identify_key_factors(self, parameters: SixRParameterBase, 
                             strategy_scores: List[Dict[str, Any]]) -> List[str]:
        """Identify key decision factors."""
        key_factors = []
        
        # Identify parameters with extreme values
        param_values = {
            "business_value": parameters.business_value,
            "technical_complexity": parameters.technical_complexity,
            "migration_urgency": parameters.migration_urgency,
            "compliance_requirements": parameters.compliance_requirements,
            "cost_sensitivity": parameters.cost_sensitivity,
            "risk_tolerance": parameters.risk_tolerance,
            "innovation_priority": parameters.innovation_priority
        }
        
        for param_name, value in param_values.items():
            if value >= 8:
                key_factors.append(f"High {param_name.replace('_', ' ')}")
            elif value <= 2:
                key_factors.append(f"Low {param_name.replace('_', ' ')}")
        
        # Add score-based factors
        top_strategy = strategy_scores[0]
        if top_strategy["score"] >= 80:
            key_factors.append("Strong alignment with strategy parameters")
        elif top_strategy["score"] <= 50:
            key_factors.append("Weak parameter alignment requires careful consideration")
        
        return key_factors
    
    def _generate_assumptions(self, parameters: SixRParameterBase,
                            application_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate analysis assumptions."""
        assumptions = [
            "Parameter values accurately reflect organizational priorities",
            "Application architecture and dependencies are well understood",
            "Cloud target environment capabilities are suitable for the application",
            "Organizational change management capabilities support the chosen strategy"
        ]
        
        # Add context-specific assumptions
        if application_context:
            if application_context.get("has_dependencies"):
                assumptions.append("Application dependencies can be migrated or maintained")
            
            if application_context.get("compliance_sensitive"):
                assumptions.append("Compliance requirements can be met in target environment")
        
        return assumptions
    
    def _generate_next_steps(self, strategy: SixRStrategy, parameters: SixRParameterBase) -> List[str]:
        """Generate recommended next steps."""
        next_steps = []
        
        # Strategy-specific next steps
        strategy_steps = {
            SixRStrategy.REHOST: [
                "Conduct infrastructure sizing and capacity planning",
                "Identify and resolve cloud compatibility issues",
                "Plan migration timeline and cutover strategy"
            ],
            SixRStrategy.REPLATFORM: [
                "Identify cloud services for optimization opportunities",
                "Assess application architecture for platform changes",
                "Develop migration and testing strategy"
            ],
            SixRStrategy.REFACTOR: [
                "Conduct detailed code analysis and refactoring assessment",
                "Design cloud-optimized architecture",
                "Establish development team and timeline"
            ],
            SixRStrategy.REARCHITECT: [
                "Engage architecture team for cloud-native design",
                "Conduct business requirements analysis",
                "Develop comprehensive project plan and timeline"
            ],
            SixRStrategy.RETIRE: [
                "Identify data retention and archival requirements",
                "Plan user migration to alternative solutions",
                "Develop decommissioning timeline and process"
            ],
            SixRStrategy.REWRITE: [
                "Engage cloud-native architecture specialists",
                "Conduct comprehensive requirements analysis for serverless design",
                "Develop detailed project plan with phased delivery approach"
            ]
        }
        
        next_steps.extend(strategy_steps.get(strategy, []))
        
        # Add parameter-specific steps
        if parameters.compliance_requirements >= 7:
            next_steps.append("Conduct detailed compliance assessment for target environment")
        
        if parameters.technical_complexity >= 8:
            next_steps.append("Engage technical specialists for complexity assessment")
        
        return next_steps
    
    def _validate_parameters(self, parameters: SixRParameterBase) -> List[str]:
        """Validate parameter values and return any issues."""
        issues = []
        
        param_values = {
            "business_value": parameters.business_value,
            "technical_complexity": parameters.technical_complexity,
            "migration_urgency": parameters.migration_urgency,
            "compliance_requirements": parameters.compliance_requirements,
            "cost_sensitivity": parameters.cost_sensitivity,
            "risk_tolerance": parameters.risk_tolerance,
            "innovation_priority": parameters.innovation_priority
        }
        
        for param_name, value in param_values.items():
            if not isinstance(value, (int, float)):
                issues.append(f"{param_name} must be a number")
            elif not 1.0 <= value <= 10.0:
                issues.append(f"{param_name} must be between 1.0 and 10.0")
        
        return issues
    
    def update_strategy_weights(self, strategy: SixRStrategy, weights: Dict[str, float]) -> None:
        """Update strategy-specific parameter weights."""
        if sum(weights.values()) != 1.0:
            raise ValueError("Weights must sum to 1.0")
        
        self.strategy_weights[strategy] = weights
        logger.info(f"Updated weights for strategy {strategy}")
    
    def add_assumption(self, assumption: str) -> None:
        """Add an assumption to the analysis."""
        self.assumptions.append({
            "assumption": assumption,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get current engine status and configuration."""
        return {
            "strategies_configured": len(self.strategy_weights),
            "total_assumptions": len(self.assumptions),
            "last_updated": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
    
    def _apply_application_context_adjustments(self, strategy: SixRStrategy, 
                                             context: Dict[str, Any], 
                                             param_values: Dict[str, float]) -> Tuple[float, List[str]]:
        """Apply application context-based adjustments to strategy scores."""
        adjustment_factor = 1.0
        insights = []
        
        # Technology stack analysis
        tech_stack = context.get('technology_stack', [])
        if tech_stack:
            tech_adjustment, tech_insights = self._analyze_technology_stack(strategy, tech_stack)
            adjustment_factor *= tech_adjustment
            insights.extend(tech_insights)
        
        # Infrastructure analysis
        infra_adjustment, infra_insights = self._analyze_infrastructure(strategy, context)
        adjustment_factor *= infra_adjustment
        insights.extend(infra_insights)
        
        # Dependencies analysis
        deps_adjustment, deps_insights = self._analyze_dependencies(strategy, context)
        adjustment_factor *= deps_adjustment
        insights.extend(deps_insights)
        
        # Criticality analysis
        crit_adjustment, crit_insights = self._analyze_criticality(strategy, context)
        adjustment_factor *= crit_adjustment
        insights.extend(crit_insights)
        
        # Environment analysis
        env_adjustment, env_insights = self._analyze_environment(strategy, context)
        adjustment_factor *= env_adjustment
        insights.extend(env_insights)
        
        return adjustment_factor, insights
    
    def _analyze_technology_stack(self, strategy: SixRStrategy, tech_stack: List[str]) -> Tuple[float, List[str]]:
        """Analyze technology stack compatibility with migration strategy."""
        adjustment = 1.0
        insights = []
        
        # Modern cloud-native technologies favor advanced strategies
        modern_technologies = {
            'Docker', 'Kubernetes', 'Node.js', 'React', 'Angular', 'Vue.js',
            'Spring Boot', 'Microservices', 'REST', 'GraphQL', 'MongoDB', 'Redis',
            'Elasticsearch', 'Kafka', 'RabbitMQ', 'Python', 'Go', 'Rust'
        }
        
        # Legacy technologies favor simpler strategies
        legacy_technologies = {
            'COBOL', 'Fortran', 'Visual Basic', 'ASP Classic', 'Cold Fusion',
            'Perl', 'PHP 5', 'Oracle Forms', 'PowerBuilder', 'Delphi',
            'VB6', 'Access', 'FoxPro'
        }
        
        tech_stack_str = ' '.join(tech_stack).upper()
        modern_count = sum(1 for tech in modern_technologies if tech.upper() in tech_stack_str)
        legacy_count = sum(1 for tech in legacy_technologies if tech.upper() in tech_stack_str)
        
        if strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
            if modern_count > 0:
                adjustment *= 1.2
                insights.append(f"Modern technology stack ({', '.join(tech_stack[:3])}) well-suited for {strategy.value}")
            if legacy_count > 0:
                adjustment *= 0.8
                insights.append(f"Legacy technologies may require significant effort for {strategy.value}")
        
        elif strategy in [SixRStrategy.REHOST, SixRStrategy.RETIRE]:
            if legacy_count > 0:
                adjustment *= 1.1
                insights.append(f"Legacy technology stack supports {strategy.value} approach")
        
        elif strategy == SixRStrategy.REPLATFORM:
            if modern_count > 0 and legacy_count == 0:
                adjustment *= 1.1
                insights.append(f"Technology stack enables effective platform optimization")
        
        return adjustment, insights
    
    def _analyze_infrastructure(self, strategy: SixRStrategy, context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze infrastructure characteristics."""
        adjustment = 1.0
        insights = []
        
        # Resource analysis
        cpu_cores = context.get('cpu_cores', 0)
        memory_gb = context.get('memory_gb', 0)
        storage_gb = context.get('storage_gb', 0)
        
        # High-resource applications
        if cpu_cores >= 8 or memory_gb >= 32 or storage_gb >= 1000:
            if strategy in [SixRStrategy.REHOST, SixRStrategy.REPLATFORM]:
                adjustment *= 1.1
                insights.append(f"High-resource application ({cpu_cores}CPU, {memory_gb}GB RAM) suitable for cloud lift-and-shift")
            elif strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                adjustment *= 1.2
                insights.append(f"Resource-intensive application would benefit from cloud-native optimization")
        
        # Low-resource applications
        elif cpu_cores <= 2 and memory_gb <= 4:
            if strategy == SixRStrategy.RETIRE:
                adjustment *= 1.3
                insights.append("Low-resource utilization suggests potential for retirement")
            elif strategy in [SixRStrategy.REHOST, SixRStrategy.REPLATFORM]:
                adjustment *= 0.9
                insights.append("Low-resource application may not justify cloud migration costs")
        
        return adjustment, insights
    
    def _analyze_dependencies(self, strategy: SixRStrategy, context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze application dependencies."""
        adjustment = 1.0
        insights = []
        
        network_deps = context.get('network_dependencies', [])
        db_deps = context.get('database_dependencies', [])
        external_deps = context.get('external_integrations', [])
        
        total_dependencies = len(network_deps) + len(db_deps) + len(external_deps)
        
        if total_dependencies >= 5:
            if strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                adjustment *= 0.7
                insights.append(f"High dependency count ({total_dependencies}) increases complexity for complete redesign")
            elif strategy == SixRStrategy.REHOST:
                adjustment *= 1.2
                insights.append(f"Complex dependencies ({total_dependencies}) favor lift-and-shift approach")
        
        elif total_dependencies <= 1:
            if strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                adjustment *= 1.3
                insights.append("Low dependency count enables flexible modernization approaches")
            elif strategy == SixRStrategy.RETIRE:
                adjustment *= 1.2
                insights.append("Minimal dependencies reduce retirement complexity")
        
        return adjustment, insights
    
    def _analyze_criticality(self, strategy: SixRStrategy, context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze business criticality."""
        adjustment = 1.0
        insights = []
        
        criticality = context.get('criticality', 'medium').lower()
        environment = context.get('environment', 'production').lower()
        
        if criticality in ['high', 'critical'] or environment == 'production':
            if strategy == SixRStrategy.RETIRE:
                adjustment *= 0.3
                insights.append("High criticality application not suitable for retirement")
            elif strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                adjustment *= 0.8
                insights.append("High criticality requires careful approach to avoid business disruption")
            elif strategy in [SixRStrategy.REHOST, SixRStrategy.REPLATFORM]:
                adjustment *= 1.2
                insights.append("High criticality supports lower-risk migration strategies")
        
        elif criticality in ['low', 'non-critical']:
            if strategy == SixRStrategy.RETIRE:
                adjustment *= 1.5
                insights.append("Low criticality application candidate for retirement")
            elif strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                adjustment *= 1.1
                insights.append("Low criticality allows for experimental modernization approaches")
        
        return adjustment, insights
    
    def _analyze_environment(self, strategy: SixRStrategy, context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze deployment environment characteristics."""
        adjustment = 1.0
        insights = []
        
        environment = context.get('environment', 'production').lower()
        location = context.get('location', 'unknown').lower()
        
        if environment in ['development', 'test', 'staging']:
            if strategy == SixRStrategy.RETIRE:
                adjustment *= 1.4
                insights.append(f"Non-production environment ({environment}) suitable for retirement")
            elif strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                adjustment *= 1.2
                insights.append(f"Non-production environment allows for experimental approaches")
        
        if 'cloud' in location or 'aws' in location or 'azure' in location:
            if strategy in [SixRStrategy.REPLATFORM, SixRStrategy.REARCHITECT]:
                adjustment *= 1.3
                insights.append("Existing cloud deployment enables advanced cloud strategies")
        
        return adjustment, insights
    
    def _analyze_context_risks_benefits(self, strategy: SixRStrategy, 
                                      context: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Analyze context-specific risks and benefits."""
        risks = []
        benefits = []
        
        # Technology-specific risks/benefits
        tech_stack = context.get('technology_stack', [])
        if 'database' in ' '.join(tech_stack).lower():
            if strategy in [SixRStrategy.REARCHITECT, SixRStrategy.REWRITE]:
                risks.append("Database migration complexity may impact timeline")
                benefits.append("Opportunity to modernize data architecture")
        
        # Infrastructure-specific considerations
        if context.get('cpu_cores', 0) >= 16:
            if strategy in [SixRStrategy.REHOST, SixRStrategy.REPLATFORM]:
                benefits.append("High-performance infrastructure maps well to cloud instances")
        
        # Dependency-specific considerations
        external_deps = context.get('external_integrations', [])
        if len(external_deps) > 3:
            risks.append("Multiple external integrations require careful migration planning")
        
        return risks, benefits 