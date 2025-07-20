"""
Business Context Analysis for Questionnaire Targeting - B2.4
ADCS AI Analysis & Intelligence Service

This service analyzes business context to optimize questionnaire targeting,
ensuring the right questions are asked to the right stakeholders at the right time.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BusinessDomain(str, Enum):
    """Business domains for context analysis"""
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    GOVERNMENT = "government"
    EDUCATION = "education"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    GENERAL = "general"


class OrganizationSize(str, Enum):
    """Organization size categories"""
    STARTUP = "startup"           # < 50 employees
    SMALL = "small"               # 50-249 employees
    MEDIUM = "medium"             # 250-999 employees
    LARGE = "large"               # 1000-4999 employees
    ENTERPRISE = "enterprise"     # 5000+ employees


class StakeholderRole(str, Enum):
    """Stakeholder roles for questionnaire targeting"""
    INFRASTRUCTURE_ENGINEER = "infrastructure_engineer"
    APPLICATION_ARCHITECT = "application_architect"
    BUSINESS_OWNER = "business_owner"
    SECURITY_OFFICER = "security_officer"
    COMPLIANCE_MANAGER = "compliance_manager"
    OPERATIONS_MANAGER = "operations_manager"
    DATABASE_ADMINISTRATOR = "database_administrator"
    NETWORK_ADMINISTRATOR = "network_administrator"
    PROJECT_MANAGER = "project_manager"
    C_LEVEL_EXECUTIVE = "c_level_executive"


class MigrationDriverType(str, Enum):
    """Types of migration drivers"""
    COST_OPTIMIZATION = "cost_optimization"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    END_OF_LIFE = "end_of_life"
    SCALABILITY = "scalability"
    SECURITY_ENHANCEMENT = "security_enhancement"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    VENDOR_CONSOLIDATION = "vendor_consolidation"
    DISASTER_RECOVERY = "disaster_recovery"


@dataclass
class BusinessContext:
    """Comprehensive business context for questionnaire targeting"""
    organization_profile: Dict[str, Any]
    migration_drivers: List[MigrationDriverType]
    stakeholder_landscape: Dict[StakeholderRole, Dict[str, Any]]
    regulatory_environment: Dict[str, Any]
    technical_maturity: Dict[str, Any]
    cultural_factors: Dict[str, Any]
    resource_constraints: Dict[str, Any]
    success_criteria: Dict[str, Any]


@dataclass
class QuestionnaireTarget:
    """Target definition for questionnaire delivery"""
    target_stakeholders: List[StakeholderRole]
    priority_level: str  # critical, high, medium, low
    complexity_level: str  # basic, intermediate, advanced
    estimated_effort_minutes: int
    business_justification: str
    success_metrics: List[str]


class BusinessContextAnalyzer:
    """
    Analyzes business context to optimize questionnaire targeting and design.
    
    Uses business intelligence to ensure questionnaires are contextually appropriate
    and target the right stakeholders with the right questions.
    """
    
    def __init__(self):
        """Initialize business context analyzer"""
        self.domain_configurations = self._initialize_domain_configurations()
        self.stakeholder_expertise = self._initialize_stakeholder_expertise()
        self.complexity_thresholds = self._initialize_complexity_thresholds()
    
    def _initialize_domain_configurations(self) -> Dict[BusinessDomain, Dict[str, Any]]:
        """Initialize business domain-specific configurations"""
        return {
            BusinessDomain.FINANCIAL_SERVICES: {
                "regulatory_focus": ["SOX", "PCI-DSS", "GDPR", "Basel III"],
                "critical_attributes": ["data_classification", "compliance_scope", "security_controls"],
                "stakeholder_priority": [
                    StakeholderRole.COMPLIANCE_MANAGER,
                    StakeholderRole.SECURITY_OFFICER,
                    StakeholderRole.BUSINESS_OWNER
                ],
                "migration_concerns": ["regulatory_compliance", "data_security", "business_continuity"],
                "question_complexity": "high"
            },
            BusinessDomain.HEALTHCARE: {
                "regulatory_focus": ["HIPAA", "HITECH", "FDA", "GDPR"],
                "critical_attributes": ["patient_data_handling", "compliance_scope", "availability_requirements"],
                "stakeholder_priority": [
                    StakeholderRole.COMPLIANCE_MANAGER,
                    StakeholderRole.SECURITY_OFFICER,
                    StakeholderRole.OPERATIONS_MANAGER
                ],
                "migration_concerns": ["patient_safety", "data_privacy", "system_availability"],
                "question_complexity": "high"
            },
            BusinessDomain.MANUFACTURING: {
                "regulatory_focus": ["ISO_27001", "NIST", "industry_specific"],
                "critical_attributes": ["operational_impact", "downtime_tolerance", "integration_points"],
                "stakeholder_priority": [
                    StakeholderRole.OPERATIONS_MANAGER,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                    StakeholderRole.BUSINESS_OWNER
                ],
                "migration_concerns": ["operational_continuity", "system_integration", "cost_control"],
                "question_complexity": "medium"
            },
            BusinessDomain.TECHNOLOGY: {
                "regulatory_focus": ["GDPR", "SOC2", "ISO_27001"],
                "critical_attributes": ["scalability", "performance", "technology_stack"],
                "stakeholder_priority": [
                    StakeholderRole.APPLICATION_ARCHITECT,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                    StakeholderRole.SECURITY_OFFICER
                ],
                "migration_concerns": ["technical_excellence", "scalability", "innovation"],
                "question_complexity": "medium"
            },
            BusinessDomain.GOVERNMENT: {
                "regulatory_focus": ["FedRAMP", "FISMA", "NIST", "GDPR"],
                "critical_attributes": ["security_clearance", "compliance_scope", "data_sovereignty"],
                "stakeholder_priority": [
                    StakeholderRole.SECURITY_OFFICER,
                    StakeholderRole.COMPLIANCE_MANAGER,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER
                ],
                "migration_concerns": ["security_compliance", "data_sovereignty", "transparency"],
                "question_complexity": "high"
            },
            BusinessDomain.GENERAL: {
                "regulatory_focus": ["GDPR", "SOC2", "basic_compliance"],
                "critical_attributes": ["business_criticality", "cost_impact", "operational_impact"],
                "stakeholder_priority": [
                    StakeholderRole.BUSINESS_OWNER,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                    StakeholderRole.OPERATIONS_MANAGER
                ],
                "migration_concerns": ["cost_effectiveness", "risk_management", "business_value"],
                "question_complexity": "medium"
            }
        }
    
    def _initialize_stakeholder_expertise(self) -> Dict[StakeholderRole, Dict[str, Any]]:
        """Initialize stakeholder expertise profiles"""
        return {
            StakeholderRole.INFRASTRUCTURE_ENGINEER: {
                "expertise_areas": [
                    "server_configuration", "network_architecture", "storage_systems",
                    "virtualization", "cloud_platforms", "performance_monitoring"
                ],
                "question_types": ["technical", "operational", "performance"],
                "complexity_comfort": "high",
                "typical_knowledge_gaps": ["business_impact", "compliance_requirements"],
                "optimal_session_length": 30,
                "preferred_question_format": "technical_detail"
            },
            StakeholderRole.APPLICATION_ARCHITECT: {
                "expertise_areas": [
                    "application_design", "technology_stack", "integration_patterns",
                    "data_architecture", "security_design", "scalability"
                ],
                "question_types": ["architectural", "technical", "integration"],
                "complexity_comfort": "high",
                "typical_knowledge_gaps": ["operational_procedures", "business_processes"],
                "optimal_session_length": 45,
                "preferred_question_format": "architectural_diagram"
            },
            StakeholderRole.BUSINESS_OWNER: {
                "expertise_areas": [
                    "business_processes", "user_requirements", "business_value",
                    "cost_impact", "operational_procedures", "stakeholder_needs"
                ],
                "question_types": ["business", "functional", "strategic"],
                "complexity_comfort": "low",
                "typical_knowledge_gaps": ["technical_architecture", "infrastructure_details"],
                "optimal_session_length": 20,
                "preferred_question_format": "business_language"
            },
            StakeholderRole.SECURITY_OFFICER: {
                "expertise_areas": [
                    "security_controls", "compliance_requirements", "threat_assessment",
                    "data_classification", "access_management", "audit_trails"
                ],
                "question_types": ["security", "compliance", "risk"],
                "complexity_comfort": "high",
                "typical_knowledge_gaps": ["operational_details", "business_processes"],
                "optimal_session_length": 35,
                "preferred_question_format": "security_framework"
            },
            StakeholderRole.COMPLIANCE_MANAGER: {
                "expertise_areas": [
                    "regulatory_requirements", "audit_processes", "documentation",
                    "risk_management", "policy_compliance", "reporting"
                ],
                "question_types": ["compliance", "regulatory", "documentation"],
                "complexity_comfort": "medium",
                "typical_knowledge_gaps": ["technical_implementation", "infrastructure"],
                "optimal_session_length": 25,
                "preferred_question_format": "compliance_checklist"
            },
            StakeholderRole.OPERATIONS_MANAGER: {
                "expertise_areas": [
                    "operational_procedures", "service_management", "incident_response",
                    "change_management", "monitoring", "maintenance"
                ],
                "question_types": ["operational", "procedural", "management"],
                "complexity_comfort": "medium",
                "typical_knowledge_gaps": ["detailed_technical_specs", "architectural_design"],
                "optimal_session_length": 30,
                "preferred_question_format": "operational_workflow"
            }
        }
    
    def _initialize_complexity_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize complexity thresholds for different contexts"""
        return {
            "question_complexity": {
                "basic": {
                    "max_questions_per_section": 8,
                    "max_total_questions": 20,
                    "technical_depth": "surface",
                    "business_context_required": False
                },
                "intermediate": {
                    "max_questions_per_section": 12,
                    "max_total_questions": 35,
                    "technical_depth": "moderate",
                    "business_context_required": True
                },
                "advanced": {
                    "max_questions_per_section": 20,
                    "max_total_questions": 60,
                    "technical_depth": "detailed",
                    "business_context_required": True
                }
            },
            "stakeholder_capacity": {
                "low": {"max_session_minutes": 15, "max_questions": 10},
                "medium": {"max_session_minutes": 30, "max_questions": 25},
                "high": {"max_session_minutes": 60, "max_questions": 50}
            }
        }
    
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
            org_profile = self._analyze_organization_profile(organization_info)
            
            # Identify migration drivers
            drivers = self._identify_migration_drivers(migration_objectives)
            
            # Analyze stakeholder landscape
            stakeholder_landscape = self._analyze_stakeholder_landscape(stakeholder_info)
            
            # Assess regulatory environment
            regulatory_env = self._assess_regulatory_environment(
                org_profile, regulatory_requirements or {}
            )
            
            # Evaluate technical maturity
            tech_maturity = self._evaluate_technical_maturity(organization_info)
            
            # Assess cultural factors
            cultural_factors = self._assess_cultural_factors(organization_info, stakeholder_info)
            
            # Identify resource constraints
            resource_constraints = self._identify_resource_constraints(
                organization_info, stakeholder_info
            )
            
            # Define success criteria
            success_criteria = self._define_success_criteria(migration_objectives, org_profile)
            
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
            return self._create_default_business_context()
    
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
                    target = self._create_questionnaire_target(gap, business_context, available_stakeholders)
                    if target:
                        questionnaire_targets.append(target)
            
            # Optimize delivery sequence
            delivery_sequence = self._optimize_delivery_sequence(questionnaire_targets, business_context)
            
            # Generate stakeholder communication strategy
            communication_strategy = self._generate_communication_strategy(
                questionnaire_targets, business_context
            )
            
            # Calculate effort and timeline estimates
            effort_estimates = self._calculate_effort_estimates(questionnaire_targets, business_context)
            
            return {
                "targeting_strategy": {
                    "questionnaire_targets": [self._target_to_dict(target) for target in questionnaire_targets],
                    "delivery_sequence": delivery_sequence,
                    "total_questionnaires": len(questionnaire_targets),
                    "estimated_completion_days": effort_estimates["total_days"]
                },
                "stakeholder_optimization": {
                    "primary_stakeholders": self._identify_primary_stakeholders(business_context),
                    "stakeholder_workload": effort_estimates["stakeholder_workload"],
                    "capacity_constraints": self._assess_capacity_constraints(business_context),
                    "escalation_paths": self._define_escalation_paths(business_context)
                },
                "communication_strategy": communication_strategy,
                "success_metrics": {
                    "target_response_rate": self._calculate_target_response_rate(business_context),
                    "quality_thresholds": self._define_quality_thresholds(business_context),
                    "timeline_milestones": effort_estimates["milestones"],
                    "risk_mitigation": self._identify_targeting_risks(business_context)
                },
                "optimization_metadata": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "business_domain": business_context.organization_profile.get("domain"),
                    "organization_size": business_context.organization_profile.get("size"),
                    "complexity_level": self._assess_overall_complexity(business_context)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing questionnaire targeting: {e}")
            return self._create_default_targeting_strategy()
    
    def _analyze_organization_profile(self, org_info: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _identify_migration_drivers(self, migration_objectives: Dict[str, Any]) -> List[MigrationDriverType]:
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
    
    def _analyze_stakeholder_landscape(self, stakeholder_info: Dict[str, Any]) -> Dict[StakeholderRole, Dict[str, Any]]:
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
    
    def _assess_regulatory_environment(
        self, 
        org_profile: Dict[str, Any], 
        regulatory_reqs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess regulatory environment and compliance requirements"""
        try:
            domain = org_profile.get("domain", BusinessDomain.GENERAL)
            domain_config = self.domain_configurations.get(domain, {})
            
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
    
    def _evaluate_technical_maturity(self, org_info: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _assess_cultural_factors(self, org_info: Dict[str, Any], stakeholder_info: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _identify_resource_constraints(self, org_info: Dict[str, Any], stakeholder_info: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _define_success_criteria(self, migration_objectives: Dict[str, Any], org_profile: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _create_questionnaire_target(
        self, 
        gap: Dict[str, Any], 
        business_context: BusinessContext,
        available_stakeholders: List[Dict[str, Any]]
    ) -> Optional[QuestionnaireTarget]:
        """Create a questionnaire target for a specific gap"""
        try:
            gap_category = gap.get("category", "general")
            gap_priority = gap.get("priority", 3)
            
            # Determine appropriate stakeholders
            target_stakeholders = self._determine_target_stakeholders(gap_category, business_context)
            
            # Filter by available stakeholders
            available_roles = [StakeholderRole(s.get("role", "").lower().replace(" ", "_")) 
                             for s in available_stakeholders 
                             if s.get("role")]
            target_stakeholders = [role for role in target_stakeholders if role in available_roles]
            
            if not target_stakeholders:
                return None
            
            # Determine complexity and effort
            complexity = self._determine_question_complexity(gap, business_context)
            effort_minutes = self._estimate_effort_minutes(gap, complexity, business_context)
            
            return QuestionnaireTarget(
                target_stakeholders=target_stakeholders,
                priority_level=self._map_gap_priority(gap_priority),
                complexity_level=complexity,
                estimated_effort_minutes=effort_minutes,
                business_justification=gap.get("business_justification", "Required for migration planning"),
                success_metrics=[
                    f"Fill {gap.get('attribute_name', 'missing')} data gap",
                    f"Improve 6R strategy confidence",
                    f"Enable accurate migration planning"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error creating questionnaire target: {e}")
            return None
    
    def _determine_target_stakeholders(self, gap_category: str, business_context: BusinessContext) -> List[StakeholderRole]:
        """Determine appropriate stakeholders for a gap category"""
        stakeholder_mapping = {
            "infrastructure": [
                StakeholderRole.INFRASTRUCTURE_ENGINEER,
                StakeholderRole.OPERATIONS_MANAGER,
                StakeholderRole.NETWORK_ADMINISTRATOR
            ],
            "application": [
                StakeholderRole.APPLICATION_ARCHITECT,
                StakeholderRole.BUSINESS_OWNER,
                StakeholderRole.PROJECT_MANAGER
            ],
            "operational": [
                StakeholderRole.OPERATIONS_MANAGER,
                StakeholderRole.BUSINESS_OWNER,
                StakeholderRole.PROJECT_MANAGER
            ],
            "dependencies": [
                StakeholderRole.APPLICATION_ARCHITECT,
                StakeholderRole.INFRASTRUCTURE_ENGINEER,
                StakeholderRole.BUSINESS_OWNER
            ],
            "security": [
                StakeholderRole.SECURITY_OFFICER,
                StakeholderRole.COMPLIANCE_MANAGER
            ],
            "compliance": [
                StakeholderRole.COMPLIANCE_MANAGER,
                StakeholderRole.SECURITY_OFFICER,
                StakeholderRole.BUSINESS_OWNER
            ]
        }
        
        return stakeholder_mapping.get(gap_category, [StakeholderRole.BUSINESS_OWNER])
    
    def _determine_question_complexity(self, gap: Dict[str, Any], business_context: BusinessContext) -> str:
        """Determine appropriate question complexity level"""
        domain = business_context.organization_profile.get("domain", BusinessDomain.GENERAL)
        domain_config = self.domain_configurations.get(domain, {})
        base_complexity = domain_config.get("question_complexity", "medium")
        
        # Adjust based on gap characteristics
        if gap.get("priority", 3) == 1:  # Critical gaps need detailed questions
            return "advanced"
        elif gap.get("technical_depth") == "high":
            return "advanced"
        elif base_complexity == "high":
            return "intermediate"
        else:
            return "basic"
    
    def _estimate_effort_minutes(self, gap: Dict[str, Any], complexity: str, business_context: BusinessContext) -> int:
        """Estimate effort required in minutes"""
        base_minutes = {
            "basic": 10,
            "intermediate": 20,
            "advanced": 35
        }
        
        effort = base_minutes.get(complexity, 15)
        
        # Adjust for organizational factors
        if business_context.cultural_factors.get("communication_style") == "detailed":
            effort += 5
        if business_context.resource_constraints.get("time_constraints") == "high":
            effort -= 5
        
        return max(5, effort)
    
    def _map_gap_priority(self, gap_priority: int) -> str:
        """Map gap priority to questionnaire priority"""
        mapping = {1: "critical", 2: "high", 3: "medium", 4: "low"}
        return mapping.get(gap_priority, "medium")
    
    def _optimize_delivery_sequence(self, targets: List[QuestionnaireTarget], business_context: BusinessContext) -> List[Dict[str, Any]]:
        """Optimize questionnaire delivery sequence"""
        # Sort by priority and complexity
        sorted_targets = sorted(targets, key=lambda t: (
            {"critical": 1, "high": 2, "medium": 3, "low": 4}[t.priority_level],
            {"basic": 1, "intermediate": 2, "advanced": 3}[t.complexity_level]
        ))
        
        sequence = []
        for i, target in enumerate(sorted_targets):
            sequence.append({
                "sequence_order": i + 1,
                "target_id": f"target_{i+1}",
                "stakeholders": [role.value for role in target.target_stakeholders],
                "priority": target.priority_level,
                "estimated_duration": target.estimated_effort_minutes,
                "dependencies": [],  # Could be enhanced with actual dependencies
                "recommended_timing": self._calculate_optimal_timing(i, business_context)
            })
        
        return sequence
    
    def _calculate_optimal_timing(self, sequence_index: int, business_context: BusinessContext) -> str:
        """Calculate optimal timing for questionnaire delivery"""
        # Simple timing calculation - could be enhanced
        days_offset = sequence_index * 2  # 2-day intervals
        return f"Day {days_offset + 1}"
    
    def _generate_communication_strategy(self, targets: List[QuestionnaireTarget], business_context: BusinessContext) -> Dict[str, Any]:
        """Generate stakeholder communication strategy"""
        try:
            return {
                "communication_channels": {
                    "primary": business_context.cultural_factors.get("communication_style", "email"),
                    "secondary": ["teams_meeting", "slack"],
                    "escalation": "management_review"
                },
                "messaging_framework": {
                    "business_justification": "Critical for migration success and risk reduction",
                    "time_commitment": "Minimal time investment for maximum migration value",
                    "value_proposition": "Your expertise directly improves migration outcomes",
                    "urgency_level": business_context.resource_constraints.get("time_constraints", "medium")
                },
                "stakeholder_customization": {
                    "technical_stakeholders": "Focus on technical accuracy and migration feasibility",
                    "business_stakeholders": "Emphasize business value and risk mitigation",
                    "executive_stakeholders": "Highlight strategic importance and ROI"
                },
                "follow_up_strategy": {
                    "reminder_cadence": "3_day_intervals",
                    "escalation_threshold": "7_days_no_response",
                    "completion_recognition": "public_acknowledgment"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating communication strategy: {e}")
            return {"communication_channels": {"primary": "email"}}
    
    def _calculate_effort_estimates(self, targets: List[QuestionnaireTarget], business_context: BusinessContext) -> Dict[str, Any]:
        """Calculate effort and timeline estimates"""
        try:
            total_minutes = sum(target.estimated_effort_minutes for target in targets)
            
            # Account for organizational factors
            efficiency_factor = 1.0
            if business_context.cultural_factors.get("collaboration_level") == "high":
                efficiency_factor *= 0.9
            if business_context.resource_constraints.get("stakeholder_availability") == "limited":
                efficiency_factor *= 1.3
            
            adjusted_minutes = total_minutes * efficiency_factor
            total_days = max(7, int(adjusted_minutes / 60 / 2))  # Assuming 2 hours per day max
            
            return {
                "total_minutes": int(adjusted_minutes),
                "total_days": total_days,
                "stakeholder_workload": self._calculate_stakeholder_workload(targets),
                "milestones": self._generate_timeline_milestones(total_days)
            }
            
        except Exception as e:
            logger.error(f"Error calculating effort estimates: {e}")
            return {"total_minutes": 0, "total_days": 7, "stakeholder_workload": {}}
    
    def _calculate_stakeholder_workload(self, targets: List[QuestionnaireTarget]) -> Dict[str, int]:
        """Calculate workload per stakeholder role"""
        workload = {}
        
        for target in targets:
            minutes_per_stakeholder = target.estimated_effort_minutes / len(target.target_stakeholders)
            for stakeholder in target.target_stakeholders:
                workload[stakeholder.value] = workload.get(stakeholder.value, 0) + minutes_per_stakeholder
        
        return {k: int(v) for k, v in workload.items()}
    
    def _generate_timeline_milestones(self, total_days: int) -> List[Dict[str, Any]]:
        """Generate timeline milestones"""
        milestones = []
        
        quarter_days = total_days // 4
        milestones.extend([
            {"day": quarter_days, "milestone": "25% questionnaires completed"},
            {"day": quarter_days * 2, "milestone": "50% questionnaires completed"},
            {"day": quarter_days * 3, "milestone": "75% questionnaires completed"},
            {"day": total_days, "milestone": "All questionnaires completed"}
        ])
        
        return milestones
    
    def _identify_primary_stakeholders(self, business_context: BusinessContext) -> List[str]:
        """Identify primary stakeholders based on business context"""
        domain = business_context.organization_profile.get("domain", BusinessDomain.GENERAL)
        domain_config = self.domain_configurations.get(domain, {})
        
        primary_roles = domain_config.get("stakeholder_priority", [StakeholderRole.BUSINESS_OWNER])
        return [role.value for role in primary_roles[:3]]  # Top 3 primary stakeholders
    
    def _assess_capacity_constraints(self, business_context: BusinessContext) -> Dict[str, Any]:
        """Assess stakeholder capacity constraints"""
        return {
            "overall_availability": business_context.resource_constraints.get("stakeholder_availability", "medium"),
            "competing_priorities": business_context.resource_constraints.get("competing_priorities", "medium"),
            "seasonal_factors": business_context.resource_constraints.get("seasonal_factors", []),
            "workload_distribution": "balanced",  # Could be enhanced with actual data
            "capacity_risk_level": "medium"
        }
    
    def _define_escalation_paths(self, business_context: BusinessContext) -> List[Dict[str, Any]]:
        """Define escalation paths for questionnaire non-completion"""
        return [
            {
                "level": 1,
                "trigger": "3_days_overdue",
                "action": "automated_reminder",
                "escalation_to": "direct_manager"
            },
            {
                "level": 2,
                "trigger": "7_days_overdue",
                "action": "manager_intervention",
                "escalation_to": "project_manager"
            },
            {
                "level": 3,
                "trigger": "14_days_overdue",
                "action": "executive_review",
                "escalation_to": "c_level_sponsor"
            }
        ]
    
    def _calculate_target_response_rate(self, business_context: BusinessContext) -> float:
        """Calculate target response rate based on context"""
        base_rate = 75.0
        
        # Adjust based on organizational factors
        if business_context.cultural_factors.get("collaboration_level") == "high":
            base_rate += 10
        if business_context.resource_constraints.get("stakeholder_availability") == "limited":
            base_rate -= 15
        if business_context.organization_profile.get("change_readiness") == "high":
            base_rate += 5
        
        return max(50.0, min(95.0, base_rate))
    
    def _define_quality_thresholds(self, business_context: BusinessContext) -> Dict[str, float]:
        """Define quality thresholds for responses"""
        domain = business_context.organization_profile.get("domain", BusinessDomain.GENERAL)
        domain_config = self.domain_configurations.get(domain, {})
        
        base_threshold = 75.0
        if domain_config.get("question_complexity") == "high":
            base_threshold = 80.0
        
        return {
            "minimum_completeness": base_threshold,
            "minimum_accuracy": base_threshold + 5,
            "minimum_relevance": base_threshold - 5,
            "overall_quality": base_threshold
        }
    
    def _identify_targeting_risks(self, business_context: BusinessContext) -> List[Dict[str, Any]]:
        """Identify risks in questionnaire targeting"""
        risks = []
        
        if business_context.resource_constraints.get("stakeholder_availability") == "limited":
            risks.append({
                "risk": "Low stakeholder availability",
                "impact": "medium",
                "mitigation": "Flexible scheduling and async collection methods"
            })
        
        if business_context.cultural_factors.get("change_tolerance") == "low":
            risks.append({
                "risk": "Change resistance",
                "impact": "high",
                "mitigation": "Enhanced communication and executive sponsorship"
            })
        
        return risks
    
    def _assess_overall_complexity(self, business_context: BusinessContext) -> str:
        """Assess overall complexity level for the business context"""
        domain = business_context.organization_profile.get("domain", BusinessDomain.GENERAL)
        domain_config = self.domain_configurations.get(domain, {})
        
        base_complexity = domain_config.get("question_complexity", "medium")
        org_size = business_context.organization_profile.get("size", OrganizationSize.MEDIUM)
        
        if org_size in [OrganizationSize.LARGE, OrganizationSize.ENTERPRISE] and base_complexity == "high":
            return "advanced"
        elif base_complexity == "high" or org_size == OrganizationSize.ENTERPRISE:
            return "intermediate"
        else:
            return "basic"
    
    def _target_to_dict(self, target: QuestionnaireTarget) -> Dict[str, Any]:
        """Convert QuestionnaireTarget to dictionary"""
        return {
            "target_stakeholders": [role.value for role in target.target_stakeholders],
            "priority_level": target.priority_level,
            "complexity_level": target.complexity_level,
            "estimated_effort_minutes": target.estimated_effort_minutes,
            "business_justification": target.business_justification,
            "success_metrics": target.success_metrics
        }
    
    def _create_default_business_context(self) -> BusinessContext:
        """Create default business context on error"""
        return BusinessContext(
            organization_profile={"domain": BusinessDomain.GENERAL, "size": OrganizationSize.MEDIUM},
            migration_drivers=[MigrationDriverType.DIGITAL_TRANSFORMATION],
            stakeholder_landscape={},
            regulatory_environment={"applicable_regulations": []},
            technical_maturity={"cloud_adoption_level": "hybrid"},
            cultural_factors={"change_tolerance": "medium"},
            resource_constraints={"stakeholder_availability": "medium"},
            success_criteria={"data_completeness_target": 80}
        )
    
    def _create_default_targeting_strategy(self) -> Dict[str, Any]:
        """Create default targeting strategy on error"""
        return {
            "targeting_strategy": {
                "questionnaire_targets": [],
                "delivery_sequence": [],
                "total_questionnaires": 0,
                "estimated_completion_days": 7
            },
            "stakeholder_optimization": {
                "primary_stakeholders": ["business_owner"],
                "stakeholder_workload": {},
                "capacity_constraints": {"overall_availability": "medium"},
                "escalation_paths": []
            },
            "communication_strategy": {"communication_channels": {"primary": "email"}},
            "success_metrics": {
                "target_response_rate": 75.0,
                "quality_thresholds": {"minimum_completeness": 75.0},
                "timeline_milestones": [],
                "risk_mitigation": []
            },
            "optimization_metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True
            }
        }


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