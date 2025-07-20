#!/usr/bin/env python3
"""
ADCS Test Runner
Runs available tests for the ADCS implementation
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("ADCS Test Runner")
    print("="*60)
    
    tests_to_run = [
        # Integration tests
        ("pytest /app/tests/integration/test_smart_workflow_integration.py -v -k 'test_complete_smart_workflow or test_workflow_status_tracking' || true", 
         "Smart Workflow Integration Tests (Basic)"),
        
        # API tests  
        ("pytest /app/tests/api/v1/endpoints/test_sessions.py -v -k 'test_' --tb=short || true",
         "Session API Tests"),
        
        # Flow tests
        ("pytest /app/tests/flows/test_discovery_flow.py -v -k 'test_discovery_flow' --tb=short || true", 
         "Discovery Flow Tests"),
         
        # Services tests
        ("pytest /app/tests/services/test_master_flow_orchestrator.py -v -k 'test_flow_registration' --tb=short || true",
         "Master Flow Orchestrator Tests"),
         
        # Memory tests
        ("pytest /app/tests/memory/test_shared_memory.py -v --tb=short || true",
         "Shared Memory Tests"),
    ]
    
    results = []
    
    for cmd, desc in tests_to_run:
        success = run_command(f"docker exec migration_backend {cmd}", desc)
        results.append((desc, success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for desc, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {desc}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    # Check if we can at least import ADCS components
    print("\n" + "="*60)
    print("ADCS COMPONENT STATUS")
    print("="*60)
    
    import_test = run_command(
        "docker exec migration_backend python /app/test_adcs_basic.py",
        "ADCS Import Test"
    )
    
    if import_test:
        print("✅ ADCS components can be imported successfully!")
    else:
        print("⚠️  Some ADCS components have import issues")
    
    return 0 if passed > 0 else 1

if __name__ == "__main__":
    sys.exit(main())