#!/usr/bin/env python3
"""
Fix all create_index calls in migration 012 to use create_index_if_not_exists
"""

import re
from pathlib import Path


def fix_create_index_calls(file_path: Path):
    """Replace op.create_index with create_index_if_not_exists"""

    content = file_path.read_text()

    # Skip the function definition itself
    lines = content.split("\n")
    in_function_def = False
    modified_lines = []

    for line in lines:
        # Check if we're in the create_index_if_not_exists function definition
        if "def create_index_if_not_exists" in line:
            in_function_def = True
        elif in_function_def and line.strip() and not line.startswith(" "):
            in_function_def = False

        # Replace op.create_index calls outside of function definitions
        if not in_function_def and re.match(r"^\s*op\.create_index\(", line):
            line = re.sub(r"op\.create_index\(", "create_index_if_not_exists(", line)

        modified_lines.append(line)

    file_path.write_text("\n".join(modified_lines))
    print(f"✓ Fixed create_index calls in {file_path.name}")


def main():
    """Main function"""
    migration_file = (
        Path(__file__).parent.parent
        / "alembic"
        / "versions"
        / "012_agent_observability_enhancement.py"
    )

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return

    fix_create_index_calls(migration_file)
    print("✅ Done")


if __name__ == "__main__":
    main()
