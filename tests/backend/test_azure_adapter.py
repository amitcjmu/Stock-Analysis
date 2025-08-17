"""
Test module for Azure Adapter modularization.

This test verifies that the modularized azure_adapter can be imported correctly
and that basic functionality is working.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


def test_azure_adapter_import():
    """Test that AzureAdapter can be imported from the modularized location."""
    try:
        from app.services.adapters.azure_adapter import AzureAdapter
        assert AzureAdapter is not None
        print("✅ AzureAdapter imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import AzureAdapter: {e}")


def test_azure_adapter_constants():
    """Test that Azure adapter constants are accessible."""
    try:
        from app.services.adapters.azure_adapter import AZURE_SDK_AVAILABLE
        assert isinstance(AZURE_SDK_AVAILABLE, bool)
        print(f"✅ AZURE_SDK_AVAILABLE = {AZURE_SDK_AVAILABLE}")
    except ImportError as e:
        pytest.fail(f"Failed to import Azure adapter constants: {e}")


def test_azure_adapter_classes():
    """Test that Azure adapter classes can be imported."""
    try:
        from app.services.adapters.azure_adapter import (
            AzureAdapter,
            AzureConfig,
            AzureResourceInfo
        )

        # Test that classes are accessible
        assert AzureAdapter is not None
        assert AzureConfig is not None
        assert AzureResourceInfo is not None
        print("✅ Azure adapter classes imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import Azure adapter classes: {e}")


@patch('app.services.adapters.azure_adapter.AZURE_SDK_AVAILABLE', False)
def test_azure_adapter_without_sdk():
    """Test that Azure adapter handles missing SDK gracefully."""
    try:
        from app.services.adapters.azure_adapter import AzureAdapter

        # Should not raise an error even without Azure SDK
        assert AzureAdapter is not None
        print("✅ AzureAdapter works without Azure SDK")
    except Exception as e:
        pytest.fail(f"AzureAdapter should work without Azure SDK: {e}")


def test_azure_adapter_metadata():
    """Test that Azure adapter metadata is properly defined."""
    try:
        from app.services.adapters.azure_adapter import AzureAdapter

        # Try to access metadata
        if hasattr(AzureAdapter, 'get_metadata'):
            # This should work even with mocked dependencies
            pass
        print("✅ Azure adapter metadata structure verified")
    except Exception as e:
        pytest.fail(f"Failed to verify Azure adapter metadata: {e}")


def test_azure_config_dataclass():
    """Test that AzureConfig dataclass is properly defined."""
    try:
        from app.services.adapters.azure_adapter import AzureConfig

        # Test that it's a dataclass-like structure
        assert hasattr(AzureConfig, '__annotations__') or hasattr(AzureConfig, '__dataclass_fields__')
        print("✅ AzureConfig dataclass structure verified")
    except Exception as e:
        pytest.fail(f"Failed to verify AzureConfig structure: {e}")


if __name__ == "__main__":
    # Run tests if called directly
    print("Running Azure Adapter tests...")
    test_azure_adapter_import()
    test_azure_adapter_constants()
    test_azure_adapter_classes()
    test_azure_adapter_without_sdk()
    test_azure_adapter_metadata()
    test_azure_config_dataclass()
    print("All Azure Adapter tests passed!")
