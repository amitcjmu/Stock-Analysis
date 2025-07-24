"""
Encryption Utilities for Secure Credential Storage
Provides encryption/decryption functions using industry-standard algorithms
"""

import base64
import json
import logging
import os
import secrets
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""

    pass


class EncryptionManager:
    """
    Manages encryption/decryption operations for sensitive data
    Supports multiple encryption methods and key derivation
    """

    def __init__(self):
        self._master_key = self._get_or_generate_master_key()
        self._fernet = None

    def _get_or_generate_master_key(self) -> bytes:
        """
        Get master key from environment or generate one
        In production, this should come from a secure key management service
        """
        # Try to get from environment
        key_str = os.getenv("ENCRYPTION_MASTER_KEY")

        if key_str:
            try:
                return base64.urlsafe_b64decode(key_str)
            except Exception as e:
                logger.error(f"Invalid ENCRYPTION_MASTER_KEY format: {e}")
                raise EncryptionError("Invalid master key format")

        # For development only - generate a key
        if settings.ENVIRONMENT == "development":
            logger.warning("Generating temporary encryption key for development")
            key = Fernet.generate_key()
            logger.warning(f"Set ENCRYPTION_MASTER_KEY={key.decode()} in environment")
            return key

        raise EncryptionError("ENCRYPTION_MASTER_KEY not set in production environment")

    @property
    def fernet(self) -> Fernet:
        """Get or create Fernet instance"""
        if not self._fernet:
            self._fernet = Fernet(self._master_key)
        return self._fernet

    def derive_key(self, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive a key from the master key using PBKDF2

        Args:
            salt: Random salt for key derivation
            iterations: Number of iterations for PBKDF2

        Returns:
            Derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        return base64.urlsafe_b64encode(kdf.derive(self._master_key))

    def encrypt_with_fernet(self, plaintext: str) -> Tuple[str, Dict[str, Any]]:
        """
        Encrypt data using Fernet (symmetric encryption)

        Args:
            plaintext: Data to encrypt

        Returns:
            Tuple of (encrypted_data, metadata)
        """
        try:
            # Convert to bytes if string
            if isinstance(plaintext, str):
                plaintext_bytes = plaintext.encode("utf-8")
            else:
                plaintext_bytes = plaintext

            # Encrypt
            encrypted = self.fernet.encrypt(plaintext_bytes)

            # Return base64 encoded ciphertext and metadata
            return base64.urlsafe_b64encode(encrypted).decode("utf-8"), {
                "algorithm": "fernet",
                "version": "1.0",
            }
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")

    def decrypt_with_fernet(self, ciphertext: str) -> str:
        """
        Decrypt data encrypted with Fernet

        Args:
            ciphertext: Base64 encoded encrypted data

        Returns:
            Decrypted plaintext
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext)

            # Decrypt
            decrypted = self.fernet.decrypt(encrypted_bytes)

            # Return as string
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")

    def encrypt_with_aes_gcm(
        self, plaintext: str, associated_data: Optional[bytes] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Encrypt data using AES-GCM (authenticated encryption)

        Args:
            plaintext: Data to encrypt
            associated_data: Additional data to authenticate but not encrypt

        Returns:
            Tuple of (encrypted_data, metadata)
        """
        try:
            # Generate random salt and derive key
            salt = os.urandom(16)
            key = self.derive_key(salt)[:32]  # Use 256-bit key

            # Generate random nonce
            nonce = os.urandom(12)  # 96-bit nonce for GCM

            # Create cipher
            aesgcm = AESGCM(key)

            # Convert plaintext to bytes
            plaintext_bytes = (
                plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext
            )

            # Encrypt
            ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, associated_data)

            # Combine salt, nonce, and ciphertext
            combined = salt + nonce + ciphertext

            # Return base64 encoded result and metadata
            return base64.urlsafe_b64encode(combined).decode("utf-8"), {
                "algorithm": "aes-gcm",
                "version": "1.0",
                "salt_length": 16,
                "nonce_length": 12,
                "has_associated_data": associated_data is not None,
            }
        except Exception as e:
            logger.error(f"AES-GCM encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data with AES-GCM: {str(e)}")

    def decrypt_with_aes_gcm(
        self,
        ciphertext: str,
        metadata: Dict[str, Any],
        associated_data: Optional[bytes] = None,
    ) -> str:
        """
        Decrypt data encrypted with AES-GCM

        Args:
            ciphertext: Base64 encoded encrypted data
            metadata: Encryption metadata
            associated_data: Additional authenticated data

        Returns:
            Decrypted plaintext
        """
        try:
            # Decode from base64
            combined = base64.urlsafe_b64decode(ciphertext)

            # Extract components
            salt_length = metadata.get("salt_length", 16)
            nonce_length = metadata.get("nonce_length", 12)

            salt = combined[:salt_length]
            nonce = combined[salt_length : salt_length + nonce_length]
            ciphertext_bytes = combined[salt_length + nonce_length :]

            # Derive key
            key = self.derive_key(salt)[:32]

            # Create cipher and decrypt
            aesgcm = AESGCM(key)
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_bytes, associated_data)

            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"AES-GCM decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data with AES-GCM: {str(e)}")

    def encrypt_credential(
        self, credential_data: Dict[str, Any], credential_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Encrypt credential data with appropriate algorithm based on type

        Args:
            credential_data: Credential data to encrypt
            credential_type: Type of credential

        Returns:
            Tuple of (encrypted_data, metadata)
        """
        # Convert credential data to JSON string
        plaintext = json.dumps(credential_data)

        # Choose encryption method based on credential type
        if credential_type in ["api_key", "basic_auth"]:
            # Use Fernet for simple credentials
            return self.encrypt_with_fernet(plaintext)
        else:
            # Use AES-GCM for more complex credentials
            # Use credential type as associated data for authentication
            associated_data = credential_type.encode("utf-8")
            return self.encrypt_with_aes_gcm(plaintext, associated_data)

    def decrypt_credential(
        self, encrypted_data: str, metadata: Dict[str, Any], credential_type: str
    ) -> Dict[str, Any]:
        """
        Decrypt credential data

        Args:
            encrypted_data: Encrypted credential data
            metadata: Encryption metadata
            credential_type: Type of credential

        Returns:
            Decrypted credential data
        """
        algorithm = metadata.get("algorithm", "fernet")

        if algorithm == "fernet":
            plaintext = self.decrypt_with_fernet(encrypted_data)
        elif algorithm == "aes-gcm":
            associated_data = credential_type.encode("utf-8")
            plaintext = self.decrypt_with_aes_gcm(
                encrypted_data, metadata, associated_data
            )
        else:
            raise EncryptionError(f"Unknown encryption algorithm: {algorithm}")

        return json.loads(plaintext)

    def generate_data_key(self) -> Tuple[str, str]:
        """
        Generate a data encryption key for envelope encryption

        Returns:
            Tuple of (encrypted_key, plaintext_key)
        """
        # Generate random data key
        data_key = Fernet.generate_key()

        # Encrypt the data key with master key
        encrypted_key, _ = self.encrypt_with_fernet(data_key.decode("utf-8"))

        return encrypted_key, data_key.decode("utf-8")

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt

        Args:
            password: Password to hash

        Returns:
            Hashed password
        """
        import bcrypt

        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against a hash

        Args:
            password: Password to verify
            hashed: Hashed password

        Returns:
            True if password matches
        """
        import bcrypt

        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# Global encryption manager instance
encryption_manager = EncryptionManager()


# Convenience functions
def encrypt_credential(
    credential_data: Dict[str, Any], credential_type: str
) -> Tuple[str, Dict[str, Any]]:
    """Encrypt credential data"""
    return encryption_manager.encrypt_credential(credential_data, credential_type)


def decrypt_credential(
    encrypted_data: str, metadata: Dict[str, Any], credential_type: str
) -> Dict[str, Any]:
    """Decrypt credential data"""
    return encryption_manager.decrypt_credential(
        encrypted_data, metadata, credential_type
    )


def hash_password(password: str) -> str:
    """Hash a password"""
    return encryption_manager.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password"""
    return encryption_manager.verify_password(password, hashed)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)
