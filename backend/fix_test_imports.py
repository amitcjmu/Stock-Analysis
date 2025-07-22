#!/usr/bin/env python3
"""
Script to fix common import issues in test files.
Adds type: ignore comments where necessary and fixes common import patterns.
"""

import os
import re
import sys
from pathlib import Path

def fix_test_imports(file_path: Path) -> bool:
    """Fix import issues in a single test file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
original_content = content
        
        # Fix backend.main imports
        content = re.sub(r'from backend\.main import', 'from app.main import', content)
        
        # Add type: ignore for known problematic imports
        problematic_imports = [
            'litellm',
            'asyncpg',
            'pgvector',
            'crewai',
            'embedchain',
            'chromadb',
            'anthropic',
            'openai',
            'cohere',
            'lancedb',
            'mem0ai',
            'posthog',
            'opentelemetry',
            'psutil',
            'requests',
            'pandas'
        ] for module in problematic_imports:
            # Add type: ignore to imports of these modules
            content = re.sub(
                rf'(import {module}(?:\.[^\n]*)?)(\s*#.*)?$',
                rf'\1  # type: ignore[import-untyped]',
                content,
                flags=re.MULTILINE
            )
            content = re.sub(
                rf'(from {module}(?:\.[^\n]*)?import[^\n]*)(\s*#.*)?$',
                rf'\1  # type: ignore[import-untyped]',
                content,
                flags=re.MULTILINE
            )
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Process all test files."""
    tests_dir = Path(__file__).parent / 'tests'
    
    if not tests_dir.exists():
        print(f"Tests directory not found: {tests_dir}")
        sys.exit(1)
    
    fixed_count = 0
total_count = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if test_file.name.startswith('test_') or test_file.name == 'conftest.py':
            total_count += 1
            if fix_test_imports(test_file):
                fixed_count += 1
print(f"Fixed: {test_file.relative_to(tests_dir)}")
    
    print(f"\nProcessed {total_count} test files, fixed {fixed_count}")


if __name__ == '__main__':
main()