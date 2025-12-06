"""
Compliance Validation Tools for Issue #1243

Three-level compliance validation using existing catalog infrastructure:
- Level 1: OS Compliance (Asset.operating_system/os_version vs engagement standards)
- Level 2: Application Compliance (COTS apps vs vendor EOL dates)
- Level 3: Component Compliance (databases, runtimes, frameworks)

DB-first, RAG-augment strategy:
1. Query VendorProductsCatalog → ProductVersionsCatalog → LifecycleMilestones
2. On cache miss, use RAG to look up EOL data from endoflife.date
3. Cache results back to catalog for future lookups
"""

from app.services.persistent_agents.tools.eol_catalog_lookup_tool import (
    create_eol_catalog_lookup_tools,
)
from app.services.persistent_agents.tools.rag_eol_enrichment_tool import (
    create_rag_eol_enrichment_tools,
)
from app.services.persistent_agents.tools.asset_product_linker_tool import (
    create_asset_product_linker_tools,
)

__all__ = [
    "create_eol_catalog_lookup_tools",
    "create_rag_eol_enrichment_tools",
    "create_asset_product_linker_tools",
]
