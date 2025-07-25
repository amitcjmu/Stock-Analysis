"""
Adaptive Form Generation Service

Generates dynamic forms based on gap analysis results, application context,
and the 22 critical attributes framework defined in the ADCS specifications.

Agent Team B3 - Task B3.1
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

# QualityAssessmentService will be lazily imported when needed


class FieldType(str, Enum):
    """Form field types supported by the adaptive form system"""

    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTISELECT = "multiselect"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    FILE = "file"


class ValidationRule(str, Enum):
    """Validation rules for form fields"""

    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    EMAIL_FORMAT = "email"
    URL_FORMAT = "url"
    CONDITIONAL_REQUIRED = "conditional_required"


@dataclass
class ConditionalDisplayRule:
    """Rules for conditional field display based on other field values"""

    dependent_field: str
    condition: str  # 'equals', 'contains', 'not_equals', 'in', 'not_in'
    values: List[str]
    required_when_visible: bool = False


@dataclass
class FieldValidation:
    """Validation configuration for a form field"""

    rules: List[ValidationRule]
    parameters: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class FormField:
    """Configuration for a dynamic form field"""

    id: str
    label: str
    field_type: FieldType
    critical_attribute: str  # Maps to one of the 22 critical attributes
    description: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None  # For select/radio fields
    validation: Optional[FieldValidation] = None
    conditional_display: Optional[ConditionalDisplayRule] = None
    section: str = "general"
    order: int = 0
    help_text: Optional[str] = None
    business_impact_score: float = 0.0  # Impact on 6R decision confidence


@dataclass
class FormSection:
    """Logical grouping of related form fields"""

    id: str
    title: str
    description: Optional[str] = None
    fields: List[FormField] = None
    order: int = 0
    required_fields_count: int = 0
    completion_weight: float = 0.0  # Weight in overall form completion


@dataclass
class AdaptiveForm:
    """Complete adaptive form configuration"""

    id: str
    title: str
    application_id: UUID
    gap_analysis_id: UUID
    sections: List[FormSection]
    total_fields: int
    required_fields: int
    estimated_completion_time: int  # minutes
    confidence_impact_score: float  # Expected confidence improvement
    created_at: datetime
    updated_at: datetime


@dataclass
class GapAnalysisResult:
    """Gap analysis result structure"""

    critical_gaps: List[Dict[str, Any]]
    completeness_score: float
    missing_attributes: List[str]
    business_context: Dict[str, Any]
    application_metadata: Dict[str, Any]


@dataclass
class ApplicationContext:
    """Application context for form adaptation"""

    application_id: UUID
    technology_stack: List[str]
    architecture_pattern: str
    detected_patterns: List[str]
    business_criticality: str
    compliance_requirements: List[str]
    related_applications: List[UUID]


class AdaptiveFormService:
    """Service for generating adaptive forms based on gap analysis and application context"""

    # Critical Attributes Framework (22 attributes as defined in specifications)
    CRITICAL_ATTRIBUTES_CONFIG = {
        # Infrastructure Attributes (6)
        "os_version": {
            "category": "infrastructure",
            "weight": 0.05,
            "label": "Operating System & Version",
            "description": "Operating system type and version information",
            "field_type": FieldType.SELECT,
            "business_impact": "Required for compatibility assessment and migration strategy",
        },
        "specifications": {
            "category": "infrastructure",
            "weight": 0.05,
            "label": "CPU/Memory/Storage Specifications",
            "description": "Hardware specifications and resource requirements",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Required for rightsizing and cost optimization",
        },
        "network_config": {
            "category": "infrastructure",
            "weight": 0.04,
            "label": "Network Configuration",
            "description": "Network topology, ports, protocols, and connectivity requirements",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Required for connectivity planning and security assessment",
        },
        "virtualization": {
            "category": "infrastructure",
            "weight": 0.04,
            "label": "Virtualization Platform",
            "description": "Current virtualization technology and configuration",
            "field_type": FieldType.SELECT,
            "business_impact": "Required for migration strategy selection",
        },
        "performance_baseline": {
            "category": "infrastructure",
            "weight": 0.04,
            "label": "Performance Baseline",
            "description": "Current performance metrics and benchmarks",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Required for performance validation post-migration",
        },
        "availability_requirements": {
            "category": "infrastructure",
            "weight": 0.03,
            "label": "Availability/Uptime Requirements",
            "description": "SLA requirements and uptime expectations",
            "field_type": FieldType.SELECT,
            "business_impact": "Required for SLA planning and architecture decisions",
        },
        # Application Attributes (8)
        "technology_stack": {
            "category": "application",
            "weight": 0.08,
            "label": "Technology Stack",
            "description": "Programming languages, frameworks, runtime versions",
            "field_type": FieldType.MULTISELECT,
            "business_impact": "Critical for modernization path selection",
        },
        "architecture_pattern": {
            "category": "application",
            "weight": 0.07,
            "label": "Architecture Pattern",
            "description": "Application architecture classification",
            "field_type": FieldType.RADIO,
            "business_impact": "Determines refactoring vs replatforming approach",
        },
        "integration_dependencies": {
            "category": "application",
            "weight": 0.06,
            "label": "Integration Dependencies",
            "description": "External APIs, databases, message queues, and service dependencies",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Critical for dependency mapping and migration ordering",
        },
        "data_characteristics": {
            "category": "application",
            "weight": 0.06,
            "label": "Data Volume and Characteristics",
            "description": "Database size, file storage, data types, and growth patterns",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Required for storage planning and data migration strategy",
        },
        "user_load_patterns": {
            "category": "application",
            "weight": 0.05,
            "label": "User Load Patterns",
            "description": "Concurrent users, peak usage times, seasonal patterns",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Required for capacity planning and scaling strategy",
        },
        "business_logic_complexity": {
            "category": "application",
            "weight": 0.05,
            "label": "Custom Business Logic Complexity",
            "description": "Proprietary algorithms, complex business rules, custom workflows",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Determines refactoring effort and cloud-native potential",
        },
        "configuration_complexity": {
            "category": "application",
            "weight": 0.04,
            "label": "Configuration Complexity",
            "description": "Environment-specific settings, feature flags, deployment configurations",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Impacts containerization and automation potential",
        },
        "security_requirements": {
            "category": "application",
            "weight": 0.04,
            "label": "Security and Compliance Requirements",
            "description": "Security protocols, regulatory constraints, data protection requirements",
            "field_type": FieldType.MULTISELECT,
            "business_impact": "Determines cloud security posture and compliance validation",
        },
        # Business Context Attributes (4)
        "business_criticality": {
            "category": "business",
            "weight": 0.08,
            "label": "Business Criticality Score",
            "description": "Revenue impact, operational importance, and business dependency",
            "field_type": FieldType.SELECT,
            "business_impact": "Determines migration priority and risk tolerance",
        },
        "change_tolerance": {
            "category": "business",
            "weight": 0.05,
            "label": "Change Tolerance",
            "description": "User adaptability, training requirements, change management needs",
            "field_type": FieldType.SELECT,
            "business_impact": "Influences modernization approach and timeline",
        },
        "compliance_constraints": {
            "category": "business",
            "weight": 0.04,
            "label": "Compliance and Regulatory Constraints",
            "description": "Industry-specific requirements, regulatory compliance needs",
            "field_type": FieldType.MULTISELECT,
            "business_impact": "Determines cloud region and compliance validation requirements",
        },
        "stakeholder_impact": {
            "category": "business",
            "weight": 0.03,
            "label": "Stakeholder Impact Analysis",
            "description": "User base size, organizational dependencies, communication needs",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Influences change management and communication strategy",
        },
        # Technical Debt Attributes (4)
        "code_quality": {
            "category": "technical_debt",
            "weight": 0.03,
            "label": "Code Quality Metrics",
            "description": "Maintainability index, technical debt ratio, code coverage",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Determines refactoring effort and modernization feasibility",
        },
        "security_vulnerabilities": {
            "category": "technical_debt",
            "weight": 0.03,
            "label": "Security Vulnerability Assessment",
            "description": "CVE count, severity classification, security scan results",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Critical for security posture and remediation planning",
        },
        "eol_technology": {
            "category": "technical_debt",
            "weight": 0.02,
            "label": "End-of-Life Technology Assessment",
            "description": "Unsupported versions, deprecated features, legacy components",
            "field_type": FieldType.TEXTAREA,
            "business_impact": "Determines modernization urgency and approach",
        },
        "documentation_quality": {
            "category": "technical_debt",
            "weight": 0.02,
            "label": "Documentation Quality",
            "description": "Availability, accuracy, completeness of technical documentation",
            "field_type": FieldType.SELECT,
            "business_impact": "Impacts migration complexity and knowledge transfer needs",
        },
    }

    # Field options for common select/radio fields
    FIELD_OPTIONS = {
        "os_version": [
            {"value": "windows_server_2019", "label": "Windows Server 2019"},
            {"value": "windows_server_2016", "label": "Windows Server 2016"},
            {"value": "windows_server_2012", "label": "Windows Server 2012"},
            {"value": "ubuntu_20.04", "label": "Ubuntu 20.04 LTS"},
            {"value": "ubuntu_18.04", "label": "Ubuntu 18.04 LTS"},
            {"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"},
            {"value": "rhel_7", "label": "Red Hat Enterprise Linux 7"},
            {"value": "centos_8", "label": "CentOS 8"},
            {"value": "centos_7", "label": "CentOS 7"},
            {"value": "other", "label": "Other (specify in description)"},
        ],
        "virtualization": [
            {"value": "vmware_vsphere", "label": "VMware vSphere"},
            {"value": "hyper_v", "label": "Microsoft Hyper-V"},
            {"value": "kvm", "label": "KVM"},
            {"value": "xen", "label": "Citrix Xen"},
            {"value": "physical", "label": "Physical Server"},
            {"value": "cloud_vm", "label": "Cloud Virtual Machine"},
            {"value": "container", "label": "Containerized"},
            {"value": "other", "label": "Other"},
        ],
        "availability_requirements": [
            {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
            {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
            {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
            {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
            {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
            {"value": "best_effort", "label": "Best Effort (No SLA)"},
        ],
        "technology_stack": [
            {"value": "java", "label": "Java"},
            {"value": "dotnet", "label": ".NET Framework"},
            {"value": "dotnet_core", "label": ".NET Core"},
            {"value": "python", "label": "Python"},
            {"value": "nodejs", "label": "Node.js"},
            {"value": "php", "label": "PHP"},
            {"value": "ruby", "label": "Ruby"},
            {"value": "go", "label": "Go"},
            {"value": "rust", "label": "Rust"},
            {"value": "cpp", "label": "C++"},
            {"value": "oracle", "label": "Oracle Database"},
            {"value": "sql_server", "label": "SQL Server"},
            {"value": "mysql", "label": "MySQL"},
            {"value": "postgresql", "label": "PostgreSQL"},
            {"value": "mongodb", "label": "MongoDB"},
            {"value": "redis", "label": "Redis"},
            {"value": "elasticsearch", "label": "Elasticsearch"},
        ],
        "architecture_pattern": [
            {"value": "monolith", "label": "Monolithic Application"},
            {"value": "microservices", "label": "Microservices Architecture"},
            {"value": "soa", "label": "Service-Oriented Architecture (SOA)"},
            {"value": "layered", "label": "Layered/N-Tier Architecture"},
            {"value": "event_driven", "label": "Event-Driven Architecture"},
            {"value": "serverless", "label": "Serverless/Function-based"},
            {"value": "hybrid", "label": "Hybrid Architecture"},
        ],
        "business_criticality": [
            {
                "value": "mission_critical",
                "label": "Mission Critical (Revenue Generating)",
            },
            {
                "value": "business_critical",
                "label": "Business Critical (Operations Dependent)",
            },
            {"value": "important", "label": "Important (Business Supporting)"},
            {"value": "standard", "label": "Standard (Operational Support)"},
            {"value": "low", "label": "Low Priority (Development/Testing)"},
        ],
        "change_tolerance": [
            {
                "value": "high",
                "label": "High (Users adapt quickly, minimal training needed)",
            },
            {
                "value": "medium",
                "label": "Medium (Some training required, moderate adaptation)",
            },
            {
                "value": "low",
                "label": "Low (Significant training needed, resistance to change)",
            },
            {
                "value": "very_low",
                "label": "Very Low (Change averse, extensive change management)",
            },
        ],
        "security_requirements": [
            {"value": "pci_dss", "label": "PCI DSS"},
            {"value": "hipaa", "label": "HIPAA"},
            {"value": "sox", "label": "SOX"},
            {"value": "gdpr", "label": "GDPR"},
            {"value": "iso_27001", "label": "ISO 27001"},
            {"value": "fedramp", "label": "FedRAMP"},
            {"value": "pii", "label": "PII Data Protection"},
            {"value": "encryption_rest", "label": "Encryption at Rest"},
            {"value": "encryption_transit", "label": "Encryption in Transit"},
            {"value": "multi_factor_auth", "label": "Multi-Factor Authentication"},
        ],
        "compliance_constraints": [
            {"value": "healthcare", "label": "Healthcare (HIPAA, FDA)"},
            {"value": "financial", "label": "Financial Services (PCI DSS, SOX)"},
            {"value": "government", "label": "Government (FedRAMP, FISMA)"},
            {"value": "manufacturing", "label": "Manufacturing (ITAR, EAR)"},
            {"value": "retail", "label": "Retail (PCI DSS)"},
            {"value": "education", "label": "Education (FERPA)"},
            {"value": "data_residency", "label": "Data Residency Requirements"},
            {
                "value": "cross_border",
                "label": "Cross-Border Data Transfer Restrictions",
            },
        ],
        "documentation_quality": [
            {
                "value": "excellent",
                "label": "Excellent (Comprehensive, up-to-date, detailed)",
            },
            {"value": "good", "label": "Good (Mostly complete, minor gaps)"},
            {"value": "fair", "label": "Fair (Basic documentation, some outdated)"},
            {"value": "poor", "label": "Poor (Minimal documentation, mostly outdated)"},
            {"value": "none", "label": "None (No documentation available)"},
        ],
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._quality_service = None

    @property
    def quality_service(self):
        """Lazy initialization of QualityAssessmentService with request context."""
        if self._quality_service is None:
            try:
                # For now, return None since we don't have context management set up
                # This prevents request-scoped context issues during class instantiation
                self.logger.warning(
                    "QualityAssessmentService not initialized - requires proper context setup"
                )
                return None
            except Exception as e:
                self.logger.warning(
                    f"Could not initialize QualityAssessmentService with context: {e}"
                )
                return None
        return self._quality_service

    def generate_adaptive_form(
        self, gap_analysis: GapAnalysisResult, application_context: ApplicationContext
    ) -> AdaptiveForm:
        """
        Generate an adaptive form based on gap analysis and application context.

        This is the core implementation of B3.1 - Adaptive form generation and rendering.
        The form adapts based on:
        1. Gap analysis results (which critical attributes are missing)
        2. Application context (technology stack, architecture, business context)
        3. Business rules and conditional logic
        """
        self.logger.info(
            f"Generating adaptive form for application {application_context.application_id}"
        )

        # Generate form sections based on missing critical attributes
        sections = self._generate_form_sections(gap_analysis, application_context)

        # Calculate form metadata
        total_fields = sum(len(section.fields) for section in sections)
        required_fields = sum(
            len(
                [
                    f
                    for f in section.fields
                    if self._is_field_required(f, application_context)
                ]
            )
            for section in sections
        )

        # Estimate completion time (2 minutes per field + 5 minutes base)
        estimated_time = max(5, total_fields * 2)

        # Calculate confidence impact score
        confidence_impact = self._calculate_confidence_impact(gap_analysis, sections)

        form = AdaptiveForm(
            id=f"form_{application_context.application_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=f"Data Collection for {application_context.application_id}",
            application_id=application_context.application_id,
            gap_analysis_id=UUID(
                str(
                    gap_analysis.critical_gaps[0].get(
                        "id", "00000000-0000-0000-0000-000000000000"
                    )
                )
            ),
            sections=sections,
            total_fields=total_fields,
            required_fields=required_fields,
            estimated_completion_time=estimated_time,
            confidence_impact_score=confidence_impact,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.logger.info(
            f"Generated adaptive form with {total_fields} fields across {len(sections)} sections"
        )
        return form

    def _generate_form_sections(
        self, gap_analysis: GapAnalysisResult, application_context: ApplicationContext
    ) -> List[FormSection]:
        """Generate form sections based on missing critical attributes"""

        sections_dict = {
            "infrastructure": FormSection(
                id="infrastructure",
                title="Infrastructure Details",
                description="Information about the underlying infrastructure and platform",
                fields=[],
                order=1,
            ),
            "application": FormSection(
                id="application",
                title="Application Architecture",
                description="Details about the application design, technology, and dependencies",
                fields=[],
                order=2,
            ),
            "business": FormSection(
                id="business",
                title="Business Context",
                description="Business impact, criticality, and stakeholder information",
                fields=[],
                order=3,
            ),
            "technical_debt": FormSection(
                id="technical_debt",
                title="Technical Assessment",
                description="Code quality, security, and technical debt evaluation",
                fields=[],
                order=4,
            ),
        }

        # Generate fields for each missing critical attribute
        field_order = 0
        for gap in gap_analysis.critical_gaps:
            attribute_name = gap.get("attribute_name")
            if attribute_name in self.CRITICAL_ATTRIBUTES_CONFIG:
                field = self._generate_field_for_attribute(
                    attribute_name, gap, application_context, field_order
                )
                if field:
                    category = self.CRITICAL_ATTRIBUTES_CONFIG[attribute_name][
                        "category"
                    ]
                    sections_dict[category].fields.append(field)
                    field_order += 1

        # Filter out empty sections and sort by order
        sections = [section for section in sections_dict.values() if section.fields]
        sections.sort(key=lambda x: x.order)

        # Update section metadata
        for section in sections:
            section.required_fields_count = len(
                [
                    f
                    for f in section.fields
                    if self._is_field_required(f, application_context)
                ]
            )
            section.completion_weight = len(section.fields) / sum(
                len(s.fields) for s in sections
            )

        return sections

    def _generate_field_for_attribute(
        self,
        attribute_name: str,
        gap: Dict[str, Any],
        application_context: ApplicationContext,
        order: int,
    ) -> Optional[FormField]:
        """Generate a form field for a specific critical attribute"""

        config = self.CRITICAL_ATTRIBUTES_CONFIG[attribute_name]

        # Base field configuration
        field = FormField(
            id=f"field_{attribute_name}",
            label=config["label"],
            field_type=config["field_type"],
            critical_attribute=attribute_name,
            description=config["description"],
            section=config["category"],
            order=order,
            help_text=config["business_impact"],
            business_impact_score=config["weight"],
        )

        # Add field options for select/radio/multiselect fields
        if field.field_type in [
            FieldType.SELECT,
            FieldType.RADIO,
            FieldType.MULTISELECT,
        ]:
            if attribute_name in self.FIELD_OPTIONS:
                field.options = self.FIELD_OPTIONS[attribute_name]

        # Customize field based on application context
        field = self._customize_field_for_context(field, application_context)

        # Add validation rules
        field.validation = self._generate_field_validation(field, application_context)

        # Add conditional display rules if applicable
        field.conditional_display = self._generate_conditional_display(
            field, application_context
        )

        return field

    def _customize_field_for_context(
        self, field: FormField, application_context: ApplicationContext
    ) -> FormField:
        """Customize field based on application context and detected patterns"""

        # Technology stack customization
        if field.critical_attribute == "technology_stack":
            # Filter options based on detected patterns
            if field.options and application_context.detected_patterns:
                filtered_options = []
                for pattern in application_context.detected_patterns:
                    if pattern == "web_application":
                        filtered_options.extend(
                            [
                                opt
                                for opt in field.options
                                if opt["value"]
                                in ["java", "dotnet", "nodejs", "python", "php"]
                            ]
                        )
                    elif pattern == "database":
                        filtered_options.extend(
                            [
                                opt
                                for opt in field.options
                                if opt["value"]
                                in [
                                    "oracle",
                                    "sql_server",
                                    "mysql",
                                    "postgresql",
                                    "mongodb",
                                ]
                            ]
                        )
                if filtered_options:
                    field.options = filtered_options

        # Architecture pattern customization
        elif field.critical_attribute == "architecture_pattern":
            if "microservices" in application_context.detected_patterns:
                field.description += " (Microservices architecture detected)"
            elif "monolith" in application_context.detected_patterns:
                field.description += " (Monolithic architecture detected)"

        # Security requirements based on compliance
        elif field.critical_attribute == "security_requirements":
            if application_context.compliance_requirements:
                # Pre-select relevant compliance options
                requirements = ", ".join(application_context.compliance_requirements)
                field.description += (
                    f" (Compliance requirements detected: {requirements})"
                )

        # Business criticality based on existing assessment
        elif field.critical_attribute == "business_criticality":
            if application_context.business_criticality:
                field.description += (
                    f" (Current assessment: {application_context.business_criticality})"
                )

        return field

    def _generate_field_validation(
        self, field: FormField, application_context: ApplicationContext
    ) -> FieldValidation:
        """Generate validation rules for a field"""

        rules = []
        parameters = {}

        # Required field determination
        if self._is_field_required(field, application_context):
            rules.append(ValidationRule.REQUIRED)

        # Field-specific validation
        if field.field_type == FieldType.EMAIL:
            rules.append(ValidationRule.EMAIL_FORMAT)
        elif field.field_type == FieldType.URL:
            rules.append(ValidationRule.URL_FORMAT)
        elif field.field_type == FieldType.TEXTAREA:
            rules.append(ValidationRule.MIN_LENGTH)
            parameters["min_length"] = 10
            rules.append(ValidationRule.MAX_LENGTH)
            parameters["max_length"] = 2000
        elif field.field_type == FieldType.TEXT:
            rules.append(ValidationRule.MAX_LENGTH)
            parameters["max_length"] = 500

        # Critical attribute specific validation
        if field.critical_attribute in [
            "specifications",
            "network_config",
            "integration_dependencies",
        ]:
            # These are high-impact fields requiring detailed input
            rules.append(ValidationRule.MIN_LENGTH)
            parameters["min_length"] = 50

        return FieldValidation(
            rules=rules,
            parameters=parameters,
            error_message=self._generate_validation_error_message(
                field.critical_attribute
            ),
        )

    def _generate_conditional_display(
        self, field: FormField, application_context: ApplicationContext
    ) -> Optional[ConditionalDisplayRule]:
        """Generate conditional display rules for fields"""

        # Example: Show AD integration questions for Windows environments
        if field.critical_attribute == "integration_dependencies":
            return ConditionalDisplayRule(
                dependent_field="field_os_version",
                condition="contains",
                values=["windows"],
                required_when_visible=True,
            )

        # Show container-specific questions for microservices
        elif field.critical_attribute == "virtualization":
            return ConditionalDisplayRule(
                dependent_field="field_architecture_pattern",
                condition="equals",
                values=["microservices"],
                required_when_visible=True,
            )

        # Show compliance details when specific requirements are selected
        elif field.critical_attribute == "compliance_constraints":
            return ConditionalDisplayRule(
                dependent_field="field_security_requirements",
                condition="contains",
                values=["pci_dss", "hipaa", "sox", "gdpr"],
                required_when_visible=True,
            )

        return None

    def _is_field_required(
        self, field: FormField, application_context: ApplicationContext
    ) -> bool:
        """Determine if a field is required based on business context"""

        # High business impact attributes are always required
        if field.business_impact_score >= 0.05:
            return True

        # Mission critical applications require more comprehensive data
        if application_context.business_criticality == "mission_critical":
            return field.business_impact_score >= 0.03

        # Compliance requirements make certain fields mandatory
        if application_context.compliance_requirements:
            compliance_required_fields = [
                "security_requirements",
                "compliance_constraints",
                "data_characteristics",
                "network_config",
            ]
            if field.critical_attribute in compliance_required_fields:
                return True

        return field.business_impact_score >= 0.04

    def _calculate_confidence_impact(
        self, gap_analysis: GapAnalysisResult, sections: List[FormSection]
    ) -> float:
        """Calculate expected confidence score improvement from form completion"""

        total_weight = 0.0
        for section in sections:
            for field in section.fields:
                total_weight += field.business_impact_score

        # Confidence improvement is the sum of weights of missing attributes
        # multiplied by expected completion rate (assume 85% completion)
        expected_improvement = total_weight * 0.85

        return min(expected_improvement, 1.0)

    def _generate_validation_error_message(self, attribute_name: str) -> str:
        """Generate contextual validation error messages"""

        messages = {
            "os_version": "Operating system information is required for compatibility assessment",
            "technology_stack": "Technology stack details are critical for migration planning",
            "business_criticality": "Business criticality assessment is required for prioritization",
            "security_requirements": "Security requirements must be specified for compliance validation",
            "integration_dependencies": "Integration details are required for dependency analysis",
        }

        return messages.get(
            attribute_name, "This field is required for accurate assessment"
        )

    def to_dict(self, form: AdaptiveForm) -> Dict[str, Any]:
        """Convert AdaptiveForm to dictionary for API response"""
        return asdict(form)

    def to_json_schema(self, form: AdaptiveForm) -> Dict[str, Any]:
        """Convert AdaptiveForm to JSON Schema for frontend validation"""

        properties = {}
        required = []

        for section in form.sections:
            for field in section.fields:
                field_schema = {
                    "type": self._get_json_schema_type(field.field_type),
                    "title": field.label,
                    "description": field.description,
                }

                if field.options:
                    field_schema["enum"] = [opt["value"] for opt in field.options]
                    field_schema["enumNames"] = [opt["label"] for opt in field.options]

                if field.validation:
                    for rule in field.validation.rules:
                        if rule == ValidationRule.REQUIRED:
                            required.append(field.id)
                        elif rule == ValidationRule.MIN_LENGTH:
                            field_schema["minLength"] = field.validation.parameters.get(
                                "min_length", 1
                            )
                        elif rule == ValidationRule.MAX_LENGTH:
                            field_schema["maxLength"] = field.validation.parameters.get(
                                "max_length", 1000
                            )
                        elif rule == ValidationRule.PATTERN:
                            field_schema["pattern"] = field.validation.parameters.get(
                                "pattern", ""
                            )

                properties[field.id] = field_schema

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "title": form.title,
        }

    def _get_json_schema_type(self, field_type: FieldType) -> str:
        """Map FieldType to JSON Schema type"""
        mapping = {
            FieldType.TEXT: "string",
            FieldType.TEXTAREA: "string",
            FieldType.SELECT: "string",
            FieldType.MULTISELECT: "array",
            FieldType.RADIO: "string",
            FieldType.CHECKBOX: "boolean",
            FieldType.NUMBER: "number",
            FieldType.DATE: "string",
            FieldType.EMAIL: "string",
            FieldType.URL: "string",
            FieldType.FILE: "string",
        }
        return mapping.get(field_type, "string")
