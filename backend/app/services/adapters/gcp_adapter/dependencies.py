"""
GCP SDK Dependencies

Handles the conditional import of Google Cloud SDK libraries.
"""

try:
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import (
        asset_v1,
        compute_v1,
        container_v1,
        functions_v1,
        monitoring_v3,
        sql_v1,
        storage,
    )
    from google.oauth2 import service_account
    from googleapiclient import discovery
    from googleapiclient.errors import HttpError

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    # Create dummy classes to prevent NameError
    asset_v1 = None
    monitoring_v3 = None
    compute_v1 = None
    sql_v1 = None
    storage = None
    container_v1 = None
    functions_v1 = None
    service_account = None
    DefaultCredentialsError = Exception
    discovery = None
    HttpError = Exception

__all__ = [
    "GCP_AVAILABLE",
    "asset_v1",
    "monitoring_v3",
    "compute_v1",
    "sql_v1",
    "storage",
    "container_v1",
    "functions_v1",
    "service_account",
    "DefaultCredentialsError",
    "discovery",
    "HttpError",
]
