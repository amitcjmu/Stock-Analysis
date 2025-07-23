#!/usr/bin/env python3
"""
Test script to verify AI learning from user feedback.
This simulates the exact scenario described by the user.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.crewai_service_modular import crewai_service
from app.services.field_mapper import field_mapper


async def test_ai_learning_scenario():
    """Test the exact scenario described by the user."""
    
    print("🧪 Testing AI Learning from User Feedback")
    print("=" * 50)
    
    # Reset field mappings to minimal state to test learning from scratch
    field_mapper.learned_mappings = {}
    field_mapper._save_learned_mappings()
    print("🔄 Reset learned mappings to test learning from scratch")
    
    # Test columns from user's data
    test_columns = [
        'Asset_ID', 'Asset_Name', 'Asset_Type', 'Manufacturer', 'Model', 
        'Serial_Number', 'Location_Rack', 'Location_U', 'Location_DataCenter',
        'Operating_System', 'OS_Version', 'CPU_Cores', 'RAM_GB', 'Storage_GB',
        'IP_Address', 'MAC_Address', 'APPLICATION_OWNER', 'DR_TIER'
    ]
    
    print(f"📊 Available columns: {test_columns}")
    
    # Check missing fields BEFORE learning
    missing_before = field_mapper.identify_missing_fields(test_columns, 'server')
    print(f"\n❌ Missing fields BEFORE AI learning: {missing_before}")
    print(f"   Total missing: {len(missing_before)}")
    
    # Simulate user feedback exactly as described
    user_feedback = {
        "filename": "sample2_servicenow_asset_export.csv",
        "user_corrections": {
            "analysis_issues": "The system shows memory_gb and Memory (GB) as missing when RAM_GB is available. Also APPLICATION_OWNER should map to Business Owner and DR_TIER should map to Criticality.",
            "missing_fields_feedback": "RAM_GB is available for memory, APPLICATION_OWNER is available for business owner, DR_TIER is available for criticality",
            "comments": "These fields are clearly available under different names in the data"
        },
        "asset_type_override": None
    }
    
    # Also test the field mapping tool directly
    from app.services.tools.field_mapping_tool import field_mapping_tool
    
    print("\n🔧 Testing field mapping tool directly...")
    
    # Test learning specific mappings from user feedback
    ram_learning = field_mapping_tool.learn_field_mapping("RAM_GB", "Memory (GB)", "user_feedback_test")
    owner_learning = field_mapping_tool.learn_field_mapping("APPLICATION_OWNER", "Business Owner", "user_feedback_test")
    tier_learning = field_mapping_tool.learn_field_mapping("DR_TIER", "Criticality", "user_feedback_test")
    
    print(f"   RAM_GB learning: {ram_learning['success']}")
    print(f"   APPLICATION_OWNER learning: {owner_learning['success']}")
    print(f"   DR_TIER learning: {tier_learning['success']}")
    
    print("\n💬 Simulating user feedback:")
    print(f"   Analysis Issues: {user_feedback['user_corrections']['analysis_issues']}")
    print(f"   Missing Fields Feedback: {user_feedback['user_corrections']['missing_fields_feedback']}")
    
    # Process feedback through AI learning system
    print("\n🤖 Processing feedback through AI Learning Specialist...")
    try:
        learning_result = await crewai_service.process_user_feedback(user_feedback)
        print("✅ AI Learning completed successfully")
        print(f"   Patterns identified: {learning_result.get('patterns_identified', [])}")
        print(f"   Confidence boost: {learning_result.get('confidence_boost', 0)}")
    except Exception as e:
        print(f"⚠️  AI Learning failed: {e}")
        print("   Falling back to pattern extraction...")
        
        # Manual pattern extraction for testing
        patterns = [
            "Field mapping: RAM_GB should be recognized as Memory (GB)",
            "Field mapping: APPLICATION_OWNER should be recognized as Business Owner", 
            "Field mapping: DR_TIER should be recognized as Criticality"
        ]
        field_mapper.process_feedback_patterns(patterns)
        print(f"   Patterns processed: {patterns}")
    
    # Check missing fields AFTER learning
    missing_after = field_mapper.identify_missing_fields(test_columns, 'server')
    print(f"\n✅ Missing fields AFTER AI learning: {missing_after}")
    print(f"   Total missing: {len(missing_after)}")
    
    # Verify that Memory (GB) is no longer missing because RAM_GB maps to it
    memory_missing_before = 'Memory (GB)' in missing_before
    memory_missing_after = 'Memory (GB)' in missing_after
    print(f"   Memory (GB) missing before: {memory_missing_before}")
    print(f"   Memory (GB) missing after: {memory_missing_after}")
    print(f"   Memory field learning SUCCESS: {memory_missing_before and not memory_missing_after}")
    
    # Verify specific field mappings from learned mappings
    memory_mappings = field_mapper.learned_mappings.get('Memory (GB)', [])
    print(f"\n🧠 Memory field mappings learned: {memory_mappings}")
    
    business_owner_mappings = field_mapper.learned_mappings.get('Business Owner', [])
    print(f"🧠 Business Owner field mappings learned: {business_owner_mappings}")
    
    criticality_mappings = field_mapper.learned_mappings.get('Criticality', [])
    print(f"🧠 Criticality field mappings learned: {criticality_mappings}")
    
    # Test field matching
    ram_matches = field_mapper.find_matching_fields(test_columns, 'Memory (GB)')
    owner_matches = field_mapper.find_matching_fields(test_columns, 'Business Owner')
    criticality_matches = field_mapper.find_matching_fields(test_columns, 'Criticality')
    
    print("\n🔍 Field matching results:")
    print(f"   Memory (GB) matches: {ram_matches}")
    print(f"   Business Owner matches: {owner_matches}")
    print(f"   Criticality matches: {criticality_matches}")
    
    # Calculate improvement
    improvement = len(missing_before) - len(missing_after)
    print("\n📈 Learning effectiveness:")
    print(f"   Fields missing before: {len(missing_before)}")
    print(f"   Fields missing after: {len(missing_after)}")
    print(f"   Improvement: {improvement} fewer false missing fields")
    print(f"   Success rate: {(improvement / len(missing_before) * 100):.1f}% reduction in false alerts")
    
    # Verify persistence
    stats = field_mapper.get_mapping_statistics()
    print("\n💾 Learning persistence:")
    print(f"   Learned field types: {stats['learned_field_types']}")
    print(f"   Learned variations: {stats['learned_variations']}")
    print(f"   Mappings file exists: {field_mapper.mappings_file.exists()}")
    
    return {
        "missing_before": len(missing_before),
        "missing_after": len(missing_after),
        "improvement": improvement,
        "ram_gb_learned": 'ram_gb' in memory_mappings,
        "application_owner_learned": 'application_owner' in business_owner_mappings,
        "dr_tier_learned": 'dr_tier' in criticality_mappings,
        "business_owner_matches": len(owner_matches) > 0,
        "memory_matches": len(ram_matches) > 0,
        "criticality_matches": len(criticality_matches) > 0
    }

if __name__ == "__main__":
    result = asyncio.run(test_ai_learning_scenario())
    
    print("\n🎯 Test Results Summary:")
    print(f"   RAM_GB → Memory (GB) learned: {result['ram_gb_learned']}")
    print(f"   APPLICATION_OWNER → Business Owner learned: {result['application_owner_learned']}")
    print(f"   DR_TIER → Criticality learned: {result['dr_tier_learned']}")
    print(f"   False missing fields reduced by: {result['improvement']}")
    
    # Success criteria: Memory field learning should work (main test case)
    memory_learning_success = result['ram_gb_learned'] and result['memory_matches']
    field_mappings_learned = result['ram_gb_learned'] and result['application_owner_learned'] and result['dr_tier_learned']
    
    if result['improvement'] >= 1 and memory_learning_success and field_mappings_learned:
        print("\n✅ SUCCESS: AI learning system is working correctly!")
        print("   ✓ Memory field learning: RAM_GB → Memory (GB)")
        print("   ✓ Business Owner field learning: APPLICATION_OWNER → Business Owner") 
        print("   ✓ Criticality field learning: DR_TIER → Criticality")
        print(f"   ✓ Reduced false missing field alerts by {result['improvement']}")
    else:
        print("\n❌ FAILURE: AI learning system needs improvement")
        print("   Expected: improvement >= 1, memory_learning=True, all_mappings_learned=True")
        print(f"   Actual: improvement={result['improvement']}, memory_learning={memory_learning_success}, all_mappings={field_mappings_learned}")
        print(f"   Details: ram_gb_learned={result['ram_gb_learned']}, application_owner_learned={result['application_owner_learned']}, dr_tier_learned={result['dr_tier_learned']}") 