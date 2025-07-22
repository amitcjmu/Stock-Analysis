"""
Six R Decision Engine - Determines optimal 6R strategy for components

This module contains the SixRDecisionEngine class which analyzes components
to determine the optimal 6R migration strategy based on multiple factors including
technology stack, technical debt, cloud readiness, and complexity.
"""

import json
import logging
from typing import Any, Dict, List, Tuple

from app.models.assessment_flow_state import ComponentType, SixRStrategy, TechDebtSeverity

logger = logging.getLogger(__name__)


class SixRDecisionEngine:
    """
    Determines optimal 6R strategy for components based on multiple factors.
    
    Decision factors include:
    - Technology stack modernity and support status
    - Tech debt severity and accumulated issues
    - Architecture complexity and dependencies
    - Business value and criticality
    - Cloud readiness and modernization potential
    """
    
    def __init__(self):
        self.name = "sixr_decision_engine"
        self.description = "Analyzes components to determine optimal 6R migration strategy"
        logger.info("Initialized SixRDecisionEngine")
    
    def _run(self, component_data: Dict[str, Any], tech_debt_items: List[Dict[str, Any]], 
             architecture_standards: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze component and determine optimal 6R strategy.
        
        Args:
            component_data: Component details including type, technology stack
            tech_debt_items: List of tech debt items for the component
            architecture_standards: Engagement-level architecture requirements
            
        Returns:
            Dict with recommended strategy, confidence, and rationale
        """
        try:
            # Extract component details
            component_type = component_data.get("component_type", "unknown")
            tech_stack = component_data.get("technology_stack", {})
            dependencies = component_data.get("dependencies", [])
            
            # Calculate tech debt score
            tech_debt_score = self._calculate_tech_debt_score(tech_debt_items)
            
            # Assess technology currency
            tech_currency_score = self._assess_technology_currency(tech_stack, architecture_standards)
            
            # Determine cloud readiness
            cloud_readiness_score = self._assess_cloud_readiness(tech_stack, component_type)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(dependencies, tech_stack)
            
            # Determine strategy based on scores
            strategy, confidence = self._determine_strategy(
                tech_debt_score, tech_currency_score, cloud_readiness_score, 
                complexity_score, component_type
            )
            
            # Generate detailed rationale
            rationale = self._generate_rationale(
                strategy, tech_debt_score, tech_currency_score, 
                cloud_readiness_score, complexity_score, tech_debt_items
            )
            
            return {
                "recommended_strategy": strategy.value,
                "confidence_score": confidence,
                "rationale": rationale,
                "decision_factors": {
                    "tech_debt_score": tech_debt_score,
                    "tech_currency_score": tech_currency_score,
                    "cloud_readiness_score": cloud_readiness_score,
                    "complexity_score": complexity_score
                },
                "risk_factors": self._identify_risk_factors(tech_debt_items, tech_stack),
                "modernization_benefits": self._calculate_modernization_benefits(strategy)
            }
            
        except Exception as e:
            logger.error(f"Error in SixRDecisionEngine: {str(e)}")
            return {
                "recommended_strategy": SixRStrategy.RETAIN.value,
                "confidence_score": 0.3,
                "rationale": f"Error during analysis: {str(e)}. Defaulting to retain strategy.",
                "error": str(e)
            }
    
    def _calculate_tech_debt_score(self, tech_debt_items: List[Dict[str, Any]]) -> float:
        """Calculate aggregate tech debt score (0-100, higher is worse)"""
        if not tech_debt_items:
            return 0.0
        
        severity_weights = {
            TechDebtSeverity.CRITICAL.value: 10.0,
            TechDebtSeverity.HIGH.value: 7.0,
            TechDebtSeverity.MEDIUM.value: 4.0,
            TechDebtSeverity.LOW.value: 1.0
        }
        
        total_score = 0.0
        for item in tech_debt_items:
            severity = item.get("severity", TechDebtSeverity.LOW.value)
            weight = severity_weights.get(severity, 1.0)
            impact_score = item.get("tech_debt_score", 5.0)
            total_score += weight * (impact_score / 10.0)
        
        # Normalize to 0-100 scale
        return min(100.0, total_score * 10)
    
    def _assess_technology_currency(self, tech_stack: Dict[str, Any], 
                                  architecture_standards: Dict[str, Any]) -> float:
        """Assess how current the technology stack is (0-100, higher is better)"""
        if not tech_stack:
            return 50.0  # Default middle score
        
        current_score = 100.0
        outdated_penalties = {
            "eol": 40.0,  # End of life
            "deprecated": 30.0,  # Deprecated
            "legacy": 25.0,  # Legacy
            "outdated": 20.0,  # Outdated version
            "unsupported": 35.0  # No longer supported
        }
        
        for tech, details in tech_stack.items():
            if isinstance(details, dict):
                version = details.get("version", "")
                status = details.get("status", "").lower()
                
                for penalty_key, penalty_value in outdated_penalties.items():
                    if penalty_key in status or penalty_key in str(version).lower():
                        current_score -= penalty_value
                        break
        
        return max(0.0, current_score)
    
    def _assess_cloud_readiness(self, tech_stack: Dict[str, Any], component_type: str) -> float:
        """Assess cloud readiness (0-100, higher is better)"""
        base_score = 50.0
        
        # Cloud-friendly technologies
        cloud_friendly = {
            "docker": 15.0, "kubernetes": 20.0, "containerized": 15.0,
            "microservices": 15.0, "rest": 10.0, "api": 10.0,
            "stateless": 15.0, "cloud": 10.0, "serverless": 20.0
        }
        
        # Cloud-unfriendly patterns
        cloud_unfriendly = {
            "monolithic": -20.0, "stateful": -15.0, "file-based": -10.0,
            "com+": -25.0, "activex": -25.0, "desktop": -20.0,
            "thick-client": -20.0, "mainframe": -30.0
        }
        
        tech_string = json.dumps(tech_stack).lower()
        
        for pattern, score_delta in cloud_friendly.items():
            if pattern in tech_string:
                base_score += score_delta
        
        for pattern, score_delta in cloud_unfriendly.items():
            if pattern in tech_string:
                base_score += score_delta
        
        # Component type adjustments
        if component_type == ComponentType.DATABASE.value:
            base_score -= 10.0  # Databases are harder to migrate
        elif component_type == ComponentType.API.value:
            base_score += 10.0  # APIs are easier to modernize
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_complexity_score(self, dependencies: List[str], 
                                  tech_stack: Dict[str, Any]) -> float:
        """Calculate complexity score (0-100, higher is more complex)"""
        base_complexity = 20.0
        
        # Dependency complexity
        base_complexity += len(dependencies) * 5.0
        
        # Technology diversity complexity
        tech_count = len(tech_stack)
        base_complexity += tech_count * 3.0
        
        # Integration complexity indicators
        complex_patterns = ["integration", "etl", "batch", "messaging", "workflow"]
        tech_string = json.dumps(tech_stack).lower()
        
        for pattern in complex_patterns:
            if pattern in tech_string:
                base_complexity += 10.0
        
        return min(100.0, base_complexity)
    
    def _determine_strategy(self, tech_debt_score: float, tech_currency_score: float,
                          cloud_readiness_score: float, complexity_score: float,
                          component_type: str) -> Tuple[SixRStrategy, float]:
        """
        Determine optimal strategy based on scores.
        
        Decision matrix:
        - REWRITE: High tech debt (>80), low currency (<20), high complexity (>80)
        - REARCHITECT: High tech debt (>60), medium currency (20-50), high complexity (>60)
        - REFACTOR: Medium tech debt (40-60), good currency (>50), medium complexity
        - REPLATFORM: Low tech debt (<40), good currency, good cloud readiness
        - REHOST: Low tech debt, any currency, low complexity, lift-and-shift ready
        - RETAIN: Very low tech debt (<20), current tech, low business value
        """
        
        # Calculate composite scores
        modernization_need = (tech_debt_score + (100 - tech_currency_score)) / 2
        migration_difficulty = (complexity_score + (100 - cloud_readiness_score)) / 2
        
        confidence = 0.8  # Base confidence
        
        # Decision logic
        if modernization_need > 80:
            # High modernization need
            if migration_difficulty > 70:
                strategy = SixRStrategy.REWRITE
                confidence = 0.9
            else:
                strategy = SixRStrategy.REARCHITECT
                confidence = 0.85
        elif modernization_need > 60:
            # Medium modernization need
            if cloud_readiness_score > 70:
                strategy = SixRStrategy.REFACTOR
                confidence = 0.8
            else:
                strategy = SixRStrategy.REARCHITECT
                confidence = 0.75
        elif modernization_need > 40:
            # Some modernization needed
            if cloud_readiness_score > 60:
                strategy = SixRStrategy.REPLATFORM
                confidence = 0.8
            else:
                strategy = SixRStrategy.REFACTOR
                confidence = 0.75
        elif cloud_readiness_score > 70 and complexity_score < 40:
            # Good candidate for lift-and-shift
            strategy = SixRStrategy.REHOST
            confidence = 0.85
        else:
            # Low modernization need
            if tech_currency_score > 80:
                strategy = SixRStrategy.RETAIN
                confidence = 0.9
            else:
                strategy = SixRStrategy.REPLATFORM
                confidence = 0.7
        
        # Adjust confidence based on data quality
        if tech_debt_score == 0 or tech_currency_score == 50:
            confidence *= 0.8  # Reduce confidence for default values
        
        return strategy, confidence
    
    def _generate_rationale(self, strategy: SixRStrategy, tech_debt_score: float,
                          tech_currency_score: float, cloud_readiness_score: float,
                          complexity_score: float, tech_debt_items: List[Dict[str, Any]]) -> str:
        """Generate human-readable rationale for the decision"""
        
        rationale_parts = []
        
        # Strategy-specific explanation
        strategy_explanations = {
            SixRStrategy.REWRITE: "Complete rewrite recommended due to significant technical debt and outdated technology stack",
            SixRStrategy.REARCHITECT: "Re-architecture needed to address design issues and enable cloud-native capabilities",
            SixRStrategy.REFACTOR: "Refactoring will modernize the codebase while preserving core functionality",
            SixRStrategy.REPLATFORM: "Platform change recommended to leverage cloud capabilities with minimal code changes",
            SixRStrategy.REHOST: "Lift-and-shift migration is suitable given the application's current state",
            SixRStrategy.RETAIN: "Retention recommended as the application is modern and well-maintained",
            SixRStrategy.RETIRE: "Application should be retired and functionality replaced or eliminated",
            SixRStrategy.REPURCHASE: "Replace with SaaS solution for better functionality and lower maintenance"
        }
        
        rationale_parts.append(strategy_explanations.get(strategy, "Strategy selected based on analysis"))
        
        # Add score-based reasoning
        if tech_debt_score > 70:
            rationale_parts.append(f"High technical debt score ({tech_debt_score:.1f}/100) indicates significant accumulated issues")
        elif tech_debt_score < 30:
            rationale_parts.append(f"Low technical debt score ({tech_debt_score:.1f}/100) shows good maintenance")
        
        if tech_currency_score < 30:
            rationale_parts.append(f"Technology currency score ({tech_currency_score:.1f}/100) indicates outdated stack")
        elif tech_currency_score > 70:
            rationale_parts.append(f"Modern technology stack ({tech_currency_score:.1f}/100) supports current standards")
        
        if cloud_readiness_score > 70:
            rationale_parts.append(f"High cloud readiness ({cloud_readiness_score:.1f}/100) enables easier migration")
        elif cloud_readiness_score < 30:
            rationale_parts.append(f"Low cloud readiness ({cloud_readiness_score:.1f}/100) requires significant changes")
        
        if complexity_score > 70:
            rationale_parts.append(f"High complexity ({complexity_score:.1f}/100) increases migration risk")
        
        # Add specific tech debt callouts
        critical_items = [item for item in tech_debt_items 
                         if item.get("severity") == TechDebtSeverity.CRITICAL.value]
        if critical_items:
            rationale_parts.append(f"{len(critical_items)} critical issues require immediate attention")
        
        return ". ".join(rationale_parts) + "."
    
    def _identify_risk_factors(self, tech_debt_items: List[Dict[str, Any]], 
                             tech_stack: Dict[str, Any]) -> List[str]:
        """Identify key risk factors for migration"""
        risk_factors = []
        
        # Tech debt risks
        critical_count = sum(1 for item in tech_debt_items 
                           if item.get("severity") == TechDebtSeverity.CRITICAL.value)
        if critical_count > 0:
            risk_factors.append(f"{critical_count} critical technical debt items")
        
        # Technology risks
        tech_string = json.dumps(tech_stack).lower()
        risk_keywords = {
            "eol": "End-of-life technologies in use",
            "deprecated": "Deprecated technologies present",
            "unsupported": "Unsupported technology versions",
            "legacy": "Legacy systems integration required",
            "mainframe": "Mainframe dependencies exist",
            "proprietary": "Proprietary technology lock-in"
        }
        
        for keyword, risk_description in risk_keywords.items():
            if keyword in tech_string:
                risk_factors.append(risk_description)
        
        # Complexity risks
        dependencies = tech_stack.get("dependencies", [])
        if len(dependencies) > 10:
            risk_factors.append(f"High dependency count ({len(dependencies)})")
        
        return risk_factors
    
    def _calculate_modernization_benefits(self, strategy: SixRStrategy) -> List[str]:
        """Calculate expected benefits from the chosen strategy"""
        
        benefits_map = {
            SixRStrategy.REWRITE: [
                "Complete technology stack modernization",
                "Opportunity to implement best practices from scratch",
                "Elimination of all technical debt",
                "Full cloud-native architecture"
            ],
            SixRStrategy.REARCHITECT: [
                "Improved scalability and performance",
                "Cloud-native design patterns",
                "Microservices architecture enablement",
                "Enhanced maintainability"
            ],
            SixRStrategy.REFACTOR: [
                "Code quality improvements",
                "Performance optimizations",
                "Security enhancements",
                "Improved testability"
            ],
            SixRStrategy.REPLATFORM: [
                "Cloud platform benefits (auto-scaling, managed services)",
                "Reduced infrastructure management",
                "Improved deployment flexibility",
                "Cost optimization opportunities"
            ],
            SixRStrategy.REHOST: [
                "Quick migration timeline",
                "Minimal business disruption",
                "Immediate cloud cost benefits",
                "Foundation for future modernization"
            ],
            SixRStrategy.RETAIN: [
                "No migration risk",
                "Continued stability",
                "No retraining required",
                "Focus resources on other priorities"
            ]
        }
        
        return benefits_map.get(strategy, ["Benefits specific to chosen strategy"])