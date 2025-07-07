#!/usr/bin/env python3
"""
Run integration tests that simulate real browser interactions
This ensures we catch runtime errors before deployment
"""

import sys
import pytest
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def run_integration_tests():
    """Run integration and e2e tests with detailed output"""
    print("🧪 Running Integration Tests...")
    print("=" * 80)
    
    test_files = [
        "tests/api/test_flows_endpoint_integration.py",
        "tests/e2e/test_data_import_page_load.py"
    ]
    
    # Run with verbose output and stop on first failure
    args = [
        "-v",  # Verbose
        "-s",  # No capture, show print statements
        "-x",  # Stop on first failure
        "--tb=short",  # Short traceback format
        "--asyncio-mode=auto",  # Handle async tests
        *test_files
    ]
    
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All integration tests passed!")
    else:
        print("\n❌ Integration tests failed!")
        print("These tests simulate real page loads and API interactions.")
        print("Fix these issues before marking tests as passing.")
    
    return exit_code


def run_specific_scenario(scenario: str):
    """Run a specific test scenario"""
    scenarios = {
        "page_load": "tests/e2e/test_data_import_page_load.py::TestDataImportPageLoad::test_data_import_page_load_sequence",
        "empty_flows": "tests/api/test_flows_endpoint_integration.py::TestFlowsEndpointIntegration::test_list_flows_empty_database",
        "with_flows": "tests/api/test_flows_endpoint_integration.py::TestFlowsEndpointIntegration::test_list_flows_with_existing_flows",
        "admin_demo": "tests/e2e/test_data_import_page_load.py::TestDataImportPageLoad::test_admin_user_with_demo_context"
    }
    
    if scenario not in scenarios:
        print(f"Unknown scenario: {scenario}")
        print(f"Available scenarios: {', '.join(scenarios.keys())}")
        return 1
    
    print(f"🧪 Running scenario: {scenario}")
    args = ["-v", "-s", "-x", "--tb=short", "--asyncio-mode=auto", scenarios[scenario]]
    return pytest.main(args)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific scenario
        exit_code = run_specific_scenario(sys.argv[1])
    else:
        # Run all integration tests
        exit_code = run_integration_tests()
    
    sys.exit(exit_code)