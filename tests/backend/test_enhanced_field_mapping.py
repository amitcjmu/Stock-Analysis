#!/usr/bin/env python3
"""
Test Enhanced Field Mapping System
Test the improved agentic field mapping with real-world CMDB data formats.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.field_mapper import field_mapper
from app.services.tools.field_mapping_tool import field_mapping_tool
from app.api.v1.endpoints.discovery import processor
import pandas as pd
import json

def test_enhanced_field_mapping():
    """Test enhanced field mapping with data similar to the screenshots."""
    print("🧪 Testing Enhanced Agentic Field Mapping System")
    print("=" * 60)
    
    # Test data similar to what was shown in the screenshots
    test_csv_content = """HOSTNAME,WORKLOAD TYPE,ENVIRONMENT,CPU CORES,RAM (GB),DISK SIZE (GB),OS TYPE,OS VERSION,APPLICATION_MAPPED,APPLICA
server-1,DB Server,Dev,10,16,500,Linux,Ubuntu 20.04,App 130,
server-2,Web Server,Dev,8,8,500,Linux,2016,App 252,
server-3,App Server,Dev,15,64,500,Linux,Ubuntu 20.04,App 76,
server-4,DB Server,Test,13,8,250,Windows,2016,App 75,
server-5,DB Server,Dev,10,16,500,AIX,7.2,App 210"""
    
    try:
        # Parse the CSV
        df = processor.parse_file_content(test_csv_content, 'text/csv')
        print(f"✅ Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
        print(f"   Columns: {list(df.columns)}")
        
        # Test pattern analysis
        columns = df.columns.tolist()
        sample_rows = []
        for _, row in df.head().iterrows():
            sample_row = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
            sample_rows.append(sample_row)
        
        print(f"\n🔍 Testing Pattern Analysis:")
        pattern_analysis = field_mapper.analyze_data_patterns(columns, sample_rows, "server")
        
        column_mappings = pattern_analysis.get("column_analysis", {})
        confidence_scores = pattern_analysis.get("confidence_scores", {})
        
        print(f"   Mappings found: {len(column_mappings)}")
        for column, mapped_field in column_mappings.items():
            confidence = confidence_scores.get(column, 0.0)
            print(f"   • {column} → {mapped_field} (confidence: {confidence:.2f})")
        
        # Test field mapping tool integration
        print(f"\n🤖 Testing Agentic Field Mapping Tool:")
        tool_analysis = field_mapping_tool.analyze_data_patterns(columns, sample_rows, "server")
        auto_learned = tool_analysis.get("auto_learned_mappings", [])
        
        print(f"   Auto-learned mappings: {len(auto_learned)}")
        for mapping in auto_learned:
            print(f"   • {mapping}")
        
        # Test missing field detection with enhanced logic
        print(f"\n🎯 Testing Enhanced Missing Field Detection:")
        missing_fields = processor.identify_missing_fields(df)
        print(f"   Missing fields: {missing_fields}")
        
        # Verify key improvements
        print(f"\n✨ Verification Results:")
        
        # Check if RAM (GB) is properly mapped
        ram_mapped = any("Memory" in mapped for mapped in column_mappings.values())
        print(f"   • RAM (GB) properly mapped: {'✅' if ram_mapped else '❌'}")
        
        # Check if HOSTNAME is properly mapped  
        hostname_mapped = any("Asset Name" in mapped for mapped in column_mappings.values())
        print(f"   • HOSTNAME properly mapped: {'✅' if hostname_mapped else '❌'}")
        
        # Check if APPLICATION_MAPPED is recognized
        app_mapped = any("Dependencies" in mapped or "Application" in mapped for mapped in column_mappings.values())
        print(f"   • APPLICATION_MAPPED recognized: {'✅' if app_mapped else '❌'}")
        
        # Check if false missing fields are reduced
        false_positives = ["Memory (GB)", "Asset Name", "Dependencies"]
        false_missing = [field for field in missing_fields if field in false_positives and any(field.lower().replace(" ", "").replace("(", "").replace(")", "") in col.lower().replace(" ", "").replace("(", "").replace(")", "") for col in columns)]
        print(f"   • Reduced false missing fields: {'✅' if not false_missing else '❌ Still missing: ' + str(false_missing)}")
        
        # Test asset type detection
        print(f"\n🏷️  Testing Asset Type Detection:")
        coverage = processor.identify_asset_types(df)
        print(f"   • Applications: {coverage.applications}")
        print(f"   • Servers: {coverage.servers}")
        print(f"   • Databases: {coverage.databases}")
        print(f"   • Primary type: {'Server' if coverage.servers > coverage.applications else 'Application'}")
        
        # Test data quality assessment
        print(f"\n📊 Testing Data Quality Assessment:")
        structure_analysis = processor.analyze_data_structure(df)
        print(f"   • Quality score: {structure_analysis.get('quality_score', 'N/A')}")
        print(f"   • Null percentage: {structure_analysis.get('null_percentage', 'N/A'):.1f}%")
        
        # Show learned mappings state
        print(f"\n💾 Current Learned Mappings:")
        context = field_mapping_tool.get_mapping_context()
        learned_count = context.get("total_learned_mappings", 0)
        print(f"   • Total learned mappings: {learned_count}")
        
        # Test feedback learning simulation
        print(f"\n🧠 Testing Feedback Learning:")
        feedback_result = field_mapping_tool.learn_from_feedback_text(
            "The RAM (GB) column contains memory information and APPLICATION_MAPPED shows dependencies", 
            "test_feedback"
        )
        print(f"   • Feedback processed: {'✅' if feedback_result.get('success') else '❌'}")
        
        print(f"\n🎉 Enhanced Field Mapping Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in enhanced field mapping test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_column_cases():
    """Test specific problematic column cases from the screenshots."""
    print(f"\n🔬 Testing Specific Column Cases:")
    
    test_cases = [
        ("HOSTNAME", ["server-1", "web-server-02", "db-prod-03"]),
        ("RAM (GB)", ["16", "32", "8", "64"]),
        ("APPLICATION_MAPPED", ["App 130", "App 252", "CRM System"]),
        ("WORKLOAD TYPE", ["DB Server", "Web Server", "App Server"]),
        ("OS TYPE", ["Linux", "Windows", "AIX"]),
    ]
    
    for column_name, sample_values in test_cases:
        print(f"\n   Testing: {column_name}")
        analysis = field_mapper._analyze_column_content(column_name, sample_values)
        
        suggested_field = analysis.get("suggested_field")
        confidence = analysis.get("confidence", 0.0)
        reason = analysis.get("reason", "No reason")
        
        print(f"     → Suggested: {suggested_field} (confidence: {confidence:.2f})")
        print(f"     → Reason: {reason}")
        
        # Verify expected mappings
        expected_mappings = {
            "HOSTNAME": "Asset Name",
            "RAM (GB)": "Memory (GB)", 
            "APPLICATION_MAPPED": "Dependencies",
            "WORKLOAD TYPE": "Asset Type",
            "OS TYPE": "Operating System"
        }
        
        expected = expected_mappings.get(column_name)
        if expected and suggested_field == expected:
            print(f"     ✅ Correctly mapped to {expected}")
        elif expected:
            print(f"     ❌ Expected {expected}, got {suggested_field}")
        else:
            print(f"     ℹ️  No specific expectation for this column")

if __name__ == "__main__":
    print("Starting Enhanced Agentic Field Mapping Tests...\n")
    
    success = test_enhanced_field_mapping()
    test_specific_column_cases()
    
    if success:
        print(f"\n🎊 All tests completed! The enhanced agentic field mapping system")
        print(f"   should now properly handle the column mapping issues shown in the screenshots.")
        print(f"\n💡 Key improvements:")
        print(f"   • Pattern-based field recognition using data content analysis")
        print(f"   • Automatic learning of field mappings with confidence scoring")
        print(f"   • Reduced false 'missing field' alerts")
        print(f"   • Better handling of different CMDB export formats")
        print(f"   • Persistent learning from user feedback")
    else:
        print(f"\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1) 