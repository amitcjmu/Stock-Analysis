#!/usr/bin/env python3
"""
Test Field Mappings Script

This script triggers the asset creation process to capture debug logs
and identify where field mapping application fails.

Usage:
    python test_field_mappings.py --flow-id <flow_id>
"""

import asyncio
import sys
import os
import argparse
import logging

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db')

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.core.database import get_db
from app.models.discovery_flow import DiscoveryFlow
from app.services.flow_orchestration.execution_engine_crew_discovery import ExecutionEngineDiscoveryCrews
from app.core.context import RequestContext
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from sqlalchemy import select


async def test_field_mappings(flow_id: str):
    """Test field mapping application by triggering asset creation"""
    
    async for db in get_db():
        try:
            print(f"🧪 Testing field mappings for flow: {flow_id}")
            print("=" * 50)
            
            # Find the discovery flow
            flow_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
            flow_result = await db.execute(flow_query)
            discovery_flow = flow_result.scalar_one_or_none()
            
            if not discovery_flow:
                print(f"❌ No discovery flow found for flow_id: {flow_id}")
                return
            
            print(f"✅ Found discovery flow: {discovery_flow.flow_name}")
            print(f"   Data import ID: {discovery_flow.data_import_id}")
            print(f"   Current phase: {discovery_flow.current_phase}")
            
            # Create context
            context = RequestContext(
                client_account_id='11111111-1111-1111-1111-111111111111',
                engagement_id='22222222-2222-2222-2222-222222222222',
                user_id='33333333-3333-3333-3333-333333333333',
                flow_id=flow_id
            )
            
            # Initialize the execution engine
            execution_engine = ExecutionEngineDiscoveryCrews(db, context)
            
            # Prepare phase input
            phase_input = {
                "master_flow_id": flow_id,
                "data_import_id": str(discovery_flow.data_import_id),
                "flow_name": discovery_flow.flow_name
            }
            
            print(f"\n🚀 Triggering asset inventory phase execution...")
            print(f"   Phase input: {phase_input}")
            
            # Execute the asset inventory phase
            agent_pool = {}  # Empty agent pool for testing
            result = await execution_engine._execute_discovery_asset_inventory(agent_pool, phase_input)
            
            print(f"\n✅ Execution completed!")
            print(f"   Result: {result}")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
        
        break


async def main():
    parser = argparse.ArgumentParser(description='Test field mapping application')
    parser.add_argument('--flow-id', required=True, help='Flow ID to test')
    
    args = parser.parse_args()
    
    await test_field_mappings(args.flow_id)


if __name__ == "__main__":
    asyncio.run(main())


