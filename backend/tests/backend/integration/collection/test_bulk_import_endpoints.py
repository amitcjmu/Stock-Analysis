"""
Integration tests for Collection bulk import API endpoints.

Tests the full request/response cycle for:
- POST /api/v1/collection/bulk-import/analyze
- POST /api/v1/collection/bulk-import/execute
- GET  /api/v1/collection/bulk-import/status/{task_id}
"""

import pytest
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.timeout(150)  # File analysis with potential agent calls
async def test_analyze_csv_file(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test analyzing a CSV file for import."""
    # Arrange
    csv_content = b"app_name,version,language\nApp1,1.0,Python\nApp2,2.0,Java"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    data = {
        "child_flow_id": str(uuid4()),
        "import_type": "application",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-import/analyze",
        files=files,
        data=data,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "file_name" in result
    assert "total_rows" in result
    assert "detected_columns" in result
    assert "suggested_mappings" in result
    assert result["file_name"] == "test.csv"
    assert result["total_rows"] == 2


@pytest.mark.asyncio
@pytest.mark.timeout(150)  # File analysis with potential agent calls
async def test_analyze_json_file(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test analyzing a JSON file for import."""
    # Arrange
    json_content = b'[{"server_name":"SRV-01","os":"Linux"}]'
    files = {"file": ("servers.json", json_content, "application/json")}
    data = {
        "child_flow_id": str(uuid4()),
        "import_type": "server",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-import/analyze",
        files=files,
        data=data,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["file_name"] == "servers.json"
    assert "detected_columns" in result


@pytest.mark.asyncio
async def test_analyze_file_invalid_format(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test analyzing file with invalid format."""
    # Arrange
    invalid_content = b"This is not valid CSV or JSON"
    files = {"file": ("invalid.txt", invalid_content, "text/plain")}
    data = {
        "child_flow_id": str(uuid4()),
        "import_type": "application",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-import/analyze",
        files=files,
        data=data,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ]


@pytest.mark.asyncio
@pytest.mark.timeout(150)  # Background task with potential agent calls
async def test_execute_import_task(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test executing import task in background."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "import_batch_id": str(uuid4()),
        "confirmed_mappings": {
            "app_name": "app_01_name",
            "version": "app_02_version",
        },
        "import_type": "application",
        "overwrite_existing": False,
        "gap_recalculation_mode": "fast",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-import/execute",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
    ]
    result = response.json()
    assert "id" in result
    assert "status" in result
    assert result["status"] in ["pending", "running"]


@pytest.mark.asyncio
@pytest.mark.timeout(150)  # Background task with potential agent calls
async def test_execute_import_with_thorough_mode(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test executing import with thorough gap recalculation."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "import_batch_id": str(uuid4()),
        "confirmed_mappings": {
            "server_name": "server_01_name",
        },
        "import_type": "server",
        "overwrite_existing": True,
        "gap_recalculation_mode": "thorough",
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-import/execute",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
    ]


@pytest.mark.asyncio
async def test_get_import_task_status_pending(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test getting status of pending import task."""
    # Arrange
    task_id = str(uuid4())

    # Act
    response = await async_client.get(
        f"/api/v1/collection/bulk-import/status/{task_id}",
        headers=auth_headers,
    )

    # Assert
    # Task may not exist, so accept 404
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_404_NOT_FOUND,
    ]

    if response.status_code == status.HTTP_200_OK:
        result = response.json()
        assert "task_id" in result
        assert "status" in result
        assert "progress_percent" in result


@pytest.mark.asyncio
async def test_execute_import_missing_mappings(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test executing import without field mappings."""
    # Arrange
    payload = {
        "child_flow_id": str(uuid4()),
        "import_batch_id": str(uuid4()),
        "import_type": "application",
        # Missing field_mappings
    }

    # Act
    response = await async_client.post(
        "/api/v1/collection/bulk-import/execute",
        json=payload,
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_task_status_invalid_uuid(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """Test getting task status with invalid UUID."""
    # Arrange
    invalid_task_id = "not-a-uuid"

    # Act
    response = await async_client.get(
        f"/api/v1/collection/bulk-import/status/{invalid_task_id}",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code in [
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_400_BAD_REQUEST,
    ]
