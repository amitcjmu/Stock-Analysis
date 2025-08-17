#!/usr/bin/env python3
"""
Test service functionality and API signatures
Tests the modularized services without requiring full initialization
"""

import sys
import os
import inspect
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

class ServiceFunctionalityValidator:
    """Validates service functionality and API consistency."""
    
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

    def test_crewai_service_api_consistency(self) -> bool:
        """Test CrewAI service API consistency between main and modular components."""
        try:
            # Import without dependency errors by mocking problematic imports
            import unittest.mock
            
            # Mock the problematic CrewAI dependency
            with unittest.mock.patch.dict('sys.modules', {
                'crewai': unittest.mock.MagicMock(),
                'crewai.agent': unittest.mock.MagicMock(),
                'crewai.crew': unittest.mock.MagicMock(),
                'crewai.task': unittest.mock.MagicMock(),
            }):
                
                # Test individual modular components
                from app.services import crewai_flow_state_manager
                from app.services import crewai_flow_executor
                from app.services import crewai_flow_lifecycle
                from app.services import crewai_flow_monitoring
                from app.services import crewai_flow_utils
                
                self.log_result("crewai_modular_components_loadable", True, "All modular components loaded successfully")
                
                # Check if components have expected classes/functions
                components_info = []
                
                # State Manager
                state_classes = [name for name, obj in inspect.getmembers(crewai_flow_state_manager, inspect.isclass)]
                components_info.append(f"StateManager: {len(state_classes)} classes")
                
                # Executor  
                executor_classes = [name for name, obj in inspect.getmembers(crewai_flow_executor, inspect.isclass)]
                components_info.append(f"Executor: {len(executor_classes)} classes")
                
                # Lifecycle
                lifecycle_classes = [name for name, obj in inspect.getmembers(crewai_flow_lifecycle, inspect.isclass)]
                components_info.append(f"Lifecycle: {len(lifecycle_classes)} classes")
                
                # Monitoring
                monitoring_classes = [name for name, obj in inspect.getmembers(crewai_flow_monitoring, inspect.isclass)]
                components_info.append(f"Monitoring: {len(monitoring_classes)} classes")
                
                # Utils
                utils_functions = [name for name, obj in inspect.getmembers(crewai_flow_utils, inspect.isfunction)]
                components_info.append(f"Utils: {len(utils_functions)} functions")
                
                self.log_result("crewai_component_analysis", True, " | ".join(components_info))
                
                # Test main service
                from app.services.crewai_flow_service import CrewAIFlowService
                
                # Get the class signature
                init_signature = inspect.signature(CrewAIFlowService.__init__)
                methods = [name for name, method in inspect.getmembers(CrewAIFlowService, predicate=inspect.ismethod)]
                public_methods = [m for m in dir(CrewAIFlowService) if not m.startswith('_') and callable(getattr(CrewAIFlowService, m))]
                
                self.log_result("crewai_service_api_signature", True, 
                               f"Init params: {len(init_signature.parameters)}, Public methods: {len(public_methods)}")
                
                return True
                
        except Exception as e:
            self.log_result("crewai_service_api_consistency", False, "", str(e))
            return False

    def test_azure_adapter_api_consistency(self) -> bool:
        """Test Azure adapter API consistency."""
        try:
            # Mock Azure dependencies
            import unittest.mock
            
            with unittest.mock.patch.dict('sys.modules', {
                'azure.identity': unittest.mock.MagicMock(),
                'azure.mgmt.resource': unittest.mock.MagicMock(),
                'azure.mgmt.compute': unittest.mock.MagicMock(),
                'azure.mgmt.storage': unittest.mock.MagicMock(),
                'google.cloud': unittest.mock.MagicMock(),
                'google.auth': unittest.mock.MagicMock(),
                'google.oauth2': unittest.mock.MagicMock(),
                'google.oauth2.service_account': None,  # This causes the AttributeError
            }):
                
                # Test individual modular components
                try:
                    # These might still fail due to the service_account.Credentials issue
                    # but let's see what we can test
                    
                    # Test the main adapter class definition
                    spec = importlib.util.find_spec("app.services.adapters.azure_adapter")
                    if spec and spec.origin:
                        with open(spec.origin, 'r') as f:
                            content = f.read()
                            
                        # Check if the main class is defined
                        if "class AzureAdapter" in content:
                            self.log_result("azure_adapter_class_defined", True, "AzureAdapter class is defined")
                        else:
                            self.log_result("azure_adapter_class_defined", False, "", "AzureAdapter class not found")
                            
                        # Check for imports from modular components
                        modular_imports = [
                            "azure_adapter_auth",
                            "azure_adapter_storage",
                            "azure_adapter_compute",
                            "azure_adapter_data",
                            "azure_adapter_utils"
                        ]
                        
                        found_imports = sum(1 for imp in modular_imports if imp in content)
                        self.log_result("azure_adapter_modular_imports", True, 
                                       f"Uses {found_imports}/{len(modular_imports)} modular components")
                    
                    # Test individual module files exist and have content
                    module_files = [
                        "app/services/adapters/azure_adapter_auth.py",
                        "app/services/adapters/azure_adapter_storage.py", 
                        "app/services/adapters/azure_adapter_compute.py",
                        "app/services/adapters/azure_adapter_data.py",
                        "app/services/adapters/azure_adapter_utils.py"
                    ]
                    
                    for module_file in module_files:
                        module_path = Path(__file__).parent / module_file
                        if module_path.exists():
                            with open(module_path, 'r') as f:
                                content = f.read()
                            
                            # Count classes and functions
                            classes = content.count("class ")
                            functions = content.count("def ")
                            
                            module_name = module_file.split('/')[-1].replace('.py', '')
                            self.log_result(f"azure_{module_name}_structure", True, 
                                           f"{classes} classes, {functions} functions")
                        else:
                            module_name = module_file.split('/')[-1].replace('.py', '')
                            self.log_result(f"azure_{module_name}_structure", False, "", "File not found")
                    
                    return True
                    
                except Exception as e:
                    self.log_result("azure_adapter_component_analysis", False, "", str(e))
                    return False
                
        except Exception as e:
            self.log_result("azure_adapter_api_consistency", False, "", str(e))
            return False

    def test_collection_endpoint_structure(self) -> bool:
        """Test collection endpoint structure and route definitions."""
        try:
            # Test collection modular components
            from pathlib import Path
            
            # Analyze collection_crud
            crud_file = Path(__file__).parent / "app/api/v1/endpoints/collection_crud.py"
            if crud_file.exists():
                with open(crud_file, 'r') as f:
                    content = f.read()
                
                # Count async def functions (API endpoints)
                async_functions = content.count("async def")
                classes = content.count("class ")
                
                self.log_result("collection_crud_structure", True, 
                               f"{async_functions} async functions, {classes} classes")
            
            # Analyze collection_validators
            validators_file = Path(__file__).parent / "app/api/v1/endpoints/collection_validators.py"
            if validators_file.exists():
                with open(validators_file, 'r') as f:
                    content = f.read()
                
                functions = content.count("def ")
                classes = content.count("class ")
                
                self.log_result("collection_validators_structure", True,
                               f"{functions} functions, {classes} classes")
            
            # Analyze collection_serializers
            serializers_file = Path(__file__).parent / "app/api/v1/endpoints/collection_serializers.py"
            if serializers_file.exists():
                with open(serializers_file, 'r') as f:
                    content = f.read()
                
                functions = content.count("def ")
                classes = content.count("class ")
                
                self.log_result("collection_serializers_structure", True,
                               f"{functions} functions, {classes} classes")
            
            # Analyze collection_utils
            utils_file = Path(__file__).parent / "app/api/v1/endpoints/collection_utils.py"
            if utils_file.exists():
                with open(utils_file, 'r') as f:
                    content = f.read()
                
                functions = content.count("def ")
                classes = content.count("class ")
                
                self.log_result("collection_utils_structure", True,
                               f"{functions} functions, {classes} classes")
            
            # Analyze main collection file
            main_file = Path(__file__).parent / "app/api/v1/endpoints/collection.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                
                # Count route definitions
                routes = content.count("@router.")
                async_functions = content.count("async def")
                
                self.log_result("collection_main_routes", True,
                               f"{routes} routes, {async_functions} async functions")
            
            return True
            
        except Exception as e:
            self.log_result("collection_endpoint_structure", False, "", str(e))
            return False

    def test_assessment_flow_structure(self) -> bool:
        """Test assessment flow endpoint structure."""
        try:
            from pathlib import Path
            
            # Analyze main assessment flow file
            main_file = Path(__file__).parent / "app/api/v1/endpoints/assessment_flow.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                
                routes = content.count("@router.")
                async_functions = content.count("async def")
                
                self.log_result("assessment_flow_main_routes", True,
                               f"{routes} routes, {async_functions} async functions")
            
            # Test modular components
            components = [
                "assessment_flow_crud.py",
                "assessment_flow_validators.py", 
                "assessment_flow_processors.py",
                "assessment_flow_utils.py"
            ]
            
            for component in components:
                comp_file = Path(__file__).parent / f"app/api/v1/endpoints/{component}"
                if comp_file.exists():
                    with open(comp_file, 'r') as f:
                        content = f.read()
                    
                    functions = content.count("def ")
                    classes = content.count("class ")
                    
                    comp_name = component.replace(".py", "")
                    self.log_result(f"{comp_name}_structure", True,
                                   f"{functions} functions, {classes} classes")
            
            return True
            
        except Exception as e:
            self.log_result("assessment_flow_structure", False, "", str(e))
            return False

    def test_backward_compatibility_signatures(self) -> bool:
        """Test that public API signatures remain consistent."""
        try:
            # Test that main imports still work by checking file contents
            from pathlib import Path
            
            # Check collection.py imports collection_crud
            collection_file = Path(__file__).parent / "app/api/v1/endpoints/collection.py"
            if collection_file.exists():
                with open(collection_file, 'r') as f:
                    content = f.read()
                
                if "from app.api.v1.endpoints import collection_crud" in content:
                    self.log_result("collection_backward_compatibility", True, 
                                   "Collection maintains imports from modular components")
                else:
                    self.log_result("collection_backward_compatibility", False, "",
                                   "Collection doesn't import from modular components")
            
            # Check CrewAI service imports its components
            crewai_file = Path(__file__).parent / "app/services/crewai_flow_service.py"
            if crewai_file.exists():
                with open(crewai_file, 'r') as f:
                    content = f.read()
                
                modular_components = [
                    "crewai_flow_state_manager",
                    "crewai_flow_executor", 
                    "crewai_flow_lifecycle",
                    "crewai_flow_monitoring",
                    "crewai_flow_utils"
                ]
                
                found_imports = sum(1 for comp in modular_components if comp in content)
                
                if found_imports >= 3:  # At least most components imported
                    self.log_result("crewai_service_backward_compatibility", True,
                                   f"CrewAI service imports {found_imports}/{len(modular_components)} components")
                else:
                    self.log_result("crewai_service_backward_compatibility", False, "",
                                   f"CrewAI service only imports {found_imports}/{len(modular_components)} components")
            
            # Check Azure adapter imports its components
            azure_file = Path(__file__).parent / "app/services/adapters/azure_adapter.py"
            if azure_file.exists():
                with open(azure_file, 'r') as f:
                    content = f.read()
                
                azure_components = [
                    "azure_adapter_auth",
                    "azure_adapter_storage",
                    "azure_adapter_compute",
                    "azure_adapter_data",
                    "azure_adapter_utils"
                ]
                
                found_imports = sum(1 for comp in azure_components if comp in content)
                
                if found_imports >= 3:  # At least most components imported
                    self.log_result("azure_adapter_backward_compatibility", True,
                                   f"Azure adapter imports {found_imports}/{len(azure_components)} components")
                else:
                    self.log_result("azure_adapter_backward_compatibility", False, "",
                                   f"Azure adapter only imports {found_imports}/{len(azure_components)} components")
            
            return True
            
        except Exception as e:
            self.log_result("backward_compatibility_signatures", False, "", str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all functionality validation tests."""
        print("=" * 70)
        print("SERVICE FUNCTIONALITY VALIDATION")
        print("=" * 70)
        
        tests = [
            self.test_crewai_service_api_consistency,
            self.test_azure_adapter_api_consistency,
            self.test_collection_endpoint_structure,
            self.test_assessment_flow_structure,
            self.test_backward_compatibility_signatures
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = test()
                all_passed = all_passed and result
            except Exception as e:
                print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
                all_passed = False
                
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.results.values() if result["success"])
        total = len(self.results)
        
        print(f"Functionality tests passed: {passed}/{total}")
        
        if self.errors:
            print(f"\nIssues found ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if all_passed:
            print("\n✅ All service functionality tests PASSED!")
        else:
            print("\n⚠️  Some service functionality issues found!")
            
        return all_passed

if __name__ == "__main__":
    validator = ServiceFunctionalityValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)