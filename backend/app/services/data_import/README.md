# Data Import Services - Modular Architecture

This directory contains the modular data import services architecture, refactored from the original monolithic `import_storage_handler.py` (872 LOC) into clean, maintainable components.

## Architecture Overview

The modular architecture follows a composition pattern where the main `ImportStorageHandler` orchestrates specialized services:

```
ImportStorageHandler (Main Orchestrator)
├── ImportValidator          - Data validation and conflict checking
├── ImportStorageManager     - Database operations and CRUD
├── FlowTriggerService       - Flow creation and triggering
├── ImportTransactionManager - Transaction handling and rollback
├── BackgroundExecutionService - Async flow execution
└── ImportResponseBuilder    - Response formatting
```

## Modular Components

### 1. ImportValidator (`import_validator.py`)
- **Purpose**: Data validation logic and conflict checking
- **Responsibilities**:
  - Schema validation and data integrity checks
  - Business rule validation
  - Import format verification
  - Discovery flow conflict detection
- **Key Methods**:
  - `validate_import_context()` - Validates request context
  - `validate_import_id()` - Validates UUID format
  - `validate_no_incomplete_discovery_flow()` - Prevents conflicting flows
  - `validate_import_data()` - Validates data quality

### 2. ImportStorageManager (`storage_manager.py`)
- **Purpose**: Database storage operations and CRUD
- **Responsibilities**:
  - Data persistence and retrieval
  - Transaction management for storage
  - Storage optimization and indexing
  - Raw record management
- **Key Methods**:
  - `find_or_create_import()` - Manages import records
  - `store_raw_records()` - Stores raw CSV data
  - `create_field_mappings()` - Creates initial field mappings
  - `update_import_status()` - Updates import status
  - `get_raw_records()` - Retrieves stored data

### 3. FlowTriggerService (`flow_trigger_service.py`)
- **Purpose**: Discovery flow creation and triggering
- **Responsibilities**:
  - Master flow orchestration integration
  - Flow initialization and setup
  - Flow configuration management
  - Background flow execution setup
- **Key Methods**:
  - `trigger_discovery_flow_atomic()` - Atomic flow creation
  - `trigger_discovery_flow()` - Standalone flow creation
  - `prepare_flow_configuration()` - Flow config preparation
  - `validate_flow_prerequisites()` - Pre-flight validation

### 4. ImportTransactionManager (`transaction_manager.py`)
- **Purpose**: Atomic transaction handling and rollback
- **Responsibilities**:
  - Multi-step operation coordination
  - Error recovery and cleanup
  - Transaction state tracking
  - Savepoint management
- **Key Methods**:
  - `transaction()` - Context manager for transactions
  - `savepoint()` - Savepoint management
  - `execute_with_retry()` - Retry logic for operations
  - `validate_transaction_state()` - Transaction state validation

### 5. BackgroundExecutionService (`background_execution_service.py`)
- **Purpose**: Async flow execution management
- **Responsibilities**:
  - Background task scheduling
  - Long-running operation handling
  - Progress tracking and monitoring
  - Flow status management
- **Key Methods**:
  - `start_background_flow_execution()` - Initiates background processing
  - `monitor_flow_progress()` - Tracks flow progress
  - `cancel_background_execution()` - Cancels running flows
  - `get_execution_status()` - Retrieves execution status

### 6. ImportResponseBuilder (`response_builder.py`)
- **Purpose**: Response formatting and standardization
- **Responsibilities**:
  - Success/error response construction
  - Data transformation for API responses
  - Status message generation
  - Performance metrics formatting
- **Key Methods**:
  - `success_response()` - Success response formatting
  - `error_response()` - Error response formatting
  - `partial_success_response()` - Partial success handling
  - `format_import_metadata()` - Metadata formatting

## Main Orchestrator

### ImportStorageHandler (`import_storage_handler.py`)
- **Purpose**: Main composition service that orchestrates all modules
- **Pattern**: Dependency injection and composition
- **Key Features**:
  - Maintains all existing functionality
  - Provides clean API for endpoints
  - Handles transaction coordination
  - Manages error handling and recovery

## Benefits of Modular Architecture

### 1. **Maintainability**
- Each module has a single responsibility
- Easy to locate and fix issues
- Clear separation of concerns
- Reduced cognitive load

### 2. **Testability**
- Each module can be tested independently
- Mock dependencies for unit testing
- Focused test coverage
- Easier debugging

### 3. **Scalability**
- Easy to add new features
- Components can be optimized independently
- Parallel development possible
- Easier to refactor specific areas

### 4. **Reliability**
- Isolated failure points
- Better error handling
- Atomic operations preserved
- Transaction integrity maintained

## Usage Example

```python
# Initialize the orchestrator
import_handler = ImportStorageHandler(db, client_account_id)

# Handle complete import process
response = await import_handler.handle_import(store_request, context)

# Get import status
status = await import_handler.get_import_status(import_id)

# Retry failed import
retry_response = await import_handler.retry_failed_import(import_id, context)
```

## Database Integration

- **PostgreSQL-only**: All modules use async PostgreSQL sessions
- **Multi-tenant**: All operations include client account scoping
- **Transaction Safety**: Atomic operations with proper rollback
- **Performance**: Optimized queries with limits and indexing

## Error Handling

- **Structured Exceptions**: Custom exception types for different error categories
- **Graceful Degradation**: Fail-safe operations where appropriate
- **Detailed Logging**: Comprehensive logging for debugging
- **User-Friendly Messages**: Clear error messages for API consumers

## Integration Points

- **Master Flow Orchestrator**: Seamless integration with CrewAI flows
- **CrewAI Services**: Real CrewAI flow execution
- **Background Tasks**: Async task management
- **API Endpoints**: Clean integration with FastAPI endpoints

## Migration Notes

- **Backward Compatibility**: All existing API contracts maintained
- **Database Schema**: No schema changes required
- **Configuration**: No configuration changes needed
- **Deployment**: Drop-in replacement for existing handler

The modular architecture provides a solid foundation for future enhancements while maintaining all existing functionality and improving code maintainability.