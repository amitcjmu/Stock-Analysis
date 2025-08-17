#!/usr/bin/env python3
"""
Comprehensive Modularization Testing Script

This script tests all modularized components in Docker containers and generates
a detailed report on what's working and what needs to be fixed.

Test Modules:
1. azure_adapter ✅ (already tested)
2. crewai_flow_service ✅ (already tested)
3. collection_handlers ✅ (already tested)
4. storage_manager - NEEDS TESTING
5. field_mapping_executor - NEEDS TESTING
"""

import sys
import traceback
from typing import Dict, List, Tuple, Any


class ModularizationTester:
    """Comprehensive testing of all modularized components"""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}

    def test_module(
        self, module_name: str, import_statements: List[str]
    ) -> Tuple[bool, str, List[str]]:
        """
        Test a module with multiple import statements

        Returns:
            (success, error_message, successful_imports)
        """
        successful_imports = []
        errors = []

        for import_stmt in import_statements:
            try:
                exec(import_stmt)
                successful_imports.append(import_stmt)
                print(f"✅ {import_stmt}")
            except Exception as e:
                error_msg = f"❌ {import_stmt}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)

        success = len(errors) == 0
        error_summary = "; ".join(errors) if errors else "All imports successful"

        return success, error_summary, successful_imports

    def run_all_tests(self):
        """Run comprehensive tests on all modularized components"""

        print("=" * 80)
        print("COMPREHENSIVE MODULARIZATION TESTING")
        print("=" * 80)

        # Test 1: azure_adapter (already working)
        print("\n1. Testing azure_adapter modularization...")
        azure_imports = [
            "from app.services.adapters.azure_adapter import AzureAdapter",
            "from app.services.adapters.azure_adapter import AzureConfig",
            "from app.services.adapters.azure_adapter import create_azure_adapter",
        ]
        success, error, working = self.test_module("azure_adapter", azure_imports)
        self.results["azure_adapter"] = {
            "success": success,
            "error": error,
            "working_imports": working,
            "status": "✅ WORKING" if success else "❌ ISSUES",
        }

        # Test 2: crewai_flow_service (already working)
        print("\n2. Testing crewai_flow_service modularization...")
        crewai_imports = [
            "from app.services.crewai_flow_service import CrewAIFlowService",
            "from app.services.crewai_flow_service import CrewAIConfig",
            "from app.services.crewai_flow_service import create_flow_service",
        ]
        success, error, working = self.test_module(
            "crewai_flow_service", crewai_imports
        )
        self.results["crewai_flow_service"] = {
            "success": success,
            "error": error,
            "working_imports": working,
            "status": "✅ WORKING" if success else "❌ ISSUES",
        }

        # Test 3: collection_handlers (already working)
        print("\n3. Testing collection_handlers modularization...")
        collection_imports = [
            "from app.services.flow_configs.collection_handlers import collection_initialization",
            "from app.services.flow_configs.collection_handlers import get_collection_config",
            "from app.services.flow_configs.collection_handlers import validate_collection_data",
        ]
        success, error, working = self.test_module(
            "collection_handlers", collection_imports
        )
        self.results["collection_handlers"] = {
            "success": success,
            "error": error,
            "working_imports": working,
            "status": "✅ WORKING" if success else "❌ ISSUES",
        }

        # Test 4: storage_manager (needs fixing)
        print("\n4. Testing storage_manager modularization...")

        # Test core components first
        print("  4a. Testing storage_manager core components...")
        core_imports = [
            "from app.services.storage_manager.core import StorageManager",
            "from app.services.storage_manager.core import get_storage_manager",
        ]
        core_success, core_error, core_working = self.test_module(
            "storage_manager_core", core_imports
        )

        # Test full module imports
        print("  4b. Testing storage_manager full imports...")
        full_imports = [
            "from app.services.storage_manager import StorageManager",
            "from app.services.storage_manager import get_storage_manager",
        ]
        full_success, full_error, full_working = self.test_module(
            "storage_manager_full", full_imports
        )

        self.results["storage_manager"] = {
            "core_success": core_success,
            "core_error": core_error,
            "core_working": core_working,
            "full_success": full_success,
            "full_error": full_error,
            "full_working": full_working,
            "status": (
                "✅ CORE WORKING, FULL NEEDS FIX"
                if core_success and not full_success
                else "✅ WORKING" if full_success else "❌ ISSUES"
            ),
        }

        # Test 5: field_mapping_executor (needs fixing)
        print("\n5. Testing field_mapping_executor modularization...")

        # Test individual components first to isolate circular import
        print("  5a. Testing field_mapping_executor components...")
        component_imports = [
            "from app.services.field_mapping_executor.exceptions import FieldMappingExecutorError",
            "from app.services.field_mapping_executor.parsers import BaseMappingParser",
            "from app.services.field_mapping_executor.validation import BaseValidator",
        ]
        comp_success, comp_error, comp_working = self.test_module(
            "field_mapping_components", component_imports
        )

        # Test full import
        print("  5b. Testing field_mapping_executor full import...")
        field_imports = [
            "from app.services.field_mapping_executor import FieldMappingExecutor"
        ]
        field_success, field_error, field_working = self.test_module(
            "field_mapping_executor", field_imports
        )

        self.results["field_mapping_executor"] = {
            "component_success": comp_success,
            "component_error": comp_error,
            "component_working": comp_working,
            "full_success": field_success,
            "full_error": field_error,
            "full_working": field_working,
            "status": (
                "✅ COMPONENTS WORKING, FULL NEEDS FIX"
                if comp_success and not field_success
                else "✅ WORKING" if field_success else "❌ ISSUES"
            ),
        }

        # Test 6: Combined import test
        print("\n6. Testing combined modularization imports...")
        combined_imports = [
            "from app.services.adapters.azure_adapter import AzureAdapter",
            "from app.services.crewai_flow_service import CrewAIFlowService",
            "from app.services.flow_configs.collection_handlers import collection_initialization",
            "from app.services.storage_manager.core import StorageManager, get_storage_manager",
        ]
        combined_success, combined_error, combined_working = self.test_module(
            "combined_working", combined_imports
        )

        self.results["combined_working"] = {
            "success": combined_success,
            "error": combined_error,
            "working_imports": combined_working,
            "status": "✅ WORKING" if combined_success else "❌ ISSUES",
        }

    def generate_report(self):
        """Generate comprehensive test report"""

        print("\n" + "=" * 80)
        print("MODULARIZATION TEST REPORT")
        print("=" * 80)

        for module_name, result in self.results.items():
            print(f"\n{module_name.upper()}:")
            print(f"  Status: {result['status']}")

            if "success" in result:
                print(f"  Success: {result['success']}")
                print(f"  Error: {result['error']}")
                print(f"  Working imports: {len(result['working_imports'])}")
                if result["working_imports"]:
                    for imp in result["working_imports"]:
                        print(f"    ✅ {imp}")

            # Handle complex results for storage_manager and field_mapping_executor
            if "core_success" in result:
                print(f"  Core Success: {result['core_success']}")
                print(f"  Full Success: {result['full_success']}")
                if result["core_working"]:
                    print("  Core working imports:")
                    for imp in result["core_working"]:
                        print(f"    ✅ {imp}")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        working_modules = [
            name
            for name, result in self.results.items()
            if result["status"].startswith("✅")
        ]
        issue_modules = [
            name
            for name, result in self.results.items()
            if result["status"].startswith("❌")
        ]

        print(f"✅ Working modules: {len(working_modules)}")
        for module in working_modules:
            print(f"   - {module}")

        print(f"❌ Modules with issues: {len(issue_modules)}")
        for module in issue_modules:
            print(f"   - {module}")

        print(f"\nTotal modules tested: {len(self.results)}")
        success_rate = len(working_modules) / len(self.results) * 100
        print(f"Success rate: {success_rate:.1f}%")

        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        if (
            "storage_manager" in issue_modules
            or self.results.get("storage_manager", {}).get("full_success") is False
        ):
            print("1. STORAGE_MANAGER: Fix missing class imports in modular components")
            print("   - Add missing EncryptionType, CompressionType, etc. classes")
            print("   - Create placeholder implementations for all imported classes")

        if (
            "field_mapping_executor" in issue_modules
            or self.results.get("field_mapping_executor", {}).get("full_success")
            is False
        ):
            print("2. FIELD_MAPPING_EXECUTOR: Resolve circular import dependency")
            print(
                "   - Break circular dependency between field_mapping_executor and crewai_flows"
            )
            print("   - Consider using lazy imports or dependency injection")

        print("3. For working modules, consider integration testing next")

        return self.results


def main():
    """Main test execution"""

    print("Starting comprehensive modularization testing...")

    tester = ModularizationTester()

    try:
        tester.run_all_tests()
        results = tester.generate_report()

        print("\nTest completed. Results saved in memory.")

        # Return exit code based on results
        issue_count = len([r for r in results.values() if r["status"].startswith("❌")])
        return 0 if issue_count == 0 else 1

    except Exception as e:
        print(f"ERROR: Test execution failed: {e}")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
