"""
Azure-specific exceptions and error handling
"""

try:
    from azure.core.exceptions import ClientAuthenticationError, HttpResponseError

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    # Create dummy classes for type hints
    ClientAuthenticationError = HttpResponseError = Exception


class AzureAdapterError(Exception):
    """Base exception for Azure adapter errors"""

    pass


class AzureCredentialsError(AzureAdapterError):
    """Azure credentials validation error"""

    pass


class AzureConnectivityError(AzureAdapterError):
    """Azure connectivity test error"""

    pass


class AzureResourceDiscoveryError(AzureAdapterError):
    """Azure resource discovery error"""

    pass


class AzureMetricsCollectionError(AzureAdapterError):
    """Azure metrics collection error"""

    pass


class AzureSDKNotAvailableError(AzureAdapterError):
    """Azure SDK not available error"""

    def __init__(self):
        super().__init__(
            "Azure SDK is not installed. Please install azure-mgmt-* packages."
        )
