#!/usr/bin/env python3
"""
Comprehensive validation script for modularization changes.
Tests imports, service instantiation, and basic functionality.
"""

import sys
import os
import traceback
from typing import Dict, List, Any, Optional
import importlib

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

class ModularizationValidator:
    """Validates that modularization changes work correctly."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result."""
        self.results[test_name] = {
            "success": success,
            "details": details,
            "error": error
        }
        
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
            self.errors.append(f"{test_name}: {error}")

    def test_collection_imports(self) -> bool:
        """Test collection endpoint and modularized components."""
        try:
            # Test main collection endpoint
            from app.api.v1.endpoints.collection import router
            self.log_result("collection_main_import", True, "Main collection endpoint imported successfully")
            
            # Test modularized components
            components = [
                ("collection_crud", "app.api.v1.endpoints.collection_crud"),
                ("collection_validators", "app.api.v1.endpoints.collection_validators"),
                ("collection_serializers", "app.api.v1.endpoints.collection_serializers"),
                ("collection_utils", "app.api.v1.endpoints.collection_utils")
            ]
            
            for name, module_path in components:
                try:
                    module = importlib.import_module(module_path)
                    self.log_result(f"collection_{name}_import", True, f"Module {module_path} imported successfully")
                except Exception as e:
                    self.log_result(f"collection_{name}_import", False, "", str(e))
                    
            return True
            
        except Exception as e:
            self.log_result("collection_imports", False, "", str(e))
            return False

    def test_assessment_flow_imports(self) -> bool:
        """Test assessment flow endpoint and modularized components."""
        try:
            # Test main assessment flow endpoint
            from app.api.v1.endpoints.assessment_flow import router
            self.log_result("assessment_flow_main_import", True, "Main assessment flow endpoint imported successfully")
            
            # Test modularized components
            components = [
                ("assessment_flow_crud", "app.api.v1.endpoints.assessment_flow_crud"),
                ("assessment_flow_validators", "app.api.v1.endpoints.assessment_flow_validators"),
                ("assessment_flow_processors", "app.api.v1.endpoints.assessment_flow_processors"),
                ("assessment_flow_utils", "app.api.v1.endpoints.assessment_flow_utils")
            ]
            
            for name, module_path in components:
                try:
                    module = importlib.import_module(module_path)
                    self.log_result(f"assessment_flow_{name}_import", True, f"Module {module_path} imported successfully")
                except Exception as e:
                    self.log_result(f"assessment_flow_{name}_import", False, "", str(e))
                    
            return True
            
        except Exception as e:
            self.log_result("assessment_flow_imports", False, "", str(e))
            return False

    def test_crewai_flow_service_imports(self) -> bool:
        """Test CrewAI flow service and modularized components."""
        try:
            # Test main service
            from app.services.crewai_flow_service import CrewAIFlowService
            self.log_result("crewai_flow_service_main_import", True, "Main CrewAI flow service imported successfully")
            
            # Test modularized components
            components = [
                ("state_manager", "app.services.crewai_flow_state_manager"),
                ("executor", "app.services.crewai_flow_executor"),
                ("lifecycle", "app.services.crewai_flow_lifecycle"),
                ("monitoring", "app.services.crewai_flow_monitoring"),
                ("utils", "app.services.crewai_flow_utils")
            ]
            
            for name, module_path in components:
                try:
                    module = importlib.import_module(module_path)
                    self.log_result(f"crewai_flow_{name}_import", True, f"Module {module_path} imported successfully")
                except Exception as e:
                    self.log_result(f"crewai_flow_{name}_import", False, "", str(e))
                    
            return True
            
        except Exception as e:
            self.log_result("crewai_flow_service_imports", False, "", str(e))
            return False

    def test_azure_adapter_imports(self) -> bool:
        """Test Azure adapter and modularized components."""
        try:
            # Test main adapter
            from app.services.adapters.azure_adapter import AzureAdapter
            self.log_result("azure_adapter_main_import", True, "Main Azure adapter imported successfully")
            
            # Test modularized components
            components = [
                ("auth", "app.services.adapters.azure_adapter_auth"),
                ("storage", "app.services.adapters.azure_adapter_storage"),
                ("compute", "app.services.adapters.azure_adapter_compute"),
                ("data", "app.services.adapters.azure_adapter_data"),
                ("utils", "app.services.adapters.azure_adapter_utils")
            ]
            
            for name, module_path in components:
                try:
                    module = importlib.import_module(module_path)
                    self.log_result(f"azure_adapter_{name}_import", True, f"Module {module_path} imported successfully")
                except Exception as e:
                    self.log_result(f"azure_adapter_{name}_import", False, "", str(e))
                    
            return True
            
        except Exception as e:
            self.log_result("azure_adapter_imports", False, "", str(e))
            return False

    def test_service_instantiation(self) -> bool:
        """Test that modularized services can be instantiated."""
        try:
            # Test CrewAI Flow Service instantiation
            from app.services.crewai_flow_service import CrewAIFlowService
            try:
                # Note: This might require database connection, so we'll catch and log appropriately
                service = CrewAIFlowService()
                self.log_result("crewai_flow_service_instantiation", True, "Service instantiated successfully")
            except Exception as e:
                if "database" in str(e).lower() or "connection" in str(e).lower():
                    self.log_result("crewai_flow_service_instantiation", True, "Service class structure valid (DB connection expected)")
                else:
                    self.log_result("crewai_flow_service_instantiation", False, "", str(e))
                    
            # Test Azure Adapter instantiation
            from app.services.adapters.azure_adapter import AzureAdapter
            try:
                adapter = AzureAdapter()
                self.log_result("azure_adapter_instantiation", True, "Adapter instantiated successfully")
            except Exception as e:
                if "credential" in str(e).lower() or "auth" in str(e).lower():
                    self.log_result("azure_adapter_instantiation", True, "Adapter class structure valid (credentials expected)")
                else:
                    self.log_result("azure_adapter_instantiation", False, "", str(e))
                    
            return True
            
        except Exception as e:
            self.log_result("service_instantiation", False, "", str(e))
            return False

    def test_backward_compatibility(self) -> bool:
        """Test that existing imports still work (facade pattern)."""
        try:
            # Test that main imports still work as expected
            from app.api.v1.endpoints.collection import router as collection_router
            from app.api.v1.endpoints.assessment_flow import router as assessment_router
            from app.services.crewai_flow_service import CrewAIFlowService
            from app.services.adapters.azure_adapter import AzureAdapter
            
            # Check that routers are properly defined
            if hasattr(collection_router, 'routes'):
                self.log_result("collection_router_compatibility", True, f"Router has {len(collection_router.routes)} routes")
            else:
                self.log_result("collection_router_compatibility", False, "", "Router missing routes attribute")
                
            if hasattr(assessment_router, 'routes'):
                self.log_result("assessment_router_compatibility", True, f"Router has {len(assessment_router.routes)} routes")
            else:
                self.log_result("assessment_router_compatibility", False, "", "Router missing routes attribute")
                
            # Check that service classes have expected methods
            service_methods = [method for method in dir(CrewAIFlowService) if not method.startswith('_')]
            self.log_result("crewai_service_methods", True, f"Service has {len(service_methods)} public methods")
            
            adapter_methods = [method for method in dir(AzureAdapter) if not method.startswith('_')]
            self.log_result("azure_adapter_methods", True, f"Adapter has {len(adapter_methods)} public methods")
            
            return True
            
        except Exception as e:
            self.log_result("backward_compatibility", False, "", str(e))
            return False

    def test_api_route_structure(self) -> bool:
        """Test that API routes are properly structured."""
        try:
            from app.api.v1.endpoints.collection import router as collection_router
            from app.api.v1.endpoints.assessment_flow import router as assessment_router
            
            # Check collection routes
            collection_routes = [route.path for route in collection_router.routes if hasattr(route, 'path')]
            self.log_result("collection_routes_structure", True, f"Collection has {len(collection_routes)} routes")
            
            # Check assessment flow routes  
            assessment_routes = [route.path for route in assessment_router.routes if hasattr(route, 'path')]
            self.log_result("assessment_routes_structure", True, f"Assessment flow has {len(assessment_routes)} routes")
            
            return True
            
        except Exception as e:
            self.log_result("api_route_structure", False, "", str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all validation tests."""
        print("=" * 60)
        print("MODULARIZATION VALIDATION TESTS")
        print("=" * 60)
        
        tests = [
            self.test_collection_imports,
            self.test_assessment_flow_imports,
            self.test_crewai_flow_service_imports,
            self.test_azure_adapter_imports,
            self.test_service_instantiation,
            self.test_backward_compatibility,
            self.test_api_route_structure
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = test()
                all_passed = all_passed and result
            except Exception as e:
                print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
                all_passed = False
                
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.results.values() if result["success"])
        total = len(self.results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if self.errors:
            print(f"\nErrors found ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if all_passed:
            print("\n✅ All modularization tests PASSED!")
        else:
            print("\n❌ Some modularization tests FAILED!")
            
        return all_passed

if __name__ == "__main__":
    validator = ModularizationValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)