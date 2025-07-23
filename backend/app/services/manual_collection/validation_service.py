"""
Questionnaire Response Validation Service

Comprehensive validation service for manual collection questionnaire responses,
including real-time validation, cross-field validation, business rule validation,
and confidence scoring.

Agent Team B3 - Task B3.3
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from .adaptive_form_service import (
    AdaptiveForm,
    ConditionalDisplayRule,
    FieldType,
    FormField,
    ValidationRule,
)


class ValidationResult(str, Enum):
    """Validation result types"""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    CONDITIONAL = "conditional"


class ValidationCategory(str, Enum):
    """Categories of validation"""

    FORMAT = "format"
    BUSINESS_RULE = "business_rule"
    CROSS_FIELD = "cross_field"
    COMPLETENESS = "completeness"
    QUALITY = "quality"
    CONSISTENCY = "consistency"


@dataclass
class ValidationError:
    """Individual validation error"""

    field_id: str
    field_label: str
    error_code: str
    error_message: str
    severity: str  # 'error', 'warning', 'info'
    category: ValidationCategory
    suggested_value: Optional[str] = None
    auto_correctable: bool = False
    validation_context: Optional[Dict[str, Any]] = None


@dataclass
class FieldValidationResult:
    """Result of validating a single field"""

    field_id: str
    is_valid: bool
    result_type: ValidationResult
    errors: List[ValidationError]
    warnings: List[ValidationError]
    normalized_value: Any
    confidence_score: float
    validation_timestamp: datetime


@dataclass
class FormValidationResult:
    """Result of validating an entire form"""

    form_id: str
    is_valid: bool
    overall_confidence_score: float
    completion_percentage: float
    field_results: Dict[str, FieldValidationResult]
    cross_field_errors: List[ValidationError]
    business_rule_violations: List[ValidationError]
    validation_summary: Dict[str, int]
    validation_timestamp: datetime
    estimated_6r_confidence_impact: float


@dataclass
class QuestionnaireResponse:
    """Questionnaire response data structure"""

    response_id: str
    form_id: str
    application_id: UUID
    user_id: UUID
    responses: Dict[str, Any]
    partial_save: bool
    submitted_at: Optional[datetime] = None
    last_modified: datetime = None


class QuestionnaireValidationService:
    """Service for comprehensive questionnaire response validation"""

    # Business rules for cross-field validation
    BUSINESS_RULES = {
        "cloud_readiness_architecture": {
            "description": "Microservices architecture should use containers",
            "condition": lambda responses: (
                responses.get("field_architecture_pattern") == "microservices"
                and responses.get("field_virtualization")
                not in ["container", "cloud_vm"]
            ),
            "message": "Microservices applications typically run in containerized environments",
            "severity": "warning",
            "suggested_action": "Consider containerization for microservices architecture",
        },
        "compliance_security_alignment": {
            "description": "Compliance requirements should align with security controls",
            "condition": lambda responses: (
                "hipaa"
                in str(responses.get("field_compliance_constraints", "")).lower()
                and "encryption_rest"
                not in str(responses.get("field_security_requirements", "")).lower()
            ),
            "message": "HIPAA compliance requires encryption at rest",
            "severity": "error",
            "suggested_action": "Add encryption at rest to security requirements",
        },
        "legacy_technology_risk": {
            "description": "Legacy technology increases technical debt",
            "condition": lambda responses: (
                "windows_server_2012"
                in str(responses.get("field_os_version", "")).lower()
                and responses.get("field_business_criticality") == "mission_critical"
            ),
            "message": "Mission critical applications on legacy OS pose significant risk",
            "severity": "warning",
            "suggested_action": "Consider OS upgrade as part of migration strategy",
        },
        "performance_scalability_consistency": {
            "description": "High performance requirements need scalable architecture",
            "condition": lambda responses: (
                "high" in str(responses.get("field_user_load_patterns", "")).lower()
                and responses.get("field_architecture_pattern") == "monolith"
            ),
            "message": "High load applications may benefit from scalable architecture patterns",
            "severity": "warning",
            "suggested_action": "Consider microservices or horizontal scaling capabilities",
        },
    }

    # Data quality patterns for validation
    QUALITY_PATTERNS = {
        "technology_stack_completeness": {
            "pattern": r"(java|python|\.net|node\.?js|php|ruby|go|rust)",
            "field": "field_technology_stack",
            "message": "Technology stack should include programming language/runtime",
            "min_components": 2,  # Should have at least language + framework/database
        },
        "network_config_detail": {
            "pattern": r"(port|protocol|tcp|udp|http|https|\d+)",
            "field": "field_network_config",
            "message": "Network configuration should include specific ports or protocols",
            "min_length": 30,
        },
        "integration_dependency_structure": {
            "pattern": r"(api|database|queue|service|endpoint)",
            "field": "field_integration_dependencies",
            "message": "Integration dependencies should specify connection types",
            "min_length": 20,
        },
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def validate_questionnaire_response(
        self, response: QuestionnaireResponse, form: AdaptiveForm
    ) -> FormValidationResult:
        """
        Comprehensive validation of questionnaire response.

        Core implementation of B3.3 - questionnaire response validation.
        Includes format validation, business rules, cross-field validation,
        and confidence scoring.
        """
        start_time = datetime.now()

        self.logger.info(f"Validating questionnaire response {response.response_id}")

        # Validate individual fields
        field_results = {}
        for section in form.sections:
            for field in section.fields:
                field_result = await self._validate_field(
                    field, response.responses.get(field.id), response.responses, form
                )
                field_results[field.id] = field_result

        # Perform cross-field validation
        cross_field_errors = await self._validate_cross_field_rules(
            response.responses, form
        )

        # Apply business rules
        business_rule_violations = await self._validate_business_rules(
            response.responses
        )

        # Calculate overall validation status
        is_valid = (
            all(result.is_valid for result in field_results.values())
            and not any(error.severity == "error" for error in cross_field_errors)
            and not any(error.severity == "error" for error in business_rule_violations)
        )

        # Calculate confidence and completion scores
        overall_confidence = await self._calculate_overall_confidence(
            field_results, form
        )
        completion_percentage = await self._calculate_completion_percentage(
            field_results, form
        )

        # Generate validation summary
        validation_summary = self._generate_validation_summary(
            field_results, cross_field_errors, business_rule_violations
        )

        # Estimate 6R confidence impact
        confidence_impact = await self._estimate_6r_confidence_impact(
            field_results, form
        )

        result = FormValidationResult(
            form_id=form.id,
            is_valid=is_valid,
            overall_confidence_score=overall_confidence,
            completion_percentage=completion_percentage,
            field_results=field_results,
            cross_field_errors=cross_field_errors,
            business_rule_violations=business_rule_violations,
            validation_summary=validation_summary,
            validation_timestamp=start_time,
            estimated_6r_confidence_impact=confidence_impact,
        )

        self.logger.info(
            f"Validation completed for {response.response_id}: "
            f"valid={is_valid}, confidence={overall_confidence:.2f}, "
            f"completion={completion_percentage:.1f}%"
        )

        return result

    async def validate_real_time_field(
        self,
        field_id: str,
        value: Any,
        current_responses: Dict[str, Any],
        form: AdaptiveForm,
    ) -> FieldValidationResult:
        """
        Real-time validation of individual field as user types.

        Provides immediate feedback for form fields without requiring
        full form submission.
        """
        # Find the field in the form
        field = None
        for section in form.sections:
            for f in section.fields:
                if f.id == field_id:
                    field = f
                    break
            if field:
                break

        if not field:
            raise ValueError(f"Field {field_id} not found in form {form.id}")

        return await self._validate_field(field, value, current_responses, form)

    async def _validate_field(
        self,
        field: FormField,
        value: Any,
        all_responses: Dict[str, Any],
        form: AdaptiveForm,
    ) -> FieldValidationResult:
        """Validate individual field value"""

        errors = []
        warnings = []
        normalized_value = value
        confidence_score = 0.0

        # Check if field should be displayed (conditional logic)
        if field.conditional_display:
            is_visible = self._evaluate_conditional_display(
                field.conditional_display, all_responses
            )
            if not is_visible:
                return FieldValidationResult(
                    field_id=field.id,
                    is_valid=True,
                    result_type=ValidationResult.CONDITIONAL,
                    errors=[],
                    warnings=[],
                    normalized_value=None,
                    confidence_score=1.0,
                    validation_timestamp=datetime.now(),
                )

        # Normalize value
        normalized_value = self._normalize_field_value(value, field.field_type)

        # Required field validation
        if field.validation and ValidationRule.REQUIRED in field.validation.rules:
            if self._is_empty_value(normalized_value):
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="REQUIRED_FIELD",
                        error_message=f"{field.label} is required",
                        severity="error",
                        category=ValidationCategory.COMPLETENESS,
                    )
                )

        # Skip further validation if field is empty and not required
        if self._is_empty_value(normalized_value):
            return FieldValidationResult(
                field_id=field.id,
                is_valid=len(errors) == 0,
                result_type=(
                    ValidationResult.VALID
                    if len(errors) == 0
                    else ValidationResult.INVALID
                ),
                errors=errors,
                warnings=warnings,
                normalized_value=normalized_value,
                confidence_score=0.0,
                validation_timestamp=datetime.now(),
            )

        # Format validation
        format_errors = await self._validate_field_format(field, normalized_value)
        errors.extend(format_errors)

        # Length validation
        length_errors = await self._validate_field_length(field, normalized_value)
        errors.extend(length_errors)

        # Value validation (for select fields)
        value_errors = await self._validate_field_values(field, normalized_value)
        errors.extend(value_errors)

        # Quality validation
        quality_warnings = await self._validate_field_quality(field, normalized_value)
        warnings.extend(quality_warnings)

        # Calculate confidence score based on validation results
        confidence_score = self._calculate_field_confidence(
            field, normalized_value, errors, warnings
        )

        result_type = ValidationResult.VALID
        if errors:
            result_type = ValidationResult.INVALID
        elif warnings:
            result_type = ValidationResult.WARNING

        return FieldValidationResult(
            field_id=field.id,
            is_valid=len(errors) == 0,
            result_type=result_type,
            errors=errors,
            warnings=warnings,
            normalized_value=normalized_value,
            confidence_score=confidence_score,
            validation_timestamp=datetime.now(),
        )

    async def _validate_field_format(
        self, field: FormField, value: Any
    ) -> List[ValidationError]:
        """Validate field format based on field type"""
        errors = []

        if field.field_type == FieldType.EMAIL:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="INVALID_EMAIL",
                        error_message="Invalid email format",
                        severity="error",
                        category=ValidationCategory.FORMAT,
                    )
                )

        elif field.field_type == FieldType.URL:
            url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if not re.match(url_pattern, str(value)):
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="INVALID_URL",
                        error_message="Invalid URL format",
                        severity="error",
                        category=ValidationCategory.FORMAT,
                    )
                )

        elif field.field_type == FieldType.NUMBER:
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="INVALID_NUMBER",
                        error_message="Value must be a number",
                        severity="error",
                        category=ValidationCategory.FORMAT,
                    )
                )

        return errors

    async def _validate_field_length(
        self, field: FormField, value: Any
    ) -> List[ValidationError]:
        """Validate field length constraints"""
        errors = []

        if not field.validation:
            return errors

        value_str = str(value) if value is not None else ""

        if ValidationRule.MIN_LENGTH in field.validation.rules:
            min_length = field.validation.parameters.get("min_length", 1)
            if len(value_str) < min_length:
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="MIN_LENGTH",
                        error_message=f"Minimum length is {min_length} characters",
                        severity="error",
                        category=ValidationCategory.FORMAT,
                    )
                )

        if ValidationRule.MAX_LENGTH in field.validation.rules:
            max_length = field.validation.parameters.get("max_length", 1000)
            if len(value_str) > max_length:
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="MAX_LENGTH",
                        error_message=f"Maximum length is {max_length} characters",
                        severity="error",
                        category=ValidationCategory.FORMAT,
                    )
                )

        return errors

    async def _validate_field_values(
        self, field: FormField, value: Any
    ) -> List[ValidationError]:
        """Validate field values against allowed options"""
        errors = []

        if field.field_type in [FieldType.SELECT, FieldType.RADIO] and field.options:
            valid_values = [opt["value"] for opt in field.options]
            if str(value) not in valid_values:
                errors.append(
                    ValidationError(
                        field_id=field.id,
                        field_label=field.label,
                        error_code="INVALID_OPTION",
                        error_message=f'Invalid option selected. Valid options: {", ".join(valid_values)}',
                        severity="error",
                        category=ValidationCategory.FORMAT,
                        suggested_value=valid_values[0] if valid_values else None,
                    )
                )

        elif field.field_type == FieldType.MULTISELECT and field.options:
            valid_values = [opt["value"] for opt in field.options]
            if isinstance(value, list):
                invalid_values = [v for v in value if str(v) not in valid_values]
                if invalid_values:
                    errors.append(
                        ValidationError(
                            field_id=field.id,
                            field_label=field.label,
                            error_code="INVALID_MULTISELECT",
                            error_message=f'Invalid options: {", ".join(invalid_values)}',
                            severity="error",
                            category=ValidationCategory.FORMAT,
                        )
                    )

        return errors

    async def _validate_field_quality(
        self, field: FormField, value: Any
    ) -> List[ValidationError]:
        """Validate field quality based on patterns and content analysis"""
        warnings = []

        value_str = str(value) if value is not None else ""

        # Check quality patterns for specific critical attributes
        for pattern_name, pattern_config in self.QUALITY_PATTERNS.items():
            if field.id == pattern_config["field"]:
                # Check pattern match
                if "pattern" in pattern_config:
                    if not re.search(
                        pattern_config["pattern"], value_str, re.IGNORECASE
                    ):
                        warnings.append(
                            ValidationError(
                                field_id=field.id,
                                field_label=field.label,
                                error_code="QUALITY_PATTERN",
                                error_message=pattern_config["message"],
                                severity="warning",
                                category=ValidationCategory.QUALITY,
                            )
                        )

                # Check minimum length for detail
                if "min_length" in pattern_config:
                    if len(value_str) < pattern_config["min_length"]:
                        warnings.append(
                            ValidationError(
                                field_id=field.id,
                                field_label=field.label,
                                error_code="INSUFFICIENT_DETAIL",
                                error_message=f'More detail recommended (at least {pattern_config["min_length"]} characters)',
                                severity="warning",
                                category=ValidationCategory.QUALITY,
                            )
                        )

                # Check minimum components for technology stack
                if (
                    "min_components" in pattern_config
                    and field.id == "field_technology_stack"
                ):
                    components = len(
                        [comp.strip() for comp in value_str.split(",") if comp.strip()]
                    )
                    if components < pattern_config["min_components"]:
                        warnings.append(
                            ValidationError(
                                field_id=field.id,
                                field_label=field.label,
                                error_code="INCOMPLETE_STACK",
                                error_message=f'Technology stack should include multiple components (found {components}, recommended {pattern_config["min_components"]}+)',
                                severity="warning",
                                category=ValidationCategory.QUALITY,
                            )
                        )

        return warnings

    async def _validate_cross_field_rules(
        self, responses: Dict[str, Any], form: AdaptiveForm
    ) -> List[ValidationError]:
        """Validate cross-field business rules"""
        errors = []

        # Conditional required field validation
        for section in form.sections:
            for field in section.fields:
                if field.conditional_display:
                    is_visible = self._evaluate_conditional_display(
                        field.conditional_display, responses
                    )
                    if is_visible and field.conditional_display.required_when_visible:
                        field_value = responses.get(field.id)
                        if self._is_empty_value(field_value):
                            errors.append(
                                ValidationError(
                                    field_id=field.id,
                                    field_label=field.label,
                                    error_code="CONDITIONAL_REQUIRED",
                                    error_message=f"{field.label} is required based on other field values",
                                    severity="error",
                                    category=ValidationCategory.CROSS_FIELD,
                                )
                            )

        return errors

    async def _validate_business_rules(
        self, responses: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate business rules across the response"""
        violations = []

        for rule_name, rule_config in self.BUSINESS_RULES.items():
            try:
                if rule_config["condition"](responses):
                    violations.append(
                        ValidationError(
                            field_id="business_rule",
                            field_label="Business Rule",
                            error_code=rule_name.upper(),
                            error_message=rule_config["message"],
                            severity=rule_config["severity"],
                            category=ValidationCategory.BUSINESS_RULE,
                            suggested_value=rule_config.get("suggested_action"),
                            validation_context={"rule_name": rule_name},
                        )
                    )
            except Exception as e:
                self.logger.error(
                    f"Error evaluating business rule {rule_name}: {str(e)}"
                )

        return violations

    def _evaluate_conditional_display(
        self, rule: ConditionalDisplayRule, responses: Dict[str, Any]
    ) -> bool:
        """Evaluate conditional display rule"""
        dependent_value = responses.get(rule.dependent_field)

        if rule.condition == "equals":
            return str(dependent_value) in rule.values
        elif rule.condition == "contains":
            return any(
                value.lower() in str(dependent_value).lower() for value in rule.values
            )
        elif rule.condition == "not_equals":
            return str(dependent_value) not in rule.values
        elif rule.condition == "in":
            return str(dependent_value) in rule.values
        elif rule.condition == "not_in":
            return str(dependent_value) not in rule.values

        return False

    def _normalize_field_value(self, value: Any, field_type: FieldType) -> Any:
        """Normalize field value based on type"""
        if value is None:
            return None

        if field_type == FieldType.TEXT or field_type == FieldType.TEXTAREA:
            return str(value).strip()
        elif field_type == FieldType.NUMBER:
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        elif field_type == FieldType.CHECKBOX:
            return bool(value)
        elif field_type == FieldType.MULTISELECT:
            if isinstance(value, list):
                return [str(v).strip() for v in value]
            else:
                return [str(value).strip()] if value else []
        else:
            return str(value).strip() if value else None

    def _is_empty_value(self, value: Any) -> bool:
        """Check if value is considered empty"""
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, list) and not value:
            return True
        return False

    def _calculate_field_confidence(
        self,
        field: FormField,
        value: Any,
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> float:
        """Calculate confidence score for individual field"""
        if errors:
            return 0.0

        if self._is_empty_value(value):
            return 0.0

        base_confidence = 0.8

        # Reduce confidence for warnings
        warning_penalty = len(warnings) * 0.1

        # Increase confidence for high-quality responses
        value_str = str(value) if value is not None else ""
        if len(value_str) > 50:  # Detailed responses
            base_confidence += 0.1

        # Field-specific confidence adjustments
        if field.critical_attribute in ["technology_stack", "integration_dependencies"]:
            if len(value_str) > 100:
                base_confidence += 0.1

        final_confidence = max(0.0, min(1.0, base_confidence - warning_penalty))
        return final_confidence

    async def _calculate_overall_confidence(
        self, field_results: Dict[str, FieldValidationResult], form: AdaptiveForm
    ) -> float:
        """Calculate overall confidence score for the form"""
        if not field_results:
            return 0.0

        total_weight = 0.0
        weighted_confidence = 0.0

        for section in form.sections:
            for field in section.fields:
                if field.id in field_results:
                    result = field_results[field.id]
                    weight = field.business_impact_score
                    total_weight += weight
                    weighted_confidence += result.confidence_score * weight

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    async def _calculate_completion_percentage(
        self, field_results: Dict[str, FieldValidationResult], form: AdaptiveForm
    ) -> float:
        """Calculate completion percentage"""
        total_fields = 0
        completed_fields = 0

        for section in form.sections:
            for field in section.fields:
                total_fields += 1
                if field.id in field_results:
                    result = field_results[field.id]
                    if result.result_type in [
                        ValidationResult.VALID,
                        ValidationResult.WARNING,
                    ]:
                        completed_fields += 1

        return (completed_fields / total_fields * 100) if total_fields > 0 else 0.0

    def _generate_validation_summary(
        self,
        field_results: Dict[str, FieldValidationResult],
        cross_field_errors: List[ValidationError],
        business_rule_violations: List[ValidationError],
    ) -> Dict[str, int]:
        """Generate summary of validation results"""
        summary = {
            "total_fields": len(field_results),
            "valid_fields": 0,
            "invalid_fields": 0,
            "warning_fields": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "cross_field_errors": len(cross_field_errors),
            "business_rule_violations": len(business_rule_violations),
        }

        for result in field_results.values():
            if result.result_type == ValidationResult.VALID:
                summary["valid_fields"] += 1
            elif result.result_type == ValidationResult.INVALID:
                summary["invalid_fields"] += 1
            elif result.result_type == ValidationResult.WARNING:
                summary["warning_fields"] += 1

            summary["total_errors"] += len(result.errors)
            summary["total_warnings"] += len(result.warnings)

        return summary

    async def _estimate_6r_confidence_impact(
        self, field_results: Dict[str, FieldValidationResult], form: AdaptiveForm
    ) -> float:
        """Estimate impact on 6R recommendation confidence"""
        total_weight = 0.0
        collected_weight = 0.0

        for section in form.sections:
            for field in section.fields:
                weight = field.business_impact_score
                total_weight += weight

                if field.id in field_results:
                    result = field_results[field.id]
                    if result.result_type in [
                        ValidationResult.VALID,
                        ValidationResult.WARNING,
                    ]:
                        collected_weight += weight * result.confidence_score

        return collected_weight / total_weight if total_weight > 0 else 0.0
