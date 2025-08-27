"""
Slim application entrypoint delegating setup to app_setup modules.
"""

import os
import uvicorn

from app.app_setup.application import create_app

# ASGI app
app = create_app()
application = app


def get_host_for_environment() -> str:
    """
    Determine the appropriate host binding based on environment.

    Security considerations:
    - 127.0.0.1: Local development only - restricts access to local machine
    - 0.0.0.0: Production/container environments only - allows external access

    SECURITY FIX: Enhanced container detection to prevent accidental exposure
    of development machines when ENVIRONMENT=production is set locally.

    Returns:
        str: Host address for uvicorn binding
    """
    import logging

    logger = logging.getLogger(__name__)
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # SECURITY FIX: More explicit container detection
    # Check for explicit container environment indicators
    container_indicators = [
        os.getenv("RAILWAY_ENVIRONMENT"),
        os.getenv("RAILWAY_PROJECT_NAME"),
        os.getenv("VERCEL_ENV"),
        os.getenv("KUBERNETES_SERVICE_HOST"),  # Kubernetes
        os.getenv("DOCKER_CONTAINER"),  # Docker indicator
        os.path.exists("/.dockerenv"),  # Docker container file
        os.path.exists("/proc/1/cgroup")
        and "docker" in open("/proc/1/cgroup", "r").read(),
    ]

    # Check database URL for hosted services
    database_url = os.getenv("DATABASE_URL", "")
    hosted_db_indicators = [
        "railway.app" in database_url,
        "amazonaws.com" in database_url,
        "azure.com" in database_url,
        "googleusercontent.com" in database_url,
    ]

    # SECURITY FIX: Require explicit permission for 0.0.0.0 binding
    explicit_bind_all = os.getenv("BIND_ALL_INTERFACES", "").lower() in [
        "true",
        "1",
        "yes",
    ]

    # Determine if we're in a legitimate container/production environment
    is_containerized = (
        any(container_indicators)
        or any(hosted_db_indicators)
        or bool(os.getenv("PORT"))  # Common in hosted environments
    )

    # Log security decision for audit trail
    if environment in ["production", "prod"] and not is_containerized:
        if explicit_bind_all:
            logger.warning(
                "SECURITY: BIND_ALL_INTERFACES=true overrides container detection. "
                "Binding to 0.0.0.0 on local machine."
            )
            return "0.0.0.0"  # nosec B104 - explicitly requested
        else:
            logger.warning(
                "SECURITY: ENVIRONMENT=production detected but no container indicators found. "
                "Binding to 127.0.0.1 for safety. Set BIND_ALL_INTERFACES=true to override."
            )
            return "127.0.0.1"

    if is_containerized or explicit_bind_all:
        logger.info(
            f"Container/hosted environment detected. Binding to 0.0.0.0 (env: {environment})"
        )
        return "0.0.0.0"  # nosec B104
    else:
        logger.info(
            f"Local development environment detected. Binding to 127.0.0.1 (env: {environment})"
        )
        return "127.0.0.1"


if __name__ == "__main__":
    import logging

    # Set up basic logging for security audit trail
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    port = int(os.getenv("PORT", 8000))
    host = get_host_for_environment()
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # SECURITY AUDIT: Log binding configuration
    logger.info(f"Starting server on {host}:{port} (environment: {environment})")
    if host == "0.0.0.0":  # nosec B104 - validated container environment
        logger.info(
            "SECURITY: Server will accept connections from any network interface"
        )
    else:
        logger.info("SECURITY: Server restricted to local connections only")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=environment == "development",
    )
