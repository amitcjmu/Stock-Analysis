"""
Intelligent Gap Scanner - Main scanner class with 6-source data awareness.

Core gap scanning logic that orchestrates data loading and extraction from 6 sources.
Refactored to keep under 400 lines per pre-commit requirements.

CC Generated for Issue #1111 - IntelligentGapScanner (Modular

ized)
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

import logging
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset
from app.services.collection.gap_analysis.models import (
    DataSource,
    IntelligentGap,
    COLLECTION_FLOW_FIELD_METADATA,
)
from app.services.collection.gap_analysis.asset_type_requirements import (
    AssetTypeRequirements,
)
from app.services.collection.critical_attributes import CriticalAttributesDefinition
from .data_loaders import DataLoaders
from .data_extractors import DataExtractors

logger = logging.getLogger(__name__)


class IntelligentGapScanner:
    """
    Intelligent Gap Scanner with 6-Source Data Awareness.

    Checks ALL possible data sources before flagging a gap:
    1. Standard columns (assets.{field})
    2. Custom attributes (custom_attributes JSONB)
    3. Enrichment tables (tech_debt, performance, cost)
    4. Environment field (assets.environment)
    5. Canonical applications (via junction table)
    6. Related assets (via asset_dependencies)

    Returns TRUE gaps only (data not found in ANY source).

    Usage:
        scanner = IntelligentGapScanner(db, client_account_id, engagement_id)
        gaps = await scanner.scan_gaps(asset)
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: int,
        engagement_id: int,
        sections_to_scan: Optional[List[str]] = None,
    ):
        """
        Initialize scanner with database session and tenant context.

        Args:
            db: Async database session
            client_account_id: Multi-tenant client ID
            engagement_id: Multi-tenant engagement ID
            sections_to_scan: Optional list of sections to scan (None = all sections)
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.sections_to_scan = sections_to_scan

        # Initialize data loaders and extractors
        self.data_loaders = DataLoaders(db, client_account_id, engagement_id)
        self.data_extractors = DataExtractors()

        # Build field_id → attribute mapping for proper applicability checks
        # Issue #1193 Fix: COLLECTION_FLOW_FIELD_METADATA uses field_ids (e.g., "operating_system")
        # but AssetTypeRequirements uses attribute names (e.g., "operating_system_version")
        # This mapping bridges the gap
        self._field_to_attr_map = self._build_field_to_attr_map()

    async def scan_gaps(self, asset: Asset) -> List[IntelligentGap]:
        """
        Scan asset for TRUE gaps across all 6 data sources.

        Args:
            asset: Asset to scan

        Returns:
            List of IntelligentGap objects (only TRUE gaps where data not found)
        """
        gaps = []

        # Load data from sources 3-6 (async database queries)
        enrichment_data = await self.data_loaders.load_enrichment_data(asset.id)
        canonical_apps = await self.data_loaders.load_canonical_applications(asset.id)
        related_assets = await self.data_loaders.load_related_assets(asset.id)

        # Issue #1193 Fix: Get applicable attributes for this asset type
        # Applications should NOT get gaps for server-level infrastructure attributes
        # (operating_system_version, cpu_memory_storage_specs, network_configuration)
        asset_type = getattr(asset, "asset_type", "application")
        applicable_attrs_list = AssetTypeRequirements.get_applicable_attributes(
            asset_type
        )
        # GPT5.1 Codex Safety: If get_applicable_attributes returns empty (unknown/typo),
        # fallback to ALL attributes to avoid skipping mapped fields for unknown types
        applicable_attrs = (
            set(applicable_attrs_list)
            if applicable_attrs_list
            else set(AssetTypeRequirements.ALL_CRITICAL_ATTRIBUTES)
        )
        inapplicable_count = 0

        # Scan fields by section
        for section_id, section_meta in COLLECTION_FLOW_FIELD_METADATA.items():
            # Skip section if not in sections_to_scan
            if self.sections_to_scan and section_id not in self.sections_to_scan:
                continue

            section_fields = section_meta["fields"]

            for field_id, field_meta in section_fields.items():
                # Issue #1193 Fix: Skip fields not applicable to this asset type
                # E.g., applications should NOT get gaps for operating_system, cpu_cores, etc.
                # because apps can depend on multiple servers with different OSes
                #
                # GPT5.1 Codex Fix: field_id (e.g., "operating_system") != attribute name
                # (e.g., "operating_system_version"). Use _is_field_applicable() to map
                # field_ids to their corresponding attributes and check if ANY are applicable.
                if not self._is_field_applicable(field_id, applicable_attrs):
                    inapplicable_count += 1
                    continue

                # Check all 6 sources
                data_sources_checked: List[DataSource] = []

                # Source 1: Standard column
                # ✅ FIX Bug #4: Use correct DataSource parameter names
                # (source_type, field_path, value, confidence) NOT (source, location, value)
                std_value = self._check_standard_column(asset, field_id)
                if std_value is not None:
                    data_sources_checked.append(
                        DataSource(
                            source_type="standard_column",
                            field_path=f"assets.{field_id}",
                            value=std_value,
                            confidence=1.0,  # Highest confidence (authoritative)
                        )
                    )

                # Source 2: custom_attributes JSONB
                # ✅ FIX Bug #9 (Asset enrichment_data AttributeError):
                # Asset model has technical_details JSONB (NOT enrichment_data)
                # technical_details contains technical enrichments and details
                jsonb_value = self.data_extractors.extract_from_jsonb(
                    asset.custom_attributes, asset.technical_details, field_id
                )
                if jsonb_value is not None:
                    data_sources_checked.append(
                        DataSource(
                            source_type="custom_attributes",
                            field_path=f"custom_attributes.{field_id}",
                            value=jsonb_value,
                            confidence=0.95,  # Structured data
                        )
                    )

                # Source 3: Enrichment tables
                enrichment_value = self.data_extractors.extract_from_enrichment(
                    enrichment_data, field_id
                )
                if enrichment_value is not None:
                    data_sources_checked.append(
                        DataSource(
                            source_type="enrichment_tables",
                            field_path=f"enrichment.{field_id}",
                            value=enrichment_value,
                            confidence=0.90,  # Assessed data
                        )
                    )

                # Source 4: Environment field
                if field_id == "environment" and asset.environment:
                    data_sources_checked.append(
                        DataSource(
                            source_type="environment_field",
                            field_path="assets.environment",
                            value=asset.environment,
                            confidence=0.85,  # Metadata
                        )
                    )

                # Source 5: Canonical applications
                canonical_value = self.data_extractors.extract_from_canonical_apps(
                    canonical_apps, field_id
                )
                if canonical_value is not None:
                    data_sources_checked.append(
                        DataSource(
                            source_type="canonical_applications",
                            field_path=f"canonical_apps.{field_id}",
                            value=canonical_value,
                            confidence=0.80,  # Derived data
                        )
                    )

                # Source 6: Related assets
                related_value = self.data_extractors.extract_from_related_assets(
                    related_assets, field_id
                )
                if related_value is not None:
                    data_sources_checked.append(
                        DataSource(
                            source_type="related_assets",
                            field_path=f"related_assets.{field_id}",
                            value=related_value,
                            confidence=0.70,  # Propagated data
                        )
                    )

                # If NO sources found data → TRUE gap
                is_true_gap = len(data_sources_checked) == 0

                if is_true_gap:
                    # Calculate confidence (1.0 for true gaps)
                    confidence = self._calculate_confidence(data_sources_checked)

                    # ✅ FIX Bug #10 (IntelligentGap parameter name):
                    # Model expects 'field_name' not 'field_display_name'
                    # ✅ FIX Bug #12 (IntelligentGap section_name parameter):
                    # Model expects 'section' only (NOT 'section_name')
                    # ✅ FIX Bug #13 (IntelligentGap confidence parameter):
                    # Model expects 'confidence_score' not 'confidence'
                    # ✅ FIX Bug #14 (IntelligentGap data_sources parameter):
                    # Model expects 'data_found' not 'data_sources_checked'
                    gaps.append(
                        IntelligentGap(
                            field_id=field_id,
                            field_name=self._get_field_display_name(field_id),
                            section=section_id,
                            is_true_gap=True,
                            confidence_score=confidence,
                            data_found=data_sources_checked,
                            priority=field_meta.get("importance", "medium"),
                        )
                    )

        logger.info(
            f"Scanned asset {asset.id} ({asset_type}): Found {len(gaps)} TRUE gaps "
            f"(checked 6 sources, skipped {inapplicable_count} inapplicable fields)"
        )

        return gaps

    def _check_standard_column(self, asset: Asset, field_id: str) -> Optional[Any]:
        """Check if field exists in standard Asset columns."""
        if hasattr(asset, field_id):
            value = getattr(asset, field_id, None)
            # Consider empty strings/lists as missing data
            if value is not None and value != "" and value != []:
                return value
        return None

    def _calculate_confidence(self, data_sources: List[DataSource]) -> float:
        """
        Calculate confidence score based on number of sources checked.

        Returns:
            1.0 if no sources found (true gap)
            0.9 if 1 source found
            0.5 if 2-3 sources found
            0.0 if 4+ sources found (data exists)
        """
        source_count = len(data_sources)

        if source_count == 0:
            return 1.0  # True gap - highest confidence
        elif source_count == 1:
            return 0.9  # Data found in only 1 source (possibly outdated)
        elif source_count <= 3:
            return 0.5  # Data found in multiple sources (likely accurate)
        else:
            return 0.0  # Data found in 4+ sources (definitely not a gap)

    def _get_field_display_name(self, field_id: str) -> str:
        """Get human-readable field name from metadata."""
        for section_meta in COLLECTION_FLOW_FIELD_METADATA.values():
            if field_id in section_meta["fields"]:
                return section_meta["fields"][field_id].get("label", field_id)
        return field_id.replace("_", " ").title()

    # Wrapper methods for testing data extraction logic
    def _extract_from_canonical_apps(
        self, canonical_apps: List[Any], field_id: str
    ) -> Optional[DataSource]:
        """
        Wrapper for testing canonical apps extraction.

        Returns DataSource if value found, None otherwise.
        """
        value = self.data_extractors.extract_from_canonical_apps(
            canonical_apps, field_id
        )
        if value is not None:
            return DataSource(
                source_type="canonical_applications",
                field_path=f"canonical_apps.{field_id}",
                value=value,
                confidence=0.80,
            )
        return None

    def _extract_from_related_assets(
        self, related_assets: List[Asset], field_id: str
    ) -> Optional[DataSource]:
        """
        Wrapper for testing related assets extraction.

        Returns DataSource if value found, None otherwise.
        """
        value = self.data_extractors.extract_from_related_assets(
            related_assets, field_id
        )
        if value is not None:
            return DataSource(
                source_type="related_assets",
                field_path=f"related_assets.{field_id}",
                value=value,
                confidence=0.70,
            )
        return None

    def _build_field_to_attr_map(self) -> Dict[str, List[str]]:
        """
        Build mapping from field_id to list of attribute names.

        Issue #1193 Fix (GPT5.1 Codex): COLLECTION_FLOW_FIELD_METADATA uses field_ids
        like "operating_system", "cpu_cores", etc. but AssetTypeRequirements uses
        attribute names like "operating_system_version", "cpu_memory_storage_specs".

        This method creates a reverse mapping from field_id -> [attribute names]
        so we can check if a field_id maps to any applicable attribute.

        Example mapping:
            "operating_system" -> ["operating_system_version"]
            "os_version" -> ["operating_system_version"]
            "cpu_cores" -> ["cpu_memory_storage_specs"]
            "memory_gb" -> ["cpu_memory_storage_specs"]
            "technology_stack" -> ["technology_stack"]  # Direct match

        Returns:
            Dict mapping field_id to list of attribute names it belongs to
        """
        field_to_attr: Dict[str, List[str]] = {}

        # Get attribute mappings from CriticalAttributesDefinition
        attr_mapping = CriticalAttributesDefinition.get_attribute_mapping()

        for attr_name, attr_config in attr_mapping.items():
            asset_fields = attr_config.get("asset_fields", [])

            for field in asset_fields:
                # Handle custom_attributes.* paths - extract just the field name
                if field.startswith("custom_attributes."):
                    field_key = field.replace("custom_attributes.", "")
                elif "." in field:
                    # Skip complex paths like "resilience.rto_minutes"
                    # (these are enrichment table paths, not field_ids)
                    continue
                else:
                    field_key = field

                # Add to mapping
                if field_key not in field_to_attr:
                    field_to_attr[field_key] = []
                if attr_name not in field_to_attr[field_key]:
                    field_to_attr[field_key].append(attr_name)

        logger.debug(
            f"Built field_id → attribute mapping with {len(field_to_attr)} field_ids"
        )
        return field_to_attr

    def _is_field_applicable(self, field_id: str, applicable_attrs: Set[str]) -> bool:
        """
        Check if a field_id is applicable for the given asset type.

        Issue #1193 Fix (GPT5.1 Codex): Instead of checking if field_id is directly
        in applicable_attrs (which would fail since they use different naming),
        we look up which attribute(s) the field_id maps to and check if ANY of
        those attributes are applicable.

        Args:
            field_id: Field from COLLECTION_FLOW_FIELD_METADATA (e.g., "operating_system")
            applicable_attrs: Set of applicable attribute names for this asset type
                             (e.g., {"operating_system_version", "technology_stack", ...})

        Returns:
            True if field should be scanned for this asset type, False to skip

        Example:
            field_id="operating_system", applicable_attrs={"technology_stack", ...}
            -> "operating_system" maps to "operating_system_version"
            -> "operating_system_version" NOT in applicable_attrs
            -> Return False (skip this field for applications)

            field_id="technology_stack", applicable_attrs={"technology_stack", ...}
            -> "technology_stack" maps to "technology_stack"
            -> "technology_stack" IS in applicable_attrs
            -> Return True (scan this field)
        """
        # Look up which attributes this field_id maps to
        mapped_attrs = self._field_to_attr_map.get(field_id, [])

        if not mapped_attrs:
            # Field not found in mapping - default to applicable
            # This ensures we don't accidentally skip fields not in the mapping
            logger.debug(
                f"Field '{field_id}' not in attribute mapping, defaulting to applicable"
            )
            return True

        # Check if ANY mapped attribute is applicable
        for attr in mapped_attrs:
            if attr in applicable_attrs:
                return True

        # None of the mapped attributes are applicable - skip this field
        return False
