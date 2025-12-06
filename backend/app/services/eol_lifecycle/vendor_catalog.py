"""
Vendor Product Lifecycle Catalog

ADR-039: Provides EOL lifecycle data for vendor-specific products
not covered by endoflife.date API.

This catalog can be overridden per-engagement via engagement_standards.
"""

import logging
from datetime import date
from typing import Optional

from .models import (
    EOLDataSource,
    EOLStatus,
    EOLStatusEnum,
    SupportTypeEnum,
)

logger = logging.getLogger(__name__)


# Vendor product lifecycle catalog
# Products not covered by endoflife.date API
VENDOR_LIFECYCLE_CATALOG: dict[str, dict[str, dict]] = {
    # Oracle Database
    "oracle_database": {
        "11g": {
            "eol_date": date(2020, 12, 31),
            "extended_support_end": date(2024, 12, 31),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.EXTENDED,
        },
        "12c": {
            "eol_date": date(2022, 3, 31),
            "extended_support_end": date(2025, 3, 31),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.EXTENDED,
        },
        "18c": {
            "eol_date": date(2021, 6, 30),
            "extended_support_end": date(2024, 6, 30),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "19c": {
            "eol_date": date(2027, 4, 30),
            "extended_support_end": date(2030, 4, 30),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
        "21c": {
            "eol_date": date(2024, 4, 30),
            "extended_support_end": date(2027, 4, 30),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.EXTENDED,
        },
        "23c": {
            "eol_date": date(2028, 4, 30),
            "extended_support_end": date(2031, 4, 30),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # SAP NetWeaver
    "sap_netweaver": {
        "7.0": {
            "eol_date": date(2020, 12, 31),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "7.3": {
            "eol_date": date(2021, 12, 31),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "7.4": {
            "eol_date": date(2024, 12, 31),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "7.5": {
            "eol_date": date(2030, 12, 31),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # SAP HANA
    "sap_hana": {
        "1.0": {
            "eol_date": date(2020, 6, 30),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "2.0": {
            "eol_date": date(2040, 12, 31),  # SPS 07
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # IBM DB2
    "ibm_db2": {
        "10.5": {
            "eol_date": date(2022, 4, 30),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "11.1": {
            "eol_date": date(2024, 9, 30),
            "extended_support_end": date(2027, 9, 30),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.EXTENDED,
        },
        "11.5": {
            "eol_date": date(2029, 4, 30),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # IBM WebSphere
    "ibm_websphere": {
        "8.0": {
            "eol_date": date(2018, 6, 30),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "8.5": {
            "eol_date": date(2025, 6, 30),
            "extended_support_end": date(2028, 6, 30),
            "status": EOLStatusEnum.EOL_SOON,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
        "9.0": {
            "eol_date": date(2030, 9, 30),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # Microsoft SQL Server
    "sql_server": {
        "2012": {
            "eol_date": date(2022, 7, 12),
            "extended_support_end": date(2022, 7, 12),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "2014": {
            "eol_date": date(2024, 7, 9),
            "extended_support_end": date(2024, 7, 9),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "2016": {
            "eol_date": date(2026, 7, 14),
            "extended_support_end": date(2026, 7, 14),
            "status": EOLStatusEnum.EOL_SOON,
            "support_type": SupportTypeEnum.EXTENDED,
        },
        "2017": {
            "eol_date": date(2027, 10, 12),
            "status": EOLStatusEnum.EOL_SOON,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
        "2019": {
            "eol_date": date(2030, 1, 8),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
        "2022": {
            "eol_date": date(2033, 1, 11),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # VMware vSphere
    "vmware_vsphere": {
        "6.5": {
            "eol_date": date(2022, 10, 15),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "6.7": {
            "eol_date": date(2023, 10, 15),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "7.0": {
            "eol_date": date(2027, 4, 2),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
        "8.0": {
            "eol_date": date(2029, 10, 11),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
    # Citrix Virtual Apps and Desktops
    "citrix_vad": {
        "7.15": {
            "eol_date": date(2023, 8, 31),
            "status": EOLStatusEnum.EOL_EXPIRED,
            "support_type": SupportTypeEnum.NONE,
        },
        "1912": {
            "eol_date": date(2025, 12, 31),
            "status": EOLStatusEnum.EOL_SOON,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
        "2203": {
            "eol_date": date(2027, 12, 31),
            "status": EOLStatusEnum.ACTIVE,
            "support_type": SupportTypeEnum.MAINSTREAM,
        },
    },
}

# Product name normalization mappings
VENDOR_PRODUCT_ALIASES: dict[str, str] = {
    "oracle": "oracle_database",
    "oracle db": "oracle_database",
    "oracle database": "oracle_database",
    "sap": "sap_netweaver",
    "sap nw": "sap_netweaver",
    "netweaver": "sap_netweaver",
    "hana": "sap_hana",
    "sap hana": "sap_hana",
    "db2": "ibm_db2",
    "ibm db2": "ibm_db2",
    "websphere": "ibm_websphere",
    "ibm websphere": "ibm_websphere",
    "was": "ibm_websphere",
    "mssql": "sql_server",
    "sql server": "sql_server",
    "microsoft sql server": "sql_server",
    "vsphere": "vmware_vsphere",
    "vmware": "vmware_vsphere",
    "esxi": "vmware_vsphere",
    "citrix": "citrix_vad",
    "xenapp": "citrix_vad",
    "xendesktop": "citrix_vad",
    "virtual apps": "citrix_vad",
}


def normalize_vendor_product(product: str) -> str:
    """Normalize vendor product name for catalog lookup."""
    product_lower = product.lower().strip()
    return VENDOR_PRODUCT_ALIASES.get(product_lower, product_lower)


def normalize_version(version: str, product_key: str) -> str:
    """Normalize version string for catalog lookup."""
    version = version.strip()

    # Handle Oracle version formats (e.g., "11.2" -> "11g", "12.1" -> "12c")
    if product_key == "oracle_database":
        if version.startswith("11"):
            return "11g"
        elif version.startswith("12"):
            return "12c"
        elif version.startswith("18"):
            return "18c"
        elif version.startswith("19"):
            return "19c"
        elif version.startswith("21"):
            return "21c"
        elif version.startswith("23"):
            return "23c"

    # Handle SQL Server year formats
    if product_key == "sql_server":
        # Remove "SP" suffixes (e.g., "2016 SP2" -> "2016")
        version = version.split()[0] if " " in version else version

    return version


def get_vendor_eol_status(
    product: str,
    version: str,
    engagement_overrides: Optional[dict] = None,
) -> Optional[EOLStatus]:
    """
    Get EOL status from vendor catalog.

    Args:
        product: Vendor product name (e.g., "Oracle", "SAP", "SQL Server")
        version: Version string (e.g., "19c", "7.5", "2019")
        engagement_overrides: Optional per-engagement overrides

    Returns:
        EOLStatus if found in catalog, None otherwise
    """
    # Normalize product name
    product_key = normalize_vendor_product(product)

    # Check engagement overrides first
    if engagement_overrides:
        override_key = f"{product_key}_{version}"
        if override_key in engagement_overrides:
            override = engagement_overrides[override_key]
            return EOLStatus(
                product=product,
                version=version,
                product_type="database",  # Most vendor products are databases
                status=EOLStatusEnum(override.get("status", "unknown")),
                eol_date=override.get("eol_date"),
                extended_support_end=override.get("extended_support_end"),
                support_type=SupportTypeEnum(override.get("support_type", "none")),
                source=EOLDataSource.VENDOR_CATALOG,
                confidence=0.9,  # High confidence for explicit overrides
            )

    # Look up in catalog
    if product_key not in VENDOR_LIFECYCLE_CATALOG:
        logger.debug(f"Product {product} ({product_key}) not in vendor catalog")
        return None

    product_versions = VENDOR_LIFECYCLE_CATALOG[product_key]

    # Normalize version
    normalized_version = normalize_version(version, product_key)

    if normalized_version not in product_versions:
        logger.debug(
            f"Version {version} ({normalized_version}) not found for {product_key}"
        )
        return None

    version_data = product_versions[normalized_version]

    return EOLStatus(
        product=product,
        version=version,
        product_type="database",  # Default - most vendor products are databases
        status=version_data.get("status", EOLStatusEnum.UNKNOWN),
        eol_date=version_data.get("eol_date"),
        extended_support_end=version_data.get("extended_support_end"),
        support_type=version_data.get("support_type", SupportTypeEnum.NONE),
        source=EOLDataSource.VENDOR_CATALOG,
        confidence=0.85,  # Good confidence for catalog data
    )
