"""
Pluggable pattern provider for field mapping heuristics.
Allows for configurable and extensible field pattern matching strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FieldPatternProvider(ABC):
    """Abstract base class for field pattern providers."""

    @abstractmethod
    def get_patterns(self, target_field: str) -> List[str]:
        """Get field mapping patterns for a given target field."""
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """Get the priority of this provider (higher number = higher priority)."""
        pass


class LearnedPatternProvider(FieldPatternProvider):
    """Provider that uses learned patterns from historical mappings."""

    def __init__(self, learned_patterns: Optional[Dict[str, List[str]]] = None):
        self.learned_patterns = learned_patterns or {}

    def get_patterns(self, target_field: str) -> List[str]:
        """Get learned patterns for the target field."""
        return self.learned_patterns.get(target_field.lower(), [])

    def get_priority(self) -> int:
        """Learned patterns have the highest priority."""
        return 100

    def add_learned_pattern(
        self, target_field: str, source_patterns: List[str]
    ) -> None:
        """Add a learned pattern for a target field."""
        if target_field.lower() not in self.learned_patterns:
            self.learned_patterns[target_field.lower()] = []

        # Add new patterns that aren't already present
        existing = set(self.learned_patterns[target_field.lower()])
        for pattern in source_patterns:
            if pattern.lower() not in existing:
                self.learned_patterns[target_field.lower()].append(pattern.lower())


class HeuristicPatternProvider(FieldPatternProvider):
    """Provider that uses rule-based heuristic patterns."""

    def __init__(self, pattern_config: Optional[Dict[str, List[str]]] = None):
        self.pattern_config = pattern_config or self._get_default_patterns()

    def get_patterns(self, target_field: str) -> List[str]:
        """Get heuristic patterns for the target field."""
        patterns = []

        # Add basic variations
        patterns.append(target_field.lower())

        # Add underscore/space variations
        if "_" in target_field:
            patterns.append(target_field.replace("_", ""))
            patterns.append(target_field.replace("_", " "))

        # Add configured specific patterns
        for pattern_key, pattern_list in self.pattern_config.items():
            if pattern_key.lower() in target_field.lower():
                patterns.extend(pattern_list)

        return patterns

    def get_priority(self) -> int:
        """Heuristic patterns have medium priority."""
        return 50

    def _get_default_patterns(self) -> Dict[str, List[str]]:
        """Get default heuristic pattern configuration."""
        return {
            "hostname": [
                "host_name",
                "server_name",
                "servername",
                "name",
                "host",
                "server",
            ],
            "ip_address": [
                "ip",
                "ipaddress",
                "ip_addr",
                "address",
                "private_ip",
                "public_ip",
            ],
            "operating_system": [
                "os",
                "os_name",
                "operating_sys",
                "platform",
                "os_type",
                "system",
            ],
            "os": ["os", "os_name", "operating_sys", "platform", "os_type", "system"],
            "cpu": [
                "cpu",
                "cores",
                "processors",
                "vcpu",
                "cpu_count",
                "num_cpus",
                "cpus",
            ],
            "memory": [
                "memory",
                "ram",
                "ram_gb",
                "mem",
                "total_memory",
                "memory_size",
                "ram (gb)",
            ],
            "ram": [
                "memory",
                "ram",
                "ram_gb",
                "mem",
                "total_memory",
                "memory_size",
                "ram (gb)",
            ],
            "storage": [
                "storage",
                "disk",
                "disk_gb",
                "disk_space",
                "total_storage",
                "disk_size",
            ],
            "disk": [
                "storage",
                "disk",
                "disk_gb",
                "disk_space",
                "total_storage",
                "disk_size",
            ],
        }


class FallbackPatternProvider(FieldPatternProvider):
    """Fallback provider that provides basic name variations."""

    def get_patterns(self, target_field: str) -> List[str]:
        """Get basic fallback patterns."""
        patterns = [target_field.lower()]

        # Add basic variations
        if "_" in target_field:
            patterns.append(target_field.replace("_", ""))
            patterns.append(target_field.replace("_", " "))

        if " " in target_field:
            patterns.append(target_field.replace(" ", "_"))
            patterns.append(target_field.replace(" ", ""))

        return patterns

    def get_priority(self) -> int:
        """Fallback patterns have lowest priority."""
        return 10


class PluggablePatternManager:
    """Manager for pluggable field pattern providers."""

    def __init__(self):
        self.providers: List[FieldPatternProvider] = []
        self._register_default_providers()

    def register_provider(self, provider: FieldPatternProvider) -> None:
        """Register a new pattern provider."""
        self.providers.append(provider)
        # Sort by priority (highest first)
        self.providers.sort(key=lambda p: p.get_priority(), reverse=True)
        logger.info(
            f"Registered pattern provider: {provider.__class__.__name__} with priority {provider.get_priority()}"
        )

    def get_patterns(self, target_field: str) -> List[str]:
        """Get patterns for a target field from all providers."""
        all_patterns = []
        seen_patterns = set()

        # Collect patterns from all providers (already sorted by priority)
        for provider in self.providers:
            try:
                provider_patterns = provider.get_patterns(target_field)
                for pattern in provider_patterns:
                    if pattern.lower() not in seen_patterns:
                        all_patterns.append(pattern.lower())
                        seen_patterns.add(pattern.lower())
            except Exception as e:
                logger.warning(
                    f"Error getting patterns from {provider.__class__.__name__}: {e}"
                )

        return all_patterns

    def build_field_patterns(
        self, target_field_names: List[str]
    ) -> Dict[str, List[str]]:
        """Build field mapping patterns for multiple target fields."""
        patterns = {}

        for target_field in target_field_names:
            patterns[target_field] = self.get_patterns(target_field)

        return patterns

    def _register_default_providers(self) -> None:
        """Register default pattern providers."""
        # Register in order of decreasing priority
        self.register_provider(LearnedPatternProvider())
        self.register_provider(HeuristicPatternProvider())
        self.register_provider(FallbackPatternProvider())

    def update_learned_patterns(self, learned_patterns: Dict[str, List[str]]) -> None:
        """Update learned patterns in the learned pattern provider."""
        for provider in self.providers:
            if isinstance(provider, LearnedPatternProvider):
                for target_field, source_patterns in learned_patterns.items():
                    provider.add_learned_pattern(target_field, source_patterns)
                break


# Global pattern manager instance
_pattern_manager = None


def get_pattern_manager() -> PluggablePatternManager:
    """Get the global pattern manager instance."""
    global _pattern_manager
    if _pattern_manager is None:
        _pattern_manager = PluggablePatternManager()
    return _pattern_manager


def configure_pattern_manager(
    learned_patterns: Optional[Dict[str, List[str]]] = None,
    heuristic_config: Optional[Dict[str, List[str]]] = None,
    custom_providers: Optional[List[FieldPatternProvider]] = None,
) -> None:
    """Configure the global pattern manager with custom settings."""
    global _pattern_manager
    _pattern_manager = PluggablePatternManager()

    # Register custom providers first (they'll have highest priority if configured correctly)
    if custom_providers:
        for provider in custom_providers:
            _pattern_manager.register_provider(provider)

    # Update learned patterns if provided
    if learned_patterns:
        _pattern_manager.update_learned_patterns(learned_patterns)

    # Update heuristic config if provided
    if heuristic_config:
        for provider in _pattern_manager.providers:
            if isinstance(provider, HeuristicPatternProvider):
                provider.pattern_config.update(heuristic_config)
                break
