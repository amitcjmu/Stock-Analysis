# DataImport Model Fields Fix Summary

## Problem
The import storage handler was using outdated field names that don't match the current DataImport model, causing a 500 error:
- `'source_filename' is an invalid keyword argument for DataImport`

## Root Cause
The DataImport model was updated with consolidated field names, but the import storage handler wasn't updated to match:
- `source_filename` → `filename`
- `file_size_bytes` → `file_size`
- `file_type` → `mime_type`
- `is_mock` was removed from the model

Additionally, RawImportRecord model fields were changed:
- `row_number` → `record_index`
- `is_processed` and `is_valid` fields were removed

## Solution

### 1. Updated import_storage_handler.py
Fixed all field references to match the current model:
- Changed `source_filename` to `filename` throughout the file
- Changed `file_size_bytes` to `file_size`
- Changed `file_type` to `mime_type`
- Removed `is_mock` field
- Changed `row_number` to `record_index`
- Removed `is_processed` and `is_valid` fields from RawImportRecord creation
- Removed `import_config` assignment (field doesn't exist in model)

## Testing
The data import should now work without the 500 error. The handler properly creates DataImport records with the correct field names.