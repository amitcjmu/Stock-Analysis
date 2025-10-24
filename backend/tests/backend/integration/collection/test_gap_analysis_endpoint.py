"""
Integration tests for Collection gap analysis API endpoint.

Tests the full request/response cycle for:
- POST /api/v1/collection/gap-analysis
"""

import pytest
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_gap_analysis_fast_mode(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis in fast mode."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "analysis_mode": "fast",
        "critical_only": False,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "asset_id" in data
    assert "child_flow_id" in data
    assert "analysis_mode" in data
    assert "total_gaps" in data
    assert "critical_gaps" in data
    assert "gaps" in data
    assert "progress_metrics" in data
    assert data["analysis_mode"] == "fast"


@pytest.mark.asyncio
async def test_gap_analysis_thorough_mode(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis in thorough mode with dependency traversal."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "analysis_mode": "thorough",
        "critical_only": False,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["analysis_mode"] == "thorough"
    # Thorough mode may include depends_on field in gaps
    if data["gaps"]:
        gap = data["gaps"][0]
        assert "question_id" in gap
        assert "question_text" in gap
        assert "weight" in gap


@pytest.mark.asyncio
async def test_gap_analysis_critical_only(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis filtering for critical gaps only."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "analysis_mode": "fast",
        "critical_only": True,
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # All returned gaps should be critical
    for gap in data["gaps"]:
        assert gap.get("is_critical") is True


@pytest.mark.asyncio
async def test_gap_analysis_progress_metrics(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis includes proper progress metrics."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "analysis_mode": "fast",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    metrics = data["progress_metrics"]
    assert "total_questions" in metrics
    assert "answered_questions" in metrics
    assert "unanswered_questions" in metrics
    assert "total_weight" in metrics
    assert "answered_weight" in metrics
    assert "completion_percent" in metrics
    # Completion percent should be 0-100
    assert 0 <= metrics["completion_percent"] <= 100


@pytest.mark.asyncio
async def test_gap_analysis_invalid_mode(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis with invalid analysis mode."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),
        "analysis_mode": "invalid_mode",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_gap_analysis_missing_required_fields(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis with missing required fields."""
    # Arrange - missing asset_id
    payload = {
        "child_flow_id": str(uuid4()),
        "analysis_mode": "fast",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_gap_analysis_nonexistent_asset(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test gap analysis for non-existent asset."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "asset_id": str(uuid4()),  # Random UUID that doesn't exist
        "analysis_mode": "fast",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/gap-analysis",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    # Should return 200 with empty gaps or 404
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_404_NOT_FOUND,
    ]

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        # Non-existent asset should have zero gaps
        assert data["total_gaps"] == 0
