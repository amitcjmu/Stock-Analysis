#!/usr/bin/env python3
"""
Test Fallback Analysis
"""

import asyncio

from app.services.agents.intelligent_flow_agent import IntelligentFlowAgent


async def test_fallback_analysis():
    agent = IntelligentFlowAgent()
    
    flow_id = '23678d88-f4bd-49f4-bca8-b93c7b2b9ef2'
    
    print(f'Testing _fallback_analysis with flow_id: {flow_id}')
    
    try:
        result = await agent._fallback_analysis(
            flow_id=flow_id,
            client_account_id='21990f3a-abb6-4862-be06-cb6f854e167b',
            engagement_id='58467010-6a72-44e8-ba37-cc0238724455',
            user_id='77b30e13-c331-40eb-a0ec-ed0717f72b22'
        )
        
        print('\n✅ Fallback analysis result:')
        print(f'   Success: {result.success}')
        print(f'   Flow ID: {result.flow_id}')
        print(f'   Flow Type: {result.flow_type}')
        print(f'   Current Phase: {result.current_phase}')
        print(f'   Routing Decision: {result.routing_decision}')
        print(f'   User Guidance: {result.user_guidance}')
        print(f'   Confidence: {result.confidence}')
        
        if result.current_phase != 'not_found':
            print('🎉 SUCCESS: Fallback analysis now finds the flow!')
            return True
        else:
            print('❌ Fallback analysis still returning not_found')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_fallback_analysis())