#!/usr/bin/env python3
"""Validate no singular /flow/ resource endpoints exist."""
import sys
from pathlib import Path
import re

def check_for_singular_flow_endpoints():
    violations = []
    backend_path = Path("backend/app/api")

    for py_file in backend_path.rglob("*.py"):
        content = py_file.read_text()

        # Check for @router decorators with /flow/ (excluding flow-processing)
        # Use regex to match /flow/ but not /flows/
        if '@router.' in content and re.search(r'"/flow/(?!s)', content):
            # Skip if it's flow-processing (action endpoint)
            if 'flow-processing' not in str(py_file) and 'flow-processing' not in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '@router.' in line and re.search(r'"/flow/(?!s)', line):
                        violations.append(f"{py_file}:{i+1}: {line.strip()}")

        # Check for prefix="/flow" mounts (but not /flows or flow-* compound names)
        if re.search(r'prefix="/flow(?!s|-)', content):
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.search(r'prefix="/flow(?!s|-)', line):
                    violations.append(f"{py_file}:{i+1}: {line.strip()}")

    return violations

if __name__ == "__main__":
    violations = check_for_singular_flow_endpoints()
    if violations:
        print("❌ Singular /flow/ endpoints found (should be /flows/):")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)
    else:
        print("✅ No singular /flow/ endpoints found")
        sys.exit(0)
