"""
Storage Manager Compression Module

Provides compression and decompression utilities for storage operations.
This module can be extended to support various compression algorithms
for optimizing storage space and network transfer.
"""

import gzip
import json
import pickle
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict

from .exceptions import StorageSerializationError


class CompressionType(str, Enum):
    """Supported compression types"""

    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"
    LZ4 = "lz4"  # Future implementation
    BROTLI = "brotli"  # Future implementation


class SerializationFormat(str, Enum):
    """Supported serialization formats"""

    JSON = "json"
    PICKLE = "pickle"
    RAW = "raw"  # No serialization, pass-through


class BaseCompressor(ABC):
    """Abstract base class for compression implementations"""

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compress data"""
        pass

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        pass

    @property
    @abstractmethod
    def compression_type(self) -> CompressionType:
        """Get compression type identifier"""
        pass


class NoCompression(BaseCompressor):
    """No-op compressor for when compression is disabled"""

    def compress(self, data: bytes) -> bytes:
        return data

    def decompress(self, data: bytes) -> bytes:
        return data

    @property
    def compression_type(self) -> CompressionType:
        return CompressionType.NONE


class GzipCompressor(BaseCompressor):
    """GZIP compression implementation"""

    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level

    def compress(self, data: bytes) -> bytes:
        try:
            return gzip.compress(data, compresslevel=self.compression_level)
        except Exception as e:
            raise StorageSerializationError(
                f"GZIP compression failed: {e}", serialization_format="gzip"
            )

    def decompress(self, data: bytes) -> bytes:
        try:
            return gzip.decompress(data)
        except Exception as e:
            raise StorageSerializationError(
                f"GZIP decompression failed: {e}", serialization_format="gzip"
            )

    @property
    def compression_type(self) -> CompressionType:
        return CompressionType.GZIP


class ZlibCompressor(BaseCompressor):
    """ZLIB compression implementation"""

    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level

    def compress(self, data: bytes) -> bytes:
        try:
            return zlib.compress(data, level=self.compression_level)
        except Exception as e:
            raise StorageSerializationError(
                f"ZLIB compression failed: {e}", serialization_format="zlib"
            )

    def decompress(self, data: bytes) -> bytes:
        try:
            return zlib.decompress(data)
        except Exception as e:
            raise StorageSerializationError(
                f"ZLIB decompression failed: {e}", serialization_format="zlib"
            )

    @property
    def compression_type(self) -> CompressionType:
        return CompressionType.ZLIB


class CompressionManager:
    """
    Manages compression and serialization for storage operations.

    This class handles the combination of serialization (converting Python objects
    to bytes) and compression (reducing byte size) for storage efficiency.
    """

    def __init__(
        self,
        compression_type: CompressionType = CompressionType.NONE,
        serialization_format: SerializationFormat = SerializationFormat.JSON,
        compression_threshold: int = 1024,  # Only compress if data > 1KB
        compression_level: int = 6,
    ):
        self.compression_type = compression_type
        self.serialization_format = serialization_format
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level

        # Initialize compressor
        self._compressor = self._create_compressor()

    def _create_compressor(self) -> BaseCompressor:
        """Create appropriate compressor based on configuration"""
        if self.compression_type == CompressionType.NONE:
            return NoCompression()
        elif self.compression_type == CompressionType.GZIP:
            return GzipCompressor(self.compression_level)
        elif self.compression_type == CompressionType.ZLIB:
            return ZlibCompressor(self.compression_level)
        else:
            # Future compression types can be added here
            raise StorageSerializationError(
                f"Unsupported compression type: {self.compression_type}",
                serialization_format=str(self.compression_type),
            )

    def serialize_and_compress(self, value: Any) -> tuple[bytes, Dict[str, Any]]:
        """
        Serialize and optionally compress a value for storage.

        Args:
            value: The value to serialize and compress

        Returns:
            Tuple of (compressed_data, metadata)
        """
        # Step 1: Serialize to bytes
        serialized_data = self._serialize(value)

        # Step 2: Compress if beneficial
        should_compress = (
            len(serialized_data) >= self.compression_threshold
            and self.compression_type != CompressionType.NONE
        )

        if should_compress:
            compressed_data = self._compressor.compress(serialized_data)

            # Only use compressed version if it's actually smaller
            if len(compressed_data) < len(serialized_data):
                final_data = compressed_data
                is_compressed = True
            else:
                final_data = serialized_data
                is_compressed = False
        else:
            final_data = serialized_data
            is_compressed = False

        # Create metadata
        metadata = {
            "serialization_format": self.serialization_format.value,
            "compression_type": (
                self.compression_type.value
                if is_compressed
                else CompressionType.NONE.value
            ),
            "is_compressed": is_compressed,
            "original_size": len(serialized_data),
            "final_size": len(final_data),
            "compression_ratio": (
                len(final_data) / len(serialized_data) if serialized_data else 1.0
            ),
        }

        return final_data, metadata

    def decompress_and_deserialize(self, data: bytes, metadata: Dict[str, Any]) -> Any:
        """
        Decompress and deserialize data from storage.

        Args:
            data: The compressed/serialized data
            metadata: Metadata about the data format

        Returns:
            The original Python object
        """
        # Step 1: Decompress if needed
        if metadata.get("is_compressed", False):
            compression_type = CompressionType(
                metadata.get("compression_type", CompressionType.NONE.value)
            )

            if compression_type != CompressionType.NONE:
                # Create appropriate decompressor
                if compression_type == CompressionType.GZIP:
                    decompressor = GzipCompressor()
                elif compression_type == CompressionType.ZLIB:
                    decompressor = ZlibCompressor()
                else:
                    raise StorageSerializationError(
                        f"Unsupported compression type for decompression: {compression_type}",
                        serialization_format=str(compression_type),
                    )

                serialized_data = decompressor.decompress(data)
            else:
                serialized_data = data
        else:
            serialized_data = data

        # Step 2: Deserialize
        serialization_format = SerializationFormat(
            metadata.get("serialization_format", SerializationFormat.JSON.value)
        )

        return self._deserialize(serialized_data, serialization_format)

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes based on configured format"""
        try:
            if self.serialization_format == SerializationFormat.JSON:
                return json.dumps(value, default=str).encode("utf-8")
            elif self.serialization_format == SerializationFormat.PICKLE:
                return pickle.dumps(value)
            elif self.serialization_format == SerializationFormat.RAW:
                if isinstance(value, bytes):
                    return value
                elif isinstance(value, str):
                    return value.encode("utf-8")
                else:
                    # Fallback to JSON for non-string/bytes types
                    return json.dumps(value, default=str).encode("utf-8")
            else:
                raise StorageSerializationError(
                    f"Unsupported serialization format: {self.serialization_format}",
                    serialization_format=str(self.serialization_format),
                )
        except Exception as e:
            if isinstance(e, StorageSerializationError):
                raise
            raise StorageSerializationError(
                f"Serialization failed: {e}",
                data_type=type(value).__name__,
                serialization_format=str(self.serialization_format),
            )

    def _deserialize(
        self, data: bytes, serialization_format: SerializationFormat
    ) -> Any:
        """Deserialize bytes to Python object"""
        try:
            if serialization_format == SerializationFormat.JSON:
                return json.loads(data.decode("utf-8"))
            elif serialization_format == SerializationFormat.PICKLE:
                return pickle.loads(data)
            elif serialization_format == SerializationFormat.RAW:
                return data  # Return as bytes
            else:
                raise StorageSerializationError(
                    f"Unsupported serialization format for deserialization: {serialization_format}",
                    serialization_format=str(serialization_format),
                )
        except Exception as e:
            if isinstance(e, StorageSerializationError):
                raise
            raise StorageSerializationError(
                f"Deserialization failed: {e}",
                serialization_format=str(serialization_format),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get compression manager statistics"""
        return {
            "compression_type": self.compression_type.value,
            "serialization_format": self.serialization_format.value,
            "compression_threshold": self.compression_threshold,
            "compression_level": self.compression_level,
        }


# Default compression manager instance
default_compression_manager = CompressionManager()


def compress_value(
    value: Any, compression_type: CompressionType = CompressionType.NONE
) -> tuple[bytes, Dict[str, Any]]:
    """
    Convenience function to compress a value with default settings.

    Args:
        value: Value to compress
        compression_type: Type of compression to use

    Returns:
        Tuple of (compressed_data, metadata)
    """
    manager = CompressionManager(compression_type=compression_type)
    return manager.serialize_and_compress(value)


def decompress_value(data: bytes, metadata: Dict[str, Any]) -> Any:
    """
    Convenience function to decompress a value.

    Args:
        data: Compressed data
        metadata: Compression metadata

    Returns:
        Original value
    """
    return default_compression_manager.decompress_and_deserialize(data, metadata)
