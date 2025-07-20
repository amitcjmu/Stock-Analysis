"""
Service factory for creating appropriate service implementations based on deployment mode.
"""

import logging
from typing import Dict, Any, Optional, Type

from ..credentials import CredentialManager, CloudKMSCredentialManager, LocalCredentialManager
from ..telemetry import TelemetryService, CloudTelemetryService, NoOpTelemetryService
from ..authentication import AuthenticationBackend, DatabaseAuthBackend, SSOAuthBackend
from .noop_services import (
    NoOpExternalAPIService,
    NoOpNotificationService,
    NoOpQueueService,
    NoOpCacheService,
    NoOpSearchService
)
from .config import DeploymentConfig, ServiceConfig
from .detector import service_detector

logger = logging.getLogger(__name__)


class ServiceFactory:
    """
    Factory for creating service instances based on deployment configuration.
    """
    
    def __init__(self, deployment_config: DeploymentConfig):
        """
        Initialize service factory.
        
        Args:
            deployment_config: Deployment configuration
        """
        self.config = deployment_config
        self._service_cache: Dict[str, Any] = {}
        self._service_registry: Dict[str, Dict[str, Type]] = {
            "credentials": {
                "cloud_kms": CloudKMSCredentialManager,
                "local": LocalCredentialManager,
                "noop": LocalCredentialManager
            },
            "telemetry": {
                "cloud": CloudTelemetryService,
                "noop": NoOpTelemetryService,
                "local": NoOpTelemetryService
            },
            "authentication": {
                "database": DatabaseAuthBackend,
                "sso": SSOAuthBackend,
                "noop": DatabaseAuthBackend
            },
            "external_api": {
                "production": None,  # Would be actual implementation
                "mock": NoOpExternalAPIService,
                "noop": NoOpExternalAPIService
            },
            "notification": {
                "production": None,  # Would be actual implementation
                "noop": NoOpNotificationService
            },
            "queue": {
                "production": None,  # Would be actual implementation
                "noop": NoOpQueueService
            },
            "cache": {
                "production": None,  # Would be actual implementation
                "noop": NoOpCacheService
            },
            "search": {
                "production": None,  # Would be actual implementation
                "noop": NoOpSearchService
            }
        }
        
        logger.info(f"Initialized ServiceFactory for deployment mode: {deployment_config.mode.value}")
    
    async def get_service(self, service_name: str, **kwargs) -> Any:
        """
        Get or create a service instance.
        
        Args:
            service_name: Name of the service
            **kwargs: Additional arguments for service initialization
            
        Returns:
            Service instance
        """
        # Check cache first
        if service_name in self._service_cache:
            return self._service_cache[service_name]
        
        # Get service configuration
        service_config = self.config.get_service_config(service_name)
        
        # Create service instance
        service = await self._create_service(service_name, service_config, **kwargs)
        
        # Cache the service
        self._service_cache[service_name] = service
        
        return service
    
    async def _create_service(
        self,
        service_name: str,
        service_config: ServiceConfig,
        **kwargs
    ) -> Any:
        """
        Create a service instance with fallback support.
        
        Args:
            service_name: Name of the service
            service_config: Service configuration
            **kwargs: Additional arguments
            
        Returns:
            Service instance
        """
        if not service_config.enabled:
            logger.info(f"Service {service_name} is disabled, using no-op implementation")
            return await self._create_noop_service(service_name, **kwargs)
        
        # Try primary implementation
        try:
            implementation = service_config.implementation
            service_class = self._get_service_class(service_name, implementation)
            
            if service_class:
                # Check if service is available
                if await self._check_service_availability(service_name, implementation):
                    logger.info(f"Creating {implementation} implementation for {service_name}")
                    return service_class(**service_config.config, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create {service_config.implementation} for {service_name}: {e}")
        
        # Try fallback implementation
        if service_config.fallback:
            try:
                fallback_class = self._get_service_class(service_name, service_config.fallback)
                if fallback_class:
                    logger.warning(f"Using fallback {service_config.fallback} for {service_name}")
                    return fallback_class(**kwargs)
            except Exception as e:
                logger.error(f"Failed to create fallback {service_config.fallback} for {service_name}: {e}")
        
        # Last resort: no-op implementation
        logger.warning(f"Using no-op implementation for {service_name}")
        return await self._create_noop_service(service_name, **kwargs)
    
    def _get_service_class(self, service_name: str, implementation: str) -> Optional[Type]:
        """
        Get service class for given implementation.
        
        Args:
            service_name: Name of the service
            implementation: Implementation type
            
        Returns:
            Service class or None
        """
        service_impls = self._service_registry.get(service_name, {})
        return service_impls.get(implementation)
    
    async def _check_service_availability(self, service_name: str, implementation: str) -> bool:
        """
        Check if a service implementation is available.
        
        Args:
            service_name: Name of the service
            implementation: Implementation type
            
        Returns:
            True if available
        """
        # Map service implementations to detector checks
        availability_map = {
            ("credentials", "cloud_kms"): "cloud_kms",
            ("telemetry", "cloud"): "telemetry",
            ("authentication", "sso"): "sso",
            ("external_api", "production"): "external_api"
        }
        
        detector_service = availability_map.get((service_name, implementation))
        if detector_service:
            return await service_detector.check_service(detector_service)
        
        # Default to available for unknown services
        return True
    
    async def _create_noop_service(self, service_name: str, **kwargs) -> Any:
        """
        Create a no-op service implementation.
        
        Args:
            service_name: Name of the service
            **kwargs: Additional arguments
            
        Returns:
            No-op service instance
        """
        noop_mapping = {
            "credentials": LocalCredentialManager,
            "telemetry": NoOpTelemetryService,
            "authentication": DatabaseAuthBackend,
            "external_api": NoOpExternalAPIService,
            "notification": NoOpNotificationService,
            "queue": NoOpQueueService,
            "cache": NoOpCacheService,
            "search": NoOpSearchService
        }
        
        service_class = noop_mapping.get(service_name)
        if service_class:
            return service_class(**kwargs)
        
        raise ValueError(f"No no-op implementation for service: {service_name}")
    
    async def get_credential_manager(self, **kwargs) -> CredentialManager:
        """Get credential manager instance."""
        return await self.get_service("credentials", **kwargs)
    
    async def get_telemetry_service(self, **kwargs) -> TelemetryService:
        """Get telemetry service instance."""
        return await self.get_service("telemetry", **kwargs)
    
    async def get_auth_backend(self, **kwargs) -> AuthenticationBackend:
        """Get authentication backend instance."""
        return await self.get_service("authentication", **kwargs)
    
    async def get_external_api(self, **kwargs) -> Any:
        """Get external API service instance."""
        return await self.get_service("external_api", **kwargs)
    
    async def get_notification_service(self, **kwargs) -> Any:
        """Get notification service instance."""
        return await self.get_service("notification", **kwargs)
    
    async def get_queue_service(self, **kwargs) -> Any:
        """Get queue service instance."""
        return await self.get_service("queue", **kwargs)
    
    async def get_cache_service(self, **kwargs) -> Any:
        """Get cache service instance."""
        return await self.get_service("cache", **kwargs)
    
    async def get_search_service(self, **kwargs) -> Any:
        """Get search service instance."""
        return await self.get_service("search", **kwargs)
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all services.
        
        Returns:
            Dictionary of service health statuses
        """
        health_status = {}
        
        for service_name, service_instance in self._service_cache.items():
            try:
                if hasattr(service_instance, 'health_check'):
                    health_status[service_name] = await service_instance.health_check()
                else:
                    health_status[service_name] = True
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_status[service_name] = False
        
        return health_status


# Global service factory instance
_service_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """
    Get the global service factory instance.
    
    Returns:
        Service factory instance
    """
    global _service_factory
    
    if _service_factory is None:
        from .config import get_deployment_config
        deployment_config = get_deployment_config()
        _service_factory = ServiceFactory(deployment_config)
    
    return _service_factory


async def get_service(service_name: str, **kwargs) -> Any:
    """
    Convenience function to get a service instance.
    
    Args:
        service_name: Name of the service
        **kwargs: Additional arguments
        
    Returns:
        Service instance
    """
    factory = get_service_factory()
    return await factory.get_service(service_name, **kwargs)