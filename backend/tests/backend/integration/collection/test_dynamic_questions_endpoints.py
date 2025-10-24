"""
Integration tests for Collection dynamic questions API endpoints.

Tests the full request/response cycle for:
- POST /api/v1/collection/questions/filtered
- POST /api/v1/collection/dependency-change
"""

import pytest
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_filtered_questions_unanswered_only(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test getting only unanswered questions for an asset."""
    # Arrange
    child_flow_id = str(uuid4())
    asset_id = str(uuid4())

    payload = {
        "child_flow_id": child_flow_id,
        "asset_id": asset_id,
        "include_answered": False,
        "refresh_agent_analysis": False,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/questions/filtered",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "asset_type" in data
    assert "total_questions" in data
    assert "questions" in data
    assert "agent_status" in data
    assert isinstance(data["questions"], list)


@pytest.mark.asyncio
async def test_get_filtered_questions_include_answered(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test getting all questions including answered ones."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "include_answered": True,
        "refresh_agent_analysis": False,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/questions/filtered",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["include_answered"] is True


@pytest.mark.asyncio
async def test_get_filtered_questions_with_agent_pruning(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test getting filtered questions with agent-based pruning."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "include_answered": False,
        "refresh_agent_analysis": True,  # Enable agent pruning
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/questions/filtered",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Agent status should be set (completed or fallback)
    assert data["agent_status"] in ["not_requested", "completed", "fallback"]


@pytest.mark.asyncio
async def test_detect_dependency_change_os_change(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test detecting dependency changes when OS changes."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "changed_field": "operating_system",
        "new_value": "Linux",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/dependency-change",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "changed_field" in data
    assert "old_value" in data
    assert "new_value" in data
    assert "reopened_question_ids" in data
    assert isinstance(data["reopened_question_ids"], list)


@pytest.mark.asyncio
async def test_detect_dependency_change_no_dependencies(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test dependency detection when field has no dependencies."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "changed_field": "asset_name",
        "new_value": "New Name",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/dependency-change",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Should return empty reopened list
    assert len(data["reopened_question_ids"]) == 0


@pytest.mark.asyncio
async def test_filtered_questions_invalid_asset_id(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test filtered questions with invalid asset ID format."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": "invalid-uuid",
        "include_answered": False,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/questions/filtered",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_dependency_change_missing_required_field(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test dependency change with missing required field."""
    # Arrange - missing new_value
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "changed_field": "operating_system",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/dependency-change",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
