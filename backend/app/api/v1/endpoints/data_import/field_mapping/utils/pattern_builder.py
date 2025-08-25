"""
Field pattern builder utility for intelligent field mapping.
Now uses pluggable pattern providers for extensible field mapping strategies.
"""

import logging
from typing import Dict, List, Optional

from .pattern_provider import (
    FieldPatternProvider,
    configure_pattern_manager,
    get_pattern_manager,
)

logger = logging.getLogger(__name__)


class FieldPatternBuilder:
    """Builder for creating field mapping patterns using pluggable providers."""

    @staticmethod
    def build_field_patterns(
        target_field_names: List[str],
        learned_patterns: Optional[Dict[str, List[str]]] = None,
        custom_providers: Optional[List[FieldPatternProvider]] = None,
    ) -> Dict[str, List[str]]:
        """
        Build field mapping patterns based on available target fields.

        Args:
            target_field_names: List of target field names to generate patterns for
            learned_patterns: Optional dictionary of learned patterns from historical mappings
            custom_providers: Optional list of custom pattern providers

        Returns:
            Dictionary mapping target field names to lists of possible source field patterns
        """
        # Configure pattern manager if custom settings provided
        if learned_patterns or custom_providers:
            configure_pattern_manager(
                learned_patterns=learned_patterns, custom_providers=custom_providers
            )

        # Get the pattern manager and build patterns
        pattern_manager = get_pattern_manager()

        try:
            patterns = pattern_manager.build_field_patterns(target_field_names)
            logger.info(
                f"Generated patterns for {len(target_field_names)} target fields using pluggable providers"
            )
            return patterns
        except Exception as e:
            logger.error(f"Error building field patterns: {e}")
            # Fallback to legacy static patterns in case of error
            return FieldPatternBuilder._build_legacy_patterns(target_field_names)

    @staticmethod
    def _build_legacy_patterns(target_field_names: List[str]) -> Dict[str, List[str]]:
        """
        Legacy fallback pattern builder for backward compatibility.
        This method preserves the original static heuristic behavior.
        """
        logger.warning("Using legacy pattern builder as fallback")
        patterns = {}

        for target_field in target_field_names:
            # Create variations of the target field name for pattern matching
            field_patterns = [target_field.lower()]

            # Add common variations
            if "_" in target_field:
                field_patterns.append(target_field.replace("_", ""))
                field_patterns.append(target_field.replace("_", " "))

            # Add specific patterns for common fields
            if "hostname" in target_field.lower():
                field_patterns.extend(
                    ["host_name", "server_name", "servername", "name", "host", "server"]
                )
            elif "ip_address" in target_field.lower():
                field_patterns.extend(
                    ["ip", "ipaddress", "ip_addr", "address", "private_ip", "public_ip"]
                )
            elif (
                "operating_system" in target_field.lower()
                or target_field.lower() == "os"
            ):
                field_patterns.extend(
                    ["os", "os_name", "operating_sys", "platform", "os_type", "system"]
                )
            elif "cpu" in target_field.lower():
                field_patterns.extend(
                    [
                        "cpu",
                        "cores",
                        "processors",
                        "vcpu",
                        "cpu_count",
                        "num_cpus",
                        "cpus",
                    ]
                )
            elif "memory" in target_field.lower() or "ram" in target_field.lower():
                field_patterns.extend(
                    [
                        "memory",
                        "ram",
                        "ram_gb",
                        "mem",
                        "total_memory",
                        "memory_size",
                        "ram (gb)",
                    ]
                )
            elif "storage" in target_field.lower() or "disk" in target_field.lower():
                field_patterns.extend(
                    [
                        "storage",
                        "disk",
                        "disk_gb",
                        "disk_space",
                        "total_storage",
                        "disk_size",
                    ]
                )

            patterns[target_field] = field_patterns

        return patterns

    @staticmethod
    def add_learned_pattern(target_field: str, source_patterns: List[str]) -> None:
        """
        Add a learned pattern to the pattern manager.

        Args:
            target_field: The target field name
            source_patterns: List of source field patterns that map to this target
        """
        try:
            pattern_manager = get_pattern_manager()
            pattern_manager.update_learned_patterns({target_field: source_patterns})
            logger.info(
                f"Added learned patterns for field '{target_field}': {source_patterns}"
            )
        except Exception as e:
            logger.error(f"Error adding learned pattern for '{target_field}': {e}")

    @staticmethod
    def register_custom_provider(provider: FieldPatternProvider) -> None:
        """
        Register a custom pattern provider.

        Args:
            provider: Custom pattern provider to register
        """
        try:
            pattern_manager = get_pattern_manager()
            pattern_manager.register_provider(provider)
            logger.info(
                f"Registered custom pattern provider: {provider.__class__.__name__}"
            )
        except Exception as e:
            logger.error(f"Error registering custom provider: {e}")
