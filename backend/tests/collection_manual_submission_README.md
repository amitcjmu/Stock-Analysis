# Collection Manual Submission Tests

Comprehensive unit tests for the collection manual submission fixes implemented to resolve gap resolution, tenant scoping, and asset write-back functionality.

## Test Coverage

### 1. Gap Resolution Tests (`test_collection_gap_resolution.py`)

Tests the core functionality of resolving data gaps through manual questionnaire submissions:

#### Key Test Cases:
- ✅ **Gap Resolution**: Submitting questionnaire responses updates `CollectionDataGap.resolution_status` from "pending" to "resolved"
- ✅ **Metadata Updates**: `resolved_at` and `resolved_by` fields are set correctly during gap resolution
- ✅ **Asset Write-back Trigger**: Asset write-back is triggered after successful gap resolution
- ✅ **Field Matching**: Only gaps with field names matching form responses are resolved
- ✅ **Empty Response Handling**: Empty or null responses don't resolve gaps
- ✅ **No Gaps Handling**: Submission works correctly when no gaps exist
- ✅ **Write-back Failure Resilience**: Write-back failures don't fail the entire operation
- ✅ **Flow Completion**: Flow completion status is updated correctly (100% completion)
- ✅ **Asset Linking**: Asset linking works when `asset_id` is provided in metadata
- ✅ **Invalid Asset Handling**: Invalid asset IDs are handled gracefully

### 2. Tenant Scoping Tests (`test_collection_tenant_scoping.py`)

Tests multi-tenant isolation and security in both questionnaire retrieval and submission:

#### Key Test Cases:
- ✅ **Tenant Filtering**: `get_adaptive_questionnaires` filters by both `client_account_id` and `engagement_id`
- ✅ **Unauthorized Access**: Requests with wrong tenant context return 404 (not found)
- ✅ **Cross-tenant Isolation**: Questionnaires from other tenants are not accessible
- ✅ **Submit Tenant Scoping**: `submit_questionnaire_response` enforces tenant scoping
- ✅ **Asset Validation Scoping**: Asset validation is also tenant-scoped
- ✅ **Cross-tenant Asset Rejection**: Assets from different tenants cannot be linked
- ✅ **Context Validation**: Proper tenant context is required for all operations
- ✅ **UUID Format Handling**: String vs UUID tenant ID variations are handled correctly
- ✅ **Malformed ID Rejection**: Malformed tenant IDs are properly rejected

### 3. Asset Write-back Tests (`test_asset_write_back.py`)

Tests the asset write-back functionality that updates asset records with resolved gap data:

#### Key Test Cases:
- ✅ **Field Updates**: `apply_resolved_gaps_to_assets` updates Asset fields correctly
- ✅ **Tenant Scoping**: Asset updates are properly tenant-scoped
- ✅ **Field Whitelist**: Only whitelisted fields are updated on assets
- ✅ **Assessment Readiness**: `assessment_readiness` is set when minimum fields are present
- ✅ **Missing Assets**: Missing assets are handled gracefully
- ✅ **No Gaps Handling**: No operations when no resolved gaps exist
- ✅ **Error Handling**: Invalid tenant context raises appropriate errors
- ✅ **Database Rollback**: Database errors trigger proper rollback
- ✅ **Batch Processing**: Multiple batches are processed correctly
- ✅ **Asset ID Resolution**: Asset IDs are resolved from gap metadata hints
- ✅ **Custom Batch Sizes**: Custom batch sizes are honored
- ✅ **SQL Injection Prevention**: Parameterized queries prevent SQL injection

## Test Architecture

### Fixtures and Mocks

The tests use comprehensive pytest fixtures to provide:

- **`mock_db`**: AsyncSession mock with execute, commit, rollback operations
- **`mock_user`**: User model mock with UUID-based ID
- **`mock_context`**: RequestContext mock with tenant information
- **`mock_collection_flow`**: CollectionFlow model mock with proper tenant association
- **`mock_questionnaire_request`**: QuestionnaireSubmissionRequest mock with form data
- **`mock_pending_gaps`**: CollectionDataGap mocks in "pending" status
- **`mock_asset`**: Asset model mock with tenant scoping

### Testing Patterns

1. **Async Test Support**: All tests use `@pytest.mark.asyncio` for async function testing
2. **Mock Isolation**: Each test uses isolated mocks to prevent cross-test contamination
3. **Error Path Testing**: Both success and failure paths are comprehensively tested
4. **Edge Case Coverage**: Empty responses, missing data, and malformed inputs are tested
5. **Security Testing**: Cross-tenant access attempts are verified to fail appropriately

## Running Tests

### Prerequisites

Ensure you have the required test dependencies:

```bash
pip install pytest pytest-asyncio
```

### Running Individual Test Files

```bash
# Gap resolution tests
python -m pytest tests/api/v1/endpoints/test_collection_gap_resolution.py -v

# Tenant scoping tests
python -m pytest tests/api/v1/endpoints/test_collection_tenant_scoping.py -v

# Asset write-back tests
python -m pytest tests/services/test_asset_write_back.py -v
```

### Running All Collection Tests

```bash
# Run all collection manual submission tests
python scripts/run_collection_tests.py

# Run with verbose output
python scripts/run_collection_tests.py --verbose

# Run specific test category
python scripts/run_collection_tests.py --gap
python scripts/run_collection_tests.py --tenant
python scripts/run_collection_tests.py --writeback
```

### Running Tests in Docker

```bash
# From project root
docker-compose exec backend python -m pytest tests/api/v1/endpoints/test_collection_gap_resolution.py -v
```

## Test Configuration

The tests use `pytest.ini` configuration for:

- **Test Discovery**: Automatic discovery of `test_*.py` files
- **Async Mode**: Automatic async test handling with `asyncio-mode=auto`
- **Output Format**: Verbose output with short tracebacks
- **Markers**: Custom markers for test categorization

## Security Considerations

The tests verify several security aspects:

1. **Tenant Isolation**: Multi-tenant data isolation is enforced
2. **SQL Injection Prevention**: Parameterized queries are used
3. **Input Validation**: Malformed UUIDs and contexts are rejected
4. **Field Whitelisting**: Only approved fields can be updated on assets
5. **Authorization**: Proper user and tenant context is required

## Integration with CI/CD

These tests are designed to run in continuous integration environments:

- **Fast Execution**: Tests use mocks for quick execution
- **Isolated Dependencies**: No external service dependencies
- **Clear Output**: Structured output for CI parsing
- **Exit Codes**: Proper exit codes for CI success/failure detection

## Future Enhancements

Potential areas for test expansion:

1. **Performance Tests**: Load testing with large datasets
2. **Integration Tests**: End-to-end testing with real database
3. **Concurrent Access Tests**: Multi-user concurrent submission testing
4. **Data Migration Tests**: Testing gap resolution with various data formats
5. **Audit Trail Tests**: Verification of audit logging functionality

## CC Generated with Claude Code

These comprehensive tests ensure the reliability, security, and correctness of the collection manual submission functionality, providing confidence in the gap resolution, tenant scoping, and asset write-back implementations.
