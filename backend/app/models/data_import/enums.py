"""
Data Import Enumerations
"""

import enum


class ImportStatus(str, enum.Enum):
    """Enum for the status of a data import job."""

    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VALIDATING = "validating"
    PROCESSED = "processed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ImportType(str, enum.Enum):
    """Enum for the type of data being imported."""

    CMDB = "cmdb"
    ASSET_INVENTORY = "asset_inventory"
    NETWORK_DATA = "network_data"
    BUSINESS_APPS = "business_apps"
    USER_DATA = "user_data"
    OTHER = "other"
