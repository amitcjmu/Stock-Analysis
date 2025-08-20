# Data Import API Troubleshooting Guide

## Common Issues and Solutions

### 1. Authentication Errors

#### Problem: 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

**Solutions:**
- Verify Bearer token is included in Authorization header
- Check token hasn't expired
- Ensure token format is correct: `Bearer <token>`

```bash
# Correct
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Incorrect
curl -H "Authorization: eyJhbGciOiJIUzI1NiIs..."  # Missing "Bearer" prefix
```

#### Problem: Missing Multi-tenant Headers
```json
{
  "detail": "Missing required headers: X-Client-Account-ID, X-Engagement-ID"
}
```

**Solutions:**
- Include both required headers in all requests:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_TOKEN',
  'X-Client-Account-ID': '1',
  'X-Engagement-ID': '1'
}
```

### 2. Data Validation Errors

#### Problem: Invalid CSV Format
```json
{
  "error": "validation_error",
  "message": "Invalid CSV data format",
  "details": {
    "missing_columns": ["server_name", "ip_address"],
    "invalid_rows": [3, 7, 12]
  }
}
```

**Solutions:**
- Ensure required columns are present based on import type
- Check for proper CSV formatting (commas, quotes)
- Validate data types match expected format

**Required Fields by Import Type:**

| Import Type | Required Fields |
|-------------|----------------|
| servers | server_name, ip_address, os |
| applications | app_name, version, server_name |
| databases | db_name, db_type, server_name |

#### Problem: Empty or Invalid Data
```json
{
  "error": "validation_error",
  "message": "File contains no valid data rows"
}
```

**Solutions:**
- Ensure CSV has header row and at least one data row
- Remove empty rows or rows with all empty values
- Check for BOM (Byte Order Mark) issues in UTF-8 files

### 3. Flow Conflicts

#### Problem: Incomplete Discovery Flow Exists
```json
{
  "error": "incomplete_discovery_flow_exists",
  "message": "An incomplete discovery flow already exists for this engagement",
  "existing_flow": {
    "flow_id": "disc_flow_123",
    "status": "processing",
    "created_at": "2025-01-15T09:00:00Z"
  }
}
```

**Solutions:**

1. **Check flow status:**
```bash
curl -X GET "https://api.yourdomain.com/api/v1/flows/active" \
  -H "Authorization: Bearer TOKEN" \
  -H "X-Client-Account-ID: 1" \
  -H "X-Engagement-ID: 1"
```

2. **Complete the existing flow:**
- Wait for it to finish processing
- Review and complete any pending steps

3. **Cancel the existing flow:**
```bash
curl -X DELETE "https://api.yourdomain.com/api/v1/master-flows/disc_flow_123" \
  -H "Authorization: Bearer TOKEN" \
  -H "X-Client-Account-ID: 1" \
  -H "X-Engagement-ID: 1"
```

### 4. File Size and Performance Issues

#### Problem: Request Too Large
```json
{
  "error": "request_too_large",
  "message": "File size exceeds maximum allowed size of 100MB"
}
```

**Solutions:**
- Split large files into smaller chunks (< 100MB each)
- Compress data before uploading
- Use batch import endpoints for large datasets

**Chunking Example:**
```python
def chunk_csv_data(data, chunk_size=1000):
    """Split data into chunks for batch processing."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# Import in chunks
for i, chunk in enumerate(chunk_csv_data(large_dataset)):
    result = client.import_data_direct(
        data=chunk,
        filename=f"servers_chunk_{i}.csv",
        import_type="servers"
    )
```

#### Problem: Timeout During Processing
```json
{
  "error": "timeout_error",
  "message": "Import processing timed out"
}
```

**Solutions:**
- Reduce batch size
- Implement retry logic with exponential backoff
- Use async processing for large imports

### 5. Data Quality Issues

#### Problem: Invalid IP Addresses
```json
{
  "error": "validation_error",
  "details": {
    "invalid_ips": ["not-an-ip", "256.256.256.256", "10.0.0"]
  }
}
```

**Solutions:**
```python
import ipaddress

def validate_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

# Clean data before import
cleaned_data = [
    row for row in data
    if validate_ip(row.get('ip_address', ''))
]
```

#### Problem: Duplicate Records
```json
{
  "warning": "duplicate_records_detected",
  "duplicates": [
    {"server_name": "prod-web-01", "count": 3}
  ]
}
```

**Solutions:**
```python
# Remove duplicates before import
seen = set()
unique_data = []
for row in data:
    key = row['server_name']
    if key not in seen:
        seen.add(key)
        unique_data.append(row)
```

### 6. Rate Limiting

#### Problem: 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 60 seconds",
  "retry_after": 60
}
```

**Solutions:**
- Implement exponential backoff
- Respect retry-after header
- Use bulk operations instead of individual requests

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }
}
```

### 7. Debugging Tips

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Log request details
logger.debug(f"Request URL: {url}")
logger.debug(f"Request Headers: {headers}")
logger.debug(f"Request Body: {json.dumps(data, indent=2)}")
```

#### Validate JSON Structure
```javascript
// Use JSON schema validation
const Ajv = require('ajv');
const ajv = new Ajv();

const schema = {
  type: 'object',
  properties: {
    file_data: { type: 'array', minItems: 1 },
    metadata: { type: 'object' },
    upload_context: { type: 'object' }
  },
  required: ['file_data', 'metadata', 'upload_context']
};

const validate = ajv.compile(schema);
if (!validate(requestData)) {
  console.error('Validation errors:', validate.errors);
}
```

#### Test with Minimal Data
Start with a single record to isolate issues:
```json
{
  "file_data": [
    {
      "server_name": "test-server",
      "ip_address": "10.0.0.1",
      "os": "Ubuntu 20.04"
    }
  ],
  "metadata": {
    "filename": "test.csv",
    "size": 100,
    "type": "text/csv"
  },
  "upload_context": {
    "intended_type": "servers",
    "upload_timestamp": "2025-01-15T10:00:00Z"
  }
}
```

### 8. Contact Support

If issues persist after trying these solutions:

1. **Collect Debug Information:**
   - Request ID from response headers
   - Exact error message and status code
   - Sample of data causing issues
   - Time of occurrence

2. **Check System Status:**
   - API health endpoint: `GET /api/v1/health`
   - Service status page

3. **Submit Support Ticket:**
   - Include debug information
   - Describe steps to reproduce
   - Provide expected vs actual behavior

## Prevention Best Practices

1. **Validate Data Locally First**
   - Use schema validation before sending
   - Check for required fields
   - Validate data types and formats

2. **Implement Proper Error Handling**
   - Catch and handle specific error types
   - Provide user-friendly error messages
   - Log errors for debugging

3. **Monitor Import Progress**
   - Poll status endpoint regularly
   - Implement timeout handling
   - Alert on failures

4. **Use Idempotent Operations**
   - Store import IDs for retry
   - Check for existing imports before creating new ones
   - Implement proper cleanup on failures
