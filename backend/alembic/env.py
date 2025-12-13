import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.database import Base

# Import all models explicitly for Alembic auto-detection
# flake8: noqa: F401
from app.models.agent_communication import AgentInsight, AgentQuestion, DataItem
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.models.agent_performance_daily import AgentPerformanceDaily
from app.models.agent_task_history import AgentTaskHistory
from app.models.asset import Asset, AssetDependency
from app.models.client_account import (
    ClientAccount,
    Engagement,
    User,
    UserAccountAssociation,
)
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_cleansing import DataCleansingRecommendation
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.models.feedback import Feedback
from app.models.flow_deletion_audit import FlowDeletionAudit
from app.models.llm_usage import LLMUsageLog, LLMUsageSummary
from app.models.migration import Migration
from app.models.platform_adapter import AdapterStatus, PlatformAdapter
from app.models.platform_credentials import (
    CredentialAccessLog,
    CredentialPermission,
    CredentialRotationHistory,
    CredentialStatus,
    CredentialType,
    PlatformCredential,
)
from app.models.rbac import AccessLevel, ClientAccess, UserRole
from app.models.security_audit import RoleChangeApproval, SecurityAuditLog

# REMOVED: SixR Analysis model deleted in Phase 4 (Issue #840)
# from app.models.sixr_analysis import SixRAnalysis
from app.models.stock import Stock, StockAnalysis
from app.models.tags import AssetTag, Tag
from app.models.user_active_flows import UserActiveFlow
from app.models.watchlist import Watchlist

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import all models to ensure they are registered with SQLAlchemy
# The following import is critical for Alembic to detect model changes.
# It assumes that your models/__init__.py file imports all your model modules.

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from environment variables or config."""
    # First try to get Railway's DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Ensure it uses sync driver for migrations (remove asyncpg)
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace(
                "postgresql+asyncpg://", "postgresql+psycopg://", 1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return database_url

    # Fallback to individual environment variables for local development
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "migration_db")

    # Use psycopg (sync) for migrations instead of asyncpg
    return f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # Ensure migration schema exists before running migrations
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS migration"))
    connection.execute(text("SET search_path TO migration"))

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table="alembic_version",
        version_table_schema="migration",
        version_table_pk=False,  # This allows for custom version table schema
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # The key fix: ensure transaction is committed
        await connection.run_sync(do_run_migrations)
        await connection.commit()

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
