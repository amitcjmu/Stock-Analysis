"""
EOL Fallback Heuristics

ADR-039: Provides fallback EOL detection when endoflife.date API is unavailable.
Contains hardcoded patterns migrated from eol_detection.py.
"""

import logging
import re
from datetime import date

from .models import EOLDataSource, EOLStatus, EOLStatusEnum, SupportTypeEnum

logger = logging.getLogger(__name__)

# Known EOL patterns for operating systems
# Status: EOL_EXPIRED = past EOL, EOL_SOON = within 12 months
EOL_OS_PATTERNS: dict[str, dict] = {
    # AIX versions
    "aix 7.1": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2023, 4, 30),
        "support_type": SupportTypeEnum.NONE,
    },
    "aix 7.2": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2024, 12, 31),
        "support_type": SupportTypeEnum.EXTENDED,
    },
    "aix 7.3": {
        "status": EOLStatusEnum.ACTIVE,
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    # Windows Server versions
    "windows server 2008": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2020, 1, 14),
        "support_type": SupportTypeEnum.NONE,
    },
    "windows server 2012": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2023, 10, 10),
        "extended_support_end": date(2026, 10, 13),
        "support_type": SupportTypeEnum.EXTENDED,
    },
    "windows server 2016": {
        "status": EOLStatusEnum.EOL_SOON,
        "eol_date": date(2027, 1, 12),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    "windows server 2019": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2029, 1, 9),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    "windows server 2022": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2031, 10, 14),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    # RHEL versions
    "rhel 6": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2020, 11, 30),
        "support_type": SupportTypeEnum.NONE,
    },
    "rhel 7": {
        "status": EOLStatusEnum.EOL_SOON,
        "eol_date": date(2024, 6, 30),
        "extended_support_end": date(2028, 6, 30),
        "support_type": SupportTypeEnum.EXTENDED,
    },
    "rhel 8": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2029, 5, 31),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    "rhel 9": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2032, 5, 31),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    # Solaris versions
    "solaris 10": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2021, 1, 31),
        "support_type": SupportTypeEnum.NONE,
    },
    "solaris 11": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2031, 11, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    # Ubuntu LTS versions
    "ubuntu 18.04": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2023, 5, 31),
        "extended_support_end": date(2028, 4, 30),
        "support_type": SupportTypeEnum.EXTENDED,
        "lts": True,
    },
    "ubuntu 20.04": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2025, 4, 30),
        "extended_support_end": date(2030, 4, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    "ubuntu 22.04": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2027, 4, 30),
        "extended_support_end": date(2032, 4, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    "ubuntu 24.04": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2029, 4, 30),
        "extended_support_end": date(2034, 4, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
}

# Known EOL patterns for runtimes/languages
EOL_RUNTIME_PATTERNS: dict[str, dict] = {
    # Java versions
    "java 8": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2030, 12, 31),  # Oracle extends to 2030
        "support_type": SupportTypeEnum.EXTENDED,
        "lts": True,
    },
    "java 11": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2032, 9, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    "java 17": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2029, 9, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    "java 21": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2031, 9, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    # Python versions
    "python 2.7": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2020, 1, 1),
        "support_type": SupportTypeEnum.NONE,
    },
    "python 3.6": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2021, 12, 23),
        "support_type": SupportTypeEnum.NONE,
    },
    "python 3.7": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2023, 6, 27),
        "support_type": SupportTypeEnum.NONE,
    },
    "python 3.8": {
        "status": EOLStatusEnum.EOL_SOON,
        "eol_date": date(2024, 10, 31),
        "support_type": SupportTypeEnum.EXTENDED,
    },
    "python 3.9": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2025, 10, 31),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    "python 3.10": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2026, 10, 31),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    "python 3.11": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2027, 10, 31),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    "python 3.12": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2028, 10, 31),
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    # Node.js versions
    "node 10": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2021, 4, 30),
        "support_type": SupportTypeEnum.NONE,
        "lts": True,
    },
    "node 12": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2022, 4, 30),
        "support_type": SupportTypeEnum.NONE,
        "lts": True,
    },
    "node 14": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2023, 4, 30),
        "support_type": SupportTypeEnum.NONE,
        "lts": True,
    },
    "node 16": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2024, 4, 30),
        "support_type": SupportTypeEnum.NONE,
        "lts": True,
    },
    "node 18": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2025, 4, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    "node 20": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2026, 4, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    "node 22": {
        "status": EOLStatusEnum.ACTIVE,
        "eol_date": date(2027, 4, 30),
        "support_type": SupportTypeEnum.MAINSTREAM,
        "lts": True,
    },
    # .NET Framework versions
    ".net framework 4.5": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2016, 1, 12),
        "support_type": SupportTypeEnum.NONE,
    },
    ".net framework 4.6": {
        "status": EOLStatusEnum.EOL_EXPIRED,
        "eol_date": date(2022, 4, 26),
        "support_type": SupportTypeEnum.NONE,
    },
    ".net framework 4.7": {
        "status": EOLStatusEnum.ACTIVE,
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
    ".net framework 4.8": {
        "status": EOLStatusEnum.ACTIVE,
        "support_type": SupportTypeEnum.MAINSTREAM,
    },
}


def normalize_product_name(product: str) -> str:
    """Normalize product name for lookup."""
    normalized = product.lower().strip()
    # Common normalizations
    normalized = re.sub(r"red\s*hat\s*enterprise\s*linux", "rhel", normalized)
    normalized = re.sub(r"nodejs|node\.js", "node", normalized)
    normalized = re.sub(r"jdk|openjdk|oracle\s*java", "java", normalized)
    return normalized


def fallback_eol_check(
    product: str,
    version: str,
    product_type: str = "os",
) -> EOLStatus:
    """
    Check EOL status using hardcoded fallback patterns.

    Args:
        product: Product name (e.g., "Windows Server", "Java", "RHEL")
        version: Version string (e.g., "2012", "8", "7")
        product_type: Product type (os, runtime, database, framework)

    Returns:
        EOLStatus with fallback heuristics source
    """
    # Normalize product name
    normalized_product = normalize_product_name(product)

    # Build lookup key
    lookup_key = f"{normalized_product} {version}".lower().strip()

    # Select pattern dict based on product type
    if product_type in ("runtime", "framework"):
        patterns = EOL_RUNTIME_PATTERNS
    else:
        patterns = EOL_OS_PATTERNS

    # Try exact match first
    if lookup_key in patterns:
        pattern = patterns[lookup_key]
        return EOLStatus(
            product=product,
            version=version,
            product_type=product_type,
            status=pattern.get("status", EOLStatusEnum.UNKNOWN),
            eol_date=pattern.get("eol_date"),
            extended_support_end=pattern.get("extended_support_end"),
            support_type=pattern.get("support_type", SupportTypeEnum.NONE),
            source=EOLDataSource.FALLBACK_HEURISTICS,
            lts=pattern.get("lts"),
            confidence=0.75,  # Fallback patterns have lower confidence
        )

    # Try partial match (product prefix)
    for key, pattern in patterns.items():
        if key.startswith(normalized_product) and version in key:
            return EOLStatus(
                product=product,
                version=version,
                product_type=product_type,
                status=pattern.get("status", EOLStatusEnum.UNKNOWN),
                eol_date=pattern.get("eol_date"),
                extended_support_end=pattern.get("extended_support_end"),
                support_type=pattern.get("support_type", SupportTypeEnum.NONE),
                source=EOLDataSource.FALLBACK_HEURISTICS,
                lts=pattern.get("lts"),
                confidence=0.6,  # Partial match has lower confidence
            )

    # No match found
    logger.debug(f"No fallback pattern found for {product} {version}")
    return EOLStatus(
        product=product,
        version=version,
        product_type=product_type,
        status=EOLStatusEnum.UNKNOWN,
        support_type=SupportTypeEnum.NONE,
        source=EOLDataSource.FALLBACK_HEURISTICS,
        confidence=0.0,
    )
