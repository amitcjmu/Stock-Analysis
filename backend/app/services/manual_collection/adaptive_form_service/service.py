"""
Adaptive Form Service Main Implementation
"""

import logging
import uuid
from datetime import datetime
from typing import List

from .config import CRITICAL_ATTRIBUTES_CONFIG, FIELD_OPTIONS
from .enums import FieldType, ValidationRule
from .form_creation import FormCreationMixin
from .models import (
    AdaptiveForm,
    ApplicationContext,
    ConditionalDisplayRule,
    FieldValidation,
    FormField,
    FormSection,
    GapAnalysisResult,
)

logger = logging.getLogger(__name__)


class AdaptiveFormService(FormCreationMixin):
    """Service for generating adaptive forms based on gap analysis and application context"""

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

        # Calculate estimated completion time (2-3 minutes per field on average)
        estimated_time = max(5, min(30, int(round(total_fields * 2.5))))

        # Calculate confidence impact score
        confidence_impact = self._calculate_confidence_impact(sections)

        # Create adaptive form
        form = AdaptiveForm(
            id=f"adaptive_form_{uuid.uuid4().hex[:8]}",
            title=f"Data Collection Form - {application_context.business_criticality.title()} Priority",
            application_id=application_context.application_id,
            gap_analysis_id=uuid.uuid4(),  # This should come from the actual gap analysis
            sections=sections,
            total_fields=total_fields,
            required_fields=required_fields,
            estimated_completion_time=int(estimated_time),
            confidence_impact_score=confidence_impact,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.logger.info(
            f"Generated adaptive form with {len(sections)} sections, "
            f"{total_fields} total fields, {required_fields} required fields"
        )

        return form

    def _generate_form_sections(
        self, gap_analysis: GapAnalysisResult, application_context: ApplicationContext
    ) -> List[FormSection]:
        """Generate form sections based on missing critical attributes and categories"""

        sections = []
        missing_by_category = {}

        # Group missing attributes by category
        for attr_name in gap_analysis.missing_attributes:
            if attr_name in CRITICAL_ATTRIBUTES_CONFIG:
                config = CRITICAL_ATTRIBUTES_CONFIG[attr_name]
                category = config["category"]

                if category not in missing_by_category:
                    missing_by_category[category] = []

                missing_by_category[category].append(attr_name)

        # Create sections for each category with missing attributes
        section_order = 0
        category_titles = {
            "infrastructure": "Infrastructure & Environment",
            "application": "Application Details",
            "business": "Business Context",
            "technical_debt": "Technical Assessment",
        }

        for category, attributes in missing_by_category.items():
            if not attributes:  # Skip empty categories
                continue

            section_title = category_titles.get(category, category.title())
            section_id = f"{category}_section"

            # Generate fields for this section
            fields = []
            for attr_name in attributes:
                field = self._generate_field_for_attribute(
                    attr_name, application_context, len(fields)
                )
                if field:
                    fields.append(field)

            if fields:  # Only create section if it has fields
                section = FormSection(
                    id=section_id,
                    title=section_title,
                    description=f"Please provide information about {section_title.lower()}",
                    fields=fields,
                    order=section_order,
                    required_fields_count=len(
                        [
                            f
                            for f in fields
                            if self._is_field_required(f, application_context)
                        ]
                    ),
                    completion_weight=sum(
                        CRITICAL_ATTRIBUTES_CONFIG.get(f.critical_attribute, {}).get(
                            "weight", 0.0
                        )
                        for f in fields
                    ),
                )
                sections.append(section)
                section_order += 1

        return sections

    def _generate_field_for_attribute(
        self,
        attribute_name: str,
        application_context: ApplicationContext,
        field_order: int,
    ) -> FormField:
        """Generate a form field for a specific critical attribute"""

        if attribute_name not in CRITICAL_ATTRIBUTES_CONFIG:
            self.logger.warning(f"Unknown critical attribute: {attribute_name}")
            return None

        config = CRITICAL_ATTRIBUTES_CONFIG[attribute_name]

        # Create base field
        field = FormField(
            id=f"field_{attribute_name}",
            label=config["label"],
            field_type=config["field_type"],
            critical_attribute=attribute_name,
            description=config["description"],
            section=config["category"],
            order=field_order,
            help_text=f"Business Impact: {config['business_impact']}",
            business_impact_score=config["weight"],
        )

        # Add field options for select/multiselect/radio fields
        if config["field_type"] in [
            FieldType.SELECT,
            FieldType.MULTISELECT,
            FieldType.RADIO,
        ]:
            if attribute_name in FIELD_OPTIONS:
                field.options = FIELD_OPTIONS[attribute_name]

        # Customize field based on application context
        field = self._customize_field_for_context(field, application_context)

        # Generate validation rules
        field.validation = self._generate_field_validation(field, application_context)

        # Generate conditional display rules
        field.conditional_display = self._generate_conditional_display(
            field, application_context
        )

        return field

    def _customize_field_for_context(
        self, field: FormField, application_context: ApplicationContext
    ) -> FormField:
        """Customize field based on application context and detected patterns"""

        # Customize placeholder and help text based on detected technology stack
        if field.critical_attribute == "technology_stack":
            detected_techs = []
            for tech in application_context.technology_stack:
                if tech.lower() in ["java", "python", "nodejs", "dotnet"]:
                    detected_techs.append(tech)

            if detected_techs:
                field.placeholder = f"Detected: {', '.join(detected_techs)}. Add any missing technologies."
            else:
                field.placeholder = "e.g., Java 11, Spring Boot, PostgreSQL, Redis"

        elif field.critical_attribute == "architecture_pattern":
            if application_context.architecture_pattern:
                field.placeholder = (
                    f"Current: {application_context.architecture_pattern}"
                )
            else:
                field.placeholder = "Select the architecture pattern that best describes this application"

        elif field.critical_attribute == "business_criticality":
            if application_context.business_criticality:
                # Pre-select based on context
                field.placeholder = (
                    f"Suggested: {application_context.business_criticality}"
                )

        elif field.critical_attribute == "compliance_constraints":
            if application_context.compliance_requirements:
                detected_reqs = application_context.compliance_requirements
                field.placeholder = f"Detected requirements: {', '.join(detected_reqs)}"
            else:
                field.placeholder = "Select all applicable compliance requirements"

        # Customize based on business criticality
        if application_context.business_criticality == "mission_critical":
            if field.critical_attribute in [
                "availability_requirements",
                "security_requirements",
                "performance_baseline",
            ]:
                field.help_text += (
                    " (CRITICAL: Required for mission-critical applications)"
                )

        return field

    def _generate_field_validation(
        self, field: FormField, application_context: ApplicationContext
    ) -> FieldValidation:
        """Generate validation rules for a form field"""

        rules = []
        parameters = {}

        # Required field validation
        if self._is_field_required(field, application_context):
            rules.append(ValidationRule.REQUIRED)

        # Field type specific validation
        if field.field_type == FieldType.EMAIL:
            rules.append(ValidationRule.EMAIL_FORMAT)
        elif field.field_type == FieldType.URL:
            rules.append(ValidationRule.URL_FORMAT)
        elif field.field_type in [FieldType.TEXT, FieldType.TEXTAREA]:
            if field.critical_attribute in [
                "specifications",
                "integration_dependencies",
            ]:
                rules.append(ValidationRule.MIN_LENGTH)
                parameters["min_length"] = 10
        elif field.field_type == FieldType.NUMBER:
            rules.append(ValidationRule.MIN_VALUE)
            parameters["min_value"] = 0

        error_message = self._generate_validation_error_message(
            field.critical_attribute
        )

        return FieldValidation(
            rules=rules, parameters=parameters, error_message=error_message
        )

    def _generate_conditional_display(
        self, field: FormField, application_context: ApplicationContext
    ) -> ConditionalDisplayRule:
        """Generate conditional display rules for fields"""

        # Example: Show network configuration details only if not containerized
        if field.critical_attribute == "network_config":
            return ConditionalDisplayRule(
                dependent_field="virtualization",
                condition="not_equals",
                values=["container"],
                required_when_visible=True,
            )

        # Show performance baseline only for business/mission critical applications
        elif field.critical_attribute == "performance_baseline":
            return ConditionalDisplayRule(
                dependent_field="business_criticality",
                condition="in",
                values=["business_critical", "mission_critical"],
                required_when_visible=True,
            )

        return None

    def _is_field_required(
        self, field: FormField, application_context: ApplicationContext
    ) -> bool:
        """Determine if a field is required based on context and business rules"""

        # Always required for mission critical applications
        if application_context.business_criticality == "mission_critical":
            if field.critical_attribute in [
                "technology_stack",
                "architecture_pattern",
                "business_criticality",
                "availability_requirements",
                "security_requirements",
            ]:
                return True

        # Required based on business impact score (high impact fields)
        if field.business_impact_score >= 0.06:
            return True

        # Required for specific technology patterns
        if "microservices" in application_context.architecture_pattern.lower():
            if field.critical_attribute in [
                "integration_dependencies",
                "configuration_complexity",
            ]:
                return True

        return False

    def _calculate_confidence_impact(self, sections: List[FormSection]) -> float:
        """Calculate expected confidence improvement from completing this form"""

        total_weight = 0.0
        for section in sections:
            for field in section.fields:
                total_weight += field.business_impact_score

        # Convert weight to confidence improvement percentage (0-100)
        # Maximum possible weight is 1.0 (100% of critical attributes)
        confidence_improvement = min(100.0, total_weight * 100)

        return confidence_improvement

    def _generate_validation_error_message(self, attribute_name: str) -> str:
        """Generate user-friendly validation error messages"""

        messages = {
            "technology_stack": "Please select at least one technology from the list",
            "business_criticality": "Business criticality is required for migration planning",
            "architecture_pattern": "Architecture pattern helps determine the migration approach",
            "integration_dependencies": "Please describe any external system dependencies",
        }

        return messages.get(
            attribute_name,
            f"Please provide valid information for {attribute_name.replace('_', ' ')}",
        )
