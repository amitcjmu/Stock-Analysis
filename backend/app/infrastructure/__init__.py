"""
Infrastructure abstractions for deployment flexibility.
"""

from .authentication import AuthenticationBackend
from .credentials import CredentialManager
from .deployment import (
    DeploymentConfig,
    DeploymentMode,
    ServiceDetector,
    ServiceFactory,
    get_deployment_config,
    get_service,
    get_service_factory,
)
from .telemetry import TelemetryService

__all__ = [
    "CredentialManager",
    "TelemetryService",
    "AuthenticationBackend",
    "DeploymentMode",
    "DeploymentConfig",
    "get_deployment_config",
    "ServiceDetector",
    "ServiceFactory",
    "get_service_factory",
    "get_service",
]
