# Database Timeout Configuration

## Overview
This document explains the database timeout configuration implemented to handle long-running asset inventory operations.

## Problem
The asset inventory page was experiencing `TimeoutError` when processing large datasets because the default database session timeout of 60 seconds was insufficient.

## Solution

### 1. Backend - Extended Database Sessions
Created `database_timeout.py` with configurable timeouts for different operation types:

- **Default**: 60 seconds
- **Asset List**: 120 seconds (2 minutes)
- **Asset Analysis**: 300 seconds (5 minutes) 
- **Bulk Operations**: 180 seconds (3 minutes)
- **Report Generation**: 240 seconds (4 minutes)

Usage:
```python
from app.core.database_timeout import get_db_for_asset_list

@router.get("/list/paginated")
async def list_assets_paginated(
    db: AsyncSession = Depends(get_db_for_asset_list),
    # ... other parameters
):
```

### 2. Frontend - Request Timeouts
Added timeout handling to `apiCall` with operation-specific timeouts:

- `/assets/list/paginated`: 2 minutes
- `/assets/analyze`: 5 minutes
- `/bulk` operations: 3 minutes
- Default: 1 minute

The frontend uses `AbortController` to cancel requests that exceed the timeout and provides user-friendly error messages.

### 3. Query Optimization
- Optimized asset listing by pre-calculating summary stats
- Added database indexes for common query patterns:
  - Composite index on `client_account_id` and `engagement_id`
  - Index on `created_at DESC` for pagination
  - Indexes on `asset_type` and `status` for filtering

### 4. Error Handling
- Backend logs timeout errors with context
- Frontend displays specific timeout messages
- Timeout errors are distinguished from other errors (status 408)

## Testing
To test timeout handling:
1. Create a large dataset (1000+ assets)
2. Access the inventory page
3. Monitor network tab for request duration
4. Verify no timeout errors occur

## Monitoring
- Check backend logs for "Database session timeout" errors
- Monitor `connection_health` metrics
- Track API response times in browser console

## Future Improvements
1. Implement cursor-based pagination for very large datasets
2. Add background job processing for heavy operations
3. Implement request queuing for concurrent operations
4. Add progress indicators for long-running requests