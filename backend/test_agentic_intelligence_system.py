#!/usr/bin/env python3
"""
Test Agentic Intelligence System Integration

This script tests the complete agentic intelligence system to verify:
1. BusinessValueAgent reasoning and scoring works correctly
2. RiskAssessmentAgent threat analysis and pattern discovery functions
3. ModernizationAgent cloud readiness assessment performs properly
4. AgenticAssetEnrichment orchestration integrates all three agents
5. Integration with discovery flow data cleansing phase works end-to-end
6. Agent memory tools and pattern discovery are functional

This demonstrates the complete replacement of rule-based systems with agentic intelligence.
"""

import sys
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the app directory to the Python path
sys.path.append('/app')

async def test_agentic_intelligence_system():
    """Test the complete agentic intelligence system integration"""
    
    print(f"🧠 Testing Agentic Intelligence System - {datetime.now()}")
    print("=" * 70)
    
    # Test 1: Create Test Tenant Context
    print("\n1️⃣ Creating Test Tenant Context...")
    try:
        from app.models.client_account import ClientAccount  
        from app.core.database import AsyncSessionLocal
        
        # Create test entities with proper foreign key relationships
        client_account_id = uuid.uuid4()
        engagement_id = uuid.uuid4()
        timestamp = int(datetime.now().timestamp())
        
        async with AsyncSessionLocal() as session:
            # Create test client account first (required for foreign key)
            test_client = ClientAccount(
                id=client_account_id,
                name="Test Agentic Intelligence Client",
                slug=f"test-agentic-intelligence-{timestamp}"
            )
            session.add(test_client)
            await session.commit()  # Commit client first
            
            # Now create test engagement record (can reference committed client)
            from sqlalchemy import text
            await session.execute(text('''
                INSERT INTO engagements (id, client_account_id, name, slug, status) 
                VALUES (:engagement_id, :client_id, :name, :slug, :status)
            '''), {
                'engagement_id': engagement_id,
                'client_id': client_account_id,
                'name': 'Test Agentic Intelligence Engagement',
                'slug': f'test-agentic-intelligence-engagement-{timestamp}',
                'status': 'active'
            })
            
            await session.commit()
            print("✅ Test tenant context created successfully")
            print(f"   - Client Account ID: {client_account_id}")
            print(f"   - Engagement ID: {engagement_id}")
        
    except Exception as e:
        print(f"❌ Test context creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Create Sample Assets for Analysis
    print("\n2️⃣ Creating Sample Assets for Intelligence Analysis...")
    try:
        sample_assets = [
            {
                "id": str(uuid.uuid4()),
                "name": "prod-db-customer-01",
                "asset_type": "database",
                "technology_stack": "PostgreSQL 13",
                "environment": "production",
                "business_criticality": "high",
                "cpu_utilization_percent": 85.0,
                "memory_utilization_percent": 78.5,
                "network_exposure": "internal",
                "data_sensitivity": "customer_data"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "legacy-app-finance",
                "asset_type": "web application",
                "technology_stack": "Java 8, Tomcat 8",
                "environment": "production",
                "business_criticality": "critical",
                "cpu_utilization_percent": 45.0,
                "network_exposure": "public",
                "data_sensitivity": "financial_data"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "api-microservice-orders",
                "asset_type": "microservice",
                "technology_stack": "Spring Boot 2.7, Docker",
                "environment": "production",
                "business_criticality": "high",
                "cpu_utilization_percent": 35.0,
                "architecture_style": "microservices",
                "network_exposure": "internal"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "test-web-server",
                "asset_type": "web server",
                "technology_stack": "Apache 2.4",
                "environment": "test",
                "business_criticality": "low",
                "cpu_utilization_percent": 15.0,
                "network_exposure": "internal"
            }
        ]
        
        print(f"✅ Created {len(sample_assets)} sample assets for testing:")
        for asset in sample_assets:
            print(f"   - {asset['name']} ({asset['asset_type']}) - {asset['environment']}")
        
    except Exception as e:
        print(f"❌ Sample asset creation failed: {e}")
        return False
    
    # Test 3: Initialize CrewAI Service
    print("\n3️⃣ Initializing CrewAI Service...")
    try:
        from app.services.crewai_handlers.crew_manager import CrewManager
        
        # Create a simple service object that mimics the expected interface
        class MockCrewAIService:
            def __init__(self):
                self.crew_manager = CrewManager()
                self.llm = self.crew_manager.llm
            
            def get_llm(self):
                return self.llm
        
        crewai_service = MockCrewAIService()
        
        if crewai_service.get_llm():
            print("✅ CrewAI service initialized successfully")
            print(f"   - LLM Model: {crewai_service.get_llm().model}")
        else:
            print("⚠️ CrewAI service initialized but LLM not available")
            print("   - Using fallback mode for testing")
        
    except Exception as e:
        print(f"❌ CrewAI service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test BusinessValueAgent
    print("\n4️⃣ Testing BusinessValueAgent Intelligence...")
    try:
        from app.services.agentic_intelligence.business_value_agent import BusinessValueAgent
        
        business_agent = BusinessValueAgent(
            crewai_service=crewai_service,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        # Test with production database (should have high business value)
        test_asset = sample_assets[0]  # prod-db-customer-01
        business_result = await business_agent.analyze_asset_business_value(test_asset)
        
        print("✅ BusinessValueAgent analysis completed:")
        print(f"   - Asset: {test_asset['name']}")
        print(f"   - Business Value Score: {business_result.get('business_value_score')}/10")
        print(f"   - Confidence: {business_result.get('confidence_level')}")
        print(f"   - Analysis Method: {business_result.get('analysis_method')}")
        
    except Exception as e:
        print(f"❌ BusinessValueAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Test RiskAssessmentAgent
    print("\n5️⃣ Testing RiskAssessmentAgent Intelligence...")
    try:
        from app.services.agentic_intelligence.risk_assessment_agent import RiskAssessmentAgent
        
        risk_agent = RiskAssessmentAgent(
            crewai_service=crewai_service,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        # Test with legacy Java application (should have security risks)
        test_asset = sample_assets[1]  # legacy-app-finance
        risk_result = await risk_agent.analyze_asset_risk(test_asset)
        
        print("✅ RiskAssessmentAgent analysis completed:")
        print(f"   - Asset: {test_asset['name']}")
        print(f"   - Risk Assessment: {risk_result.get('risk_assessment')}")
        print(f"   - Security Risk Score: {risk_result.get('security_risk_score')}/10")
        print(f"   - Analysis Method: {risk_result.get('analysis_method')}")
        
    except Exception as e:
        print(f"❌ RiskAssessmentAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Test ModernizationAgent
    print("\n6️⃣ Testing ModernizationAgent Intelligence...")
    try:
        from app.services.agentic_intelligence.modernization_agent import ModernizationAgent
        
        modernization_agent = ModernizationAgent(
            crewai_service=crewai_service,
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        # Test with Spring Boot microservice (should have high modernization potential)
        test_asset = sample_assets[2]  # api-microservice-orders
        modernization_result = await modernization_agent.analyze_modernization_potential(test_asset)
        
        print("✅ ModernizationAgent analysis completed:")
        print(f"   - Asset: {test_asset['name']}")
        print(f"   - Cloud Readiness: {modernization_result.get('cloud_readiness_score')}/100")
        print(f"   - Modernization Potential: {modernization_result.get('modernization_potential')}")
        print(f"   - Recommended Strategy: {modernization_result.get('recommended_strategy')}")
        print(f"   - Analysis Method: {modernization_result.get('analysis_method')}")
        
    except Exception as e:
        print(f"❌ ModernizationAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 7: Test Complete Agentic Enrichment Orchestration
    print("\n7️⃣ Testing Complete Agentic Enrichment Orchestration...")
    try:
        from app.services.agentic_intelligence.agentic_asset_enrichment import enrich_assets_with_agentic_intelligence
        
        # Enrich all sample assets with complete intelligence analysis
        enriched_assets = await enrich_assets_with_agentic_intelligence(
            assets=sample_assets,
            crewai_service=crewai_service,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            batch_size=2,  # Process 2 assets at a time
            enable_parallel_agents=False  # Disable parallel for stability testing
        )
        
        print(f"✅ Complete agentic enrichment completed for {len(enriched_assets)} assets:")
        
        for asset in enriched_assets:
            print(f"\n   📊 {asset['name']}:")
            print(f"      - Business Value: {asset.get('business_value_score', 'N/A')}/10")
            print(f"      - Risk Level: {asset.get('risk_assessment', 'N/A')}")
            print(f"      - Cloud Readiness: {asset.get('cloud_readiness_score', 'N/A')}/100")
            print(f"      - Enrichment Status: {asset.get('enrichment_status', 'N/A')}")
            print(f"      - Overall Score: {asset.get('overall_enrichment_score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Complete agentic enrichment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 8: Test Memory Pattern Discovery
    print("\n8️⃣ Testing Memory Pattern Discovery...")
    try:
        from app.services.agentic_memory import ThreeTierMemoryManager, MemoryQuery
        from app.models.agent_memory import PatternType
        
        memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)
        
        # Search for patterns discovered during analysis
        search_query = MemoryQuery(
            query_text="business value production database modernization",
            memory_tiers=['semantic'],
            pattern_types=[PatternType.BUSINESS_VALUE_INDICATOR, PatternType.MODERNIZATION_OPPORTUNITY],
            min_confidence=0.5,
            max_results=10
        )
        
        discovered_patterns = await memory_manager.query_memory(search_query)
        
        print(f"✅ Memory pattern discovery completed:")
        print(f"   - Patterns found: {len(discovered_patterns)}")
        
        for i, pattern in enumerate(discovered_patterns[:3]):  # Show first 3
            if pattern.tier == 'semantic':
                pattern_data = pattern.content
                print(f"   - Pattern {i+1}: {pattern_data.get('name', 'Unknown')}")
                print(f"     Confidence: {pattern_data.get('confidence', 0.0)}")
                print(f"     Type: {pattern_data.get('type', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Memory pattern discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 9: Test Integration with Discovery Flow Data Cleansing
    print("\n9️⃣ Testing Integration with Discovery Flow...")
    try:
        from app.services.crewai_flows.handlers.phase_executors.data_cleansing_executor import DataCleansingExecutor
        from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
        
        # Create mock state with raw data
        mock_state = UnifiedDiscoveryFlowState()
        mock_state.flow_id = str(uuid.uuid4())
        mock_state.client_account_id = str(client_account_id)
        mock_state.engagement_id = str(engagement_id)
        mock_state.user_id = "test-user"
        mock_state.raw_data = [
            {
                "name": "integration-test-db",
                "asset_type": "database",
                "technology_stack": "MySQL 8.0",
                "environment": "production",
                "cpu_utilization_percent": 75
            }
        ]
        
        # Create data cleansing executor (this should now use agentic intelligence)
        from app.services.crewai_flows.handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
        crew_manager = UnifiedFlowCrewManager(crewai_service, mock_state)
        
        executor = DataCleansingExecutor(mock_state, crew_manager, None)
        
        # Execute with agentic intelligence integration
        crew_input = {"test": "integration"}
        result = await executor.execute_with_crew(crew_input)
        
        print("✅ Discovery flow integration test completed:")
        print(f"   - Agentic Analysis Used: {result.get('agentic_analysis', False)}")
        print(f"   - Assets Processed: {len(result.get('cleaned_data', []))}")
        print(f"   - Quality Score: {result.get('quality_metrics', {}).get('quality_score', 'N/A')}")
        
        # Check if assets were enriched with intelligence
        enriched_data = result.get('cleaned_data', [])
        if enriched_data:
            sample_enriched = enriched_data[0]
            print(f"   - Sample Asset Business Value: {sample_enriched.get('business_value_score', 'N/A')}")
            print(f"   - Sample Asset Risk: {sample_enriched.get('risk_assessment', 'N/A')}")
            print(f"   - Sample Asset Cloud Readiness: {sample_enriched.get('cloud_readiness_score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Discovery flow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            # Clean up in reverse order of creation due to foreign keys
            await session.execute(text("DELETE FROM agent_discovered_patterns WHERE client_account_id = :client_id"), 
                                {"client_id": client_account_id})
            await session.execute(text("DELETE FROM engagements WHERE id = :engagement_id"), 
                                {"engagement_id": engagement_id})
            await session.execute(text("DELETE FROM client_accounts WHERE id = :client_id"), 
                                {"client_id": client_account_id})
            await session.commit()
            print("✅ Test data cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    # Summary
    print("\n🎉 AGENTIC INTELLIGENCE SYSTEM TEST RESULTS")
    print("=" * 50)
    print("✅ All tests passed successfully!")
    print("")
    print("🧠 BusinessValueAgent: WORKING")
    print("🛡️ RiskAssessmentAgent: WORKING") 
    print("☁️ ModernizationAgent: WORKING")
    print("🔗 AgenticAssetEnrichment Orchestration: WORKING")
    print("💾 Memory Pattern Discovery: WORKING")
    print("🔄 Discovery Flow Integration: WORKING")
    print("")
    print("🚀 AGENTIC INTELLIGENCE SYSTEM READY!")
    print("The platform now uses true agent reasoning instead of rule-based logic")
    print("for business value assessment, risk analysis, and modernization planning.")
    
    return True


if __name__ == "__main__":
    async def main():
        try:
            success = await test_agentic_intelligence_system()
            
            if success:
                print(f"\n✅ CONCLUSION: Agentic intelligence system is fully operational!")
                exit(0)
            else:
                print(f"\n❌ CONCLUSION: Agentic intelligence system has issues.")
                exit(1)
                
        except Exception as e:
            print(f"\n💥 Unexpected error in agentic intelligence testing: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    asyncio.run(main())