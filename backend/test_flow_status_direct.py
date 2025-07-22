#!/usr/bin/env python3
"""
Direct test of flow status to bypass all caching and complexity
"""

import asyncio
import json

from app.services.agents.intelligent_flow_agent import IntelligentFlowAgent


async def test_flow_status_direct():
    agent = IntelligentFlowAgent()
    
    flow_id = '23678d88-f4bd-49f4-bca8-b93c7b2b9ef2'
    
    print('🔍 Testing direct IntelligentFlowAgent...')
    print(f'   Flow ID: {flow_id}')
    
    result = await agent.analyze_flow_continuation(
        flow_id=flow_id,
        client_account_id='21990f3a-abb6-4862-be06-cb6f854e167b',
        engagement_id='58467010-6a72-44e8-ba37-cc0238724455',
        user_id='77b30e13-c331-40eb-a0ec-ed0717f72b22'
    )
    
    print('📊 DIRECT AGENT RESULT:')
    print(f'   Success: {result.success}')
    print(f'   Current Phase: {result.current_phase}')
    print(f'   User Guidance: {result.user_guidance}')
    print(f'   Routing Decision: {result.routing_decision}')
    print(f'   Confidence: {result.confidence}')
    
    if result.current_phase == 'not_found':
        print('❌ STILL RETURNING NOT_FOUND!')
        return False
    else:
        print('✅ SUCCESS: Found the flow!')
        return True

if __name__ == '__main__':
    result = asyncio.run(test_flow_status_direct())
    exit(0 if result else 1)