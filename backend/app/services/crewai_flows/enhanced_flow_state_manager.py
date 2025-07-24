#!/usr/bin/env python3
"""
Enhanced Flow State Manager for Master Flow Orchestrator
MFO-017, MFO-018, MFO-019: State persistence, serialization/deserialization, and encryption

This enhanced version adds:
- Advanced state serialization/deserialization (MFO-018)
- State encryption for sensitive fields (MFO-019)
- Enhanced state persistence with compression
- Multi-format serialization support
- Sensitive data protection
"""

import base64
import gzip
import json
import logging
import os
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.core.context import RequestContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.ext.asyncio import AsyncSession

from .flow_state_manager import FlowStateManager

logger = logging.getLogger(__name__)


@dataclass
class SerializationConfig:
    """Configuration for state serialization"""

    format: str = "json"  # json, pickle, msgpack
    compress: bool = True
    encrypt_sensitive: bool = True
    max_size_mb: int = 10
    include_metadata: bool = True


@dataclass
class EncryptionConfig:
    """Configuration for state encryption"""

    enabled: bool = True
    algorithm: str = "fernet"
    key_rotation_days: int = 90
    sensitive_fields: List[str] = None

    def __post_init__(self):
        if self.sensitive_fields is None:
            self.sensitive_fields = [
                "api_keys",
                "passwords",
                "tokens",
                "credentials",
                "personal_data",
                "sensitive_metadata",
                "user_data",
                "private_keys",
            ]


class StateSerializationError(Exception):
    """Raised when state serialization/deserialization fails"""

    pass


class StateEncryptionError(Exception):
    """Raised when state encryption/decryption fails"""

    pass


class StateEncryption:
    """Handles encryption/decryption of sensitive state data"""

    def __init__(self, config: EncryptionConfig):
        self.config = config
        self._cipher_suite = None
        self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption cipher"""
        if not self.config.enabled:
            return

        try:
            # Get or generate encryption key
            key = self._get_or_create_key()
            self._cipher_suite = Fernet(key)
            logger.info("✅ State encryption initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize state encryption: {e}")
            raise StateEncryptionError(f"Encryption initialization failed: {e}")

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        # In production, this should use a secure key management service
        key_env_var = "FLOW_STATE_ENCRYPTION_KEY"

        if key_env_var in os.environ:
            # Use provided key
            key_data = os.environ[key_env_var].encode()
        else:
            # Generate key from password
            password = os.getenv(
                "FLOW_STATE_PASSWORD", "default-password-change-me"
            ).encode()
            salt = b"flow_state_salt_2024"  # In production, use random salt per environment

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key_data = kdf.derive(password)

        return base64.urlsafe_b64encode(key_data)

    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in state data"""
        if not self.config.enabled or not self._cipher_suite:
            return data

        try:
            encrypted_data = data.copy()

            for field in self.config.sensitive_fields:
                if field in encrypted_data:
                    # Encrypt the sensitive field
                    field_data = json.dumps(encrypted_data[field])
                    encrypted_value = self._cipher_suite.encrypt(field_data.encode())
                    encrypted_data[field] = {
                        "__encrypted__": True,
                        "__algorithm__": self.config.algorithm,
                        "__data__": base64.b64encode(encrypted_value).decode(),
                        "__timestamp__": datetime.utcnow().isoformat(),
                    }

            return encrypted_data

        except Exception as e:
            logger.error(f"❌ Failed to encrypt sensitive data: {e}")
            raise StateEncryptionError(f"Encryption failed: {e}")

    def decrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in state data"""
        if not self.config.enabled or not self._cipher_suite:
            return data

        try:
            decrypted_data = data.copy()

            for field_name, field_value in decrypted_data.items():
                if isinstance(field_value, dict) and field_value.get("__encrypted__"):
                    # Decrypt the sensitive field
                    encrypted_data = base64.b64decode(field_value["__data__"])
                    decrypted_bytes = self._cipher_suite.decrypt(encrypted_data)
                    decrypted_data[field_name] = json.loads(decrypted_bytes.decode())

            return decrypted_data

        except Exception as e:
            logger.error(f"❌ Failed to decrypt sensitive data: {e}")
            raise StateEncryptionError(f"Decryption failed: {e}")


class StateSerializer:
    """Handles serialization/deserialization of flow state data"""

    def __init__(self, config: SerializationConfig):
        self.config = config
        self.encryption = StateEncryption(EncryptionConfig())

    def serialize_state(self, state: Dict[str, Any]) -> bytes:
        """Serialize state data to bytes"""
        try:
            # Encrypt sensitive data first
            if self.encryption.config.enabled:
                state = self.encryption.encrypt_sensitive_data(state)

            # Add metadata if configured
            if self.config.include_metadata:
                state = self._add_serialization_metadata(state)

            # Serialize based on format
            if self.config.format == "json":
                serialized = json.dumps(state, default=self._json_serializer).encode(
                    "utf-8"
                )
            elif self.config.format == "pickle":
                serialized = pickle.dumps(state)
            else:
                raise StateSerializationError(
                    f"Unsupported serialization format: {self.config.format}"
                )

            # Compress if configured
            if self.config.compress:
                serialized = gzip.compress(serialized)

            # Check size limit
            size_mb = len(serialized) / (1024 * 1024)
            if size_mb > self.config.max_size_mb:
                raise StateSerializationError(
                    f"Serialized state too large: {size_mb:.2f}MB > {self.config.max_size_mb}MB"
                )

            logger.debug(
                f"✅ State serialized: {len(serialized)} bytes ({self.config.format})"
            )
            return serialized

        except Exception as e:
            logger.error(f"❌ State serialization failed: {e}")
            raise StateSerializationError(f"Serialization failed: {e}")

    def deserialize_state(self, data: bytes) -> Dict[str, Any]:
        """Deserialize state data from bytes"""
        try:
            # Decompress if needed
            if self.config.compress:
                try:
                    data = gzip.decompress(data)
                except Exception:
                    # Data might not be compressed (backward compatibility)
                    pass

            # Deserialize based on format
            if self.config.format == "json":
                state = json.loads(data.decode("utf-8"))
            elif self.config.format == "pickle":
                state = pickle.loads(data)
            else:
                raise StateSerializationError(
                    f"Unsupported deserialization format: {self.config.format}"
                )

            # Decrypt sensitive data
            if self.encryption.config.enabled:
                state = self.encryption.decrypt_sensitive_data(state)

            # Remove metadata if present
            state = self._remove_serialization_metadata(state)

            logger.debug(f"✅ State deserialized: {self.config.format}")
            return state

        except Exception as e:
            logger.error(f"❌ State deserialization failed: {e}")
            raise StateSerializationError(f"Deserialization failed: {e}")

    def _add_serialization_metadata(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Add serialization metadata"""
        metadata = {
            "__serialization__": {
                "format": self.config.format,
                "compressed": self.config.compress,
                "encrypted": self.encryption.config.enabled,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
            }
        }

        return {**state, **metadata}

    def _remove_serialization_metadata(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Remove serialization metadata"""
        if "__serialization__" in state:
            state = state.copy()
            del state["__serialization__"]
        return state

    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)


class EnhancedFlowStateManager(FlowStateManager):
    """
    Enhanced Flow State Manager with serialization and encryption
    Extends the base FlowStateManager with:
    - Advanced serialization/deserialization (MFO-018)
    - State encryption for sensitive fields (MFO-019)
    - Enhanced persistence capabilities
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        serialization_config: Optional[SerializationConfig] = None,
        encryption_config: Optional[EncryptionConfig] = None,
    ):
        super().__init__(db, context)

        # Initialize serialization and encryption
        self.serialization_config = serialization_config or SerializationConfig()
        self.encryption_config = encryption_config or EncryptionConfig()
        self.serializer = StateSerializer(self.serialization_config)

        logger.info("✅ Enhanced Flow State Manager initialized")

    async def create_flow_state_enhanced(
        self,
        flow_id: str,
        initial_data: Dict[str, Any],
        serialization_format: str = "json",
    ) -> Dict[str, Any]:
        """Create flow state with enhanced serialization"""
        try:
            # Set serialization format
            self.serialization_config.format = serialization_format

            # Create base flow state
            result = await super().create_flow_state(flow_id, initial_data)

            # Serialize and store enhanced state
            enhanced_state = {
                **initial_data,
                "flow_metadata": {
                    "serialization_format": serialization_format,
                    "encryption_enabled": self.encryption_config.enabled,
                    "created_with_enhanced_manager": True,
                    "manager_version": "1.0",
                },
            }

            # Store serialized state
            serialized_data = self.serializer.serialize_state(enhanced_state)
            await self._store_serialized_state(flow_id, serialized_data)

            logger.info(f"✅ Enhanced flow state created: {flow_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Enhanced flow state creation failed: {e}")
            raise

    async def get_flow_state_enhanced(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state with automatic deserialization"""
        try:
            # Try to get enhanced serialized state first
            serialized_data = await self._load_serialized_state(flow_id)

            if serialized_data:
                # Deserialize enhanced state
                enhanced_state = self.serializer.deserialize_state(serialized_data)

                # Merge with base state
                base_state = await super().get_flow_state(flow_id)
                if base_state:
                    return {**base_state, **enhanced_state}
                else:
                    return enhanced_state
            else:
                # Fallback to base state manager
                return await super().get_flow_state(flow_id)

        except Exception as e:
            logger.error(f"❌ Enhanced flow state retrieval failed: {e}")
            # Fallback to base implementation
            return await super().get_flow_state(flow_id)

    async def update_flow_state_enhanced(
        self, flow_id: str, state_updates: Dict[str, Any], version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update flow state with enhanced serialization"""
        try:
            # Update base state
            result = await super().update_flow_state(flow_id, state_updates, version)

            # Get current enhanced state
            current_enhanced = await self._load_serialized_state(flow_id)

            if current_enhanced:
                # Deserialize, update, and re-serialize
                enhanced_state = self.serializer.deserialize_state(current_enhanced)
                enhanced_state.update(state_updates)
                enhanced_state["updated_at"] = datetime.utcnow().isoformat()

                # Re-serialize and store
                serialized_data = self.serializer.serialize_state(enhanced_state)
                await self._store_serialized_state(flow_id, serialized_data)

            return result

        except Exception as e:
            logger.error(f"❌ Enhanced flow state update failed: {e}")
            # Fallback to base implementation
            return await super().update_flow_state(flow_id, state_updates, version)

    async def export_flow_state(
        self, flow_id: str, export_format: str = "json", include_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Export flow state in specified format"""
        try:
            # Get enhanced state
            state = await self.get_flow_state_enhanced(flow_id)

            if not state:
                raise ValueError(f"Flow state not found: {flow_id}")

            # Configure export serialization
            export_config = SerializationConfig(
                format=export_format,
                compress=False,
                encrypt_sensitive=not include_sensitive,
                include_metadata=True,
            )

            export_serializer = StateSerializer(export_config)

            # Prepare export data
            export_data = {
                "flow_id": flow_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "export_format": export_format,
                "include_sensitive": include_sensitive,
                "state": state,
            }

            # Serialize for export
            serialized = export_serializer.serialize_state(export_data)

            return {
                "flow_id": flow_id,
                "format": export_format,
                "size_bytes": len(serialized),
                "data": (
                    base64.b64encode(serialized).decode()
                    if export_format != "json"
                    else export_data
                ),
                "exported_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Flow state export failed: {e}")
            raise StateSerializationError(f"Export failed: {e}")

    async def import_flow_state(
        self,
        flow_id: str,
        import_data: Union[str, bytes, Dict[str, Any]],
        import_format: str = "json",
    ) -> Dict[str, Any]:
        """Import flow state from external data"""
        try:
            # Configure import serialization
            import_config = SerializationConfig(
                format=import_format,
                compress=False,
                encrypt_sensitive=True,
                include_metadata=True,
            )

            import_serializer = StateSerializer(import_config)

            # Handle different input types
            if isinstance(import_data, str):
                if import_format == "json":
                    data = json.loads(import_data)
                else:
                    data = base64.b64decode(import_data)
            elif isinstance(import_data, bytes):
                data = import_data
            else:
                data = import_data

            # Deserialize imported data
            if isinstance(data, dict):
                imported_state = data.get("state", data)
            else:
                imported_export = import_serializer.deserialize_state(data)
                imported_state = imported_export.get("state", imported_export)

            # Create new flow state with imported data
            result = await self.create_flow_state_enhanced(
                flow_id, imported_state, import_format
            )

            return {
                "flow_id": flow_id,
                "import_format": import_format,
                "imported_at": datetime.utcnow().isoformat(),
                "result": result,
            }

        except Exception as e:
            logger.error(f"❌ Flow state import failed: {e}")
            raise StateSerializationError(f"Import failed: {e}")

    async def _store_serialized_state(
        self, flow_id: str, serialized_data: bytes
    ) -> None:
        """Store serialized state data"""
        try:
            # In production, this would store in a dedicated blob storage or database field
            # For now, we'll use the existing state store with base64 encoding
            encoded_data = base64.b64encode(serialized_data).decode()

            state_record = {
                "serialized_state": encoded_data,
                "serialization_format": self.serialization_config.format,
                "compressed": self.serialization_config.compress,
                "encrypted": self.encryption_config.enabled,
                "stored_at": datetime.utcnow().isoformat(),
            }

            await self.store.save_state(
                flow_id=flow_id, state=state_record, phase="serialized_storage"
            )

        except Exception as e:
            logger.error(f"❌ Failed to store serialized state: {e}")
            raise

    async def _load_serialized_state(self, flow_id: str) -> Optional[bytes]:
        """Load serialized state data"""
        try:
            # Load from state store
            state_record = await self.store.load_state(flow_id)

            if state_record and "serialized_state" in state_record:
                encoded_data = state_record["serialized_state"]
                return base64.b64decode(encoded_data)

            return None

        except Exception as e:
            logger.error(f"❌ Failed to load serialized state: {e}")
            return None

    async def get_state_analytics(self, flow_id: str) -> Dict[str, Any]:
        """Get analytics about state storage and performance"""
        try:
            # Get base state
            base_state = await super().get_flow_state(flow_id)

            # Get serialized state
            serialized_data = await self._load_serialized_state(flow_id)

            analytics = {
                "flow_id": flow_id,
                "base_state_exists": base_state is not None,
                "serialized_state_exists": serialized_data is not None,
                "serialization_config": asdict(self.serialization_config),
                "encryption_config": {
                    "enabled": self.encryption_config.enabled,
                    "algorithm": self.encryption_config.algorithm,
                    "sensitive_fields_count": len(
                        self.encryption_config.sensitive_fields
                    ),
                },
            }

            if base_state:
                analytics["base_state_size"] = len(json.dumps(base_state))
                analytics["base_state_fields"] = list(base_state.keys())

            if serialized_data:
                analytics["serialized_size_bytes"] = len(serialized_data)
                analytics["compression_ratio"] = None

                # Calculate compression ratio
                if self.serialization_config.compress:
                    uncompressed = gzip.decompress(serialized_data)
                    analytics["uncompressed_size_bytes"] = len(uncompressed)
                    analytics["compression_ratio"] = len(serialized_data) / len(
                        uncompressed
                    )

            analytics["generated_at"] = datetime.utcnow().isoformat()
            return analytics

        except Exception as e:
            logger.error(f"❌ Failed to get state analytics: {e}")
            return {"error": str(e), "flow_id": flow_id}


# Factory function for creating enhanced flow state managers
async def create_enhanced_flow_manager(
    context: RequestContext,
    serialization_format: str = "json",
    enable_encryption: bool = True,
    enable_compression: bool = True,
) -> EnhancedFlowStateManager:
    """Create an enhanced flow state manager"""
    from app.core.database import AsyncSessionLocal

    serialization_config = SerializationConfig(
        format=serialization_format,
        compress=enable_compression,
        encrypt_sensitive=enable_encryption,
    )

    encryption_config = EncryptionConfig(enabled=enable_encryption)

    async with AsyncSessionLocal() as db:
        return EnhancedFlowStateManager(
            db=db,
            context=context,
            serialization_config=serialization_config,
            encryption_config=encryption_config,
        )
