"""
Data fixtures for assessment flow testing.

Sample data, test objects, and mock responses for assessment flow scenarios.
"""

from datetime import datetime, timezone

import pytest

from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
)


@pytest.fixture
def sample_applications():
    """Sample application IDs for testing - MFO compliant."""
    return ["app-1", "app-2", "app-3"]


@pytest.fixture
def sample_assessment_flow_state():
    """Sample assessment flow state for testing - MFO compliant."""
    return {
        "flow_id": "test-flow-123",
        "master_flow_id": "master-flow-456",
        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
        "engagement_id": DEMO_ENGAGEMENT_ID,
        "user_id": DEMO_USER_ID,
        "status": "initialized",
        "current_phase": "architecture_minimums",
        "progress": 10,
        "selected_application_ids": ["app-1", "app-2"],
        "engagement_architecture_standards": [],
        "application_components": {},
        "tech_debt_analysis": {},
        "sixr_decisions": {},
        "assessment_results": {},
        "apps_ready_for_planning": [],
        "pause_points": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_architecture_standards():
    """Sample architecture standards for testing."""
    return [
        {
            "requirement_type": "java_versions",
            "description": "Java version requirements",
            "mandatory": True,
            "supported_versions": {"java": "11+"},
            "rationale": "Java 8 end of life",
        },
        {
            "requirement_type": "database_versions",
            "description": "Database version requirements",
            "mandatory": True,
            "supported_versions": {"postgresql": "12+", "mysql": "8.0+"},
            "rationale": "Security and performance",
        },
        {
            "requirement_type": "container_standards",
            "description": "Containerization requirements",
            "mandatory": False,
            "supported_versions": {"docker": "20.10+"},
            "rationale": "Cloud migration readiness",
        },
    ]


@pytest.fixture
def sample_application_metadata():
    """Sample application metadata for testing."""
    return {
        "app-1": {
            "application_name": "Frontend Portal",
            "technology_stack": {"react": "16.14.0", "node": "14.17.0"},
            "database_type": "postgresql",
            "deployment_model": "on_premise",
        },
        "app-2": {
            "application_name": "Backend API",
            "technology_stack": {"java": "8", "spring": "5.3.0"},
            "database_type": "mysql",
            "deployment_model": "on_premise",
        },
        "app-3": {
            "application_name": "Database Server",
            "technology_stack": {"postgresql": "11"},
            "database_type": "postgresql",
            "deployment_model": "bare_metal",
        },
    }


@pytest.fixture
def sample_component_analysis_result():
    """Sample component analysis result for testing."""
    return {
        "components": [
            {
                "name": "frontend",
                "type": "ui",
                "technology_stack": {"react": "16.14.0"},
                "complexity_score": 6.5,
            },
            {
                "name": "backend_api",
                "type": "api",
                "technology_stack": {"java": "8"},
                "complexity_score": 8.0,
            },
            {
                "name": "database",
                "type": "data",
                "technology_stack": {"postgresql": "11"},
                "complexity_score": 4.5,
            },
        ],
        "tech_debt_analysis": [
            {
                "category": "version_obsolescence",
                "severity": "high",
                "description": "Java 8 is end-of-life",
                "score": 8.5,
                "component": "backend_api",
            },
            {
                "category": "framework_outdated",
                "severity": "medium",
                "description": "React 16 has security issues",
                "score": 6.0,
                "component": "frontend",
            },
        ],
        "component_scores": {
            "frontend": 6.5,
            "backend_api": 8.0,
            "database": 4.5,
        },
        "overall_tech_debt_score": 7.2,
    }


@pytest.fixture
def sample_sixr_strategy_result():
    """Sample 6R strategy result for testing."""
    return {
        "component_treatments": [
            {
                "component_name": "frontend",
                "recommended_strategy": "refactor",
                "rationale": "React upgrade and modernization needed",
            },
            {
                "component_name": "backend_api",
                "recommended_strategy": "replatform",
                "rationale": "Java upgrade with containerization",
            },
            {
                "component_name": "database",
                "recommended_strategy": "rehost",
                "rationale": "PostgreSQL compatible with cloud",
            },
        ],
        "overall_strategy": "refactor",
        "confidence_score": 0.85,
    }


@pytest.fixture
def sample_engagement_context():
    """Sample engagement context data - MFO compliant."""
    return {
        "engagement_id": DEMO_ENGAGEMENT_ID,
        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
        "engagement_name": "Test Migration Project",
        "engagement_type": "cloud_migration",
        "target_cloud": "aws",
        "compliance_requirements": ["SOX", "PCI"],
        "business_drivers": ["cost_optimization", "modernization"],
        "timeline_constraints": {
            "project_start": "2025-01-01",
            "go_live_target": "2025-12-31",
        },
    }
