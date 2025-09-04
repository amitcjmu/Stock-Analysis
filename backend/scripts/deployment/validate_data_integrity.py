#!/usr/bin/env python3
"""
Production Data Integrity Validation Script - Facade for Backward Compatibility

This script validates data integrity in production environments by checking:
1. Foreign key relationships are properly established
2. No orphaned records exist
3. Cascade deletion rules are configured correctly
4. Performance monitoring queries execute efficiently
5. Database constraints are enforced

This file now serves as a facade, importing the modularized implementation.

Usage:
    python scripts/deployment/validate_data_integrity.py
    python scripts/deployment/validate_data_integrity.py --client-id <uuid>
    python scripts/deployment/validate_data_integrity.py --engagement-id <uuid>
    python scripts/deployment/validate_data_integrity.py --fix-issues
"""

import argparse
import asyncio
import json
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the modularized validator
try:
    from .data_integrity_validation import DataIntegrityValidator
except ImportError:
    # Handle relative import when running directly
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from data_integrity_validation import DataIntegrityValidator


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Validate data integrity in production database"
    )
    parser.add_argument(
        "--client-id", type=str, help="Limit validation to specific client account ID"
    )
    parser.add_argument(
        "--engagement-id", type=str, help="Limit validation to specific engagement ID"
    )
    parser.add_argument(
        "--fix-issues",
        action="store_true",
        help="Attempt to automatically fix identified issues",
    )
    parser.add_argument(
        "--output-file", type=str, help="Save validation results to JSON file"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def validate_uuid_args(args):
    """Validate UUID format for arguments"""
    client_account_id = None
    if args.client_id:
        try:
            uuid.UUID(args.client_id)
            client_account_id = args.client_id
        except ValueError:
            logger.error(f"Invalid client-id format: {args.client_id}")
            return None, None, 1

    engagement_id = None
    if args.engagement_id:
        try:
            uuid.UUID(args.engagement_id)
            engagement_id = args.engagement_id
        except ValueError:
            logger.error(f"Invalid engagement-id format: {args.engagement_id}")
            return None, None, 1

    return client_account_id, engagement_id, 0


def print_validation_summary(results):
    """Print validation results summary"""
    print("\n" + "=" * 80)
    print("DATA INTEGRITY VALIDATION RESULTS")
    print("=" * 80)
    print(f"Status: {results.get('overall_status', 'UNKNOWN')}")
    print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
    print(f"Issues Found: {len(results.get('issues_found', []))}")

    # Print summary
    summary = results.get("summary", {})
    if summary:
        print(f"\nComponents Tested: {summary['components_tested']}")
        print(f"Components Passed: {summary['components_passed']}")

        for component, status in summary.get("component_status", {}).items():
            status_icon = "✅" if status["status"] == "PASS" else "❌"
            print(
                f"  {status_icon} {component}: {status['status']} ({status['issues_count']} issues)"
            )


def print_issues_and_recommendations(results):
    """Print issues and recommendations"""
    # Print issues if any
    issues_found = results.get("issues_found", [])
    if issues_found:
        print(f"\n{'='*40} ISSUES {'='*40}")
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. {issue}")

    # Print recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n{'='*35} RECOMMENDATIONS {'='*35}")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = (
                "🔴"
                if rec["priority"] == "CRITICAL"
                else "🟡" if rec["priority"] == "HIGH" else "🟢"
            )
            print(f"{i}. {priority_icon} [{rec['priority']}] {rec['title']}")
            print(f"   {rec['description']}")
            print(f"   Action: {rec['action']}")
            print()


def get_exit_code(results):
    """Determine appropriate exit code based on results"""
    overall_status = results.get("overall_status", "ERROR")

    if overall_status == "HEALTHY":
        logger.info("✅ Data integrity validation completed successfully")
        return 0
    elif overall_status == "WARNING":
        logger.warning("⚠️ Data integrity validation completed with warnings")
        # Return 0 for warnings to prevent CI pipeline failures
        # Warnings indicate issues that need attention but don't prevent deployment
        return 0
    else:
        logger.error("❌ Data integrity validation found critical issues")
        return 1  # Changed from 2 to 1 for standard error exit code


async def main():
    """Main entry point for the data integrity validation script"""
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate UUID format if provided
    client_account_id, engagement_id, error_code = validate_uuid_args(args)
    if error_code != 0:
        return error_code

    try:
        # Create validator instance
        validator = DataIntegrityValidator(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            fix_issues=args.fix_issues,
        )

        # Run comprehensive validation
        logger.info("🚀 Starting data integrity validation...")
        results = await validator.validate_all()

        # Output results
        print_validation_summary(results)
        print_issues_and_recommendations(results)

        # Save results to file if requested
        if args.output_file:
            with open(args.output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to {args.output_file}")

        # Return appropriate exit code
        return get_exit_code(results)

    except Exception as e:
        logger.error(f"❌ Data integrity validation failed: {str(e)}", exc_info=True)
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
