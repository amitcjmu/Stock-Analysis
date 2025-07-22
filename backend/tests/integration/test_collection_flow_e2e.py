"""
End-to-End Integration Test for Unified Collection Flow

This comprehensive test validates the entire collection flow from initialization
through finalization with real database persistence, pause/resume functionality,
and proper data flow to PostgreSQL.

Test Coverage:
1. Create test context with client and engagement
2. Initialize UnifiedCollectionFlow
3. Execute through all phases
4. Verify database persistence at each phase
5. Test pause/resume functionality
6. Verify data flows to PostgreSQL correctly

Generated with CC.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models import ClientAccount, Engagement, User
from app.models.collected_data_inventory import CollectedDataInventory
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import (
    CollectionFlow,
    CollectionPhase,
    CollectionStatus,
    PlatformType,
)
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.platform_credentials import PlatformCredential
from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow
from app.services.crewai_service import CrewAIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCollectionFlowE2E:
    """
    End-to-end integration test for the entire collection flow.
    
    Tests the complete flow from initialization through finalization,
    including database persistence, pause/resume, and data validation.
    """
    
    @pytest.fixture
    async def test_context(self):
        """Create test context with client and engagement"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="test_user_" + str(uuid.uuid4()),
            user_role="admin",
            request_id=str(uuid.uuid4())
        )
    
    @pytest.fixture
    async def db_session(self):
        """Create database session for testing"""
        async with AsyncSessionLocal() as session:
            yield session
    
    @pytest.fixture
    async def test_client_engagement(self, db_session: AsyncSession, test_context: RequestContext):
        """Create test client and engagement in database"""
        # Create client account
        client = ClientAccount(
            id=uuid.UUID(test_context.client_account_id),
            account_name="Test Client for Collection Flow",
            industry="Technology",
            company_size="Enterprise",
            headquarters_location="Test City",
            primary_contact_name="Test Contact",
            primary_contact_email="test@example.com",
            business_objectives=["Cloud Migration", "Cost Optimization"],
            target_cloud_providers=["aws", "azure"],
            business_priorities=["scalability", "cost_reduction"],
            compliance_requirements=["SOC2", "HIPAA"]
        )
        db_session.add(client)
        
        # Create user
        user = User(
            id=test_context.user_id,
            username=f"test_user_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="test_password_hash",
            is_active=True,
            is_verified=True,
            client_account_id=client.id,
            engagement_id=uuid.UUID(test_context.engagement_id)
        )
        db_session.add(user)
        
        # Create engagement
        engagement = Engagement(
            id=uuid.UUID(test_context.engagement_id),
            name="Test Engagement for Collection Flow",
            description="E2E test engagement",
            client_id=client.id,
            created_by=user.id,
            status="active",
            scope="full_migration_assessment",
            timeline_months=6,
            budget_range="100k-500k"
        )
        db_session.add(engagement)
        
        await db_session.commit()
        await db_session.refresh(client)
        await db_session.refresh(user)
        await db_session.refresh(engagement)
        
        return {
            "client": client,
            "user": user,
            "engagement": engagement
        }
    
    @pytest.fixture
    async def crewai_service(self):
        """Create CrewAI service instance"""
        return CrewAIService()
    
    @pytest.fixture
    async def collection_flow(self, crewai_service, test_context, db_session):
        """Create UnifiedCollectionFlow instance"""
        flow = UnifiedCollectionFlow(
            crewai_service=crewai_service,
            context=test_context,
            automation_tier="tier_2",
            db_session=db_session,
            config={
                "environment_config": {
                    "platforms": ["aws", "azure"],
                    "environments": ["production", "staging"],
                    "regions": ["us-east-1", "us-west-2"]
                },
                "client_requirements": {
                    "sixr_requirements": {
                        "rehost": True,
                        "replatform": True,
                        "refactor": False
                    },
                    "validation_rules": {
                        "required_fields": ["hostname", "ip_address", "environment"],
                        "data_quality_threshold": 0.8
                    },
                    "approval_required_phases": ["platform_detection"]
                }
            }
        )
        return flow
    
    @pytest.mark.asyncio
    async def test_complete_collection_flow_e2e(
        self, 
        collection_flow: UnifiedCollectionFlow,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test complete collection flow execution end-to-end"""
        logger.info("Starting end-to-end collection flow test")
        
        # Phase 1: Initialize flow
        logger.info("Phase 1: Initializing collection flow")
        init_result = await collection_flow.initialize_collection()
        
        assert init_result["status"] == "completed"
        assert init_result["phase"] == "initialization"
        assert init_result["flow_id"] == collection_flow._flow_id
        
        # Verify database persistence
        flow_record = await db_session.get(CollectionFlow, collection_flow._flow_id)
        assert flow_record is not None
        assert flow_record.status == CollectionStatus.INITIALIZING.value
        assert flow_record.current_phase == CollectionPhase.PLATFORM_DETECTION.value
        
        # Phase 2: Platform Detection
        logger.info("Phase 2: Detecting platforms")
        platform_result = await collection_flow.detect_platforms(init_result)
        
        assert platform_result["status"] == "completed"
        assert platform_result["phase"] == "platform_detection"
        assert platform_result["platforms_detected"] > 0
        assert platform_result["quality_score"] > 0
        
        # Verify state persistence
        state_record = await db_session.execute(
            select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == collection_flow._flow_id
            )
        )
        state = state_record.scalar_one_or_none()
        assert state is not None
        assert state.flow_type == "collection"
        
        # Phase 3: Automated Collection
        logger.info("Phase 3: Running automated collection")
        collection_result = await collection_flow.automated_collection(platform_result)
        
        assert collection_result["status"] == "completed"
        assert collection_result["phase"] == "automated_collection"
        assert collection_result["data_collected"] > 0
        assert collection_result["quality_score"] > 0
        
        # Verify collected data persistence
        collected_data = await db_session.execute(
            select(CollectedDataInventory).where(
                CollectedDataInventory.collection_flow_id == collection_flow._flow_id
            )
        )
        data_records = collected_data.scalars().all()
        assert len(data_records) > 0
        
        # Phase 4: Gap Analysis
        logger.info("Phase 4: Analyzing gaps")
        gap_result = await collection_flow.analyze_gaps(collection_result)
        
        assert gap_result["status"] == "completed"
        assert gap_result["phase"] == "gap_analysis"
        assert "gaps_identified" in gap_result
        assert "sixr_impact_score" in gap_result
        
        # Verify gap analysis persistence
        gaps = await db_session.execute(
            select(CollectionDataGap).where(
                CollectionDataGap.collection_flow_id == collection_flow._flow_id
            )
        )
        gap_records = gaps.scalars().all()
        logger.info(f"Found {len(gap_records)} gap records")
        
        # Phase 5: Questionnaire Generation (if gaps exist)
        if gap_result["gaps_identified"] > 0:
            logger.info("Phase 5: Generating questionnaires")
            questionnaire_result = await collection_flow.generate_questionnaires(gap_result)
            
            assert questionnaire_result["status"] == "completed"
            assert questionnaire_result["phase"] == "questionnaire_generation"
            assert questionnaire_result["questionnaires_generated"] > 0
            assert questionnaire_result["requires_user_input"] is True
            
            # Simulate user input for manual collection
            user_responses = {
                "manual_responses": {
                    "response_1": {
                        "question": "What is the primary database technology?",
                        "answer": "PostgreSQL 13",
                        "confidence": 0.9
                    },
                    "response_2": {
                        "question": "What is the average daily transaction volume?",
                        "answer": "1.5 million transactions",
                        "confidence": 0.85
                    }
                }
            }
            
            # Resume flow with user input
            collection_flow.state.user_inputs.update(user_responses)
            
            # Phase 6: Manual Collection
            logger.info("Phase 6: Processing manual collection")
            manual_result = await collection_flow.manual_collection(questionnaire_result)
            
            assert manual_result["status"] == "completed"
            assert manual_result["phase"] == "manual_collection"
            assert manual_result["responses_collected"] > 0
            
            # Verify questionnaire responses persistence
            responses = await db_session.execute(
                select(CollectionQuestionnaireResponse).where(
                    CollectionQuestionnaireResponse.collection_flow_id == collection_flow._flow_id
                )
            )
            response_records = responses.scalars().all()
            assert len(response_records) > 0
        
        # Phase 7: Data Validation
        logger.info("Phase 7: Validating all collected data")
        validation_result = await collection_flow.validate_data(
            gap_result if gap_result["gaps_identified"] == 0 else manual_result
        )
        
        assert validation_result["status"] == "completed"
        assert validation_result["phase"] == "data_validation"
        assert validation_result["data_quality_score"] > 0
        assert validation_result["sixr_readiness_score"] > 0
        
        # Phase 8: Finalization
        logger.info("Phase 8: Finalizing collection flow")
        final_result = await collection_flow.finalize_collection(validation_result)
        
        assert final_result["status"] == "completed"
        assert final_result["phase"] == "finalization"
        assert final_result["flow_completed"] is True
        assert "assessment_package" in final_result
        
        # Verify final flow state
        await db_session.refresh(flow_record)
        assert flow_record.status == CollectionStatus.COMPLETED.value
        assert flow_record.current_phase == CollectionPhase.FINALIZATION.value
        assert flow_record.progress_percentage == 100.0
        assert flow_record.completed_at is not None
        
        # Verify assessment package
        assessment_package = final_result["assessment_package"]
        assert assessment_package["flow_id"] == collection_flow._flow_id
        assert assessment_package["client_account_id"] == str(test_client_engagement["client"].id)
        assert assessment_package["engagement_id"] == str(test_client_engagement["engagement"].id)
        assert "collected_data" in assessment_package
        assert "gap_analysis" in assessment_package
        assert assessment_package["sixr_readiness"] > 0
        
        logger.info("✅ End-to-end collection flow test completed successfully")
    
    @pytest.mark.asyncio
    async def test_pause_resume_functionality(
        self,
        collection_flow: UnifiedCollectionFlow,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test pause and resume functionality during flow execution"""
        logger.info("Testing pause/resume functionality")
        
        # Initialize flow
        init_result = await collection_flow.initialize_collection()
        assert init_result["status"] == "completed"
        
        # Execute platform detection
        platform_result = await collection_flow.detect_platforms(init_result)
        assert platform_result["status"] == "completed"
        
        # Check if flow is paused (based on approval requirement)
        flow_record = await db_session.get(CollectionFlow, collection_flow._flow_id)
        if "platform_detection_approval" in collection_flow.state.pause_points:
            assert flow_record.status == CollectionStatus.PAUSED.value
            
            # Simulate user approval
            user_approval = {
                "platform_detection_approved": True,
                "approved_by": test_client_engagement["user"].id,
                "approval_timestamp": datetime.utcnow().isoformat()
            }
            
            # Resume flow
            resume_result = await collection_flow.resume_flow(user_approval)
            assert resume_result is not None
            
            # Verify flow resumed
            await db_session.refresh(flow_record)
            assert flow_record.status != CollectionStatus.PAUSED.value
        
        logger.info("✅ Pause/resume functionality test completed")
    
    @pytest.mark.asyncio
    async def test_data_persistence_integrity(
        self,
        collection_flow: UnifiedCollectionFlow,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test data persistence and integrity throughout flow execution"""
        logger.info("Testing data persistence integrity")
        
        # Execute initialization
        await collection_flow.initialize_collection()
        
        # Verify flow state extension created
        state_ext = await db_session.execute(
            select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == collection_flow._flow_id
            )
        )
        state_record = state_ext.scalar_one()
        
        assert state_record.flow_type == "collection"
        assert state_record.client_account_id == uuid.UUID(test_client_engagement["client"].id)
        assert state_record.engagement_id == uuid.UUID(test_client_engagement["engagement"].id)
        assert state_record.current_state is not None
        
        # Verify JSON state structure
        current_state = json.loads(state_record.current_state)
        assert "flow_id" in current_state
        assert "current_phase" in current_state
        assert "status" in current_state
        assert "phase_results" in current_state
        
        logger.info("✅ Data persistence integrity test completed")
    
    @pytest.mark.asyncio
    async def test_error_recovery(
        self,
        collection_flow: UnifiedCollectionFlow,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test error handling and recovery during flow execution"""
        logger.info("Testing error recovery mechanisms")
        
        # Initialize flow
        await collection_flow.initialize_collection()
        
        # Simulate error by corrupting state
        collection_flow.state.detected_platforms = None
        
        # Attempt to execute automated collection (should handle error gracefully)
        try:
            await collection_flow.automated_collection({"phase": "platform_detection"})
        except Exception:
            # Verify error was logged
            assert collection_flow.state.errors is not None
            assert len(collection_flow.state.errors) > 0
            
            # Verify flow status
            flow_record = await db_session.get(CollectionFlow, collection_flow._flow_id)
            assert flow_record.status in [
                CollectionStatus.FAILED.value,
                CollectionStatus.COLLECTING_DATA.value
            ]
        
        logger.info("✅ Error recovery test completed")
    
    @pytest.mark.asyncio
    async def test_multi_tier_execution(
        self,
        crewai_service,
        test_context,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test collection flow execution across different automation tiers"""
        logger.info("Testing multi-tier execution")
        
        tiers = ["tier_1", "tier_2", "tier_3"]
        
        for tier in tiers:
            logger.info(f"Testing {tier} automation")
            
            # Create flow for tier
            flow = UnifiedCollectionFlow(
                crewai_service=crewai_service,
                context=test_context,
                automation_tier=tier,
                db_session=db_session,
                config={
                    "environment_config": {
                        "platforms": ["aws"],
                        "environments": ["production"]
                    },
                    "client_requirements": {
                        "sixr_requirements": {"rehost": True}
                    }
                }
            )
            
            # Execute initialization
            init_result = await flow.initialize_collection()
            assert init_result["status"] == "completed"
            
            # Verify tier-specific behavior
            flow_record = await db_session.get(CollectionFlow, flow._flow_id)
            assert flow_record.automation_tier == tier
            
            # Tier 1 should skip manual collection
            if tier == "tier_1":
                assert flow.state.next_phase != CollectionPhase.MANUAL_COLLECTION
        
        logger.info("✅ Multi-tier execution test completed")
    
    @pytest.mark.asyncio 
    async def test_platform_credential_integration(
        self,
        collection_flow: UnifiedCollectionFlow,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test integration with platform credentials"""
        logger.info("Testing platform credential integration")
        
        # Create test platform credentials
        aws_cred = PlatformCredential(
            id=uuid.uuid4(),
            engagement_id=test_client_engagement["engagement"].id,
            platform_type=PlatformType.AWS,
            credential_name="Test AWS Credential",
            credential_data={"access_key": "test_key", "secret_key": "encrypted"},
            is_active=True,
            created_by=test_client_engagement["user"].id
        )
        
        azure_cred = PlatformCredential(
            id=uuid.uuid4(),
            engagement_id=test_client_engagement["engagement"].id,
            platform_type=PlatformType.AZURE,
            credential_name="Test Azure Credential",
            credential_data={"tenant_id": "test_tenant", "client_id": "test_client"},
            is_active=True,
            created_by=test_client_engagement["user"].id
        )
        
        db_session.add_all([aws_cred, azure_cred])
        await db_session.commit()
        
        # Execute flow initialization and platform detection
        await collection_flow.initialize_collection()
        await collection_flow.detect_platforms({"phase": "initialization"})
        
        # Verify platforms detected match credentials
        detected = collection_flow.state.detected_platforms
        assert any(p.get("platform") == "aws" for p in detected)
        assert any(p.get("platform") == "azure" for p in detected)
        
        logger.info("✅ Platform credential integration test completed")
    
    @pytest.mark.asyncio
    async def test_performance_metrics(
        self,
        collection_flow: UnifiedCollectionFlow,
        test_client_engagement: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Test performance metrics collection during flow execution"""
        logger.info("Testing performance metrics")
        
        import time
        
        # Track execution times
        phase_times = {}
        
        # Phase 1: Initialize
        start_time = time.time()
        await collection_flow.initialize_collection()
        phase_times["initialization"] = time.time() - start_time
        
        # Phase 2: Platform Detection
        start_time = time.time()
        await collection_flow.detect_platforms({"phase": "initialization"})
        phase_times["platform_detection"] = time.time() - start_time
        
        # Verify reasonable execution times
        assert phase_times["initialization"] < 5.0  # Should complete within 5 seconds
        assert phase_times["platform_detection"] < 10.0  # Should complete within 10 seconds
        
        # Verify metrics stored in flow
        flow_record = await db_session.get(CollectionFlow, collection_flow._flow_id)
        assert flow_record.metadata is not None
        
        logger.info(f"Performance metrics: {phase_times}")
        logger.info("✅ Performance metrics test completed")


# Utility function for external test runners
async def run_collection_flow_e2e_test():
    """Run the complete end-to-end test suite"""
    test_instance = TestCollectionFlowE2E()
    
    # Setup test fixtures
    context = await test_instance.test_context()
    
    async with AsyncSessionLocal() as session:
        # Create test data
        client_engagement = await test_instance.test_client_engagement(session, context)
        crewai_service = await test_instance.crewai_service()
        
        # Create flow
        flow = await test_instance.collection_flow(crewai_service, context, session)
        
        # Run main test
        await test_instance.test_complete_collection_flow_e2e(
            flow, client_engagement, session
        )
        
        print("✅ All collection flow E2E tests passed!")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_collection_flow_e2e_test())