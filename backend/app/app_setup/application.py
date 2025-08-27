import logging
import os
from fastapi import FastAPI


def create_app():  # factory to assemble app
    # Configure logging
    try:
        from app.core.rich_config import configure_rich_for_backend

        configure_rich_for_backend()
    except Exception:
        pass

    try:
        from app.core.logging import configure_logging, get_logger

        env = os.getenv("ENVIRONMENT", "production")
        log_format = "json" if env == "production" else "text"
        configure_logging(level="INFO", format=log_format, enable_security_filter=True)
        logger = get_logger(__name__)
        logger.info("✅ Structured logging configured", extra={"environment": env})
    except Exception:
        logging.basicConfig(level=logging.INFO)

    # Import settings
    try:
        from app.core.config import settings
    except Exception:

        class MinimalSettings:
            FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8081")
            ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
            DEBUG = os.getenv("DEBUG", "False").lower() == "true"
            ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8081")

            @property
            def allowed_origins_list(self):
                return (
                    self.ALLOWED_ORIGINS.split(",")
                    if isinstance(self.ALLOWED_ORIGINS, str)
                    else self.ALLOWED_ORIGINS
                )

        settings = MinimalSettings()

    # App
    from app.app_setup.lifecycle import get_lifespan

    app = FastAPI(
        title="AI Modernize Migration Platform API",
        description="AI-powered cloud migration management platform",
        version=os.getenv("API_VERSION", "0.2.0"),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=get_lifespan(),
    )

    # Middleware and CORS
    from app.app_setup.middleware import add_middlewares
    from app.app_setup.cors import add_cors

    add_middlewares(app, settings)
    add_cors(app, settings)

    # Routes
    from app.app_setup.routes import include_api_routes, add_debug_routes

    include_api_routes(app)
    add_debug_routes(app)

    return app
