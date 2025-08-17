#!/usr/bin/env python3
"""
Utility script to check all Python files in the codebase for length violations.
This is for analysis purposes - the pre-commit hook only checks staged files.
"""

import sys
from pathlib import Path
from typing import Dict, List
import argparse

# Configuration (same as pre-commit hook)
MAX_LINES_ERROR = 400  # Hard limit
MAX_LINES_WARNING = 350  # Soft limit
IDEAL_MAX_LINES = 300  # Best practice

# Directories to exclude
EXCLUDE_DIRS = {
    "venv", "env", ".venv",
    "node_modules",
    "__pycache__",
    ".git",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    "migrations",
}


def find_python_files(root_path: Path) -> List[Path]:
    """Find all Python files in the codebase."""
    python_files = []

    for file_path in root_path.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue
        python_files.append(file_path)

    return python_files


def count_code_lines(file_path: Path) -> int:
    """Count actual code lines (excluding blanks and pure comments)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            code_lines = 0
            in_docstring = False

            for line in lines:
                stripped = line.strip()

                # Handle docstrings
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = not in_docstring
                    code_lines += 1
                    continue

                if in_docstring:
                    code_lines += 1
                    continue

                # Count non-empty, non-comment lines
                if stripped and not stripped.startswith("#"):
                    code_lines += 1

            return code_lines
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0


def analyze_codebase(root_path: Path, verbose: bool = False) -> Dict[str, List[Path]]:
    """Analyze all Python files and categorize by size."""
    results = {
        "critical": [],  # > 400 lines
        "warning": [],   # 350-400 lines
        "attention": [], # 300-350 lines
        "good": [],      # < 300 lines
    }

    python_files = find_python_files(root_path)
    total_files = len(python_files)

    print(f"Analyzing {total_files} Python files...")

    for file_path in python_files:
        line_count = count_code_lines(file_path)
        relative_path = file_path.relative_to(root_path)

        if line_count > MAX_LINES_ERROR:
            results["critical"].append((relative_path, line_count))
        elif line_count > MAX_LINES_WARNING:
            results["warning"].append((relative_path, line_count))
        elif line_count > IDEAL_MAX_LINES:
            results["attention"].append((relative_path, line_count))
        else:
            results["good"].append((relative_path, line_count))

    return results, total_files


def print_report(results: Dict, total_files: int, verbose: bool = False):
    """Print analysis report."""
    print("\n" + "=" * 70)
    print("📊 CODEBASE FILE LENGTH ANALYSIS REPORT")
    print("=" * 70)

    # Summary statistics
    critical_count = len(results["critical"])
    warning_count = len(results["warning"])
    attention_count = len(results["attention"])
    good_count = len(results["good"])

    compliance_rate = (good_count / total_files * 100) if total_files > 0 else 0

    print(f"\n📈 SUMMARY:")
    print(f"  Total Python files: {total_files}")
    print(f"  ✅ Good (<{IDEAL_MAX_LINES} lines): {good_count} ({good_count/total_files*100:.1f}%)")
    print(f"  ℹ️  Attention ({IDEAL_MAX_LINES}-{MAX_LINES_WARNING} lines): {attention_count} ({attention_count/total_files*100:.1f}%)")
    print(f"  ⚠️  Warning ({MAX_LINES_WARNING}-{MAX_LINES_ERROR} lines): {warning_count} ({warning_count/total_files*100:.1f}%)")
    print(f"  ❌ Critical (>{MAX_LINES_ERROR} lines): {critical_count} ({critical_count/total_files*100:.1f}%)")
    print(f"\n  📊 Ideal Compliance Rate (<{IDEAL_MAX_LINES} lines): {compliance_rate:.1f}%")

    # Critical files (always show)
    if results["critical"]:
        print(f"\n🚨 CRITICAL FILES (>{MAX_LINES_ERROR} lines) - MUST BE MODULARIZED:")
        print("-" * 70)
        for path, lines in sorted(results["critical"], key=lambda x: x[1], reverse=True)[:20]:
            print(f"  ❌ {path}: {lines} lines")
        if len(results["critical"]) > 20:
            print(f"  ... and {len(results['critical']) - 20} more files")

    # Warning files (show top 10)
    if results["warning"] and verbose:
        print(f"\n⚠️  WARNING FILES ({MAX_LINES_WARNING}-{MAX_LINES_ERROR} lines):")
        print("-" * 70)
        for path, lines in sorted(results["warning"], key=lambda x: x[1], reverse=True)[:10]:
            print(f"  ⚠️  {path}: {lines} lines")
        if len(results["warning"]) > 10:
            print(f"  ... and {len(results['warning']) - 10} more files")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 70)
    if critical_count > 0:
        print(f"  🔴 {critical_count} files need IMMEDIATE modularization")
        print(f"  🟡 {warning_count} files should be modularized soon")
        print(f"  🟢 Target: All files under {MAX_LINES_ERROR} lines")
        print("\n  📚 See backend/app/repositories/crewai_flow_state_extensions/")
        print("     for a good modularization example")
    else:
        print("  ✅ No critical violations found!")
        if warning_count > 0:
            print(f"  📝 Consider modularizing {warning_count} warning-level files")

    print("\n" + "=" * 70)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Check Python file lengths across the codebase"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including warning-level files"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="backend",
        help="Path to analyze (default: backend)"
    )

    args = parser.parse_args()

    root_path = Path(args.path)
    if not root_path.exists():
        print(f"Error: Path {root_path} does not exist")
        sys.exit(1)

    results, total_files = analyze_codebase(root_path, args.verbose)
    print_report(results, total_files, args.verbose)

    # Exit with error if there are critical violations
    if results["critical"]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
