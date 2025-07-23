"""
PII Scanner Tool for sensitive data detection
"""

import re
from typing import Any, ClassVar, Dict, List, Set

from app.services.tools.base_tool import BaseDiscoveryTool
from app.services.tools.registry import ToolMetadata


class PIIScannerTool(BaseDiscoveryTool):
    """Scans data for personally identifiable information"""

    name: str = "pii_scanner"
    description: str = "Detect PII and sensitive data in datasets"

    # PII patterns
    PATTERNS: ClassVar[Dict[str, str]] = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",
        "ip_address": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        "date_of_birth": r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b",
    }

    # Sensitive field name indicators
    SENSITIVE_FIELD_NAMES: ClassVar[Set[str]] = {
        "ssn",
        "social_security",
        "social_security_number",
        "credit_card",
        "card_number",
        "cc_number",
        "email",
        "email_address",
        "e_mail",
        "phone",
        "phone_number",
        "telephone",
        "mobile",
        "date_of_birth",
        "dob",
        "birth_date",
        "birthdate",
        "password",
        "pwd",
        "pass",
        "secret",
        "salary",
        "income",
        "wage",
        "compensation",
        "address",
        "street",
        "city",
        "zip",
        "postal_code",
    }

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="pii_scanner",
            description="Scan and detect PII in data",
            tool_class=cls,
            categories=["security", "validation", "compliance"],
            required_params=[],
            optional_params=["deep_scan"],
            context_aware=True,
            async_tool=False,
        )

    def run(
        self, data: List[Dict[str, Any]], field_names: List[str], deep_scan: bool = True
    ) -> Dict[str, Any]:
        """
        Scan data for PII.

        Args:
            data: Sample data records to scan
            field_names: All field names in dataset
            deep_scan: Whether to scan actual values

        Returns:
            PII detection results
        """
        results = {
            "pii_fields": [],
            "sensitive_fields": [],
            "detection_details": {},
            "risk_level": "low",
            "recommendations": [],
        }

        # Check field names
        for field in field_names:
            field_lower = field.lower()

            # Check against sensitive field names
            for sensitive_name in self.SENSITIVE_FIELD_NAMES:
                if sensitive_name in field_lower:
                    results["sensitive_fields"].append(
                        {"field": field, "type": sensitive_name, "confidence": "high"}
                    )
                    break

        # Deep scan actual values
        if deep_scan and data:
            pii_detections = {}

            for record in data[:100]:  # Limit scan size
                for field, value in record.items():
                    if value and isinstance(value, str):
                        # Check against PII patterns
                        for pii_type, pattern in self.PATTERNS.items():
                            if re.search(pattern, str(value)):
                                if field not in pii_detections:
                                    pii_detections[field] = set()
                                pii_detections[field].add(pii_type)

            # Convert to results format
            for field, pii_types in pii_detections.items():
                results["pii_fields"].append(
                    {
                        "field": field,
                        "pii_types": list(pii_types),
                        "confidence": "high" if len(pii_types) > 1 else "medium",
                    }
                )

        # Determine risk level
        total_sensitive = len(results["sensitive_fields"]) + len(results["pii_fields"])
        if total_sensitive >= 5:
            results["risk_level"] = "high"
        elif total_sensitive >= 2:
            results["risk_level"] = "medium"

        # Add recommendations
        if results["risk_level"] in ["medium", "high"]:
            results["recommendations"].extend(
                [
                    "Implement data masking for PII fields",
                    "Ensure encryption at rest and in transit",
                    "Limit access to sensitive fields",
                    "Consider tokenization for highly sensitive data",
                ]
            )

        return results
