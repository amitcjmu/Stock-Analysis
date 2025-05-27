#!/usr/bin/env python3
"""
Comprehensive test suite for the CrewAI Agentic System.
Tests all components including memory, agents, crews, and learning.
"""

import sys
import os
import asyncio
import tempfile
import shutil
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.crewai_service import CrewAIService
from app.services.memory import AgentMemory
from app.services.agents import AgentManager
from app.services.analysis import IntelligentAnalyzer, PlaceholderAnalyzer
from app.services.feedback import FeedbackProcessor


class TestCrewAISystem:
    """Comprehensive test suite for the CrewAI agentic system."""
    
    def __init__(self):
        self.temp_dir = None
        self.memory = None
        self.service = None
    
    def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        print(f"   Created temp directory: {self.temp_dir}")
        
        # Initialize memory with temp directory
        self.memory = AgentMemory(data_dir=self.temp_dir)
        print("   ✅ Memory system initialized")
        
        # Initialize CrewAI service
        self.service = CrewAIService()
        print("   ✅ CrewAI service initialized")
    
    def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up test environment...")
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("   ✅ Temporary directory cleaned up")
    
    def test_memory_system(self):
        """Test the agent memory system."""
        print("\n🧠 Testing Agent Memory System")
        print("-" * 40)
        
        # Test adding experiences
        test_experience = {
            "filename": "test_cmdb.csv",
            "asset_type_detected": "server",
            "confidence": 0.85
        }
        
        self.memory.add_experience("analysis_attempt", test_experience)
        print("   ✅ Experience added successfully")
        
        # Test retrieving experiences
        experiences = self.memory.get_relevant_experiences("test_cmdb.csv")
        assert len(experiences) > 0, "Should retrieve relevant experiences"
        print(f"   ✅ Retrieved {len(experiences)} relevant experiences")
        
        # Test memory statistics
        stats = self.memory.get_memory_stats()
        assert stats["total_experiences"] > 0, "Should have experiences"
        print(f"   ✅ Memory stats: {stats['total_experiences']} total experiences")
        
        # Test learning metrics
        self.memory.update_learning_metrics("total_analyses", 1)
        assert self.memory.learning_metrics["total_analyses"] == 1
        print("   ✅ Learning metrics updated successfully")
        
        return True
    
    def test_agent_manager(self):
        """Test the agent manager."""
        print("\n🤖 Testing Agent Manager")
        print("-" * 40)
        
        # Test agent manager initialization
        agent_manager = AgentManager(llm=None)  # Test without LLM
        print("   ✅ Agent manager initialized")
        
        # Test agent listing
        agents = agent_manager.list_agents()
        print(f"   ✅ Found {len(agents)} agents: {list(agents.keys())}")
        
        # Test crew listing
        crews = agent_manager.list_crews()
        print(f"   ✅ Found {len(crews)} crews: {list(crews.keys())}")
        
        # Test agent capabilities
        capabilities = agent_manager.get_agent_capabilities()
        print(f"   ✅ Agent capabilities defined for {len(capabilities)} agents")
        
        # Test system status
        status = agent_manager.get_system_status()
        print(f"   ✅ System status: CrewAI available = {status['crewai_available']}")
        
        return True
    
    def test_intelligent_analyzer(self):
        """Test the intelligent analyzer."""
        print("\n🔍 Testing Intelligent Analyzer")
        print("-" * 40)
        
        analyzer = IntelligentAnalyzer(self.memory)
        
        # Test data
        test_cmdb_data = {
            "filename": "test_servers.csv",
            "structure": {
                "columns": ["Name", "CI_Type", "IP_Address", "OS", "CPU_Cores", "Memory_GB"],
                "row_count": 50
            },
            "sample_data": [
                {"Name": "WebServer01", "CI_Type": "Server", "IP_Address": "192.168.1.10", "OS": "Linux"},
                {"Name": "AppServer02", "CI_Type": "Server", "IP_Address": "192.168.1.11", "OS": "Windows"}
            ]
        }
        
        # Test intelligent analysis
        result = analyzer.intelligent_placeholder_analysis(test_cmdb_data)
        
        assert "asset_type_detected" in result
        assert "confidence_level" in result
        assert "data_quality_score" in result
        assert result["fallback_mode"] is True
        
        print(f"   ✅ Asset type detected: {result['asset_type_detected']}")
        print(f"   ✅ Confidence level: {result['confidence_level']:.2f}")
        print(f"   ✅ Quality score: {result['data_quality_score']}")
        print(f"   ✅ Missing fields: {len(result['missing_fields_relevant'])}")
        
        return True
    
    def test_feedback_processor(self):
        """Test the feedback processor."""
        print("\n📝 Testing Feedback Processor")
        print("-" * 40)
        
        processor = FeedbackProcessor(self.memory)
        
        # Test feedback data
        feedback_data = {
            "filename": "test_cmdb.csv",
            "user_corrections": {
                "analysis_issues": "These are servers, not applications. CI_TYPE field clearly indicates Server.",
                "missing_fields_feedback": "IP Address and OS Version are required for servers.",
                "comments": "Please improve server detection logic."
            },
            "asset_type_override": "server",
            "original_analysis": {
                "asset_type_detected": "application",
                "confidence_level": 0.75
            }
        }
        
        # Test feedback processing
        result = processor.intelligent_feedback_processing(feedback_data)
        
        assert result["learning_applied"] is True
        assert len(result["patterns_identified"]) > 0
        assert len(result["knowledge_updates"]) > 0
        assert result["confidence_boost"] > 0
        
        print(f"   ✅ Learning applied: {result['learning_applied']}")
        print(f"   ✅ Patterns identified: {len(result['patterns_identified'])}")
        print(f"   ✅ Knowledge updates: {len(result['knowledge_updates'])}")
        print(f"   ✅ Confidence boost: {result['confidence_boost']:.2f}")
        
        # Test feedback trends
        trends = processor.analyze_feedback_trends()
        print(f"   ✅ Feedback trends analyzed: {trends['total_feedback']} feedback items")
        
        return True
    
    def test_placeholder_analyzers(self):
        """Test placeholder analyzers."""
        print("\n📊 Testing Placeholder Analyzers")
        print("-" * 40)
        
        # Test 6R analysis
        asset_data = {
            "name": "WebApp01",
            "asset_type": "application",
            "business_criticality": "high"
        }
        
        result_6r = PlaceholderAnalyzer.placeholder_6r_analysis(asset_data)
        assert "recommended_strategy" in result_6r
        assert result_6r["placeholder_mode"] is True
        print(f"   ✅ 6R Analysis: {result_6r['recommended_strategy']} strategy recommended")
        
        # Test risk assessment
        migration_data = {
            "total_assets": 150,
            "timeline_days": 60
        }
        
        result_risk = PlaceholderAnalyzer.placeholder_risk_assessment(migration_data)
        assert "overall_risk_level" in result_risk
        assert result_risk["placeholder_mode"] is True
        print(f"   ✅ Risk Assessment: {result_risk['overall_risk_level']} risk level")
        
        # Test wave planning
        assets_data = [{"name": f"Asset{i}"} for i in range(100)]
        
        result_wave = PlaceholderAnalyzer.placeholder_wave_plan(assets_data)
        assert "total_waves" in result_wave
        assert result_wave["placeholder_mode"] is True
        print(f"   ✅ Wave Planning: {result_wave['total_waves']} waves planned")
        
        return True
    
    async def test_crewai_service(self):
        """Test the main CrewAI service."""
        print("\n🚀 Testing CrewAI Service")
        print("-" * 40)
        
        # Test CMDB analysis
        test_data = {
            "filename": "integration_test.csv",
            "structure": {
                "columns": ["Name", "Type", "Environment", "CPU", "Memory"],
                "row_count": 25
            },
            "sample_data": [
                {"Name": "TestApp", "Type": "Application", "Environment": "Prod"},
                {"Name": "TestServer", "Type": "Server", "Environment": "Prod"}
            ]
        }
        
        result = await self.service.analyze_cmdb_data(test_data)
        
        assert "asset_type_detected" in result
        assert "confidence_level" in result
        print(f"   ✅ CMDB Analysis completed: {result['asset_type_detected']}")
        
        # Test feedback processing
        feedback_data = {
            "filename": "integration_test.csv",
            "user_corrections": {
                "analysis_issues": "Mixed asset types need better classification"
            },
            "original_analysis": result
        }
        
        feedback_result = await self.service.process_user_feedback(feedback_data)
        assert "learning_applied" in feedback_result
        print(f"   ✅ Feedback processed: {feedback_result['learning_applied']}")
        
        # Test 6R analysis
        asset_data = {
            "name": "TestAsset",
            "asset_type": "application",
            "business_criticality": "medium"
        }
        
        strategy_result = await self.service.analyze_asset_6r_strategy(asset_data)
        assert "recommended_strategy" in strategy_result
        print(f"   ✅ 6R Strategy: {strategy_result.get('recommended_strategy', 'N/A')}")
        
        return True
    
    def test_memory_persistence(self):
        """Test memory persistence across sessions."""
        print("\n💾 Testing Memory Persistence")
        print("-" * 40)
        
        # Add some test data
        test_data = {
            "filename": "persistence_test.csv",
            "result": "test_result"
        }
        
        self.memory.add_experience("analysis_attempt", test_data)
        original_stats = self.memory.get_memory_stats()
        
        # Create new memory instance with same directory
        new_memory = AgentMemory(data_dir=self.temp_dir)
        new_stats = new_memory.get_memory_stats()
        
        assert new_stats["total_experiences"] == original_stats["total_experiences"]
        print("   ✅ Memory persisted across sessions")
        
        # Test memory export
        export_path = os.path.join(self.temp_dir, "memory_export.json")
        success = self.memory.export_memory(export_path)
        assert success and os.path.exists(export_path)
        print("   ✅ Memory exported successfully")
        
        return True
    
    def test_learning_effectiveness(self):
        """Test learning system effectiveness."""
        print("\n📈 Testing Learning Effectiveness")
        print("-" * 40)
        
        processor = FeedbackProcessor(self.memory)
        
        # Add multiple feedback instances
        for i in range(3):
            feedback_data = {
                "filename": f"learning_test_{i}.csv",
                "user_corrections": {
                    "analysis_issues": f"Test issue {i}",
                    "missing_fields_feedback": "Test field feedback"
                },
                "asset_type_override": "server"
            }
            
            processor.intelligent_feedback_processing(feedback_data)
        
        # Test learning effectiveness
        effectiveness = processor.get_learning_effectiveness()
        
        assert effectiveness["total_feedback_processed"] == 3
        assert effectiveness["patterns_learned"] > 0
        print(f"   ✅ Learning effectiveness: {effectiveness['learning_quality']}")
        print(f"   ✅ Patterns per feedback: {effectiveness['patterns_per_feedback']:.2f}")
        
        return True
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("🧪 Starting Comprehensive CrewAI System Tests")
        print("=" * 60)
        
        try:
            self.setup()
            
            # Run all tests
            tests = [
                ("Memory System", self.test_memory_system),
                ("Agent Manager", self.test_agent_manager),
                ("Intelligent Analyzer", self.test_intelligent_analyzer),
                ("Feedback Processor", self.test_feedback_processor),
                ("Placeholder Analyzers", self.test_placeholder_analyzers),
                ("CrewAI Service", self.test_crewai_service),
                ("Memory Persistence", self.test_memory_persistence),
                ("Learning Effectiveness", self.test_learning_effectiveness)
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                try:
                    if asyncio.iscoroutinefunction(test_func):
                        result = await test_func()
                    else:
                        result = test_func()
                    
                    if result:
                        passed += 1
                        print(f"✅ {test_name} - PASSED")
                    else:
                        failed += 1
                        print(f"❌ {test_name} - FAILED")
                        
                except Exception as e:
                    failed += 1
                    print(f"❌ {test_name} - ERROR: {e}")
            
            # Print summary
            print("\n" + "=" * 60)
            print("🏁 Test Summary")
            print(f"   ✅ Passed: {passed}")
            print(f"   ❌ Failed: {failed}")
            print(f"   📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
            
            if failed == 0:
                print("\n🎉 All tests passed! The agentic system is working correctly.")
            else:
                print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
            
            return failed == 0
            
        finally:
            self.teardown()


async def main():
    """Main test runner."""
    tester = TestCrewAISystem()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 