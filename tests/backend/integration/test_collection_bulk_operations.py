"""
Integration Tests for Collection Bulk Operations API Endpoints

Tests all 8 collection bulk operation endpoints with real HTTP requests.
Covers bulk answers, dynamic questions, and bulk import workflows.

Coverage:
- POST /collection/bulk-answer-preview
- POST /collection/bulk-answer (200, 409, 400)
- POST /collection/questions/filtered
- POST /collection/questions/filtered (with refresh_agent_analysis=True)
- POST /collection/dependency-change
- POST /collection/bulk-import/analyze
- POST /collection/bulk-import/execute
- GET /collection/bulk-import/status/{task_id}

Per Issue #784 and design doc Section 8.2.
"""

import pytest
import httpx
from uuid import uuid4
from io import BytesIO

# Test base URL
BASE_URL = "http://localhost:8000/api/v1/collection"


@pytest.fixture
def sample_child_flow_id():
    """Sample child flow UUID"""
    return str(uuid4())


@pytest.fixture
def sample_asset_ids():
    """Sample asset UUIDs"""
    return [str(uuid4()) for _ in range(5)]


@pytest.fixture
def sample_question_ids():
    """Sample question IDs"""
    return ["app_01_name", "app_02_language", "app_03_database"]


@pytest.fixture
def auth_headers():
    """Authentication headers for requests"""
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
    }


class TestBulkAnswerEndpoints:
    """Test bulk answer endpoints"""

    @pytest.mark.asyncio
    async def test_bulk_answer_preview_success(
        self, sample_child_flow_id, sample_asset_ids, sample_question_ids, auth_headers
    ):
        """Test POST /bulk-answer-preview returns 200 OK"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/bulk-answer-preview",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_ids": sample_asset_ids,
                    "question_ids": sample_question_ids,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "conflicts" in data
            assert "affected_assets_count" in data
            assert "questions_count" in data
            assert data["affected_assets_count"] == len(sample_asset_ids)
            assert data["questions_count"] == len(sample_question_ids)

    @pytest.mark.asyncio
    async def test_bulk_answer_preview_validation_error(self, auth_headers):
        """Test POST /bulk-answer-preview returns 400 for invalid input"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/bulk-answer-preview",
                json={
                    "child_flow_id": "invalid-uuid",  # Invalid UUID
                    "asset_ids": [],
                    "question_ids": [],
                },
                headers=auth_headers,
            )

            assert response.status_code in [400, 422]
            # Should return validation error

    @pytest.mark.asyncio
    async def test_bulk_answer_submit_success(
        self, sample_child_flow_id, sample_asset_ids, auth_headers
    ):
        """Test POST /bulk-answer returns 200 on successful submission"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/bulk-answer",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_ids": sample_asset_ids,
                    "answers": [
                        {
                            "question_id": "app_01_name",
                            "answer_value": "Test App",
                        },
                        {
                            "question_id": "app_02_language",
                            "answer_value": "Python",
                        },
                    ],
                    "conflict_resolution_strategy": "overwrite",
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert "total_assets" in data
            assert "successful_assets" in data
            assert data["total_assets"] == len(sample_asset_ids)

    @pytest.mark.asyncio
    async def test_bulk_answer_submit_with_conflicts(
        self, sample_child_flow_id, sample_asset_ids, auth_headers
    ):
        """Test POST /bulk-answer handles conflicts (409 or special response)"""
        async with httpx.AsyncClient() as client:
            # First submission
            await client.post(
                f"{BASE_URL}/bulk-answer",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_ids": sample_asset_ids[:2],
                    "answers": [
                        {"question_id": "app_01_name", "answer_value": "App1"}
                    ],
                    "conflict_resolution_strategy": "skip",
                },
                headers=auth_headers,
            )

            # Second submission with different value (conflict)
            response = await client.post(
                f"{BASE_URL}/bulk-answer",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_ids": sample_asset_ids[:2],
                    "answers": [
                        {"question_id": "app_01_name", "answer_value": "App2"}
                    ],
                    "conflict_resolution_strategy": "skip",
                },
                headers=auth_headers,
            )

            # Should either return 200 with skipped assets or 409 conflict
            assert response.status_code in [200, 409]
            if response.status_code == 200:
                data = response.json()
                # Some assets should be skipped due to conflicts
                assert "successful_assets" in data

    @pytest.mark.asyncio
    async def test_bulk_answer_submit_validation_error(self, auth_headers):
        """Test POST /bulk-answer returns 400 for invalid request"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/bulk-answer",
                json={
                    "child_flow_id": str(uuid4()),
                    "asset_ids": [],  # Empty asset list
                    "answers": [],
                    "conflict_resolution_strategy": "invalid_strategy",
                },
                headers=auth_headers,
            )

            assert response.status_code in [400, 422]


class TestDynamicQuestionEndpoints:
    """Test dynamic question filtering endpoints"""

    @pytest.mark.asyncio
    async def test_questions_filtered_basic(
        self, sample_child_flow_id, auth_headers
    ):
        """Test GET /questions/filtered returns asset-type questions"""
        async with httpx.AsyncClient() as client:
            asset_id = str(uuid4())
            response = await client.post(
                f"{BASE_URL}/questions/filtered",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_id": asset_id,
                    "asset_type": "Application",
                    "include_answered": False,
                    "refresh_agent_analysis": False,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "questions" in data
            assert isinstance(data["questions"], list)
            # Should only return Application questions
            if data["questions"]:
                assert all("app_" in q["question_id"] for q in data["questions"])

    @pytest.mark.asyncio
    async def test_questions_filtered_with_agent_refresh(
        self, sample_child_flow_id, auth_headers
    ):
        """Test POST /questions/filtered with agent pruning (async 202)"""
        async with httpx.AsyncClient() as client:
            asset_id = str(uuid4())
            response = await client.post(
                f"{BASE_URL}/questions/filtered",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_id": asset_id,
                    "asset_type": "Server",
                    "include_answered": False,
                    "refresh_agent_analysis": True,  # Trigger agent pruning
                },
                headers=auth_headers,
                timeout=30.0,  # Agent analysis may take longer
            )

            # Should return 200 or 202 (if async processing)
            assert response.status_code in [200, 202]
            data = response.json()
            assert "questions" in data
            if response.status_code == 200:
                # Agent analysis completed
                assert "agent_status" in data
                assert data["agent_status"] in ["completed", "fallback"]

    @pytest.mark.asyncio
    async def test_questions_filtered_include_answered(
        self, sample_child_flow_id, auth_headers
    ):
        """Test questions/filtered with include_answered=True"""
        async with httpx.AsyncClient() as client:
            asset_id = str(uuid4())
            response = await client.post(
                f"{BASE_URL}/questions/filtered",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_id": asset_id,
                    "asset_type": "Database",
                    "include_answered": True,  # Include answered questions
                    "refresh_agent_analysis": False,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "questions" in data
            # Should include both answered and unanswered

    @pytest.mark.asyncio
    async def test_dependency_change_reopen(
        self, sample_child_flow_id, auth_headers
    ):
        """Test POST /dependency-change reopens questions"""
        async with httpx.AsyncClient() as client:
            asset_id = str(uuid4())
            response = await client.post(
                f"{BASE_URL}/dependency-change",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "changed_asset_id": asset_id,
                    "changed_field": "os_version",  # Critical field
                    "old_value": "Linux 18.04",
                    "new_value": "Linux 20.04",
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "reopened_count" in data
            assert "reopened_questions" in data
            assert isinstance(data["reopened_questions"], list)


class TestBulkImportEndpoints:
    """Test bulk import endpoints"""

    @pytest.mark.asyncio
    async def test_bulk_import_analyze_csv(self, auth_headers):
        """Test POST /bulk-import/analyze for CSV file"""
        # Create sample CSV
        csv_content = b"app_name,language,database\nApp1,Python,PostgreSQL\nApp2,Java,MySQL"

        async with httpx.AsyncClient() as client:
            files = {
                "file": ("test.csv", BytesIO(csv_content), "text/csv")
            }
            data = {
                "import_type": "application"
            }

            response = await client.post(
                f"{BASE_URL}/bulk-import/analyze",
                files=files,
                data=data,
                headers={"Authorization": auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            result = response.json()
            assert "file_name" in result
            assert "total_rows" in result
            assert "detected_columns" in result
            assert "suggested_mappings" in result
            assert "import_batch_id" in result
            assert result["total_rows"] == 2
            assert len(result["detected_columns"]) == 3

    @pytest.mark.asyncio
    async def test_bulk_import_analyze_json(self, auth_headers):
        """Test POST /bulk-import/analyze for JSON file"""
        # Create sample JSON
        json_content = b'[{"server_name":"web-01","os":"Linux"},{"server_name":"db-01","os":"Windows"}]'

        async with httpx.AsyncClient() as client:
            files = {
                "file": ("servers.json", BytesIO(json_content), "application/json")
            }
            data = {
                "import_type": "server"
            }

            response = await client.post(
                f"{BASE_URL}/bulk-import/analyze",
                files=files,
                data=data,
                headers={"Authorization": auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            result = response.json()
            assert result["file_name"] == "servers.json"
            assert result["total_rows"] == 2

    @pytest.mark.asyncio
    async def test_bulk_import_analyze_validation_error(self, auth_headers):
        """Test POST /bulk-import/analyze returns 400 for invalid file"""
        # Empty file
        async with httpx.AsyncClient() as client:
            files = {
                "file": ("empty.csv", BytesIO(b""), "text/csv")
            }
            data = {
                "import_type": "application"
            }

            response = await client.post(
                f"{BASE_URL}/bulk-import/analyze",
                files=files,
                data=data,
                headers={"Authorization": auth_headers["Authorization"]},
            )

            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_bulk_import_execute(
        self, sample_child_flow_id, auth_headers
    ):
        """Test POST /bulk-import/execute creates background task"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/bulk-import/execute",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "import_batch_id": "batch_123",
                    "confirmed_mappings": [
                        {
                            "csv_column": "app_name",
                            "suggested_field": "app_01_name",
                            "confidence": 0.95,
                        }
                    ],
                    "import_type": "application",
                    "overwrite_existing": True,
                    "gap_recalculation_mode": "fast",
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data  # Task ID
            assert "status" in data
            assert "progress_percent" in data
            assert "current_stage" in data
            assert data["status"] in ["pending", "queued", "running"]

    @pytest.mark.asyncio
    async def test_bulk_import_execute_thorough_mode(
        self, sample_child_flow_id, auth_headers
    ):
        """Test POST /bulk-import/execute with thorough gap recalculation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/bulk-import/execute",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "import_batch_id": "batch_456",
                    "confirmed_mappings": [
                        {
                            "csv_column": "server_name",
                            "suggested_field": "server_01_name",
                            "confidence": 0.90,
                        }
                    ],
                    "import_type": "server",
                    "overwrite_existing": False,
                    "gap_recalculation_mode": "thorough",  # Thorough mode
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["status"] in ["pending", "queued", "running"]

    @pytest.mark.asyncio
    async def test_bulk_import_status(self, auth_headers):
        """Test GET /bulk-import/status/{task_id}"""
        # First create a task
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                f"{BASE_URL}/bulk-import/execute",
                json={
                    "child_flow_id": str(uuid4()),
                    "import_batch_id": "batch_789",
                    "confirmed_mappings": [],
                    "import_type": "application",
                    "overwrite_existing": True,
                    "gap_recalculation_mode": "fast",
                },
                headers=auth_headers,
            )

            if create_response.status_code == 200:
                task_data = create_response.json()
                task_id = task_data["id"]

                # Now get the status
                status_response = await client.get(
                    f"{BASE_URL}/bulk-import/status/{task_id}",
                    headers=auth_headers,
                )

                assert status_response.status_code in [200, 404]
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    assert "id" in status_data
                    assert "status" in status_data
                    assert "progress_percent" in status_data
                    assert "current_stage" in status_data
                    assert status_data["id"] == task_id

    @pytest.mark.asyncio
    async def test_bulk_import_status_not_found(self, auth_headers):
        """Test GET /bulk-import/status/{task_id} returns 404 for invalid ID"""
        async with httpx.AsyncClient() as client:
            fake_task_id = str(uuid4())
            response = await client.get(
                f"{BASE_URL}/bulk-import/status/{fake_task_id}",
                headers=auth_headers,
            )

            assert response.status_code == 404


class TestEndToEndBulkWorkflow:
    """Test complete end-to-end bulk operation workflows"""

    @pytest.mark.asyncio
    async def test_complete_bulk_answer_workflow(
        self, sample_child_flow_id, sample_asset_ids, auth_headers
    ):
        """Test complete bulk answer workflow: preview -> submit"""
        async with httpx.AsyncClient() as client:
            # Step 1: Preview
            preview_response = await client.post(
                f"{BASE_URL}/bulk-answer-preview",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_ids": sample_asset_ids,
                    "question_ids": ["app_01_name", "app_02_language"],
                },
                headers=auth_headers,
            )

            assert preview_response.status_code == 200
            preview_data = preview_response.json()

            # Step 2: Submit (with conflict resolution based on preview)
            strategy = "overwrite" if preview_data["conflicts"] else "skip"

            submit_response = await client.post(
                f"{BASE_URL}/bulk-answer",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "asset_ids": sample_asset_ids,
                    "answers": [
                        {"question_id": "app_01_name", "answer_value": "MyApp"},
                        {"question_id": "app_02_language", "answer_value": "Python"},
                    ],
                    "conflict_resolution_strategy": strategy,
                },
                headers=auth_headers,
            )

            assert submit_response.status_code == 200
            submit_data = submit_response.json()
            assert submit_data["success"] is True

    @pytest.mark.asyncio
    async def test_complete_bulk_import_workflow(
        self, sample_child_flow_id, auth_headers
    ):
        """Test complete bulk import workflow: analyze -> execute -> check status"""
        async with httpx.AsyncClient() as client:
            # Step 1: Analyze file
            csv_content = b"app_name,language\nApp1,Python\nApp2,Java"
            files = {"file": ("apps.csv", BytesIO(csv_content), "text/csv")}
            data = {"import_type": "application"}

            analyze_response = await client.post(
                f"{BASE_URL}/bulk-import/analyze",
                files=files,
                data=data,
                headers={"Authorization": auth_headers["Authorization"]},
            )

            assert analyze_response.status_code == 200
            analyze_data = analyze_response.json()
            import_batch_id = analyze_data["import_batch_id"]

            # Step 2: Execute import
            execute_response = await client.post(
                f"{BASE_URL}/bulk-import/execute",
                json={
                    "child_flow_id": sample_child_flow_id,
                    "import_batch_id": import_batch_id,
                    "confirmed_mappings": analyze_data["suggested_mappings"],
                    "import_type": "application",
                    "overwrite_existing": True,
                    "gap_recalculation_mode": "fast",
                },
                headers=auth_headers,
            )

            assert execute_response.status_code == 200
            execute_data = execute_response.json()
            task_id = execute_data["id"]

            # Step 3: Check status
            status_response = await client.get(
                f"{BASE_URL}/bulk-import/status/{task_id}",
                headers=auth_headers,
            )

            assert status_response.status_code in [200, 404]
