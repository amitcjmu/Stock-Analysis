"""
RAG EOL Enrichment Tool Implementation

Implementation for RAG-based EOL lookup using embedded knowledge base.
When catalog lookup returns cache_miss, looks up EOL data and caches results.
"""

import json
import logging
import uuid
from typing import Optional

from .knowledge_base import EOL_KNOWLEDGE_BASE
from .utils import calculate_eol_status

logger = logging.getLogger(__name__)


class RAGEOLEnrichmentToolImpl:
    """Implementation for RAG EOL enrichment tool"""

    def __init__(self, registry):
        self._registry = registry

    async def execute_async(
        self,
        normalized_key: str,
        technology: str,
        version: str,
        cache_result: bool = True,
    ) -> str:
        """
        Look up EOL information from RAG knowledge base.

        Args:
            normalized_key: Normalized key from catalog lookup (e.g., "rhel:9")
            technology: Original technology name
            version: Original version string
            cache_result: Whether to cache the result back to catalog

        Returns:
            JSON with EOL data from RAG
        """
        try:
            logger.info(f"🔍 RAG EOL Lookup: {normalized_key}")

            # Parse normalized key
            parts = normalized_key.split(":")
            if len(parts) >= 2:
                tech_key = parts[0]
                version_key = parts[1]
            else:
                tech_key = normalized_key
                version_key = version

            # Look up in knowledge base
            tech_data = EOL_KNOWLEDGE_BASE.get(tech_key)

            if not tech_data:
                logger.debug(f"RAG miss: No knowledge base entry for {tech_key}")
                return json.dumps(
                    {
                        "rag_hit": False,
                        "normalized_key": normalized_key,
                        "technology": technology,
                        "version": version,
                        "message": f"No RAG data for technology: {tech_key}",
                    }
                )

            # Look up version
            version_data = tech_data.get("versions", {}).get(version_key)

            if not version_data:
                # Try fuzzy version matching
                available_versions = list(tech_data.get("versions", {}).keys())
                for av in available_versions:
                    if av.startswith(version_key) or version_key.startswith(av):
                        version_data = tech_data["versions"][av]
                        version_key = av
                        break

            if not version_data:
                logger.debug(f"RAG miss: No version {version_key} for {tech_key}")
                return json.dumps(
                    {
                        "rag_hit": False,
                        "normalized_key": normalized_key,
                        "technology": technology,
                        "version": version,
                        "vendor_name": tech_data.get("vendor"),
                        "product_name": tech_data.get("product"),
                        "available_versions": list(
                            tech_data.get("versions", {}).keys()
                        ),
                        "message": f"No RAG data for version: {version_key}",
                    }
                )

            # Extract EOL data
            eol_date = version_data.get("eol")
            extended_support = version_data.get("extended_support")
            release_date = version_data.get("release")
            eol_status = calculate_eol_status(eol_date)

            logger.info(
                f"✅ RAG hit: {normalized_key} → EOL: {eol_date}, Status: {eol_status}"
            )

            result = {
                "rag_hit": True,
                "normalized_key": normalized_key,
                "technology": technology,
                "version": version,
                "vendor_name": tech_data.get("vendor"),
                "product_name": tech_data.get("product"),
                "version_label": version_key,
                "eol_date": eol_date,
                "extended_support_date": extended_support,
                "release_date": release_date,
                "eol_status": eol_status,
                "source": tech_data.get("source"),
            }

            # Cache result to catalog if requested
            if cache_result:
                try:
                    cached = await self._cache_to_catalog(
                        tech_key=tech_key,
                        version_key=version_key,
                        vendor_name=tech_data.get("vendor"),
                        product_name=tech_data.get("product"),
                        eol_date=eol_date,
                        extended_support=extended_support,
                        release_date=release_date,
                        source=tech_data.get("source"),
                    )
                    result["cached_to_catalog"] = cached
                except Exception as cache_error:
                    logger.warning(f"Failed to cache EOL result: {cache_error}")
                    result["cached_to_catalog"] = False

            return json.dumps(result)

        except Exception as e:
            logger.error(f"❌ RAG EOL Lookup failed: {e}", exc_info=True)
            return json.dumps(
                {
                    "rag_hit": False,
                    "normalized_key": normalized_key,
                    "error": str(e),
                    "message": "RAG lookup failed",
                }
            )

    async def _cache_to_catalog(
        self,
        tech_key: str,
        version_key: str,
        vendor_name: str,
        product_name: str,
        eol_date: Optional[str],
        extended_support: Optional[str],
        release_date: Optional[str],
        source: str,
    ) -> bool:
        """Cache RAG result to catalog for future lookups."""
        try:
            from datetime import datetime

            from sqlalchemy import select

            from app.models.vendor_products_catalog import (
                VendorProductsCatalog,
                ProductVersionsCatalog,
                LifecycleMilestones,
            )

            db_session = await self._registry.get_db_session()

            # Find or create catalog product
            stmt = select(VendorProductsCatalog).where(
                VendorProductsCatalog.normalized_key == tech_key
            )
            result = await db_session.execute(stmt)
            catalog_product = result.scalar_one_or_none()

            if not catalog_product:
                # Create new catalog product
                catalog_product = VendorProductsCatalog(
                    id=uuid.uuid4(),
                    vendor_name=vendor_name or "Unknown",
                    product_name=product_name or tech_key,
                    normalized_key=tech_key,
                    is_global=True,
                )
                db_session.add(catalog_product)
                await db_session.flush()

            # Find or create version
            stmt = select(ProductVersionsCatalog).where(
                ProductVersionsCatalog.catalog_id == catalog_product.id,
                ProductVersionsCatalog.version_label == version_key,
            )
            result = await db_session.execute(stmt)
            catalog_version = result.scalar_one_or_none()

            if not catalog_version:
                catalog_version = ProductVersionsCatalog(
                    id=uuid.uuid4(),
                    catalog_id=catalog_product.id,
                    version_label=version_key,
                    version_semver=version_key,
                )
                db_session.add(catalog_version)
                await db_session.flush()

            # Add lifecycle milestones
            def parse_date(date_str: Optional[str]):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return None

            # Check existing milestones
            existing_stmt = select(LifecycleMilestones).where(
                LifecycleMilestones.catalog_version_id == catalog_version.id
            )
            existing_result = await db_session.execute(existing_stmt)
            existing_milestones = {
                m.milestone_type: m for m in existing_result.scalars().all()
            }

            # Add EOL milestone
            if eol_date and "end_of_life" not in existing_milestones:
                eol_milestone = LifecycleMilestones(
                    id=uuid.uuid4(),
                    catalog_version_id=catalog_version.id,
                    milestone_type="end_of_life",
                    milestone_date=parse_date(eol_date),
                    source=source,
                    provenance={
                        "agent": "rag_eol_enrichment",
                        "cached_at": datetime.utcnow().isoformat(),
                    },
                )
                db_session.add(eol_milestone)

            # Add extended support milestone
            if extended_support and "extended_support_end" not in existing_milestones:
                ext_milestone = LifecycleMilestones(
                    id=uuid.uuid4(),
                    catalog_version_id=catalog_version.id,
                    milestone_type="extended_support_end",
                    milestone_date=parse_date(extended_support),
                    source=source,
                    provenance={
                        "agent": "rag_eol_enrichment",
                        "cached_at": datetime.utcnow().isoformat(),
                    },
                )
                db_session.add(ext_milestone)

            # Add release milestone
            if release_date and "release" not in existing_milestones:
                release_milestone = LifecycleMilestones(
                    id=uuid.uuid4(),
                    catalog_version_id=catalog_version.id,
                    milestone_type="release",
                    milestone_date=parse_date(release_date),
                    source=source,
                    provenance={
                        "agent": "rag_eol_enrichment",
                        "cached_at": datetime.utcnow().isoformat(),
                    },
                )
                db_session.add(release_milestone)

            await db_session.commit()
            logger.info(f"✅ Cached EOL data for {tech_key}:{version_key} to catalog")
            return True

        except Exception as e:
            logger.error(f"Failed to cache EOL data to catalog: {e}", exc_info=True)
            return False

    def execute_sync(
        self,
        normalized_key: str,
        technology: str,
        version: str,
        cache_result: bool = True,
    ) -> str:
        """Synchronous wrapper for execute_async"""
        import asyncio
        import nest_asyncio

        nest_asyncio.apply()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        # OBSERVABILITY: tracking not needed - Agent tool internal
                        self.execute_async(
                            normalized_key, technology, version, cache_result
                        ),
                    )
                    return future.result()
            else:
                # OBSERVABILITY: tracking not needed - Agent tool internal execution
                return asyncio.run(
                    self.execute_async(
                        normalized_key, technology, version, cache_result
                    )
                )
        except RuntimeError:
            # OBSERVABILITY: tracking not needed - Agent tool internal execution
            return asyncio.run(
                self.execute_async(normalized_key, technology, version, cache_result)
            )
