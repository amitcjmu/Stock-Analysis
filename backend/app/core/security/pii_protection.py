"""
PII Protection Utilities for Data Export Security

This module provides field-level classification and redaction of personally
identifiable information (PII) to ensure compliance with data protection
regulations during data exports.
"""

import re
import logging
from typing import Any, Dict, List
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class PIISensitivityLevel(str, Enum):
    """PII sensitivity classification levels"""

    PUBLIC = "public"  # No sensitive data
    INTERNAL = "internal"  # Internal business data
    CONFIDENTIAL = "confidential"  # Sensitive but not PII
    RESTRICTED = "restricted"  # Contains PII, restricted access
    HIGHLY_RESTRICTED = "highly_restricted"  # Contains highly sensitive PII


class PIIFieldClassifier:
    """
    Classifier for identifying PII fields in data exports.

    Uses pattern matching and field name analysis to classify fields
    based on their potential sensitivity level.
    """

    def __init__(self):
        # PII field patterns (case-insensitive)
        self.highly_restricted_patterns = {
            # Identity documents
            r".*ssn.*",
            r".*social.*security.*",
            r".*passport.*",
            r".*driver.*license.*",
            r".*tax.*id.*",
            r".*national.*id.*",
            r".*identity.*card.*",
            # Financial
            r".*credit.*card.*",
            r".*card.*number.*",
            r".*bank.*account.*",
            r".*routing.*number.*",
            r".*iban.*",
            r".*swift.*",
            r".*account.*number.*",
            # Authentication
            r".*password.*",
            r".*secret.*",
            r".*token.*",
            r".*key.*",
            r".*hash.*",
            r".*credential.*",
            r".*pin.*",
            r".*security.*code.*",
        }

        self.restricted_patterns = {
            # Personal contact
            r".*email.*",
            r".*phone.*",
            r".*mobile.*",
            r".*cell.*",
            r".*address.*",
            r".*street.*",
            r".*postal.*",
            r".*zip.*",
            r".*home.*",
            r".*personal.*",
            # Personal identifiers
            r".*first.*name.*",
            r".*last.*name.*",
            r".*full.*name.*",
            r".*surname.*",
            r".*given.*name.*",
            r".*middle.*name.*",
            r".*maiden.*name.*",
            r".*birth.*date.*",
            r".*dob.*",
            r".*age.*",
            r".*birthday.*",
            # Employment/HR
            r".*employee.*id.*",
            r".*emp.*id.*",
            r".*staff.*id.*",
            r".*salary.*",
            r".*wage.*",
            r".*compensation.*",
            r".*hire.*date.*",
            r".*termination.*date.*",
        }

        self.confidential_patterns = {
            # Business sensitive
            r".*revenue.*",
            r".*profit.*",
            r".*cost.*",
            r".*budget.*",
            r".*price.*",
            r".*contract.*",
            r".*deal.*",
            r".*negotiation.*",
            r".*strategy.*",
            r".*confidential.*",
            r".*proprietary.*",
            r".*internal.*",
        }

        # Compile patterns for performance
        self.compiled_highly_restricted = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.highly_restricted_patterns
        ]
        self.compiled_restricted = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.restricted_patterns
        ]
        self.compiled_confidential = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.confidential_patterns
        ]

    def classify_field(
        self, field_name: str, field_value: Any = None
    ) -> PIISensitivityLevel:
        """
        Classify a field based on its name and optionally its value.

        Args:
            field_name: Name of the field to classify
            field_value: Optional value for additional analysis

        Returns:
            Sensitivity level classification
        """
        field_name_lower = field_name.lower()

        # Check highly restricted patterns
        for pattern in self.compiled_highly_restricted:
            if pattern.search(field_name_lower):
                return PIISensitivityLevel.HIGHLY_RESTRICTED

        # Check restricted patterns
        for pattern in self.compiled_restricted:
            if pattern.search(field_name_lower):
                return PIISensitivityLevel.RESTRICTED

        # Check confidential patterns
        for pattern in self.compiled_confidential:
            if pattern.search(field_name_lower):
                return PIISensitivityLevel.CONFIDENTIAL

        # Additional value-based classification if value is provided
        if field_value is not None:
            sensitivity = self._classify_by_value(field_value)
            if sensitivity != PIISensitivityLevel.PUBLIC:
                return sensitivity

        # Default to internal for unclassified fields
        return PIISensitivityLevel.INTERNAL

    def _classify_by_value(self, value: Any) -> PIISensitivityLevel:
        """
        Classify based on field value patterns.

        Args:
            value: Field value to analyze

        Returns:
            Sensitivity level based on value patterns
        """
        if not isinstance(value, str):
            return PIISensitivityLevel.PUBLIC

        value_str = str(value).strip()

        # Email pattern
        if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value_str):
            return PIISensitivityLevel.RESTRICTED

        # Phone number patterns
        phone_patterns = [
            r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$",  # US
            r"^\+?[0-9]{1,4}[-.\s]?[0-9]{3,14}$",  # International
        ]
        for pattern in phone_patterns:
            if re.match(pattern, value_str):
                return PIISensitivityLevel.RESTRICTED

        # SSN pattern (XXX-XX-XXXX)
        if re.match(r"^\d{3}-?\d{2}-?\d{4}$", value_str):
            return PIISensitivityLevel.HIGHLY_RESTRICTED

        # Credit card pattern (basic check)
        if re.match(r"^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$", value_str):
            return PIISensitivityLevel.HIGHLY_RESTRICTED

        return PIISensitivityLevel.PUBLIC


class PIIRedactor:
    """
    Redacts PII data based on sensitivity classification.
    """

    def __init__(self, classifier: PIIFieldClassifier = None):
        self.classifier = classifier or PIIFieldClassifier()

    def redact_record(
        self,
        record: Dict[str, Any],
        redaction_level: PIISensitivityLevel = PIISensitivityLevel.RESTRICTED,
    ) -> Dict[str, Any]:
        """
        Redact PII fields in a record based on sensitivity level.

        Args:
            record: Dictionary containing field data
            redaction_level: Minimum sensitivity level to redact

        Returns:
            Record with PII fields redacted
        """
        if not settings.ENABLE_PII_REDACTION:
            return record

        redacted_record = {}
        redacted_count = 0

        for field_name, field_value in record.items():
            field_sensitivity = self.classifier.classify_field(field_name, field_value)

            # Redact if sensitivity level meets or exceeds redaction threshold
            if self._should_redact(field_sensitivity, redaction_level):
                redacted_record[field_name] = self._get_redaction_value(
                    field_sensitivity, field_value
                )
                redacted_count += 1
            else:
                redacted_record[field_name] = field_value

        if redacted_count > 0:
            logger.info(f"Redacted {redacted_count} PII fields from record")

        return redacted_record

    def _should_redact(
        self,
        field_sensitivity: PIISensitivityLevel,
        redaction_level: PIISensitivityLevel,
    ) -> bool:
        """
        Determine if a field should be redacted based on sensitivity levels.
        """
        sensitivity_order = {
            PIISensitivityLevel.PUBLIC: 0,
            PIISensitivityLevel.INTERNAL: 1,
            PIISensitivityLevel.CONFIDENTIAL: 2,
            PIISensitivityLevel.RESTRICTED: 3,
            PIISensitivityLevel.HIGHLY_RESTRICTED: 4,
        }

        return (
            sensitivity_order[field_sensitivity] >= sensitivity_order[redaction_level]
        )

    def _get_redaction_value(
        self, sensitivity: PIISensitivityLevel, original_value: Any
    ) -> str:
        """
        Get appropriate redaction value based on sensitivity level.
        """
        if sensitivity == PIISensitivityLevel.HIGHLY_RESTRICTED:
            return "***HIGHLY_RESTRICTED***"
        elif sensitivity == PIISensitivityLevel.RESTRICTED:
            return "***RESTRICTED***"
        elif sensitivity == PIISensitivityLevel.CONFIDENTIAL:
            return "***CONFIDENTIAL***"
        else:
            return "***REDACTED***"

    def get_redaction_summary(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of PII fields that would be redacted.

        Args:
            records: List of records to analyze

        Returns:
            Summary of PII classification
        """
        field_classifications = {}
        total_fields = set()

        for record in records[:100]:  # Sample first 100 records for analysis
            for field_name, field_value in record.items():
                total_fields.add(field_name)
                if field_name not in field_classifications:
                    sensitivity = self.classifier.classify_field(
                        field_name, field_value
                    )
                    field_classifications[field_name] = sensitivity.value

        # Count by sensitivity level
        sensitivity_counts = {}
        for sensitivity in field_classifications.values():
            sensitivity_counts[sensitivity] = sensitivity_counts.get(sensitivity, 0) + 1

        return {
            "total_fields": len(total_fields),
            "field_classifications": field_classifications,
            "sensitivity_distribution": sensitivity_counts,
            "pii_redaction_enabled": settings.ENABLE_PII_REDACTION,
        }


# Global instances for reuse
_classifier = PIIFieldClassifier()
_redactor = PIIRedactor(_classifier)


def classify_field(field_name: str, field_value: Any = None) -> PIISensitivityLevel:
    """Convenience function for field classification."""
    return _classifier.classify_field(field_name, field_value)


def redact_record(
    record: Dict[str, Any],
    redaction_level: PIISensitivityLevel = PIISensitivityLevel.RESTRICTED,
) -> Dict[str, Any]:
    """Convenience function for record redaction."""
    return _redactor.redact_record(record, redaction_level)


def get_redaction_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for redaction summary."""
    return _redactor.get_redaction_summary(records)
