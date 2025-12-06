"""
EOL Catalog Lookup Tool for Issue #1243

Level 1 of DB-first, RAG-augment strategy:
Query VendorProductsCatalog → ProductVersionsCatalog → LifecycleMilestones
to find cached EOL data for a technology/version combination.

Returns EOL data if found in catalog, or indicates cache miss for RAG fallback.
"""

import json
import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


# Technology normalization mappings
TECHNOLOGY_ALIASES = {
    # Operating Systems
    "linux red hat": "rhel",
    "red hat enterprise linux": "rhel",
    "redhat": "rhel",
    "linux oracle": "oracle-linux",
    "oracle linux": "oracle-linux",
    "ol": "oracle-linux",
    "windows server": "windows-server",
    "win server": "windows-server",
    "windows": "windows-server",
    "z/os": "zos",
    "zos": "zos",
    "aix": "aix",
    "ubuntu": "ubuntu",
    "debian": "debian",
    "centos": "centos",
    "suse": "sles",
    "sles": "sles",
    # Databases
    "oracle database": "oracle-database",
    "oracle db": "oracle-database",
    "sql server": "sql-server",
    "mssql": "sql-server",
    "microsoft sql server": "sql-server",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "mongodb": "mongodb",
    "db2": "db2",
    "ibm db2": "db2",
    # Runtimes
    "java": "java",
    "openjdk": "openjdk",
    "jdk": "java",
    ".net": "dotnet",
    "dotnet": "dotnet",
    ".net framework": "dotnet-framework",
    ".net core": "dotnet-core",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "node": "nodejs",
    "python": "python",
    # Frameworks
    "spring boot": "spring-boot",
    "spring framework": "spring",
    "angular": "angular",
    "react": "react",
    "vue": "vue",
    "django": "django",
    "flask": "flask",
}


def normalize_technology_name(technology: str) -> str:
    """
    Normalize technology name to canonical form for catalog lookup.

    Examples:
        "Linux Red Hat" → "rhel"
        "Windows Server" → "windows-server"
        "Oracle Database" → "oracle-database"
    """
    if not technology:
        return ""

    tech_lower = technology.lower().strip()

    # Check direct alias mapping
    if tech_lower in TECHNOLOGY_ALIASES:
        return TECHNOLOGY_ALIASES[tech_lower]

    # Try partial matching
    for alias, normalized in TECHNOLOGY_ALIASES.items():
        if alias in tech_lower or tech_lower in alias:
            return normalized

    # Default: replace spaces with hyphens, lowercase
    return tech_lower.replace(" ", "-")


def extract_major_version(version: str) -> str:
    """
    Extract major version number from version string.

    Examples:
        "9.6" → "9"
        "8.10" → "8"
        "2019" → "2019"
        "19c" → "19"
        "02.05.00" → "2"
    """
    if not version:
        return ""

    version = version.strip()

    # Handle Oracle-style versions (19c, 12c, etc.)
    oracle_match = re.match(r"^(\d+)[cCrR]?$", version)
    if oracle_match:
        return oracle_match.group(1)

    # Handle semver-style (X.Y.Z)
    semver_match = re.match(r"^(\d+)\.?\d*\.?\d*", version)
    if semver_match:
        major = semver_match.group(1)
        # Remove leading zeros
        return str(int(major)) if major else ""

    # Handle Windows-style years
    year_match = re.match(r"^(20\d{2})", version)
    if year_match:
        return year_match.group(1)

    return version


def calculate_eol_status(eol_date: Optional[date]) -> str:
    """
    Calculate EOL status based on date.

    Returns: "active", "eol_soon" (within 12 months), or "eol_expired"
    """
    if not eol_date:
        return "unknown"

    today = date.today()

    if eol_date < today:
        return "eol_expired"

    # Check if within 12 months
    months_until_eol = (eol_date.year - today.year) * 12 + (
        eol_date.month - today.month
    )
    if months_until_eol <= 12:
        return "eol_soon"

    return "active"


class EOLCatalogLookupToolImpl:
    """Implementation for EOL catalog lookup tool"""

    def __init__(self, registry):
        self._registry = registry

    async def execute_async(self, technology: str, version: str) -> str:
        """
        Look up EOL information from catalog.

        Args:
            technology: Technology name (e.g., "RHEL", "Windows Server", "Oracle Database")
            version: Version string (e.g., "9.6", "2019", "19c")

        Returns:
            JSON with EOL data if found, or cache_miss indicator
        """
        try:
            logger.info(f"🔍 EOL Catalog Lookup: {technology} {version}")

            # Normalize inputs
            normalized_tech = normalize_technology_name(technology)
            major_version = extract_major_version(version)
            normalized_key = f"{normalized_tech}:{major_version}"

            logger.debug(f"Normalized: {technology} {version} → {normalized_key}")

            # Query catalog
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from app.models.vendor_products_catalog import (
                VendorProductsCatalog,
                ProductVersionsCatalog,
            )

            # Get database session from registry
            db_session = await self._registry.get_db_session()

            # Query for product in catalog
            stmt = select(VendorProductsCatalog).where(
                VendorProductsCatalog.normalized_key == normalized_tech
            )
            result = await db_session.execute(stmt)
            catalog_product = result.scalar_one_or_none()

            if not catalog_product:
                logger.debug(f"Cache miss: No catalog product for {normalized_tech}")
                return json.dumps(
                    {
                        "cache_hit": False,
                        "technology": technology,
                        "version": version,
                        "normalized_key": normalized_key,
                        "message": f"No catalog entry for {normalized_tech}",
                    }
                )

            # Query for version
            stmt = (
                select(ProductVersionsCatalog)
                .where(
                    ProductVersionsCatalog.catalog_id == catalog_product.id,
                    ProductVersionsCatalog.version_label == major_version,
                )
                .options(selectinload(ProductVersionsCatalog.lifecycle_milestones))
            )
            result = await db_session.execute(stmt)
            catalog_version = result.scalar_one_or_none()

            if not catalog_version:
                # Try partial version match
                stmt = (
                    select(ProductVersionsCatalog)
                    .where(
                        ProductVersionsCatalog.catalog_id == catalog_product.id,
                    )
                    .options(selectinload(ProductVersionsCatalog.lifecycle_milestones))
                )
                result = await db_session.execute(stmt)
                all_versions = result.scalars().all()

                # Find closest version match
                for v in all_versions:
                    if v.version_label.startswith(
                        major_version
                    ) or major_version.startswith(v.version_label):
                        catalog_version = v
                        break

            if not catalog_version:
                logger.debug(
                    f"Cache miss: No version {major_version} for {normalized_tech}"
                )
                return json.dumps(
                    {
                        "cache_hit": False,
                        "technology": technology,
                        "version": version,
                        "normalized_key": normalized_key,
                        "vendor_name": catalog_product.vendor_name,
                        "product_name": catalog_product.product_name,
                        "message": f"No version {major_version} in catalog for {catalog_product.product_name}",
                    }
                )

            # Get lifecycle milestones
            milestones = catalog_version.lifecycle_milestones
            eol_date = None
            extended_support_date = None
            release_date = None
            source = None

            for milestone in milestones:
                if milestone.milestone_type == "end_of_life":
                    eol_date = milestone.milestone_date
                    source = milestone.source
                elif milestone.milestone_type == "extended_support_end":
                    extended_support_date = milestone.milestone_date
                elif milestone.milestone_type == "release":
                    release_date = milestone.milestone_date

            # Use extended support as fallback for EOL
            effective_eol = eol_date or extended_support_date

            eol_status = calculate_eol_status(effective_eol)

            logger.info(
                f"✅ Cache hit: {normalized_key} → EOL: {effective_eol}, Status: {eol_status}"
            )

            return json.dumps(
                {
                    "cache_hit": True,
                    "technology": technology,
                    "version": version,
                    "normalized_key": normalized_key,
                    "vendor_name": catalog_product.vendor_name,
                    "product_name": catalog_product.product_name,
                    "version_label": catalog_version.version_label,
                    "eol_date": effective_eol.isoformat() if effective_eol else None,
                    "extended_support_date": (
                        extended_support_date.isoformat()
                        if extended_support_date
                        else None
                    ),
                    "release_date": release_date.isoformat() if release_date else None,
                    "eol_status": eol_status,
                    "source": source,
                    "catalog_version_id": str(catalog_version.id),
                }
            )

        except Exception as e:
            logger.error(f"❌ EOL Catalog Lookup failed: {e}", exc_info=True)
            return json.dumps(
                {
                    "cache_hit": False,
                    "technology": technology,
                    "version": version,
                    "error": str(e),
                    "message": "Catalog lookup failed - try RAG fallback",
                }
            )

    def execute_sync(self, technology: str, version: str) -> str:
        """Synchronous wrapper for execute_async.

        Uses a robust pattern for running async code from sync context.
        """
        import asyncio

        # OBSERVABILITY: tracking not needed - Agent tool internal execution
        coro = self.execute_async(technology, version)

        try:
            # Check if we're already in an event loop
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(coro)

        # We're inside a running loop - need to run in a new thread
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result(timeout=60)  # 60 second timeout for safety


def create_eol_catalog_lookup_tools(
    context_info: Dict[str, Any], registry: Optional[Any] = None
) -> List:
    """
    Create EOL catalog lookup tools for compliance validation agent.

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id
        registry: Optional ServiceRegistry for dependency injection

    Returns:
        List of EOL catalog lookup tools
    """
    logger.info("🔧 Creating EOL catalog lookup tools for compliance validation")

    if registry is None:
        registry = context_info.get("service_registry") if context_info else None
        if registry is None:
            logger.warning(
                "⚠️ No ServiceRegistry available - returning empty tools list"
            )
            return []

    tools = []

    if CREWAI_TOOLS_AVAILABLE:
        tools.append(EOLCatalogLookupTool(registry))
    else:
        tools.append(EOLCatalogLookupToolImpl(registry))

    logger.info(f"✅ Created {len(tools)} EOL catalog lookup tools")
    return tools


if CREWAI_TOOLS_AVAILABLE:

    class EOLCatalogLookupTool(BaseTool):
        """CrewAI Tool wrapper for EOL catalog lookup"""

        name: str = "eol_catalog_lookup"
        description: str = (
            "Look up End-of-Life (EOL) information for a technology/version from the catalog.\n\n"
            "This is the first step in compliance validation - checks the cached catalog before RAG.\n\n"
            "Input:\n"
            "- technology: Technology name (e.g., 'RHEL', 'Windows Server', 'Oracle Database')\n"
            "- version: Version string (e.g., '9.6', '2019', '19c')\n\n"
            "Output: JSON with:\n"
            "- cache_hit: true if found in catalog, false if RAG lookup needed\n"
            "- eol_date: End-of-life date (if found)\n"
            "- eol_status: 'active', 'eol_soon', or 'eol_expired'\n"
            "- vendor_name, product_name, source metadata"
        )

        def __init__(self, registry):
            super().__init__()
            self._impl = EOLCatalogLookupToolImpl(registry)

        async def _arun(self, technology: str, version: str) -> str:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return await self._impl.execute_async(technology, version)

        def _run(self, technology: str, version: str) -> str:
            return self._impl.execute_sync(technology, version)

else:

    class EOLCatalogLookupTool:
        """Dummy tool when CrewAI not available"""

        def __init__(self, registry):
            self._impl = EOLCatalogLookupToolImpl(registry)

        async def _arun(self, technology: str, version: str) -> str:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return await self._impl.execute_async(technology, version)

        def _run(self, technology: str, version: str) -> str:
            return self._impl.execute_sync(technology, version)
