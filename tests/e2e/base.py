"""
Base utilities for E2E testing.
Provides common functionality for end-to-end test suites.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    passed: bool
    details: str = ""
    timestamp: str = ""
    execution_time: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class TestResultTracker:
    """Tracks test results and provides reporting."""

    def __init__(self):
        self.results: List[TestResult] = []

    def log_result(
        self,
        test_name: str,
        passed: bool,
        details: str = "",
        execution_time: float = 0.0
    ):
        """Log a test result."""
        result = TestResult(
            test_name=test_name,
            passed=passed,
            details=details,
            execution_time=execution_time
        )
        self.results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} - {test_name}")
        if details:
            print(f"   Details: {details}")
        if execution_time > 0:
            print(f"   Execution time: {execution_time:.2f}s")

    @property
    def passed_count(self) -> int:
        """Get count of passed tests."""
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        """Get count of failed tests."""
        return sum(1 for r in self.results if not r.passed)

    @property
    def total_count(self) -> int:
        """Get total test count."""
        return len(self.results)

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.passed_count / self.total_count) * 100

    def get_failed_tests(self) -> List[TestResult]:
        """Get list of failed tests."""
        return [r for r in self.results if not r.passed]

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        print(f"\nTotal Tests: {self.total_count}")
        print(f"Passed: {self.passed_count} ✅")
        print(f"Failed: {self.failed_count} ❌")
        print(f"Success Rate: {self.success_rate:.1f}%")

        if self.failed_count == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️ SOME TESTS FAILED:")
            for result in self.get_failed_tests():
                print(f"  - {result.test_name}: {result.details}")

        print("\n" + "="*80)

    def save_results(self, filename: str = "test_results.json"):
        """Save results to JSON file."""
        data = {
            "summary": {
                "total": self.total_count,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "success_rate": self.success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "details": r.details,
                    "timestamp": r.timestamp,
                    "execution_time": r.execution_time
                }
                for r in self.results
            ]
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\nTest results saved to: {filename}")


class E2ETestBase:
    """Base class for E2E test suites."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tracker = TestResultTracker()
        self.headers = {
            "Content-Type": "application/json",
            "X-Client-Account-ID": "1",
            "X-Engagement-ID": "1"
        }

    async def setup(self):
        """Setup method called before tests."""
        pass

    async def teardown(self):
        """Teardown method called after tests."""
        pass

    async def run_test(
        self,
        test_name: str,
        test_func,
        *args,
        **kwargs
    ) -> bool:
        """Run a single test and track results."""
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func(*args, **kwargs)
            else:
                result = test_func(*args, **kwargs)

            execution_time = time.time() - start_time

            if isinstance(result, bool):
                passed = result
                details = "Test completed"
            elif isinstance(result, dict) and "passed" in result:
                passed = result["passed"]
                details = result.get("details", "")
            else:
                passed = True
                details = str(result) if result else "Test completed"

            self.tracker.log_result(test_name, passed, details, execution_time)
            return passed

        except Exception as e:
            execution_time = time.time() - start_time
            self.tracker.log_result(test_name, False, str(e), execution_time)
            return False

    async def run_all_tests(self, test_methods: List[tuple]) -> bool:
        """Run all tests in the list."""
        await self.setup()

        try:
            for test_name, test_func, *args in test_methods:
                await self.run_test(test_name, test_func, *args)

            self.tracker.print_summary()
            return self.tracker.failed_count == 0

        finally:
            await self.teardown()

    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, headers=request_headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == "application/json" else await response.text(),
                        "headers": dict(response.headers)
                    }
            elif method.upper() == "POST":
                async with session.post(url, json=data, headers=request_headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == "application/json" else await response.text(),
                        "headers": dict(response.headers)
                    }
            elif method.upper() == "PUT":
                async with session.put(url, json=data, headers=request_headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == "application/json" else await response.text(),
                        "headers": dict(response.headers)
                    }
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=request_headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == "application/json" else await response.text(),
                        "headers": dict(response.headers)
                    }
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

    async def wait_for_condition(
        self,
        condition_func,
        max_attempts: int = 30,
        delay: float = 1.0,
        timeout_message: str = "Condition timeout"
    ) -> bool:
        """Wait for a condition to be true."""
        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(condition_func):
                    if await condition_func():
                        return True
                else:
                    if condition_func():
                        return True
            except Exception:
                pass

            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)

        return False
