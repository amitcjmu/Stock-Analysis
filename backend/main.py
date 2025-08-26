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

    Returns:
        str: Host address for uvicorn binding
    """
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # Check if we're in a container/production environment
    is_containerized = bool(
        os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RAILWAY_PROJECT_NAME")
        or os.getenv("VERCEL_ENV")
        or "railway.app" in os.getenv("DATABASE_URL", "")
        or environment in ["production", "prod"]
    )

    if is_containerized:
        # Safe to bind to all interfaces in container/production environments
        return "0.0.0.0"  # nosec B104
    else:
        # Local development - restrict to localhost for security
        return "127.0.0.1"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = get_host_for_environment()
    environment = os.getenv("ENVIRONMENT", "production").lower()

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=environment == "development",
    )
