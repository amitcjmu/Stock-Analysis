"""
Provider Contract Verification Tests

Issue #592: API Contract Testing Implementation

This test verifies that the backend API provider satisfies the consumer contracts
defined by the frontend. It uses pact-python to replay consumer expectations.

Usage:
    1. Run consumer tests first to generate pact files:
       cd .. && npx vitest tests/contract/

    2. Run provider verification:
       cd backend && python -m pytest tests/contract/ -v

Prerequisites:
    - pip install pact-python pytest-asyncio httpx
    - Consumer pact files in ../tests/contract/pacts/
"""

import os
import re
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from contextlib import contextmanager

# Provider verification imports
try:
    from pact import Verifier

    PACT_AVAILABLE = True
except ImportError:
    PACT_AVAILABLE = False
    Verifier = None

# Backend app imports (will be available when running in backend context)
try:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from fastapi.responses import JSONResponse
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None
    app = None
    FastAPI = None
    Request = None
    JSONResponse = None

# Database imports for provider state setup
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    create_engine = None
    sessionmaker = None
    settings = None

# Configuration
PACT_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "contract" / "pacts"
PROVIDER_NAME = "migrate-api-backend"
PROVIDER_BASE_URL = os.environ.get("PROVIDER_BASE_URL", "http://localhost:8000")
STATE_CHANGE_URL = f"{PROVIDER_BASE_URL}/_pact/provider_states"

# Test UUIDs for deterministic testing
TEST_UUIDS = {
    "assessment_flow": "550e8400-e29b-41d4-a716-446655440000",
    "master_flow": "660e8400-e29b-41d4-a716-446655440000",
    "discovery_flow": "770e8400-e29b-41d4-a716-446655440000",
    "collection_flow": "880e8400-e29b-41d4-a716-446655440000",
    "decommission_flow": "990e8400-e29b-41d4-a716-446655440000",
    "canonical_app": "aa0e8400-e29b-41d4-a716-446655440000",
    "asset": "bb0e8400-e29b-41d4-a716-446655440000",
    "data_import": "cc0e8400-e29b-41d4-a716-446655440000",
}


class ProviderStateSetup:
    """
    Provider state handlers for Pact verification.

    These handlers set up the database/mock state required for each
    consumer expectation defined in the pact files.
    """

    # Class-level mapping of state descriptions to handler method names
    STATE_HANDLERS = {
        # Health & Auth states
        "the API is running": "_setup_healthy_api",
        "a user is authenticated": "_setup_authenticated_user",
        # Assessment Flow states
        "an assessment flow exists": "_setup_assessment_flow",
        "no assessment flow exists": "_setup_no_flow",
        "applications ready for assessment": "_setup_ready_applications",
        "assessment flow with 6R decisions": "_setup_flow_with_decisions",
        # Master Flow states
        "a master flow exists": "_setup_master_flow",
        "multiple master flows exist": "_setup_multiple_flows",
        "an active master flow exists": "_setup_active_flow",
        "a paused master flow exists": "_setup_paused_flow",
        # Discovery Flow states
        "ready to create discovery flow": "_setup_ready_for_discovery",
        "a discovery flow exists": "_setup_discovery_flow",
        "an active discovery flow exists": "_setup_active_discovery_flow",
        "a discovery flow ready for execution": "_setup_discovery_flow",
        "a running discovery flow": "_setup_running_discovery_flow",
        "a paused discovery flow": "_setup_paused_discovery_flow",
        "discovery flow has assets": "_setup_discovery_with_assets",
        "discovery flow has field mappings": "_setup_discovery_with_mappings",
        "discovery service is running": "_setup_healthy_api",
        # Collection Flow states
        "an active collection flow exists": "_setup_active_collection_flow",
        "collection flows exist": "_setup_collection_flows",
        "a collection flow exists": "_setup_collection_flow",
        "a collection flow ready for gap analysis": "_setup_collection_flow",
        "a completed collection flow": "_setup_completed_collection_flow",
        # Decommission Flow states
        "systems eligible for decommission exist": "_setup_decommission_eligible",
        "a decommission flow exists": "_setup_decommission_flow",
        "a paused decommission flow": "_setup_paused_decommission_flow",
        "a running decommission flow": "_setup_running_decommission_flow",
        "an active decommission flow": "_setup_active_decommission_flow",
        "decommission flows exist": "_setup_decommission_flows",
        "systems exist that can be decommissioned": "_setup_decommission_eligible",
        "a decommission flow ready for phase execution": "_setup_decommission_flow",
        "data retention policies exist": "_setup_data_retention_policies",
        # Data Import states
        "data imports exist": "_setup_data_imports",
        "at least one data import exists": "_setup_data_imports",
        "a data import exists": "_setup_data_import",
        "target fields are configured": "_setup_target_fields",
        "field categories are configured": "_setup_field_categories",
        "an import with field mappings exists": "_setup_import_with_mappings",
        "an import ready for mapping generation": "_setup_import_for_mapping",
        "imports with critical attributes exist": "_setup_critical_attributes",
        "learning data exists": "_setup_learning_data",
        "data import service is running": "_setup_healthy_api",
        # FinOps states
        "FinOps metrics are available": "_setup_finops_metrics",
        "resources with costs exist": "_setup_finops_resources",
        "cost optimization opportunities exist": "_setup_finops_opportunities",
        "cost alerts are configured": "_setup_finops_alerts",
        "LLM usage data exists": "_setup_llm_usage",
        "FinOps service is running": "_setup_healthy_api",
        # Canonical Applications states
        "canonical applications exist": "_setup_canonical_apps",
        "a canonical application and asset exist": "_setup_canonical_app_with_asset",
        "a canonical application and multiple assets exist": "_setup_canonical_app_with_assets",
        "a canonical application with assessed assets": "_setup_canonical_app_assessed",
    }

    def __init__(self, db_session=None):
        """
        Initialize provider state setup.

        Args:
            db_session: Optional database session for creating test data.
                       If None, handlers will use mock/in-memory state.
        """
        self.db_session = db_session
        self._created_entities = []  # Track created entities for cleanup

    def setup_state(self, state: str, **kwargs) -> dict:
        """
        Set up provider state based on consumer expectation.

        Args:
            state: The provider state description from the pact
            **kwargs: Optional parameters for the state

        Returns:
            dict with status and any created entity IDs
        """
        params = kwargs or {}
        result = {"status": "ok", "state": state}

        handler_name = self.STATE_HANDLERS.get(state)
        if handler_name:
            handler = getattr(self, handler_name, None)
            if handler:
                handler_result = handler(params)
                if handler_result:
                    result.update(handler_result)
            else:
                result["warning"] = f"Handler method '{handler_name}' not found"
        else:
            result["warning"] = f"No handler for state '{state}'"

        return result

    def teardown_state(self, state: str) -> None:
        """Clean up any test data created for this state."""
        # In real implementation, clean up created test data
        self._created_entities.clear()

    @contextmanager
    def _db_transaction(self):
        """Context manager for database transactions."""
        if self.db_session:
            try:
                yield self.db_session
                self.db_session.commit()
            except Exception:
                self.db_session.rollback()
                raise
        else:
            yield None

    # ============== Health & Auth Handlers ==============

    def _setup_healthy_api(self, params: dict) -> dict:
        """API is running - no setup needed."""
        return {"health": "ok"}

    def _setup_authenticated_user(self, params: dict) -> dict:
        """Set up authenticated user context."""
        return {
            "user_id": "test-user-001",
            "client_account_id": 1,
            "engagement_id": 1,
        }

    # ============== Assessment Flow Handlers ==============

    def _setup_assessment_flow(self, params: dict) -> dict:
        """Set up an existing assessment flow in the database."""
        flow_id = params.get("flow_id", TEST_UUIDS["assessment_flow"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    # Create master flow first
                    master_id = str(uuid.uuid4())
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.crewai_flow_state_extensions
                        (flow_id, flow_type, status, current_phase, client_account_id, engagement_id)
                        VALUES (:flow_id, 'assessment', 'running', 'tech_debt_assessment', 1, 1)
                        ON CONFLICT (flow_id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"flow_id": master_id},
                    )

                    # Create assessment flow
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.assessment_flows
                        (id, name, status, master_flow_id, client_account_id, engagement_id)
                        VALUES (:id, 'Test Assessment', 'processing', :master_id, 1, 1)
                        ON CONFLICT (id) DO UPDATE SET status = 'processing'
                    """
                        ),
                        {"id": flow_id, "master_id": master_id},
                    )

                    self._created_entities.append(("assessment_flows", flow_id))
                    self._created_entities.append(
                        ("crewai_flow_state_extensions", master_id)
                    )

        return {"flow_id": flow_id, "status": "processing"}

    def _setup_no_flow(self, params: dict) -> dict:
        """Ensure no flow exists - clean state."""
        # In test database, this would delete any existing test flows
        return {"flows_cleared": True}

    def _setup_ready_applications(self, params: dict) -> dict:
        """Set up applications ready for assessment."""
        app_ids = [str(uuid.uuid4()) for _ in range(3)]

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    for app_id in app_ids:
                        session.execute(
                            text(
                                """
                            INSERT INTO migration.canonical_applications
                            (id, name, business_criticality, client_account_id, engagement_id)
                            VALUES (:id, :name, 'high', 1, 1)
                            ON CONFLICT (id) DO NOTHING
                        """
                            ),
                            {"id": app_id, "name": f"Test App {app_id[:8]}"},
                        )
                        self._created_entities.append(
                            ("canonical_applications", app_id)
                        )

        return {"application_ids": app_ids, "count": len(app_ids)}

    def _setup_flow_with_decisions(self, params: dict) -> dict:
        """Set up flow with existing 6R decisions."""
        flow_id = params.get("flow_id", TEST_UUIDS["assessment_flow"])
        app_id = params.get("app_id", TEST_UUIDS["canonical_app"])

        # First set up the assessment flow
        self._setup_assessment_flow({"flow_id": flow_id})

        return {"flow_id": flow_id, "app_id": app_id, "has_decisions": True}

    # ============== Master Flow Handlers ==============

    def _setup_master_flow(self, params: dict) -> dict:
        """Set up a master flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["master_flow"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.crewai_flow_state_extensions
                        (flow_id, flow_type, status, current_phase, client_account_id, engagement_id)
                        VALUES (:flow_id, 'master', 'running', 'initialization', 1, 1)
                        ON CONFLICT (flow_id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"flow_id": flow_id},
                    )
                    self._created_entities.append(
                        ("crewai_flow_state_extensions", flow_id)
                    )

        return {"flow_id": flow_id, "status": "running"}

    def _setup_multiple_flows(self, params: dict) -> dict:
        """Set up multiple master flows."""
        flow_ids = [str(uuid.uuid4()) for _ in range(3)]

        for flow_id in flow_ids:
            self._setup_master_flow({"flow_id": flow_id})

        return {"flow_ids": flow_ids, "count": len(flow_ids)}

    def _setup_active_flow(self, params: dict) -> dict:
        """Set up an active (running) flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["master_flow"])
        result = self._setup_master_flow({"flow_id": flow_id})
        result["status"] = "running"
        return result

    def _setup_paused_flow(self, params: dict) -> dict:
        """Set up a paused flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["master_flow"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.crewai_flow_state_extensions
                        (flow_id, flow_type, status, current_phase, client_account_id, engagement_id)
                        VALUES (:flow_id, 'master', 'paused', 'initialization', 1, 1)
                        ON CONFLICT (flow_id) DO UPDATE SET status = 'paused'
                    """
                        ),
                        {"flow_id": flow_id},
                    )

        return {"flow_id": flow_id, "status": "paused"}

    # ============== Discovery Flow Handlers ==============

    def _setup_ready_for_discovery(self, params: dict) -> dict:
        """Ready to create discovery flow."""
        return {"ready": True, "client_account_id": 1, "engagement_id": 1}

    def _setup_discovery_flow(self, params: dict) -> dict:
        """Set up a discovery flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["discovery_flow"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    # Create master flow
                    master_id = str(uuid.uuid4())
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.crewai_flow_state_extensions
                        (flow_id, flow_type, status, current_phase, client_account_id, engagement_id)
                        VALUES (:flow_id, 'discovery', 'running', 'data_collection', 1, 1)
                        ON CONFLICT (flow_id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"flow_id": master_id},
                    )

                    # Create discovery flow
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.discovery_flows
                        (flow_id, name, status, master_flow_id, client_account_id, engagement_id)
                        VALUES (:id, 'Test Discovery', 'running', :master_id, 1, 1)
                        ON CONFLICT (flow_id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"id": flow_id, "master_id": master_id},
                    )

                    self._created_entities.append(("discovery_flows", flow_id))

        return {"flow_id": flow_id, "status": "running"}

    def _setup_active_discovery_flow(self, params: dict) -> dict:
        """Set up an active discovery flow."""
        return self._setup_discovery_flow(params)

    def _setup_running_discovery_flow(self, params: dict) -> dict:
        """Set up a running discovery flow."""
        return self._setup_discovery_flow(params)

    def _setup_paused_discovery_flow(self, params: dict) -> dict:
        """Set up a paused discovery flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["discovery_flow"])
        result = self._setup_discovery_flow({"flow_id": flow_id})

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    session.execute(
                        text(
                            """
                        UPDATE migration.discovery_flows
                        SET status = 'paused'
                        WHERE flow_id = :flow_id
                    """
                        ),
                        {"flow_id": flow_id},
                    )

        result["status"] = "paused"
        return result

    def _setup_discovery_with_assets(self, params: dict) -> dict:
        """Set up discovery flow with assets."""
        flow_id = params.get("flow_id", TEST_UUIDS["discovery_flow"])
        self._setup_discovery_flow({"flow_id": flow_id})

        asset_ids = [str(uuid.uuid4()) for _ in range(5)]

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    for asset_id in asset_ids:
                        session.execute(
                            text(
                                """
                            INSERT INTO migration.discovered_assets
                            (id, discovery_flow_id, name, asset_type, client_account_id, engagement_id)
                            VALUES (:id, :flow_id, :name, 'server', 1, 1)
                            ON CONFLICT (id) DO NOTHING
                        """
                            ),
                            {
                                "id": asset_id,
                                "flow_id": flow_id,
                                "name": f"Asset {asset_id[:8]}",
                            },
                        )

        return {
            "flow_id": flow_id,
            "asset_ids": asset_ids,
            "asset_count": len(asset_ids),
        }

    def _setup_discovery_with_mappings(self, params: dict) -> dict:
        """Set up discovery flow with field mappings."""
        flow_id = params.get("flow_id", TEST_UUIDS["discovery_flow"])
        self._setup_discovery_flow({"flow_id": flow_id})

        return {
            "flow_id": flow_id,
            "mappings": [
                {"source": "hostname", "target": "server_name"},
                {"source": "ip_addr", "target": "ip_address"},
            ],
        }

    # ============== Collection Flow Handlers ==============

    def _setup_active_collection_flow(self, params: dict) -> dict:
        """Set up an active collection flow."""
        return self._setup_collection_flow(params)

    def _setup_collection_flows(self, params: dict) -> dict:
        """Set up multiple collection flows."""
        flow_ids = [str(uuid.uuid4()) for _ in range(3)]

        for flow_id in flow_ids:
            self._setup_collection_flow({"flow_id": flow_id})

        return {"flow_ids": flow_ids, "count": len(flow_ids)}

    def _setup_collection_flow(self, params: dict) -> dict:
        """Set up a collection flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["collection_flow"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    # Create master flow
                    master_id = str(uuid.uuid4())
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.crewai_flow_state_extensions
                        (flow_id, flow_type, status, current_phase, client_account_id, engagement_id)
                        VALUES (:flow_id, 'collection', 'running', 'data_collection', 1, 1)
                        ON CONFLICT (flow_id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"flow_id": master_id},
                    )

                    # Create collection flow
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.collection_flows
                        (id, name, status, master_flow_id, client_account_id, engagement_id)
                        VALUES (:id, 'Test Collection', 'running', :master_id, 1, 1)
                        ON CONFLICT (id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"id": flow_id, "master_id": master_id},
                    )

                    self._created_entities.append(("collection_flows", flow_id))

        return {"flow_id": flow_id, "status": "running"}

    def _setup_completed_collection_flow(self, params: dict) -> dict:
        """Set up a completed collection flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["collection_flow"])
        result = self._setup_collection_flow({"flow_id": flow_id})

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    session.execute(
                        text(
                            """
                        UPDATE migration.collection_flows
                        SET status = 'completed'
                        WHERE id = :flow_id
                    """
                        ),
                        {"flow_id": flow_id},
                    )

        result["status"] = "completed"
        return result

    # ============== Decommission Flow Handlers ==============

    def _setup_decommission_eligible(self, params: dict) -> dict:
        """Set up systems eligible for decommission."""
        return {
            "eligible_systems": [
                {"id": str(uuid.uuid4()), "name": "Legacy Server 1"},
                {"id": str(uuid.uuid4()), "name": "Legacy Server 2"},
            ]
        }

    def _setup_decommission_flow(self, params: dict) -> dict:
        """Set up a decommission flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["decommission_flow"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.decommission_flows
                        (id, name, status, client_account_id, engagement_id)
                        VALUES (:id, 'Test Decommission', 'running', 1, 1)
                        ON CONFLICT (id) DO UPDATE SET status = 'running'
                    """
                        ),
                        {"id": flow_id},
                    )
                    self._created_entities.append(("decommission_flows", flow_id))

        return {"flow_id": flow_id, "status": "running"}

    def _setup_paused_decommission_flow(self, params: dict) -> dict:
        """Set up a paused decommission flow."""
        flow_id = params.get("flow_id", TEST_UUIDS["decommission_flow"])
        result = self._setup_decommission_flow({"flow_id": flow_id})
        result["status"] = "paused"
        return result

    def _setup_running_decommission_flow(self, params: dict) -> dict:
        """Set up a running decommission flow."""
        return self._setup_decommission_flow(params)

    def _setup_active_decommission_flow(self, params: dict) -> dict:
        """Set up an active decommission flow."""
        return self._setup_decommission_flow(params)

    def _setup_decommission_flows(self, params: dict) -> dict:
        """Set up multiple decommission flows."""
        flow_ids = [str(uuid.uuid4()) for _ in range(3)]

        for flow_id in flow_ids:
            self._setup_decommission_flow({"flow_id": flow_id})

        return {"flow_ids": flow_ids, "count": len(flow_ids)}

    def _setup_data_retention_policies(self, params: dict) -> dict:
        """Set up data retention policies."""
        return {
            "policies": [
                {"name": "Standard", "retention_days": 90},
                {"name": "Extended", "retention_days": 365},
            ]
        }

    # ============== Data Import Handlers ==============

    def _setup_data_imports(self, params: dict) -> dict:
        """Set up data imports."""
        import_ids = [str(uuid.uuid4()) for _ in range(3)]

        for import_id in import_ids:
            self._setup_data_import({"import_id": import_id})

        return {"import_ids": import_ids, "count": len(import_ids)}

    def _setup_data_import(self, params: dict) -> dict:
        """Set up a specific data import."""
        import_id = params.get("import_id", TEST_UUIDS["data_import"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.data_imports
                        (id, filename, status, client_account_id, engagement_id)
                        VALUES (:id, 'test_import.csv', 'completed', 1, 1)
                        ON CONFLICT (id) DO UPDATE SET status = 'completed'
                    """
                        ),
                        {"id": import_id},
                    )
                    self._created_entities.append(("data_imports", import_id))

        return {"import_id": import_id, "status": "completed"}

    def _setup_target_fields(self, params: dict) -> dict:
        """Set up target fields configuration."""
        return {
            "fields": [
                {"name": "server_name", "type": "string", "required": True},
                {"name": "ip_address", "type": "string", "required": True},
                {"name": "os_version", "type": "string", "required": False},
            ]
        }

    def _setup_field_categories(self, params: dict) -> dict:
        """Set up field categories."""
        return {
            "categories": [
                {"name": "Infrastructure", "fields": ["server_name", "ip_address"]},
                {"name": "Software", "fields": ["os_version", "app_name"]},
            ]
        }

    def _setup_import_with_mappings(self, params: dict) -> dict:
        """Set up import with field mappings."""
        import_id = params.get("import_id", TEST_UUIDS["data_import"])
        self._setup_data_import({"import_id": import_id})

        return {
            "import_id": import_id,
            "mappings": [
                {"source": "hostname", "target": "server_name", "confidence": 0.95},
                {"source": "ip", "target": "ip_address", "confidence": 0.99},
            ],
        }

    def _setup_import_for_mapping(self, params: dict) -> dict:
        """Set up import ready for mapping generation."""
        import_id = params.get("import_id", TEST_UUIDS["data_import"])
        result = self._setup_data_import({"import_id": import_id})
        result["ready_for_mapping"] = True
        return result

    def _setup_critical_attributes(self, params: dict) -> dict:
        """Set up critical attributes."""
        return {
            "critical_attributes": [
                {"name": "business_criticality", "coverage": 0.85},
                {"name": "owner", "coverage": 0.72},
            ]
        }

    def _setup_learning_data(self, params: dict) -> dict:
        """Set up learning data."""
        return {
            "learning_stats": {
                "total_mappings_learned": 150,
                "accuracy": 0.92,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        }

    # ============== FinOps Handlers ==============

    def _setup_finops_metrics(self, params: dict) -> dict:
        """Set up FinOps metrics."""
        return {
            "metrics": {
                "total_cost": 15000.00,
                "compute_cost": 8000.00,
                "storage_cost": 4000.00,
                "network_cost": 3000.00,
            }
        }

    def _setup_finops_resources(self, params: dict) -> dict:
        """Set up FinOps resources."""
        return {
            "resources": [
                {"id": str(uuid.uuid4()), "name": "Web Server", "monthly_cost": 500.00},
                {"id": str(uuid.uuid4()), "name": "Database", "monthly_cost": 800.00},
            ]
        }

    def _setup_finops_opportunities(self, params: dict) -> dict:
        """Set up FinOps opportunities."""
        return {
            "opportunities": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Right-size instances",
                    "potential_savings": 2500.00,
                },
            ]
        }

    def _setup_finops_alerts(self, params: dict) -> dict:
        """Set up FinOps alerts."""
        return {
            "alerts": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "budget",
                    "message": "Budget threshold exceeded",
                },
            ]
        }

    def _setup_llm_usage(self, params: dict) -> dict:
        """Set up LLM usage data."""
        return {
            "llm_usage": {
                "total_cost": 250.00,
                "total_tokens": 5000000,
                "models_used": ["gpt-4", "claude-3-opus"],
            }
        }

    # ============== Canonical Applications Handlers ==============

    def _setup_canonical_apps(self, params: dict) -> dict:
        """Set up canonical applications."""
        app_ids = [str(uuid.uuid4()) for _ in range(3)]

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    for i, app_id in enumerate(app_ids):
                        session.execute(
                            text(
                                """
                            INSERT INTO migration.canonical_applications
                            (id, name, business_criticality, client_account_id, engagement_id)
                            VALUES (:id, :name, 'high', 1, 1)
                            ON CONFLICT (id) DO NOTHING
                        """
                            ),
                            {"id": app_id, "name": f"Application {i + 1}"},
                        )

        return {"app_ids": app_ids, "count": len(app_ids)}

    def _setup_canonical_app_with_asset(self, params: dict) -> dict:
        """Set up canonical application with asset."""
        app_id = params.get("app_id", TEST_UUIDS["canonical_app"])
        asset_id = params.get("asset_id", TEST_UUIDS["asset"])

        if self.db_session:
            with self._db_transaction() as session:
                if session:
                    # Create app
                    session.execute(
                        text(
                            """
                        INSERT INTO migration.canonical_applications
                        (id, name, business_criticality, client_account_id, engagement_id)
                        VALUES (:id, 'Test App', 'high', 1, 1)
                        ON CONFLICT (id) DO NOTHING
                    """
                        ),
                        {"id": app_id},
                    )

        return {"app_id": app_id, "asset_id": asset_id}

    def _setup_canonical_app_with_assets(self, params: dict) -> dict:
        """Set up canonical application with multiple assets."""
        app_id = params.get("app_id", TEST_UUIDS["canonical_app"])
        asset_ids = [str(uuid.uuid4()) for _ in range(5)]

        self._setup_canonical_app_with_asset({"app_id": app_id})

        return {"app_id": app_id, "asset_ids": asset_ids, "asset_count": len(asset_ids)}

    def _setup_canonical_app_assessed(self, params: dict) -> dict:
        """Set up canonical application with assessed assets."""
        app_id = params.get("app_id", TEST_UUIDS["canonical_app"])
        result = self._setup_canonical_app_with_assets({"app_id": app_id})
        result["assessment_complete"] = True
        return result


# Global state handler instance
_state_handler: Optional[ProviderStateSetup] = None


def get_state_handler() -> ProviderStateSetup:
    """Get or create the global state handler."""
    global _state_handler
    if _state_handler is None:
        db_session = None
        if DB_AVAILABLE and settings:
            try:
                engine = create_engine(str(settings.database_url))
                Session = sessionmaker(bind=engine)
                db_session = Session()
            except Exception as e:
                print(f"Warning: Could not connect to database: {e}")
        _state_handler = ProviderStateSetup(db_session)
    return _state_handler


# State change endpoint for Pact verification
def create_state_change_app() -> "FastAPI":
    """
    Create a FastAPI app with the state change endpoint.

    This is used during Pact verification to set up provider states.
    """
    if not FASTAPI_AVAILABLE:
        return None

    state_app = FastAPI()

    @state_app.post("/_pact/provider_states")
    async def provider_states(request: Request):
        """Handle provider state setup requests from Pact verifier."""
        body = await request.json()
        state = body.get("state", body.get("consumer", ""))
        params = body.get("params", {})

        handler = get_state_handler()
        result = handler.setup_state(state, **params)

        return JSONResponse(content=result)

    @state_app.delete("/_pact/provider_states")
    async def teardown_states(request: Request):
        """Clean up provider states after verification."""
        body = await request.json()
        state = body.get("state", "")

        handler = get_state_handler()
        handler.teardown_state(state)

        return JSONResponse(content={"status": "cleaned"})

    return state_app


@pytest.fixture
def provider_state_handler():
    """Fixture for provider state setup."""
    return get_state_handler()


@pytest.mark.skipif(
    not PACT_AVAILABLE,
    reason="pact-python not installed. Install with: pip install pact-python",
)
@pytest.mark.skipif(
    not PACT_DIR.exists(),
    reason=f"Pact files not found at {PACT_DIR}. Run consumer tests first.",
)
class TestProviderVerification:
    """
    Provider verification tests.

    These tests verify that the backend API satisfies the contracts
    defined by the frontend consumer.
    """

    def test_verify_pacts(self, provider_state_handler):
        """
        Verify all pact contracts against the running provider.

        Note: This test requires the backend to be running at PROVIDER_BASE_URL.
        For CI, this would be started as part of the test setup.
        """
        # Find all pact files
        pact_files = list(PACT_DIR.glob("*.json"))

        if not pact_files:
            pytest.skip("No pact files found")

        # Create verifier with state change URL
        verifier = Verifier(
            provider=PROVIDER_NAME,
            provider_base_url=PROVIDER_BASE_URL,
        )

        # Verify each pact file
        for pact_file in pact_files:
            print(f"\nVerifying pact: {pact_file.name}")

            # Run verification with state change URL
            # The state change URL allows the verifier to set up provider states
            output, result = verifier.verify_pacts(
                str(pact_file),
                enable_pending=True,
                verbose=True,
                provider_states_setup_url=STATE_CHANGE_URL,
            )

            # Check result
            assert (
                result == 0
            ), f"Pact verification failed for {pact_file.name}: {output}"

    def test_openapi_schema_available(self):
        """
        Verify OpenAPI schema is available at /openapi.json.

        This is a prerequisite for type generation.
        """
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Verify basic OpenAPI structure
        assert "openapi" in schema
        assert "paths" in schema
        assert "components" in schema

        # Verify critical endpoints exist
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/me" in schema["paths"]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
class TestAPIEndpointContracts:
    """
    Direct API contract tests without Pact broker.

    These tests verify endpoint contracts directly using the test client.
    Useful for local development and CI when Pact broker is not available.
    """

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    def test_health_endpoint_contract(self, client):
        """Verify health endpoint returns expected structure."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Contract: must have status field
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_me_endpoint_requires_headers(self, client):
        """Verify /me endpoint requires tenant headers."""
        # Without headers - should work but return demo context
        response = client.get("/api/v1/me")

        # Should return 200 with context
        assert response.status_code == 200
        data = response.json()

        # Contract: must have client/engagement context
        assert "client_account_id" in data or "client" in data

    def test_assessment_flow_endpoints_exist(self, client):
        """Verify assessment flow endpoints are registered."""
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        schema = response.json()

        # Critical assessment flow endpoints
        required_endpoints = [
            "/api/v1/assessment-flow/initialize",
            "/api/v1/assessment-flow/{flow_id}/status",
        ]

        # Normalize path parameters for robust matching
        paths = schema["paths"].keys()
        normalized_paths = {re.sub(r"\{.*?\}", "{param}", path) for path in paths}

        for endpoint in required_endpoints:
            normalized_endpoint = re.sub(r"\{.*?\}", "{param}", endpoint)
            assert (
                normalized_endpoint in normalized_paths
            ), f"Endpoint {endpoint} not found in OpenAPI schema"


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
class TestProviderStateSetup:
    """
    Tests for the provider state setup handlers.

    These tests verify that state handlers correctly create test data.
    """

    def test_assessment_flow_state_setup(self, provider_state_handler):
        """Test assessment flow state handler."""
        result = provider_state_handler.setup_state(
            "an assessment flow exists",
            flow_id="test-flow-123",
        )

        assert result["status"] == "ok"
        assert "flow_id" in result

    def test_master_flow_state_setup(self, provider_state_handler):
        """Test master flow state handler."""
        result = provider_state_handler.setup_state(
            "a master flow exists",
            flow_id="test-master-456",
        )

        assert result["status"] == "ok"
        assert "flow_id" in result

    def test_unknown_state_returns_warning(self, provider_state_handler):
        """Test that unknown states return a warning."""
        result = provider_state_handler.setup_state("unknown state that does not exist")

        assert result["status"] == "ok"
        assert "warning" in result


# Entry point for standalone verification
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
