"""
Service availability detection for automatic fallbacks.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceDetector:
    """
    Detects availability of external services and manages fallbacks.
    """
    
    def __init__(self):
        """Initialize service detector."""
        self._service_status: Dict[str, bool] = {}
        self._last_check: Dict[str, datetime] = {}
        self._check_interval = timedelta(minutes=5)
        self._health_checks: Dict[str, Callable] = {}
        logger.info("Initialized ServiceDetector")
    
    def register_health_check(self, service_name: str, health_check: Callable) -> None:
        """
        Register a health check function for a service.
        
        Args:
            service_name: Name of the service
            health_check: Async function that returns True if healthy
        """
        self._health_checks[service_name] = health_check
        logger.info(f"Registered health check for service: {service_name}")
    
    async def check_service(self, service_name: str, force: bool = False) -> bool:
        """
        Check if a service is available.
        
        Args:
            service_name: Name of the service to check
            force: Force check even if recently checked
            
        Returns:
            True if service is available
        """
        # Check cache first
        if not force and service_name in self._last_check:
            if datetime.utcnow() - self._last_check[service_name] < self._check_interval:
                return self._service_status.get(service_name, False)
        
        # Perform health check
        if service_name not in self._health_checks:
            logger.warning(f"No health check registered for service: {service_name}")
            return False
        
        try:
            health_check = self._health_checks[service_name]
            is_healthy = await health_check()
            
            self._service_status[service_name] = is_healthy
            self._last_check[service_name] = datetime.utcnow()
            
            if is_healthy:
                logger.info(f"Service {service_name} is healthy")
            else:
                logger.warning(f"Service {service_name} is not available")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            self._service_status[service_name] = False
            self._last_check[service_name] = datetime.utcnow()
            return False
    
    async def check_all_services(self) -> Dict[str, bool]:
        """
        Check all registered services.
        
        Returns:
            Dictionary of service statuses
        """
        results = {}
        
        # Check services in parallel
        tasks = []
        for service_name in self._health_checks:
            tasks.append(self.check_service(service_name, force=True))
        
        statuses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service_name, status in zip(self._health_checks.keys(), statuses):
            if isinstance(status, Exception):
                logger.error(f"Exception checking {service_name}: {status}")
                results[service_name] = False
            else:
                results[service_name] = status
        
        return results
    
    async def detect_cloud_kms(self) -> bool:
        """Detect if Cloud KMS is available."""
        # Check for KMS configuration
        kms_endpoint = os.getenv("KMS_ENDPOINT")
        kms_api_key = os.getenv("KMS_API_KEY")
        
        if not kms_endpoint or not kms_api_key:
            logger.debug("Cloud KMS not configured")
            return False
        
        # In production, would ping the KMS endpoint
        # For now, assume available if configured
        return True
    
    async def detect_telemetry_service(self) -> bool:
        """Detect if telemetry service is available."""
        # Check for telemetry configuration
        telemetry_endpoint = os.getenv("TELEMETRY_ENDPOINT")
        telemetry_api_key = os.getenv("TELEMETRY_API_KEY")
        
        if not telemetry_endpoint:
            logger.debug("Telemetry service not configured")
            return False
        
        # In production, would ping the telemetry endpoint
        return True
    
    async def detect_sso_provider(self) -> bool:
        """Detect if SSO provider is available."""
        # Check for SSO configuration
        sso_enabled = os.getenv("SSO_ENABLED", "false").lower() == "true"
        sso_client_id = os.getenv("SSO_CLIENT_ID")
        sso_authorize_url = os.getenv("SSO_AUTHORIZE_URL")
        
        if not sso_enabled or not sso_client_id or not sso_authorize_url:
            logger.debug("SSO not configured")
            return False
        
        # In production, would check SSO provider endpoint
        return True
    
    async def detect_external_api(self) -> bool:
        """Detect if external API is available."""
        # Check for external API configuration
        api_enabled = os.getenv("EXTERNAL_API_ENABLED", "false").lower() == "true"
        api_endpoint = os.getenv("EXTERNAL_API_ENDPOINT")
        
        if not api_enabled or not api_endpoint:
            logger.debug("External API not configured")
            return False
        
        # In production, would ping the API endpoint
        return True
    
    async def detect_database(self) -> bool:
        """Detect if database is available."""
        try:
            # Import here to avoid circular dependencies
            from app.core.database import SessionLocal
            
            # Try to create a session
            async with SessionLocal() as session:
                # Simple query to test connection
                result = await session.execute("SELECT 1")
                return result is not None
                
        except Exception as e:
            logger.error(f"Database detection failed: {e}")
            return False
    
    def get_service_status(self, service_name: str) -> Optional[bool]:
        """
        Get cached status of a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if healthy, False if not, None if never checked
        """
        return self._service_status.get(service_name)
    
    def get_all_statuses(self) -> Dict[str, bool]:
        """Get all cached service statuses."""
        return self._service_status.copy()
    
    async def initialize_default_checks(self) -> None:
        """Initialize default health checks for common services."""
        # Register default health checks
        self.register_health_check("cloud_kms", self.detect_cloud_kms)
        self.register_health_check("telemetry", self.detect_telemetry_service)
        self.register_health_check("sso", self.detect_sso_provider)
        self.register_health_check("external_api", self.detect_external_api)
        self.register_health_check("database", self.detect_database)
        
        # Perform initial checks
        await self.check_all_services()
        
        logger.info("Initialized default service health checks")


# Global service detector instance
service_detector = ServiceDetector()


async def get_available_services() -> Dict[str, bool]:
    """
    Get current availability of all services.
    
    Returns:
        Dictionary of service availability
    """
    return await service_detector.check_all_services()


async def is_service_available(service_name: str) -> bool:
    """
    Check if a specific service is available.
    
    Args:
        service_name: Name of the service
        
    Returns:
        True if available
    """
    return await service_detector.check_service(service_name)