"""
Six R Strategy Tools - CrewAI Tool Implementations

These tools support the Six R Strategy Crew in determining optimal migration strategies
for applications and their components, validating compatibility, and generating move groups.

Key Tools:
1. SixRDecisionEngine - Determines optimal 6R strategy for components
2. CompatibilityChecker - Validates treatment compatibility between components  
3. BusinessValueCalculator - Assesses business impact and value
4. MoveGroupAnalyzer - Identifies move group hints for planning
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from app.models.assessment_flow_state import (
    SixRStrategy, ComponentType, ComponentTreatment,
    TechDebtSeverity, TechDebtItem
)

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


class CompatibilityChecker:
    """
    Validates compatibility between component treatments within an application.
    
    Checks for:
    - Technical compatibility between component strategies
    - Data flow and integration compatibility
    - Timing and sequencing requirements
    - Shared resource conflicts
    """
    
    def __init__(self):
        self.name = "compatibility_checker"
        self.description = "Validates treatment compatibility between related components"
        logger.info("Initialized CompatibilityChecker")
    
    def _run(self, component_treatments: List[Dict[str, Any]], 
             application_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compatibility between component treatments.
        
        Args:
            component_treatments: List of proposed treatments for components
            application_metadata: Application details and architecture
            
        Returns:
            Dict with compatibility validation results
        """
        try:
            # Group treatments by component type
            treatments_by_type = {}
            for treatment in component_treatments:
                comp_type = treatment.get("component_type", "unknown")
                strategy = treatment.get("recommended_strategy", "unknown")
                treatments_by_type[comp_type] = strategy
            
            # Check for incompatibilities
            issues = self._check_treatment_conflicts(treatments_by_type)
            
            # Check data flow compatibility
            data_flow_issues = self._check_data_flow_compatibility(
                component_treatments, application_metadata
            )
            issues.extend(data_flow_issues)
            
            # Check timing requirements
            timing_issues = self._check_timing_requirements(component_treatments)
            issues.extend(timing_issues)
            
            # Generate compatibility score
            compatibility_score = self._calculate_compatibility_score(issues)
            
            # Generate recommendations
            recommendations = self._generate_compatibility_recommendations(
                issues, treatments_by_type
            )
            
            return {
                "compatible": len(issues) == 0,
                "compatibility_score": compatibility_score,
                "issues": issues,
                "recommendations": recommendations,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in CompatibilityChecker: {str(e)}")
            return {
                "compatible": False,
                "compatibility_score": 0.0,
                "issues": [f"Validation error: {str(e)}"],
                "error": str(e)
            }
    
    def _check_treatment_conflicts(self, treatments_by_type: Dict[str, str]) -> List[str]:
        """Check for known incompatible treatment combinations"""
        issues = []
        
        # Define incompatible patterns
        incompatible_patterns = [
            {
                "condition": lambda t: (
                    t.get(ComponentType.FRONTEND.value) == SixRStrategy.REWRITE.value and
                    t.get(ComponentType.BACKEND.value) == SixRStrategy.RETAIN.value
                ),
                "issue": "Frontend rewrite with backend retain may cause API compatibility issues"
            },
            {
                "condition": lambda t: (
                    t.get(ComponentType.DATABASE.value) == SixRStrategy.RETIRE.value and
                    t.get(ComponentType.BACKEND.value) in [SixRStrategy.RETAIN.value, SixRStrategy.REHOST.value]
                ),
                "issue": "Database retirement conflicts with retained backend components"
            },
            {
                "condition": lambda t: (
                    t.get(ComponentType.FRONTEND.value) == SixRStrategy.REHOST.value and
                    t.get(ComponentType.BACKEND.value) == SixRStrategy.REARCHITECT.value
                ),
                "issue": "Rehosted frontend may not support re-architected backend patterns"
            },
            {
                "condition": lambda t: (
                    t.get(ComponentType.API.value) == SixRStrategy.RETIRE.value and
                    any(s == SixRStrategy.RETAIN.value for s in t.values())
                ),
                "issue": "API retirement impacts retained components that depend on it"
            }
        ]
        
        for pattern in incompatible_patterns:
            if pattern["condition"](treatments_by_type):
                issues.append(pattern["issue"])
        
        return issues
    
    def _check_data_flow_compatibility(self, component_treatments: List[Dict[str, Any]],
                                     application_metadata: Dict[str, Any]) -> List[str]:
        """Check if data flow between components remains viable"""
        issues = []
        
        # Extract dependencies
        component_deps = {}
        for treatment in component_treatments:
            comp_name = treatment.get("component_name", "")
            deps = treatment.get("dependencies", [])
            component_deps[comp_name] = deps
        
        # Check if modernized components can still communicate with legacy ones
        for treatment in component_treatments:
            comp_name = treatment.get("component_name", "")
            strategy = treatment.get("recommended_strategy", "")
            
            if strategy in [SixRStrategy.REWRITE.value, SixRStrategy.REARCHITECT.value]:
                # Check dependencies
                for dep in component_deps.get(comp_name, []):
                    dep_treatment = next(
                        (t for t in component_treatments if t.get("component_name") == dep),
                        None
                    )
                    if dep_treatment and dep_treatment.get("recommended_strategy") == SixRStrategy.RETAIN.value:
                        issues.append(
                            f"Modernized component '{comp_name}' depends on retained component '{dep}' - interface compatibility required"
                        )
        
        return issues
    
    def _check_timing_requirements(self, component_treatments: List[Dict[str, Any]]) -> List[str]:
        """Check if migration timing creates conflicts"""
        issues = []
        
        # Count strategies that require significant downtime
        high_impact_strategies = [
            SixRStrategy.REWRITE.value,
            SixRStrategy.REARCHITECT.value,
            SixRStrategy.RETIRE.value
        ]
        
        high_impact_count = sum(
            1 for t in component_treatments
            if t.get("recommended_strategy") in high_impact_strategies
        )
        
        if high_impact_count > len(component_treatments) / 2:
            issues.append(
                f"{high_impact_count} components require major changes - consider phased migration approach"
            )
        
        # Check for database changes with dependent components
        db_components = [
            t for t in component_treatments
            if t.get("component_type") == ComponentType.DATABASE.value
        ]
        
        for db_comp in db_components:
            if db_comp.get("recommended_strategy") != SixRStrategy.RETAIN.value:
                dependent_count = sum(
                    1 for t in component_treatments
                    if db_comp.get("component_name") in t.get("dependencies", [])
                )
                if dependent_count > 2:
                    issues.append(
                        f"Database changes affect {dependent_count} components - requires careful coordination"
                    )
        
        return issues
    
    def _calculate_compatibility_score(self, issues: List[str]) -> float:
        """Calculate overall compatibility score (0-100)"""
        if not issues:
            return 100.0
        
        # Deduct points based on issue severity
        base_score = 100.0
        
        for issue in issues:
            if "conflicts" in issue.lower() or "incompatible" in issue.lower():
                base_score -= 20.0  # Severe issues
            elif "requires" in issue.lower() or "careful" in issue.lower():
                base_score -= 10.0  # Moderate issues
            else:
                base_score -= 5.0   # Minor issues
        
        return max(0.0, base_score)
    
    def _generate_compatibility_recommendations(self, issues: List[str],
                                              treatments_by_type: Dict[str, str]) -> List[str]:
        """Generate recommendations to address compatibility issues"""
        recommendations = []
        
        if not issues:
            recommendations.append("All component treatments are compatible - proceed with confidence")
            return recommendations
        
        # General recommendations based on issue patterns
        if any("interface compatibility" in issue for issue in issues):
            recommendations.append("Implement API versioning and backwards compatibility layers")
            recommendations.append("Consider using API gateways or service mesh for protocol translation")
        
        if any("phased migration" in issue for issue in issues):
            recommendations.append("Develop a phased migration plan with clear milestones")
            recommendations.append("Implement feature flags for gradual rollout")
        
        if any("database changes" in issue for issue in issues):
            recommendations.append("Use database migration tools with rollback capabilities")
            recommendations.append("Consider database replication during transition period")
        
        if any("conflicts" in issue for issue in issues):
            recommendations.append("Review component strategies for alignment")
            recommendations.append("Consider adjusting strategies for better compatibility")
        
        # Strategy-specific recommendations
        if treatments_by_type.get(ComponentType.FRONTEND.value) == SixRStrategy.REWRITE.value:
            recommendations.append("Implement API contracts early in frontend rewrite")
        
        if treatments_by_type.get(ComponentType.DATABASE.value) == SixRStrategy.RETIRE.value:
            recommendations.append("Plan data migration strategy before database retirement")
        
        return recommendations


class BusinessValueCalculator:
    """
    Calculates business value and impact of migration strategies.
    
    Factors include:
    - Business criticality and revenue impact
    - User experience improvements
    - Operational efficiency gains
    - Risk reduction benefits
    - Compliance and security improvements
    """
    
    def __init__(self):
        self.name = "business_value_calculator"
        self.description = "Assesses business impact and value of migration strategies"
        logger.info("Initialized BusinessValueCalculator")
    
    def _run(self, application_metadata: Dict[str, Any], 
             sixr_strategy: str, tech_debt_score: float) -> Dict[str, Any]:
        """
        Calculate business value for a migration strategy.
        
        Args:
            application_metadata: Application business context
            sixr_strategy: Chosen 6R strategy
            tech_debt_score: Current technical debt score
            
        Returns:
            Dict with business value metrics and recommendations
        """
        try:
            # Extract business context
            criticality = application_metadata.get("business_criticality", "medium")
            user_count = application_metadata.get("user_count", 100)
            revenue_impact = application_metadata.get("revenue_impact", "medium")
            compliance_required = application_metadata.get("compliance_required", False)
            
            # Calculate base business value
            base_value = self._calculate_base_value(criticality, user_count, revenue_impact)
            
            # Calculate strategy-specific value
            strategy_value = self._calculate_strategy_value(sixr_strategy, tech_debt_score)
            
            # Calculate risk reduction value
            risk_value = self._calculate_risk_reduction_value(
                tech_debt_score, compliance_required, sixr_strategy
            )
            
            # Calculate operational value
            operational_value = self._calculate_operational_value(sixr_strategy)
            
            # Calculate total business value
            total_value = (base_value + strategy_value + risk_value + operational_value) / 4
            
            # Generate business case elements
            business_case = self._generate_business_case(
                sixr_strategy, total_value, criticality, 
                tech_debt_score, compliance_required
            )
            
            # Calculate ROI metrics
            roi_metrics = self._calculate_roi_metrics(
                sixr_strategy, total_value, tech_debt_score
            )
            
            return {
                "business_value_score": total_value,
                "value_components": {
                    "base_business_value": base_value,
                    "strategy_value": strategy_value,
                    "risk_reduction_value": risk_value,
                    "operational_value": operational_value
                },
                "business_case": business_case,
                "roi_metrics": roi_metrics,
                "priority_recommendation": self._get_priority_recommendation(total_value),
                "value_realization_timeline": self._get_value_timeline(sixr_strategy)
            }
            
        except Exception as e:
            logger.error(f"Error in BusinessValueCalculator: {str(e)}")
            return {
                "business_value_score": 50.0,
                "error": str(e),
                "business_case": ["Unable to calculate business value due to error"]
            }
    
    def _calculate_base_value(self, criticality: str, user_count: int, 
                            revenue_impact: str) -> float:
        """Calculate base business value from application attributes"""
        
        # Criticality scoring
        criticality_scores = {
            "critical": 100.0,
            "high": 80.0,
            "medium": 50.0,
            "low": 20.0
        }
        crit_score = criticality_scores.get(criticality.lower(), 50.0)
        
        # User impact scoring
        if user_count > 10000:
            user_score = 100.0
        elif user_count > 1000:
            user_score = 80.0
        elif user_count > 100:
            user_score = 60.0
        else:
            user_score = 40.0
        
        # Revenue impact scoring
        revenue_scores = {
            "high": 100.0,
            "medium": 60.0,
            "low": 30.0,
            "none": 10.0
        }
        rev_score = revenue_scores.get(revenue_impact.lower(), 50.0)
        
        # Weighted average
        return (crit_score * 0.4 + user_score * 0.3 + rev_score * 0.3)
    
    def _calculate_strategy_value(self, sixr_strategy: str, tech_debt_score: float) -> float:
        """Calculate value specific to the chosen strategy"""
        
        strategy_values = {
            SixRStrategy.REWRITE.value: {
                "base": 90.0,  # High transformation value
                "debt_multiplier": 1.5  # More valuable for high debt
            },
            SixRStrategy.REARCHITECT.value: {
                "base": 80.0,
                "debt_multiplier": 1.3
            },
            SixRStrategy.REFACTOR.value: {
                "base": 70.0,
                "debt_multiplier": 1.2
            },
            SixRStrategy.REPLATFORM.value: {
                "base": 60.0,
                "debt_multiplier": 1.0
            },
            SixRStrategy.REHOST.value: {
                "base": 40.0,
                "debt_multiplier": 0.8
            },
            SixRStrategy.RETAIN.value: {
                "base": 20.0,
                "debt_multiplier": 0.5
            }
        }
        
        strategy_config = strategy_values.get(sixr_strategy, {"base": 50.0, "debt_multiplier": 1.0})
        
        # Adjust value based on technical debt
        debt_factor = (tech_debt_score / 100.0) * strategy_config["debt_multiplier"]
        
        return strategy_config["base"] * (1 + debt_factor * 0.5)
    
    def _calculate_risk_reduction_value(self, tech_debt_score: float, 
                                      compliance_required: bool, 
                                      sixr_strategy: str) -> float:
        """Calculate value from risk reduction"""
        
        base_risk_value = 0.0
        
        # Technical debt risk reduction
        if tech_debt_score > 70:
            if sixr_strategy in [SixRStrategy.REWRITE.value, SixRStrategy.REARCHITECT.value]:
                base_risk_value += 80.0  # Major risk reduction
            elif sixr_strategy == SixRStrategy.REFACTOR.value:
                base_risk_value += 60.0  # Moderate risk reduction
            else:
                base_risk_value += 30.0  # Some risk reduction
        
        # Compliance risk reduction
        if compliance_required:
            if sixr_strategy in [SixRStrategy.REWRITE.value, SixRStrategy.REARCHITECT.value]:
                base_risk_value += 40.0  # Full compliance opportunity
            else:
                base_risk_value += 20.0  # Partial compliance improvement
        
        # Security risk reduction
        modernization_strategies = [
            SixRStrategy.REWRITE.value,
            SixRStrategy.REARCHITECT.value,
            SixRStrategy.REFACTOR.value
        ]
        if sixr_strategy in modernization_strategies:
            base_risk_value += 30.0  # Security improvements
        
        return min(100.0, base_risk_value)
    
    def _calculate_operational_value(self, sixr_strategy: str) -> float:
        """Calculate operational efficiency value"""
        
        operational_values = {
            SixRStrategy.REWRITE.value: 90.0,      # Maximum efficiency gains
            SixRStrategy.REARCHITECT.value: 85.0,  # High efficiency gains
            SixRStrategy.REFACTOR.value: 70.0,     # Good efficiency gains
            SixRStrategy.REPLATFORM.value: 80.0,   # Platform benefits
            SixRStrategy.REHOST.value: 50.0,       # Cloud cost benefits
            SixRStrategy.REPURCHASE.value: 95.0,   # SaaS operational benefits
            SixRStrategy.RETIRE.value: 100.0,      # Eliminate maintenance
            SixRStrategy.RETAIN.value: 10.0        # Minimal gains
        }
        
        return operational_values.get(sixr_strategy, 50.0)
    
    def _generate_business_case(self, sixr_strategy: str, total_value: float,
                              criticality: str, tech_debt_score: float,
                              compliance_required: bool) -> List[str]:
        """Generate business case points"""
        
        business_case = []
        
        # Value-based case
        if total_value > 80:
            business_case.append("High business value justifies migration investment")
        elif total_value > 60:
            business_case.append("Solid business value supports migration effort")
        else:
            business_case.append("Moderate business value - evaluate against other priorities")
        
        # Strategy-specific benefits
        strategy_benefits = {
            SixRStrategy.REWRITE.value: "Complete modernization enables digital transformation",
            SixRStrategy.REARCHITECT.value: "Architecture improvements enable scalability and agility",
            SixRStrategy.REFACTOR.value: "Code improvements reduce maintenance costs",
            SixRStrategy.REPLATFORM.value: "Cloud platform benefits improve operational efficiency",
            SixRStrategy.REHOST.value: "Quick cloud migration provides immediate cost benefits",
            SixRStrategy.RETAIN.value: "Minimal disruption preserves stability"
        }
        
        benefit = strategy_benefits.get(sixr_strategy)
        if benefit:
            business_case.append(benefit)
        
        # Risk mitigation
        if tech_debt_score > 70:
            business_case.append(f"Addresses critical technical debt (score: {tech_debt_score:.1f})")
        
        # Compliance
        if compliance_required:
            business_case.append("Enables compliance with regulatory requirements")
        
        # Criticality
        if criticality.lower() == "critical":
            business_case.append("Critical business application requires modernization for continuity")
        
        return business_case
    
    def _calculate_roi_metrics(self, sixr_strategy: str, total_value: float,
                             tech_debt_score: float) -> Dict[str, Any]:
        """Calculate ROI metrics for the migration"""
        
        # Estimate costs based on strategy
        cost_factors = {
            SixRStrategy.REWRITE.value: 1.0,
            SixRStrategy.REARCHITECT.value: 0.8,
            SixRStrategy.REFACTOR.value: 0.6,
            SixRStrategy.REPLATFORM.value: 0.4,
            SixRStrategy.REHOST.value: 0.2,
            SixRStrategy.RETAIN.value: 0.05
        }
        
        relative_cost = cost_factors.get(sixr_strategy, 0.5)
        
        # Estimate payback period
        if total_value > 80 and relative_cost < 0.5:
            payback_months = 12
        elif total_value > 60:
            payback_months = 18
        else:
            payback_months = 24
        
        # Calculate 3-year ROI
        annual_value = total_value * 12  # Simplified annual value
        total_cost = relative_cost * 1000  # Simplified cost model
        three_year_value = annual_value * 3
        roi_percentage = ((three_year_value - total_cost) / total_cost) * 100
        
        return {
            "estimated_payback_months": payback_months,
            "three_year_roi_percentage": round(roi_percentage, 1),
            "annual_value_score": round(annual_value, 1),
            "relative_cost_factor": relative_cost,
            "cost_avoidance_factors": [
                "Reduced maintenance costs",
                "Avoided security breach risks",
                "Eliminated technical debt interest"
            ] if tech_debt_score > 50 else ["Minimal cost avoidance"]
        }
    
    def _get_priority_recommendation(self, total_value: float) -> str:
        """Get priority recommendation based on value"""
        
        if total_value >= 80:
            return "HIGH PRIORITY - Significant business value justifies immediate action"
        elif total_value >= 60:
            return "MEDIUM PRIORITY - Good candidate for migration wave 1-2"
        elif total_value >= 40:
            return "LOW PRIORITY - Consider for later migration waves"
        else:
            return "MINIMAL PRIORITY - Evaluate alternatives to migration"
    
    def _get_value_timeline(self, sixr_strategy: str) -> Dict[str, str]:
        """Get value realization timeline"""
        
        timelines = {
            SixRStrategy.REWRITE.value: {
                "initial_value": "12-18 months",
                "full_value": "18-24 months",
                "value_type": "Transformational"
            },
            SixRStrategy.REARCHITECT.value: {
                "initial_value": "6-12 months",
                "full_value": "12-18 months",
                "value_type": "Architectural"
            },
            SixRStrategy.REFACTOR.value: {
                "initial_value": "3-6 months",
                "full_value": "6-12 months",
                "value_type": "Incremental"
            },
            SixRStrategy.REPLATFORM.value: {
                "initial_value": "1-3 months",
                "full_value": "3-6 months",
                "value_type": "Platform"
            },
            SixRStrategy.REHOST.value: {
                "initial_value": "< 1 month",
                "full_value": "1-3 months",
                "value_type": "Infrastructure"
            },
            SixRStrategy.RETAIN.value: {
                "initial_value": "N/A",
                "full_value": "N/A",
                "value_type": "None"
            }
        }
        
        return timelines.get(sixr_strategy, {
            "initial_value": "3-6 months",
            "full_value": "6-12 months",
            "value_type": "Standard"
        })


class MoveGroupAnalyzer:
    """
    Identifies move group hints for the Planning Flow.
    
    Analyzes:
    - Technical dependencies between applications
    - Business process relationships
    - Data dependencies and integrations
    - Risk profiles and complexity alignment
    - Resource and timing constraints
    """
    
    def __init__(self):
        self.name = "move_group_analyzer"
        self.description = "Identifies migration grouping hints for planning"
        logger.info("Initialized MoveGroupAnalyzer")
    
    def _run(self, application_decisions: List[Dict[str, Any]], 
             dependency_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze applications to identify move group hints.
        
        Args:
            application_decisions: List of 6R decisions for applications
            dependency_data: Dependency information between applications
            
        Returns:
            Dict with move group recommendations and rationale
        """
        try:
            # Extract application details
            app_details = {}
            for decision in application_decisions:
                app_id = decision.get("application_id")
                app_details[app_id] = {
                    "name": decision.get("application_name"),
                    "strategy": decision.get("overall_strategy"),
                    "complexity": decision.get("complexity_score", 50),
                    "risk_factors": decision.get("risk_factors", []),
                    "components": decision.get("component_treatments", [])
                }
            
            # Identify dependency clusters
            dependency_groups = self._identify_dependency_clusters(
                app_details, dependency_data
            )
            
            # Group by strategy affinity
            strategy_groups = self._group_by_strategy_affinity(app_details)
            
            # Identify risk-based groups
            risk_groups = self._group_by_risk_profile(app_details)
            
            # Generate move group recommendations
            move_groups = self._synthesize_move_groups(
                dependency_groups, strategy_groups, risk_groups
            )
            
            # Generate group rationale
            group_rationale = self._generate_group_rationale(move_groups, app_details)
            
            # Calculate group metrics
            group_metrics = self._calculate_group_metrics(move_groups, app_details)
            
            return {
                "recommended_move_groups": move_groups,
                "group_rationale": group_rationale,
                "group_metrics": group_metrics,
                "dependency_constraints": self._get_dependency_constraints(dependency_data),
                "sequencing_recommendations": self._get_sequencing_recommendations(
                    move_groups, app_details
                )
            }
            
        except Exception as e:
            logger.error(f"Error in MoveGroupAnalyzer: {str(e)}")
            return {
                "recommended_move_groups": [],
                "error": str(e),
                "group_rationale": ["Unable to analyze move groups due to error"]
            }
    
    def _identify_dependency_clusters(self, app_details: Dict[str, Any],
                                    dependency_data: Dict[str, Any]) -> List[List[str]]:
        """Identify tightly coupled application clusters"""
        
        clusters = []
        processed = set()
        
        # Build dependency graph
        dependencies = dependency_data.get("dependencies", {})
        
        for app_id in app_details:
            if app_id in processed:
                continue
            
            # Find connected applications
            cluster = self._find_connected_apps(app_id, dependencies, processed)
            
            if len(cluster) > 1:
                clusters.append(cluster)
                processed.update(cluster)
            else:
                processed.add(app_id)
        
        return clusters
    
    def _find_connected_apps(self, start_app: str, dependencies: Dict[str, List[str]],
                           processed: set) -> List[str]:
        """Find all applications connected to the start app"""
        
        connected = [start_app]
        to_check = [start_app]
        checked = set()
        
        while to_check:
            current = to_check.pop()
            if current in checked:
                continue
            checked.add(current)
            
            # Check outgoing dependencies
            for dep in dependencies.get(current, []):
                if dep not in connected and dep not in processed:
                    connected.append(dep)
                    to_check.append(dep)
            
            # Check incoming dependencies
            for app, deps in dependencies.items():
                if current in deps and app not in connected and app not in processed:
                    connected.append(app)
                    to_check.append(app)
        
        return connected
    
    def _group_by_strategy_affinity(self, app_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group applications by compatible strategies"""
        
        strategy_groups = {
            "modernization": [],  # Rewrite, Rearchitect, Refactor
            "replatform": [],     # Replatform
            "lift_and_shift": [], # Rehost
            "minimal_change": []  # Retain, Retire
        }
        
        modernization_strategies = [
            SixRStrategy.REWRITE.value,
            SixRStrategy.REARCHITECT.value,
            SixRStrategy.REFACTOR.value
        ]
        
        for app_id, details in app_details.items():
            strategy = details.get("strategy")
            
            if strategy in modernization_strategies:
                strategy_groups["modernization"].append(app_id)
            elif strategy == SixRStrategy.REPLATFORM.value:
                strategy_groups["replatform"].append(app_id)
            elif strategy == SixRStrategy.REHOST.value:
                strategy_groups["lift_and_shift"].append(app_id)
            else:
                strategy_groups["minimal_change"].append(app_id)
        
        # Remove empty groups
        return {k: v for k, v in strategy_groups.items() if v}
    
    def _group_by_risk_profile(self, app_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group applications by risk level"""
        
        risk_groups = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": []
        }
        
        for app_id, details in app_details.items():
            risk_factors = details.get("risk_factors", [])
            complexity = details.get("complexity", 50)
            
            # Calculate risk score
            risk_score = len(risk_factors) * 10 + (complexity / 10)
            
            if risk_score > 70:
                risk_groups["high_risk"].append(app_id)
            elif risk_score > 40:
                risk_groups["medium_risk"].append(app_id)
            else:
                risk_groups["low_risk"].append(app_id)
        
        return risk_groups
    
    def _synthesize_move_groups(self, dependency_groups: List[List[str]],
                              strategy_groups: Dict[str, List[str]],
                              risk_groups: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Synthesize final move group recommendations"""
        
        move_groups = []
        assigned_apps = set()
        
        # Priority 1: Keep dependent applications together
        for idx, dep_group in enumerate(dependency_groups):
            move_groups.append({
                "group_id": f"dependency_group_{idx + 1}",
                "applications": dep_group,
                "group_type": "dependency_cluster",
                "priority": "high",
                "rationale": "Tightly coupled applications that should migrate together"
            })
            assigned_apps.update(dep_group)
        
        # Priority 2: Group remaining apps by strategy
        for strategy_type, apps in strategy_groups.items():
            unassigned = [app for app in apps if app not in assigned_apps]
            
            if unassigned:
                # Split large groups
                chunk_size = 5  # Max apps per group
                for i in range(0, len(unassigned), chunk_size):
                    chunk = unassigned[i:i + chunk_size]
                    move_groups.append({
                        "group_id": f"{strategy_type}_group_{i // chunk_size + 1}",
                        "applications": chunk,
                        "group_type": "strategy_affinity",
                        "priority": "medium",
                        "rationale": f"Applications with {strategy_type} migration approach"
                    })
                    assigned_apps.update(chunk)
        
        # Priority 3: Risk-based adjustments
        high_risk_apps = risk_groups.get("high_risk", [])
        for group in move_groups:
            group_apps = group["applications"]
            high_risk_in_group = [app for app in group_apps if app in high_risk_apps]
            
            if high_risk_in_group and len(high_risk_in_group) < len(group_apps):
                # Mixed risk group - flag for attention
                group["risk_warning"] = "Contains mix of high and lower risk applications"
        
        return move_groups
    
    def _generate_group_rationale(self, move_groups: List[Dict[str, Any]],
                                app_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate detailed rationale for each move group"""
        
        group_rationale = {}
        
        for group in move_groups:
            group_id = group["group_id"]
            apps = group["applications"]
            rationale = [group["rationale"]]
            
            # Add strategy details
            strategies = set()
            for app_id in apps:
                strategy = app_details.get(app_id, {}).get("strategy")
                if strategy:
                    strategies.add(strategy)
            
            if len(strategies) > 1:
                rationale.append(f"Mixed strategies: {', '.join(strategies)}")
            else:
                rationale.append(f"Unified strategy: {strategies.pop() if strategies else 'Unknown'}")
            
            # Add complexity assessment
            avg_complexity = sum(
                app_details.get(app_id, {}).get("complexity", 50)
                for app_id in apps
            ) / len(apps) if apps else 0
            
            if avg_complexity > 70:
                rationale.append("High complexity group - requires experienced team")
            elif avg_complexity < 30:
                rationale.append("Low complexity group - suitable for parallel execution")
            
            # Add size recommendation
            if len(apps) > 7:
                rationale.append("Large group - consider splitting if resources are limited")
            elif len(apps) == 1:
                rationale.append("Single application - can be combined with other groups")
            
            group_rationale[group_id] = rationale
        
        return group_rationale
    
    def _calculate_group_metrics(self, move_groups: List[Dict[str, Any]],
                               app_details: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for move groups"""
        
        metrics = {
            "total_groups": len(move_groups),
            "avg_group_size": 0,
            "largest_group_size": 0,
            "dependency_groups": 0,
            "strategy_groups": 0,
            "estimated_waves": 0
        }
        
        if not move_groups:
            return metrics
        
        group_sizes = []
        for group in move_groups:
            size = len(group["applications"])
            group_sizes.append(size)
            
            if group["group_type"] == "dependency_cluster":
                metrics["dependency_groups"] += 1
            elif group["group_type"] == "strategy_affinity":
                metrics["strategy_groups"] += 1
        
        metrics["avg_group_size"] = sum(group_sizes) / len(group_sizes)
        metrics["largest_group_size"] = max(group_sizes)
        
        # Estimate waves based on group priorities
        high_priority = sum(1 for g in move_groups if g.get("priority") == "high")
        medium_priority = sum(1 for g in move_groups if g.get("priority") == "medium")
        
        # Assume 3-4 groups per wave
        metrics["estimated_waves"] = max(1, (high_priority + medium_priority) // 3)
        
        return metrics
    
    def _get_dependency_constraints(self, dependency_data: Dict[str, Any]) -> List[str]:
        """Extract key dependency constraints for planning"""
        
        constraints = []
        
        dependencies = dependency_data.get("dependencies", {})
        
        # Find circular dependencies
        for app, deps in dependencies.items():
            for dep in deps:
                if app in dependencies.get(dep, []):
                    constraints.append(f"Circular dependency between {app} and {dep}")
        
        # Find hub applications (many dependencies)
        for app, deps in dependencies.items():
            if len(deps) > 5:
                constraints.append(f"{app} has {len(deps)} dependencies - migration will impact many systems")
        
        # Find critical path dependencies
        incoming_counts = {}
        for deps in dependencies.values():
            for dep in deps:
                incoming_counts[dep] = incoming_counts.get(dep, 0) + 1
        
        for app, count in incoming_counts.items():
            if count > 3:
                constraints.append(f"{app} is depended upon by {count} applications - critical path item")
        
        return constraints
    
    def _get_sequencing_recommendations(self, move_groups: List[Dict[str, Any]],
                                      app_details: Dict[str, Any]) -> List[str]:
        """Generate sequencing recommendations for move groups"""
        
        recommendations = []
        
        # Recommend starting with low-risk groups
        low_complexity_groups = []
        high_complexity_groups = []
        
        for group in move_groups:
            avg_complexity = sum(
                app_details.get(app_id, {}).get("complexity", 50)
                for app_id in group["applications"]
            ) / len(group["applications"]) if group["applications"] else 0
            
            if avg_complexity < 40:
                low_complexity_groups.append(group["group_id"])
            elif avg_complexity > 70:
                high_complexity_groups.append(group["group_id"])
        
        if low_complexity_groups:
            recommendations.append(
                f"Start with low-complexity groups for quick wins: {', '.join(low_complexity_groups[:2])}"
            )
        
        if high_complexity_groups:
            recommendations.append(
                f"Schedule high-complexity groups with adequate resources: {', '.join(high_complexity_groups[:2])}"
            )
        
        # Recommend parallel execution where possible
        independent_groups = [
            g for g in move_groups 
            if g["group_type"] != "dependency_cluster" and len(g["applications"]) < 4
        ]
        
        if len(independent_groups) > 2:
            recommendations.append(
                f"{len(independent_groups)} groups can potentially be migrated in parallel"
            )
        
        # Dependency-based sequencing
        dep_groups = [g for g in move_groups if g["group_type"] == "dependency_cluster"]
        if dep_groups:
            recommendations.append(
                "Migrate dependency clusters as atomic units to maintain system integrity"
            )
        
        return recommendations