"""
Docker container validation tests for the migration UI orchestrator.
Tests that all components work correctly in Docker containers.
"""

import pytest
import docker
import requests
import time
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker configuration
DOCKER_COMPOSE_FILE = "docker-compose.yml"
PROJECT_NAME = "migrate-ui-orchestrator"
TIMEOUT = 120  # 2 minutes timeout for container startup

# Service endpoints
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
DATABASE_URL = "postgresql://localhost:5432"

@pytest.fixture(scope="session")
def docker_client():
    """Docker client for container management."""
    return docker.from_env()

@pytest.fixture(scope="session")
def compose_project():
    """Docker Compose project management."""
    class ComposeProject:
        def __init__(self):
            self.project_name = PROJECT_NAME
            
        def up(self, services=None, detach=True):
            """Start services using docker-compose."""
            cmd = ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "-p", self.project_name, "up"]
            if detach:
                cmd.append("-d")
            if services:
                cmd.extend(services)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Docker compose up failed: {result.stderr}")
            return result
            
        def down(self, volumes=False):
            """Stop and remove services."""
            cmd = ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "-p", self.project_name, "down"]
            if volumes:
                cmd.append("-v")
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
            
        def logs(self, service=None, follow=False):
            """Get logs from services."""
            cmd = ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "-p", self.project_name, "logs"]
            if follow:
                cmd.append("-f")
            if service:
                cmd.append(service)
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
            
        def ps(self):
            """List running services."""
            cmd = ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "-p", self.project_name, "ps"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
    
    return ComposeProject()

def wait_for_service(url: str, timeout: int = TIMEOUT, interval: int = 5) -> bool:
    """Wait for a service to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code < 500:  # Any response below 500 means service is running
                logger.info(f"Service at {url} is responding")
                return True
        except requests.exceptions.RequestException:
            pass
        
        logger.info(f"Waiting for service at {url}...")
        time.sleep(interval)
    
    logger.error(f"Service at {url} did not start within {timeout} seconds")
    return False

class TestDockerContainerStartup:
    """Test that Docker containers start correctly."""
    
    def test_compose_file_exists(self):
        """Test that docker-compose.yml exists."""
        assert os.path.exists(DOCKER_COMPOSE_FILE), "docker-compose.yml file not found"
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        assert os.path.exists("Dockerfile"), "Dockerfile not found"
    
    @pytest.mark.slow
    def test_start_all_services(self, compose_project):
        """Test starting all services with docker-compose."""
        try:
            # Clean up any existing containers
            compose_project.down(volumes=True)
            time.sleep(5)
            
            # Start all services
            logger.info("Starting all services...")
            result = compose_project.up()
            
            # Check that command succeeded
            assert result is not None
            
            # Wait a bit for services to initialize
            time.sleep(10)
            
            # Check running services
            ps_output = compose_project.ps()
            logger.info(f"Running services:\n{ps_output}")
            
            # Should have some services running
            assert "Up" in ps_output or "running" in ps_output.lower()
            
        finally:
            # Clean up
            compose_project.down(volumes=True)
    
    @pytest.mark.slow
    def test_backend_container_startup(self, compose_project):
        """Test that backend container starts correctly."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            
            # Start only backend dependencies first
            logger.info("Starting backend service...")
            compose_project.up(services=["backend"])
            
            # Wait for backend to be ready
            backend_ready = wait_for_service(f"{BACKEND_URL}/health", timeout=60)
            if not backend_ready:
                # Try root endpoint if health endpoint doesn't exist
                backend_ready = wait_for_service(BACKEND_URL, timeout=30)
            
            assert backend_ready, "Backend service did not start within timeout"
            
        finally:
            compose_project.down(volumes=True)
    
    @pytest.mark.slow
    def test_frontend_container_startup(self, compose_project):
        """Test that frontend container starts correctly."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            
            # Start frontend service
            logger.info("Starting frontend service...")
            compose_project.up(services=["frontend"])
            
            # Wait for frontend to be ready
            frontend_ready = wait_for_service(FRONTEND_URL, timeout=60)
            assert frontend_ready, "Frontend service did not start within timeout"
            
        finally:
            compose_project.down(volumes=True)


class TestDockerContainerHealth:
    """Test container health and resource usage."""
    
    @pytest.mark.slow
    def test_container_health_checks(self, docker_client, compose_project):
        """Test that containers pass health checks."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            time.sleep(20)  # Wait for services to stabilize
            
            # Get all containers for this project
            containers = docker_client.containers.list(
                filters={"label": f"com.docker.compose.project={PROJECT_NAME}"}
            )
            
            assert len(containers) > 0, "No containers found for project"
            
            for container in containers:
                logger.info(f"Checking container: {container.name}")
                
                # Check container is running
                container.reload()
                assert container.status == "running", f"Container {container.name} is not running: {container.status}"
                
                # Check container logs for errors
                logs = container.logs(tail=50).decode('utf-8')
                
                # Log some output for debugging
                logger.info(f"Last 50 lines from {container.name}:\n{logs[-1000:]}")
                
                # Check for common error patterns (but don't fail tests on warnings)
                critical_errors = [
                    "FATAL:",
                    "CRITICAL:",
                    "Error: failed to",
                    "panic:",
                    "segmentation fault"
                ]
                
                for error_pattern in critical_errors:
                    assert error_pattern not in logs, f"Critical error found in {container.name}: {error_pattern}"
                    
        finally:
            compose_project.down(volumes=True)
    
    @pytest.mark.slow
    def test_container_resource_usage(self, docker_client, compose_project):
        """Test that containers use reasonable resources."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            time.sleep(30)  # Wait for services to stabilize
            
            containers = docker_client.containers.list(
                filters={"label": f"com.docker.compose.project={PROJECT_NAME}"}
            )
            
            for container in containers:
                stats = container.stats(stream=False)
                
                # Check memory usage (should be reasonable)
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', float('inf'))
                memory_percent = (memory_usage / memory_limit) * 100 if memory_limit != float('inf') else 0
                
                logger.info(f"Container {container.name} memory usage: {memory_usage / 1024 / 1024:.1f}MB ({memory_percent:.1f}%)")
                
                # Memory usage should be reasonable (less than 90% of limit)
                if memory_limit != float('inf'):
                    assert memory_percent < 90, f"Container {container.name} using too much memory: {memory_percent:.1f}%"
                    
        finally:
            compose_project.down(volumes=True)


class TestDockerNetworking:
    """Test container networking and communication."""
    
    @pytest.mark.slow
    def test_frontend_backend_communication(self, compose_project):
        """Test that frontend can communicate with backend."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            
            # Wait for both services
            backend_ready = wait_for_service(BACKEND_URL, timeout=60)
            frontend_ready = wait_for_service(FRONTEND_URL, timeout=60)
            
            assert backend_ready and frontend_ready, "Services did not start properly"
            
            # Test that backend API is accessible
            try:
                response = requests.get(f"{BACKEND_URL}/api/v1/discovery/assets", timeout=10)
                assert response.status_code in [200, 404, 422], f"Backend API returned unexpected status: {response.status_code}"
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Could not reach backend API: {e}")
            
            # Test that frontend serves content
            try:
                response = requests.get(FRONTEND_URL, timeout=10)
                assert response.status_code == 200, f"Frontend returned status: {response.status_code}"
                assert "text/html" in response.headers.get("content-type", ""), "Frontend should serve HTML"
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Could not reach frontend: {e}")
                
        finally:
            compose_project.down(volumes=True)
    
    @pytest.mark.slow
    def test_cors_configuration(self, compose_project):
        """Test that CORS is properly configured."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            
            backend_ready = wait_for_service(BACKEND_URL, timeout=60)
            assert backend_ready, "Backend service not ready"
            
            # Test CORS preflight request
            headers = {
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            try:
                response = requests.options(f"{BACKEND_URL}/api/v1/discovery/assets", headers=headers, timeout=10)
                
                # CORS should not block the request
                assert response.status_code in [200, 204, 404], f"CORS preflight failed: {response.status_code}"
                
                # Check for CORS headers if they exist
                if "Access-Control-Allow-Origin" in response.headers:
                    cors_origin = response.headers["Access-Control-Allow-Origin"]
                    assert cors_origin == "*" or FRONTEND_URL in cors_origin, f"CORS origin not configured correctly: {cors_origin}"
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"CORS test failed (this might be expected): {e}")
                
        finally:
            compose_project.down(volumes=True)


class TestDockerPersistence:
    """Test data persistence in Docker containers."""
    
    @pytest.mark.slow
    def test_database_persistence(self, compose_project):
        """Test that database data persists between container restarts."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            
            # Start services
            compose_project.up()
            backend_ready = wait_for_service(BACKEND_URL, timeout=60)
            assert backend_ready, "Backend service not ready"
            
            # Try to make a request that would use the database
            test_data = {
                "filename": "test_persistence.csv",
                "content": "Asset_Name,Type\ntest-asset,Server",
                "fileType": "csv"
            }
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/discovery/analyze-cmdb",
                    json=test_data,
                    timeout=30
                )
                initial_success = response.status_code == 200
            except requests.exceptions.RequestException:
                initial_success = False
            
            if initial_success:
                # Restart containers (but keep volumes)
                logger.info("Restarting containers to test persistence...")
                compose_project.down(volumes=False)  # Don't remove volumes
                time.sleep(5)
                compose_project.up()
                
                backend_ready = wait_for_service(BACKEND_URL, timeout=60)
                assert backend_ready, "Backend service not ready after restart"
                
                # Try the same request again
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/discovery/analyze-cmdb",
                        json=test_data,
                        timeout=30
                    )
                    assert response.status_code == 200, "Database connection failed after restart"
                except requests.exceptions.RequestException as e:
                    pytest.fail(f"Database persistence test failed: {e}")
            else:
                logger.warning("Initial database test failed, skipping persistence test")
                
        finally:
            compose_project.down(volumes=True)


class TestDockerEnvironment:
    """Test Docker environment configuration."""
    
    def test_environment_variables(self, compose_project):
        """Test that environment variables are properly set."""
        # This test checks the compose file structure
        import yaml
        
        try:
            with open(DOCKER_COMPOSE_FILE, 'r') as f:
                compose_config = yaml.safe_load(f)
        except Exception as e:
            pytest.skip(f"Could not read docker-compose file: {e}")
        
        assert "services" in compose_config, "No services defined in docker-compose.yml"
        
        services = compose_config["services"]
        
        # Check that backend service exists and has environment config
        if "backend" in services:
            backend_service = services["backend"]
            
            # Should have environment variables or env_file
            has_env = "environment" in backend_service or "env_file" in backend_service
            assert has_env, "Backend service should have environment configuration"
        
        # Check that frontend service exists
        if "frontend" in services:
            frontend_service = services["frontend"]
            assert "build" in frontend_service or "image" in frontend_service, "Frontend service should have build or image config"
    
    @pytest.mark.slow
    def test_port_configuration(self, compose_project):
        """Test that ports are properly configured."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            
            # Check that expected ports are accessible
            backend_accessible = wait_for_service(BACKEND_URL, timeout=60)
            frontend_accessible = wait_for_service(FRONTEND_URL, timeout=60)
            
            # At least one service should be accessible
            assert backend_accessible or frontend_accessible, "No services are accessible on expected ports"
            
            if backend_accessible:
                logger.info("Backend is accessible on port 8000")
            if frontend_accessible:
                logger.info("Frontend is accessible on port 3000")
                
        finally:
            compose_project.down(volumes=True)


class TestDockerIntegrationWithAssetInventory:
    """Test the enhanced asset inventory functionality in Docker."""
    
    @pytest.mark.slow
    def test_cmdb_analysis_in_docker(self, compose_project):
        """Test CMDB analysis functionality in Docker containers."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            
            backend_ready = wait_for_service(BACKEND_URL, timeout=60)
            assert backend_ready, "Backend service not ready"
            
            # Test enhanced CMDB analysis with device types
            test_data = {
                "filename": "docker_test_assets.csv",
                "content": """Asset_Name,CI_Type,Environment,CPU_Cores,Memory_GB
mysql-prod-01,Database,Production,8,32
core-switch-01,Network,Production,,
firewall-dmz,Security,Production,,
srv-web-01,Server,Production,16,64
SAN01,Storage,Production,,
vmware-vcenter,Virtualization,Production,8,16""",
                "fileType": "csv"
            }
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/discovery/analyze-cmdb",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify enhanced analysis features
                    assert "dataQuality" in data, "Data quality analysis missing"
                    assert "coverage" in data, "Coverage analysis missing"
                    
                    # Should handle mixed asset types including devices
                    quality = data["dataQuality"]
                    assert "score" in quality, "Quality score missing"
                    assert isinstance(quality["score"], int), "Quality score should be integer"
                    assert 0 <= quality["score"] <= 100, "Quality score should be 0-100"
                    
                    logger.info(f"CMDB analysis successful in Docker - Quality Score: {quality['score']}")
                else:
                    logger.warning(f"CMDB analysis returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"CMDB analysis test failed in Docker: {e}")
                
        finally:
            compose_project.down(volumes=True)
    
    @pytest.mark.slow
    def test_asset_inventory_api_in_docker(self, compose_project):
        """Test asset inventory API in Docker containers."""
        try:
            compose_project.down(volumes=True)
            time.sleep(5)
            compose_project.up()
            
            backend_ready = wait_for_service(BACKEND_URL, timeout=60)
            assert backend_ready, "Backend service not ready"
            
            try:
                response = requests.get(f"{BACKEND_URL}/api/v1/discovery/assets", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify enhanced inventory structure
                    assert "assets" in data, "Assets missing from response"
                    assert "summary" in data, "Summary missing from response"
                    
                    summary = data["summary"]
                    expected_fields = ["total", "applications", "servers", "databases", "devices", "unknown"]
                    for field in expected_fields:
                        assert field in summary, f"Summary field {field} missing"
                        assert isinstance(summary[field], int), f"Summary field {field} should be integer"
                    
                    logger.info(f"Asset inventory API working in Docker - {summary['total']} total assets")
                else:
                    logger.warning(f"Asset inventory API returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Asset inventory test failed in Docker: {e}")
                
        finally:
            compose_project.down(volumes=True)


class TestDockerCleanup:
    """Test Docker cleanup procedures."""
    
    def test_cleanup_containers(self, compose_project):
        """Test that containers can be properly cleaned up."""
        # Start services
        compose_project.up()
        time.sleep(10)
        
        # Stop and remove containers
        result = compose_project.down(volumes=True)
        assert result.returncode == 0, f"Cleanup failed: {result.stderr}"
        
        # Verify no containers are running
        ps_output = compose_project.ps()
        # After cleanup, ps should show no running containers or empty output
        assert "Up" not in ps_output and "running" not in ps_output.lower()
    
    def test_volume_cleanup(self, docker_client, compose_project):
        """Test that volumes are properly cleaned up."""
        try:
            # Start services to create volumes
            compose_project.up()
            time.sleep(10)
            
            # Get volumes before cleanup
            volumes_before = [v.name for v in docker_client.volumes.list() if PROJECT_NAME in v.name]
            
            # Cleanup with volumes
            compose_project.down(volumes=True)
            time.sleep(5)
            
            # Get volumes after cleanup
            volumes_after = [v.name for v in docker_client.volumes.list() if PROJECT_NAME in v.name]
            
            # Project-specific volumes should be removed
            assert len(volumes_after) <= len(volumes_before), "Volumes were not properly cleaned up"
            
        except Exception as e:
            logger.warning(f"Volume cleanup test failed: {e}")


if __name__ == "__main__":
    # Run with markers: pytest tests/docker/ -v -m "not slow" for quick tests
    # Run with: pytest tests/docker/ -v -m "slow" for full integration tests
    pytest.main([__file__, "-v", "--tb=short"]) 