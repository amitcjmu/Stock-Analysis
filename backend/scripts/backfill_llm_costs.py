#!/usr/bin/env python3
"""
Backfill LLM costs for existing records with NULL costs.

This script recalculates costs for llm_usage_logs records where:
- llm_provider was 'unknown' (due to provider detection bug)
- total_cost is NULL

It corrects the provider based on model_name patterns and recalculates costs
using the llm_model_pricing table.

Usage:
    python backend/scripts/backfill_llm_costs.py [--days N] [--dry-run]

Options:
    --days N     Only backfill records from last N days (default: all records)
    --dry-run    Show what would be updated without making changes
"""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


def detect_provider_from_model(model_name: str) -> str:
    """
    Detect provider from model name using same logic as fixed callback.

    Args:
        model_name: The model name to analyze

    Returns:
        Provider name (deepinfra, openai, anthropic, or unknown)
    """
    model_lower = model_name.lower()

    # Check for provider prefix in model name
    if "deepinfra/" in model_lower or "deepinfra" in model_lower:
        return "deepinfra"
    elif "openai" in model_lower or "gpt" in model_lower:
        return "openai"
    elif "anthropic" in model_lower or "claude" in model_lower:
        return "anthropic"
    # Check for model name patterns hosted on DeepInfra
    elif model_name.startswith(("meta-llama/", "google/", "mistralai/")):
        return "deepinfra"
    else:
        return "unknown"


async def get_model_pricing(
    session: AsyncSession, provider: str, model_name: str
) -> Optional[dict]:
    """
    Get pricing for a specific model from llm_model_pricing table.

    Args:
        session: Database session
        provider: Provider name (deepinfra, openai, etc.)
        model_name: Model name

    Returns:
        Dict with input/output pricing or None if not found
    """
    query = text(
        """
        SELECT input_cost_per_1k_tokens, output_cost_per_1k_tokens
        FROM migration.llm_model_pricing
        WHERE provider = :provider
        AND model_name = :model
        AND is_active = true
        AND effective_from <= NOW()
        AND (effective_to IS NULL OR effective_to > NOW())
        ORDER BY effective_from DESC
        LIMIT 1
    """
    )

    result = await session.execute(query, {"provider": provider, "model": model_name})
    row = result.fetchone()

    if row:
        return {"input": float(row[0]), "output": float(row[1])}
    return None


async def backfill_costs(
    days: Optional[int] = None, dry_run: bool = False
) -> dict:
    """
    Backfill costs for records with NULL costs.

    Args:
        days: Only process records from last N days (None = all)
        dry_run: If True, show updates without applying them

    Returns:
        Dict with stats about the backfill operation
    """
    stats = {
        "total_records": 0,
        "records_processed": 0,
        "provider_corrected": 0,
        "costs_calculated": 0,
        "pricing_not_found": 0,
        "errors": 0,
        "by_provider": {},
    }

    async with AsyncSessionLocal() as session:
        try:
            # Build query for records needing backfill
            where_clause = "WHERE (total_cost IS NULL OR llm_provider = 'unknown')"
            if days:
                where_clause += f" AND created_at >= NOW() - INTERVAL '{days} days'"

            # Get records to backfill
            query = text(
                f"""
                SELECT id, llm_provider, model_name, input_tokens, output_tokens
                FROM migration.llm_usage_logs
                {where_clause}
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(query)
            records = result.fetchall()
            stats["total_records"] = len(records)

            print(f"\n📊 Found {len(records)} records to backfill")
            if dry_run:
                print("🔍 DRY RUN MODE - No changes will be made\n")
            else:
                print("✍️  LIVE MODE - Updating database\n")

            for record in records:
                record_id, current_provider, model_name, input_tokens, output_tokens = (
                    record
                )
                stats["records_processed"] += 1

                try:
                    # Detect correct provider
                    correct_provider = detect_provider_from_model(model_name)

                    # Track provider corrections
                    if correct_provider != current_provider:
                        stats["provider_corrected"] += 1
                        print(
                            f"  Provider correction: {current_provider} → {correct_provider} "
                            f"(model: {model_name})"
                        )

                    # Track by provider
                    if correct_provider not in stats["by_provider"]:
                        stats["by_provider"][correct_provider] = 0
                    stats["by_provider"][correct_provider] += 1

                    # Get pricing
                    pricing = await get_model_pricing(
                        session, correct_provider, model_name
                    )

                    if not pricing:
                        stats["pricing_not_found"] += 1
                        print(
                            f"  ⚠️  No pricing found for {correct_provider}/{model_name}"
                        )
                        continue

                    # Calculate costs
                    input_cost = 0
                    output_cost = 0

                    if input_tokens:
                        input_cost = (input_tokens / 1000) * pricing["input"]

                    if output_tokens:
                        output_cost = (output_tokens / 1000) * pricing["output"]

                    total_cost = input_cost + output_cost

                    if not dry_run:
                        # Update record
                        update = text(
                            """
                            UPDATE migration.llm_usage_logs
                            SET llm_provider = :provider,
                                input_cost = :input_cost,
                                output_cost = :output_cost,
                                total_cost = :total_cost,
                                updated_at = NOW()
                            WHERE id = :id
                        """
                        )

                        await session.execute(
                            update,
                            {
                                "id": record_id,
                                "provider": correct_provider,
                                "input_cost": Decimal(str(input_cost)),
                                "output_cost": Decimal(str(output_cost)),
                                "total_cost": Decimal(str(total_cost)),
                            },
                        )

                    stats["costs_calculated"] += 1

                    # Show progress every 100 records
                    if stats["records_processed"] % 100 == 0:
                        print(
                            f"  Progress: {stats['records_processed']}/{stats['total_records']} records..."
                        )

                except Exception as e:
                    stats["errors"] += 1
                    print(f"  ❌ Error processing record {record_id}: {e}")
                    continue

            if not dry_run:
                await session.commit()
                print("\n✅ Database updated successfully")
            else:
                print("\n🔍 Dry run complete - no changes made")

        except Exception as e:
            print(f"\n❌ Fatal error during backfill: {e}")
            if not dry_run:
                await session.rollback()
            raise

    return stats


def print_stats(stats: dict):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("BACKFILL SUMMARY")
    print("=" * 60)
    print(f"Total records found:      {stats['total_records']}")
    print(f"Records processed:        {stats['records_processed']}")
    print(f"Provider corrected:       {stats['provider_corrected']}")
    print(f"Costs calculated:         {stats['costs_calculated']}")
    print(f"Pricing not found:        {stats['pricing_not_found']}")
    print(f"Errors:                   {stats['errors']}")
    print("\nBy Provider:")
    for provider, count in sorted(stats["by_provider"].items()):
        print(f"  {provider}: {count} records")
    print("=" * 60)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill LLM costs for existing records"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Only backfill records from last N days (default: all records)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    print("\n🔧 LLM Cost Backfill Tool")
    print("=" * 60)

    if args.days:
        print(f"Scope: Last {args.days} days")
    else:
        print("Scope: All records")

    if args.dry_run:
        print("Mode: DRY RUN (no changes)")
    else:
        print("Mode: LIVE (will update database)")
        confirm = input("\n⚠️  This will update the database. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

    print("\nStarting backfill...\n")

    try:
        stats = await backfill_costs(days=args.days, dry_run=args.dry_run)
        print_stats(stats)

        if not args.dry_run and stats["costs_calculated"] > 0:
            print(
                "\n✨ Backfill complete! Grafana dashboards should now show cost data."
            )
            print("   Visit: http://localhost:9999/d/llm-costs/llm-costs")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
