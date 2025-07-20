"""
Infrastructure abstractions for deployment flexibility.
"""

from .credentials import CredentialManager
from .telemetry import TelemetryService
from .authentication import AuthenticationBackend
from .deployment import (
    DeploymentMode,
    DeploymentConfig,
    get_deployment_config,
    ServiceDetector,
    ServiceFactory,
    get_service_factory,
    get_service
)

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
    "get_service"
]