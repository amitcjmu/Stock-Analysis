"""
Gap Report Caching Service

Implements Redis caching for ComprehensiveGapReport to improve performance.
TTL: 5 minutes (balances performance with data freshness).

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 16
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #8 (JSON safety)
"""

import hashlib
import json
import logging
from typing import Optional
from uuid import UUID

from app.services.gap_detection.schemas import ComprehensiveGapReport

logger = logging.getLogger(__name__)

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


class GapReportCache:
    """
    Redis-based caching for ComprehensiveGapReport.

    Cache Key Format:
        gap_report:{client_account_id}:{engagement_id}:{asset_id}:{hash}

    The hash component ensures cache invalidation when underlying data changes.

    Performance Impact:
    - Cache HIT: <5ms (vs 35-45ms for full analysis)
    - Cache MISS: 35-45ms + 2ms cache write
    - Hit Rate Target: >80% for typical engagements
    """

    def __init__(self, redis_client=None):
        """
        Initialize cache service.

        Args:
            redis_client: Redis client instance (optional for testing)
        """
        self._redis = redis_client
        self._enabled = redis_client is not None

        if not self._enabled:
            logger.warning("Gap report cache disabled - no Redis client provided")

    def _generate_cache_key(
        self,
        client_account_id: UUID,
        engagement_id: UUID,
        asset_id: UUID,
        data_hash: str,
    ) -> str:
        """
        Generate cache key with tenant scoping and data versioning.

        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            asset_id: Asset UUID
            data_hash: Hash of asset + application data

        Returns:
            Cache key string
        """
        return f"gap_report:{client_account_id}:{engagement_id}:{asset_id}:{data_hash}"

    def _compute_data_hash(self, asset_data: dict, application_data: dict) -> str:
        """
        Compute hash of asset and application data for cache versioning.

        This ensures cache is automatically invalidated when underlying data changes.

        Args:
            asset_data: Asset fields relevant to gap detection
            application_data: Application enrichment fields

        Returns:
            SHA256 hash (first 16 chars)
        """
        # Extract only fields that affect gap detection
        relevant_data = {
            "asset": {
                "operating_system": asset_data.get("operating_system"),
                "ip_address": asset_data.get("ip_address"),
                "hostname": asset_data.get("hostname"),
                "environment": asset_data.get("environment"),
            },
            "application": application_data if application_data else {},
        }

        # Serialize to JSON and hash
        json_str = json.dumps(relevant_data, sort_keys=True)
        hash_obj = hashlib.sha256(json_str.encode())
        return hash_obj.hexdigest()[:16]  # First 16 chars sufficient

    async def get(
        self,
        client_account_id: UUID,
        engagement_id: UUID,
        asset_id: UUID,
        asset_data: dict,
        application_data: dict,
    ) -> Optional[ComprehensiveGapReport]:
        """
        Retrieve cached gap report if available.

        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            asset_id: Asset UUID
            asset_data: Current asset data
            application_data: Current application data

        Returns:
            ComprehensiveGapReport if cached, None otherwise
        """
        if not self._enabled:
            return None

        try:
            data_hash = self._compute_data_hash(asset_data, application_data)
            cache_key = self._generate_cache_key(
                client_account_id, engagement_id, asset_id, data_hash
            )

            cached_json = await self._redis.get(cache_key)
            if cached_json:
                logger.debug(f"Cache HIT for asset {asset_id}")
                return ComprehensiveGapReport.model_validate_json(cached_json)

            logger.debug(f"Cache MISS for asset {asset_id}")
            return None

        except Exception as e:
            logger.error(f"Cache retrieval error: {e}", exc_info=True)
            return None  # Graceful degradation

    async def set(
        self,
        client_account_id: UUID,
        engagement_id: UUID,
        asset_id: UUID,
        asset_data: dict,
        application_data: dict,
        report: ComprehensiveGapReport,
    ) -> bool:
        """
        Cache gap report with TTL.

        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            asset_id: Asset UUID
            asset_data: Asset data used for hash
            application_data: Application data used for hash
            report: ComprehensiveGapReport to cache

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._enabled:
            return False

        try:
            data_hash = self._compute_data_hash(asset_data, application_data)
            cache_key = self._generate_cache_key(
                client_account_id, engagement_id, asset_id, data_hash
            )

            report_json = report.model_dump_json()
            await self._redis.setex(cache_key, CACHE_TTL, report_json)

            logger.debug(f"Cached gap report for asset {asset_id} (TTL: {CACHE_TTL}s)")
            return True

        except Exception as e:
            logger.error(f"Cache write error: {e}", exc_info=True)
            return False  # Graceful degradation

    async def invalidate(
        self,
        client_account_id: UUID,
        engagement_id: UUID,
        asset_id: UUID,
    ) -> bool:
        """
        Invalidate all cached reports for an asset.

        Useful when asset data is updated and we want to force re-analysis.

        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            asset_id: Asset UUID

        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self._enabled:
            return False

        try:
            # Pattern to match all cache keys for this asset
            pattern = f"gap_report:{client_account_id}:{engagement_id}:{asset_id}:*"

            # Scan and delete matching keys
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            logger.info(
                f"Invalidated {deleted_count} cached reports for asset {asset_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}", exc_info=True)
            return False

    async def invalidate_engagement(
        self,
        client_account_id: UUID,
        engagement_id: UUID,
    ) -> bool:
        """
        Invalidate all cached reports for an engagement.

        Useful when engagement standards change.

        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID

        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self._enabled:
            return False

        try:
            pattern = f"gap_report:{client_account_id}:{engagement_id}:*"

            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break

            logger.info(
                f"Invalidated {deleted_count} cached reports for engagement {engagement_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Engagement cache invalidation error: {e}", exc_info=True)
            return False


__all__ = ["GapReportCache", "CACHE_TTL"]
