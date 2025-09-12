# Data Processing Artifact Cleanup Patterns

## Problem: Extra Columns in Imported Data Display
**Issue**: Extra columns (like row_index) appearing in UI that don't exist in original CSV files.

## Common Causes
1. Pandas DataFrame operations adding index columns
2. Processing pipelines adding metadata fields
3. Data transformation artifacts

## Solution Pattern
Filter unwanted columns at the response layer before returning to frontend:

```python
# In get_import_data or similar methods
# Build response data, filtering out any processing artifacts
data = []
for record in raw_records:
    if record.raw_data:
        # Filter out processing artifacts (regression fix)
        cleaned_data = {
            k: v for k, v in record.raw_data.items()
            if k not in ['row_index', '_id', '_processed']  # Add any artifacts here
        }
        data.append(cleaned_data)
```

## Prevention Patterns
1. **CSV Reading**: Use index_col=False when reading CSVs with pandas
2. **DataFrame Conversion**: Use to_dict('records') without reset_index()
3. **Response Layer**: Always clean data before sending to frontend

## Files Fixed
- backend/app/services/data_import/storage_manager/operations.py:320-330

## Common Artifacts to Filter
- row_index: Added by pandas operations
- _id: MongoDB-style internal IDs
- _processed: Internal processing flags
- index: Default pandas index column

## Testing
1. Upload a CSV file
2. Check imported data display for extra columns
3. Verify only original CSV columns are shown
4. Check raw database to confirm artifacts aren't stored

## Related Issues
- This was a regression of a previously fixed bug
- Consider adding unit tests to prevent regression
- May appear after pandas/library updates
