"""
Deprecation Middleware for API v3
Adds deprecation headers to old API versions and tracks usage.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add deprecation headers to old API versions"""
    
    # Mapping of deprecated paths to their v3 replacements
    DEPRECATED_PATHS = {
        "/api/v1/unified-discovery": "/api/v3/discovery-flow",
        "/api/v1/discovery": "/api/v3/discovery-flow", 
        "/api/v2/discovery-flows": "/api/v3/discovery-flow",
        "/api/v1/data-import": "/api/v3/data-import"
    }
    
    # Specific endpoint mappings for more precise deprecation messages
    ENDPOINT_MAPPINGS = {
        # Discovery Flow endpoints
        "/api/v1/unified-discovery/flow/initialize": "/api/v3/discovery-flow/flows",
        "/api/v1/discovery/session/{id}/status": "/api/v3/discovery-flow/flows/{id}/status",
        "/api/v2/discovery-flows/flows/active": "/api/v3/discovery-flow/flows?status=active",
        "/api/v1/unified-discovery/flow/status/{id}": "/api/v3/discovery-flow/flows/{id}/status",
        "/api/v2/discovery-flows/flows/{id}/continue": "/api/v3/discovery-flow/flows/{id}/resume",
        
        # Data Import endpoints  
        "/api/v1/data-import/store-import": "/api/v3/data-import/imports",
        "/api/v1/data-import/upload": "/api/v3/data-import/imports/upload",
        "/api/v1/data-import/validate": "/api/v3/data-import/imports/{id}/validate",
        
        # Field Mapping endpoints
        "/api/v1/field-mapping": "/api/v3/field-mapping/mappings",
        "/api/v1/data-import/field-mapping": "/api/v3/field-mapping/mappings"
    }
    
    # Sunset dates for different API versions
    SUNSET_DATES = {
        "v1": "2024-06-01",  # 6 months from implementation
        "v2": "2024-09-01"   # 9 months from implementation (newer API)
    }
    
    def __init__(self, app, track_usage: bool = True, log_deprecated_calls: bool = True):
        super().__init__(app)
        self.track_usage = track_usage
        self.log_deprecated_calls = log_deprecated_calls
        self.usage_stats: Dict[str, int] = {}
        self.warned_endpoints: Set[str] = set()
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Check if this is a deprecated endpoint
        deprecation_info = self._get_deprecation_info(path)
        
        if deprecation_info:
            # Log deprecated API usage
            if self.log_deprecated_calls:
                endpoint_key = f"{method} {path}"
                if endpoint_key not in self.warned_endpoints:
                    logger.warning(
                        f"🚨 DEPRECATED API USAGE: {method} {path} -> Use {deprecation_info['replacement']}"
                    )
                    self.warned_endpoints.add(endpoint_key)
            
            # Track usage statistics
            if self.track_usage:
                self.usage_stats[path] = self.usage_stats.get(path, 0) + 1
        
        # Process the request
        response = await call_next(request)
        
        # Add deprecation headers if this is a deprecated endpoint
        if deprecation_info:
            self._add_deprecation_headers(response, deprecation_info)
        
        return response
    
    def _get_deprecation_info(self, path: str) -> Optional[Dict[str, str]]:
        """Get deprecation information for a given path"""
        
        # Check for exact endpoint matches first
        if path in self.ENDPOINT_MAPPINGS:
            api_version = self._extract_api_version(path)
            return {
                "replacement": self.ENDPOINT_MAPPINGS[path],
                "message": f"This endpoint is deprecated. Use {self.ENDPOINT_MAPPINGS[path]}",
                "version": api_version,
                "sunset_date": self.SUNSET_DATES.get(api_version, "2024-12-31")
            }
        
        # Check for path prefix matches
        for deprecated_prefix, replacement_prefix in self.DEPRECATED_PATHS.items():
            if path.startswith(deprecated_prefix):
                api_version = self._extract_api_version(path)
                replacement_path = path.replace(deprecated_prefix, replacement_prefix, 1)
                return {
                    "replacement": replacement_path,
                    "message": f"This API version is deprecated. Use {replacement_prefix}",
                    "version": api_version,
                    "sunset_date": self.SUNSET_DATES.get(api_version, "2024-12-31")
                }
        
        return None
    
    def _extract_api_version(self, path: str) -> str:
        """Extract API version from path"""
        if "/api/v1/" in path:
            return "v1"
        elif "/api/v2/" in path:
            return "v2"
        else:
            return "unknown"
    
    def _add_deprecation_headers(self, response: Response, deprecation_info: Dict[str, str]):
        """Add deprecation headers to the response"""
        
        # Standard deprecation headers
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = deprecation_info["sunset_date"]
        response.headers["Link"] = f'<{deprecation_info["replacement"]}>; rel="successor-version"'
        
        # Custom headers for more detailed information
        response.headers["X-API-Deprecation-Warning"] = deprecation_info["message"]
        response.headers["X-API-Deprecation-Date"] = deprecation_info["sunset_date"]
        response.headers["X-API-Deprecated-Version"] = deprecation_info["version"]
        response.headers["X-API-Replacement-URL"] = deprecation_info["replacement"]
        
        # Add migration guide header
        response.headers["X-API-Migration-Guide"] = "https://docs.aiforce.com/api/v3/migration-guide"
        
        # Cache control to discourage caching of deprecated responses
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    def get_usage_stats(self) -> Dict[str, any]:
        """Get deprecation usage statistics"""
        return {
            "deprecated_endpoint_usage": dict(self.usage_stats),
            "total_deprecated_calls": sum(self.usage_stats.values()),
            "unique_deprecated_endpoints": len(self.usage_stats),
            "warned_endpoints": list(self.warned_endpoints),
            "collection_timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.usage_stats.clear()
        self.warned_endpoints.clear()


class DeprecationNoticeMiddleware(BaseHTTPMiddleware):
    """Lightweight middleware that just adds deprecation notices without tracking"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Process the request
        response = await call_next(request)
        
        # Add deprecation notice for all v1 and v2 APIs
        if "/api/v1/" in path or "/api/v2/" in path:
            response.headers["X-API-Deprecation-Notice"] = (
                "This API version is deprecated. Migrate to /api/v3/ for continued support."
            )
            response.headers["X-API-Current-Version"] = "v3"
            response.headers["X-API-Documentation"] = "https://docs.aiforce.com/api/v3/"
        
        return response


def create_deprecation_response_modifier(deprecated_paths: Dict[str, str]):
    """
    Factory function to create a response modifier for deprecated endpoints.
    This can be used as a dependency in FastAPI endpoints.
    """
    
    def modify_response(request: Request, response: Response):
        path = request.url.path
        
        for deprecated_prefix, replacement in deprecated_paths.items():
            if path.startswith(deprecated_prefix):
                # Add deprecation headers
                response.headers["X-API-Deprecation-Warning"] = (
                    f"This endpoint is deprecated. Use {replacement} instead."
                )
                response.headers["X-API-Replacement"] = replacement
                response.headers["Deprecation"] = "true"
                break
        
        return response
    
    return modify_response


# Usage example for FastAPI dependencies
deprecated_endpoint_modifier = create_deprecation_response_modifier(
    DeprecationMiddleware.DEPRECATED_PATHS
)


def log_deprecated_usage(endpoint: str, replacement: str, version: str = "unknown"):
    """Utility function to manually log deprecated usage"""
    logger.warning(
        f"🚨 DEPRECATED USAGE: {endpoint} (v{version}) -> Use {replacement}"
    )


def add_deprecation_headers_to_response(
    response: Response, 
    replacement_url: str,
    sunset_date: str = "2024-12-31",
    version: str = "unknown"
):
    """Utility function to manually add deprecation headers"""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = sunset_date
    response.headers["X-API-Deprecation-Warning"] = f"Use {replacement_url} instead"
    response.headers["X-API-Replacement-URL"] = replacement_url
    response.headers["X-API-Deprecated-Version"] = version