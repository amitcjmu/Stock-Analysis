"""
Credential Manager interface for abstracting credential storage and retrieval.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CredentialManager(ABC):
    """
    Abstract interface for credential management.
    Supports both cloud-based (KMS) and local credential storage.
    """

    @abstractmethod
    async def get_credential(
        self, key: str, namespace: Optional[str] = None
    ) -> Optional[str]:
        """
        Retrieve a credential by key.

        Args:
            key: The credential identifier
            namespace: Optional namespace for credential organization

        Returns:
            The credential value or None if not found
        """
        pass

    @abstractmethod
    async def set_credential(
        self, key: str, value: str, namespace: Optional[str] = None
    ) -> None:
        """
        Store a credential.

        Args:
            key: The credential identifier
            value: The credential value
            namespace: Optional namespace for credential organization
        """
        pass

    @abstractmethod
    async def delete_credential(
        self, key: str, namespace: Optional[str] = None
    ) -> bool:
        """
        Delete a credential.

        Args:
            key: The credential identifier
            namespace: Optional namespace for credential organization

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_credentials(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        List available credentials.

        Args:
            namespace: Optional namespace filter

        Returns:
            Dictionary of credential metadata (without values)
        """
        pass

    @abstractmethod
    async def rotate_credential(self, key: str, namespace: Optional[str] = None) -> str:
        """
        Rotate a credential (generate new value).

        Args:
            key: The credential identifier
            namespace: Optional namespace for credential organization

        Returns:
            The new credential value
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the credential manager is operational.

        Returns:
            True if healthy, False otherwise
        """
        pass
