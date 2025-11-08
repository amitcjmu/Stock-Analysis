"""
RequirementsEngine - Context-aware requirements aggregation.

Merges requirements from multiple contexts (asset type, 6R strategy, compliance, criticality).
Uses @lru_cache for <1ms lookups.

Performance: <1ms per lookup (cached)

Usage:
    engine = RequirementsEngine()
    reqs = await engine.get_requirements(
        asset_type="application",
        six_r_strategy="refactor",
        compliance_scopes=["PCI-DSS"],
        criticality="tier_1_critical",
    )
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from app.services.gap_detection.schemas import DataRequirements
from .asset_type_matrix import ASSET_TYPE_REQUIREMENTS
from .compliance_matrix import COMPLIANCE_REQUIREMENTS
from .criticality_matrix import CRITICALITY_REQUIREMENTS
from .six_r_strategy_matrix import SIX_R_STRATEGY_REQUIREMENTS

logger = logging.getLogger(__name__)


class RequirementsEngine:
    """
    Aggregates context-aware requirements for gap detection.

    This engine merges requirements from multiple contexts:
    1. Asset type (server, database, application, network, storage, container)
    2. 6R strategy (rehost, replatform, refactor, repurchase, retire, retain)
    3. Compliance scope (PCI-DSS, HIPAA, SOC2, GDPR, ISO27001)
    4. Criticality tier (tier_1_critical, tier_2_important, tier_3_standard)

    Performance:
    - Uses @lru_cache with maxsize=256 for <1ms lookups
    - Arguments must be hashable (tuples, not lists)
    - Cache key includes all context dimensions

    Example:
        engine = RequirementsEngine()
        reqs = await engine.get_requirements(
            asset_type="application",
            six_r_strategy="refactor",
            compliance_scopes=["PCI-DSS"],
            criticality="tier_1_critical",
        )
        # reqs.required_columns = ["technology_stack", "architecture_pattern", ...]
        # reqs.completeness_threshold = 0.90 (highest of all contexts)
    """

    @lru_cache(maxsize=256)
    def _get_requirements_cached(
        self,
        asset_type: str,
        six_r_strategy: Optional[str],
        compliance_scopes: Optional[Tuple[str, ...]],  # Tuple for hashability
        criticality: Optional[str],
    ) -> DataRequirements:
        """
        Cached requirements lookup (LRU cache for performance).

        Args MUST be hashable (strings, tuples, NOT lists/dicts).

        Args:
            asset_type: Asset type from AssetType enum
            six_r_strategy: Optional 6R strategy
            compliance_scopes: Optional tuple of compliance scopes (for hashability)
            criticality: Optional criticality tier

        Returns:
            DataRequirements with merged requirements from all contexts
        """
        # Start with asset type base requirements
        merged = ASSET_TYPE_REQUIREMENTS.get(
            asset_type.lower(), ASSET_TYPE_REQUIREMENTS["other"]
        ).copy()

        # Merge 6R strategy requirements
        if six_r_strategy:
            strategy_key = six_r_strategy.lower()
            if strategy_key in SIX_R_STRATEGY_REQUIREMENTS:
                strategy_reqs = SIX_R_STRATEGY_REQUIREMENTS[strategy_key]
                merged = self._merge(merged, strategy_reqs)
                logger.debug(f"Merged 6R strategy '{six_r_strategy}' requirements")

        # Merge compliance requirements
        if compliance_scopes:
            for scope in compliance_scopes:
                if scope in COMPLIANCE_REQUIREMENTS:
                    compliance_reqs = COMPLIANCE_REQUIREMENTS[scope]
                    merged = self._merge(merged, compliance_reqs)
                    logger.debug(f"Merged compliance scope '{scope}' requirements")

        # Merge criticality requirements
        if criticality:
            criticality_key = criticality.lower()
            if criticality_key in CRITICALITY_REQUIREMENTS:
                criticality_reqs = CRITICALITY_REQUIREMENTS[criticality_key]
                merged = self._merge(merged, criticality_reqs)
                logger.debug(f"Merged criticality '{criticality}' requirements")

        # Convert to DataRequirements Pydantic model
        requirements = DataRequirements(
            required_columns=merged.get("required_columns", []),
            required_enrichments=merged.get("required_enrichments", []),
            required_jsonb_keys=merged.get("required_jsonb_keys", {}),
            required_standards=merged.get("required_standards", []),
            priority_weights=merged.get(
                "priority_weights",
                {
                    "columns": 0.50,
                    "enrichments": 0.30,
                    "jsonb": 0.15,
                    "application": 0.00,
                    "standards": 0.05,
                },
            ),
            completeness_threshold=merged.get("completeness_threshold", 0.75),
        )

        logger.info(
            f"Generated requirements for asset_type={asset_type}, "
            f"6r={six_r_strategy}, compliance={compliance_scopes}, criticality={criticality}: "
            f"{len(requirements.required_columns)} columns, "
            f"{len(requirements.required_enrichments)} enrichments, "
            f"{len(requirements.required_standards)} standards, "
            f"threshold={requirements.completeness_threshold}"
        )

        return requirements

    async def get_requirements(
        self,
        asset_type: str,
        six_r_strategy: Optional[str] = None,
        compliance_scopes: Optional[List[str]] = None,
        criticality: Optional[str] = None,
    ) -> DataRequirements:
        """
        Get context-aware requirements (async interface for future DB lookups).

        This method is async to allow for future database-backed requirement lookups
        (e.g., tenant-specific requirement overrides from database).

        Args:
            asset_type: Asset type from AssetType enum (e.g., "server", "application")
            six_r_strategy: Optional 6R strategy (e.g., "rehost", "refactor")
            compliance_scopes: Optional list of compliance scopes (e.g., ["PCI-DSS", "HIPAA"])
            criticality: Optional criticality tier (e.g., "tier_1_critical")

        Returns:
            DataRequirements with merged requirements from all contexts

        Performance:
            - First call: ~5-10ms (computation + cache storage)
            - Subsequent calls: <1ms (cache hit)
            - Cache size: 256 unique context combinations
        """
        # Convert list to tuple for caching (hashable)
        compliance_tuple = tuple(compliance_scopes) if compliance_scopes else None

        # Call cached method
        return self._get_requirements_cached(
            asset_type=asset_type,
            six_r_strategy=six_r_strategy,
            compliance_scopes=compliance_tuple,
            criticality=criticality,
        )

    def _merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two requirement dictionaries.

        Rules:
        - Lists: Union (deduplicated)
        - Dicts: Recursive merge (priority_weights are summed, others are merged)
        - Scalars: Maximum value (for completeness_threshold)

        Args:
            base: Base requirements dictionary
            overlay: Overlay requirements dictionary to merge into base

        Returns:
            Merged requirements dictionary

        Examples:
            >>> base = {"required_columns": ["a", "b"], "completeness_threshold": 0.75}
            >>> overlay = {"required_columns": ["b", "c"], "completeness_threshold": 0.90}
            >>> merged = _merge(base, overlay)
            >>> merged["required_columns"]
            ["a", "b", "c"]  # Deduplicated union
            >>> merged["completeness_threshold"]
            0.90  # Maximum
        """
        merged = base.copy()

        for key, value in overlay.items():
            if key not in merged:
                # Key doesn't exist in base - add it
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Union lists (deduplicate)
                merged[key] = list(set(merged[key] + value))
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # Recursive dict merge
                if key == "priority_weights":
                    # Special handling for priority_weights: sum values (normalized later)
                    merged[key] = self._merge_priority_weights(merged[key], value)
                else:
                    # Standard recursive merge for other dicts
                    merged[key] = self._merge(merged[key], value)
            elif key == "completeness_threshold":
                # Take maximum threshold (most stringent requirement)
                merged[key] = max(merged[key], value)
            else:
                # Overlay wins for scalars
                merged[key] = value

        return merged

    def _merge_priority_weights(
        self, base_weights: Dict[str, float], overlay_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Merge priority weights by averaging (not summing).

        When merging contexts (e.g., asset_type + compliance), we want to
        blend their priority preferences, not add them.

        Args:
            base_weights: Base priority weights
            overlay_weights: Overlay priority weights

        Returns:
            Merged priority weights (averaged)

        Example:
            >>> base = {"columns": 0.5, "enrichments": 0.3}
            >>> overlay = {"enrichments": 0.4, "standards": 0.3}
            >>> merged = _merge_priority_weights(base, overlay)
            >>> merged
            {"columns": 0.5, "enrichments": 0.35, "standards": 0.3}
        """
        merged = base_weights.copy()

        for layer, weight in overlay_weights.items():
            if layer in merged:
                # Average the two weights
                merged[layer] = (merged[layer] + weight) / 2.0
            else:
                # New layer - use overlay weight
                merged[layer] = weight

        return merged

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get LRU cache statistics for monitoring.

        Returns:
            Dict with cache hits, misses, size, and hit rate

        Example:
            >>> engine = RequirementsEngine()
            >>> await engine.get_requirements("server")
            >>> await engine.get_requirements("server")  # Cache hit
            >>> cache_info = engine.get_cache_info()
            >>> cache_info["hit_rate"]
            0.5  # 1 hit out of 2 calls
        """
        cache_info = self._get_requirements_cached.cache_info()
        total_calls = cache_info.hits + cache_info.misses

        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "current_size": cache_info.currsize,
            "max_size": cache_info.maxsize,
            "hit_rate": cache_info.hits / total_calls if total_calls > 0 else 0.0,
        }

    def clear_cache(self) -> None:
        """
        Clear the LRU cache.

        Useful for testing or when requirements matrix is updated.
        """
        self._get_requirements_cached.cache_clear()
        logger.info("RequirementsEngine cache cleared")
