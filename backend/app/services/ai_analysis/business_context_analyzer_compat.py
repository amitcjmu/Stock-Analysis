"""
Business Context Analysis for Questionnaire Targeting - B2.4
ADCS AI Analysis & Intelligence Service

This service analyzes business context to optimize questionnaire targeting,
ensuring the right questions are asked to the right stakeholders at the right time.

This file maintains backward compatibility by re-exporting all components from
the modularized business_context_analyzer package.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# Import all components from the modularized package subdirectory
# Use relative import to avoid circular import issue
from .business_context_analyzer.enums import (
    BusinessDomain,
    OrganizationSize,
    StakeholderRole,
    MigrationDriverType
)
from .business_context_analyzer.models import (
    BusinessContext,
    QuestionnaireTarget
)
from .business_context_analyzer.domain_configurations import DomainConfigurationManager
from .business_context_analyzer.analyzers import BusinessAnalyzers
from .business_context_analyzer.optimization import QuestionnaireOptimizer
from .business_context_analyzer.utilities import BusinessContextUtilities

logger = logging.getLogger(__name__)


class BusinessContextAnalyzer:
    """
    Analyzes business context to optimize questionnaire targeting and design.
    
    Uses business intelligence to ensure questionnaires are contextually appropriate
    and target the right stakeholders with the right questions.
    """
    
    def __init__(self):
        """Initialize business context analyzer"""
        self.domain_configurations = DomainConfigurationManager.get_domain_configurations()
        self.stakeholder_expertise = DomainConfigurationManager.get_stakeholder_expertise()
        self.complexity_thresholds = DomainConfigurationManager.get_complexity_thresholds()
        
        # Initialize optimizer with domain configurations
        self.optimizer = QuestionnaireOptimizer(self.domain_configurations)
    
    def analyze_business_context(
        self,
        organization_info: Dict[str, Any],
        migration_objectives: Dict[str, Any],
        stakeholder_info: Dict[str, Any],
        regulatory_requirements: Optional[Dict[str, Any]] = None
    ) -> BusinessContext:
        """
        Analyze comprehensive business context for questionnaire optimization.
        
        Args:
            organization_info: Organization profile and characteristics
            migration_objectives: Migration drivers and objectives
            stakeholder_info: Available stakeholder information
            regulatory_requirements: Regulatory and compliance requirements
            
        Returns:
            Comprehensive business context analysis
        """
        try:
            # Analyze organization profile
            org_profile = BusinessAnalyzers.analyze_organization_profile(organization_info)
            
            # Identify migration drivers
            drivers = BusinessAnalyzers.identify_migration_drivers(migration_objectives)
            
            # Analyze stakeholder landscape
            stakeholder_landscape = BusinessAnalyzers.analyze_stakeholder_landscape(stakeholder_info)
            
            # Assess regulatory environment
            regulatory_env = BusinessAnalyzers.assess_regulatory_environment(
                org_profile, regulatory_requirements or {}, self.domain_configurations
            )
            
            # Evaluate technical maturity
            tech_maturity = BusinessAnalyzers.evaluate_technical_maturity(organization_info)
            
            # Assess cultural factors
            cultural_factors = BusinessAnalyzers.assess_cultural_factors(organization_info, stakeholder_info)
            
            # Identify resource constraints
            resource_constraints = BusinessAnalyzers.identify_resource_constraints(
                organization_info, stakeholder_info
            )
            
            # Define success criteria
            success_criteria = BusinessAnalyzers.define_success_criteria(migration_objectives, org_profile)
            
            return BusinessContext(
                organization_profile=org_profile,
                migration_drivers=drivers,
                stakeholder_landscape=stakeholder_landscape,
                regulatory_environment=regulatory_env,
                technical_maturity=tech_maturity,
                cultural_factors=cultural_factors,
                resource_constraints=resource_constraints,
                success_criteria=success_criteria
            )
            
        except Exception as e:
            logger.error(f"Error analyzing business context: {e}")
            return BusinessContextUtilities.create_default_business_context()
    
    def optimize_questionnaire_targeting(
        self,
        business_context: BusinessContext,
        gap_analysis: Dict[str, Any],
        available_stakeholders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Optimize questionnaire targeting based on business context and gap analysis.
        
        Args:
            business_context: Analyzed business context
            gap_analysis: Results from gap analysis
            available_stakeholders: List of available stakeholders
            
        Returns:
            Optimized questionnaire targeting strategy
        """
        try:
            # Create stakeholder-specific questionnaire targets
            questionnaire_targets = []
            
            prioritized_gaps = gap_analysis.get("prioritized_gaps", [])
            
            for gap in prioritized_gaps:
                if gap.get("priority", 4) <= 2:  # Critical and high priority only
                    target = self.optimizer.create_questionnaire_target(gap, business_context, available_stakeholders)
                    if target:
                        questionnaire_targets.append(target)
            
            # Optimize delivery sequence
            delivery_sequence = self.optimizer.optimize_delivery_sequence(questionnaire_targets, business_context)
            
            # Generate stakeholder communication strategy
            communication_strategy = self.optimizer.generate_communication_strategy(
                questionnaire_targets, business_context
            )
            
            # Calculate effort and timeline estimates
            effort_estimates = self.optimizer.calculate_effort_estimates(questionnaire_targets, business_context)
            
            return {
                "targeting_strategy": {
                    "questionnaire_targets": [self.optimizer.target_to_dict(target) for target in questionnaire_targets],
                    "delivery_sequence": delivery_sequence,
                    "total_questionnaires": len(questionnaire_targets),
                    "estimated_completion_days": effort_estimates["total_days"]
                },
                "stakeholder_optimization": {
                    "primary_stakeholders": self.optimizer.identify_primary_stakeholders(business_context),
                    "stakeholder_workload": effort_estimates["stakeholder_workload"],
                    "capacity_constraints": self.optimizer.assess_capacity_constraints(business_context),
                    "escalation_paths": self.optimizer.define_escalation_paths(business_context)
                },
                "communication_strategy": communication_strategy,
                "success_metrics": {
                    "target_response_rate": self.optimizer.calculate_target_response_rate(business_context),
                    "quality_thresholds": self.optimizer.define_quality_thresholds(business_context),
                    "timeline_milestones": effort_estimates["milestones"],
                    "risk_mitigation": self.optimizer.identify_targeting_risks(business_context)
                },
                "optimization_metadata": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "business_domain": business_context.organization_profile.get("domain"),
                    "organization_size": business_context.organization_profile.get("size"),
                    "complexity_level": self.optimizer.assess_overall_complexity(business_context)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing questionnaire targeting: {e}")
            return BusinessContextUtilities.create_default_targeting_strategy()


# Convenience function for easy integration
def analyze_and_optimize_targeting(
    organization_info: Dict[str, Any],
    migration_objectives: Dict[str, Any],
    stakeholder_info: Dict[str, Any],
    gap_analysis: Dict[str, Any],
    regulatory_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    High-level function to analyze business context and optimize questionnaire targeting.
    
    Args:
        organization_info: Organization profile and characteristics
        migration_objectives: Migration drivers and objectives
        stakeholder_info: Available stakeholder information
        gap_analysis: Results from gap analysis
        regulatory_requirements: Regulatory and compliance requirements
        
    Returns:
        Complete business context analysis and optimized targeting strategy
    """
    try:
        analyzer = BusinessContextAnalyzer()
        
        # Analyze business context
        business_context = analyzer.analyze_business_context(
            organization_info,
            migration_objectives,
            stakeholder_info,
            regulatory_requirements
        )
        
        # Optimize questionnaire targeting
        available_stakeholders = stakeholder_info.get("available_stakeholders", [])
        targeting_optimization = analyzer.optimize_questionnaire_targeting(
            business_context,
            gap_analysis,
            available_stakeholders
        )
        
        return {
            "business_context_analysis": {
                "organization_profile": business_context.organization_profile,
                "migration_drivers": [driver.value for driver in business_context.migration_drivers],
                "regulatory_environment": business_context.regulatory_environment,
                "technical_maturity": business_context.technical_maturity,
                "cultural_factors": business_context.cultural_factors,
                "resource_constraints": business_context.resource_constraints,
                "success_criteria": business_context.success_criteria
            },
            "targeting_optimization": targeting_optimization,
            "analysis_metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "analyzer_version": "business_context_v1.0",
                "domain": business_context.organization_profile.get("domain"),
                "organization_size": business_context.organization_profile.get("size")
            }
        }
        
    except Exception as e:
        logger.error(f"Error in business context analysis and targeting optimization: {e}")
        return {
            "error": str(e),
            "business_context_analysis": {},
            "targeting_optimization": {},
            "analysis_metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True
            }
        }