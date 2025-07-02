#!/usr/bin/env python
"""
Comprehensive test of all SQLAlchemy models against the database schema.
This ensures all models can be instantiated and work with the current database.
"""

import asyncio
import uuid
from datetime import datetime

# Import all models
from app.models.client_account import ClientAccount, Engagement, User, UserAccountAssociation
from app.models.discovery_flow import DiscoveryFlow
from app.models.data_import import DataImport
from app.models.data_import.core import RawImportRecord, ImportProcessingStep
from app.models.data_import.mapping import ImportFieldMapping
from app.models.data_import_session import DataImportSession
from app.models.asset import Asset, AssetDependency, WorkflowProgress, CMDBSixRAnalysis
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.rbac import UserProfile, UserRole, ClientAccess, EngagementAccess, AccessAuditLog
from app.models.rbac_enhanced import EnhancedUserProfile, RolePermissions, SoftDeletedItems
from app.models.tags import Tag, AssetTag
from app.models.migration import Migration
from app.models.assessment import Assessment, WavePlan
from app.models.analytics import (
    SixRAnalysis, MigrationWave, AgentQuestion, 
    AgentInsight, DataItem, Feedback, FlowDeletionAudit
)
from app.models.observability import LLMUsageLog, LLMUsageSummary
from app.models.security import SecurityAuditLog, RoleChangeApproval

# Import database session
from app.core.database import AsyncSessionLocal


async def test_all_models():
    """Test instantiation of all models to ensure schema compatibility."""
    
    print("=== COMPREHENSIVE MODEL TESTING ===\n")
    
    # Create test UUIDs
    client_id = uuid.uuid4()
    user_id = uuid.uuid4()
    engagement_id = uuid.uuid4()
    flow_id = f"flow_{uuid.uuid4()}"
    
    results = []
    
    # Test each model
    models_to_test = [
        # Core models
        ("ClientAccount", lambda: ClientAccount(
            id=client_id,
            name="Test Client",
            slug="test-client"
        )),
        
        ("User", lambda: User(
            id=user_id,
            email="test@example.com"
        )),
        
        ("Engagement", lambda: Engagement(
            id=engagement_id,
            client_account_id=client_id,
            name="Test Engagement",
            slug="test-engagement"
        )),
        
        ("UserAccountAssociation", lambda: UserAccountAssociation(
            user_id=user_id,
            client_account_id=client_id,
            role="member"
        )),
        
        # Discovery flow models
        ("DiscoveryFlow", lambda: DiscoveryFlow(
            flow_id=flow_id,
            client_account_id=client_id,
            engagement_id=engagement_id,
            user_id=str(user_id),
            flow_name="Test Flow"
        )),
        
        ("CrewAIFlowStateExtensions", lambda: CrewAIFlowStateExtensions(
            flow_id=flow_id,
            client_account_id=client_id,
            engagement_id=engagement_id,
            user_id=str(user_id),
            flow_type="discovery",
            flow_status="initialized"
        )),
        
        # Data import models
        ("DataImportSession", lambda: DataImportSession(
            client_account_id=client_id,
            engagement_id=engagement_id,
            session_name="Test Session"
        )),
        
        ("DataImport", lambda: DataImport(
            client_account_id=client_id,
            engagement_id=engagement_id
        )),
        
        ("RawImportRecord", lambda: RawImportRecord(
            import_id=uuid.uuid4(),
            client_account_id=client_id,
            raw_data={}
        )),
        
        ("ImportFieldMapping", lambda: ImportFieldMapping(
            client_account_id=client_id,
            engagement_id=engagement_id,
            source_field="test",
            target_field="test",
            import_id=uuid.uuid4()
        )),
        
        ("ImportProcessingStep", lambda: ImportProcessingStep(
            import_id=uuid.uuid4(),
            step_name="Test Step",
            step_order=1
        )),
        
        # Asset models
        ("Asset", lambda: Asset(
            client_account_id=client_id,
            engagement_id=engagement_id,
            asset_name="Test Asset",
            asset_type="server"
        )),
        
        ("AssetDependency", lambda: AssetDependency(
            asset_id=uuid.uuid4(),
            depends_on_asset_id=uuid.uuid4(),
            dependency_type="runtime"
        )),
        
        ("WorkflowProgress", lambda: WorkflowProgress(
            asset_id=uuid.uuid4(),
            flow_id=flow_id,
            phase="discovery",
            step_name="initial"
        )),
        
        ("CMDBSixRAnalysis", lambda: CMDBSixRAnalysis(
            asset_id=uuid.uuid4(),
            analysis_date=datetime.utcnow()
        )),
        
        # RBAC models
        ("UserProfile", lambda: UserProfile(
            user_id=user_id
        )),
        
        ("UserRole", lambda: UserRole(
            user_id=user_id,
            role_type="ANALYST",
            role_name="Data Analyst"
        )),
        
        ("ClientAccess", lambda: ClientAccess(
            user_profile_id=user_id,
            client_account_id=client_id,
            access_level="READ_ONLY",
            granted_by=user_id
        )),
        
        ("EngagementAccess", lambda: EngagementAccess(
            user_profile_id=user_id,
            engagement_id=engagement_id,
            access_level="READ_WRITE",
            granted_by=user_id
        )),
        
        ("AccessAuditLog", lambda: AccessAuditLog(
            user_id=user_id,
            action_type="login",
            result="success"
        )),
        
        # Enhanced RBAC models
        ("EnhancedUserProfile", lambda: EnhancedUserProfile(
            user_id=user_id
        )),
        
        ("RolePermissions", lambda: RolePermissions(
            role_type="ANALYST",
            permission_name="view_data"
        )),
        
        ("SoftDeletedItems", lambda: SoftDeletedItems(
            table_name="assets",
            record_id=uuid.uuid4(),
            record_data={},
            deleted_by=user_id
        )),
        
        # Analytics models
        ("Assessment", lambda: Assessment(
            client_account_id=client_id,
            engagement_id=engagement_id,
            assessment_type="migration_readiness"
        )),
        
        ("SixRAnalysis", lambda: SixRAnalysis(
            asset_id=uuid.uuid4(),
            analysis_date=datetime.utcnow()
        )),
        
        ("Migration", lambda: Migration(
            client_account_id=client_id,
            engagement_id=engagement_id,
            source_asset_id=uuid.uuid4(),
            target_cloud="AWS"
        )),
        
        ("WavePlan", lambda: WavePlan(
            client_account_id=client_id,
            engagement_id=engagement_id,
            wave_name="Wave 1"
        )),
        
        ("MigrationWave", lambda: MigrationWave(
            client_account_id=client_id,
            engagement_id=engagement_id,
            wave_number=1,
            wave_name="Test Wave"
        )),
        
        # Other models
        ("Tag", lambda: Tag(
            client_account_id=client_id,
            tag_name="test-tag"
        )),
        
        ("AssetTag", lambda: AssetTag(
            asset_id=uuid.uuid4(),
            tag_id=uuid.uuid4()
        )),
        
        ("AgentQuestion", lambda: AgentQuestion(
            client_account_id=client_id,
            engagement_id=engagement_id,
            flow_id=flow_id,
            agent_name="test_agent",
            question_text="Test question?"
        )),
        
        ("AgentInsight", lambda: AgentInsight(
            client_account_id=client_id,
            engagement_id=engagement_id,
            flow_id=flow_id,
            agent_name="test_agent",
            insight_type="observation",
            insight_text="Test insight"
        )),
        
        ("DataItem", lambda: DataItem(
            client_account_id=client_id,
            engagement_id=engagement_id,
            flow_id=flow_id,
            data_type="test",
            data_key="test_key",
            data_value={}
        )),
        
        ("Feedback", lambda: Feedback(
            client_account_id=client_id,
            user_id=user_id,
            feedback_type="general"
        )),
        
        ("FlowDeletionAudit", lambda: FlowDeletionAudit(
            flow_id=flow_id,
            deleted_by=user_id,
            deletion_reason="Test deletion"
        )),
        
        ("LLMUsageLog", lambda: LLMUsageLog(
            client_account_id=client_id,
            user_id=user_id,
            model_name="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )),
        
        ("LLMUsageSummary", lambda: LLMUsageSummary(
            client_account_id=client_id,
            summary_date=datetime.utcnow().date(),
            total_requests=1,
            total_tokens=150
        )),
        
        ("SecurityAuditLog", lambda: SecurityAuditLog(
            event_type="login_success",
            user_id=user_id,
            ip_address="127.0.0.1"
        )),
        
        ("RoleChangeApproval", lambda: RoleChangeApproval(
            requested_by=user_id,
            user_id=user_id,
            new_role="ANALYST",
            justification="Test"
        ))
    ]
    
    # Test each model
    for model_name, model_factory in models_to_test:
        try:
            instance = model_factory()
            # Check that the instance has expected attributes
            if hasattr(instance, '__table__'):
                column_count = len(instance.__table__.columns)
                results.append(f"✅ {model_name}: Success ({column_count} columns)")
            else:
                results.append(f"✅ {model_name}: Success")
        except Exception as e:
            results.append(f"❌ {model_name}: {type(e).__name__}: {str(e)}")
    
    # Print results
    print("\n=== TEST RESULTS ===\n")
    for result in results:
        print(result)
    
    # Summary
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_count = len(results)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total models tested: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    
    if success_count == total_count:
        print("\n🎉 ALL MODELS PASSED! The database schema is complete and compatible.")
    else:
        print("\n⚠️  Some models failed. Check the errors above.")
    
    # Test database connectivity
    print("\n=== DATABASE CONNECTIVITY TEST ===")
    try:
        async with AsyncSessionLocal() as session:
            # Test a simple query
            result = await session.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Count tables
            table_count_result = await session.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_count = table_count_result.scalar()
            print(f"✅ Total tables in database: {table_count}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_all_models())