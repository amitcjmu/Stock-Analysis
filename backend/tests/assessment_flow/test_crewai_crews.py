"""
Unit tests for Assessment Flow CrewAI crews

This module tests the CrewAI crew implementations for assessment flow
with mocked agents for fast, isolated testing.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from app.services.crewai_flows.assessment.crews.app_on_page_crew import AppOnPageCrew
    from app.services.crewai_flows.assessment.crews.architecture_standards_crew import ArchitectureStandardsCrew
    from app.services.crewai_flows.assessment.crews.component_analysis_crew import ComponentAnalysisCrew
    from app.services.crewai_flows.assessment.crews.sixr_strategy_crew import SixRStrategyCrew
    CREWS_AVAILABLE = True
except ImportError:
    # Mock classes for when components don't exist yet
    CREWS_AVAILABLE = False
    
    class ArchitectureStandardsCrew:
        def __init__(self, flow_context):
            self.flow_context = flow_context
            self.crew = MagicMock()
    
    class ComponentAnalysisCrew:
        def __init__(self, flow_context):
            self.flow_context = flow_context
            self.crew = MagicMock()
    
    class SixRStrategyCrew:
        def __init__(self, flow_context):
            self.flow_context = flow_context
            self.crew = MagicMock()
    
    class AppOnPageCrew:
        def __init__(self, flow_context):
            self.flow_context = flow_context
            self.crew = MagicMock()



class TestArchitectureStandardsCrew:
    """Unit tests for Architecture Standards CrewAI crew"""
    
    @pytest.fixture
    def architecture_crew(self, mock_flow_context):
        """Create architecture standards crew with mocked context"""
        crew = ArchitectureStandardsCrew(mock_flow_context)
        crew.crew = MagicMock()
        return crew
    
    @pytest.mark.asyncio
    async def test_crew_execution_with_mocked_agents(
        self,
        architecture_crew,
        sample_engagement_context
    ):
        """Test crew execution with mocked agents"""
        
        mock_crew_result = {
            "engagement_standards": [
                {
                    "requirement_type": "java_versions",
                    "description": "Java version requirements",
                    "mandatory": True,
                    "supported_versions": {"java": "11+"},
                    "rationale": "Java 8 end of life"
                }
            ],
            "application_compliance": {
                "app-1": {
                    "compliance_score": 0.6,
                    "violations": [
                        {
                            "standard": "java_versions",
                            "current_value": "Java 8",
                            "required_value": "Java 11+",
                            "severity": "high"
                        }
                    ]
                }
            },
            "architecture_exceptions": [],
            "confidence_score": 0.9
        }
        
        architecture_crew.crew.kickoff = AsyncMock(return_value=mock_crew_result)
        
        result = await architecture_crew.execute({
            "engagement_context": sample_engagement_context,
            "selected_applications": ["app-1", "app-2"]
        })
        
        assert "engagement_standards" in result
        assert "application_compliance" in result
        assert result["crew_confidence"] == 0.9
        
        # Verify crew was called
        architecture_crew.crew.kickoff.assert_called_once()
        
        # Verify standards structure
        standards = result["engagement_standards"]
        assert len(standards) == 1
        java_standard = standards[0]
        assert java_standard["requirement_type"] == "java_versions"
        assert java_standard["mandatory"] is True
    
    @pytest.mark.asyncio
    async def test_crew_with_existing_standards(
        self,
        architecture_crew,
        sample_engagement_context,
        sample_architecture_standards
    ):
        """Test crew execution when engagement already has standards"""
        
        # Mock existing standards
        context_with_standards = {
            **sample_engagement_context,
            "existing_standards": sample_architecture_standards
        }
        
        mock_crew_result = {
            "engagement_standards": sample_architecture_standards,
            "standards_updated": False,
            "application_compliance": {},
            "confidence_score": 1.0
        }
        
        architecture_crew.crew.kickoff = AsyncMock(return_value=mock_crew_result)
        
        result = await architecture_crew.execute({
            "engagement_context": context_with_standards,
            "selected_applications": ["app-1"]
        })
        
        assert result["standards_updated"] is False
        assert len(result["engagement_standards"]) == 3
    
    @pytest.mark.asyncio
    async def test_crew_error_handling(
        self,
        architecture_crew,
        sample_engagement_context
    ):
        """Test crew error handling"""
        
        # Mock crew failure
        architecture_crew.crew.kickoff = AsyncMock(side_effect=Exception("Agent execution failed"))
        
        with pytest.raises(Exception) as exc_info:
            await architecture_crew.execute({
                "engagement_context": sample_engagement_context,
                "selected_applications": ["app-1"]
            })
        
        assert "Agent execution failed" in str(exc_info.value)


class TestComponentAnalysisCrew:
    """Unit tests for Component Analysis CrewAI crew"""
    
    @pytest.fixture
    def component_crew(self, mock_flow_context):
        """Create component analysis crew with mocked context"""
        crew = ComponentAnalysisCrew(mock_flow_context)
        crew.crew = MagicMock()
        return crew
    
    @pytest.mark.asyncio
    async def test_component_analysis_execution(
        self,
        component_crew,
        sample_application_metadata,
        sample_component_analysis_result
    ):
        """Test component analysis crew execution"""
        
        component_crew.crew.kickoff = AsyncMock(return_value=sample_component_analysis_result)
        
        result = await component_crew.execute({
            "applications": sample_application_metadata,
            "architecture_standards": [
                {"requirement_type": "java_versions", "supported_versions": {"java": "11+"}}
            ]
        })
        
        assert "components" in result
        assert "tech_debt_analysis" in result
        assert "component_scores" in result
        
        # Verify component analysis
        components = result["components"]
        assert len(components) == 3
        
        backend_component = next((c for c in components if c["name"] == "backend_api"), None)
        assert backend_component is not None
        assert backend_component["type"] == "api"
        assert backend_component["technology_stack"]["java"] == "8"
        
        # Verify tech debt analysis
        tech_debt = result["tech_debt_analysis"]
        assert len(tech_debt) == 2
        
        java_debt = next((t for t in tech_debt if t["category"] == "version_obsolescence"), None)
        assert java_debt is not None
        assert java_debt["severity"] == "high"
        assert java_debt["score"] == 8.5
    
    @pytest.mark.asyncio
    async def test_component_analysis_with_compliance_check(
        self,
        component_crew,
        sample_application_metadata
    ):
        """Test component analysis with architecture compliance checking"""
        
        mock_result_with_compliance = {
            "components": [
                {
                    "name": "backend_api",
                    "type": "api",
                    "technology_stack": {"java": "8"},
                    "compliance_violations": [
                        {
                            "standard": "java_versions",
                            "violation": "Java 8 below minimum 11+",
                            "severity": "high"
                        }
                    ]
                }
            ],
            "tech_debt_analysis": [],
            "component_scores": {"backend_api": 8.5},
            "compliance_summary": {
                "total_violations": 1,
                "high_severity_violations": 1
            }
        }
        
        component_crew.crew.kickoff = AsyncMock(return_value=mock_result_with_compliance)
        
        result = await component_crew.execute({
            "applications": sample_application_metadata,
            "architecture_standards": [
                {"requirement_type": "java_versions", "supported_versions": {"java": "11+"}}
            ]
        })
        
        # Verify compliance checking
        assert "compliance_summary" in result
        assert result["compliance_summary"]["total_violations"] == 1
        
        backend_component = result["components"][0]
        assert "compliance_violations" in backend_component
        assert len(backend_component["compliance_violations"]) == 1
    
    @pytest.mark.asyncio
    async def test_large_application_analysis(
        self,
        component_crew
    ):
        """Test component analysis with large number of applications"""
        
        # Create large application set
        large_app_set = {}
        for i in range(20):
            large_app_set[f"app-{i}"] = {
                "application_name": f"Application {i}",
                "technology_stack": {"java": "8", "database": "postgresql"}
            }
        
        # Mock result for large set
        mock_large_result = {
            "components": [
                {"name": f"component-{i}", "type": "api", "complexity_score": 5.0}
                for i in range(60)  # 3 components per app on average
            ],
            "tech_debt_analysis": [
                {"category": "version_obsolescence", "score": 7.0}
                for _ in range(20)
            ],
            "component_scores": {f"component-{i}": 5.0 for i in range(60)},
            "processing_time_seconds": 45.2
        }
        
        component_crew.crew.kickoff = AsyncMock(return_value=mock_large_result)
        
        result = await component_crew.execute({
            "applications": large_app_set,
            "architecture_standards": []
        })
        
        # Verify large set processing
        assert len(result["components"]) == 60
        assert len(result["tech_debt_analysis"]) == 20
        assert "processing_time_seconds" in result


class TestSixRStrategyCrew:
    """Unit tests for 6R Strategy CrewAI crew"""
    
    @pytest.fixture
    def sixr_crew(self, mock_flow_context):
        """Create 6R strategy crew with mocked context"""
        crew = SixRStrategyCrew(mock_flow_context)
        crew.crew = MagicMock()
        return crew
    
    @pytest.mark.asyncio
    async def test_sixr_strategy_determination(
        self,
        sixr_crew,
        sample_component_analysis_result,
        sample_sixr_strategy_result
    ):
        """Test 6R strategy determination with component analysis"""
        
        sixr_crew.crew.kickoff = AsyncMock(return_value=sample_sixr_strategy_result)
        
        result = await sixr_crew.execute({
            "component_analysis": sample_component_analysis_result,
            "architecture_standards": [
                {"requirement_type": "java_versions", "supported_versions": {"java": "11+"}}
            ],
            "business_context": {
                "timeline_constraints": {"go_live_target": "2025-12-31"},
                "budget_constraints": {"max_budget": 500000}
            }
        })
        
        assert "component_treatments" in result
        assert "overall_strategy" in result
        assert "confidence_score" in result
        
        # Verify component treatments
        treatments = result["component_treatments"]
        assert len(treatments) == 3
        
        frontend_treatment = next((t for t in treatments if t["component_name"] == "frontend"), None)
        assert frontend_treatment is not None
        assert frontend_treatment["recommended_strategy"] == "refactor"
        assert frontend_treatment["rationale"] == "React upgrade and modernization needed"
        
        # Verify overall strategy
        assert result["overall_strategy"] == "refactor"
        assert result["confidence_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_sixr_strategy_with_business_constraints(
        self,
        sixr_crew,
        sample_component_analysis_result
    ):
        """Test 6R strategy considering business constraints"""
        
        mock_constrained_result = {
            "component_treatments": [
                {
                    "component_name": "backend_api",
                    "recommended_strategy": "rehost",  # Changed from replatform due to constraints
                    "rationale": "Budget constraints require minimal changes",
                    "original_recommendation": "replatform",
                    "constraint_applied": "budget_limitation"
                }
            ],
            "overall_strategy": "rehost",
            "confidence_score": 0.7,  # Lower confidence due to constraints
            "constraint_impacts": [
                {
                    "constraint_type": "budget",
                    "impact": "Reduced to rehost strategy",
                    "risk_increase": "medium"
                }
            ]
        }
        
        sixr_crew.crew.kickoff = AsyncMock(return_value=mock_constrained_result)
        
        result = await sixr_crew.execute({
            "component_analysis": sample_component_analysis_result,
            "business_context": {
                "budget_constraints": {"max_budget": 50000},  # Very tight budget
                "timeline_constraints": {"go_live_target": "2025-06-30"}  # Tight timeline
            }
        })
        
        # Verify constraint impacts
        assert "constraint_impacts" in result
        assert len(result["constraint_impacts"]) == 1
        assert result["constraint_impacts"][0]["constraint_type"] == "budget"
        
        # Verify adjusted strategy
        backend_treatment = result["component_treatments"][0]
        assert backend_treatment["recommended_strategy"] == "rehost"
        assert backend_treatment["constraint_applied"] == "budget_limitation"
    
    @pytest.mark.asyncio
    async def test_sixr_strategy_risk_assessment(
        self,
        sixr_crew,
        sample_component_analysis_result
    ):
        """Test 6R strategy with risk assessment"""
        
        mock_risk_result = {
            "component_treatments": [
                {
                    "component_name": "database",
                    "recommended_strategy": "rehost",
                    "risk_assessment": {
                        "overall_risk": "low",
                        "risk_factors": [
                            {"factor": "data_migration", "risk": "medium"},
                            {"factor": "downtime", "risk": "low"}
                        ],
                        "mitigation_strategies": [
                            "Implement database replication for zero-downtime migration"
                        ]
                    }
                }
            ],
            "overall_strategy": "rehost",
            "confidence_score": 0.9,
            "risk_summary": {
                "overall_risk": "low",
                "high_risk_components": [],
                "risk_mitigation_plan": "Standard cloud migration practices"
            }
        }
        
        sixr_crew.crew.kickoff = AsyncMock(return_value=mock_risk_result)
        
        result = await sixr_crew.execute({
            "component_analysis": sample_component_analysis_result,
            "risk_tolerance": "low"
        })
        
        # Verify risk assessment
        assert "risk_summary" in result
        assert result["risk_summary"]["overall_risk"] == "low"
        
        db_treatment = result["component_treatments"][0]
        assert "risk_assessment" in db_treatment
        assert db_treatment["risk_assessment"]["overall_risk"] == "low"
        assert len(db_treatment["risk_assessment"]["mitigation_strategies"]) == 1


class TestAppOnPageCrew:
    """Unit tests for App-on-Page Generation CrewAI crew"""
    
    @pytest.fixture
    def app_page_crew(self, mock_flow_context):
        """Create app-on-page crew with mocked context"""
        crew = AppOnPageCrew(mock_flow_context)
        crew.crew = MagicMock()
        return crew
    
    @pytest.mark.asyncio
    async def test_app_on_page_generation(
        self,
        app_page_crew
    ):
        """Test app-on-page summary generation"""
        
        sixr_decisions = {
            "app-1": {
                "application_name": "Frontend Portal",
                "overall_strategy": "refactor",
                "confidence_score": 0.85,
                "component_treatments": [
                    {"component_name": "frontend", "recommended_strategy": "refactor"}
                ]
            },
            "app-2": {
                "application_name": "Backend API",
                "overall_strategy": "replatform",
                "confidence_score": 0.80,
                "component_treatments": [
                    {"component_name": "backend_api", "recommended_strategy": "replatform"}
                ]
            }
        }
        
        mock_app_page_result = {
            "applications_summary": [
                {
                    "application_id": "app-1",
                    "application_name": "Frontend Portal",
                    "recommended_strategy": "refactor",
                    "business_justification": "Modernization improves user experience and performance",
                    "technical_summary": "React upgrade from 16 to 18, TypeScript migration",
                    "effort_estimate": "12 weeks",
                    "cost_estimate": "$75,000 - $100,000",
                    "risk_assessment": "Low to Medium risk with proven upgrade path",
                    "migration_sequence": 2,
                    "dependencies": ["Backend API upgrade"]
                },
                {
                    "application_id": "app-2",
                    "application_name": "Backend API",
                    "recommended_strategy": "replatform",
                    "business_justification": "Java upgrade mandatory for security compliance",
                    "technical_summary": "Java 8 to 17 upgrade with containerization",
                    "effort_estimate": "20 weeks",
                    "cost_estimate": "$150,000 - $200,000",
                    "risk_assessment": "Medium risk requiring thorough testing",
                    "migration_sequence": 1,
                    "dependencies": []
                }
            ],
            "assessment_summary": {
                "total_applications": 2,
                "applications_ready": 2,
                "strategy_distribution": {"refactor": 1, "replatform": 1},
                "total_effort_estimate": "32 weeks",
                "total_cost_estimate": "$225,000 - $300,000",
                "overall_risk": "Medium",
                "migration_timeline": "8 months"
            }
        }
        
        app_page_crew.crew.kickoff = AsyncMock(return_value=mock_app_page_result)
        
        result = await app_page_crew.execute({
            "sixr_decisions": sixr_decisions,
            "engagement_context": {
                "target_cloud": "aws",
                "compliance_requirements": ["SOX"]
            }
        })
        
        assert "applications_summary" in result
        assert "assessment_summary" in result
        
        # Verify applications summary
        apps_summary = result["applications_summary"]
        assert len(apps_summary) == 2
        
        frontend_app = next((app for app in apps_summary if app["application_id"] == "app-1"), None)
        assert frontend_app is not None
        assert frontend_app["recommended_strategy"] == "refactor"
        assert frontend_app["effort_estimate"] == "12 weeks"
        assert frontend_app["migration_sequence"] == 2
        
        # Verify assessment summary
        summary = result["assessment_summary"]
        assert summary["total_applications"] == 2
        assert summary["applications_ready"] == 2
        assert summary["strategy_distribution"]["refactor"] == 1
        assert summary["strategy_distribution"]["replatform"] == 1
    
    @pytest.mark.asyncio
    async def test_app_on_page_with_prioritization(
        self,
        app_page_crew
    ):
        """Test app-on-page generation with migration wave prioritization"""
        
        mock_prioritized_result = {
            "applications_summary": [
                {
                    "application_id": "app-1",
                    "application_name": "Critical System",
                    "migration_wave": 1,
                    "wave_rationale": "Critical business function, migrate first",
                    "recommended_strategy": "rehost"
                },
                {
                    "application_id": "app-2", 
                    "application_name": "Support System",
                    "migration_wave": 2,
                    "wave_rationale": "Depends on critical system, migrate second",
                    "recommended_strategy": "refactor"
                }
            ],
            "wave_plan": {
                "wave_1": {
                    "applications": ["app-1"],
                    "duration": "8 weeks",
                    "risk": "low"
                },
                "wave_2": {
                    "applications": ["app-2"],
                    "duration": "12 weeks", 
                    "risk": "medium"
                }
            }
        }
        
        app_page_crew.crew.kickoff = AsyncMock(return_value=mock_prioritized_result)
        
        result = await app_page_crew.execute({
            "sixr_decisions": {"app-1": {}, "app-2": {}},
            "prioritization_criteria": {
                "business_criticality": "high",
                "dependency_analysis": True
            }
        })
        
        # Verify wave planning
        assert "wave_plan" in result
        wave_plan = result["wave_plan"]
        assert "wave_1" in wave_plan
        assert "wave_2" in wave_plan
        
        # Verify app prioritization
        apps = result["applications_summary"]
        critical_app = next((app for app in apps if app["application_id"] == "app-1"), None)
        assert critical_app["migration_wave"] == 1
        assert "Critical business function" in critical_app["wave_rationale"]


class TestCrewIntegration:
    """Integration tests for crew coordination"""
    
    @pytest.mark.asyncio
    async def test_crew_output_compatibility(
        self,
        mock_flow_context,
        sample_engagement_context,
        sample_application_metadata
    ):
        """Test that crew outputs are compatible between phases"""
        
        # Architecture Standards Crew output
        arch_crew = ArchitectureStandardsCrew(mock_flow_context)
        arch_crew.crew = MagicMock()
        arch_crew.crew.kickoff = AsyncMock(return_value={
            "engagement_standards": [
                {"requirement_type": "java_versions", "supported_versions": {"java": "11+"}}
            ]
        })
        
        arch_result = await arch_crew.execute({
            "engagement_context": sample_engagement_context,
            "selected_applications": ["app-1"]
        })
        
        # Component Analysis Crew using architecture output
        comp_crew = ComponentAnalysisCrew(mock_flow_context)
        comp_crew.crew = MagicMock()
        comp_crew.crew.kickoff = AsyncMock(return_value={
            "components": [{"name": "test", "type": "api"}],
            "tech_debt_analysis": [],
            "component_scores": {"test": 7.0}
        })
        
        comp_result = await comp_crew.execute({
            "applications": sample_application_metadata,
            "architecture_standards": arch_result["engagement_standards"]
        })
        
        # Verify compatibility
        assert "components" in comp_result
        assert "tech_debt_analysis" in comp_result
        
        # 6R Strategy Crew using component analysis output
        sixr_crew = SixRStrategyCrew(mock_flow_context)
        sixr_crew.crew = MagicMock()
        sixr_crew.crew.kickoff = AsyncMock(return_value={
            "component_treatments": [],
            "overall_strategy": "refactor",
            "confidence_score": 0.8
        })
        
        sixr_result = await sixr_crew.execute({
            "component_analysis": comp_result,
            "architecture_standards": arch_result["engagement_standards"]
        })
        
        # Verify compatibility
        assert "component_treatments" in sixr_result
        assert "overall_strategy" in sixr_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])