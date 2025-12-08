"""
EOL Lifecycle Service

ADR-039: Provides EOL status for operating systems and vendor products.
Uses endoflife.date API with Redis caching and graceful fallback.
"""

import json
import logging
from datetime import date, timedelta
from typing import Optional

import httpx
from redis.asyncio import Redis

from .fallback_heuristics import fallback_eol_check
from .models import (
    EOLBatchResult,
    EOLDataSource,
    EOLStatus,
    EOLStatusEnum,
    SupportTypeEnum,
)

logger = logging.getLogger(__name__)


# Product name mappings for endoflife.date API
PRODUCT_NAME_MAPPINGS: dict[str, str] = {
    "windows server": "windows-server",
    "windows-server": "windows-server",
    "rhel": "rhel",
    "red hat": "rhel",
    "ubuntu": "ubuntu",
    "debian": "debian",
    "centos": "centos",
    "java": "java",
    "openjdk": "java",
    "oracle java": "java",
    "python": "python",
    "node": "nodejs",
    "nodejs": "nodejs",
    "node.js": "nodejs",
    ".net": "dotnet",
    "dotnet": "dotnet",
    ".net core": "dotnetcore",
    "dotnet core": "dotnetcore",
    ".net framework": "dotnetfx",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "mongodb": "mongodb",
    "redis": "redis",
    "nginx": "nginx",
    "apache": "apache",
    "tomcat": "tomcat",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "docker": "docker",
    "aix": "ibm-aix",
    "solaris": "solaris",
}


class EOLLifecycleService:
    """
    Provides EOL status for operating systems and vendor products.

    Uses endoflife.date API with Redis caching and graceful fallback.
    """

    ENDOFLIFE_API_BASE = "https://endoflife.date/api"
    CACHE_TTL_SECONDS = 86400  # 24 hours
    CACHE_KEY_PREFIX = "eol:v1:"
    API_TIMEOUT_SECONDS = 10.0

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize EOL Lifecycle Service.

        Args:
            redis_client: Optional Redis client for caching.
                          If None, caching is disabled.
        """
        self.redis = redis_client
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.API_TIMEOUT_SECONDS,
                headers={"Accept": "application/json"},
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def _normalize_product_name(self, product: str) -> str:
        """Normalize product name for API lookup."""
        product_lower = product.lower().strip()
        return PRODUCT_NAME_MAPPINGS.get(product_lower, product_lower)

    def _build_cache_key(self, product: str, version: str) -> str:
        """Build Redis cache key for product/version."""
        normalized = self._normalize_product_name(product)
        return f"{self.CACHE_KEY_PREFIX}{normalized}:{version}"

    async def _get_cached(self, product: str, version: str) -> Optional[EOLStatus]:
        """Get cached EOL status."""
        if self.redis is None:
            return None

        try:
            cache_key = self._build_cache_key(product, version)
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return EOLStatus(**data)
        except Exception as e:
            logger.warning(f"Cache read error for {product} {version}: {e}")

        return None

    async def _cache_result(
        self, product: str, version: str, result: EOLStatus
    ) -> None:
        """Cache EOL status result."""
        if self.redis is None:
            return

        try:
            cache_key = self._build_cache_key(product, version)
            # Serialize with custom encoder for dates
            data = result.model_dump(mode="json")
            await self.redis.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps(data),
            )
        except Exception as e:
            logger.warning(f"Cache write error for {product} {version}: {e}")

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string from API response."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, bool):
                return None
            return date.fromisoformat(str(date_str))
        except (ValueError, TypeError):
            return None

    def _calculate_status(
        self,
        eol_date: Optional[date],
        extended_support_end: Optional[date] = None,
    ) -> tuple[EOLStatusEnum, SupportTypeEnum]:
        """Calculate EOL status from dates."""
        today = date.today()
        soon_threshold = today + timedelta(days=365)  # 12 months

        if eol_date is None:
            # No EOL date means still active
            return EOLStatusEnum.ACTIVE, SupportTypeEnum.MAINSTREAM

        if eol_date < today:
            # Past EOL
            if extended_support_end and extended_support_end >= today:
                return EOLStatusEnum.EOL_EXPIRED, SupportTypeEnum.EXTENDED
            return EOLStatusEnum.EOL_EXPIRED, SupportTypeEnum.NONE

        if eol_date <= soon_threshold:
            # Within 12 months
            return EOLStatusEnum.EOL_SOON, SupportTypeEnum.MAINSTREAM

        return EOLStatusEnum.ACTIVE, SupportTypeEnum.MAINSTREAM

    async def _fetch_from_api(self, product: str, version: str) -> Optional[EOLStatus]:
        """Fetch EOL status from endoflife.date API."""
        normalized_product = self._normalize_product_name(product)

        try:
            client = await self._get_http_client()

            # First, try specific version endpoint
            url = f"{self.ENDOFLIFE_API_BASE}/{normalized_product}/{version}.json"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                eol_date = self._parse_date(data.get("eol"))
                extended_support = self._parse_date(data.get("extendedSupport"))
                status, support_type = self._calculate_status(
                    eol_date, extended_support
                )

                return EOLStatus(
                    product=product,
                    version=version,
                    product_type=(
                        "os"
                        if normalized_product
                        in (
                            "windows-server",
                            "rhel",
                            "ubuntu",
                            "debian",
                            "centos",
                            "ibm-aix",
                            "solaris",
                        )
                        else "runtime"
                    ),
                    status=status,
                    eol_date=eol_date,
                    extended_support_end=extended_support,
                    support_type=support_type,
                    source=EOLDataSource.ENDOFLIFE_DATE,
                    lts=data.get("lts"),
                    latest_version=data.get("latest"),
                    release_date=self._parse_date(data.get("releaseDate")),
                    confidence=0.95,  # High confidence from authoritative source
                )

            if response.status_code == 404:
                # Product or version not found
                logger.debug(
                    f"Product/version not found in endoflife.date: "
                    f"{normalized_product}/{version}"
                )
                return None

            # Other error
            logger.warning(
                f"Unexpected API response for {normalized_product}/{version}: "
                f"{response.status_code}"
            )
            return None

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching EOL data for {product} {version}")
            return None
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching EOL data for {product} {version}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error fetching EOL data for {product} {version}: {e}"
            )
            return None

    async def get_eol_status(
        self,
        product: str,
        version: str,
        product_type: str = "os",
    ) -> EOLStatus:
        """
        Get EOL status for a product/version combination.

        Uses three-tier lookup:
        1. Redis cache (if available)
        2. endoflife.date API
        3. Fallback heuristics

        Args:
            product: Product name (e.g., "Windows Server", "Java", "RHEL")
            version: Version string (e.g., "2012", "8", "7")
            product_type: Product type: "os", "runtime", "database", "framework"

        Returns:
            EOLStatus with status, eol_date, support_type, and source
        """
        # 1. Check cache first
        cached = await self._get_cached(product, version)
        if cached:
            logger.debug(f"Cache hit for {product} {version}")
            return cached

        # 2. Try endoflife.date API
        api_result = await self._fetch_from_api(product, version)
        if api_result:
            await self._cache_result(product, version, api_result)
            return api_result

        # 3. Fall back to heuristics
        logger.debug(f"Falling back to heuristics for {product} {version}")
        fallback_result = fallback_eol_check(product, version, product_type)

        # Cache fallback results too (but with lower TTL)
        if fallback_result.status != EOLStatusEnum.UNKNOWN:
            await self._cache_result(product, version, fallback_result)

        return fallback_result

    async def get_batch_eol_status(
        self,
        products: list[tuple[str, str, str]],
    ) -> EOLBatchResult:
        """
        Get EOL status for multiple product/version combinations.

        Args:
            products: List of (product, version, product_type) tuples

        Returns:
            EOLBatchResult with all results and statistics
        """
        results: list[EOLStatus] = []
        from_cache = 0
        from_api = 0
        from_fallback = 0
        errors: list[str] = []

        for product, version, product_type in products:
            try:
                result = await self.get_eol_status(product, version, product_type)
                results.append(result)

                # Track source
                if result.source == EOLDataSource.ENDOFLIFE_DATE:
                    from_api += 1
                elif result.source == EOLDataSource.FALLBACK_HEURISTICS:
                    from_fallback += 1
                else:
                    from_cache += 1

            except Exception as e:
                errors.append(f"{product} {version}: {str(e)}")

        return EOLBatchResult(
            results=results,
            total_queried=len(products),
            from_cache=from_cache,
            from_api=from_api,
            from_fallback=from_fallback,
            errors=errors,
        )


# Singleton instance (lazy initialized)
_eol_service_instance: Optional[EOLLifecycleService] = None


async def get_eol_service(
    redis_client: Optional[Redis] = None,
) -> EOLLifecycleService:
    """
    Get or create the EOL Lifecycle Service singleton.

    Args:
        redis_client: Optional Redis client for caching

    Returns:
        EOLLifecycleService instance
    """
    global _eol_service_instance
    if _eol_service_instance is None:
        _eol_service_instance = EOLLifecycleService(redis_client)
    return _eol_service_instance
