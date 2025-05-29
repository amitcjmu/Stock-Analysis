#!/usr/bin/env python3
"""
Simple test for CMDB analysis without CrewAI.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app.api.v1.discovery.processor import CMDBDataProcessor as processor
import pandas as pd
import io

def test_basic_analysis():
    """Test basic CMDB analysis without CrewAI."""
    print("🧪 Testing Basic CMDB Analysis (No CrewAI)")
    print("=" * 50)
    
    # Test data
    test_csv_content = """Name,CI_Type,Environment,CPU_Cores,Memory_GB,IP_Address
WebServer01,Server,Production,4,8,192.168.1.10
AppServer02,Server,Production,8,16,192.168.1.11
PaymentApp,Application,Production,,,
DatabaseSrv,Server,Production,16,32,192.168.1.12"""
    
    try:
        # Parse the CSV
        df = processor.parse_file_content(test_csv_content, 'text/csv')
        print(f"✅ Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
        print(f"   Columns: {list(df.columns)}")
        
        # Analyze structure
        structure = processor.analyze_data_structure(df)
        print(f"✅ Structure Analysis: Quality Score = {structure['quality_score']}")
        
        # Identify asset types
        coverage = processor.identify_asset_types(df)
        print(f"✅ Asset Coverage: Apps={coverage.applications}, Servers={coverage.servers}, DBs={coverage.databases}")
        
        # Identify missing fields
        missing_fields = processor.identify_missing_fields(df)
        print(f"✅ Missing Fields: {missing_fields}")
        
        # Suggest processing steps
        processing_steps = processor.suggest_processing_steps(df, structure)
        print(f"✅ Processing Steps: {len(processing_steps)} suggestions")
        
        print("\n🎉 Basic analysis completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in basic analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_analysis()
    exit(0 if success else 1) 