"""
API Test Client for integration testing.
Provides utilities for testing API endpoints in the test environment.
"""

import httpx
from typing import Dict, Any, Optional
import os


class APITestClient:
    """Test client for API integration testing."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """Initialize the test client."""
        self.base_url = base_url or os.getenv("TEST_API_BASE_URL", "http://localhost:8000")
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            "Content-Type": "application/json",
            "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",  # Demo Corporation
            "X-Engagement-Id": "58467010-6a72-44e8-ba37-cc0238724455",  # Azure Transformation 2025
            "X-User-Id": "77b30e13-c331-40eb-a0ec-ed0717f72b22",  # Test user
        }

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make a GET request."""
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)

        return await self.client.get(url, headers=request_headers, **kwargs)

    async def post(
        self,
        url: str,
        json: Any = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make a POST request."""
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)

        return await self.client.post(
            url,
            json=json,
            data=data,
            headers=request_headers,
            **kwargs
        )

    async def put(
        self,
        url: str,
        json: Any = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make a PUT request."""
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)

        return await self.client.put(
            url,
            json=json,
            data=data,
            headers=request_headers,
            **kwargs
        )

    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make a DELETE request."""
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)

        return await self.client.delete(url, headers=request_headers, **kwargs)

    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = await self.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def wait_for_health(self, max_attempts: int = 30, delay: float = 1.0) -> bool:
        """Wait for the API to become healthy."""
        import asyncio

        for _ in range(max_attempts):
            if await self.health_check():
                return True
            await asyncio.sleep(delay)

        return False
