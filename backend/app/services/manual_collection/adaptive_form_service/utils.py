"""
Adaptive Form Service Utility Functions
"""

from dataclasses import asdict
from typing import Any, Dict

from .enums import FieldType
from .models import AdaptiveForm


def to_dict(form: AdaptiveForm) -> Dict[str, Any]:
    """Convert AdaptiveForm to dictionary representation"""
    return asdict(form)


def to_json_schema(form: AdaptiveForm) -> Dict[str, Any]:
    """
    Convert AdaptiveForm to JSON Schema format for frontend consumption.

    This generates a schema that can be used by form libraries like react-hook-form
    or JSON Forms to render the adaptive form.
    """
    properties = {}
    required_fields = []
    sections_config = []

    for section in form.sections:
        section_fields = []

        for field in section.fields:
            field_schema = _build_field_schema(field)
            _add_field_options(field_schema, field)
            _add_validation_rules(field_schema, field, required_fields)
            _add_field_extras(field_schema, field)

            properties[field.id] = field_schema
            section_fields.append(_build_section_field_config(field))

        sections_config.append(_build_section_config(section, section_fields))

    return _build_final_schema(form, properties, required_fields, sections_config)


def _build_field_schema(field) -> Dict[str, Any]:
    """Build base field schema with type, title, and description."""
    return {
        "type": _get_json_schema_type(field.field_type),
        "title": field.label,
        "description": field.description,
    }


def _add_field_options(field_schema: Dict[str, Any], field) -> None:
    """Add field options for select/radio fields."""
    if field.options:
        field_schema["enum"] = [opt["value"] for opt in field.options]
        field_schema["enumNames"] = [opt["label"] for opt in field.options]


def _add_validation_rules(
    field_schema: Dict[str, Any], field, required_fields: list
) -> None:
    """Add validation rules to field schema."""
    if not field.validation:
        return

    if "required" in [rule.value for rule in field.validation.rules]:
        required_fields.append(field.id)

    for rule in field.validation.rules:
        if rule.value == "min_length":
            field_schema["minLength"] = field.validation.parameters.get("min_length", 1)
        elif rule.value == "max_length":
            field_schema["maxLength"] = field.validation.parameters.get(
                "max_length", 1000
            )
        elif rule.value == "min_value":
            field_schema["minimum"] = field.validation.parameters.get("min_value", 0)
        elif rule.value == "max_value":
            field_schema["maximum"] = field.validation.parameters.get(
                "max_value", 1000000
            )
        elif rule.value == "pattern":
            field_schema["pattern"] = field.validation.parameters.get("pattern", ".*")


def _add_field_extras(field_schema: Dict[str, Any], field) -> None:
    """Add placeholder, help text, and conditional display rules."""
    # Add placeholder as default or example
    if field.placeholder:
        if field.field_type in [FieldType.TEXT, FieldType.TEXTAREA]:
            field_schema["default"] = ""
            field_schema["examples"] = [field.placeholder]
        else:
            field_schema["description"] += f" Example: {field.placeholder}"

    # Add help text
    if field.help_text:
        field_schema["help"] = field.help_text

    # Add conditional display rules
    if field.conditional_display:
        field_schema["conditional"] = {
            "dependentField": field.conditional_display.dependent_field,
            "condition": field.conditional_display.condition,
            "values": field.conditional_display.values,
            "requiredWhenVisible": field.conditional_display.required_when_visible,
        }


def _build_section_field_config(field) -> Dict[str, Any]:
    """Build section field configuration."""
    return {
        "id": field.id,
        "order": field.order,
        "criticalAttribute": field.critical_attribute,
        "businessImpactScore": field.business_impact_score,
    }


def _build_section_config(section, section_fields: list) -> Dict[str, Any]:
    """Build section configuration."""
    return {
        "id": section.id,
        "title": section.title,
        "description": section.description,
        "order": section.order,
        "fields": section_fields,
        "requiredFieldsCount": section.required_fields_count,
        "completionWeight": section.completion_weight,
    }


def _build_final_schema(
    form: AdaptiveForm,
    properties: Dict[str, Any],
    required_fields: list,
    sections_config: list,
) -> Dict[str, Any]:
    """Build the final JSON schema."""
    return {
        "type": "object",
        "title": form.title,
        "properties": properties,
        "required": required_fields,
        "additionalProperties": False,
        "formMetadata": {
            "id": form.id,
            "applicationId": str(form.application_id),
            "gapAnalysisId": str(form.gap_analysis_id),
            "totalFields": form.total_fields,
            "requiredFields": form.required_fields,
            "estimatedCompletionTime": form.estimated_completion_time,
            "confidenceImpactScore": form.confidence_impact_score,
            "createdAt": form.created_at.isoformat(),
            "updatedAt": form.updated_at.isoformat(),
        },
        "sections": sections_config,
    }


def _get_json_schema_type(field_type: FieldType) -> str:
    """Convert FieldType to JSON Schema type"""

    type_mapping = {
        FieldType.TEXT: "string",
        FieldType.TEXTAREA: "string",
        FieldType.EMAIL: "string",
        FieldType.URL: "string",
        FieldType.SELECT: "string",
        FieldType.RADIO: "string",
        FieldType.MULTISELECT: "array",
        FieldType.CHECKBOX: "boolean",
        FieldType.NUMBER: "number",
        FieldType.DATE: "string",
        FieldType.FILE: "string",
    }

    return type_mapping.get(field_type, "string")
