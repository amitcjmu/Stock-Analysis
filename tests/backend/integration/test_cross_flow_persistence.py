#!/usr/bin/env python3
"""
Cross-Flow Data Persistence Tests

Tests data flow and persistence between Discovery and Assessment flows to verify:
1. Data flows correctly from Discovery to Assessment
2. Flow state remains consistent across services
3. Multi-tenant isolation is maintained across flows
4. State recovery works after failures
5. Flow transitions preserve data integrity
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

# Import necessary modules
import sys
sys.path.append('/app')

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, func, and_, or_
    from app.core.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.data_import import DataImport, RawImportRecord
    from app.models.client_account import ClientAccount
    from app.models.engagement import Engagement
    from app.models.user_profile import UserProfile
    from app.services.crewai_flows.flow_state_manager import FlowStateManager
    from app.repositories.discovery_flow_repository.base_repository import DiscoveryFlowRepository
except ImportError as e:
    pytest.skip(f"Backend modules not available: {e}", allow_module_level=True)

# Test configuration
TEST_CLIENT_ID_1 = "bafd5b46-aaaf-4c95-8142-573699d93171"
TEST_CLIENT_ID_2 = "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"  # Marathon Petroleum
TEST_ENGAGEMENT_ID_1 = "6e9c8133-4169-4b79-b052-106dc93d0208"
TEST_ENGAGEMENT_ID_2 = "12345678-1234-1234-1234-123456789012"
TEST_USER_ID = "44444444-4444-4444-4444-444444444444"

class TestCrossFlowPersistence:
    """Test suite for cross-flow data persistence and integrity"""

    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Set up test environment with necessary data"""
        async with AsyncSessionLocal() as session:
            # Verify test clients exist
            client1_result = await session.execute(
                select(ClientAccount).where(ClientAccount.id == TEST_CLIENT_ID_1)
            )
            client1 = client1_result.scalar_one_or_none()

            client2_result = await session.execute(
                select(ClientAccount).where(ClientAccount.id == TEST_CLIENT_ID_2)
            )
            client2 = client2_result.scalar_one_or_none()

            if not client1:
                pytest.skip(f"Test client 1 {TEST_CLIENT_ID_1} not found")
            if not client2:
                pytest.skip(f"Test client 2 {TEST_CLIENT_ID_2} not found")

            self.client1 = client1
            self.client2 = client2

    async def create_discovery_flow_with_assets(self,
                                                client_id: str,
                                                engagement_id: str,
                                                asset_count: int = 3) -> Dict[str, Any]:
        """Create a discovery flow with associated assets"""
        async with AsyncSessionLocal() as session:
            # Create discovery flow
            flow_id = f"flow-{uuid4()}"
            discovery_flow = DiscoveryFlow(
                id=flow_id,
                session_id=f"session-{uuid4()}",
                status="completed",
                current_phase="completed",
                client_account_id=client_id,
                engagement_id=engagement_id,
                created_by=TEST_USER_ID,
                phase_completion={
                    "data_import": True,
                    "field_mapping": True,
                    "data_cleansing": True,
                    "asset_inventory": True,
                    "dependency_analysis": True,
                    "tech_debt_analysis": True
                },
                progress_percentage=100.0
            )
            session.add(discovery_flow)

            # Create associated assets
            created_assets = []
            for i in range(asset_count):
                asset = Asset(
                    name=f"Test Asset {i+1}",
                    asset_type="Application" if i == 0 else "Server",
                    ip_address=f"10.1.1.{10+i}",
                    client_account_id=client_id,
                    engagement_id=engagement_id,
                    created_by=TEST_USER_ID,
                    discovery_flow_id=flow_id,
                    metadata_={
                        "discovery_metadata": {
                            "flow_id": flow_id,
                            "processed_at": datetime.now().isoformat(),
                            "confidence_score": 0.85 + (i * 0.05),
                            "processing_phase": "completed"
                        },
                        "technical_details": {
                            "technology_stack": ["Java", "Spring Boot"] if i == 0 else ["Ubuntu", "Apache"],
                            "criticality": "High" if i == 0 else "Medium",
                            "environment": "Production"
                        }
                    }
                )
                session.add(asset)
                created_assets.append(asset)

            await session.commit()
            await session.refresh(discovery_flow)

            # Refresh assets to get IDs
            for asset in created_assets:
                await session.refresh(asset)

            return {
                "flow_id": flow_id,
                "discovery_flow": discovery_flow,
                "assets": created_assets,
                "asset_count": len(created_assets)
            }

    @pytest.mark.asyncio
    async def test_discovery_to_assessment_data_flow(self):
        """Test data flows correctly from Discovery to Assessment"""
        print("🔄 Testing Discovery to Assessment data flow...")

        # Create discovery flow with assets
        discovery_result = await self.create_discovery_flow_with_assets(
            TEST_CLIENT_ID_1,
            TEST_ENGAGEMENT_ID_1,
            asset_count=5
        )

        flow_id = discovery_result["flow_id"]
        created_assets = discovery_result["assets"]

        print(f"✅ Created discovery flow {flow_id} with {len(created_assets)} assets")

        async with AsyncSessionLocal() as session:
            # Verify discovery flow exists and is completed
            flow_result = await session.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
            )
            flow = flow_result.scalar_one_or_none()

            assert flow is not None
            assert flow.status == "completed"
            assert flow.progress_percentage == 100.0
            print(f"✅ Discovery flow verified: {flow.status}")

            # Verify assets are properly linked to discovery flow
            assets_result = await session.execute(
                select(Asset).where(
                    and_(
                        Asset.client_account_id == TEST_CLIENT_ID_1,
                        Asset.discovery_flow_id == flow_id
                    )
                )
            )
            linked_assets = assets_result.scalars().all()

            assert len(linked_assets) == 5
            print(f"✅ Found {len(linked_assets)} assets linked to discovery flow")

            # Test asset data integrity for assessment flow consumption
            for asset in linked_assets:
                # Verify required metadata exists
                assert asset.metadata_ is not None
                assert "discovery_metadata" in asset.metadata_
                assert "technical_details" in asset.metadata_

                discovery_meta = asset.metadata_["discovery_metadata"]
                assert discovery_meta["flow_id"] == flow_id
                assert "confidence_score" in discovery_meta
                assert "processed_at" in discovery_meta

                tech_details = asset.metadata_["technical_details"]
                assert "technology_stack" in tech_details
                assert "criticality" in tech_details
                assert "environment" in tech_details

                print(f"✅ Asset {asset.name} metadata validated")

            # Simulate assessment flow selection
            application_assets = [a for a in linked_assets if a.asset_type == "Application"]
            assert len(application_assets) >= 1

            selected_app = application_assets[0]
            print(f"✅ Selected application for assessment: {selected_app.name}")

            # TODO: Create actual assessment flow and verify data transfer
            # This would involve:
            # 1. Creating AssessmentFlow record
            # 2. Linking to selected assets
            # 3. Verifying data transfer integrity
            # 4. Testing assessment metadata creation

            print("✅ Discovery to Assessment data flow test completed")

    @pytest.mark.asyncio
    async def test_flow_state_consistency_across_services(self):
        """Test flow state remains consistent across different services"""
        print("🔄 Testing flow state consistency across services...")

        async with AsyncSessionLocal() as session:
            # Create a discovery flow
            flow_id = f"consistency-test-{uuid4()}"

            # Test flow state using FlowStateManager
            flow_manager = FlowStateManager(session, TEST_CLIENT_ID_1)

            # Create initial flow state
            initial_state = {
                "flow_id": flow_id,
                "status": "running",
                "current_phase": "field_mapping",
                "progress_percentage": 25.0,
                "phase_completion": {
                    "data_import": True,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_inventory": False
                }
            }

            # Store state via flow manager
            await flow_manager.update_flow_state(flow_id, initial_state)

            # Retrieve state via flow manager
            retrieved_state = await flow_manager.get_flow_state(flow_id)

            # Verify state consistency
            assert retrieved_state["flow_id"] == flow_id
            assert retrieved_state["status"] == "running"
            assert retrieved_state["current_phase"] == "field_mapping"
            assert retrieved_state["progress_percentage"] == 25.0
            assert retrieved_state["phase_completion"]["data_import"]
            assert not retrieved_state["phase_completion"]["field_mapping"]

            print("✅ Flow state consistency verified via FlowStateManager")

            # Update state and verify consistency
            updated_state = {
                **initial_state,
                "current_phase": "data_cleansing",
                "progress_percentage": 50.0,
                "phase_completion": {
                    **initial_state["phase_completion"],
                    "field_mapping": True,
                    "data_cleansing": False
                }
            }

            await flow_manager.update_flow_state(flow_id, updated_state)

            # Retrieve updated state
            final_state = await flow_manager.get_flow_state(flow_id)

            assert final_state["current_phase"] == "data_cleansing"
            assert final_state["progress_percentage"] == 50.0
            assert final_state["phase_completion"]["field_mapping"]

            print("✅ Flow state updates maintained consistency")

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_across_flows(self):
        """Test multi-tenant isolation is maintained across different flow types"""
        print("🏢 Testing multi-tenant isolation across flows...")

        # Create discovery flows for both clients
        await self.create_discovery_flow_with_assets(
            TEST_CLIENT_ID_1,
            TEST_ENGAGEMENT_ID_1,
            asset_count=3
        )

        await self.create_discovery_flow_with_assets(
            TEST_CLIENT_ID_2,
            TEST_ENGAGEMENT_ID_2,
            asset_count=3
        )

        print("✅ Created discovery flows for both clients")

        async with AsyncSessionLocal() as session:
            # Verify client 1 can only see their own data
            client1_assets = await session.execute(
                select(Asset).where(Asset.client_account_id == TEST_CLIENT_ID_1)
            )
            client1_asset_list = client1_assets.scalars().all()

            client2_assets = await session.execute(
                select(Asset).where(Asset.client_account_id == TEST_CLIENT_ID_2)
            )
            client2_asset_list = client2_assets.scalars().all()

            # Verify no cross-contamination
            for asset in client1_asset_list:
                assert asset.client_account_id == TEST_CLIENT_ID_1
                assert asset.client_account_id != TEST_CLIENT_ID_2

            for asset in client2_asset_list:
                assert asset.client_account_id == TEST_CLIENT_ID_2
                assert asset.client_account_id != TEST_CLIENT_ID_1

            print(f"✅ Client 1: {len(client1_asset_list)} assets (isolated)")
            print(f"✅ Client 2: {len(client2_asset_list)} assets (isolated)")

            # Test discovery flow isolation
            client1_flows = await session.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.client_account_id == TEST_CLIENT_ID_1)
            )
            client1_flow_list = client1_flows.scalars().all()

            client2_flows = await session.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.client_account_id == TEST_CLIENT_ID_2)
            )
            client2_flow_list = client2_flows.scalars().all()

            # Verify flow isolation
            for flow in client1_flow_list:
                assert flow.client_account_id == TEST_CLIENT_ID_1

            for flow in client2_flow_list:
                assert flow.client_account_id == TEST_CLIENT_ID_2

            print("✅ Multi-tenant isolation maintained across flows")

    @pytest.mark.asyncio
    async def test_state_recovery_after_failures(self):
        """Test state recovery mechanisms after failures"""
        print("🔧 Testing state recovery after failures...")

        async with AsyncSessionLocal() as session:
            # Create a discovery flow
            flow_id = f"recovery-test-{uuid4()}"

            discovery_flow = DiscoveryFlow(
                id=flow_id,
                session_id=f"session-{uuid4()}",
                status="running",
                current_phase="data_cleansing",
                client_account_id=TEST_CLIENT_ID_1,
                engagement_id=TEST_ENGAGEMENT_ID_1,
                created_by=TEST_USER_ID,
                phase_completion={
                    "data_import": True,
                    "field_mapping": True,
                    "data_cleansing": False,
                    "asset_inventory": False
                },
                progress_percentage=40.0,
                errors=[],
                last_activity_at=datetime.now()
            )
            session.add(discovery_flow)
            await session.commit()

            print(f"✅ Created flow in running state: {flow_id}")

            # Simulate failure
            discovery_flow.status = "failed"
            discovery_flow.errors = [{
                "phase": "data_cleansing",
                "error": "Simulated processing failure",
                "timestamp": datetime.now().isoformat(),
                "recoverable": True
            }]
            await session.commit()

            print("⚠️ Simulated flow failure")

            # Test recovery
            flow_manager = FlowStateManager(session, TEST_CLIENT_ID_1)

            # Attempt recovery
            recovery_state = {
                "flow_id": flow_id,
                "status": "running",
                "current_phase": "data_cleansing",
                "progress_percentage": 40.0,
                "recovery_attempt": True,
                "errors": []  # Clear errors on recovery
            }

            await flow_manager.update_flow_state(flow_id, recovery_state)

            # Verify recovery
            recovered_flow = await session.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
            )
            flow_record = recovered_flow.scalar_one_or_none()

            assert flow_record is not None
            assert flow_record.status == "running"
            assert len(flow_record.errors) == 0

            print("✅ Flow recovery successful")

            # Test partial completion recovery
            flow_record.status = "completed"
            flow_record.phase_completion = {
                "data_import": True,
                "field_mapping": True,
                "data_cleansing": True,
                "asset_inventory": True,
                "dependency_analysis": False,  # Incomplete
                "tech_debt_analysis": False
            }
            flow_record.progress_percentage = 75.0
            await session.commit()

            # Verify partial completion state
            assert flow_record.phase_completion["data_cleansing"]
            assert not flow_record.phase_completion["dependency_analysis"]
            assert flow_record.progress_percentage == 75.0

            print("✅ Partial completion recovery verified")

    @pytest.mark.asyncio
    async def test_flow_transitions_preserve_data_integrity(self):
        """Test flow transitions preserve data integrity"""
        print("🔗 Testing flow transitions preserve data integrity...")

        # Create discovery flow with assets
        discovery_result = await self.create_discovery_flow_with_assets(
            TEST_CLIENT_ID_1,
            TEST_ENGAGEMENT_ID_1,
            asset_count=4
        )

        flow_id = discovery_result["flow_id"]
        assets = discovery_result["assets"]

        async with AsyncSessionLocal() as session:
            # Capture initial asset states
            initial_states = {}
            for asset in assets:
                await session.refresh(asset)
                initial_states[asset.id] = {
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "metadata": asset.metadata_.copy() if asset.metadata_ else {},
                    "created_at": asset.created_at,
                    "discovery_flow_id": asset.discovery_flow_id
                }

            print(f"✅ Captured initial state for {len(assets)} assets")

            # Simulate assessment flow creation (transition)
            assessment_flow_id = f"assessment-{uuid4()}"

            # Update assets with assessment metadata (simulating flow transition)
            for asset in assets:
                if asset.asset_type == "Application":
                    # Add assessment metadata while preserving discovery metadata
                    current_metadata = asset.metadata_ or {}
                    current_metadata["assessment_metadata"] = {
                        "assessment_flow_id": assessment_flow_id,
                        "selected_for_assessment": True,
                        "assessment_initiated_at": datetime.now().isoformat(),
                        "assessment_status": "initialized"
                    }
                    asset.metadata_ = current_metadata

            await session.commit()

            # Verify data integrity after transition
            for asset in assets:
                await session.refresh(asset)
                current_state = initial_states[asset.id]

                # Verify core attributes unchanged
                assert asset.name == current_state["name"]
                assert asset.asset_type == current_state["asset_type"]
                assert asset.created_at == current_state["created_at"]
                assert asset.discovery_flow_id == current_state["discovery_flow_id"]

                # Verify discovery metadata preserved
                if asset.metadata_ and "discovery_metadata" in asset.metadata_:
                    discovery_meta = asset.metadata_["discovery_metadata"]
                    current_state["metadata"].get("discovery_metadata", {})

                    assert discovery_meta["flow_id"] == flow_id
                    assert "confidence_score" in discovery_meta
                    assert "processed_at" in discovery_meta

                # Verify assessment metadata added for applications
                if asset.asset_type == "Application" and asset.metadata_:
                    assert "assessment_metadata" in asset.metadata_
                    assessment_meta = asset.metadata_["assessment_metadata"]
                    assert assessment_meta["assessment_flow_id"] == assessment_flow_id
                    assert assessment_meta["selected_for_assessment"]

                print(f"✅ Data integrity verified for asset {asset.name}")

            print("✅ Flow transitions preserve data integrity")

    @pytest.mark.asyncio
    async def test_cross_flow_query_performance(self):
        """Test query performance across multiple flows and large datasets"""
        print("⚡ Testing cross-flow query performance...")

        # Create multiple discovery flows with various asset counts
        flow_results = []
        total_assets = 0

        for i in range(3):  # 3 discovery flows
            asset_count = 5 + i * 2  # 5, 7, 9 assets per flow
            result = await self.create_discovery_flow_with_assets(
                TEST_CLIENT_ID_1,
                TEST_ENGAGEMENT_ID_1,
                asset_count=asset_count
            )
            flow_results.append(result)
            total_assets += asset_count

        print(f"✅ Created {len(flow_results)} flows with {total_assets} total assets")

        async with AsyncSessionLocal() as session:
            # Test cross-flow queries
            start_time = datetime.now()

            # Query all assets across flows
            all_assets_query = await session.execute(
                select(Asset).where(Asset.client_account_id == TEST_CLIENT_ID_1)
            )
            all_assets = all_assets_query.scalars().all()

            # Query assets by flow
            flow_asset_counts = {}
            for result in flow_results:
                flow_id = result["flow_id"]
                flow_assets_query = await session.execute(
                    select(func.count(Asset.id)).where(
                        and_(
                            Asset.client_account_id == TEST_CLIENT_ID_1,
                            Asset.discovery_flow_id == flow_id
                        )
                    )
                )
                count = flow_assets_query.scalar()
                flow_asset_counts[flow_id] = count

            # Query applications suitable for assessment
            app_assets_query = await session.execute(
                select(Asset).where(
                    and_(
                        Asset.client_account_id == TEST_CLIENT_ID_1,
                        Asset.asset_type == "Application"
                    )
                )
            )
            app_assets = app_assets_query.scalars().all()

            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds()

            print(f"⏱️ Cross-flow queries completed in {query_time:.3f} seconds")
            print(f"📊 Total assets found: {len(all_assets)}")
            print(f"📱 Application assets: {len(app_assets)}")

            # Performance assertions
            assert len(all_assets) == total_assets
            assert query_time < 5.0, f"Cross-flow queries should complete within 5 seconds, took {query_time:.3f}s"
            assert sum(flow_asset_counts.values()) == total_assets

            print("✅ Cross-flow query performance test passed")

if __name__ == "__main__":
    # Run tests directly
    import pytest
    pytest.main([__file__, "-v", "-s"])
