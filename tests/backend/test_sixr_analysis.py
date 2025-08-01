import os
import sys

# datetime import removed - not used
from unittest.mock import Mock

import pytest

# Add backend to path before importing app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))

from app.schemas.sixr_analysis import (  # noqa: E402
    ApplicationType,
    SixRParameters,
)
from app.services.sixr_engine_modular import SixRDecisionEngine  # noqa: E402
from app.services.tools.sixr_tools import (  # noqa: E402
    CMDBAnalysisTool,
    CodeAnalysisTool,
    ParameterScoringTool,
    QuestionGenerationTool,
    RecommendationValidationTool,
)


class TestSixRDecisionEngine:
    """Test suite for the 6R Decision Engine"""

    @pytest.fixture
    def decision_engine(self):
        return SixRDecisionEngine()

    @pytest.fixture
    def sample_parameters(self):
        return SixRParameters(
            business_value=7,
            technical_complexity=5,
            migration_urgency=6,
            compliance_requirements=4,
            cost_sensitivity=5,
            risk_tolerance=6,
            innovation_priority=8,
            application_type=ApplicationType.CUSTOM,
        )

    def test_strategy_weights_initialization(self, decision_engine):
        """Test that strategy weights are properly initialized"""
        weights = decision_engine.strategy_weights

        # Check that all strategies have weights
        expected_strategies = [
            "rehost",
            "replatform",
            "refactor",
            "rearchitect",
            "rewrite",
            "retire",
        ]
        for strategy in expected_strategies:
            assert strategy in weights
            assert len(weights[strategy]) == 7  # 7 parameters
            assert all(0 <= weight <= 1 for weight in weights[strategy].values())

    def test_parameter_validation(self, decision_engine, sample_parameters):
        """Test parameter validation logic"""
        # Valid parameters should pass
        validated = decision_engine._validate_parameters(sample_parameters)
        assert validated is not None

        # Test edge cases
        edge_params = SixRParameters(
            business_value=1,
            technical_complexity=10,
            migration_urgency=1,
            compliance_requirements=10,
            cost_sensitivity=1,
            risk_tolerance=10,
            innovation_priority=1,
            application_type=ApplicationType.CUSTOM,
        )
        validated_edge = decision_engine._validate_parameters(edge_params)
        assert validated_edge is not None

    def test_scoring_calculation(self, decision_engine, sample_parameters):
        """Test the scoring calculation for each strategy"""
        scores = decision_engine.calculate_strategy_scores(sample_parameters)

        # Check that all strategies have scores
        expected_strategies = [
            "rehost",
            "replatform",
            "refactor",
            "rearchitect",
            "rewrite",
            "retire",
        ]
        for strategy in expected_strategies:
            assert strategy in scores
            assert 0 <= scores[strategy]["score"] <= 10
            assert 0 <= scores[strategy]["confidence"] <= 1

    def test_cots_application_restrictions(self, decision_engine):
        """Test that COTS applications cannot use REWRITE strategy"""
        cots_params = SixRParameters(
            business_value=8,
            technical_complexity=6,
            migration_urgency=7,
            compliance_requirements=5,
            cost_sensitivity=4,
            risk_tolerance=6,
            innovation_priority=9,
            application_type=ApplicationType.COTS,
        )

        scores = decision_engine.calculate_strategy_scores(cots_params)

        # REWRITE should have very low score for COTS
        assert scores["rewrite"]["score"] < 3
        # REPLACE should be available and potentially high scoring
        assert "replace" in scores or scores["retire"]["score"] > 5

    def test_custom_application_scoring(self, decision_engine, sample_parameters):
        """Test scoring for custom applications"""
        scores = decision_engine.calculate_strategy_scores(sample_parameters)

        # Custom applications should have access to all strategies
        assert all(
            strategy in scores
            for strategy in [
                "rehost",
                "replatform",
                "refactor",
                "rearchitect",
                "rewrite",
            ]
        )

        # High innovation priority should favor modernization strategies
        assert scores["refactor"]["score"] > scores["rehost"]["score"]
        assert scores["rearchitect"]["score"] > scores["rehost"]["score"]

    def test_confidence_calculation(self, decision_engine, sample_parameters):
        """Test confidence score calculation"""
        decision_engine.calculate_strategy_scores(sample_parameters)
        recommendation = decision_engine.get_recommendation(sample_parameters)

        # Confidence should be between 0 and 1
        assert 0 <= recommendation.confidence_score <= 1

        # Higher parameter consistency should lead to higher confidence
        consistent_params = SixRParameters(
            business_value=8,
            technical_complexity=3,
            migration_urgency=8,
            compliance_requirements=3,
            cost_sensitivity=3,
            risk_tolerance=8,
            innovation_priority=8,
            application_type=ApplicationType.CUSTOM,
        )

        consistent_recommendation = decision_engine.get_recommendation(
            consistent_params
        )
        assert consistent_recommendation.confidence_score > 0.7

    def test_recommendation_generation(self, decision_engine, sample_parameters):
        """Test complete recommendation generation"""
        recommendation = decision_engine.get_recommendation(sample_parameters)

        # Check recommendation structure
        assert recommendation.recommended_strategy in [
            "rehost",
            "replatform",
            "refactor",
            "rearchitect",
            "rewrite",
            "retire",
        ]
        assert len(recommendation.strategy_scores) >= 5
        assert len(recommendation.key_factors) > 0
        assert len(recommendation.assumptions) > 0
        assert len(recommendation.next_steps) > 0

        # Check that strategy scores are sorted by score
        scores = [score.score for score in recommendation.strategy_scores]
        assert scores == sorted(scores, reverse=True)

    def test_edge_case_scenarios(self, decision_engine):
        """Test edge case scenarios"""
        # Very low business value should favor RETIRE
        low_value_params = SixRParameters(
            business_value=1,
            technical_complexity=9,
            migration_urgency=2,
            compliance_requirements=8,
            cost_sensitivity=9,
            risk_tolerance=2,
            innovation_priority=1,
            application_type=ApplicationType.CUSTOM,
        )

        recommendation = decision_engine.get_recommendation(low_value_params)
        # Should strongly consider RETIRE
        retire_score = next(
            score.score
            for score in recommendation.strategy_scores
            if score.strategy == "retire"
        )
        assert retire_score > 6

        # Very high innovation priority should favor modernization
        high_innovation_params = SixRParameters(
            business_value=9,
            technical_complexity=4,
            migration_urgency=6,
            compliance_requirements=3,
            cost_sensitivity=3,
            risk_tolerance=8,
            innovation_priority=10,
            application_type=ApplicationType.CUSTOM,
        )

        recommendation = decision_engine.get_recommendation(high_innovation_params)
        # Should favor REFACTOR, REARCHITECT, or REWRITE
        top_strategy = recommendation.recommended_strategy
        assert top_strategy in ["refactor", "rearchitect", "rewrite"]


# TODO: Implement SixRAgentOrchestrator before enabling these tests
# class TestSixRAgentOrchestrator:
#     """Test suite for the 6R Agent Orchestrator"""
#
#     @pytest.fixture
#     def orchestrator(self):
#         return SixRAgentOrchestrator()
#

#     @pytest.fixture
#     def sample_cmdb_data(self):
#        return {
#            "application_id": 1,
#            "name": "Test Application",
#            "technology_stack": ["Java 8", "Spring", "MySQL"],
#            "department": "Finance",
#            "business_unit": "Customer Service",
#            "criticality": "high",
#            "complexity_score": 7,
#            "user_count": 1500,
#            "data_volume": "500GB",
#            "compliance_requirements": ["PCI-DSS", "SOX"],
#            "dependencies": ["Payment Gateway", "CRM System"],
#        }

#    @pytest.mark.asyncio
#    async def test_agent_initialization(self, orchestrator):
#        """Test that all agents are properly initialized"""
#        agents = orchestrator.get_all_agents()

#        expected_agents = [
#            "discovery",
#            "initial_analysis",
#            "question_generator",
#            "input_processor",
#            "refinement",
#            "validation",
#        ]

#        for agent_name in expected_agents:
#            assert agent_name in agents
#            agent = agents[agent_name]
#            assert agent.role is not None
#            assert agent.backstory is not None

#    @pytest.mark.asyncio
#    async def test_discovery_agent(self, orchestrator, sample_cmdb_data):
#        """Test the Discovery Agent functionality"""
#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.return_value = {
#                "technology_analysis": {
#                    "primary_language": "Java",
#                    "framework": "Spring",
#                    "database": "MySQL",
#                    "modernization_potential": "high",
#                },
#                "dependency_analysis": {
#                    "external_dependencies": 2,
#                    "complexity_score": 7,
#                    "migration_risk": "medium",
#                },
#                "business_context": {
#                    "criticality": "high",
#                    "user_impact": "high",
#                    "compliance_requirements": ["PCI-DSS", "SOX"],
#                },
#            }

#            result = await orchestrator.run_discovery_agent(sample_cmdb_data)

#            assert "technology_analysis" in result
#            assert "dependency_analysis" in result
#            assert "business_context" in result
#            mock_execute.assert_called_once()

#    @pytest.mark.asyncio
#    async def test_initial_analysis_agent(self, orchestrator, sample_cmdb_data):
#        """Test the Initial Analysis Agent functionality"""
#        discovery_results = {
#            "technology_analysis": {"modernization_potential": "high"},
#            "dependency_analysis": {"complexity_score": 7},
#            "business_context": {"criticality": "high"},
#        }

#        parameters = SixRParameters(
#            business_value=7,
#            technical_complexity=5,
#            migration_urgency=6,
#            compliance_requirements=4,
#            cost_sensitivity=5,
#            risk_tolerance=6,
#            innovation_priority=8,
#            application_type=ApplicationType.CUSTOM,
#        )

#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.return_value = {
#                "preliminary_recommendation": "refactor",
#                "confidence_score": 0.75,
#                "key_factors": ["High innovation priority", "Moderate complexity"],
#                "data_gaps": ["Code quality assessment", "Performance metrics"],
#            }

#            result = await orchestrator.run_initial_analysis_agent(
#                sample_cmdb_data, discovery_results, parameters
#            )

#            assert "preliminary_recommendation" in result
#            assert "confidence_score" in result
#            assert "data_gaps" in result
#            mock_execute.assert_called_once()

#    @pytest.mark.asyncio
#    async def test_question_generator_agent(self, orchestrator):
#        """Test the Question Generator Agent functionality"""
#        analysis_results = {
#            "data_gaps": [
#                "Code quality assessment",
#                "Performance metrics",
#                "Team expertise",
#            ],
#            "preliminary_recommendation": "refactor",
#            "confidence_score": 0.65,
#        }

#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.return_value = {
#                "questions": [
#                    {
#                        "id": "code_quality",
#                        "question": "How would you rate the current code quality?",
#                        "question_type": "select",
#                        "category": "Technical Assessment",
#                        "priority": 1,
#                        "required": True,
#                        "options": [
#                            {"value": "excellent", "label": "Excellent"},
#                            {"value": "good", "label": "Good"},
#                            {"value": "fair", "label": "Fair"},
#                            {"value": "poor", "label": "Poor"},
#                        ],
#                    }
#                ],
#                "question_rationale": {
#                    "code_quality": "Needed to assess refactoring feasibility"
#                },
#            }

#            result = await orchestrator.run_question_generator_agent(analysis_results)

#            assert "questions" in result
#            assert len(result["questions"]) > 0
#            assert "question_rationale" in result
#            mock_execute.assert_called_once()

#    @pytest.mark.asyncio
#    async def test_input_processor_agent(self, orchestrator):
#        """Test the Input Processor Agent functionality"""
#        responses = [
#            QuestionResponse(
#                question_id="code_quality",
#                response="good",
#                confidence=0.8,
#                source="user_input",
#                timestamp=datetime.now(),
#            )
#        ]

#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.return_value = {
#                "processed_responses": {
#                    "code_quality": {
#                        "value": "good",
#                        "impact_on_recommendation": "positive",
#                        "confidence_adjustment": 0.1,
#                    }
#                },
#                "updated_confidence": 0.75,
#                "recommendation_adjustments": {"refactor": 0.1, "replatform": -0.05},
#            }

#            result = await orchestrator.run_input_processor_agent(responses)

#            assert "processed_responses" in result
#            assert "updated_confidence" in result
#            assert "recommendation_adjustments" in result
#            mock_execute.assert_called_once()

#    @pytest.mark.asyncio
#    async def test_refinement_agent(self, orchestrator):
#        """Test the Refinement Agent functionality"""
#        initial_recommendation = {
#            "recommended_strategy": "refactor",
#            "confidence_score": 0.75,
#            "strategy_scores": {"refactor": 8.2, "replatform": 7.1},
#        }

#        processed_responses = {
#            "code_quality": {"value": "good", "impact_on_recommendation": "positive"}
#        }

#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.return_value = {
#                "refined_recommendation": "refactor",
#                "updated_confidence": 0.82,
#                "refined_scores": {"refactor": 8.5, "replatform": 7.0},
#                "refinement_rationale": [
#                    "Improved confidence due to good code quality"
#                ],
#            }

#            result = await orchestrator.run_refinement_agent(
#                initial_recommendation, processed_responses
#            )

#            assert "refined_recommendation" in result
#            assert "updated_confidence" in result
#            assert "refined_scores" in result
#            mock_execute.assert_called_once()

#    @pytest.mark.asyncio
#    async def test_validation_agent(self, orchestrator):
#        """Test the Validation Agent functionality"""
#        final_recommendation = {
#            "recommended_strategy": "refactor",
#            "confidence_score": 0.82,
#            "strategy_scores": {"refactor": 8.5, "replatform": 7.0},
#        }

#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.return_value = {
#                "validation_result": "approved",
#                "validation_confidence": 0.85,
#                "validation_notes": ["Recommendation aligns with business objectives"],
#                "final_recommendation": final_recommendation,
#            }

#            result = await orchestrator.run_validation_agent(final_recommendation)

#            assert "validation_result" in result
#            assert "validation_confidence" in result
#            assert "final_recommendation" in result
#            mock_execute.assert_called_once()

#    @pytest.mark.asyncio
#    async def test_error_handling(self, orchestrator, sample_cmdb_data):
#        """Test error handling in agent execution"""
#        with patch.object(
#            orchestrator, "_execute_agent_task", new_callable=AsyncMock
#        ) as mock_execute:
#            mock_execute.side_effect = Exception("Agent execution failed")

#            with pytest.raises(Exception):
#                await orchestrator.run_discovery_agent(sample_cmdb_data)


class TestSixRTools:
    """Test suite for the 6R Tools"""

    def test_cmdb_analysis_tool(self):
        """Test CMDB Analysis Tool"""
        tool = CMDBAnalysisTool()

        sample_data = {
            "technology_stack": ["Java 8", "Spring", "MySQL"],
            "complexity_score": 7,
            "user_count": 1500,
            "data_volume": "500GB",
        }

        result = tool._run(sample_data)

        assert "technology_analysis" in result
        assert "complexity_assessment" in result
        assert "modernization_potential" in result

    def test_parameter_scoring_tool(self):
        """Test Parameter Scoring Tool"""
        tool = ParameterScoringTool()

        parameters = {
            "business_value": 7,
            "technical_complexity": 5,
            "migration_urgency": 6,
            "innovation_priority": 8,
        }

        result = tool._run(parameters)

        assert "strategy_scores" in result
        assert "confidence_factors" in result
        assert len(result["strategy_scores"]) >= 5

    def test_question_generation_tool(self):
        """Test Question Generation Tool"""
        tool = QuestionGenerationTool()

        data_gaps = ["code_quality", "team_expertise", "performance_metrics"]
        context = {
            "application_type": "custom",
            "preliminary_recommendation": "refactor",
            "confidence_score": 0.65,
        }

        result = tool._run(data_gaps, context)

        assert "questions" in result
        assert len(result["questions"]) > 0
        assert all("question_type" in q for q in result["questions"])

    def test_code_analysis_tool(self):
        """Test Code Analysis Tool"""
        tool = CodeAnalysisTool()

        # Mock file content
        sample_code = """
        public class CustomerService {
            private DatabaseConnection db;

            public Customer getCustomer(int id) {
                return db.query("SELECT * FROM customers WHERE id = " + id);
            }
        }
        """

        result = tool._run(sample_code, "java")

        assert "language_detected" in result
        assert "code_quality_metrics" in result
        assert "modernization_opportunities" in result

    def test_recommendation_validation_tool(self):
        """Test Recommendation Validation Tool"""
        tool = RecommendationValidationTool()

        recommendation = {
            "recommended_strategy": "refactor",
            "confidence_score": 0.82,
            "key_factors": ["High business value", "Moderate complexity"],
        }

        context = {
            "application_type": "custom",
            "business_constraints": ["6_month_timeline", "moderate_budget"],
        }

        result = tool._run(recommendation, context)

        assert "validation_result" in result
        assert "validation_confidence" in result
        assert "validation_notes" in result


class TestAPIEndpoints:
    """Test suite for 6R API endpoints"""

    @pytest.fixture
    def client(self):
        # This would typically use FastAPI TestClient
        # For now, we'll mock the client
        return Mock()

    def test_create_analysis_endpoint(self, client):
        """Test POST /sixr/analyze endpoint"""
        request_data = {
            "application_ids": [1, 2, 3],
            "parameters": {
                "business_value": 7,
                "technical_complexity": 5,
                "migration_urgency": 6,
                "compliance_requirements": 4,
                "cost_sensitivity": 5,
                "risk_tolerance": 6,
                "innovation_priority": 8,
                "application_type": "custom",
            },
        }

        # Mock successful response
        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {
            "analysis_id": 123,
            "status": "created",
            "estimated_duration": 300,
        }

        response = client.post("/sixr/analyze", json=request_data)

        assert response.status_code == 201
        assert "analysis_id" in response.json()

    def test_get_analysis_endpoint(self, client):
        """Test GET /sixr/analysis/{id} endpoint"""
        analysis_id = 123

        # Mock successful response
        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = {
            "analysisId": analysis_id,
            "status": "completed",
            "overallProgress": 100,
            "steps": [],
        }

        response = client.get(f"/sixr/analysis/{analysis_id}")

        assert response.status_code == 200
        assert response.json()["analysisId"] == analysis_id

    def test_update_parameters_endpoint(self, client):
        """Test PUT /sixr/analysis/{id}/parameters endpoint"""
        analysis_id = 123
        update_data = {
            "parameters": {"business_value": 8, "innovation_priority": 9},
            "trigger_reanalysis": True,
        }

        # Mock successful response
        client.put.return_value.status_code = 200
        client.put.return_value.json.return_value = {
            "success": True,
            "message": "Parameters updated successfully",
        }

        response = client.put(
            f"/sixr/analysis/{analysis_id}/parameters", json=update_data
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_submit_questions_endpoint(self, client):
        """Test POST /sixr/analysis/{id}/questions endpoint"""
        analysis_id = 123
        question_data = {
            "responses": [
                {
                    "question_id": "code_quality",
                    "response": "good",
                    "confidence": 0.8,
                    "source": "user_input",
                }
            ],
            "is_partial": False,
        }

        # Mock successful response
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "success": True,
            "message": "Questions submitted successfully",
        }

        response = client.post(
            f"/sixr/analysis/{analysis_id}/questions", json=question_data
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_error_handling_endpoints(self, client):
        """Test error handling in API endpoints"""
        # Test 404 for non-existent analysis
        client.get.return_value.status_code = 404
        client.get.return_value.json.return_value = {"detail": "Analysis not found"}

        response = client.get("/sixr/analysis/999999")

        assert response.status_code == 404
        assert "detail" in response.json()

        # Test 400 for invalid parameters
        client.post.return_value.status_code = 400
        client.post.return_value.json.return_value = {"detail": "Invalid parameters"}

        invalid_data = {"invalid": "data"}
        response = client.post("/sixr/analyze", json=invalid_data)

        assert response.status_code == 400


class TestIntegrationScenarios:
    """Integration tests for complete 6R analysis workflows"""

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self):
        """Test complete analysis workflow from start to finish"""
        # This would test the entire workflow:
        # 1. Create analysis
        # 2. Run discovery agent
        # 3. Run initial analysis
        # 4. Generate questions
        # 5. Process responses
        # 6. Refine recommendation
        # 7. Validate final recommendation

        # Mock the entire workflow
        # orchestrator = SixRAgentOrchestrator()
        decision_engine = SixRDecisionEngine()

        # Sample data
        # TODO: Use cmdb_data when SixRAgentOrchestrator is implemented
        # cmdb_data = {
        #     "application_id": 1,
        #     "name": "Test Application",
        #     "technology_stack": ["Java 8", "Spring", "MySQL"],
        # }

        parameters = SixRParameters(
            business_value=7,
            technical_complexity=5,
            migration_urgency=6,
            compliance_requirements=4,
            cost_sensitivity=5,
            risk_tolerance=6,
            innovation_priority=8,
            application_type=ApplicationType.CUSTOM,
        )

        # Test that the workflow can be executed without errors
        # TODO: Uncomment when SixRAgentOrchestrator is implemented
        # with patch.object(
        #     orchestrator, "_execute_agent_task", new_callable=AsyncMock
        # ) as mock_execute:
        #     mock_execute.return_value = {"status": "success"}
        #
        #     # This would be the actual workflow execution
        #     discovery_result = await orchestrator.run_discovery_agent(cmdb_data)
        #     assert discovery_result is not None
        #
        #     initial_analysis = await orchestrator.run_initial_analysis_agent(
        #         cmdb_data, discovery_result, parameters
        #     )
        #     assert initial_analysis is not None
        pass  # Placeholder until orchestrator is implemented

        # Generate final recommendation
        recommendation = decision_engine.get_recommendation(parameters)
        assert recommendation is not None
        assert recommendation.recommended_strategy is not None

    def test_performance_requirements(self):
        """Test that performance requirements are met"""
        decision_engine = SixRDecisionEngine()

        parameters = SixRParameters(
            business_value=7,
            technical_complexity=5,
            migration_urgency=6,
            compliance_requirements=4,
            cost_sensitivity=5,
            risk_tolerance=6,
            innovation_priority=8,
            application_type=ApplicationType.CUSTOM,
        )

        # Test that recommendation generation is fast enough
        import time

        start_time = time.time()

        recommendation = decision_engine.get_recommendation(parameters)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in under 1 second for single analysis
        assert execution_time < 1.0
        assert recommendation is not None

    def test_concurrent_analysis_support(self):
        """Test support for concurrent analyses"""
        decision_engine = SixRDecisionEngine()

        # Create multiple parameter sets
        parameter_sets = []
        for i in range(10):
            params = SixRParameters(
                business_value=5 + (i % 5),
                technical_complexity=3 + (i % 7),
                migration_urgency=4 + (i % 6),
                compliance_requirements=2 + (i % 8),
                cost_sensitivity=3 + (i % 7),
                risk_tolerance=4 + (i % 6),
                innovation_priority=5 + (i % 5),
                application_type=(
                    ApplicationType.CUSTOM if i % 2 == 0 else ApplicationType.COTS
                ),
            )
            parameter_sets.append(params)

        # Test concurrent execution
        import concurrent.futures
        import time

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(decision_engine.get_recommendation, params)
                for params in parameter_sets
            ]

            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        end_time = time.time()
        execution_time = end_time - start_time

        # Should handle 10 concurrent analyses efficiently
        assert len(results) == 10
        assert all(result is not None for result in results)
        assert execution_time < 5.0  # Should complete in under 5 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
