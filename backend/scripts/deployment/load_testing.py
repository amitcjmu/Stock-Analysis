#!/usr/bin/env python3
"""
Load Testing Script for Master Flow Orchestrator
Phase 6: Day 9 - Perform Load Testing (MFO-096)

This script performs comprehensive load testing of the Master Flow Orchestrator
to ensure it can handle production-level traffic and concurrent flow operations.
"""

import asyncio
import json
import logging
import os
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('load_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoadTestRunner:
    """Performs comprehensive load testing of Master Flow Orchestrator"""
    
    def __init__(self):
        self.test_id = f"load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.base_path = Path(__file__).parent.parent.parent
        self.results_path = self.base_path / "test_results" / "load_testing"
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # Load test configuration
        self.config = {
            "backend_url": os.getenv("BACKEND_URL", "http://localhost:8001"),
            "test_duration": 300,  # 5 minutes
            "ramp_up_duration": 60,  # 1 minute
            "concurrent_users": 50,
            "max_users": 100,
            "flow_operations_per_user": 10,
            "think_time_min": 1,
            "think_time_max": 5,
            "timeout": 30,
            "error_threshold": 0.05,  # 5% error rate threshold
            "response_time_threshold": 2.0,  # 2 seconds
        }
        
        # Test scenarios
        self.scenarios = [
            {
                "name": "create_discovery_flow",
                "weight": 30,
                "endpoint": "/api/v1/flows",
                "method": "POST",
                "data": {
                    "flow_type": "discovery",
                    "flow_name": "Load Test Discovery Flow",
                    "configuration": {"test": True}
                }
            },
            {
                "name": "get_active_flows",
                "weight": 25,
                "endpoint": "/api/v1/flows/active",
                "method": "GET"
            },
            {
                "name": "get_flow_status",
                "weight": 20,
                "endpoint": "/api/v1/flows/{flow_id}/status",
                "method": "GET"
            },
            {
                "name": "execute_flow_phase",
                "weight": 15,
                "endpoint": "/api/v1/flows/{flow_id}/execute",
                "method": "POST",
                "data": {
                    "phase_name": "data_import",
                    "phase_input": {"test_data": True}
                }
            },
            {
                "name": "pause_flow",
                "weight": 5,
                "endpoint": "/api/v1/flows/{flow_id}/pause",
                "method": "POST",
                "data": {"reason": "load_test_pause"}
            },
            {
                "name": "resume_flow",
                "weight": 5,
                "endpoint": "/api/v1/flows/{flow_id}/resume",
                "method": "POST",
                "data": {"resume_context": {"test": True}}
            }
        ]
        
        # Test results
        self.test_results = {
            "test_id": self.test_id,
            "start_time": datetime.now().isoformat(),
            "configuration": self.config,
            "scenarios": self.scenarios,
            "metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "response_times": [],
                "error_rate": 0.0,
                "throughput": 0.0,
                "concurrent_flows": 0,
                "system_metrics": []
            },
            "scenario_results": {},
            "performance_issues": [],
            "errors": []
        }
        
        # Flow tracking
        self.created_flows = []
        self.session_headers = {
            "Content-Type": "application/json",
            "X-Client-Account-ID": "1",
            "X-Engagement-ID": "1",
            "X-User-ID": "load-test-user"
        }
        
        logger.info(f"🚀 Starting load testing: {self.test_id}")
    
    async def run_load_testing(self) -> bool:
        """
        Run comprehensive load testing
        Task: MFO-096
        """
        try:
            logger.info("=" * 80)
            logger.info("📊 LOAD TESTING - MASTER FLOW ORCHESTRATOR")
            logger.info("=" * 80)
            
            # Phase 1: Pre-test validation
            if not await self._pre_test_validation():
                return False
            
            # Phase 2: Baseline performance test
            if not await self._run_baseline_test():
                return False
            
            # Phase 3: Ramp-up load test
            if not await self._run_ramp_up_test():
                return False
            
            # Phase 4: Sustained load test
            if not await self._run_sustained_load_test():
                return False
            
            # Phase 5: Spike load test
            if not await self._run_spike_test():
                return False
            
            # Phase 6: Stress test
            if not await self._run_stress_test():
                return False
            
            # Phase 7: Flow concurrency test
            if not await self._run_flow_concurrency_test():
                return False
            
            # Phase 8: Generate load test report
            await self._generate_load_test_report()
            
            # Determine success based on thresholds
            error_rate = self.test_results["metrics"]["error_rate"]
            avg_response_time = statistics.mean(self.test_results["metrics"]["response_times"]) if self.test_results["metrics"]["response_times"] else 0
            
            success = (
                error_rate <= self.config["error_threshold"] and
                avg_response_time <= self.config["response_time_threshold"]
            )
            
            if success:
                logger.info("✅ Load testing PASSED!")
            else:
                logger.error(f"❌ Load testing FAILED - Error rate: {error_rate:.2%}, Avg response time: {avg_response_time:.2f}s")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Load testing failed: {e}")
            await self._handle_load_test_failure(e)
            return False
    
    async def _pre_test_validation(self) -> bool:
        """Validate system before load testing"""
        logger.info("📋 Phase 1: Pre-test validation")
        
        try:
            # Check system health
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config['backend_url']}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ System health check failed: {response.status}")
                        return False
            
            # Check Master Flow Orchestrator availability
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config['backend_url']}/api/v1/flows/active",
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status >= 500:
                        logger.error(f"❌ Master Flow Orchestrator not available: {response.status}")
                        return False
            
            # Record baseline system metrics
            await self._record_system_metrics("baseline")
            
            logger.info("✅ Pre-test validation completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pre-test validation failed: {e}")
            return False
    
    async def _run_baseline_test(self) -> bool:
        """Run baseline performance test with single user"""
        logger.info("📋 Phase 2: Baseline performance test")
        
        try:
            start_time = time.time()
            
            # Single user scenario
            async with aiohttp.ClientSession() as session:
                for scenario in self.scenarios:
                    response_time, success, error = await self._execute_scenario(session, scenario)
                    
                    if success:
                        logger.info(f"✅ Baseline {scenario['name']}: {response_time:.2f}s")
                    else:
                        logger.warning(f"⚠️  Baseline {scenario['name']} failed: {error}")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
            
            duration = time.time() - start_time
            logger.info(f"✅ Baseline test completed in {duration:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Baseline test failed: {e}")
            return False
    
    async def _run_ramp_up_test(self) -> bool:
        """Run ramp-up load test"""
        logger.info("📋 Phase 3: Ramp-up load test")
        
        try:
            self.config["ramp_up_duration"]
            max_users = self.config["concurrent_users"]
            
            # Gradually increase load
            for current_users in range(1, max_users + 1, 5):
                logger.info(f"🔄 Ramping up to {current_users} users...")
                
                # Run concurrent users for 10 seconds
                tasks = []
                for _ in range(current_users):
                    task = asyncio.create_task(self._user_scenario())
                    tasks.append(task)
                
                # Wait for 10 seconds or all tasks to complete
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
                except asyncio.TimeoutError:
                    # Cancel remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                
                # Record metrics
                await self._record_system_metrics(f"ramp_up_{current_users}")
                
                # Small delay before next ramp
                await asyncio.sleep(2)
            
            logger.info("✅ Ramp-up test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ramp-up test failed: {e}")
            return False
    
    async def _run_sustained_load_test(self) -> bool:
        """Run sustained load test"""
        logger.info("📋 Phase 4: Sustained load test")
        
        try:
            duration = 120  # 2 minutes
            concurrent_users = self.config["concurrent_users"]
            
            logger.info(f"🔄 Running {concurrent_users} concurrent users for {duration} seconds...")
            
            start_time = time.time()
            end_time = start_time + duration
            
            # Create user tasks
            user_tasks = []
            for user_id in range(concurrent_users):
                task = asyncio.create_task(self._sustained_user_scenario(end_time, user_id))
                user_tasks.append(task)
            
            # Run until end time
            await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Record final metrics
            await self._record_system_metrics("sustained_load")
            
            logger.info("✅ Sustained load test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sustained load test failed: {e}")
            return False
    
    async def _run_spike_test(self) -> bool:
        """Run spike load test"""
        logger.info("📋 Phase 5: Spike load test")
        
        try:
            spike_users = self.config["max_users"]
            
            logger.info(f"⚡ Running spike test with {spike_users} users...")
            
            # Create spike tasks
            spike_tasks = []
            for _ in range(spike_users):
                task = asyncio.create_task(self._user_scenario())
                spike_tasks.append(task)
            
            # Execute all at once
            start_time = time.time()
            results = await asyncio.gather(*spike_tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            # Count successful vs failed
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            logger.info(f"⚡ Spike test: {successful} successful, {failed} failed in {duration:.2f}s")
            
            # Record metrics
            await self._record_system_metrics("spike_test")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Spike test failed: {e}")
            return False
    
    async def _run_stress_test(self) -> bool:
        """Run stress test beyond normal capacity"""
        logger.info("📋 Phase 6: Stress test")
        
        try:
            stress_users = self.config["max_users"] * 2  # Double the normal load
            
            logger.info(f"💪 Running stress test with {stress_users} users...")
            
            # Run stress test for 30 seconds
            end_time = time.time() + 30
            
            stress_tasks = []
            for user_id in range(stress_users):
                task = asyncio.create_task(self._sustained_user_scenario(end_time, user_id))
                stress_tasks.append(task)
            
            # Run with exceptions handling
            results = await asyncio.gather(*stress_tasks, return_exceptions=True)
            
            # Analyze results
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            logger.info(f"💪 Stress test: {successful} successful, {failed} failed")
            
            # Record metrics
            await self._record_system_metrics("stress_test")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Stress test failed: {e}")
            return False
    
    async def _run_flow_concurrency_test(self) -> bool:
        """Test concurrent flow operations"""
        logger.info("📋 Phase 7: Flow concurrency test")
        
        try:
            concurrent_flows = 20
            
            logger.info(f"🔄 Creating {concurrent_flows} concurrent flows...")
            
            # Create flows concurrently
            flow_creation_tasks = []
            for i in range(concurrent_flows):
                task = asyncio.create_task(self._create_test_flow(f"Concurrent Flow {i}"))
                flow_creation_tasks.append(task)
            
            created_flows = await asyncio.gather(*flow_creation_tasks, return_exceptions=True)
            
            # Count successful flow creations
            successful_flows = [f for f in created_flows if isinstance(f, dict) and "flow_id" in f]
            
            logger.info(f"✅ Created {len(successful_flows)} flows successfully")
            
            # Test concurrent operations on flows
            if successful_flows:
                operation_tasks = []
                for flow in successful_flows[:10]:  # Test on first 10 flows
                    # Pause and resume operations
                    operation_tasks.append(asyncio.create_task(self._test_flow_operations(flow["flow_id"])))
                
                await asyncio.gather(*operation_tasks, return_exceptions=True)
            
            # Record metrics
            self.test_results["metrics"]["concurrent_flows"] = len(successful_flows)
            await self._record_system_metrics("flow_concurrency")
            
            logger.info("✅ Flow concurrency test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Flow concurrency test failed: {e}")
            return False
    
    async def _user_scenario(self) -> None:
        """Simulate a single user performing multiple operations"""
        async with aiohttp.ClientSession() as session:
            for _ in range(random.randint(1, self.config["flow_operations_per_user"])):
                # Select random scenario based on weights
                scenario = self._select_weighted_scenario()
                
                # Execute scenario
                response_time, success, error = await self._execute_scenario(session, scenario)
                
                # Record metrics
                self.test_results["metrics"]["total_requests"] += 1
                if success:
                    self.test_results["metrics"]["successful_requests"] += 1
                else:
                    self.test_results["metrics"]["failed_requests"] += 1
                    self.test_results["errors"].append({
                        "scenario": scenario["name"],
                        "error": error,
                        "timestamp": datetime.now().isoformat()
                    })
                
                self.test_results["metrics"]["response_times"].append(response_time)
                
                # Think time
                think_time = random.uniform(
                    self.config["think_time_min"],
                    self.config["think_time_max"]
                )
                await asyncio.sleep(think_time)
    
    async def _sustained_user_scenario(self, end_time: float, user_id: int) -> None:
        """Simulate sustained user activity until end time"""
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                # Select random scenario
                scenario = self._select_weighted_scenario()
                
                # Execute scenario
                response_time, success, error = await self._execute_scenario(session, scenario)
                
                # Record metrics
                self.test_results["metrics"]["total_requests"] += 1
                if success:
                    self.test_results["metrics"]["successful_requests"] += 1
                else:
                    self.test_results["metrics"]["failed_requests"] += 1
                
                self.test_results["metrics"]["response_times"].append(response_time)
                
                # Short think time for sustained load
                await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async def _execute_scenario(self, session: aiohttp.ClientSession, scenario: Dict[str, Any]) -> Tuple[float, bool, Optional[str]]:
        """Execute a specific test scenario"""
        try:
            start_time = time.time()
            
            # Prepare URL
            url = f"{self.config['backend_url']}{scenario['endpoint']}"
            
            # Handle flow_id placeholder
            if "{flow_id}" in url:
                if self.created_flows:
                    flow_id = random.choice(self.created_flows)
                    url = url.replace("{flow_id}", flow_id)
                else:
                    # Create a flow first
                    flow_result = await self._create_test_flow("Dynamic Flow")
                    if isinstance(flow_result, dict) and "flow_id" in flow_result:
                        flow_id = flow_result["flow_id"]
                        self.created_flows.append(flow_id)
                        url = url.replace("{flow_id}", flow_id)
                    else:
                        return time.time() - start_time, False, "No flow available for operation"
            
            # Execute request
            if scenario["method"] == "GET":
                async with session.get(
                    url,
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
                ) as response:
                    response_time = time.time() - start_time
                    success = response.status < 400
                    error = None if success else f"HTTP {response.status}"
                    return response_time, success, error
            
            elif scenario["method"] == "POST":
                data = scenario.get("data", {})
                async with session.post(
                    url,
                    json=data,
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
                ) as response:
                    response_time = time.time() - start_time
                    success = response.status < 400
                    error = None if success else f"HTTP {response.status}"
                    
                    # If this was a flow creation, store the flow ID
                    if success and scenario["name"] == "create_discovery_flow":
                        try:
                            result = await response.json()
                            if isinstance(result, dict) and "flow_id" in result:
                                self.created_flows.append(result["flow_id"])
                        except:
                            pass
                    
                    return response_time, success, error
            
            else:
                return time.time() - start_time, False, f"Unsupported method: {scenario['method']}"
                
        except asyncio.TimeoutError:
            return self.config["timeout"], False, "Request timeout"
        except Exception as e:
            return time.time() - start_time, False, str(e)
    
    async def _create_test_flow(self, flow_name: str) -> Dict[str, Any]:
        """Create a test flow"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "flow_type": "discovery",
                    "flow_name": flow_name,
                    "configuration": {"test": True, "load_test": True}
                }
                
                async with session.post(
                    f"{self.config['backend_url']}/api/v1/flows",
                    json=data,
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
                ) as response:
                    if response.status < 400:
                        result = await response.json()
                        return result
                    else:
                        return {"error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def _test_flow_operations(self, flow_id: str) -> None:
        """Test various operations on a flow"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test pause
                async with session.post(
                    f"{self.config['backend_url']}/api/v1/flows/{flow_id}/pause",
                    json={"reason": "load_test"},
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ):
                    pass
                
                # Test resume
                await asyncio.sleep(0.5)
                async with session.post(
                    f"{self.config['backend_url']}/api/v1/flows/{flow_id}/resume",
                    json={"resume_context": {"test": True}},
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ):
                    pass
                
                # Test status check
                await asyncio.sleep(0.5)
                async with session.get(
                    f"{self.config['backend_url']}/api/v1/flows/{flow_id}/status",
                    headers=self.session_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ):
                    pass
                    
        except Exception as e:
            logger.debug(f"Flow operation error: {e}")
    
    def _select_weighted_scenario(self) -> Dict[str, Any]:
        """Select a scenario based on weights"""
        total_weight = sum(scenario["weight"] for scenario in self.scenarios)
        rand_value = random.randint(1, total_weight)
        
        current_weight = 0
        for scenario in self.scenarios:
            current_weight += scenario["weight"]
            if rand_value <= current_weight:
                return scenario
        
        return self.scenarios[0]  # Fallback
    
    async def _record_system_metrics(self, phase: str) -> None:
        """Record system performance metrics"""
        try:
            metrics = {
                "phase": phase,
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else []
            }
            
            self.test_results["metrics"]["system_metrics"].append(metrics)
            
        except Exception as e:
            logger.warning(f"Failed to record system metrics: {e}")
    
    async def _generate_load_test_report(self) -> None:
        """Generate comprehensive load test report"""
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Calculate metrics
        total_requests = self.test_results["metrics"]["total_requests"]
        if total_requests > 0:
            error_rate = self.test_results["metrics"]["failed_requests"] / total_requests
            self.test_results["metrics"]["error_rate"] = error_rate
        
        response_times = self.test_results["metrics"]["response_times"]
        if response_times:
            self.test_results["metrics"]["avg_response_time"] = statistics.mean(response_times)
            self.test_results["metrics"]["median_response_time"] = statistics.median(response_times)
            self.test_results["metrics"]["p95_response_time"] = self._percentile(response_times, 95)
            self.test_results["metrics"]["p99_response_time"] = self._percentile(response_times, 99)
            self.test_results["metrics"]["max_response_time"] = max(response_times)
            self.test_results["metrics"]["min_response_time"] = min(response_times)
        
        # Calculate duration and throughput
        start_time = datetime.fromisoformat(self.test_results["start_time"])
        end_time = datetime.fromisoformat(self.test_results["end_time"])
        duration_seconds = (end_time - start_time).total_seconds()
        
        if duration_seconds > 0:
            throughput = total_requests / duration_seconds
            self.test_results["metrics"]["throughput"] = throughput
            self.test_results["metrics"]["duration_seconds"] = duration_seconds
        
        # Save detailed report
        report_file = self.results_path / f"load_test_report_{self.test_id}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 LOAD TESTING RESULTS")
        logger.info("=" * 80)
        logger.info(f"Test ID: {self.test_id}")
        logger.info(f"Duration: {duration_seconds:.2f} seconds")
        logger.info(f"Total Requests: {total_requests}")
        logger.info(f"Successful Requests: {self.test_results['metrics']['successful_requests']}")
        logger.info(f"Failed Requests: {self.test_results['metrics']['failed_requests']}")
        logger.info(f"Error Rate: {error_rate:.2%}")
        logger.info(f"Throughput: {throughput:.2f} requests/second")
        
        if response_times:
            logger.info(f"Avg Response Time: {self.test_results['metrics']['avg_response_time']:.2f}s")
            logger.info(f"95th Percentile: {self.test_results['metrics']['p95_response_time']:.2f}s")
            logger.info(f"99th Percentile: {self.test_results['metrics']['p99_response_time']:.2f}s")
        
        logger.info(f"Concurrent Flows Created: {self.test_results['metrics']['concurrent_flows']}")
        logger.info(f"Report saved: {report_file}")
        
        # Performance evaluation
        logger.info("\n📈 Performance Evaluation:")
        
        if error_rate <= self.config["error_threshold"]:
            logger.info(f"✅ Error Rate: {error_rate:.2%} (≤ {self.config['error_threshold']:.2%})")
        else:
            logger.error(f"❌ Error Rate: {error_rate:.2%} (> {self.config['error_threshold']:.2%})")
        
        if response_times:
            avg_time = self.test_results['metrics']['avg_response_time']
            if avg_time <= self.config["response_time_threshold"]:
                logger.info(f"✅ Avg Response Time: {avg_time:.2f}s (≤ {self.config['response_time_threshold']:.2f}s)")
            else:
                logger.error(f"❌ Avg Response Time: {avg_time:.2f}s (> {self.config['response_time_threshold']:.2f}s)")
        
        if throughput >= 10:  # Minimum 10 requests/second
            logger.info(f"✅ Throughput: {throughput:.2f} req/s (≥ 10 req/s)")
        else:
            logger.warning(f"⚠️  Throughput: {throughput:.2f} req/s (< 10 req/s)")
        
        # Overall assessment
        success = (
            error_rate <= self.config["error_threshold"] and
            (not response_times or self.test_results['metrics']['avg_response_time'] <= self.config["response_time_threshold"])
        )
        
        if success:
            logger.info("\n🎉 LOAD TESTING PASSED!")
            logger.info("✅ System performance meets requirements")
            logger.info("✅ Ready for security vulnerability scan (MFO-097)")
        else:
            logger.error("\n❌ LOAD TESTING FAILED!")
            logger.error("🔧 Performance optimization required")
        
        logger.info("=" * 80)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    async def _handle_load_test_failure(self, error: Exception) -> None:
        """Handle load test failure"""
        self.test_results["execution_error"] = str(error)
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Save failure report
        failure_report_file = self.results_path / f"load_test_failure_{self.test_id}.json"
        with open(failure_report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.error("=" * 80)
        logger.error("❌ LOAD TESTING EXECUTION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {error}")
        logger.error(f"Failure report saved: {failure_report_file}")
        logger.error("=" * 80)


async def main():
    """Main load testing function"""
    load_tester = LoadTestRunner()
    
    try:
        success = await load_tester.run_load_testing()
        
        if success:
            logger.info("✅ Load testing completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Load testing failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Load testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Load testing failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())