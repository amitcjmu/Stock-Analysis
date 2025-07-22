"""
Template System for Similar Applications

Creates and manages templates for applications with similar characteristics,
enabling efficient data collection for groups of related applications.

Agent Team B3 - Task B3.4
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..collection_flow.quality_scoring import QualityAssessmentService
from .adaptive_form_service import AdaptiveForm, FormField, FormSection


class TemplateType(str, Enum):
    """Types of application templates"""
    TECHNOLOGY_BASED = "technology_based"
    ARCHITECTURE_BASED = "architecture_based"
    INDUSTRY_BASED = "industry_based"
    COMPLIANCE_BASED = "compliance_based"
    CUSTOM = "custom"


class TemplateStatus(str, Enum):
    """Template lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class SimilarityMethod(str, Enum):
    """Methods for calculating application similarity"""
    TECHNOLOGY_STACK = "technology_stack"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    BUSINESS_CONTEXT = "business_context"
    COMBINED = "combined"


@dataclass
class ApplicationProfile:
    """Profile of an application for similarity analysis"""
    application_id: UUID
    application_name: str
    technology_stack: List[str]
    architecture_pattern: str
    business_criticality: str
    compliance_requirements: List[str]
    industry_sector: str
    data_characteristics: Dict[str, Any]
    collected_attributes: List[str]
    collection_quality_score: float
    profile_created_at: datetime


@dataclass
class TemplateField:
    """Template field with default values and adaptations"""
    field_id: str
    label: str
    field_type: str
    critical_attribute: str
    default_value: Optional[Any] = None
    suggested_values: List[Any] = None
    adaptation_rules: Dict[str, Any] = None
    validation_overrides: Dict[str, Any] = None
    help_text: Optional[str] = None
    is_required: bool = False


@dataclass
class ApplicationTemplate:
    """Template for similar applications"""
    template_id: str
    name: str
    description: str
    template_type: TemplateType
    status: TemplateStatus
    similarity_criteria: Dict[str, Any]
    fields: List[TemplateField]
    default_values: Dict[str, Any]
    validation_rules: Dict[str, Any]
    source_applications: List[UUID]
    usage_count: int
    effectiveness_score: float
    created_at: datetime
    updated_at: datetime
    version: str = "1.0"


@dataclass
class SimilarityResult:
    """Result of application similarity analysis"""
    target_application_id: UUID
    similar_applications: List[Tuple[UUID, float]]  # (app_id, similarity_score)
    recommended_templates: List[Tuple[str, float]]  # (template_id, relevance_score)
    similarity_factors: Dict[str, float]
    confidence_score: float


@dataclass
class TemplateApplication:
    """Application of template to specific application"""
    application_id: UUID
    template_id: str
    applied_at: datetime
    field_values: Dict[str, Any]
    completion_percentage: float
    effectiveness_score: float
    user_feedback_score: Optional[float] = None


class TemplateService:
    """Service for managing application templates and similarity analysis"""
    
    # Pre-defined template configurations for common application types
    PREDEFINED_TEMPLATES = {
        'java_web_application': {
            'name': 'Java Web Application',
            'description': 'Template for Java-based web applications',
            'template_type': TemplateType.TECHNOLOGY_BASED,
            'similarity_criteria': {
                'technology_stack': ['java', 'spring', 'tomcat'],
                'architecture_pattern': ['monolith', 'layered'],
                'weight': 0.8
            },
            'default_values': {
                'field_technology_stack': 'Java, Spring Framework, Apache Tomcat',
                'field_architecture_pattern': 'layered',
                'field_virtualization': 'vmware_vsphere',
                'field_business_logic_complexity': 'Moderate business logic with Spring controllers and services'
            }
        },
        'dotnet_enterprise': {
            'name': '.NET Enterprise Application',
            'description': 'Template for enterprise .NET applications',
            'template_type': TemplateType.TECHNOLOGY_BASED,
            'similarity_criteria': {
                'technology_stack': ['.net', 'sql server', 'iis'],
                'architecture_pattern': ['layered', 'soa'],
                'weight': 0.8
            },
            'default_values': {
                'field_technology_stack': '.NET Framework, SQL Server, IIS',
                'field_architecture_pattern': 'layered',
                'field_os_version': 'windows_server_2019',
                'field_integration_dependencies': 'SQL Server Database, Active Directory authentication'
            }
        },
        'microservices_cloud_native': {
            'name': 'Cloud-Native Microservices',
            'description': 'Template for microservices applications',
            'template_type': TemplateType.ARCHITECTURE_BASED,
            'similarity_criteria': {
                'architecture_pattern': ['microservices'],
                'technology_stack': ['docker', 'kubernetes', 'api'],
                'weight': 0.9
            },
            'default_values': {
                'field_architecture_pattern': 'microservices',
                'field_virtualization': 'container',
                'field_integration_dependencies': 'REST APIs, Message queues, Service mesh',
                'field_configuration_complexity': 'High - Multiple services with independent deployment'
            }
        },
        'financial_services_app': {
            'name': 'Financial Services Application',
            'description': 'Template for financial sector applications',
            'template_type': TemplateType.INDUSTRY_BASED,
            'similarity_criteria': {
                'compliance_requirements': ['sox', 'pci_dss'],
                'business_criticality': ['mission_critical', 'business_critical'],
                'weight': 0.7
            },
            'default_values': {
                'field_business_criticality': 'mission_critical',
                'field_compliance_constraints': 'financial',
                'field_security_requirements': 'encryption_rest,encryption_transit,multi_factor_auth',
                'field_availability_requirements': '99.99'
            }
        },
        'healthcare_application': {
            'name': 'Healthcare Application',
            'description': 'Template for healthcare sector applications',
            'template_type': TemplateType.COMPLIANCE_BASED,
            'similarity_criteria': {
                'compliance_requirements': ['hipaa'],
                'security_requirements': ['pii', 'encryption'],
                'weight': 0.8
            },
            'default_values': {
                'field_compliance_constraints': 'healthcare',
                'field_security_requirements': 'hipaa,pii,encryption_rest,encryption_transit',
                'field_data_characteristics': 'Contains PHI (Protected Health Information)',
                'field_business_criticality': 'business_critical'
            }
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.quality_service = QualityAssessmentService()
        self._templates = {}  # In-memory store for demo
        self._application_profiles = {}  # In-memory store for demo
        self._template_applications = defaultdict(list)  # template_id -> applications
        
        # Initialize predefined templates
        self._initialize_predefined_templates()

    async def create_template_from_applications(
        self,
        source_applications: List[ApplicationProfile],
        template_name: str,
        template_type: TemplateType,
        similarity_threshold: float = 0.7
    ) -> ApplicationTemplate:
        """
        Create a template based on similar applications.
        
        Core implementation of B3.4 - template system for similar applications.
        Analyzes multiple applications to extract common patterns and create reusable templates.
        """
        template_id = f"template_{uuid4()}"
        
        self.logger.info(f"Creating template {template_id} from {len(source_applications)} applications")
        
        # Analyze applications for common patterns
        common_patterns = await self._extract_common_patterns(source_applications)
        
        # Generate template fields based on patterns
        template_fields = await self._generate_template_fields(common_patterns, source_applications)
        
        # Calculate default values from source applications
        default_values = await self._calculate_default_values(source_applications, template_fields)
        
        # Generate validation rules
        validation_rules = await self._generate_template_validation_rules(source_applications)
        
        # Calculate similarity criteria
        similarity_criteria = await self._calculate_similarity_criteria(source_applications, template_type)
        
        # Calculate effectiveness score based on source application quality
        effectiveness_score = await self._calculate_template_effectiveness(source_applications)
        
        template = ApplicationTemplate(
            template_id=template_id,
            name=template_name,
            description=f"Template created from {len(source_applications)} similar applications",
            template_type=template_type,
            status=TemplateStatus.ACTIVE,
            similarity_criteria=similarity_criteria,
            fields=template_fields,
            default_values=default_values,
            validation_rules=validation_rules,
            source_applications=[app.application_id for app in source_applications],
            usage_count=0,
            effectiveness_score=effectiveness_score,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store template
        self._templates[template_id] = template
        
        self.logger.info(f"Created template {template_id} with {len(template_fields)} fields")
        return template

    async def find_similar_applications(
        self,
        target_application: ApplicationProfile,
        similarity_method: SimilarityMethod = SimilarityMethod.COMBINED,
        min_similarity: float = 0.5,
        max_results: int = 10
    ) -> SimilarityResult:
        """
        Find applications similar to the target application.
        
        Uses multiple similarity metrics to identify applications that share
        characteristics with the target application.
        """
        self.logger.info(f"Finding similar applications for {target_application.application_id}")
        
        similar_apps = []
        similarity_factors = {}
        
        for app_id, profile in self._application_profiles.items():
            if profile.application_id == target_application.application_id:
                continue
            
            similarity_score = await self._calculate_application_similarity(
                target_application, profile, similarity_method
            )
            
            if similarity_score >= min_similarity:
                similar_apps.append((profile.application_id, similarity_score))
        
        # Sort by similarity score and limit results
        similar_apps.sort(key=lambda x: x[1], reverse=True)
        similar_apps = similar_apps[:max_results]
        
        # Find recommended templates
        recommended_templates = await self._find_relevant_templates(target_application)
        
        # Calculate overall confidence
        confidence_score = self._calculate_similarity_confidence(similar_apps, target_application)
        
        return SimilarityResult(
            target_application_id=target_application.application_id,
            similar_applications=similar_apps,
            recommended_templates=recommended_templates,
            similarity_factors=similarity_factors,
            confidence_score=confidence_score
        )

    async def apply_template_to_application(
        self,
        template_id: str,
        application_id: UUID,
        user_overrides: Optional[Dict[str, Any]] = None
    ) -> AdaptiveForm:
        """
        Apply a template to generate an adaptive form for an application.
        
        Customizes the template based on application-specific context
        and user overrides.
        """
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        self.logger.info(f"Applying template {template_id} to application {application_id}")
        
        # Generate form sections from template
        sections = await self._generate_form_sections_from_template(template, application_id)
        
        # Apply user overrides if provided
        if user_overrides:
            sections = await self._apply_user_overrides(sections, user_overrides)
        
        # Create adaptive form
        form = AdaptiveForm(
            id=f"form_{application_id}_{template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=f"{template.name} - {application_id}",
            application_id=application_id,
            gap_analysis_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
            sections=sections,
            total_fields=sum(len(section.fields) for section in sections),
            required_fields=sum(len([f for f in section.fields if f.validation and any(rule.name == 'REQUIRED' for rule in f.validation.rules)]) for section in sections),
            estimated_completion_time=max(10, len(template.fields) * 2),
            confidence_impact_score=template.effectiveness_score,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Track template application
        template_application = TemplateApplication(
            application_id=application_id,
            template_id=template_id,
            applied_at=datetime.now(),
            field_values=template.default_values.copy(),
            completion_percentage=0.0,
            effectiveness_score=0.0
        )
        self._template_applications[template_id].append(template_application)
        
        # Update template usage count
        template.usage_count += 1
        template.updated_at = datetime.now()
        
        return form

    async def get_template_recommendations(
        self,
        application_profile: ApplicationProfile,
        max_recommendations: int = 5
    ) -> List[Tuple[ApplicationTemplate, float]]:
        """Get template recommendations for an application"""
        
        recommendations = []
        
        for template in self._templates.values():
            if template.status != TemplateStatus.ACTIVE:
                continue
            
            relevance_score = await self._calculate_template_relevance(application_profile, template)
            
            if relevance_score > 0.3:  # Minimum relevance threshold
                recommendations.append((template, relevance_score))
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:max_recommendations]

    async def update_template_effectiveness(
        self,
        template_id: str,
        application_id: UUID,
        completion_percentage: float,
        user_feedback_score: Optional[float] = None
    ) -> None:
        """Update template effectiveness based on usage feedback"""
        
        template = self._templates.get(template_id)
        if not template:
            return
        
        # Find template application
        for app in self._template_applications[template_id]:
            if app.application_id == application_id:
                app.completion_percentage = completion_percentage
                app.effectiveness_score = completion_percentage / 100.0
                if user_feedback_score:
                    app.user_feedback_score = user_feedback_score
                break
        
        # Recalculate template effectiveness
        applications = self._template_applications[template_id]
        if applications:
            avg_completion = sum(app.completion_percentage for app in applications) / len(applications)
            avg_feedback = sum(app.user_feedback_score or 0.7 for app in applications) / len(applications)
            template.effectiveness_score = (avg_completion / 100.0 * 0.7 + avg_feedback * 0.3)
            template.updated_at = datetime.now()

    def _initialize_predefined_templates(self) -> None:
        """Initialize predefined templates"""
        
        for template_key, config in self.PREDEFINED_TEMPLATES.items():
            template_id = f"predefined_{template_key}"
            
            # Convert default values to template fields
            fields = []
            for field_id, default_value in config['default_values'].items():
                field = TemplateField(
                    field_id=field_id,
                    label=field_id.replace('field_', '').replace('_', ' ').title(),
                    field_type='text',
                    critical_attribute=field_id.replace('field_', ''),
                    default_value=default_value,
                    is_required=True
                )
                fields.append(field)
            
            template = ApplicationTemplate(
                template_id=template_id,
                name=config['name'],
                description=config['description'],
                template_type=config['template_type'],
                status=TemplateStatus.ACTIVE,
                similarity_criteria=config['similarity_criteria'],
                fields=fields,
                default_values=config['default_values'],
                validation_rules={},
                source_applications=[],
                usage_count=0,
                effectiveness_score=0.8,  # Default effectiveness for predefined templates
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self._templates[template_id] = template

    async def _extract_common_patterns(self, applications: List[ApplicationProfile]) -> Dict[str, Any]:
        """Extract common patterns from applications"""
        
        patterns = {
            'technology_stacks': defaultdict(int),
            'architecture_patterns': defaultdict(int),
            'business_criticalities': defaultdict(int),
            'compliance_requirements': defaultdict(int),
            'common_attributes': defaultdict(int)
        }
        
        for app in applications:
            # Technology stack patterns
            for tech in app.technology_stack:
                patterns['technology_stacks'][tech.lower()] += 1
            
            # Architecture patterns
            patterns['architecture_patterns'][app.architecture_pattern] += 1
            
            # Business criticality
            patterns['business_criticalities'][app.business_criticality] += 1
            
            # Compliance requirements
            for req in app.compliance_requirements:
                patterns['compliance_requirements'][req] += 1
            
            # Common collected attributes
            for attr in app.collected_attributes:
                patterns['common_attributes'][attr] += 1
        
        # Convert to percentages
        app_count = len(applications)
        for pattern_type, counts in patterns.items():
            for key in counts:
                counts[key] = counts[key] / app_count
        
        return patterns

    async def _generate_template_fields(
        self, 
        patterns: Dict[str, Any],
        applications: List[ApplicationProfile]
    ) -> List[TemplateField]:
        """Generate template fields based on common patterns"""
        
        fields = []
        
        # Always include critical attributes that appear in most applications
        common_attributes = patterns['common_attributes']
        for attr, frequency in common_attributes.items():
            if frequency >= 0.6:  # Present in 60%+ of applications
                field = TemplateField(
                    field_id=f"field_{attr}",
                    label=attr.replace('_', ' ').title(),
                    field_type='text',
                    critical_attribute=attr,
                    is_required=frequency >= 0.8
                )
                fields.append(field)
        
        return fields

    async def _calculate_default_values(
        self,
        applications: List[ApplicationProfile],
        fields: List[TemplateField]
    ) -> Dict[str, Any]:
        """Calculate default values for template fields"""
        
        defaults = {}
        
        # For each field, find the most common value across applications
        for field in fields:
            values = []
            attribute = field.critical_attribute
            
            for app in applications:
                if attribute == 'technology_stack':
                    values.extend(app.technology_stack)
                elif attribute == 'architecture_pattern':
                    values.append(app.architecture_pattern)
                elif attribute == 'business_criticality':
                    values.append(app.business_criticality)
                elif attribute == 'compliance_requirements':
                    values.extend(app.compliance_requirements)
            
            if values:
                # Find most common value
                value_counts = defaultdict(int)
                for value in values:
                    value_counts[value] += 1
                
                most_common = max(value_counts.items(), key=lambda x: x[1])
                defaults[field.field_id] = most_common[0]
        
        return defaults

    async def _calculate_application_similarity(
        self,
        app1: ApplicationProfile,
        app2: ApplicationProfile,
        method: SimilarityMethod
    ) -> float:
        """Calculate similarity between two applications"""
        
        if method == SimilarityMethod.TECHNOLOGY_STACK:
            return self._calculate_technology_similarity(app1, app2)
        elif method == SimilarityMethod.ARCHITECTURE_PATTERN:
            return self._calculate_architecture_similarity(app1, app2)
        elif method == SimilarityMethod.BUSINESS_CONTEXT:
            return self._calculate_business_similarity(app1, app2)
        elif method == SimilarityMethod.COMBINED:
            tech_sim = self._calculate_technology_similarity(app1, app2)
            arch_sim = self._calculate_architecture_similarity(app1, app2)
            biz_sim = self._calculate_business_similarity(app1, app2)
            return (tech_sim * 0.4 + arch_sim * 0.3 + biz_sim * 0.3)
        
        return 0.0

    def _calculate_technology_similarity(self, app1: ApplicationProfile, app2: ApplicationProfile) -> float:
        """Calculate technology stack similarity"""
        
        set1 = set(tech.lower() for tech in app1.technology_stack)
        set2 = set(tech.lower() for tech in app2.technology_stack)
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _calculate_architecture_similarity(self, app1: ApplicationProfile, app2: ApplicationProfile) -> float:
        """Calculate architecture pattern similarity"""
        return 1.0 if app1.architecture_pattern == app2.architecture_pattern else 0.0

    def _calculate_business_similarity(self, app1: ApplicationProfile, app2: ApplicationProfile) -> float:
        """Calculate business context similarity"""
        
        criticality_sim = 1.0 if app1.business_criticality == app2.business_criticality else 0.5
        
        compliance_set1 = set(app1.compliance_requirements)
        compliance_set2 = set(app2.compliance_requirements)
        compliance_sim = len(compliance_set1.intersection(compliance_set2)) / max(len(compliance_set1.union(compliance_set2)), 1)
        
        industry_sim = 1.0 if app1.industry_sector == app2.industry_sector else 0.0
        
        return (criticality_sim * 0.4 + compliance_sim * 0.4 + industry_sim * 0.2)

    async def _find_relevant_templates(self, application: ApplicationProfile) -> List[Tuple[str, float]]:
        """Find relevant templates for an application"""
        
        relevant_templates = []
        
        for template in self._templates.values():
            if template.status != TemplateStatus.ACTIVE:
                continue
            
            relevance_score = await self._calculate_template_relevance(application, template)
            
            if relevance_score > 0.3:
                relevant_templates.append((template.template_id, relevance_score))
        
        relevant_templates.sort(key=lambda x: x[1], reverse=True)
        return relevant_templates[:5]

    async def _calculate_template_relevance(
        self,
        application: ApplicationProfile,
        template: ApplicationTemplate
    ) -> float:
        """Calculate how relevant a template is for an application"""
        
        criteria = template.similarity_criteria
        relevance = 0.0
        
        # Technology stack relevance
        if 'technology_stack' in criteria:
            template_techs = set(tech.lower() for tech in criteria['technology_stack'])
            app_techs = set(tech.lower() for tech in application.technology_stack)
            tech_overlap = len(template_techs.intersection(app_techs)) / max(len(template_techs), 1)
            relevance += tech_overlap * 0.4
        
        # Architecture pattern relevance
        if 'architecture_pattern' in criteria:
            if application.architecture_pattern in criteria['architecture_pattern']:
                relevance += 0.3
        
        # Compliance relevance
        if 'compliance_requirements' in criteria:
            template_compliance = set(criteria['compliance_requirements'])
            app_compliance = set(application.compliance_requirements)
            compliance_overlap = len(template_compliance.intersection(app_compliance)) / max(len(template_compliance), 1)
            relevance += compliance_overlap * 0.3
        
        # Apply template weight
        weight = criteria.get('weight', 1.0)
        return relevance * weight

    async def _generate_form_sections_from_template(
        self,
        template: ApplicationTemplate,
        application_id: UUID
    ) -> List[FormSection]:
        """Generate form sections from template"""
        
        sections_dict = {
            'infrastructure': FormSection(
                id='infrastructure',
                title='Infrastructure Details',
                description='Infrastructure and platform information',
                fields=[],
                order=1
            ),
            'application': FormSection(
                id='application',
                title='Application Details',
                description='Application architecture and technology details',
                fields=[],
                order=2
            ),
            'business': FormSection(
                id='business',
                title='Business Context',
                description='Business criticality and stakeholder information',
                fields=[],
                order=3
            )
        }
        
        # Convert template fields to form fields
        for template_field in template.fields:
            # Determine section based on field type
            section_id = 'application'  # Default
            if template_field.critical_attribute in ['os_version', 'specifications', 'network_config', 'virtualization']:
                section_id = 'infrastructure'
            elif template_field.critical_attribute in ['business_criticality', 'compliance_constraints', 'stakeholder_impact']:
                section_id = 'business'
            
            # Create form field from template field
            form_field = FormField(
                id=template_field.field_id,
                label=template_field.label,
                field_type=FieldType(template_field.field_type),
                critical_attribute=template_field.critical_attribute,
                description=template_field.help_text,
                section=section_id,
                order=len(sections_dict[section_id].fields),
                help_text=template_field.help_text
            )
            
            sections_dict[section_id].fields.append(form_field)
        
        # Filter out empty sections
        sections = [section for section in sections_dict.values() if section.fields]
        
        return sections

    async def _apply_user_overrides(
        self,
        sections: List[FormSection],
        overrides: Dict[str, Any]
    ) -> List[FormSection]:
        """Apply user overrides to form sections"""
        
        for section in sections:
            for field in section.fields:
                if field.id in overrides:
                    # Apply override to field (e.g., change default value, validation, etc.)
                    override_value = overrides[field.id]
                    if isinstance(override_value, dict):
                        if 'default_value' in override_value:
                            field.placeholder = str(override_value['default_value'])
                        if 'required' in override_value:
                            # Update validation rules
                            pass
        
        return sections

    async def _generate_template_validation_rules(self, applications: List[ApplicationProfile]) -> Dict[str, Any]:
        """Generate validation rules for template"""
        return {}

    async def _calculate_template_effectiveness(self, applications: List[ApplicationProfile]) -> float:
        """Calculate template effectiveness based on source applications"""
        if not applications:
            return 0.5
        
        avg_quality = sum(app.collection_quality_score for app in applications) / len(applications)
        return min(1.0, avg_quality + 0.1)  # Slight boost for being template-based

    def _calculate_similarity_confidence(
        self,
        similar_apps: List[Tuple[UUID, float]],
        target_app: ApplicationProfile
    ) -> float:
        """Calculate confidence in similarity results"""
        if not similar_apps:
            return 0.0
        
        # Higher confidence with more similar apps and higher similarity scores
        avg_similarity = sum(score for _, score in similar_apps) / len(similar_apps)
        count_factor = min(1.0, len(similar_apps) / 5.0)  # Max confidence with 5+ similar apps
        
        return avg_similarity * count_factor