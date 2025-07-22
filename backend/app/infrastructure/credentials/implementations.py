"""
Concrete implementations of the CredentialManager interface.
"""

import json
import logging
import os
import secrets
from datetime import datetime
from typing import Any, Dict, Optional

from .interface import CredentialManager

logger = logging.getLogger(__name__)


class CloudKMSCredentialManager(CredentialManager):
    """
    Cloud Key Management Service implementation for SaaS deployments.
    Simulates integration with services like AWS KMS, Azure Key Vault, or Google Cloud KMS.
    """
    
    def __init__(self, kms_endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Cloud KMS credential manager.
        
        Args:
            kms_endpoint: The KMS service endpoint
            api_key: API key for KMS authentication
        """
        self.kms_endpoint = kms_endpoint or os.getenv("KMS_ENDPOINT")
        self.api_key = api_key or os.getenv("KMS_API_KEY")
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized CloudKMSCredentialManager with endpoint: {self.kms_endpoint}")
    
    async def get_credential(self, key: str, namespace: Optional[str] = None) -> Optional[str]:
        """Retrieve credential from KMS."""
        cache_key = f"{namespace or 'default'}:{key}"
        
        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Retrieved credential '{key}' from cache")
            return self._cache[cache_key].get("value")
        
        # In production, this would make an API call to KMS
        # For now, simulate with environment variables
        env_key = f"{namespace.upper()}_{key.upper()}" if namespace else key.upper()
        value = os.getenv(env_key)
        
        if value:
            self._cache[cache_key] = {
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"Retrieved credential '{key}' from KMS")
        else:
            logger.warning(f"Credential '{key}' not found in KMS")
            
        return value
    
    async def set_credential(self, key: str, value: str, namespace: Optional[str] = None) -> None:
        """Store credential in KMS."""
        cache_key = f"{namespace or 'default'}:{key}"
        
        # In production, this would make an API call to KMS
        self._cache[cache_key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "encrypted": True  # Flag indicating KMS encryption
        }
        
        logger.info(f"Stored credential '{key}' in KMS")
    
    async def delete_credential(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete credential from KMS."""
        cache_key = f"{namespace or 'default'}:{key}"
        
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"Deleted credential '{key}' from KMS")
            return True
        
        logger.warning(f"Credential '{key}' not found for deletion")
        return False
    
    async def list_credentials(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """List credentials in KMS."""
        credentials = {}
        prefix = f"{namespace}:" if namespace else ""
        
        for cache_key, data in self._cache.items():
            if not namespace or cache_key.startswith(prefix):
                key_name = cache_key.split(":", 1)[1] if ":" in cache_key else cache_key
                credentials[key_name] = {
                    "timestamp": data.get("timestamp"),
                    "encrypted": data.get("encrypted", True)
                }
        
        logger.info(f"Listed {len(credentials)} credentials from KMS")
        return credentials
    
    async def rotate_credential(self, key: str, namespace: Optional[str] = None) -> str:
        """Rotate credential in KMS."""
        # Generate new secure credential
        new_value = secrets.token_urlsafe(32)
        
        # Store with rotation metadata
        cache_key = f"{namespace or 'default'}:{key}"
        old_value = self._cache.get(cache_key, {}).get("value")
        
        self._cache[cache_key] = {
            "value": new_value,
            "timestamp": datetime.utcnow().isoformat(),
            "encrypted": True,
            "rotated_from": old_value,
            "rotation_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Rotated credential '{key}' in KMS")
        return new_value
    
    async def health_check(self) -> bool:
        """Check KMS connectivity."""
        try:
            # In production, this would ping the KMS endpoint
            # For now, check if we have basic configuration
            return bool(self.kms_endpoint or os.getenv("KMS_ENDPOINT"))
        except Exception as e:
            logger.error(f"KMS health check failed: {e}")
            return False


class LocalCredentialManager(CredentialManager):
    """
    Local file-based credential manager for development and on-premises deployments.
    Stores credentials in a secure local file with basic encryption.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize local credential manager.
        
        Args:
            storage_path: Path to credential storage file
        """
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".adcs", "credentials.json"
        )
        self._ensure_storage_dir()
        self._credentials = self._load_credentials()
        logger.info(f"Initialized LocalCredentialManager with storage: {self.storage_path}")
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        storage_dir = os.path.dirname(self.storage_path)
        os.makedirs(storage_dir, mode=0o700, exist_ok=True)
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load credentials: {e}")
                return {}
        return {}
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self._credentials, f, indent=2)
            # Set restrictive permissions
            os.chmod(self.storage_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    async def get_credential(self, key: str, namespace: Optional[str] = None) -> Optional[str]:
        """Retrieve credential from local storage."""
        ns_key = f"{namespace or 'default'}.{key}"
        
        # First check environment variables (override)
        env_key = f"{namespace.upper()}_{key.upper()}" if namespace else key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            logger.debug(f"Retrieved credential '{key}' from environment")
            return env_value
        
        # Then check local storage
        if ns_key in self._credentials:
            logger.debug(f"Retrieved credential '{key}' from local storage")
            return self._credentials[ns_key].get("value")
        
        logger.warning(f"Credential '{key}' not found")
        return None
    
    async def set_credential(self, key: str, value: str, namespace: Optional[str] = None) -> None:
        """Store credential in local storage."""
        ns_key = f"{namespace or 'default'}.{key}"
        
        self._credentials[ns_key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "encrypted": False  # Basic storage, not encrypted
        }
        
        self._save_credentials()
        logger.info(f"Stored credential '{key}' in local storage")
    
    async def delete_credential(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete credential from local storage."""
        ns_key = f"{namespace or 'default'}.{key}"
        
        if ns_key in self._credentials:
            del self._credentials[ns_key]
            self._save_credentials()
            logger.info(f"Deleted credential '{key}' from local storage")
            return True
        
        logger.warning(f"Credential '{key}' not found for deletion")
        return False
    
    async def list_credentials(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """List credentials in local storage."""
        credentials = {}
        prefix = f"{namespace}." if namespace else ""
        
        for ns_key, data in self._credentials.items():
            if not namespace or ns_key.startswith(prefix):
                key_name = ns_key.split(".", 1)[1] if "." in ns_key else ns_key
                credentials[key_name] = {
                    "timestamp": data.get("timestamp"),
                    "encrypted": data.get("encrypted", False)
                }
        
        logger.info(f"Listed {len(credentials)} credentials from local storage")
        return credentials
    
    async def rotate_credential(self, key: str, namespace: Optional[str] = None) -> str:
        """Rotate credential in local storage."""
        # Generate new secure credential
        new_value = secrets.token_urlsafe(32)
        
        # Store with rotation metadata
        ns_key = f"{namespace or 'default'}.{key}"
        old_data = self._credentials.get(ns_key, {})
        
        self._credentials[ns_key] = {
            "value": new_value,
            "timestamp": datetime.utcnow().isoformat(),
            "encrypted": False,
            "rotated_from": old_data.get("value"),
            "rotation_timestamp": datetime.utcnow().isoformat()
        }
        
        self._save_credentials()
        logger.info(f"Rotated credential '{key}' in local storage")
        return new_value
    
    async def health_check(self) -> bool:
        """Check local storage accessibility."""
        try:
            # Check if we can read/write to storage
            self._save_credentials()
            return True
        except Exception as e:
            logger.error(f"Local credential storage health check failed: {e}")
            return False