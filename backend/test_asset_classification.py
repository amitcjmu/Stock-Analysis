#!/usr/bin/env python3
"""
Direct test of enhanced asset type classification logic.
Tests if our fixes properly recognize CITYPE fields for applications vs servers.
"""

import sys
sys.path.append('/app')
sys.path.append('/app/backend')

# Sample data structure that matches what the user uploaded
SAMPLE_USER_DATA = [
    # Applications from user's screenshots
    {
        "CIID": "APP0001",
        "CITYPE": "Application", 
        "NAME": "HR_Payroll",
        "ENVIRONMENT": "Production",
        "RELATED_CI": "SRV0001"
    },
    {
        "CIID": "APP0002",
        "CITYPE": "Application",
        "NAME": "Finance_ERP", 
        "ENVIRONMENT": "Production",
        "RELATED_CI": "SRV0003"
    },
    {
        "CIID": "APP0003",
        "CITYPE": "Application",
        "NAME": "CRM_System",
        "ENVIRONMENT": "Production", 
        "RELATED_CI": "SRV0004"
    },
    # Servers from user's screenshots
    {
        "CIID": "SRV0001",
        "CITYPE": "Server",
        "NAME": "srv-hr-01",
        "IP_ADDRESS": "192.168.1.10",
        "ENVIRONMENT": "Production",
        "OS": "Windows Server 2019",
        "RELATED_CI": "APP0001"
    },
    {
        "CIID": "SRV0002",
        "CITYPE": "Server",
        "NAME": "srv-hr-db-01",
        "IP_ADDRESS": "192.168.1.11",
        "ENVIRONMENT": "Production",
        "OS": "Red Hat Enterprise Linux 8",
        "RELATED_CI": "APP0001"
    },
    {
        "CIID": "SRV0003",
        "CITYPE": "Server", 
        "NAME": "srv-erp-01",
        "IP_ADDRESS": "192.168.1.20",
        "ENVIRONMENT": "Production",
        "OS": "Windows Server 2019",
        "RELATED_CI": "APP0002"
    }
]

def test_asset_classification():
    """Test enhanced asset type classification."""
    print("🧪 Testing Enhanced Asset Type Classification")
    print("   (Testing the user's actual data structure with CITYPE fields)")
    
    try:
        from app.api.v1.endpoints.data_import import _determine_asset_type_agentic
        
        print(f"\n📊 Testing Classification Function:")
        print(f"{'CIID':<10} {'Original CITYPE':<15} {'Predicted':<15} {'Status'}")
        print("-" * 55)
        
        correct_count = 0
        total_count = len(SAMPLE_USER_DATA)
        
        for raw_data in SAMPLE_USER_DATA:
            predicted_type = _determine_asset_type_agentic(raw_data, {})
            expected_type = raw_data['CITYPE'].lower()
            correct = predicted_type == expected_type
            
            if correct:
                correct_count += 1
                status = "✅ CORRECT"
            else:
                status = "❌ WRONG"
            
            print(f"{raw_data['CIID']:<10} {raw_data['CITYPE']:<15} {predicted_type:<15} {status}")
        
        accuracy = (correct_count / total_count) * 100
        print("-" * 55)
        print(f"📈 Accuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")
        
        if accuracy == 100:
            print("🎉 SUCCESS: All assets classified correctly!")
            print("   ✅ Applications properly recognized from CITYPE='Application'")
            print("   ✅ Servers properly recognized from CITYPE='Server'")
        else:
            print(f"⚠️  ISSUE: Only {accuracy:.1f}% accuracy")
            print("   The enhanced classification function needs further improvement")
        
        # Test dependency extraction
        print(f"\n🔗 Testing Dependency Recognition:")
        dependencies_found = 0
        for raw_data in SAMPLE_USER_DATA:
            if "RELATED_CI" in raw_data and raw_data["RELATED_CI"]:
                dependencies_found += 1
                print(f"   {raw_data['CIID']} → {raw_data['RELATED_CI']} ({raw_data['CITYPE']})")
        
        print(f"📊 Dependencies Found: {dependencies_found}/{total_count}")
        
        if dependencies_found > 0:
            print("✅ Dependency relationships detected in raw data")
        else:
            print("⚠️  No dependency relationships found")
        
        return accuracy == 100
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Enhanced classification function not available")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_asset_classification()
    
    if success:
        print("\n🎉 Enhanced Asset Classification Test PASSED!")
        print("   The CrewAI Flow should now correctly classify:")
        print("   📱 Applications: HR_Payroll, Finance_ERP, CRM_System")
        print("   🖥️  Servers: srv-hr-01, srv-hr-db-01, srv-erp-01")
        print("   🔗 Dependencies: Proper app-to-server relationships")
    else:
        print("\n❌ Enhanced Asset Classification Test FAILED!")
        print("   The user's applications are likely being misclassified as servers")
        print("   This explains why App Portfolio shows 0 applications") 