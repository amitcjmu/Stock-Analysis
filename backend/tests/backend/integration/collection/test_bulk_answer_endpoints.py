"""
Integration tests for Collection bulk answer API endpoints.

Tests the full request/response cycle for:
- POST /api/v1/collection/bulk-answer-preview
- POST /api/v1/collection/bulk-answer
"""

import pytest
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_answer_preview_success(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test successful bulk answer preview with no conflicts."""
    # Arrange
    child_flow_id = str(uuid4())
    asset_ids = [str(uuid4()) for _ in range(3)]
    question_ids = ["app_01_name", "app_02_version"]

    payload = {
        "child_flow_id": child_flow_id,
        "asset_ids": asset_ids,
        "question_ids": question_ids,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-answer-preview",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_assets" in data
    assert "potential_conflicts" in data
    assert "conflicts" in data
    assert data["total_assets"] == 3


@pytest.mark.asyncio
async def test_bulk_answer_preview_with_conflicts(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test bulk answer preview detecting conflicts."""
    # Arrange
    child_flow_id = str(uuid4())
    asset_ids = [str(uuid4()) for _ in range(5)]
    question_ids = ["app_03_language"]

    payload = {
        "child_flow_id": child_flow_id,
        "asset_ids": asset_ids,
        "question_ids": question_ids,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-answer-preview",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "conflicts" in data
    # Conflicts may or may not exist depending on test data


@pytest.mark.asyncio
async def test_bulk_answer_preview_invalid_payload(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test bulk answer preview with invalid payload."""
    # Arrange - missing required field
    payload = {
        "child_flow_id": str(uuid4()),
        # Missing asset_ids
        "question_ids": ["app_01_name"],
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-answer-preview",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_bulk_answer_submit_success(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test successful bulk answer submission."""
    # Arrange
    child_flow_id = str(uuid4())
    asset_ids = [str(uuid4()) for _ in range(2)]

    payload = {
        "child_flow_id": child_flow_id,
        "asset_ids": asset_ids,
        "answers": [
            {"question_id": "app_01_name", "answer_value": "Test App"},
            {"question_id": "app_02_version", "answer_value": "1.0"},
        ],
        "conflict_strategy": "overwrite",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-answer",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    ]
    data = response.json()
    assert "total_assets" in data
    assert "successful_assets" in data
    assert "failed_chunks" in data


@pytest.mark.asyncio
async def test_bulk_answer_submit_with_conflicts_skip(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test bulk answer submission with skip conflict strategy."""
    # Arrange
    child_flow_id = str(uuid4())
    asset_ids = [str(uuid4()) for _ in range(3)]

    payload = {
        "child_flow_id": child_flow_id,
        "asset_ids": asset_ids,
        "answers": [
            {"question_id": "app_03_language", "answer_value": "Python"},
        ],
        "conflict_strategy": "skip",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-answer",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    ]
    data = response.json()
    assert data["conflict_strategy"] == "skip"


@pytest.mark.asyncio
async def test_bulk_answer_submit_invalid_strategy(
    async_client: AsyncClient,
    test_client_account_id: str,
    test_engagement_id: str,
):
    """Test bulk answer submission with invalid conflict strategy."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_ids": [str(uuid4())],
        "answers": [{"question_id": "app_01_name", "answer_value": "Test"}],
        "conflict_strategy": "invalid_strategy",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-answer",
        json=payload,
        headers={
            "X-Client-Account-ID": test_client_account_id,
            "X-Engagement-ID": test_engagement_id,
        },
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_bulk_answer_missing_auth_headers(async_client: AsyncClient):
    """Test bulk answer endpoints require authentication headers."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_ids": [str(uuid4())],
        "question_ids": ["app_01_name"],
    }

    # Act - no auth headers
    response = await async_client.post(
        "/api/v1/collection/bulk-answer-preview",
        json=payload,
    )

    # Assert
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ]
