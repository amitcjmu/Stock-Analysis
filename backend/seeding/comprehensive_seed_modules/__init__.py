#!/usr/bin/env python3
"""
Comprehensive Data Seeding Script - Modularized by CC

This package creates realistic test data across all models with proper relationships,
including multi-tenant scenarios and vector embeddings for agent patterns.

Usage:
    python -m seeding.00_comprehensive_seed [--cleanup] [--tenants=2]

Or import directly:
    from seeding.00_comprehensive_seed import seed_comprehensive_data
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path for standalone execution  # noqa: E402
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402

# Import all seeding functions to maintain backward compatibility  # noqa: E402
from .agent_data import seed_agent_data  # noqa: E402
from .asset_data import seed_assets_and_dependencies  # noqa: E402
from .base import (  # noqa: E402
    AGENT_PATTERNS,
    LLM_INTERACTIONS,
    TENANT_CONFIG,
    TEST_TENANT_1,
    TEST_TENANT_2,
    generate_dummy_embedding,
)
from .tenant_data import (  # noqa: E402
    seed_core_entities,
    seed_discovery_flows,
    seed_llm_usage,
)
from .utils import cleanup_existing_data, print_seeding_statistics  # noqa: E402

# Public API - all functions that were previously available
__all__ = [
    # Constants
    "TEST_TENANT_1",
    "TEST_TENANT_2",
    "TENANT_CONFIG",
    "AGENT_PATTERNS",
    "LLM_INTERACTIONS",
    # Utility functions
    "generate_dummy_embedding",
    "cleanup_existing_data",
    "print_seeding_statistics",
    # Seeding functions
    "seed_core_entities",
    "seed_discovery_flows",
    "seed_agent_data",
    "seed_llm_usage",
    "seed_assets_and_dependencies",
    "seed_comprehensive_data",
    "main",
]


async def seed_comprehensive_data(cleanup: bool = False, num_tenants: int = 2):
    """Main seeding function - orchestrates all seeding operations"""
    print("🚀 Starting comprehensive data seeding...\n")

    # Only use the configured test tenants
    if num_tenants > 2:
        print("⚠️  Only 2 test tenants are configured. Using both.")
        num_tenants = 2

    async with AsyncSessionLocal() as session:
        try:
            if cleanup:
                await cleanup_existing_data(session)

            # Seed data in dependency order
            await seed_core_entities(session)
            await seed_discovery_flows(session)
            await seed_agent_data(session)
            await seed_llm_usage(session)
            await seed_assets_and_dependencies(session)

            # Final statistics
            await print_seeding_statistics(session)

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await session.rollback()
            raise


async def main():
    """Main entry point for CLI execution"""
    parser = argparse.ArgumentParser(
        description="Seed comprehensive test data for multi-tenant scenarios"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean existing test data before seeding",
    )
    parser.add_argument(
        "--tenants",
        type=int,
        default=2,
        help="Number of tenants to create (max 2)",
    )

    args = parser.parse_args()

    try:
        await seed_comprehensive_data(
            cleanup=args.cleanup,
            num_tenants=args.tenants,
        )
    except KeyboardInterrupt:
        print("\n❌ Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
