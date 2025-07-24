#!/usr/bin/env python3
"""
Seed test data for Adaptive Data Collection System (ADCS)
Task A1.6: Create test seed data
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test data constants
TEST_ADAPTERS = [
    {
        "adapter_name": "servicenow_adapter",
        "adapter_type": "cmdb",
        "version": "1.0.0",
        "status": "active",
        "capabilities": ["asset_discovery", "dependency_mapping", "cmdb_sync"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "instance_url": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string", "format": "password"},
                "api_version": {"type": "string", "default": "v1"},
            },
            "required": ["instance_url", "username", "password"],
        },
        "supported_platforms": [
            "ServiceNow Madrid",
            "ServiceNow Paris",
            "ServiceNow Quebec",
        ],
        "required_credentials": ["api_key", "oauth_token"],
        "metadata": {
            "description": "ServiceNow CMDB integration adapter for automated asset discovery",
            "documentation_url": "https://docs.example.com/adapters/servicenow",
        },
    },
    {
        "adapter_name": "azure_resource_graph_adapter",
        "adapter_type": "cloud",
        "version": "2.0.0",
        "status": "active",
        "capabilities": ["cloud_discovery", "resource_tagging", "cost_analysis"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "client_secret": {"type": "string", "format": "password"},
                "subscription_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["tenant_id", "client_id", "client_secret"],
        },
        "supported_platforms": ["Azure"],
        "required_credentials": ["service_principal"],
        "metadata": {
            "description": "Azure Resource Graph adapter for cloud resource discovery",
            "rate_limits": {"requests_per_minute": 120},
        },
    },
    {
        "adapter_name": "vmware_vcenter_adapter",
        "adapter_type": "virtualization",
        "version": "1.5.0",
        "status": "active",
        "capabilities": ["vm_discovery", "host_mapping", "performance_metrics"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "vcenter_host": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string", "format": "password"},
                "port": {"type": "integer", "default": 443},
                "verify_ssl": {"type": "boolean", "default": True},
            },
            "required": ["vcenter_host", "username", "password"],
        },
        "supported_platforms": ["vCenter 6.7", "vCenter 7.0", "vCenter 8.0"],
        "required_credentials": ["vcenter_credentials"],
        "metadata": {
            "description": "VMware vCenter adapter for virtualization layer discovery"
        },
    },
    {
        "adapter_name": "aws_systems_manager_adapter",
        "adapter_type": "cloud",
        "version": "1.2.0",
        "status": "active",
        "capabilities": [
            "instance_discovery",
            "patch_compliance",
            "inventory_collection",
        ],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string"},
                "access_key_id": {"type": "string"},
                "secret_access_key": {"type": "string", "format": "password"},
                "role_arn": {"type": "string"},
            },
            "required": ["region", "access_key_id", "secret_access_key"],
        },
        "supported_platforms": ["AWS"],
        "required_credentials": ["aws_credentials"],
        "metadata": {
            "description": "AWS Systems Manager adapter for EC2 instance management"
        },
    },
    {
        "adapter_name": "manual_questionnaire_adapter",
        "adapter_type": "manual",
        "version": "1.0.0",
        "status": "active",
        "capabilities": ["manual_data_collection", "questionnaire_generation"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "questionnaire_template": {"type": "string"},
                "response_format": {"type": "string", "enum": ["json", "csv", "excel"]},
            },
        },
        "supported_platforms": ["All"],
        "required_credentials": [],
        "metadata": {"description": "Manual questionnaire adapter for gap filling"},
    },
]


async def create_test_platform_adapters(session: AsyncSession) -> List[uuid.UUID]:
    """Create test platform adapters"""
    adapter_ids = []

    for adapter_data in TEST_ADAPTERS:
        adapter_id = uuid.uuid4()
        adapter_ids.append(adapter_id)

        await session.execute(
            text(
                """
                INSERT INTO platform_adapters (
                    id, adapter_name, adapter_type, version, status,
                    capabilities, configuration_schema, supported_platforms,
                    required_credentials, metadata, created_at, updated_at
                ) VALUES (
                    :id, :adapter_name, :adapter_type, :version, :status,
                    :capabilities::jsonb, :configuration_schema::jsonb, :supported_platforms::jsonb,
                    :required_credentials::jsonb, :metadata::jsonb, now(), now()
                )
            """
            ),
            {
                "id": adapter_id,
                "adapter_name": adapter_data["adapter_name"],
                "adapter_type": adapter_data["adapter_type"],
                "version": adapter_data["version"],
                "status": adapter_data["status"],
                "capabilities": json.dumps(adapter_data["capabilities"]),
                "configuration_schema": json.dumps(
                    adapter_data["configuration_schema"]
                ),
                "supported_platforms": json.dumps(adapter_data["supported_platforms"]),
                "required_credentials": json.dumps(
                    adapter_data["required_credentials"]
                ),
                "metadata": json.dumps(adapter_data["metadata"]),
            },
        )

    await session.commit()
    print(f"✅ Created {len(adapter_ids)} platform adapters")
    return adapter_ids


async def create_test_collection_flows(
    session: AsyncSession,
    user_id: uuid.UUID,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    discovery_flow_id: uuid.UUID = None,
) -> List[uuid.UUID]:
    """Create test collection flows with various states"""
    flow_ids = []

    # Define test flows with different automation tiers and states
    test_flows = [
        {
            "flow_name": "Enterprise CMDB Full Discovery",
            "automation_tier": "tier_1",
            "status": "completed",
            "current_phase": "completed",
            "progress_percentage": 100.0,
            "collection_quality_score": 95.5,
            "confidence_score": 92.0,
            "metadata": {
                "platforms_detected": ["ServiceNow", "Azure", "VMware"],
                "total_resources": 1250,
                "collection_duration_hours": 4.5,
            },
            "collection_config": {
                "auto_discover": True,
                "parallel_execution": True,
                "retry_policy": {"max_attempts": 3, "backoff_seconds": 60},
            },
            "completed_at": datetime.now(timezone.utc) - timedelta(days=2),
        },
        {
            "flow_name": "Cloud Infrastructure Discovery",
            "automation_tier": "tier_2",
            "status": "automated_collection",
            "current_phase": "azure_discovery",
            "progress_percentage": 65.0,
            "collection_quality_score": None,
            "confidence_score": 78.5,
            "metadata": {
                "platforms_detected": ["Azure", "AWS"],
                "resources_discovered": 823,
            },
            "collection_config": {
                "target_platforms": ["azure", "aws"],
                "discovery_scope": "production_only",
            },
            "completed_at": None,
        },
        {
            "flow_name": "Legacy Application Inventory",
            "automation_tier": "tier_3",
            "status": "gap_analysis",
            "current_phase": "identifying_gaps",
            "progress_percentage": 45.0,
            "collection_quality_score": None,
            "confidence_score": 65.0,
            "metadata": {"manual_entries_required": 125, "automated_discoveries": 312},
            "collection_config": {
                "include_legacy_systems": True,
                "gap_threshold": 0.15,
            },
            "completed_at": None,
        },
        {
            "flow_name": "Manual Infrastructure Survey",
            "automation_tier": "tier_4",
            "status": "manual_collection",
            "current_phase": "questionnaire_distribution",
            "progress_percentage": 25.0,
            "collection_quality_score": None,
            "confidence_score": 40.0,
            "metadata": {"questionnaires_sent": 50, "responses_received": 12},
            "collection_config": {
                "collection_method": "manual_only",
                "response_deadline": "2025-02-01",
            },
            "completed_at": None,
        },
        {
            "flow_name": "Failed Discovery Attempt",
            "automation_tier": "tier_2",
            "status": "failed",
            "current_phase": "platform_detection",
            "progress_percentage": 15.0,
            "collection_quality_score": None,
            "confidence_score": 0.0,
            "error_message": "Authentication failed for ServiceNow instance",
            "error_details": {
                "error_code": "AUTH_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "adapter": "servicenow_adapter",
            },
            "metadata": {"failure_reason": "invalid_credentials"},
            "collection_config": {},
            "completed_at": None,
        },
    ]

    for flow_data in test_flows:
        flow_id = uuid.uuid4()
        collection_flow_id = uuid.uuid4()
        flow_ids.append(collection_flow_id)

        # Create the collection flow
        await session.execute(
            text(
                """
                INSERT INTO collection_flows (
                    id, flow_id, master_flow_id, discovery_flow_id,
                    client_account_id, engagement_id, user_id,
                    flow_name, automation_tier, status, current_phase,
                    progress_percentage, collection_quality_score, confidence_score,
                    metadata, collection_config, phase_state,
                    error_message, error_details,
                    created_at, updated_at, completed_at
                ) VALUES (
                    :id, :flow_id, null, :discovery_flow_id,
                    :client_account_id, :engagement_id, :user_id,
                    :flow_name, :automation_tier, :status, :current_phase,
                    :progress_percentage, :collection_quality_score, :confidence_score,
                    :metadata::jsonb, :collection_config::jsonb, :phase_state::jsonb,
                    :error_message, :error_details::jsonb,
                    now(), now(), :completed_at
                )
            """
            ),
            {
                "id": collection_flow_id,
                "flow_id": flow_id,
                "discovery_flow_id": discovery_flow_id,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "user_id": user_id,
                "flow_name": flow_data["flow_name"],
                "automation_tier": flow_data["automation_tier"],
                "status": flow_data["status"],
                "current_phase": flow_data.get("current_phase"),
                "progress_percentage": flow_data["progress_percentage"],
                "collection_quality_score": flow_data.get("collection_quality_score"),
                "confidence_score": flow_data.get("confidence_score"),
                "metadata": json.dumps(flow_data.get("metadata", {})),
                "collection_config": json.dumps(flow_data.get("collection_config", {})),
                "phase_state": json.dumps({}),
                "error_message": flow_data.get("error_message"),
                "error_details": (
                    json.dumps(flow_data.get("error_details", {}))
                    if flow_data.get("error_details")
                    else None
                ),
                "completed_at": flow_data.get("completed_at"),
            },
        )

    await session.commit()
    print(f"✅ Created {len(flow_ids)} collection flows")
    return flow_ids


async def create_test_collected_data(
    session: AsyncSession,
    collection_flow_ids: List[uuid.UUID],
    adapter_ids: List[uuid.UUID],
) -> None:
    """Create test collected data inventory"""

    # Sample data for different platforms
    sample_data_types = [
        {
            "platform": "ServiceNow",
            "collection_method": "api",
            "data_type": "servers",
            "sample_data": {
                "servers": [
                    {
                        "name": "PROD-WEB-01",
                        "os": "Windows Server 2019",
                        "ip": "10.0.1.10",
                    },
                    {"name": "PROD-DB-01", "os": "Red Hat Linux 8", "ip": "10.0.2.20"},
                ]
            },
            "resource_count": 125,
            "quality_score": 95.0,
            "validation_status": "validated",
        },
        {
            "platform": "Azure",
            "collection_method": "api",
            "data_type": "virtual_machines",
            "sample_data": {
                "vms": [
                    {
                        "name": "vm-prod-001",
                        "size": "Standard_D4s_v3",
                        "region": "eastus",
                    },
                    {
                        "name": "vm-prod-002",
                        "size": "Standard_D8s_v3",
                        "region": "eastus",
                    },
                ]
            },
            "resource_count": 87,
            "quality_score": 92.0,
            "validation_status": "validated",
        },
        {
            "platform": "VMware",
            "collection_method": "api",
            "data_type": "virtual_machines",
            "sample_data": {
                "vms": [
                    {
                        "name": "VM-Legacy-01",
                        "vcpu": 4,
                        "memory_gb": 16,
                        "datastore": "PROD-DS01",
                    }
                ]
            },
            "resource_count": 234,
            "quality_score": 88.5,
            "validation_status": "validated",
        },
        {
            "platform": "Manual",
            "collection_method": "questionnaire",
            "data_type": "applications",
            "sample_data": {
                "applications": [
                    {"name": "Legacy ERP", "vendor": "Custom", "criticality": "high"}
                ]
            },
            "resource_count": 45,
            "quality_score": 75.0,
            "validation_status": "pending",
        },
    ]

    # Create collected data for first few flows
    for i, flow_id in enumerate(collection_flow_ids[:4]):
        for j, data_type in enumerate(sample_data_types):
            if i < len(adapter_ids):
                await session.execute(
                    text(
                        """
                        INSERT INTO collected_data_inventory (
                            id, collection_flow_id, adapter_id, platform,
                            collection_method, raw_data, normalized_data,
                            data_type, resource_count, quality_score,
                            validation_status, validation_errors, metadata,
                            collected_at, processed_at
                        ) VALUES (
                            :id, :collection_flow_id, :adapter_id, :platform,
                            :collection_method, :raw_data::jsonb, :normalized_data::jsonb,
                            :data_type, :resource_count, :quality_score,
                            :validation_status, :validation_errors::jsonb, :metadata::jsonb,
                            now() - interval '1 day', now()
                        )
                    """
                    ),
                    {
                        "id": uuid.uuid4(),
                        "collection_flow_id": flow_id,
                        "adapter_id": adapter_ids[j % len(adapter_ids)],
                        "platform": data_type["platform"],
                        "collection_method": data_type["collection_method"],
                        "raw_data": json.dumps(data_type["sample_data"]),
                        "normalized_data": json.dumps(
                            data_type["sample_data"]
                        ),  # Simplified
                        "data_type": data_type["data_type"],
                        "resource_count": data_type["resource_count"],
                        "quality_score": data_type["quality_score"],
                        "validation_status": data_type["validation_status"],
                        "validation_errors": None,
                        "metadata": json.dumps({"collection_run": i + 1}),
                    },
                )

    await session.commit()
    print("✅ Created collected data inventory records")


async def create_test_data_gaps(
    session: AsyncSession, collection_flow_ids: List[uuid.UUID]
) -> List[uuid.UUID]:
    """Create test data gaps"""
    gap_ids = []

    test_gaps = [
        {
            "gap_type": "missing_dependency_data",
            "gap_category": "application",
            "field_name": "application_dependencies",
            "description": "Application dependency information not available in CMDB",
            "impact_on_sixr": "high",
            "priority": 1,
            "suggested_resolution": "Manual survey of application teams required",
            "resolution_status": "pending",
        },
        {
            "gap_type": "incomplete_server_data",
            "gap_category": "infrastructure",
            "field_name": "server_patch_level",
            "description": "Patch level information missing for 30% of servers",
            "impact_on_sixr": "medium",
            "priority": 2,
            "suggested_resolution": "Run patch compliance scan using Systems Manager",
            "resolution_status": "in_progress",
        },
        {
            "gap_type": "missing_cost_data",
            "gap_category": "financial",
            "field_name": "monthly_cost",
            "description": "Cost allocation data not available for on-premises resources",
            "impact_on_sixr": "low",
            "priority": 3,
            "suggested_resolution": "Import from financial system or estimate based on resource specs",
            "resolution_status": "pending",
        },
    ]

    # Create gaps for flows that need them (tier 3 and 4)
    for flow_id in collection_flow_ids[2:4]:  # Legacy and Manual flows
        for gap_data in test_gaps:
            gap_id = uuid.uuid4()
            gap_ids.append(gap_id)

            await session.execute(
                text(
                    """
                    INSERT INTO collection_data_gaps (
                        id, collection_flow_id, gap_type, gap_category,
                        field_name, description, impact_on_sixr, priority,
                        suggested_resolution, resolution_status,
                        resolved_at, resolved_by, metadata, created_at
                    ) VALUES (
                        :id, :collection_flow_id, :gap_type, :gap_category,
                        :field_name, :description, :impact_on_sixr, :priority,
                        :suggested_resolution, :resolution_status,
                        :resolved_at, :resolved_by, :metadata::jsonb, now()
                    )
                """
                ),
                {
                    "id": gap_id,
                    "collection_flow_id": flow_id,
                    "gap_type": gap_data["gap_type"],
                    "gap_category": gap_data["gap_category"],
                    "field_name": gap_data["field_name"],
                    "description": gap_data["description"],
                    "impact_on_sixr": gap_data["impact_on_sixr"],
                    "priority": gap_data["priority"],
                    "suggested_resolution": gap_data["suggested_resolution"],
                    "resolution_status": gap_data["resolution_status"],
                    "resolved_at": None,
                    "resolved_by": None,
                    "metadata": json.dumps({"auto_detected": True}),
                },
            )

    await session.commit()
    print(f"✅ Created {len(gap_ids)} data gaps")
    return gap_ids


async def create_test_questionnaire_responses(
    session: AsyncSession,
    collection_flow_ids: List[uuid.UUID],
    gap_ids: List[uuid.UUID],
    user_id: uuid.UUID,
) -> None:
    """Create test questionnaire responses"""

    test_questions = [
        {
            "questionnaire_type": "gap_resolution",
            "question_category": "application",
            "question_id": "app_deps_001",
            "question_text": "What are the primary dependencies for the Legacy ERP application?",
            "response_type": "multi_select",
            "response_value": ["Database Server", "Message Queue", "File Share"],
            "confidence_score": 85.0,
            "validation_status": "validated",
        },
        {
            "questionnaire_type": "infrastructure_survey",
            "question_category": "server",
            "question_id": "srv_patch_001",
            "question_text": "What is the current patch level for server LEGACY-APP-01?",
            "response_type": "text",
            "response_value": "Windows Server 2016 - KB5015807 (July 2022)",
            "confidence_score": 90.0,
            "validation_status": "validated",
        },
        {
            "questionnaire_type": "cost_allocation",
            "question_category": "financial",
            "question_id": "cost_001",
            "question_text": "What is the estimated monthly cost for the on-premises database cluster?",
            "response_type": "number",
            "response_value": 12500.00,
            "confidence_score": 70.0,
            "validation_status": "pending",
        },
    ]

    # Create responses for manual collection flow
    manual_flow_id = collection_flow_ids[3]  # Manual Infrastructure Survey

    for i, question in enumerate(test_questions):
        gap_id = gap_ids[i] if i < len(gap_ids) else None

        await session.execute(
            text(
                """
                INSERT INTO collection_questionnaire_responses (
                    id, collection_flow_id, gap_id, questionnaire_type,
                    question_category, question_id, question_text,
                    response_type, response_value, confidence_score,
                    validation_status, responded_by, responded_at,
                    metadata, created_at, updated_at
                ) VALUES (
                    :id, :collection_flow_id, :gap_id, :questionnaire_type,
                    :question_category, :question_id, :question_text,
                    :response_type, :response_value::jsonb, :confidence_score,
                    :validation_status, :responded_by, :responded_at,
                    :metadata::jsonb, now(), now()
                )
            """
            ),
            {
                "id": uuid.uuid4(),
                "collection_flow_id": manual_flow_id,
                "gap_id": gap_id,
                "questionnaire_type": question["questionnaire_type"],
                "question_category": question["question_category"],
                "question_id": question["question_id"],
                "question_text": question["question_text"],
                "response_type": question["response_type"],
                "response_value": json.dumps(question["response_value"]),
                "confidence_score": question["confidence_score"],
                "validation_status": question["validation_status"],
                "responded_by": user_id,
                "responded_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "metadata": json.dumps({"source": "manual_entry"}),
            },
        )

    await session.commit()
    print("✅ Created questionnaire responses")


async def get_test_context(session: AsyncSession) -> tuple:
    """Get or create test user, client, and engagement"""

    # Get test user
    result = await session.execute(
        text("SELECT id FROM users WHERE email = 'adcs_test@example.com'")
    )
    user = result.first()

    if not user:
        user_id = uuid.uuid4()
        await session.execute(
            text(
                """
                INSERT INTO users (id, email, full_name, is_active, is_superuser, hashed_password)
                VALUES (:id, :email, :full_name, true, false, 'hashed_password')
            """
            ),
            {
                "id": user_id,
                "email": "adcs_test@example.com",
                "full_name": "ADCS Test User",
            },
        )
    else:
        user_id = user[0]

    # Get test client account
    result = await session.execute(
        text("SELECT id FROM client_accounts WHERE name = 'ADCS Test Client'")
    )
    client = result.first()

    if not client:
        client_id = uuid.uuid4()
        await session.execute(
            text(
                """
                INSERT INTO client_accounts (id, name, code, industry, size, is_active)
                VALUES (:id, :name, :code, :industry, :size, true)
            """
            ),
            {
                "id": client_id,
                "name": "ADCS Test Client",
                "code": "ADCS001",
                "industry": "Technology",
                "size": "enterprise",
            },
        )
    else:
        client_id = client[0]

    # Get test engagement
    result = await session.execute(
        text("SELECT id FROM engagements WHERE name = 'ADCS Test Engagement'")
    )
    engagement = result.first()

    if not engagement:
        engagement_id = uuid.uuid4()
        await session.execute(
            text(
                """
                INSERT INTO engagements (id, client_account_id, name, type, status, start_date)
                VALUES (:id, :client_id, :name, :type, :status, :start_date)
            """
            ),
            {
                "id": engagement_id,
                "client_id": client_id,
                "name": "ADCS Test Engagement",
                "type": "discovery",
                "status": "active",
                "start_date": datetime.now(timezone.utc).date(),
            },
        )
    else:
        engagement_id = engagement[0]

    await session.commit()
    return user_id, client_id, engagement_id


async def main():
    """Main function to seed ADCS test data"""
    print("🚀 Starting ADCS test data seeding...")

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            # Get test context
            user_id, client_id, engagement_id = await get_test_context(session)
            print(
                f"✅ Test context ready - User: {user_id}, Client: {client_id}, Engagement: {engagement_id}"
            )

            # Create platform adapters
            adapter_ids = await create_test_platform_adapters(session)

            # Create collection flows
            flow_ids = await create_test_collection_flows(
                session, user_id, client_id, engagement_id
            )

            # Create collected data inventory
            await create_test_collected_data(session, flow_ids, adapter_ids)

            # Create data gaps
            gap_ids = await create_test_data_gaps(session, flow_ids)

            # Create questionnaire responses
            await create_test_questionnaire_responses(
                session, flow_ids, gap_ids, user_id
            )

            print("\n✅ ADCS test data seeding completed successfully!")
            print(f"   - Platform Adapters: {len(adapter_ids)}")
            print(f"   - Collection Flows: {len(flow_ids)}")
            print(f"   - Data Gaps: {len(gap_ids)}")

        except Exception as e:
            print(f"❌ Error seeding test data: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
