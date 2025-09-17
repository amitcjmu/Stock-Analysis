"""
Utility functions for field mapping service.

This module contains helper functions and utilities used across
the field mapping service components.
"""

import re
from typing import Any, Dict, List, Set, Tuple
from difflib import SequenceMatcher

from .base import BASE_MAPPINGS, REQUIRED_FIELDS


def calculate_field_similarity(field1: str, field2: str) -> float:
    """
    Calculate similarity between two field names.

    Args:
        field1: First field name
        field2: Second field name

    Returns:
        Similarity score between 0 and 1
    """
    # Normalize fields
    norm1 = normalize_field_name(field1)
    norm2 = normalize_field_name(field2)

    # Exact match
    if norm1 == norm2:
        return 1.0

    # Use sequence matcher for similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()

    # Boost similarity for common patterns
    if _check_common_patterns(norm1, norm2):
        similarity = min(1.0, similarity + 0.2)

    return similarity


def normalize_field_name(field_name: str) -> str:
    """
    Normalize field name for comparison.

    Args:
        field_name: Field name to normalize

    Returns:
        Normalized field name
    """
    if not field_name:
        return ""

    return field_name.lower().strip().replace(" ", "_").replace("-", "_")


def extract_field_components(field_name: str) -> Set[str]:
    """
    Extract meaningful components from a field name.

    Args:
        field_name: Field name to extract components from

    Returns:
        Set of field components
    """
    normalized = normalize_field_name(field_name)

    # Split on common separators
    components = set()
    for part in re.split(r"[_\-\s]+", normalized):
        if part and len(part) > 1:  # Ignore single characters
            components.add(part)

    # Add the full normalized name
    components.add(normalized)

    return components


def find_fuzzy_matches(
    field_name: str, candidate_fields: List[str], threshold: float = 0.6
) -> List[Tuple[str, float]]:
    """
    Find fuzzy matches for a field name among candidates.

    Args:
        field_name: Field name to match
        candidate_fields: List of candidate field names
        threshold: Minimum similarity threshold

    Returns:
        List of (field, similarity_score) tuples sorted by score
    """
    matches = []

    for candidate in candidate_fields:
        similarity = calculate_field_similarity(field_name, candidate)
        if similarity >= threshold:
            matches.append((candidate, similarity))

    # Sort by similarity score, descending
    return sorted(matches, key=lambda x: x[1], reverse=True)


def get_asset_type_priority_fields(asset_type: str) -> List[str]:
    """
    Get priority fields for a specific asset type.

    Args:
        asset_type: Type of asset

    Returns:
        List of priority field names
    """
    required = REQUIRED_FIELDS.get(asset_type, [])
    all_fields = list(BASE_MAPPINGS.keys())

    # Return required fields first, then others
    priority_fields = required + [f for f in all_fields if f not in required]
    return priority_fields


def suggest_field_corrections(field_name: str, max_suggestions: int = 3) -> List[str]:
    """
    Suggest corrections for a field name based on common mappings.

    Args:
        field_name: Field name to suggest corrections for
        max_suggestions: Maximum number of suggestions

    Returns:
        List of suggested field names
    """
    suggestions = []
    field_components = extract_field_components(field_name)

    # Check each base mapping
    for canonical, variations in BASE_MAPPINGS.items():
        canonical_components = extract_field_components(canonical)

        # Check for component overlap
        if field_components & canonical_components:
            suggestions.append(canonical)

        # Check against variations
        for variation in variations:
            variation_components = extract_field_components(variation)
            if field_components & variation_components:
                if canonical not in suggestions:
                    suggestions.append(canonical)
                break

    # Use fuzzy matching as fallback
    if len(suggestions) < max_suggestions:
        all_canonical = list(BASE_MAPPINGS.keys())
        fuzzy_matches = find_fuzzy_matches(field_name, all_canonical, threshold=0.4)

        for match, _ in fuzzy_matches:
            if match not in suggestions:
                suggestions.append(match)
                if len(suggestions) >= max_suggestions:
                    break

    return suggestions[:max_suggestions]


def analyze_field_patterns(fields: List[str]) -> Dict[str, Any]:
    """
    Analyze patterns in a list of field names.

    Args:
        fields: List of field names to analyze

    Returns:
        Dictionary with pattern analysis results
    """
    if not fields:
        return {"patterns": [], "common_prefixes": [], "common_suffixes": []}

    # Normalize all fields
    normalized_fields = [normalize_field_name(f) for f in fields]

    # Find common patterns
    common_prefixes = set()
    common_suffixes = set()

    # Analyze prefixes and suffixes
    for field in normalized_fields:
        parts = field.split("_")
        if len(parts) > 1:
            common_prefixes.add(parts[0])
            common_suffixes.add(parts[-1])

    # Find frequently occurring patterns
    component_counts = {}
    for field in normalized_fields:
        components = extract_field_components(field)
        for component in components:
            component_counts[component] = component_counts.get(component, 0) + 1

    # Identify common patterns (appearing in multiple fields)
    frequent_components = [
        component
        for component, count in component_counts.items()
        if count > 1 and len(component) > 2
    ]

    return {
        "total_fields": len(fields),
        "patterns": frequent_components,
        "common_prefixes": list(common_prefixes),
        "common_suffixes": list(common_suffixes),
        "component_frequency": component_counts,
    }


def validate_field_name_format(field_name: str) -> Dict[str, Any]:
    """
    Validate the format of a field name.

    Args:
        field_name: Field name to validate

    Returns:
        Validation result with issues and suggestions
    """
    issues = []
    suggestions = []

    if not field_name:
        issues.append("Field name is empty")
        return {"valid": False, "issues": issues, "suggestions": suggestions}

    # Check for problematic characters
    if re.search(r"[^\w\-_\s]", field_name):
        issues.append("Contains special characters")
        suggestions.append("Use only letters, numbers, hyphens, and underscores")

    # Check for spaces (prefer underscores)
    if " " in field_name:
        suggestions.append(
            f"Consider using underscores: {field_name.replace(' ', '_')}"
        )

    # Check for mixed case (prefer lowercase)
    if field_name != field_name.lower():
        suggestions.append(f"Consider lowercase: {field_name.lower()}")

    # Check length
    if len(field_name) > 50:
        issues.append("Field name is very long")
        suggestions.append("Consider shortening the field name")
    elif len(field_name) < 2:
        issues.append("Field name is too short")

    # Check for common abbreviations that could be expanded
    abbreviations = {
        "id": "identifier",
        "addr": "address",
        "num": "number",
        "qty": "quantity",
        "amt": "amount",
    }

    for abbr, full in abbreviations.items():
        if abbr in field_name.lower():
            suggestions.append(f"Consider expanding '{abbr}' to '{full}'")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "normalized": normalize_field_name(field_name),
    }


def _check_common_patterns(field1: str, field2: str) -> bool:
    """Check for common field name patterns that indicate similarity."""
    # Common abbreviation patterns
    patterns = [
        ("ip", "ip_address"),
        ("addr", "address"),
        ("os", "operating_system"),
        ("cpu", "cpu_cores"),
        ("mem", "memory"),
        ("ram", "memory"),
        ("hdd", "storage"),
        ("disk", "storage"),
        ("srv", "server"),
        ("app", "application"),
        ("db", "database"),
    ]

    for short, long in patterns:
        if (short in field1 and long in field2) or (long in field1 and short in field2):
            return True

    return False


def get_field_type_hints(field_name: str) -> Dict[str, Any]:
    """
    Get type hints for a field based on its name.

    Args:
        field_name: Field name to analyze

    Returns:
        Dictionary with type hints and suggestions
    """
    normalized = normalize_field_name(field_name)

    # Default hints
    hints = {
        "suggested_type": "string",
        "likely_nullable": True,
        "validation_suggestions": [],
        "format_hints": [],
    }

    # Numeric fields
    if any(
        term in normalized
        for term in ["count", "size", "number", "cores", "gb", "mb", "kb"]
    ):
        hints["suggested_type"] = "number"
        hints["likely_nullable"] = False
        hints["validation_suggestions"].append("Validate as positive number")

    # Boolean fields
    if any(term in normalized for term in ["is_", "has_", "enabled", "active", "flag"]):
        hints["suggested_type"] = "boolean"
        hints["likely_nullable"] = False

    # Date fields
    if any(
        term in normalized
        for term in ["date", "time", "created", "updated", "timestamp"]
    ):
        hints["suggested_type"] = "datetime"
        hints["format_hints"].append("ISO 8601 format recommended")

    # Email fields
    if "email" in normalized or "mail" in normalized:
        hints["validation_suggestions"].append("Validate email format")
        hints["format_hints"].append("Valid email address required")

    # IP address fields
    if "ip" in normalized or "address" in normalized:
        hints["validation_suggestions"].append("Validate IP address format")
        hints["format_hints"].append("IPv4 or IPv6 format")

    # URL fields
    if "url" in normalized or "uri" in normalized or "endpoint" in normalized:
        hints["validation_suggestions"].append("Validate URL format")
        hints["format_hints"].append("Valid URL with protocol")

    return hints
