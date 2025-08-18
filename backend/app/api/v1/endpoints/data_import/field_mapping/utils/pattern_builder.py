"""
Field pattern builder utility for intelligent field mapping.
"""

from typing import Dict, List


class FieldPatternBuilder:
    """Builder for creating field mapping patterns."""

    @staticmethod
    def build_field_patterns(target_field_names: List[str]) -> Dict[str, List[str]]:
        """Build field mapping patterns based on available target fields."""
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
