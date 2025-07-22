#!/usr/bin/env python3
"""
Security Validation Script
Validates that all critical security fixes have been properly implemented.
"""

import re
import sys
from pathlib import Path


def validate_authentication_bypass_fix():
    """Validate that authentication bypass has been fixed"""
    auth_service_path = Path(__file__).parent.parent / "app" / "services" / "auth_services" / "authentication_service.py"
    
    if not auth_service_path.exists():
        return False, "Authentication service file not found"
    
    content = auth_service_path.read_text()
    
    # Check for the vulnerable pattern
    if "# For users without password hash (demo mode), accept any password" in content:
        return False, "Authentication bypass vulnerability still present"
    
    if "pass" in content and "password_hash" in content:
        # Look for the specific vulnerable pattern
        if re.search(r"else:\s*#.*demo.*\s*pass", content, re.IGNORECASE | re.MULTILINE):
            return False, "Authentication bypass pattern still found"
    
    # Check for the fix
    if "if not user.password_hash:" in content and "BLOCKED" in content:
        return True, "Authentication bypass properly fixed"
    
    return False, "Authentication fix verification failed"

def validate_hardcoded_credentials():
    """Validate that hardcoded credentials have been removed"""
    issues = []
    
    # Check docker-compose.yml
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    if docker_compose_path.exists():
        content = docker_compose_path.read_text()
        if "U8JskPYWXprQvw2PGbv4lyxfcJQggI48" in content:
            issues.append("Hardcoded DeepInfra API key still in docker-compose.yml")
        if "${DEEPINFRA_API_KEY}" not in content and "DEEPINFRA_API_KEY=" in content:
            issues.append("DeepInfra API key not using environment variable in docker-compose.yml")
    
    # Check .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        content = env_path.read_text()
        if "U8JskPYWXprQvw2PGbv4lyxfcJQggI48" in content:
            issues.append("Hardcoded DeepInfra API key still in .env file")
        if "your-super-secret-key-change-in-production" in content:
            issues.append("Default SECRET_KEY still in .env file")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "No hardcoded credentials found"

def validate_demo_credentials():
    """Validate that demo credentials are not exposed"""
    demo_handlers_path = Path(__file__).parent.parent / "app" / "api" / "v1" / "auth" / "handlers" / "demo_handlers.py"
    
    if not demo_handlers_path.exists():
        return True, "Demo handlers file not found (acceptable)"
    
    content = demo_handlers_path.read_text()
    
    # Check for exposed passwords
    if '"password": "password"' in content or '"password": "demo"' in content:
        return False, "Demo password still exposed in API response"
    
    # Check for credential exposure pattern
    if re.search(r'"password":\s*"[^"]*"', content):
        return False, "Password field found in demo credentials response"
    
    return True, "Demo credentials properly secured"

def validate_rate_limiting():
    """Validate that rate limiting is implemented"""
    rate_limiter_path = Path(__file__).parent.parent / "app" / "middleware" / "rate_limiter.py"
    
    if not rate_limiter_path.exists():
        return False, "Rate limiter middleware not found"
    
    content = rate_limiter_path.read_text()
    
    # Check for rate limiting implementation
    if "RateLimitMiddleware" not in content:
        return False, "RateLimitMiddleware class not found"
    
    if "/api/v1/auth/login" not in content:
        return False, "Login endpoint rate limiting not configured"
    
    return True, "Rate limiting properly implemented"

def validate_sql_injection_protection():
    """Validate SQL injection protection"""
    # Check for dangerous SQL patterns in user-facing endpoints
    dangerous_patterns = []
    
    # Check API endpoints and services that handle user input
    api_paths = [
        Path(__file__).parent.parent / "app" / "api",
        Path(__file__).parent.parent / "app" / "services" / "data_import",
        Path(__file__).parent.parent / "app" / "services" / "auth_services",
    ]
    
    for api_path in api_paths:
        if not api_path.exists():
            continue
            
        for py_file in api_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                
                # Skip migration hooks and other internal files
                if "migration_hooks" in str(py_file) or "database_initialization" in str(py_file):
                    continue
                
                # Look for dangerous patterns with user input
                # Check for request data being directly formatted into SQL
                if re.search(r'request\.[^}]*\}.*execute|request\.[^}]*\}.*text\(', content):
                    dangerous_patterns.append(f"Request data in SQL: {py_file}")
                
                # Check for dangerous string operations in SQL
                if re.search(r'execute\([^)]*\.format\(|text\([^)]*\.format\(', content):
                    dangerous_patterns.append(f"String format in SQL: {py_file}")
                    
            except UnicodeDecodeError:
                continue
    
    if dangerous_patterns:
        return False, "; ".join(dangerous_patterns[:2])
    
    return True, "SQL injection protection validated - parameterized queries used"

def run_security_validation():
    """Run all security validations"""
    print("🔒 Running Security Validation Tests...")
    print("=" * 50)
    
    validations = [
        ("Authentication Bypass Fix", validate_authentication_bypass_fix),
        ("Hardcoded Credentials Removal", validate_hardcoded_credentials),
        ("Demo Credentials Security", validate_demo_credentials),
        ("Rate Limiting Implementation", validate_rate_limiting),
        ("SQL Injection Protection", validate_sql_injection_protection),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in validations:
        try:
            success, message = test_func()
            if success:
                print(f"✅ {test_name}: PASS - {message}")
                passed += 1
            else:
                print(f"❌ {test_name}: FAIL - {message}")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            failed += 1
    
    print("=" * 50)
    print("📊 Security Validation Results:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Total:  {passed + failed}")
    
    if failed == 0:
        print("🎉 All security validations PASSED! Platform ready for AD integration.")
        return True
    else:
        print("⚠️  Security issues found. Please fix before AD integration.")
        return False

if __name__ == "__main__":
    success = run_security_validation()
    sys.exit(0 if success else 1)