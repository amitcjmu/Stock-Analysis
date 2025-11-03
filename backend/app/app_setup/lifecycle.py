"""
Application lifecycle setup extracted from main module to reduce file size.
"""

import logging
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.agent_monitoring_startup import (
    initialize_agent_monitoring,
    shutdown_agent_monitoring,
)


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

        # Initialize FlowTypeConfig registry (ADR-027)
        try:
            from app.services.flow_type_registry_helpers import (
                initialize_default_flow_configs,
            )

            logging.getLogger(__name__).info(
                "🔄 Initializing FlowTypeConfig registry..."
            )
            initialize_default_flow_configs()
            logging.getLogger(__name__).info("✅ FlowTypeConfig registry initialized")
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "FlowTypeConfig initialization warning: %s", e
            )

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

        # Validate critical attributes consistency
        try:
            logging.getLogger(__name__).info(
                "🔄 Validating critical attributes consistency..."
            )
            from app.services.collection.critical_attributes import (
                validate_attribute_consistency,
            )

            validate_attribute_consistency()
            logging.getLogger(__name__).info("✅ Critical attributes validation passed")
        except Exception as e:
            # This is a critical error that should halt startup
            logging.getLogger(__name__).error(
                f"❌ Critical attributes validation failed: {e}", exc_info=True
            )
            raise  # Re-raise to prevent startup with invalid configuration

        # Initialize agent monitoring services
        try:
            logging.getLogger(__name__).info("🔧 Initializing agent monitoring...")
            initialize_agent_monitoring()
            logging.getLogger(__name__).info(
                "✅ Agent monitoring initialized successfully"
            )
        except Exception as e:  # pragma: no cover
            # Don't fail startup if monitoring fails - log and continue
            logging.getLogger(__name__).error(
                f"⚠️ Failed to initialize agent monitoring: {e}", exc_info=True
            )

        # Log feature flags configuration
        try:
            logging.getLogger(__name__).info(
                "🔄 Loading feature flags configuration..."
            )
            from app.core.feature_flags import log_feature_flags

            log_feature_flags()
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning("Feature flags logging warning: %s", e)

        # CrewAI OpenAI Compatibility Shim (gated by feature flag)
        # Some CrewAI versions fall back to OPENAI_API_KEY env var even when using DeepInfra
        # This shim sets OPENAI_API_KEY from DEEPINFRA_API_KEY ONLY when:
        # 1. CREWAI_OPENAI_COMPAT_SHIM=true (explicit opt-in)
        # 2. No existing OPENAI_API_KEY (doesn't shadow explicit OpenAI config)
        # Per GPT5 review: Prevents conflating providers and shadowing explicit configs
        try:
            enable_shim = (
                os.getenv("CREWAI_OPENAI_COMPAT_SHIM", "false").lower() == "true"
            )
            if enable_shim:
                deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
                existing_openai_key = os.getenv("OPENAI_API_KEY")

                if deepinfra_key and not existing_openai_key:
                    os.environ["OPENAI_API_KEY"] = deepinfra_key
                    os.environ["OPENAI_API_BASE"] = (
                        "https://api.deepinfra.com/v1/openai"
                    )
                    logging.getLogger(__name__).info(
                        "✅ CrewAI compat shim: Set OPENAI_API_KEY from DEEPINFRA_API_KEY"
                    )
                elif existing_openai_key:
                    logging.getLogger(__name__).info(
                        "ℹ️ CrewAI compat shim: Preserving existing OPENAI_API_KEY"
                    )
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"⚠️ CrewAI OpenAI compat shim setup failed: {e}"
            )

        # Setup LiteLLM tracking for automatic LLM usage logging
        try:
            logging.getLogger(__name__).info("🔄 Setting up LiteLLM tracking...")
            from app.services.litellm_tracking_callback import setup_litellm_tracking

            setup_litellm_tracking()
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning("LiteLLM tracking setup warning: %s", e)

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

        # Shutdown agent monitoring
        try:
            logging.getLogger(__name__).info("🛑 Shutting down agent monitoring...")
            shutdown_agent_monitoring()
            logging.getLogger(__name__).info(
                "✅ Agent monitoring shut down successfully"
            )
        except Exception as e:  # pragma: no cover
            logging.getLogger(__name__).warning(
                "⚠️ Failed to shut down agent monitoring: %s", e
            )

        # Shutdown flow health monitor
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
