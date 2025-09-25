#!/usr/bin/env python3
"""
Check for cloud service keys in staged files.
Windows-compatible Python version of check-cloud-keys.sh
"""

import re
import subprocess
import sys
from pathlib import Path


def get_staged_files():
    """Get list of staged files that match our patterns."""
    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        # Filter for relevant file types
        relevant_files = []
        for file in files:
            if file and Path(file).suffix in ['.py', '.yml', '.yaml', '.json', '.env']:
                relevant_files.append(file)
        return relevant_files
    except subprocess.CalledProcessError:
        return []


def check_file_for_cloud_keys(file_path):
    """Check a single file for cloud service key patterns."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # AWS Access Key ID pattern
        # AWS Secret Access Key: 40-character base64 string
        patterns = [
            r'AKIA[0-9A-Z]{16}',
            r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])'
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                return True
        return False
    except Exception:
        return False


def main():
    """Main function to check staged files for cloud keys."""
    staged_files = get_staged_files()

    if not staged_files:
        return 0

    violations = []
    for file_path in staged_files:
        if Path(file_path).exists() and check_file_for_cloud_keys(file_path):
            violations.append(file_path)

    if violations:
        print("Found cloud service keys in:")
        for file in violations:
            print(f"  {file}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
