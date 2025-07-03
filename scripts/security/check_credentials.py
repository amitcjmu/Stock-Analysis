#!/usr/bin/env python3
"""
Check for hardcoded credentials and secrets in code
Used by pre-commit hooks
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns that indicate potential secrets
SECRET_PATTERNS = [
    # API Keys
    (r'api[_-]?key\s*=\s*["\'][\w\-]{20,}["\']', 'Hardcoded API key'),
    (r'apikey\s*:\s*["\'][\w\-]{20,}["\']', 'Hardcoded API key in config'),
    
    # Passwords
    (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
    (r'passwd\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
    (r'pwd\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
    
    # Secret Keys
    (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret key'),
    (r'private[_-]?key\s*=\s*["\'][^"\']+["\']', 'Hardcoded private key'),
    
    # Database Credentials
    (r'mongodb\+srv://[^:]+:[^@]+@', 'MongoDB connection string with credentials'),
    (r'postgres://[^:]+:[^@]+@', 'PostgreSQL connection string with credentials'),
    (r'mysql://[^:]+:[^@]+@', 'MySQL connection string with credentials'),
    
    # AWS Credentials
    (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', 'AWS access key'),
    (r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']', 'AWS secret key'),
    
    # JWT Secrets
    (r'jwt[_-]?secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded JWT secret'),
    
    # Generic Secrets
    (r'token\s*=\s*["\'][\w\-\.]{20,}["\']', 'Hardcoded token'),
    (r'bearer\s+[\w\-\.]{20,}', 'Hardcoded bearer token'),
]

# Patterns that are acceptable (false positives)
ALLOWED_PATTERNS = [
    r'Field\(default=None',  # Pydantic field definitions
    r'Column\(',  # SQLAlchemy column definitions
    r'# EXAMPLE',  # Example code
    r'# TODO',  # TODO comments
    r'\.example',  # Example files
    r'test_',  # Test files
    r'mock_',  # Mock data
    r'fake_',  # Fake data
    r'dummy_',  # Dummy data
    r'sample_',  # Sample data
    r'Bearer\s+\{token\}',  # Token placeholders
    r'your-secret-key-here',  # Placeholder text
]

def check_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check a single file for hardcoded credentials"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check if line contains allowed patterns
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in ALLOWED_PATTERNS):
                continue
            
            # Check for secret patterns
            for pattern, description in SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append((line_num, description, line.strip()))
        
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
    
    return issues

def main():
    """Main function for pre-commit hook"""
    files_to_check = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not files_to_check:
        print("No files to check")
        return 0
    
    total_issues = 0
    
    for file_path_str in files_to_check:
        file_path = Path(file_path_str)
        
        # Skip certain directories
        if any(skip in file_path.parts for skip in ['venv', 'node_modules', '.git', '__pycache__']):
            continue
        
        issues = check_file(file_path)
        
        if issues:
            print(f"\n❌ Security issues found in {file_path}:")
            for line_num, description, line in issues:
                print(f"  Line {line_num}: {description}")
                print(f"    > {line[:80]}...")
            total_issues += len(issues)
    
    if total_issues > 0:
        print(f"\n🚨 Total security issues found: {total_issues}")
        print("\nTo fix these issues:")
        print("1. Move secrets to environment variables")
        print("2. Use proper secret management (e.g., AWS Secrets Manager)")
        print("3. Never commit credentials to version control")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())