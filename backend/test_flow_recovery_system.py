#!/usr/bin/env python3
"""
Test Flow Recovery System

This script tests the enhanced flow recovery system to verify it can detect and
resolve the critical flow routing issue where Discovery Flow fails on attribute mapping
when resuming from incomplete initialization phase.

CC Enhanced test for critical flow routing issue resolution.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.data_import import DataImport, RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_orchestration.flow_routing_agent import FlowRoutingAgent
from app.services.flow_orchestration.flow_state_detector import FlowStateDetector
from app.services.flow_orchestration.status_manager import FlowStatusManager
from app.services.flow_type_registry import flow_type_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlowRecoveryTestCase:
    """Test case for flow recovery scenarios"""

    def __init__(self, name: str, description: str, setup_func, test_func):
        self.name = name
        self.description = description
        self.setup_func = setup_func
        self.test_func = test_func
        self.results = {}


async def create_test_context() -> RequestContext:
    """Create a test context for the flow recovery tests"""
    return RequestContext(
        client_account_id=uuid.uuid4(),
        engagement_id=uuid.uuid4(),
        user_id="test-user-recovery",
        session_id=uuid.uuid4(),
        current_session=None,
    )


async def setup_problematic_flow_state(
    db: AsyncSession, context: RequestContext
) -> str:
    """
    Set up a problematic flow state that matches the issue described:
    - Flow is in attribute mapping phase
    - Field mappings exist
    - But data import is incomplete/missing
    """
    flow_id = str(uuid.uuid4())
    logger.info(f"🔧 Setting up problematic flow state: {flow_id}")

    # Create master flow
    master_repo = CrewAIFlowStateExtensionsRepository(
        db, str(context.client_account_id), str(context.engagement_id), context.user_id
    )

    master_flow = await master_repo.create_flow(
        flow_type="discovery",
        flow_name=f"Test Problematic Flow {flow_id[:8]}",
        configuration={},
        initial_data={"test_case": "problematic_flow_state"},
    )

    # Create discovery flow in problematic state
    discovery_flow = DiscoveryFlow(
        id=uuid.uuid4(),
        flow_id=master_flow.flow_id,
        master_flow_id=master_flow.id,  # Use database ID for FK
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        user_id=context.user_id,
        flow_name=f"Discovery Flow {flow_id[:8]}",
        status="waiting_for_approval",  # Status that causes 404 issues
        current_phase="field_mapping",  # In field mapping phase
        progress_percentage=25.0,
        # Critical: data_import_completed is False but we're in field_mapping phase
        data_import_completed=False,
        field_mapping_completed=False,
        data_cleansing_completed=False,
        asset_inventory_completed=False,
        dependency_analysis_completed=False,
        tech_debt_assessment_completed=False,
        crewai_state_data={"test_case": "problematic_state"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(discovery_flow)
    await db.commit()
    await db.refresh(discovery_flow)

    # Create field mappings (they exist but are orphaned)
    for i in range(3):
        field_mapping = ImportFieldMapping(
            source_field=f"test_field_{i}",
            target_field=f"mapped_field_{i}",
            status="suggested",
            confidence_score=0.85,
            match_type="exact",
            suggested_by="test_agent",
            transformation_rules={},
            master_flow_id=master_flow.id,  # Use database ID for FK
            # Note: data_import_id is None - this is the problem!
            data_import_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(field_mapping)

    await db.commit()

    logger.info(f"✅ Created problematic flow state: {flow_id}")
    return str(master_flow.flow_id)


async def setup_recoverable_flow_state(
    db: AsyncSession, context: RequestContext
) -> str:
    """
    Set up a flow state that can be recovered by linking orphaned data
    """
    flow_id = str(uuid.uuid4())
    logger.info(f"🔧 Setting up recoverable flow state: {flow_id}")

    # Create data import with raw data (orphaned)
    data_import = DataImport(
        id=uuid.uuid4(),
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        filename="test_import.csv",
        import_type="csv",
        status="completed",
        total_records=2,
        master_flow_id=None,  # Orphaned - not linked to any flow
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(data_import)
    await db.flush()  # Get ID

    # Add raw import records
    for i in range(2):
        raw_record = RawImportRecord(
            id=uuid.uuid4(),
            data_import_id=data_import.id,
            raw_data={
                "system_name": f"test_system_{i}",
                "server_type": "web_server",
                "location": "datacenter_1",
            },
            row_number=i + 1,
            created_at=datetime.utcnow(),
        )
        db.add(raw_record)

    # Create master flow
    master_repo = CrewAIFlowStateExtensionsRepository(
        db, str(context.client_account_id), str(context.engagement_id), context.user_id
    )

    master_flow = await master_repo.create_flow(
        flow_type="discovery",
        flow_name=f"Test Recoverable Flow {flow_id[:8]}",
        configuration={},
        initial_data={"test_case": "recoverable_flow_state"},
    )

    # Create discovery flow in problematic state
    discovery_flow = DiscoveryFlow(
        id=uuid.uuid4(),
        flow_id=master_flow.flow_id,
        master_flow_id=master_flow.id,  # Use database ID for FK
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        user_id=context.user_id,
        flow_name=f"Recoverable Discovery Flow {flow_id[:8]}",
        status="waiting_for_approval",
        current_phase="field_mapping",
        progress_percentage=25.0,
        data_import_completed=False,  # Problem: marked as incomplete
        field_mapping_completed=False,
        crewai_state_data={"test_case": "recoverable_state"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(discovery_flow)
    await db.commit()

    logger.info(f"✅ Created recoverable flow state: {flow_id}")
    return str(master_flow.flow_id)


async def test_flow_state_detection(
    db: AsyncSession, context: RequestContext, flow_id: str
) -> Dict[str, Any]:
    """Test flow state detection capabilities"""
    logger.info(f"🔍 Testing flow state detection for: {flow_id}")

    detector = FlowStateDetector(db, context)
    issues = await detector.detect_incomplete_initialization(flow_id)

    results = {
        "issues_detected": len(issues),
        "issues": [
            {
                "type": issue.issue_type,
                "severity": issue.severity,
                "description": issue.description,
                "suggested_action": issue.suggested_action,
            }
            for issue in issues
        ],
        "has_critical_issues": any(i.severity == "critical" for i in issues),
        "has_data_import_issues": any(
            "data_import" in i.issue_type or "raw_data" in i.issue_type for i in issues
        ),
    }

    logger.info(
        f"🔍 Detection results for {flow_id}: {results['issues_detected']} issues, "
        f"critical: {results['has_critical_issues']}, data_import: {results['has_data_import_issues']}"
    )

    return results


async def test_flow_routing_intelligence(
    db: AsyncSession, context: RequestContext, flow_id: str
) -> Dict[str, Any]:
    """Test flow routing intelligence"""
    logger.info(f"🧭 Testing flow routing intelligence for: {flow_id}")

    router = FlowRoutingAgent(db, context)
    routing_decision = await router.analyze_and_route_flow(flow_id)

    results = {
        "routing_decision": {
            "current_phase": routing_decision.current_phase,
            "target_phase": routing_decision.target_phase,
            "routing_reason": routing_decision.routing_reason,
            "confidence": routing_decision.confidence,
        },
        "requires_routing": routing_decision.confidence > 0.8
        and routing_decision.target_phase not in ["continue", "unknown"],
        "routes_to_data_import": routing_decision.target_phase == "data_import",
    }

    logger.info(
        f"🧭 Routing results for {flow_id}: {routing_decision.current_phase} → {routing_decision.target_phase} "
        f"(confidence: {routing_decision.confidence:.2f})"
    )

    return results


async def test_flow_recovery_execution(
    db: AsyncSession, context: RequestContext, flow_id: str
) -> Dict[str, Any]:
    """Test flow recovery execution"""
    logger.info(f"🔄 Testing flow recovery execution for: {flow_id}")

    # Initialize status manager
    master_repo = CrewAIFlowStateExtensionsRepository(
        db, str(context.client_account_id), str(context.engagement_id), context.user_id
    )

    status_manager = FlowStatusManager(db, context, master_repo, flow_type_registry)

    # Attempt recovery
    recovery_result = await status_manager.attempt_flow_recovery(flow_id)

    results = {
        "recovery_attempted": True,
        "recovery_successful": recovery_result.get("success", False),
        "recovery_action": recovery_result.get("action"),
        "error": recovery_result.get("error"),
    }

    logger.info(
        f"🔄 Recovery results for {flow_id}: success={results['recovery_successful']}, "
        f"action={results['recovery_action']}"
    )

    return results


async def test_phase_transition_interception(
    db: AsyncSession, context: RequestContext, flow_id: str
) -> Dict[str, Any]:
    """Test phase transition interception"""
    logger.info(f"🚫 Testing phase transition interception for: {flow_id}")

    # Initialize status manager
    master_repo = CrewAIFlowStateExtensionsRepository(
        db, str(context.client_account_id), str(context.engagement_id), context.user_id
    )

    status_manager = FlowStatusManager(db, context, master_repo, flow_type_registry)

    # Test interception from field_mapping to data_cleansing
    interception_result = await status_manager.intercept_phase_transition(
        flow_id, "field_mapping", "data_cleansing"
    )

    results = {
        "interception_attempted": True,
        "transition_intercepted": interception_result.get("intercepted", False),
        "allow_transition": interception_result.get("allow_transition", False),
        "redirected_to": interception_result.get("redirected_to"),
        "routing_reason": interception_result.get("routing_reason"),
    }

    logger.info(
        f"🚫 Interception results for {flow_id}: intercepted={results['transition_intercepted']}, "
        f"redirected_to={results['redirected_to']}"
    )

    return results


async def run_comprehensive_test() -> Dict[str, Any]:
    """Run comprehensive flow recovery system test"""
    logger.info("🚀 Starting comprehensive flow recovery system test")

    async with AsyncSessionLocal() as db:
        context = await create_test_context()
        test_results = {}

        # Test Case 1: Problematic Flow State (matches the original issue)
        logger.info("=" * 60)
        logger.info("TEST CASE 1: Problematic Flow State")
        logger.info("=" * 60)

        problematic_flow_id = await setup_problematic_flow_state(db, context)

        test_results["problematic_flow"] = {
            "flow_id": problematic_flow_id,
            "detection": await test_flow_state_detection(
                db, context, problematic_flow_id
            ),
            "routing": await test_flow_routing_intelligence(
                db, context, problematic_flow_id
            ),
            "recovery": await test_flow_recovery_execution(
                db, context, problematic_flow_id
            ),
            "interception": await test_phase_transition_interception(
                db, context, problematic_flow_id
            ),
        }

        # Test Case 2: Recoverable Flow State
        logger.info("=" * 60)
        logger.info("TEST CASE 2: Recoverable Flow State")
        logger.info("=" * 60)

        recoverable_flow_id = await setup_recoverable_flow_state(db, context)

        test_results["recoverable_flow"] = {
            "flow_id": recoverable_flow_id,
            "detection": await test_flow_state_detection(
                db, context, recoverable_flow_id
            ),
            "routing": await test_flow_routing_intelligence(
                db, context, recoverable_flow_id
            ),
            "recovery": await test_flow_recovery_execution(
                db, context, recoverable_flow_id
            ),
            "interception": await test_phase_transition_interception(
                db, context, recoverable_flow_id
            ),
        }

        # System-wide analysis test
        logger.info("=" * 60)
        logger.info("TEST CASE 3: System-wide Analysis")
        logger.info("=" * 60)

        detector = FlowStateDetector(db, context)
        system_analysis = await detector.detect_system_wide_issues()

        test_results["system_analysis"] = system_analysis

    logger.info("✅ Comprehensive flow recovery system test completed")
    return test_results


async def analyze_test_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze test results and provide summary"""
    logger.info("📊 Analyzing test results")

    summary = {
        "overall_success": True,
        "test_cases": {},
        "critical_findings": [],
        "recommendations": [],
    }

    # Analyze problematic flow test case
    problematic = results.get("problematic_flow", {})
    detection = problematic.get("detection", {})
    routing = problematic.get("routing", {})
    recovery = problematic.get("recovery", {})
    interception = problematic.get("interception", {})

    summary["test_cases"]["problematic_flow"] = {
        "flow_id": problematic.get("flow_id"),
        "issues_detected": detection.get("issues_detected", 0) > 0,
        "routing_works": routing.get("routes_to_data_import", False),
        "recovery_attempted": recovery.get("recovery_attempted", False),
        "interception_works": interception.get("transition_intercepted", False),
        "overall_success": all(
            [
                detection.get("issues_detected", 0) > 0,
                routing.get("routes_to_data_import", False),
                recovery.get("recovery_attempted", False),
                interception.get("transition_intercepted", False),
            ]
        ),
    }

    # Analyze recoverable flow test case
    recoverable = results.get("recoverable_flow", {})
    detection_r = recoverable.get("detection", {})
    routing_r = recoverable.get("routing", {})
    recovery_r = recoverable.get("recovery", {})
    interception_r = recoverable.get("interception", {})

    summary["test_cases"]["recoverable_flow"] = {
        "flow_id": recoverable.get("flow_id"),
        "issues_detected": detection_r.get("issues_detected", 0) > 0,
        "routing_works": routing_r.get("requires_routing", False),
        "recovery_attempted": recovery_r.get("recovery_attempted", False),
        "interception_works": interception_r.get("transition_intercepted", False),
        "overall_success": all(
            [
                detection_r.get("issues_detected", 0) > 0,
                routing_r.get("requires_routing", False),
                recovery_r.get("recovery_attempted", False),
            ]
        ),
    }

    # Overall success assessment
    summary["overall_success"] = all(
        case["overall_success"] for case in summary["test_cases"].values()
    )

    # Generate findings and recommendations
    if summary["overall_success"]:
        summary["critical_findings"].append(
            "✅ Flow recovery system successfully detects and handles problematic flow states"
        )
        summary["recommendations"].append(
            "Deploy flow recovery system to production to resolve the critical flow routing issue"
        )
    else:
        summary["critical_findings"].append(
            "❌ Flow recovery system has issues that need to be addressed"
        )
        summary["recommendations"].append("Review failed test cases and fix issues")

    return summary


if __name__ == "__main__":

    async def main():
        try:
            # Initialize flow type registry
            from app.services.flow_configs import initialize_all_flows

            initialize_all_flows()

            # Run comprehensive test
            results = await run_comprehensive_test()

            # Analyze results
            summary = await analyze_test_results(results)

            # Print summary
            logger.info("=" * 80)
            logger.info("FLOW RECOVERY SYSTEM TEST SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Overall Success: {summary['overall_success']}")
            logger.info("")

            logger.info("Critical Findings:")
            for finding in summary["critical_findings"]:
                logger.info(f"  • {finding}")
            logger.info("")

            logger.info("Recommendations:")
            for recommendation in summary["recommendations"]:
                logger.info(f"  • {recommendation}")
            logger.info("")

            logger.info("Test Case Results:")
            for case_name, case_result in summary["test_cases"].items():
                logger.info(f"  {case_name}:")
                logger.info(f"    Flow ID: {case_result['flow_id']}")
                logger.info(f"    Issues Detected: {case_result['issues_detected']}")
                logger.info(f"    Routing Works: {case_result['routing_works']}")
                logger.info(
                    f"    Recovery Attempted: {case_result['recovery_attempted']}"
                )
                logger.info(
                    f"    Interception Works: {case_result['interception_works']}"
                )
                logger.info(f"    Overall Success: {case_result['overall_success']}")
                logger.info("")

            logger.info("=" * 80)

            if summary["overall_success"]:
                logger.info(
                    "🎉 SUCCESS: Flow recovery system is ready to resolve the critical flow routing issue!"
                )
            else:
                logger.error(
                    "❌ FAILURE: Flow recovery system needs fixes before deployment."
                )

        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}", exc_info=True)

    asyncio.run(main())
