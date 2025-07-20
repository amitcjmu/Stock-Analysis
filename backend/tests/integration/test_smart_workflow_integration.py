"""
Smart Workflow Integration Tests

Comprehensive integration tests for the Collection → Discovery → Assessment smart workflow,
validating end-to-end functionality, state transitions, and data flow integrity.

Generated with CC for ADCS end-to-end integration testing.
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Dict, List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.services.integration.smart_workflow_orchestrator import (
    SmartWorkflowOrchestrator,
    SmartWorkflowContext,
    WorkflowPhase
)
from app.services.integration.data_flow_validator import DataFlowValidator
from app.services.integration.state_synchronizer import StateSynchronizer
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset
from app.models import ClientAccount, Engagement, User


class SmartWorkflowIntegrationTests:
    """Integration tests for smart workflow orchestration"""
    
    @pytest.fixture
    async def test_context(self):
        """Create test context with user, client, and engagement"""
        async with AsyncSessionLocal() as session:
            # Create test user
            user = User(
                id=uuid4(),
                username="test_user",
                email="test@example.com",
                hashed_password="test_hash",
                is_active=True
            )
            session.add(user)
            
            # Create test client
            client = ClientAccount(
                id=uuid4(),
                account_name="Test Client",
                industry="Technology",
                company_size="Large",
                primary_contact_email="client@example.com"
            )
            session.add(client)
            
            # Create test engagement
            engagement = Engagement(
                id=uuid4(),
                name="Test Engagement",
                client_id=client.id,
                created_by=user.id,
                status="active"
            )
            session.add(engagement)
            
            await session.commit()
            
            yield {
                "user_id": user.id,
                "client_id": client.id,
                "engagement_id": engagement.id,
                "session": session
            }
            
            # Cleanup
            await session.execute(delete(Asset).where(Asset.engagement_id == engagement.id))
            await session.execute(delete(CollectionFlow).where(CollectionFlow.engagement_id == engagement.id))
            await session.execute(delete(DiscoveryFlow).where(DiscoveryFlow.engagement_id == engagement.id))
            await session.execute(delete(AssessmentFlow).where(AssessmentFlow.engagement_id == engagement.id))
            await session.execute(delete(Engagement).where(Engagement.id == engagement.id))
            await session.execute(delete(ClientAccount).where(ClientAccount.id == client.id))
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()
    
    @pytest.fixture
    def orchestrator(self):
        """Create smart workflow orchestrator instance"""
        return SmartWorkflowOrchestrator()
    
    @pytest.fixture
    def validator(self):
        """Create data flow validator instance"""
        return DataFlowValidator()
    
    @pytest.fixture
    def synchronizer(self):
        """Create state synchronizer instance"""
        return StateSynchronizer()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self, test_context, orchestrator):
        """Test complete workflow execution from collection to assessment"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Create initial collection flow with completed status
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                automation_tier="tier_1",
                confidence_score=0.85,
                metadata={"asset_count": 5}
            )
            session.add(collection_flow)
            
            # Create test assets
            for i in range(5):
                asset = Asset(
                    id=uuid4(),
                    engagement_id=engagement_id,
                    name=f"Test Asset {i+1}",
                    type="application",
                    environment="production",
                    business_criticality=4,
                    confidence_score=0.8,
                    status="active"
                )
                session.add(asset)
                
            await session.commit()
        
        # Execute smart workflow
        workflow_context = await orchestrator.execute_smart_workflow(
            engagement_id=engagement_id,
            user_id=user_id,
            client_id=client_id,
            workflow_config={"automation_level": "high"}
        )
        
        # Validate workflow execution
        assert workflow_context.engagement_id == engagement_id
        assert workflow_context.user_id == user_id
        assert workflow_context.client_id == client_id
        assert len(workflow_context.phase_history) > 0
        
        # Check that phases were processed
        phase_types = [entry["phase"] for entry in workflow_context.phase_history]
        assert "collection" in phase_types
        
        # Validate data quality metrics
        assert "overall_confidence" in workflow_context.data_quality_metrics
        assert workflow_context.data_quality_metrics["overall_confidence"] > 0.0
        
    @pytest.mark.asyncio
    async def test_workflow_quality_gates(self, test_context, orchestrator):
        """Test workflow quality gates and phase transitions"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Create collection flow with low quality
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                automation_tier="tier_1",
                confidence_score=0.5,  # Low confidence
                metadata={"asset_count": 1}
            )
            session.add(collection_flow)
            
            # Create single asset with low confidence
            asset = Asset(
                id=uuid4(),
                engagement_id=engagement_id,
                name="Low Quality Asset",
                type="application",
                environment="production",
                business_criticality=1,  # Low criticality
                confidence_score=0.5,   # Low confidence
                status="active"
            )
            session.add(asset)
            
            await session.commit()
        
        # Execute workflow - should handle low quality gracefully
        workflow_context = await orchestrator.execute_smart_workflow(
            engagement_id=engagement_id,
            user_id=user_id,
            client_id=client_id
        )
        
        # Validate that quality issues are tracked
        assert "overall_confidence" in workflow_context.data_quality_metrics
        confidence = workflow_context.data_quality_metrics["overall_confidence"]
        assert confidence <= 0.7  # Should reflect low quality
        
    @pytest.mark.asyncio
    async def test_workflow_status_tracking(self, test_context, orchestrator):
        """Test workflow status tracking and reporting"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Get initial status (should be empty)
        initial_status = await orchestrator.get_workflow_status(engagement_id)
        assert initial_status["current_phase"] == "collection"
        assert initial_status["overall_status"] == "pending"
        
        # Create collection flow
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="in_progress",
                current_phase="automated_collection",
                progress_percentage=50.0,
                automation_tier="tier_1"
            )
            session.add(collection_flow)
            await session.commit()
        
        # Get status with collection in progress
        progress_status = await orchestrator.get_workflow_status(engagement_id)
        assert progress_status["current_phase"] == "collection"
        assert progress_status["overall_status"] == "in_progress"
        assert progress_status["flows"]["collection"]["exists"] is True
        assert progress_status["flows"]["collection"]["status"] == "in_progress"
        
    @pytest.mark.asyncio
    async def test_cross_flow_integration(self, test_context, orchestrator, synchronizer):
        """Test integration between collection, discovery, and assessment flows"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Create completed collection flow
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                automation_tier="tier_1",
                confidence_score=0.85,
                metadata={"asset_count": 3}
            )
            session.add(collection_flow)
            
            # Create assets
            for i in range(3):
                asset = Asset(
                    id=uuid4(),
                    engagement_id=engagement_id,
                    name=f"Asset {i+1}",
                    type="application",
                    environment="production",
                    business_criticality=4,
                    confidence_score=0.8,
                    status="active"
                )
                session.add(asset)
                
            await session.commit()
        
        # Execute workflow to create discovery flow
        await orchestrator.execute_smart_workflow(
            engagement_id=engagement_id,
            user_id=user_id,
            client_id=client_id
        )
        
        # Synchronize state
        sync_context = await synchronizer.synchronize_engagement_state(engagement_id)
        
        # Validate synchronization
        assert engagement_id in sync_context.flows or len(sync_context.flows) > 0
        assert len(sync_context.assets_snapshot) == 3
        
        # Check for conflicts
        assert len(sync_context.conflicts) == 0 or all(
            conflict["severity"] != "critical" for conflict in sync_context.conflicts
        )
        
    @pytest.mark.asyncio
    async def test_data_flow_validation_integration(self, test_context, validator):
        """Test data flow validation across workflow phases"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        
        # Create flows and assets for validation
        async with AsyncSessionLocal() as session:
            # Collection flow
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=context_data["user_id"],
                client_id=context_data["client_id"],
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                confidence_score=0.85
            )
            session.add(collection_flow)
            
            # Discovery flow
            discovery_flow = DiscoveryFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=context_data["user_id"],
                client_id=context_data["client_id"],
                status="completed",
                current_phase="completed",
                progress_percentage=100.0
            )
            session.add(discovery_flow)
            
            # Assets with good data quality
            for i in range(3):
                asset = Asset(
                    id=uuid4(),
                    engagement_id=engagement_id,
                    name=f"Validated Asset {i+1}",
                    type="application",
                    environment="production",
                    business_criticality=4,
                    confidence_score=0.85,
                    technical_fit_score=0.8,
                    status="active",
                    technical_details={"discovery_enriched": True}
                )
                session.add(asset)
                
            await session.commit()
        
        # Run validation
        validation_result = await validator.validate_end_to_end_data_flow(engagement_id)
        
        # Validate results
        assert validation_result.engagement_id == engagement_id
        assert validation_result.overall_score > 0.0
        assert "collection" in validation_result.phase_scores
        assert "discovery" in validation_result.phase_scores
        
        # Check for minimal issues with good data
        critical_issues = [
            issue for issue in validation_result.issues
            if issue.severity.value == "critical"
        ]
        assert len(critical_issues) == 0
        
    @pytest.mark.asyncio
    async def test_workflow_error_resilience(self, test_context, orchestrator):
        """Test workflow resilience to errors and recovery"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Create collection flow with potential issues
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                automation_tier="tier_1",
                confidence_score=0.6,  # Borderline confidence
                metadata={"asset_count": 0}  # No assets - potential issue
            )
            session.add(collection_flow)
            await session.commit()
        
        # Execute workflow - should handle gracefully
        try:
            workflow_context = await orchestrator.execute_smart_workflow(
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id
            )
            
            # Should complete without throwing exception
            assert workflow_context is not None
            assert workflow_context.engagement_id == engagement_id
            
        except Exception as e:
            pytest.fail(f"Workflow should handle errors gracefully, but raised: {e}")
            
    @pytest.mark.asyncio
    async def test_workflow_performance_tracking(self, test_context, orchestrator):
        """Test workflow performance tracking and metrics"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Record start time
        start_time = datetime.utcnow()
        
        # Create realistic test data
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                automation_tier="tier_1",
                confidence_score=0.85,
                metadata={"asset_count": 10}
            )
            session.add(collection_flow)
            
            # Create multiple assets
            for i in range(10):
                asset = Asset(
                    id=uuid4(),
                    engagement_id=engagement_id,
                    name=f"Performance Asset {i+1}",
                    type="application",
                    environment="production",
                    business_criticality=4,
                    confidence_score=0.8,
                    status="active"
                )
                session.add(asset)
                
            await session.commit()
        
        # Execute workflow
        workflow_context = await orchestrator.execute_smart_workflow(
            engagement_id=engagement_id,
            user_id=user_id,
            client_id=client_id
        )
        
        # Record end time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Validate performance
        assert execution_time < 30.0  # Should complete within 30 seconds
        assert workflow_context is not None
        
        # Check for performance metrics in context
        assert len(workflow_context.phase_history) > 0
        
    @pytest.mark.asyncio
    async def test_workflow_scalability(self, test_context, orchestrator):
        """Test workflow scalability with larger datasets"""
        
        context_data = test_context
        engagement_id = context_data["engagement_id"]
        user_id = context_data["user_id"]
        client_id = context_data["client_id"]
        
        # Create large dataset
        asset_count = 50  # Larger dataset
        
        async with AsyncSessionLocal() as session:
            collection_flow = CollectionFlow(
                id=uuid4(),
                engagement_id=engagement_id,
                user_id=user_id,
                client_id=client_id,
                status="completed",
                current_phase="completed",
                progress_percentage=100.0,
                automation_tier="tier_1",
                confidence_score=0.85,
                metadata={"asset_count": asset_count}
            )
            session.add(collection_flow)
            
            # Create many assets
            for i in range(asset_count):
                asset = Asset(
                    id=uuid4(),
                    engagement_id=engagement_id,
                    name=f"Scalability Asset {i+1}",
                    type="application" if i % 2 == 0 else "database",
                    environment="production",
                    business_criticality=3 + (i % 3),
                    confidence_score=0.7 + (i % 3) * 0.1,
                    status="active"
                )
                session.add(asset)
                
            await session.commit()
        
        # Execute workflow with large dataset
        start_time = datetime.utcnow()
        
        workflow_context = await orchestrator.execute_smart_workflow(
            engagement_id=engagement_id,
            user_id=user_id,
            client_id=client_id
        )
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Validate scalability
        assert workflow_context is not None
        assert execution_time < 60.0  # Should scale reasonably
        assert "asset_count" in workflow_context.data_quality_metrics
        assert workflow_context.data_quality_metrics["asset_count"] == asset_count
        
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, orchestrator):
        """Test concurrent execution of multiple workflows"""
        
        # Create multiple test engagements
        engagement_contexts = []
        
        async with AsyncSessionLocal() as session:
            for i in range(3):
                user = User(
                    id=uuid4(),
                    username=f"concurrent_user_{i}",
                    email=f"concurrent{i}@example.com",
                    hashed_password="test_hash",
                    is_active=True
                )
                session.add(user)
                
                client = ClientAccount(
                    id=uuid4(),
                    account_name=f"Concurrent Client {i}",
                    industry="Technology",
                    company_size="Large",
                    primary_contact_email=f"client{i}@example.com"
                )
                session.add(client)
                
                engagement = Engagement(
                    id=uuid4(),
                    name=f"Concurrent Engagement {i}",
                    client_id=client.id,
                    created_by=user.id,
                    status="active"
                )
                session.add(engagement)
                
                # Create collection flow for each
                collection_flow = CollectionFlow(
                    id=uuid4(),
                    engagement_id=engagement.id,
                    user_id=user.id,
                    client_id=client.id,
                    status="completed",
                    current_phase="completed",
                    progress_percentage=100.0,
                    automation_tier="tier_1",
                    confidence_score=0.85,
                    metadata={"asset_count": 5}
                )
                session.add(collection_flow)
                
                # Create assets
                for j in range(5):
                    asset = Asset(
                        id=uuid4(),
                        engagement_id=engagement.id,
                        name=f"Concurrent Asset {i}-{j}",
                        type="application",
                        environment="production",
                        business_criticality=4,
                        confidence_score=0.8,
                        status="active"
                    )
                    session.add(asset)
                
                engagement_contexts.append({
                    "engagement_id": engagement.id,
                    "user_id": user.id,
                    "client_id": client.id
                })
                
            await session.commit()
        
        try:
            # Execute workflows concurrently
            tasks = []
            for context in engagement_contexts:
                task = orchestrator.execute_smart_workflow(
                    engagement_id=context["engagement_id"],
                    user_id=context["user_id"],
                    client_id=context["client_id"]
                )
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Validate all completed successfully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Concurrent workflow {i} failed: {result}")
                
                assert result is not None
                assert result.engagement_id == engagement_contexts[i]["engagement_id"]
                
        finally:
            # Cleanup
            async with AsyncSessionLocal() as session:
                for context in engagement_contexts:
                    engagement_id = context["engagement_id"]
                    client_id = context["client_id"]
                    user_id = context["user_id"]
                    
                    await session.execute(delete(Asset).where(Asset.engagement_id == engagement_id))
                    await session.execute(delete(CollectionFlow).where(CollectionFlow.engagement_id == engagement_id))
                    await session.execute(delete(DiscoveryFlow).where(DiscoveryFlow.engagement_id == engagement_id))
                    await session.execute(delete(AssessmentFlow).where(AssessmentFlow.engagement_id == engagement_id))
                    await session.execute(delete(Engagement).where(Engagement.id == engagement_id))
                    await session.execute(delete(ClientAccount).where(ClientAccount.id == client_id))
                    await session.execute(delete(User).where(User.id == user_id))
                    
                await session.commit()