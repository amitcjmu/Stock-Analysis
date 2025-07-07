"""
End-to-end test for Data Import page load
Simulates the exact API calls made when loading the Data Import page
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
from datetime import datetime

from app.models import User, UserProfile, Client, Engagement
from app.core.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
class TestDataImportPageLoad:
    """Test the complete flow of loading the Data Import page"""
    
    async def setup_test_data(self, db: AsyncSession):
        """Set up complete test data including user profile"""
        # Create client
        client = Client(
            id=uuid.uuid4(),
            name="Test Client",
            code="TC001",
            is_active=True
        )
        db.add(client)
        
        # Create engagement
        engagement = Engagement(
            id=uuid.uuid4(),
            client_id=client.id,
            name="Test Engagement",
            code="TE001",
            is_active=True
        )
        db.add(engagement)
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email="testuser@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test User",
            is_active=True,
            role="user"
        )
        db.add(user)
        
        # Create user profile (CRITICAL - required for login)
        user_profile = UserProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            client_id=client.id,
            engagement_id=engagement.id,
            status="active",  # MUST be 'active' to login
            role="user"
        )
        db.add(user_profile)
        
        await db.commit()
        await db.refresh(user)
        await db.refresh(client)
        await db.refresh(engagement)
        
        return user, client, engagement
    
    async def test_data_import_page_load_sequence(self, client: AsyncClient, db: AsyncSession):
        """Test the complete sequence of API calls when loading Data Import page"""
        # Setup test data
        user, test_client, engagement = await self.setup_test_data(db)
        
        # Generate auth token
        access_token = create_access_token(data={"sub": user.email})
        
        # Headers that frontend would send
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Client-Account-ID": str(test_client.id),
            "X-Engagement-ID": str(engagement.id),
            "X-User-ID": str(user.id),
            "Content-Type": "application/json"
        }
        
        # 1. First API call - Get client context (from navigation)
        response = await client.get("/api/v1/context/clients", headers=headers)
        assert response.status_code == 200
        
        # 2. Second API call - Get active flows (from useIncompleteFlowDetectionV2)
        response = await client.get(
            "/api/v1/flows/?flowType=discovery",
            headers=headers
        )
        
        # This should not fail!
        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        assert isinstance(data["flows"], list)
        assert "total" in data
        
        # Verify response structure matches what frontend expects
        if data["flows"]:
            flow = data["flows"][0]
            required_fields = [
                "flow_id", "flow_type", "status", "created_at", 
                "updated_at", "created_by", "configuration", "metadata"
            ]
            for field in required_fields:
                assert field in flow, f"Missing required field: {field}"
            
            # Verify field types
            assert isinstance(flow["configuration"], dict)
            assert isinstance(flow["metadata"], dict)
    
    async def test_data_import_page_with_existing_flows(self, client: AsyncClient, db: AsyncSession):
        """Test page load when there are existing flows"""
        # Setup test data
        user, test_client, engagement = await self.setup_test_data(db)
        
        # Create some existing flows
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        
        for i in range(3):
            flow = CrewAIFlowStateExtensions(
                flow_id=uuid.uuid4(),
                client_account_id=test_client.id,
                engagement_id=engagement.id,
                user_id=str(user.id),
                flow_type="discovery",
                flow_name=f"Test Flow {i}",
                flow_status="running" if i == 0 else "completed",
                flow_configuration={"index": i}
            )
            db.add(flow)
        await db.commit()
        
        # Generate auth token
        access_token = create_access_token(data={"sub": user.email})
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Client-Account-ID": str(test_client.id),
            "X-Engagement-ID": str(engagement.id),
            "X-User-ID": str(user.id)
        }
        
        # Test the flows API call
        response = await client.get(
            "/api/v1/flows/?flowType=discovery",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["flows"]) == 3
        
        # Verify we have one running flow
        running_flows = [f for f in data["flows"] if f["status"] == "running"]
        assert len(running_flows) == 1
    
    async def test_admin_user_with_demo_context(self, client: AsyncClient, db: AsyncSession):
        """Test admin user loading page with demo UUIDs"""
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass123"),
            full_name="Admin User",
            is_active=True,
            role="platform_admin"
        )
        db.add(admin)
        
        # Admin user profile without client/engagement
        admin_profile = UserProfile(
            id=uuid.uuid4(),
            user_id=admin.id,
            status="active",
            role="platform_admin"
        )
        db.add(admin_profile)
        await db.commit()
        
        # Generate auth token
        access_token = create_access_token(data={"sub": admin.email})
        
        # Headers with demo UUIDs (what frontend sends for admin users)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
            "X-User-ID": str(admin.id)
        }
        
        # This should work without errors
        response = await client.get(
            "/api/v1/flows/?flowType=discovery",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
    
    async def test_missing_auth_headers(self, client: AsyncClient, db: AsyncSession):
        """Test proper error when auth headers are missing"""
        # No auth header
        response = await client.get("/api/v1/flows/?flowType=discovery")
        assert response.status_code == 401
        
        # Auth but no tenant headers
        user, _, _ = await self.setup_test_data(db)
        access_token = create_access_token(data={"sub": user.email})
        
        response = await client.get(
            "/api/v1/flows/?flowType=discovery",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 400  # Missing tenant context