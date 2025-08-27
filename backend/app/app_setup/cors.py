import logging
import os
import re
from typing import List
from fastapi.middleware.cors import CORSMiddleware


def validate_cors_origins(origins: List[str]) -> List[str]:
    """
    Validate CORS origins to prevent security vulnerabilities.

    Security checks:
    - No wildcard origins (*) in production
    - Origins must be valid URLs
    - No localhost origins in production unless explicitly allowed

    Args:
        origins: List of origin URLs to validate

    Returns:
        List of validated origins
    """
    validated_origins = []
    environment = os.getenv("ENVIRONMENT", "production").lower()
    is_production = environment in ["production", "prod"]

    # URL pattern for basic validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"  # domain
        r"[A-Z]{2,6}\.?|"  # TLD
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    for origin in origins:
        if not origin or not isinstance(origin, str):
            logging.getLogger(__name__).warning(
                f"Skipping invalid origin (empty or not string): {origin}"
            )
            continue

        # SECURITY: Block wildcard origins
        if origin == "*":
            if is_production:
                logging.getLogger(__name__).error(
                    "SECURITY VIOLATION: Wildcard origin (*) blocked in production"
                )
                continue
            else:
                logging.getLogger(__name__).warning(
                    "Wildcard origin (*) allowed in development only"
                )
                validated_origins.append(origin)
                continue

        # Basic URL validation
        if not url_pattern.match(origin):
            logging.getLogger(__name__).warning(f"Invalid origin URL format: {origin}")
            continue

        # SECURITY: Check for localhost in production
        if is_production and ("localhost" in origin or "127.0.0.1" in origin):
            # Only allow if explicitly configured via environment variable
            if not os.getenv("ALLOW_LOCALHOST_IN_PRODUCTION"):
                logging.getLogger(__name__).warning(
                    f"Localhost origin blocked in production: {origin}"
                )
                continue

        validated_origins.append(origin)

    # Log final validated origins for security audit
    logging.getLogger(__name__).info(
        f"CORS origins validated: {len(validated_origins)} allowed out of {len(origins)} provided"
    )

    return validated_origins


def add_cors(app, settings):
    def get_cors_origins():
        cors_origins = []
        env = getattr(settings, "ENVIRONMENT", "development").lower()
        is_dev = env in ["development", "dev", "local", "localhost"]

        if is_dev or env not in ["production", "prod"]:
            cors_origins.extend(
                [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://localhost:8080",
                    "http://localhost:8081",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:8080",
                    "http://127.0.0.1:8081",
                ]
            )
        else:
            cors_origins.extend(
                [
                    "https://aiforce-assess.vercel.app",
                    "https://migrate-ui-orchestrator-production.up.railway.app",
                ]
            )

        if (
            os.getenv("RAILWAY_ENVIRONMENT")
            or os.getenv("RAILWAY_PROJECT_NAME")
            or os.getenv("PORT")
            or "railway.app" in os.getenv("DATABASE_URL", "")
        ):
            cors_origins.extend(
                [
                    "https://aiforce-assess.vercel.app",
                    "https://migrate-ui-orchestrator-production.up.railway.app",
                ]
            )

        if hasattr(settings, "FRONTEND_URL") and settings.FRONTEND_URL:
            cors_origins.append(settings.FRONTEND_URL)

        # SECURITY FIX: Validate environment-provided CORS origins
        if hasattr(settings, "allowed_origins_list"):
            # Filter out any potential wildcards or invalid origins from environment
            env_origins = settings.allowed_origins_list
            if isinstance(env_origins, list):
                # Pre-validate environment origins before adding
                for origin in env_origins:
                    if isinstance(origin, str) and origin.strip():
                        # Basic validation - no wildcards from env vars
                        if origin != "*" or os.getenv(
                            "ENVIRONMENT", "production"
                        ).lower() not in ["production", "prod"]:
                            cors_origins.append(origin.strip())
                        else:
                            logging.getLogger(__name__).error(
                                f"SECURITY: Blocked wildcard origin from environment: {origin}"
                            )

        if (
            (
                os.getenv("DATABASE_URL")
                and "railway.app" in os.getenv("DATABASE_URL", "")
            )
            or os.getenv("PORT")
            or os.getenv("RAILWAY_ENVIRONMENT")
            or env == "production"
        ):
            vercel_domain = "https://aiforce-assess.vercel.app"
            if vercel_domain not in cors_origins:
                cors_origins.append(vercel_domain)

        # SECURITY FIX: Validate all origins before returning
        unique_origins = list(set(filter(None, cors_origins)))
        return validate_cors_origins(unique_origins)

    origins = get_cors_origins()

    # SECURITY VALIDATION: Check credentials usage with multiple origins
    environment = os.getenv("ENVIRONMENT", "production").lower()
    is_production = environment in ["production", "prod"]

    if len(origins) > 1 and is_production:
        # In production with credentials=True and multiple origins, ensure they're all trusted
        logging.getLogger(__name__).info(
            f"SECURITY AUDIT: Credentials enabled with {len(origins)} CORS origins in production"
        )
        for origin in origins:
            logging.getLogger(__name__).info(f"CORS origin allowed: {origin}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Client-Account-ID",
            "X-Client-ID",
            "X-Engagement-ID",
            "X-Trace-ID",
            "X-Request-ID",
            "X-User-ID",
            "X-User-Role",
            "X-Flow-ID",
            "Cache-Control",
            "Pragma",
            "Accept",
            "Accept-Language",
            "Accept-Encoding",
            "Content-Language",
        ],
        expose_headers=["X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Reset"],
        max_age=3600,
    )
    logging.getLogger(__name__).info("✅ CORS middleware added")
