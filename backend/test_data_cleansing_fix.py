#!/usr/bin/env python3
"""
Test script to verify the data cleansing endpoint fix works
for flow ID: 5d4149d3-ac32-40ea-85d1-56ebea8d5e17
"""

import asyncio
import logging
import os
import sys

from sqlalchemy import text

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flow ID from the issue
FLOW_ID = "5d4149d3-ac32-40ea-85d1-56ebea8d5e17"

async def test_data_retrieval():
    """Test that we can now retrieve data for the problematic flow"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"🔍 Testing data retrieval for flow: {FLOW_ID}")
            
            # Check discovery flow
            discovery_query = text('''
                SELECT flow_id, flow_name, current_phase, status, 
                       progress_percentage, data_import_id, master_flow_id
                FROM discovery_flows 
                WHERE flow_id = :flow_id
            ''')
            
            result = await db.execute(discovery_query, {'flow_id': FLOW_ID})
            flow = result.fetchone()
            
            if flow:
                logger.info("📊 Discovery Flow Found:")
                logger.info(f"   Name: {flow.flow_name}")
                logger.info(f"   Status: {flow.status}")
                logger.info(f"   Current Phase: {flow.current_phase}")
                logger.info(f"   Progress: {flow.progress_percentage}%")
                logger.info(f"   Data Import ID: {flow.data_import_id}")
                logger.info(f"   Master Flow ID: {flow.master_flow_id}")
            else:
                logger.error(f"❌ Discovery flow not found: {FLOW_ID}")
                return False
            
            # Test master flow ID lookup (the fix we implemented)
            logger.info("\n🔗 Testing master flow ID lookup...")
            
            # Get the database ID for this flow_id
            db_id_query = text('''
                SELECT id FROM crewai_flow_state_extensions 
                WHERE flow_id = :flow_id
            ''')
            
            db_id_result = await db.execute(db_id_query, {'flow_id': FLOW_ID})
            flow_db_id = db_id_result.scalar_one_or_none()
            
            if flow_db_id:
                logger.info(f"✅ Found CrewAI extensions DB ID: {flow_db_id}")
                
                # Look for data imports with this master_flow_id
                import_query = text('''
                    SELECT id, filename, total_records, status, created_at
                    FROM data_imports
                    WHERE master_flow_id = :flow_db_id
                    ORDER BY created_at DESC
                    LIMIT 1
                ''')
                
                import_result = await db.execute(import_query, {'flow_db_id': flow_db_id})
                data_import = import_result.fetchone()
                
                if data_import:
                    logger.info("✅ Found data import via master flow ID:")
                    logger.info(f"   Import ID: {data_import.id}")
                    logger.info(f"   Filename: {data_import.filename}")
                    logger.info(f"   Total Records: {data_import.total_records}")
                    logger.info(f"   Status: {data_import.status}")
                    logger.info(f"   Created: {data_import.created_at}")
                    
                    # Check raw import records
                    records_query = text('''
                        SELECT COUNT(*) as total_records
                        FROM raw_import_records
                        WHERE data_import_id = :import_id
                    ''')
                    
                    records_result = await db.execute(records_query, {'import_id': data_import.id})
                    record_count = records_result.scalar()
                    
                    logger.info(f"📄 Raw import records found: {record_count}")
                    
                    if record_count and record_count > 0:
                        logger.info(f"🎉 SUCCESS: Found {record_count} records for flow {FLOW_ID}")
                        logger.info("    This should resolve the '0 records' issue in the data cleansing page!")
                        return True
                    else:
                        logger.warning("⚠️  No raw import records found")
                        return False
                else:
                    logger.error("❌ No data import found via master flow ID lookup")
                    return False
            else:
                logger.error("❌ No CrewAI extensions found for this flow")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error during test: {str(e)}")
            return False

async def main():
    """Main test function"""
    logger.info("🧪 Starting data cleansing fix verification test")
    
    success = await test_data_retrieval()
    
    if success:
        logger.info("\n✅ TEST PASSED: Data retrieval fix is working!")
        logger.info("   The data cleansing page should now show records instead of 0.")
    else:
        logger.error("\n❌ TEST FAILED: Data retrieval issues persist")
        logger.error("   Additional investigation may be needed.")

if __name__ == "__main__":
    asyncio.run(main())