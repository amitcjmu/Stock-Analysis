#!/usr/bin/env python3
"""
Basic ADCS Component Test
Tests to verify ADCS components are properly integrated
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all ADCS components can be imported"""
    print("\n=== Testing ADCS Component Imports ===\n")
    
    errors = []
    
    # Test Phase 1 imports
    print("Testing Phase 1 (Foundation) imports...")
    try:
        from app.models.collection_flow import CollectionFlow
        print("✅ CollectionFlow model imported")
    except Exception as e:
        errors.append(f"❌ CollectionFlow model: {e}")
    
    try:
        from app.services.collection_flow import (
            CollectionFlowStateService,
            TierDetectionService,
            DataTransformationService
        )
        print("✅ Core collection services imported")
    except Exception as e:
        errors.append(f"❌ Core collection services: {e}")
    
    # Test Phase 2 imports
    print("\nTesting Phase 2 (Collection Capabilities) imports...")
    try:
        from app.services.adapters.aws_adapter import AWSAdapter
        from app.services.adapters.azure_adapter import AzureAdapter
        print("✅ Platform adapters imported")
    except Exception as e:
        errors.append(f"❌ Platform adapters: {e}")
    
    try:
        from app.services.ai_analysis.gap_analysis_agent import GapAnalysisAgent
        from app.services.ai_analysis.questionnaire_generator import QuestionnaireGenerator
        print("✅ AI analysis services imported")
    except Exception as e:
        errors.append(f"❌ AI analysis services: {e}")
    
    try:
        from app.services.manual_collection import (
            AdaptiveFormService,
            BulkDataService,
            QuestionnaireValidationService as ValidationService
        )
        print("✅ Manual collection services imported")
    except Exception as e:
        errors.append(f"❌ Manual collection services: {e}")
    
    # Test Phase 3 imports
    print("\nTesting Phase 3 (Workflow Orchestration) imports...")
    try:
        from app.services.workflow_orchestration.collection_phase_engine import CollectionPhaseExecutionEngine
        from app.services.workflow_orchestration.workflow_orchestrator import WorkflowOrchestrator
        print("✅ Workflow orchestration services imported")
    except Exception as e:
        errors.append(f"❌ Workflow orchestration services: {e}")
    
    # Test Phase 4 imports
    print("\nTesting Phase 4 (Integration) imports...")
    try:
        from app.services.integration.smart_workflow_orchestrator import SmartWorkflowOrchestrator
        from app.services.integration.data_flow_validator import DataFlowValidator
        print("✅ Integration services imported")
    except Exception as e:
        errors.append(f"❌ Integration services: {e}")
    
    # Summary
    print(f"\n=== Import Test Summary ===")
    print(f"Total errors: {len(errors)}")
    if errors:
        print("\nErrors found:")
        for error in errors:
            print(error)
        return False
    else:
        print("\n✅ All ADCS components can be imported successfully!")
        return True

def test_database_models():
    """Test that ADCS database models are properly configured"""
    print("\n=== Testing ADCS Database Models ===\n")
    
    try:
        from app.models import (
            CollectionFlow,
            CollectedDataInventory,
            CollectionDataGap,
            CollectionQuestionnaireResponse,
            PlatformAdapter,
            PlatformCredential
        )
        
        # Check table names
        print(f"CollectionFlow table: {CollectionFlow.__tablename__}")
        print(f"CollectedDataInventory table: {CollectedDataInventory.__tablename__}")
        print(f"PlatformAdapter table: {PlatformAdapter.__tablename__}")
        print(f"PlatformCredential table: {PlatformCredential.__tablename__}")
        
        print("\n✅ All ADCS database models are properly configured!")
        return True
        
    except Exception as e:
        print(f"❌ Database model error: {e}")
        return False

def test_flow_registration():
    """Test that Collection Flow is registered in Master Flow Orchestrator"""
    print("\n=== Testing Collection Flow Registration ===\n")
    
    try:
        from app.services.flow_type_registry import flow_type_registry
        from app.services.flow_configs import initialize_all_flows
        
        # Initialize flows if not already done
        initialize_all_flows()
        
        print("Registered flow types:")
        flow_types = flow_type_registry.list_flow_types()
        for flow_type in flow_types:
            print(f"  - {flow_type}")
        
        if "collection" in flow_types:
            print("\n✅ Collection Flow is registered!")
            return True
        else:
            print("\n❌ Collection Flow is NOT registered!")
            return False
            
    except Exception as e:
        print(f"❌ Flow registration error: {e}")
        return False

if __name__ == "__main__":
    print("Running ADCS Basic Tests...")
    
    # Run tests
    import_ok = test_imports()
    db_ok = test_database_models()
    flow_ok = test_flow_registration()
    
    # Overall result
    if import_ok and db_ok and flow_ok:
        print("\n🎉 All ADCS basic tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some ADCS tests failed. Please check the errors above.")
        sys.exit(1)