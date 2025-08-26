"""
Enums for canonical applications models
"""

from enum import Enum


class MatchMethod(str, Enum):
    """Methods used for application name matching"""

    EXACT = "exact"
    FUZZY_TEXT = "fuzzy_text"
    VECTOR_SIMILARITY = "vector_similarity"
    MANUAL_VERIFICATION = "manual_verification"
    BULK_IMPORT = "bulk_import"


class VerificationSource(str, Enum):
    """Sources of application name verification"""

    USER_INPUT = "user_input"
    DISCOVERY_DATA = "discovery_data"
    ASSET_INVENTORY = "asset_inventory"
    MANUAL_CURATION = "manual_curation"
    EXTERNAL_CMDB = "external_cmdb"
