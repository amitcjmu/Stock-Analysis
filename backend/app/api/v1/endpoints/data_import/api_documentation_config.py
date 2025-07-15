"""
API Documentation Configuration for Data Import Endpoints.

This module configures FastAPI's automatic documentation generation
with custom examples, descriptions, and tags.
"""

from fastapi import FastAPI
from typing import Dict, Any


def configure_api_documentation(app: FastAPI) -> None:
    """
    Configure API documentation with custom settings and examples.
    
    Args:
        app: FastAPI application instance
    """
    
    # Custom API metadata
    app.title = "AI Force Migration Platform - Data Import API"
    app.description = """
## AI Force Migration Platform Data Import API

The Data Import API provides comprehensive endpoints for managing CSV data imports
as part of the discovery flow process. This API handles:

- 📤 **Data Upload**: Store CSV data for processing
- 🔄 **Flow Integration**: Automatic discovery flow triggering
- 📊 **Status Tracking**: Real-time import progress monitoring
- 🔍 **Data Retrieval**: Access imported data and metadata
- ⚡ **Batch Operations**: Efficient handling of large datasets

### Key Features

- **Multi-tenant Support**: Full isolation between clients and engagements
- **Automatic Validation**: Data quality checks and format validation
- **Flow Orchestration**: Seamless integration with discovery flows
- **Real-time Updates**: WebSocket support for live progress
- **Comprehensive Error Handling**: Detailed error messages and recovery options

### Getting Started

1. **Authentication**: All endpoints require Bearer token authentication
2. **Multi-tenant Headers**: Include X-Client-Account-ID and X-Engagement-ID
3. **Data Format**: CSV data should be parsed into JSON array format
4. **Flow Management**: One active discovery flow per engagement at a time

### Example Usage

```python
import requests

# Configure headers
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "X-Client-Account-ID": "1",
    "X-Engagement-ID": "1",
    "Content-Type": "application/json"
}

# Import server data
data = {
    "file_data": [
        {
            "server_name": "prod-web-01",
            "ip_address": "10.0.1.10",
            "os": "Ubuntu 20.04"
        }
    ],
    "metadata": {
        "filename": "servers.csv",
        "size": 1024,
        "type": "text/csv"
    },
    "upload_context": {
        "intended_type": "servers",
        "upload_timestamp": "2025-01-15T10:30:00Z"
    }
}

response = requests.post(
    "https://api.yourdomain.com/api/v1/data-import/store-import",
    headers=headers,
    json=data
)
```

### API Documentation

- 📚 **Interactive Docs**: Available at `/docs` (Swagger UI)
- 📖 **Alternative Docs**: Available at `/redoc` (ReDoc)
- 📥 **OpenAPI Schema**: Download at `/openapi.json`
    """
    
    app.version = "1.0.0"
    app.contact = {
        "name": "API Support",
        "email": "api-support@aiforce.com"
    }
    app.license_info = {
        "name": "Proprietary",
        "url": "https://aiforce.com/license"
    }
    
    # Custom tags for grouping endpoints
    tags_metadata = [
        {
            "name": "Data Import",
            "description": "Core data import operations including upload, storage, and retrieval",
            "externalDocs": {
                "description": "Data Import Guide",
                "url": "https://docs.aiforce.com/api/data-import"
            }
        },
        {
            "name": "Import Storage",
            "description": "Storage and persistence operations for imported data"
        },
        {
            "name": "Import Retrieval",
            "description": "Data retrieval and query operations"
        },
        {
            "name": "Field Mapping",
            "description": "Field mapping and transformation operations"
        },
        {
            "name": "Clean API",
            "description": "Simplified API endpoints for common operations"
        },
        {
            "name": "Health",
            "description": "Service health and status checks"
        }
    ]
    
    app.openapi_tags = tags_metadata


def get_custom_openapi_schema() -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with additional examples and documentation.
    
    Returns:
        Custom OpenAPI schema dictionary
    """
    return {
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT Bearer token authentication"
                },
                "MultiTenantHeaders": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Client-Account-ID",
                    "description": "Client account identifier for multi-tenant isolation"
                },
                "EngagementHeader": {
                    "type": "apiKey",
                    "in": "header", 
                    "name": "X-Engagement-ID",
                    "description": "Engagement identifier for data isolation"
                }
            },
            "responses": {
                "UnauthorizedError": {
                    "description": "Authentication token is missing or invalid",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "string",
                                        "example": "Not authenticated"
                                    }
                                }
                            }
                        }
                    }
                },
                "ForbiddenError": {
                    "description": "User doesn't have permission to access this resource",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "string",
                                        "example": "Not enough permissions"
                                    }
                                }
                            }
                        }
                    }
                },
                "ValidationError": {
                    "description": "Request validation failed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "loc": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                },
                                                "msg": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "security": [
            {"BearerAuth": []},
            {"MultiTenantHeaders": []},
            {"EngagementHeader": []}
        ]
    }


# Example requests for documentation
EXAMPLE_REQUESTS = {
    "server_import": {
        "summary": "Import server inventory data",
        "value": {
            "file_data": [
                {
                    "server_name": "prod-web-01",
                    "ip_address": "10.0.1.10",
                    "os": "Ubuntu 20.04",
                    "cpu_cores": 8,
                    "memory_gb": 16,
                    "storage_gb": 500,
                    "environment": "production",
                    "business_unit": "Sales"
                },
                {
                    "server_name": "prod-db-01",
                    "ip_address": "10.0.1.20",
                    "os": "RHEL 8",
                    "cpu_cores": 16,
                    "memory_gb": 64,
                    "storage_gb": 2000,
                    "environment": "production",
                    "business_unit": "Sales"
                }
            ],
            "metadata": {
                "filename": "servers_inventory.csv",
                "size": 102400,
                "type": "text/csv"
            },
            "upload_context": {
                "intended_type": "servers",
                "upload_timestamp": "2025-01-15T10:30:00Z"
            }
        }
    },
    "application_import": {
        "summary": "Import application inventory",
        "value": {
            "file_data": [
                {
                    "app_name": "CustomerPortal",
                    "version": "2.3.4",
                    "server_name": "prod-web-01",
                    "technology_stack": "Java Spring Boot",
                    "criticality": "High"
                }
            ],
            "metadata": {
                "filename": "applications.csv",
                "size": 51200,
                "type": "text/csv"
            },
            "upload_context": {
                "intended_type": "applications",
                "upload_timestamp": "2025-01-15T10:30:00Z"
            }
        }
    }
}


# Example responses for documentation
EXAMPLE_RESPONSES = {
    "import_success": {
        "summary": "Successful import response",
        "value": {
            "success": True,
            "message": "Data imported successfully and discovery flow triggered",
            "data_import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
            "flow_id": "disc_flow_456e7890-1234-56ab-cdef-0123456789ab",
            "total_records": 2,
            "import_type": "servers",
            "next_steps": [
                "Monitor discovery flow progress",
                "Review field mappings when available",
                "Validate critical attributes"
            ]
        }
    },
    "flow_conflict": {
        "summary": "Existing flow conflict",
        "value": {
            "success": False,
            "error": "incomplete_discovery_flow_exists",
            "message": "An incomplete discovery flow already exists for this engagement",
            "details": {
                "existing_flow": {
                    "flow_id": "disc_flow_123",
                    "status": "processing",
                    "created_at": "2025-01-15T09:00:00Z"
                }
            },
            "recommendations": [
                "Complete or cancel the existing discovery flow",
                "Review the current flow status",
                "Contact support if the flow is stuck"
            ]
        }
    }
}