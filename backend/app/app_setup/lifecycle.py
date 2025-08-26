"""
Application lifecycle setup extracted from main module to reduce file size.
"""

import logging
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI


def get_lifespan():  # noqa: C901
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger = logging.getLogger(__name__)
        logger.info("🚀 Application starting up...")

        # Initialize RBAC system
        try:
            from app.api.v1.auth.rbac import initialize_rbac_system

            await initialize_rbac_system()
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning("RBAC initialization warning: %s", e)

        # Initialize Master Flow Orchestrator configurations
        try:
            from app.core.flow_initialization import initialize_flows_on_startup

            logging.getLogger(__name__).info(
                "🔄 Initializing Master Flow Orchestrator configurations..."
            )
            flow_init_results = initialize_flows_on_startup()
            if flow_init_results.get("success", False):
                logging.getLogger(__name__).info(
                    "✅ Master Flow Orchestrator initialized successfully"
                )
            else:
                errors = flow_init_results.get("initialization", {}).get("errors", [])
                logging.getLogger(__name__).warning(
                    "Flow initialization completed with issues: %s", errors
                )
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "Flow initialization warning: %s", e, exc_info=True
            )

        # Initialize LLM rate limiting to prevent 429 errors
        try:
            logging.getLogger(__name__).info("🔄 Initializing LLM rate limiting...")
            os.environ["ENABLE_LLM_RATE_LIMITING"] = "true"
            logging.getLogger(__name__).info(
                "✅ Full CrewAI functionality enabled - no bypasses"
            )

            from app.services.simple_rate_limiter import simple_rate_limiter

            logging.getLogger(__name__).info(
                "✅ LLM rate limiting enabled: %s requests/minute",
                simple_rate_limiter.max_tokens,
            )
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "LLM rate limiting initialization warning: %s", e
            )

        # Test database connection and init
        try:
            from app.core.database import db_manager, AsyncSessionLocal
            from app.core.database_initialization import initialize_database

            logging.getLogger(__name__).info("🔧 Testing database connection...")
            health_check_result = await db_manager.health_check()
            if health_check_result:
                logging.getLogger(__name__).info(
                    "✅✅✅ Database connection test successful."
                )
                if os.getenv("SKIP_DB_INIT", "false").lower() != "true":
                    try:
                        logging.getLogger(__name__).info(
                            "📦 Initializing database with required data..."
                        )
                        async with AsyncSessionLocal() as db:
                            await initialize_database(db)
                        logging.getLogger(__name__).info(
                            "✅ Database initialization completed"
                        )
                    except Exception as e:  # pragma: no cover
                        logging.getLogger(__name__).warning(
                            "Database initialization warning: %s", e
                        )
            else:  # pragma: no cover
                logging.getLogger(__name__).warning(
                    "⚠️⚠️⚠️ Database connection test failed, but continuing..."
                )
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "⚠️⚠️⚠️ Database connection test failed: %s", e, exc_info=True
            )

        # Start flow health monitor
        try:
            logging.getLogger(__name__).info("🔄 Starting flow health monitor...")
            from app.services.flow_health_monitor import flow_health_monitor

            await flow_health_monitor.start()
            logging.getLogger(__name__).info(
                "✅ Flow health monitor started successfully"
            )
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "Flow health monitor initialization warning: %s", e
            )

        yield

        # Shutdown logic
        logging.getLogger(__name__).info("🔄 Application shutting down...")
        try:
            from app.services.flow_health_monitor import flow_health_monitor

            await flow_health_monitor.stop()
            logging.getLogger(__name__).info("✅ Flow health monitor stopped")
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "Error stopping flow health monitor: %s", e
            )

        logging.getLogger(__name__).info("✅ Shutdown logic completed.")

    return lifespan
