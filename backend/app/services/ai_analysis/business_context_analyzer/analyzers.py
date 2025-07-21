"""
Business Context Analysis Core Analyzers - B2.4
ADCS AI Analysis & Intelligence Service

Core analysis methods for business context evaluation.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from typing import Dict, List, Any

from .enums import BusinessDomain, OrganizationSize, StakeholderRole, MigrationDriverType
from .models import BusinessContext

logger = logging.getLogger(__name__)


class BusinessAnalyzers:
    """Core business analysis methods"""
    
    @staticmethod
    def analyze_organization_profile(org_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze organization profile and characteristics"""
        try:
            # Determine business domain
            industry = org_info.get("industry", "").lower()
            domain = BusinessDomain.GENERAL
            
            for business_domain in BusinessDomain:
                if business_domain.value in industry:
                    domain = business_domain
                    break
            
            # Determine organization size
            employee_count = org_info.get("employee_count", 0)
            if employee_count < 50:
                size = OrganizationSize.STARTUP
            elif employee_count < 250:
                size = OrganizationSize.SMALL
            elif employee_count < 1000:
                size = OrganizationSize.MEDIUM
            elif employee_count < 5000:
                size = OrganizationSize.LARGE
            else:
                size = OrganizationSize.ENTERPRISE
            
            return {
                "domain": domain,
                "size": size,
                "industry": org_info.get("industry", "Unknown"),
                "employee_count": employee_count,
                "geographic_presence": org_info.get("geographic_presence", "single_region"),
                "technology_maturity": org_info.get("technology_maturity", "medium"),
                "risk_tolerance": org_info.get("risk_tolerance", "medium"),
                "change_readiness": org_info.get("change_readiness", "medium")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing organization profile: {e}")
            return {"domain": BusinessDomain.GENERAL, "size": OrganizationSize.MEDIUM}
    
    @staticmethod
    def identify_migration_drivers(migration_objectives: Dict[str, Any]) -> List[MigrationDriverType]:
        """Identify primary migration drivers from objectives"""
        drivers = []
        
        try:
            objectives = migration_objectives.get("objectives", [])
            priorities = migration_objectives.get("priorities", [])
            
            # Map objectives to drivers
            driver_keywords = {
                MigrationDriverType.COST_OPTIMIZATION: ["cost", "savings", "efficiency", "economics"],
                MigrationDriverType.DIGITAL_TRANSFORMATION: ["digital", "transformation", "modernization", "innovation"],
                MigrationDriverType.COMPLIANCE_REQUIREMENT: ["compliance", "regulatory", "audit", "governance"],
                MigrationDriverType.END_OF_LIFE: ["end of life", "eol", "support", "maintenance"],
                MigrationDriverType.SCALABILITY: ["scale", "growth", "capacity", "performance"],
                MigrationDriverType.SECURITY_ENHANCEMENT: ["security", "protection", "threat", "vulnerability"],
                MigrationDriverType.PERFORMANCE_IMPROVEMENT: ["performance", "speed", "latency", "optimization"],
                MigrationDriverType.VENDOR_CONSOLIDATION: ["vendor", "consolidation", "standardization"],
                MigrationDriverType.DISASTER_RECOVERY: ["disaster recovery", "backup", "resilience", "availability"]
            }
            
            all_text = " ".join(objectives + priorities).lower()
            
            for driver_type, keywords in driver_keywords.items():
                if any(keyword in all_text for keyword in keywords):
                    drivers.append(driver_type)
            
            # Default driver if none identified
            if not drivers:
                drivers.append(MigrationDriverType.DIGITAL_TRANSFORMATION)
                
        except Exception as e:
            logger.error(f"Error identifying migration drivers: {e}")
            drivers = [MigrationDriverType.DIGITAL_TRANSFORMATION]
        
        return drivers
    
    @staticmethod
    def analyze_stakeholder_landscape(stakeholder_info: Dict[str, Any]) -> Dict[StakeholderRole, Dict[str, Any]]:
        """Analyze available stakeholder landscape"""
        landscape = {}
        
        try:
            available_stakeholders = stakeholder_info.get("available_stakeholders", [])
            
            for stakeholder in available_stakeholders:
                role_str = stakeholder.get("role", "").lower().replace(" ", "_")
                
                # Map to stakeholder role enum
                matched_role = None
                for role in StakeholderRole:
                    if role.value in role_str or any(word in role_str for word in role.value.split("_")):
                        matched_role = role
                        break
                
                if matched_role:
                    landscape[matched_role] = {
                        "name": stakeholder.get("name", "Unknown"),
                        "availability": stakeholder.get("availability", "medium"),
                        "expertise_level": stakeholder.get("expertise_level", "medium"),
                        "communication_preference": stakeholder.get("communication_preference", "email"),
                        "time_zone": stakeholder.get("time_zone", "UTC"),
                        "workload": stakeholder.get("current_workload", "medium"),
                        "engagement_history": stakeholder.get("engagement_history", [])
                    }
            
        except Exception as e:
            logger.error(f"Error analyzing stakeholder landscape: {e}")
        
        return landscape
    
    @staticmethod
    def assess_regulatory_environment(
        org_profile: Dict[str, Any], 
        regulatory_reqs: Dict[str, Any],
        domain_configurations: Dict[BusinessDomain, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess regulatory environment and compliance requirements"""
        try:
            domain = org_profile.get("domain", BusinessDomain.GENERAL)
            domain_config = domain_configurations.get(domain, {})
            
            applicable_regulations = regulatory_reqs.get("applicable_regulations", [])
            if not applicable_regulations:
                applicable_regulations = domain_config.get("regulatory_focus", [])
            
            return {
                "applicable_regulations": applicable_regulations,
                "compliance_maturity": regulatory_reqs.get("compliance_maturity", "medium"),
                "audit_frequency": regulatory_reqs.get("audit_frequency", "annual"),
                "risk_tolerance": regulatory_reqs.get("risk_tolerance", "low"),
                "documentation_requirements": regulatory_reqs.get("documentation_requirements", "standard"),
                "approval_processes": regulatory_reqs.get("approval_processes", "standard")
            }
            
        except Exception as e:
            logger.error(f"Error assessing regulatory environment: {e}")
            return {"applicable_regulations": [], "compliance_maturity": "medium"}
    
    @staticmethod
    def evaluate_technical_maturity(org_info: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate technical maturity of the organization"""
        try:
            return {
                "cloud_adoption_level": org_info.get("cloud_adoption", "hybrid"),
                "automation_maturity": org_info.get("automation_maturity", "medium"),
                "monitoring_sophistication": org_info.get("monitoring_level", "basic"),
                "development_practices": org_info.get("development_practices", "traditional"),
                "infrastructure_as_code": org_info.get("iac_adoption", False),
                "api_first_approach": org_info.get("api_first", False),
                "microservices_adoption": org_info.get("microservices", "limited"),
                "data_management_maturity": org_info.get("data_maturity", "medium")
            }
            
        except Exception as e:
            logger.error(f"Error evaluating technical maturity: {e}")
            return {"cloud_adoption_level": "hybrid", "automation_maturity": "medium"}
    
    @staticmethod
    def assess_cultural_factors(org_info: Dict[str, Any], stakeholder_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess organizational cultural factors"""
        try:
            return {
                "change_tolerance": org_info.get("change_tolerance", "medium"),
                "communication_style": org_info.get("communication_style", "formal"),
                "decision_making_speed": org_info.get("decision_speed", "medium"),
                "risk_appetite": org_info.get("risk_appetite", "conservative"),
                "collaboration_level": stakeholder_info.get("collaboration_rating", "medium"),
                "transparency_preference": org_info.get("transparency", "medium"),
                "feedback_culture": org_info.get("feedback_culture", "formal")
            }
            
        except Exception as e:
            logger.error(f"Error assessing cultural factors: {e}")
            return {"change_tolerance": "medium", "communication_style": "formal"}
    
    @staticmethod
    def identify_resource_constraints(org_info: Dict[str, Any], stakeholder_info: Dict[str, Any]) -> Dict[str, Any]:
        """Identify resource constraints affecting questionnaire deployment"""
        try:
            return {
                "budget_constraints": org_info.get("budget_flexibility", "medium"),
                "time_constraints": org_info.get("timeline_pressure", "medium"),
                "stakeholder_availability": stakeholder_info.get("overall_availability", "limited"),
                "expertise_gaps": stakeholder_info.get("expertise_gaps", []),
                "competing_priorities": org_info.get("competing_initiatives", "medium"),
                "seasonal_factors": org_info.get("seasonal_constraints", []),
                "geographical_distribution": org_info.get("geographic_spread", "localized")
            }
            
        except Exception as e:
            logger.error(f"Error identifying resource constraints: {e}")
            return {"budget_constraints": "medium", "time_constraints": "medium"}
    
    @staticmethod
    def define_success_criteria(migration_objectives: Dict[str, Any], org_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Define success criteria for business context analysis"""
        try:
            return {
                "data_completeness_target": migration_objectives.get("completeness_target", 85),
                "stakeholder_engagement_target": migration_objectives.get("engagement_target", 80),
                "response_quality_threshold": migration_objectives.get("quality_threshold", 75),
                "timeline_adherence_target": migration_objectives.get("timeline_target", 90),
                "business_alignment_score": migration_objectives.get("alignment_target", 85),
                "risk_mitigation_level": org_profile.get("risk_tolerance", "medium"),
                "cost_efficiency_target": migration_objectives.get("cost_target", "budget_neutral")
            }
            
        except Exception as e:
            logger.error(f"Error defining success criteria: {e}")
            return {"data_completeness_target": 80, "stakeholder_engagement_target": 75}