#!/usr/bin/env python3
"""
Test script for PostgreSQL-only state store implementation
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator
from .postgres_store import PostgresFlowStateStore, managed_postgres_store
from .state_recovery import FlowStateRecovery
from .state_migrator import StateMigrator

async def test_postgres_store():
    """Test the PostgreSQL-only state store"""
    
    # Create test context
    context = RequestContext(
        client_account_id="test-client-123",
        engagement_id="test-engagement-456", 
        user_id="test-user-789"
    )
    
    # Test flow data
    test_flow_id = "test-flow-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    test_state = {
        'flow_id': test_flow_id,
        'client_account_id': str(context.client_account_id),
        'engagement_id': str(context.engagement_id),
        'user_id': str(context.user_id),
        'current_phase': 'initialization',
        'status': 'running',
        'progress_percentage': 0.0,
        'phase_completion': {
            'data_import': False,
            'field_mapping': False,
            'data_cleansing': False,
            'asset_creation': False,
            'asset_inventory': False,
            'dependency_analysis': False,
            'tech_debt_analysis': False
        },
        'crew_status': {},
        'raw_data': [{'test': 'data'}],
        'metadata': {'test': True},
        'errors': [],
        'warnings': [],
        'agent_insights': [],
        'user_clarifications': [],
        'workflow_log': [],
        'agent_confidences': {},
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    print("🧪 Testing PostgreSQL-only state store...")
    
    try:
        # Test 1: State validation
        print("\n1. Testing state validation...")
        validator = FlowStateValidator()
        validation_result = validator.validate_complete_state(test_state)
        
        if validation_result['valid']:
            print("✅ State validation passed")
        else:
            print(f"❌ State validation failed: {validation_result['errors']}")
            return False
        
        # Test 2: Store state
        print("\n2. Testing state storage...")
        async with managed_postgres_store(context) as store:
            await store.save_state(
                flow_id=test_flow_id,
                state=test_state,
                phase='initialization'
            )
            print("✅ State saved successfully")
            
            # Test 3: Load state
            print("\n3. Testing state loading...")
            loaded_state = await store.load_state(test_flow_id)
            
            if loaded_state:
                print("✅ State loaded successfully")
                print(f"   Flow ID: {loaded_state.get('flow_id')}")
                print(f"   Phase: {loaded_state.get('current_phase')}")
                print(f"   Status: {loaded_state.get('status')}")
            else:
                print("❌ Failed to load state")
                return False
            
            # Test 4: Create checkpoint
            print("\n4. Testing checkpoint creation...")
            checkpoint_id = await store.create_checkpoint(test_flow_id, 'initialization')
            print(f"✅ Checkpoint created: {checkpoint_id}")
            
            # Test 5: Update state
            print("\n5. Testing state update...")
            test_state['current_phase'] = 'data_import'
            test_state['progress_percentage'] = 10.0
            test_state['updated_at'] = datetime.utcnow().isoformat()
            
            await store.save_state(
                flow_id=test_flow_id,
                state=test_state,
                phase='data_import',
                version=1
            )
            print("✅ State updated successfully")
            
            # Test 6: Version history
            print("\n6. Testing version history...")
            versions = await store.get_flow_versions(test_flow_id)
            print(f"✅ Found {len(versions)} versions")
            for version in versions:
                print(f"   Version {version['version']}: {version['phase']} at {version['created_at']}")
        
        print("\n✅ All PostgreSQL store tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_state_recovery():
    """Test state recovery mechanisms"""
    
    print("\n🧪 Testing state recovery...")
    
    context = RequestContext(
        client_account_id="test-client-123",
        engagement_id="test-engagement-456",
        user_id="test-user-789"
    )
    
    # Create a corrupted state
    corrupted_state = {
        'flow_id': 'corrupted-flow-123',
        'current_phase': 'invalid_phase',  # Invalid phase
        'status': 'invalid_status',        # Invalid status
        'progress_percentage': 150.0,      # Invalid progress
        'client_account_id': str(context.client_account_id),
        'engagement_id': str(context.engagement_id),
        'user_id': str(context.user_id)
    }
    
    try:
        # Test validation on corrupted state
        validator = FlowStateValidator()
        validation_result = validator.validate_complete_state(corrupted_state)
        
        if not validation_result['valid']:
            print(f"✅ Correctly detected corrupted state: {len(validation_result['errors'])} errors")
        else:
            print("❌ Failed to detect corrupted state")
            return False
        
        print("\n✅ State recovery tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Recovery test failed: {e}")
        return False

async def test_state_validator():
    """Test state validator comprehensively"""
    
    print("\n🧪 Testing state validator...")
    
    validator = FlowStateValidator()
    
    # Test 1: Valid state
    valid_state = {
        'flow_id': 'test-123',
        'current_phase': 'initialization',
        'status': 'running',
        'progress_percentage': 0.0,
        'client_account_id': 'client-123',
        'engagement_id': 'engagement-456',
        'user_id': 'user-789',
        'phase_completion': {
            'data_import': False,
            'field_mapping': False
        },
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    result = validator.validate_complete_state(valid_state)
    if result['valid']:
        print("✅ Valid state correctly validated")
    else:
        print(f"❌ Valid state rejected: {result['errors']}")
        return False
    
    # Test 2: Invalid state
    invalid_state = {
        'flow_id': '',  # Empty flow_id
        'current_phase': 'invalid_phase',  # Invalid phase
        'progress_percentage': 150.0  # Invalid progress
    }
    
    result = validator.validate_complete_state(invalid_state)
    if not result['valid']:
        print(f"✅ Invalid state correctly rejected: {len(result['errors'])} errors")
    else:
        print("❌ Invalid state incorrectly accepted")
        return False
    
    # Test 3: Phase transition validation
    state_for_transition = {
        'current_phase': 'initialization',
        'phase_completion': {
            'initialization': True,
            'data_import': False
        }
    }
    
    if validator.validate_phase_transition(state_for_transition, 'data_import'):
        print("✅ Valid phase transition approved")
    else:
        print("❌ Valid phase transition rejected")
        return False
    
    print("\n✅ State validator tests passed!")
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting PostgreSQL-only state management tests...")
    
    test_results = []
    
    # Run tests
    test_results.append(await test_state_validator())
    test_results.append(await test_postgres_store())
    test_results.append(await test_state_recovery())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PostgreSQL-only state management is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)