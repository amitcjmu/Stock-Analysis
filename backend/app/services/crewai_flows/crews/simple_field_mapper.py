"""
Simple Field Mapper - Non-LLM based field mapping
Provides basic field mapping without using LLM calls to avoid rate limits.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SimpleFieldMapper:
    """
    Simple rule-based field mapper that doesn't use LLMs.
    Maps common field patterns to Asset model fields.
    """

    # Common field mappings based on patterns
    FIELD_MAPPINGS = {
        # Exact matches for known CSV fields (case-insensitive)
        r"^(?i)app_id$": "application_id",
        r"^(?i)app_name$": "application_name",
        r"^(?i)app_version$": "version",
        r"^(?i)owner_group$": "owner",
        r"^(?i)scan_date$": "scan_date",
        r"^(?i)port_usage$": "port",
        r"^(?i)last_update$": "last_modified",
        r"^(?i)dependency_list$": "dependencies",
        r"^(?i)scan_status$": "status",
        # Identity mappings
        r"(?i)(name|asset.*name|server.*name|hostname|host)": "asset_name",
        r"(?i)(id|asset.*id|server.*id)": "asset_id",
        r"(?i)(fqdn|fully.*qualified)": "fqdn",
        # Network mappings
        r"(?i)(ip.*address|ip|ipv4|ipv6)": "ip_address",
        r"(?i)(mac.*address|mac)": "mac_address",
        # Classification mappings
        r"(?i)(type|asset.*type|server.*type|category)": "asset_type",
        r"(?i)(description|desc|notes|comment)": "description",
        r"(?i)(technology|tech.*stack|stack|platform)": "technology_stack",
        # Location mappings
        r"(?i)(environment|env)": "environment",
        r"(?i)(location|site|datacenter|dc)": "location",
        r"(?i)(rack|rack.*location)": "rack_location",
        r"(?i)(zone|availability.*zone|az)": "availability_zone",
        # Hardware mappings
        r"(?i)(os|operating.*system)": "operating_system",
        r"(?i)(os.*version|version)": "os_version",
        r"(?i)(cpu|cores|vcpu|processor)": "cpu_cores",
        r"(?i)(memory|ram|mem).*gb": "memory_gb",
        r"(?i)(storage|disk|hdd|ssd).*gb": "storage_gb",
        # Business mappings
        r"(?i)(business.*owner|biz.*owner)": "business_owner",
        r"(?i)(technical.*owner|tech.*owner|it.*owner)": "technical_owner",
        r"(?i)(department|dept|org|organization)": "department",
        r"(?i)(application|app.*name|service)": "application_name",
        r"(?i)(criticality|priority|importance)": "criticality",
        # Status mappings
        r"(?i)(status|state)": "status",
    }

    # Fields to skip (metadata)
    SKIP_FIELDS = [
        r"(?i)(row.*index|index|row.*number|line.*number)",
        r"(?i)(timestamp|date.*created|date.*modified)",
        r"(?i)(checksum|hash|md5|sha)",
    ]

    def map_fields(self, headers: List[str]) -> Dict[str, Any]:
        """
        Map source headers to Asset model fields using pattern matching.
        Returns structure compatible with parse_field_mapping_results.

        Args:
            headers: List of source field headers

        Returns:
            Dictionary of field mappings in the correct structure
        """
        mappings = {}
        confidence_scores = {}
        agent_reasoning = {}
        skipped_fields = []
        unmapped_fields = []

        for header in headers:
            # Check if field should be skipped
            skip = False
            for skip_pattern in self.SKIP_FIELDS:
                if re.match(skip_pattern, header):
                    skipped_fields.append(header)
                    skip = True
                    break

            if skip:
                continue

            # Try to map the field
            mapped = False
            for pattern, target_field in self.FIELD_MAPPINGS.items():
                if re.match(pattern, header):
                    # Store in the format expected by parse_field_mapping_results
                    mappings[header] = target_field
                    confidence_scores[header] = (
                        0.8  # Fixed confidence for rule-based mapping
                    )
                    agent_reasoning[header] = {
                        "reasoning": f"Pattern match: {header} matches {target_field} pattern",
                        "requires_transformation": False,
                        "data_patterns": {"match_type": "pattern", "pattern": pattern},
                    }
                    mapped = True
                    break

            if not mapped:
                unmapped_fields.append(header)

        logger.info(
            f"Simple field mapping complete: {len(mappings)} mapped, "
            f"{len(skipped_fields)} skipped, {len(unmapped_fields)} unmapped"
        )

        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "agent_reasoning": agent_reasoning,
            "skipped_fields": skipped_fields,
            "unmapped_fields": unmapped_fields,
            "synthesis_required": [],  # No synthesis in simple mapper
            "transformations": [],  # No transformations in simple mapper
            "validation_results": {
                "valid": len(mappings) > 0,
                "score": len(mappings) / len(headers) if headers else 0.0,
                "coverage": len(mappings) / len(headers) if headers else 0.0,
                "avg_confidence": 0.8 if mappings else 0.0,
            },
            "agent_insights": {
                "crew_execution": "Simple rule-based fallback mapper",
                "source": "simple_field_mapper",
                "agents": ["Pattern Matcher"],
                "fallback_reason": "CrewAI unavailable or rate limited",
            },
        }


def get_simple_field_mappings(raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get field mappings using simple pattern matching without LLM calls.

    Args:
        raw_data: List of raw data records

    Returns:
        Field mapping results
    """
    if not raw_data:
        return {
            "mappings": {},
            "skipped_fields": [],
            "unmapped_fields": [],
            "synthesis_required": [],
        }

    headers = list(raw_data[0].keys())
    mapper = SimpleFieldMapper()

    return mapper.map_fields(headers)
