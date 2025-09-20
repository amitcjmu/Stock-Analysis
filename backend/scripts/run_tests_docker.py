#!/usr/bin/env python3
"""
Test runner that ensures all tests use Docker containers instead of localhost daemons.
This script manages Docker container lifecycle for testing.
"""

import os
import sys
import subprocess
import time
import logging
import argparse
import signal
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DockerTestRunner:
    """Manages Docker containers for testing and runs test suites."""

    def __init__(
        self,
        project_name: str = "migrate-ui-orchestrator-test",
        compose_file_override: Optional[str] = None,
        no_build: bool = False,
        skip_start: bool = False,
    ):
        self.project_name = project_name
        self.compose_file = compose_file_override or self._detect_compose_file()
        self.compose_cmd = self._detect_compose_command()
        self.containers_started = False
        self.no_build = no_build
        self.skip_start = skip_start

    def _detect_compose_command(self) -> List[str]:
        """Detect whether to use 'docker compose' (v2) or 'docker-compose' (v1)."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return ["docker", "compose"]
        except Exception:
            pass
        return ["docker-compose"]

    def _detect_compose_file(self) -> str:
        """Detect compose file location, prefer config/docker/docker-compose.yml when available."""
        env_compose = os.environ.get("COMPOSE_FILE")
        if env_compose and os.path.exists(env_compose):
            logger.info(f"Using compose file from COMPOSE_FILE: {env_compose}")
            return env_compose

        candidates = [
            os.path.join("config", "docker", "docker-compose.yml"),
            os.path.join("config", "docker", "docker-compose.test.yml"),
            "docker-compose.yml",
        ]
        for path in candidates:
            if os.path.exists(path):
                logger.info(f"Using compose file: {path}")
                return path
        # Fallback even if not present (let compose error clearly)
        logger.warning("No compose file detected; defaulting to docker-compose.yml")
        return "docker-compose.yml"

    def cleanup_existing_containers(self):
        """Clean up any existing test containers."""
        logger.info("Cleaning up existing containers...")
        try:
            result = subprocess.run(
                self.compose_cmd
                + [
                    "-f",
                    self.compose_file,
                    "-p",
                    self.project_name,
                    "down",
                    "-v",
                    "--remove-orphans",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                logger.info("Existing containers cleaned up successfully")
            else:
                logger.warning(f"Cleanup warning: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Cleanup timed out")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def start_containers(self, services: Optional[List[str]] = None):
        """Start Docker containers for testing."""
        logger.info("Starting Docker containers for testing...")

        try:
            cmd = self.compose_cmd + [
                "-f",
                self.compose_file,
                "-p",
                self.project_name,
                "up",
                "-d",
            ]
            if not self.no_build:
                cmd.append("--build")

            if services:
                cmd.extend(services)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"Failed to start containers: {result.stderr}")
                return False

            logger.info("Containers started successfully")
            self.containers_started = True

            # Wait for services to be ready
            self.wait_for_services()
            return True

        except subprocess.TimeoutExpired:
            logger.error("Container startup timed out")
            return False
        except Exception as e:
            logger.error(f"Container startup error: {e}")
            return False

    def wait_for_services(self, timeout: int = 120):
        """Wait for services to become ready."""
        logger.info("Waiting for services to become ready...")

        import requests

        services = [
            ("Backend", "http://localhost:8000"),
            ("Frontend", "http://localhost:8081"),
        ]

        start_time = time.time()
        ready_services = set()

        while time.time() - start_time < timeout:
            for service_name, url in services:
                if service_name in ready_services:
                    continue

                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code < 500:
                        logger.info(f"{service_name} is ready")
                        ready_services.add(service_name)
                except requests.exceptions.RequestException:
                    pass

            if len(ready_services) == len(services):
                logger.info("All services are ready")
                return True

            time.sleep(5)

        logger.warning(
            f"Only {len(ready_services)}/{len(services)} services became ready"
        )
        return len(ready_services) > 0  # Proceed if at least one service is ready

    def is_backend_running(self) -> bool:
        """Check if migration_backend container is running."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=migration_backend",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "migration_backend" in result.stdout.strip()
        except Exception:
            return False

    def stop_containers(self):
        """Stop Docker containers."""
        if not self.containers_started:
            return

        logger.info("Stopping Docker containers...")
        try:
            result = subprocess.run(
                self.compose_cmd
                + ["-f", self.compose_file, "-p", self.project_name, "down", "-v"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                logger.info("Containers stopped successfully")
            else:
                logger.warning(f"Stop warning: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("Container stop timed out")
        except Exception as e:
            logger.error(f"Container stop error: {e}")
        finally:
            self.containers_started = False

    def run_backend_tests(self) -> int:
        """Run backend Python tests inside the backend container with auto-detected test root."""
        logger.info("Running backend tests (inside container)...")

        cmd = [
            "docker",
            "exec",
            "-T",
            "migration_backend",
            "--",
            "bash",
            "-lc",
            "set -e; "
            "if [ -d backend/tests ]; then TEST_DIR=backend/tests; "
            "elif [ -d tests/backend ]; then TEST_DIR=tests/backend; "
            "elif [ -d tests ]; then TEST_DIR=tests; "
            "else echo 'No tests directory found (checked backend/tests, tests/backend, tests)' >&2; exit 2; fi; "
            'python -m pytest "$TEST_DIR" -v --tb=short -x --disable-warnings',
        ]

        try:
            result = subprocess.run(cmd, timeout=900)
            return result.returncode
        except subprocess.TimeoutExpired:
            logger.error("Backend tests timed out")
            return 1
        except Exception as e:
            logger.error(f"Backend test error: {e}")
            return 1

    def run_frontend_tests(self) -> int:
        """Run frontend JavaScript tests."""
        logger.info("Running frontend tests...")

        env = os.environ.copy()
        env.update(
            {
                "DOCKER_API_BASE": "http://localhost:8000",
                "DOCKER_FRONTEND_BASE": "http://localhost:8081",
            }
        )

        # Check if npm is available
        try:
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("npm not found. Please install Node.js and npm.")
            return 1

        # Install dependencies if needed
        if not os.path.exists("node_modules"):
            logger.info("Installing npm dependencies...")
            result = subprocess.run(["npm", "install"], timeout=300)
            if result.returncode != 0:
                logger.error("Failed to install npm dependencies")
                return 1

        # Run tests
        cmd = ["npm", "test", "--", "--run"]  # Use --run to avoid watch mode

        try:
            result = subprocess.run(cmd, env=env, timeout=300)  # 5 minute timeout
            return result.returncode
        except subprocess.TimeoutExpired:
            logger.error("Frontend tests timed out")
            return 1
        except Exception as e:
            logger.error(f"Frontend test error: {e}")
            return 1

    def run_docker_tests(self) -> int:
        """Run Docker integration tests."""
        logger.info("Running Docker integration tests...")

        env = os.environ.copy()
        env.update(
            {
                "DOCKER_API_BASE": "http://localhost:8000",
                "DOCKER_FRONTEND_BASE": "http://localhost:8081",
                "PYTHONPATH": "tests/docker",
            }
        )

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/docker/",
            "-v",
            "--tb=short",
            "-m",
            "not slow",  # Run only quick tests by default
            "--disable-warnings",
        ]

        try:
            result = subprocess.run(cmd, env=env, timeout=300)  # 5 minute timeout
            return result.returncode
        except subprocess.TimeoutExpired:
            logger.error("Docker tests timed out")
            return 1
        except Exception as e:
            logger.error(f"Docker test error: {e}")
            return 1

    def run_all_tests(self, test_suites: List[str]) -> int:
        """Run all specified test suites."""
        results = {}

        if "backend" in test_suites:
            results["backend"] = self.run_backend_tests()

        if "frontend" in test_suites:
            results["frontend"] = self.run_frontend_tests()

        if "docker" in test_suites:
            results["docker"] = self.run_docker_tests()

        # Report results
        logger.info("\n" + "=" * 50)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 50)

        all_passed = True
        for suite, returncode in results.items():
            status = "PASSED" if returncode == 0 else "FAILED"
            logger.info(f"{suite.upper()} tests: {status}")
            if returncode != 0:
                all_passed = False

        if all_passed:
            logger.info("All test suites passed!")
            return 0
        else:
            logger.error("Some test suites failed!")
            return 1


def signal_handler(signum, frame, runner: DockerTestRunner):
    """Handle interrupt signals to clean up containers."""
    logger.info("Received interrupt signal, cleaning up...")
    runner.stop_containers()
    sys.exit(1)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests with Docker containers")
    parser.add_argument(
        "--suites",
        "-s",
        nargs="+",
        choices=["backend", "frontend", "docker", "all"],
        default=["all"],
        help="Test suites to run",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up containers after tests",
    )
    parser.add_argument(
        "--services", nargs="+", help="Specific services to start (default: all)"
    )
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="Keep containers running after tests for manual inspection",
    )
    parser.add_argument("--compose-file", help="Path to docker-compose file to use")
    parser.add_argument(
        "--no-build", action="store_true", help="Do not pass --build to compose up"
    )
    parser.add_argument(
        "--skip-start",
        action="store_true",
        help="Skip container startup if already running",
    )

    args = parser.parse_args()

    # Expand "all" to all test suites
    if "all" in args.suites:
        test_suites = ["backend", "frontend", "docker"]
    else:
        test_suites = args.suites

    runner = DockerTestRunner(
        compose_file_override=args.compose_file,
        no_build=args.no_build,
        skip_start=args.skip_start,
    )

    # Set up signal handlers for graceful cleanup
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, runner))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, runner))

    try:
        # Optionally skip start when backend already running
        if runner.skip_start and runner.is_backend_running():
            logger.info("Backend already running; skipping cleanup/start")
        else:
            # Ensure we start with clean state
            runner.cleanup_existing_containers()

            # Start containers
            if not runner.start_containers(services=args.services):
                logger.error("Failed to start containers")
                logger.error(
                    "TIP: If build failures occur, try --no-build or start containers manually "
                    "with required env vars, then re-run with --skip-start"
                )
                return 1

        # Run tests
        exit_code = runner.run_all_tests(test_suites)

        if args.keep_running:
            logger.info("Keeping containers running for manual inspection...")
            logger.info(
                "Use 'docker-compose -p migrate-ui-orchestrator-test down -v' to clean up"
            )
        else:
            # Clean up
            if not args.no_cleanup:
                runner.stop_containers()

        return exit_code

    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        runner.stop_containers()
        return 1
    except Exception as e:
        logger.error(f"Test run failed: {e}")
        runner.stop_containers()
        return 1


if __name__ == "__main__":
    sys.exit(main())
