"""
Deployment configuration for different modes.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class DeploymentMode(Enum):
    """Supported deployment modes."""
    DEVELOPMENT = "development"
    ON_PREMISES = "on_premises"
    SAAS = "saas"
    HYBRID = "hybrid"


@dataclass
class ServiceConfig:
    """Configuration for a specific service."""
    enabled: bool = True
    implementation: str = "default"
    config: Dict[str, Any] = field(default_factory=dict)
    fallback: Optional[str] = None


@dataclass
class DeploymentConfig:
    """Complete deployment configuration."""
    mode: DeploymentMode
    services: Dict[str, ServiceConfig]
    features: Dict[str, bool]
    
    @classmethod
    def for_development(cls) -> "DeploymentConfig":
        """Create development mode configuration."""
        return cls(
            mode=DeploymentMode.DEVELOPMENT,
            services={
                "credentials": ServiceConfig(
                    implementation="local",
                    config={"storage_path": "./.adcs/credentials.json"}
                ),
                "telemetry": ServiceConfig(
                    implementation="noop",
                    enabled=False
                ),
                "authentication": ServiceConfig(
                    implementation="database",
                    config={"session_timeout": 86400}
                ),
                "external_api": ServiceConfig(
                    implementation="mock",
                    enabled=True
                )
            },
            features={
                "cloud_kms": False,
                "sso": False,
                "telemetry": False,
                "rate_limiting": False,
                "external_integrations": False
            }
        )
    
    @classmethod
    def for_on_premises(cls) -> "DeploymentConfig":
        """Create on-premises mode configuration."""
        return cls(
            mode=DeploymentMode.ON_PREMISES,
            services={
                "credentials": ServiceConfig(
                    implementation="local",
                    config={"storage_path": "/var/adcs/credentials.json"},
                    fallback="env"
                ),
                "telemetry": ServiceConfig(
                    implementation="noop",
                    enabled=os.getenv("ENABLE_TELEMETRY", "false").lower() == "true"
                ),
                "authentication": ServiceConfig(
                    implementation="database",
                    config={"session_timeout": 28800}  # 8 hours
                ),
                "external_api": ServiceConfig(
                    implementation="noop",
                    enabled=False
                )
            },
            features={
                "cloud_kms": False,
                "sso": False,
                "telemetry": False,
                "rate_limiting": True,
                "external_integrations": False
            }
        )
    
    @classmethod
    def for_saas(cls) -> "DeploymentConfig":
        """Create SaaS mode configuration."""
        return cls(
            mode=DeploymentMode.SAAS,
            services={
                "credentials": ServiceConfig(
                    implementation="cloud_kms",
                    config={
                        "endpoint": os.getenv("KMS_ENDPOINT"),
                        "api_key": os.getenv("KMS_API_KEY")
                    },
                    fallback="local"
                ),
                "telemetry": ServiceConfig(
                    implementation="cloud",
                    config={
                        "endpoint": os.getenv("TELEMETRY_ENDPOINT"),
                        "api_key": os.getenv("TELEMETRY_API_KEY")
                    },
                    enabled=True
                ),
                "authentication": ServiceConfig(
                    implementation="sso",
                    config={
                        "provider": os.getenv("SSO_PROVIDER", "oauth2"),
                        "client_id": os.getenv("SSO_CLIENT_ID"),
                        "client_secret": os.getenv("SSO_CLIENT_SECRET")
                    },
                    fallback="database"
                ),
                "external_api": ServiceConfig(
                    implementation="production",
                    enabled=True
                )
            },
            features={
                "cloud_kms": True,
                "sso": True,
                "telemetry": True,
                "rate_limiting": True,
                "external_integrations": True
            }
        )
    
    @classmethod
    def for_hybrid(cls) -> "DeploymentConfig":
        """Create hybrid mode configuration."""
        return cls(
            mode=DeploymentMode.HYBRID,
            services={
                "credentials": ServiceConfig(
                    implementation="cloud_kms" if os.getenv("USE_CLOUD_KMS") else "local",
                    config={
                        "endpoint": os.getenv("KMS_ENDPOINT"),
                        "storage_path": "/var/adcs/credentials.json"
                    }
                ),
                "telemetry": ServiceConfig(
                    implementation="cloud" if os.getenv("TELEMETRY_ENDPOINT") else "noop",
                    config={
                        "endpoint": os.getenv("TELEMETRY_ENDPOINT"),
                        "api_key": os.getenv("TELEMETRY_API_KEY")
                    }
                ),
                "authentication": ServiceConfig(
                    implementation="sso" if os.getenv("SSO_ENABLED") else "database",
                    config={
                        "provider": os.getenv("SSO_PROVIDER", "oauth2"),
                        "session_timeout": 43200  # 12 hours
                    }
                ),
                "external_api": ServiceConfig(
                    implementation="production" if os.getenv("EXTERNAL_API_ENABLED") else "noop",
                    enabled=True
                )
            },
            features={
                "cloud_kms": bool(os.getenv("USE_CLOUD_KMS")),
                "sso": bool(os.getenv("SSO_ENABLED")),
                "telemetry": bool(os.getenv("TELEMETRY_ENDPOINT")),
                "rate_limiting": True,
                "external_integrations": bool(os.getenv("EXTERNAL_API_ENABLED"))
            }
        )
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service."""
        return self.services.get(
            service_name,
            ServiceConfig(enabled=False, implementation="noop")
        )
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature_name, False)


class DeploymentSettings(BaseSettings):
    """Settings for deployment configuration."""
    
    DEPLOYMENT_MODE: str = os.getenv("DEPLOYMENT_MODE", "development")
    
    # Service overrides
    CREDENTIAL_SERVICE: Optional[str] = os.getenv("CREDENTIAL_SERVICE")
    TELEMETRY_SERVICE: Optional[str] = os.getenv("TELEMETRY_SERVICE")
    AUTH_SERVICE: Optional[str] = os.getenv("AUTH_SERVICE")
    
    # Feature flags
    ENABLE_CLOUD_KMS: bool = os.getenv("ENABLE_CLOUD_KMS", "false").lower() == "true"
    ENABLE_SSO: bool = os.getenv("ENABLE_SSO", "false").lower() == "true"
    ENABLE_TELEMETRY: bool = os.getenv("ENABLE_TELEMETRY", "false").lower() == "true"
    ENABLE_EXTERNAL_API: bool = os.getenv("ENABLE_EXTERNAL_API", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_deployment_config() -> DeploymentConfig:
    """Get the current deployment configuration."""
    settings = DeploymentSettings()
    
    # Determine deployment mode
    mode_str = settings.DEPLOYMENT_MODE.lower()
    if mode_str == "development":
        config = DeploymentConfig.for_development()
    elif mode_str == "on_premises" or mode_str == "onprem":
        config = DeploymentConfig.for_on_premises()
    elif mode_str == "saas" or mode_str == "cloud":
        config = DeploymentConfig.for_saas()
    elif mode_str == "hybrid":
        config = DeploymentConfig.for_hybrid()
    else:
        # Default to development
        config = DeploymentConfig.for_development()
    
    # Apply service overrides
    if settings.CREDENTIAL_SERVICE:
        config.services["credentials"].implementation = settings.CREDENTIAL_SERVICE
    
    if settings.TELEMETRY_SERVICE:
        config.services["telemetry"].implementation = settings.TELEMETRY_SERVICE
    
    if settings.AUTH_SERVICE:
        config.services["authentication"].implementation = settings.AUTH_SERVICE
    
    # Apply feature flag overrides
    if settings.ENABLE_CLOUD_KMS:
        config.features["cloud_kms"] = True
    
    if settings.ENABLE_SSO:
        config.features["sso"] = True
    
    if settings.ENABLE_TELEMETRY:
        config.features["telemetry"] = True
        config.services["telemetry"].enabled = True
    
    if settings.ENABLE_EXTERNAL_API:
        config.features["external_integrations"] = True
        config.services["external_api"].enabled = True
    
    return config