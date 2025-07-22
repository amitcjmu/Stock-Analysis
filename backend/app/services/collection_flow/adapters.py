"""
Base Adapter Interface and Registry for Collection Flow

This module provides the base adapter interface for platform-specific data collection
and a registry for managing adapter implementations.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import AutomationTier

logger = logging.getLogger(__name__)


class AdapterCapability(str, Enum):
    """Adapter capabilities"""
    SERVER_DISCOVERY = "server_discovery"
    APPLICATION_DISCOVERY = "application_discovery"
    DATABASE_DISCOVERY = "database_discovery"
    NETWORK_DISCOVERY = "network_discovery"
    DEPENDENCY_MAPPING = "dependency_mapping"
    PERFORMANCE_METRICS = "performance_metrics"
    CONFIGURATION_EXPORT = "configuration_export"
    CREDENTIAL_VALIDATION = "credential_validation"


class CollectionMethod(str, Enum):
    """Data collection methods"""
    API = "api"
    SCRIPT = "script"
    TEMPLATE = "template"
    MANUAL = "manual"
    IMPORT = "import"


@dataclass
class AdapterMetadata:
    """Metadata for adapter registration"""
    name: str
    version: str
    adapter_type: str
    automation_tier: AutomationTier
    supported_platforms: List[str]
    capabilities: List[AdapterCapability]
    required_credentials: List[str]
    configuration_schema: Dict[str, Any]
    description: Optional[str] = None
    author: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class CollectionRequest:
    """Request for data collection"""
    flow_id: uuid.UUID
    platform: str
    collection_method: CollectionMethod
    target_resources: List[str]
    credentials: Dict[str, Any]
    configuration: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CollectionResponse:
    """Response from data collection"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    resource_count: int = 0
    collection_method: Optional[CollectionMethod] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAdapter(ABC):
    """
    Base adapter interface for platform-specific data collection.
    
    All platform adapters must inherit from this base class and implement
    the required methods for data collection, validation, and transformation.
    """
    
    def __init__(self, db: AsyncSession, metadata: AdapterMetadata):
        """
        Initialize the adapter.
        
        Args:
            db: Database session
            metadata: Adapter metadata
        """
        self.db = db
        self.metadata = metadata
        self.logger = logging.getLogger(f"{__name__}.{metadata.name}")
        
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate platform credentials.
        
        Args:
            credentials: Platform-specific credentials
            
        Returns:
            True if credentials are valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to the platform.
        
        Args:
            configuration: Connection configuration
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data from the platform.
        
        Args:
            request: Collection request with parameters
            
        Returns:
            Collection response with data or error information
        """
        pass
    
    @abstractmethod
    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available resources for collection.
        
        Args:
            configuration: Platform configuration
            
        Returns:
            List of available resource identifiers
        """
        pass
    
    @abstractmethod
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw platform data to normalized format.
        
        Args:
            raw_data: Raw data from platform
            
        Returns:
            Normalized data structure
        """
        pass
    
    async def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        """
        Validate adapter configuration against schema.
        
        Args:
            configuration: Configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        schema = self.metadata.configuration_schema
        required_fields = schema.get("required", [])
        
        # Check required fields
        for field in required_fields:
            if field not in configuration:
                self.logger.error(f"Missing required configuration field: {field}")
                return False
                
        # Validate field types if specified
        properties = schema.get("properties", {})
        for field, value in configuration.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type:
                    # Simple type validation
                    type_map = {
                        "string": str,
                        "number": (int, float),
                        "boolean": bool,
                        "object": dict,
                        "array": list
                    }
                    expected = type_map.get(expected_type)
                    if expected and not isinstance(value, expected):
                        self.logger.error(
                            f"Invalid type for field {field}: expected {expected_type}, got {type(value).__name__}"
                        )
                        return False
        
        return True
    
    def get_capabilities(self) -> List[AdapterCapability]:
        """Get adapter capabilities."""
        return self.metadata.capabilities
    
    def supports_capability(self, capability: AdapterCapability) -> bool:
        """Check if adapter supports a specific capability."""
        return capability in self.metadata.capabilities
    
    def get_automation_tier(self) -> AutomationTier:
        """Get adapter automation tier."""
        return self.metadata.automation_tier


class AdapterRegistry:
    """
    Registry for managing adapter implementations.
    
    This registry maintains a collection of available adapters and provides
    methods for registration, discovery, and instantiation.
    """
    
    def __init__(self):
        """Initialize the adapter registry."""
        self._adapters: Dict[str, Type[BaseAdapter]] = {}
        self._metadata: Dict[str, AdapterMetadata] = {}
        self.logger = logging.getLogger(f"{__name__}.AdapterRegistry")
        
    def register(self, adapter_class: Type[BaseAdapter], metadata: AdapterMetadata) -> None:
        """
        Register an adapter implementation.
        
        Args:
            adapter_class: Adapter class implementing BaseAdapter
            metadata: Adapter metadata
        """
        adapter_key = f"{metadata.name}:{metadata.version}"
        
        if adapter_key in self._adapters:
            self.logger.warning(f"Adapter {adapter_key} already registered, overwriting")
            
        self._adapters[adapter_key] = adapter_class
        self._metadata[adapter_key] = metadata
        
        self.logger.info(f"Registered adapter {adapter_key} for platforms: {metadata.supported_platforms}")
        
    def unregister(self, name: str, version: str) -> None:
        """
        Unregister an adapter.
        
        Args:
            name: Adapter name
            version: Adapter version
        """
        adapter_key = f"{name}:{version}"
        
        if adapter_key in self._adapters:
            del self._adapters[adapter_key]
            del self._metadata[adapter_key]
            self.logger.info(f"Unregistered adapter {adapter_key}")
        else:
            self.logger.warning(f"Adapter {adapter_key} not found in registry")
            
    def get_adapter(self, name: str, version: str, db: AsyncSession) -> Optional[BaseAdapter]:
        """
        Get an adapter instance.
        
        Args:
            name: Adapter name
            version: Adapter version
            db: Database session
            
        Returns:
            Adapter instance or None if not found
        """
        adapter_key = f"{name}:{version}"
        
        if adapter_key not in self._adapters:
            self.logger.error(f"Adapter {adapter_key} not found in registry")
            return None
            
        adapter_class = self._adapters[adapter_key]
        metadata = self._metadata[adapter_key]
        
        return adapter_class(db, metadata)
        
    def get_adapters_by_platform(self, platform: str) -> List[AdapterMetadata]:
        """
        Get all adapters supporting a specific platform.
        
        Args:
            platform: Platform name
            
        Returns:
            List of adapter metadata
        """
        adapters = []
        
        for metadata in self._metadata.values():
            if platform in metadata.supported_platforms:
                adapters.append(metadata)
                
        return adapters
        
    def get_adapters_by_tier(self, tier: AutomationTier) -> List[AdapterMetadata]:
        """
        Get all adapters for a specific automation tier.
        
        Args:
            tier: Automation tier
            
        Returns:
            List of adapter metadata
        """
        adapters = []
        
        for metadata in self._metadata.values():
            if metadata.automation_tier == tier:
                adapters.append(metadata)
                
        return adapters
        
    def get_adapters_by_capability(self, capability: AdapterCapability) -> List[AdapterMetadata]:
        """
        Get all adapters supporting a specific capability.
        
        Args:
            capability: Adapter capability
            
        Returns:
            List of adapter metadata
        """
        adapters = []
        
        for metadata in self._metadata.values():
            if capability in metadata.capabilities:
                adapters.append(metadata)
                
        return adapters
        
    def list_all_adapters(self) -> List[AdapterMetadata]:
        """
        Get all registered adapters.
        
        Returns:
            List of all adapter metadata
        """
        return list(self._metadata.values())
        
    def get_adapter_metadata(self, name: str, version: str) -> Optional[AdapterMetadata]:
        """
        Get metadata for a specific adapter.
        
        Args:
            name: Adapter name
            version: Adapter version
            
        Returns:
            Adapter metadata or None if not found
        """
        adapter_key = f"{name}:{version}"
        return self._metadata.get(adapter_key)


# Global adapter registry instance
adapter_registry = AdapterRegistry()


def register_adapter(metadata: AdapterMetadata) -> Callable:
    """
    Decorator for registering adapter classes.
    
    Usage:
        @register_adapter(metadata)
        class MyAdapter(BaseAdapter):
            ...
    
    Args:
        metadata: Adapter metadata
        
    Returns:
        Decorator function
    """
    def decorator(adapter_class: Type[BaseAdapter]) -> Type[BaseAdapter]:
        adapter_registry.register(adapter_class, metadata)
        return adapter_class
    return decorator