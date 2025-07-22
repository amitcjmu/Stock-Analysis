#!/usr/bin/env python3
"""
Quick Security Check - Minimal dependencies
Runs basic security checks without external tools
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class QuickSecurityChecker:
    def __init__(self, backend_dir: str = "backend"):
        self.backend_dir = Path(backend_dir)
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
    def check_hardcoded_secrets(self) -> List[Dict]:
        """Check for hardcoded secrets in Python files"""
        print("🔍 Checking for hardcoded secrets...")
        
        patterns = [
            (r'SECRET_KEY\s*=\s*["\'][^"\']+["\']', 'Hardcoded SECRET_KEY', 'critical'),
            (r'api_key\s*=\s*["\'][\w\-]{20,}["\']', 'Hardcoded API key', 'high'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password', 'high'),
            (r'DEEPINFRA_API_KEY\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key', 'critical'),
            (r'JWT_SECRET\s*=\s*["\'][^"\']+["\']', 'Hardcoded JWT secret', 'critical'),
            (r'postgres://[^:]+:[^@]+@', 'Database credentials in connection string', 'critical'),
        ]
        
        exclude_patterns = [
            r'Field\(default=None',
            r'getenv',
            r'environ',
            r'# EXAMPLE',
            r'test_',
            r'\.example'
        ]
        
        for py_file in self.backend_dir.rglob("*.py"):
            if any(part in str(py_file) for part in ['venv', '__pycache__', 'migrations']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for line_num, line in enumerate(lines, 1):
                    # Skip if line matches exclude patterns
                    if any(re.search(exc, line) for exc in exclude_patterns):
                        continue
                        
                    for pattern, desc, severity in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.issues[severity].append({
                                'type': 'secret',
                                'file': str(py_file.relative_to(self.backend_dir.parent)),
                                'line': line_num,
                                'description': desc,
                                'code': line.strip()[:80]
                            })
            except Exception as e:
                print(f"  Error reading {py_file}: {e}")
                
        return self.issues
        
    def check_security_headers(self) -> None:
        """Check for missing security headers"""
        print("🔍 Checking security headers configuration...")
        
        main_py = self.backend_dir / "main.py"
        if main_py.exists():
            with open(main_py, 'r') as f:
                content = f.read()
                
            # Check for security headers
            if 'HSTS' not in content and 'Strict-Transport-Security' not in content:
                self.issues['medium'].append({
                    'type': 'config',
                    'file': 'backend/main.py',
                    'description': 'Missing HSTS security header',
                    'recommendation': 'Add Strict-Transport-Security header'
                })
                
            if 'X-Content-Type-Options' not in content:
                self.issues['medium'].append({
                    'type': 'config',
                    'file': 'backend/main.py',
                    'description': 'Missing X-Content-Type-Options header',
                    'recommendation': 'Add X-Content-Type-Options: nosniff'
                })
                
            if 'X-Frame-Options' not in content:
                self.issues['medium'].append({
                    'type': 'config',
                    'file': 'backend/main.py',
                    'description': 'Missing X-Frame-Options header',
                    'recommendation': 'Add X-Frame-Options: DENY'
                })
                
    def check_authentication(self) -> None:
        """Check authentication implementation"""
        print("🔍 Checking authentication configuration...")
        
        auth_files = list(self.backend_dir.rglob("*auth*.py"))
        
        # Check for weak token generation
        for auth_file in auth_files:
            try:
                with open(auth_file, 'r') as f:
                    content = f.read()
                    
                if 'db-token-' in content and 'uuid4().hex[:8]' in content:
                    self.issues['high'].append({
                        'type': 'auth',
                        'file': str(auth_file.relative_to(self.backend_dir.parent)),
                        'description': 'Weak token generation using simple concatenation',
                        'recommendation': 'Use proper JWT with signing'
                    })
                    
                if 'expir' not in content.lower() and 'jwt' in content.lower():
                    self.issues['high'].append({
                        'type': 'auth',
                        'file': str(auth_file.relative_to(self.backend_dir.parent)),
                        'description': 'No token expiration implemented',
                        'recommendation': 'Add token expiration time'
                    })
            except:
                pass
                
    def check_rate_limiting(self) -> None:
        """Check for rate limiting implementation"""
        print("🔍 Checking rate limiting...")
        
        # Search for rate limiting in main.py and routers
        rate_limit_found = False
        
        for py_file in self.backend_dir.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if any(term in content.lower() for term in ['ratelimit', 'rate_limit', 'slowapi', 'limiter']):
                        rate_limit_found = True
                        break
            except:
                pass
                
        if not rate_limit_found:
            self.issues['high'].append({
                'type': 'api',
                'description': 'No rate limiting implementation found',
                'recommendation': 'Implement rate limiting to prevent API abuse'
            })
            
    def check_input_validation(self) -> None:
        """Check for input validation"""
        print("🔍 Checking input validation...")
        
        # Check for SQL injection risks
        for py_file in self.backend_dir.rglob("*.py"):
            if any(part in str(py_file) for part in ['venv', '__pycache__']):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                # Check for raw SQL execution
                if 'execute(' in content and ('f"' in content or 'f\'' in content):
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'execute(' in line and ('f"' in line or 'f\'' in line):
                            self.issues['critical'].append({
                                'type': 'injection',
                                'file': str(py_file.relative_to(self.backend_dir.parent)),
                                'line': i + 1,
                                'description': 'Potential SQL injection with f-strings',
                                'code': line.strip()[:80]
                            })
            except:
                pass
                
    def generate_report(self) -> str:
        """Generate markdown report"""
        total_issues = sum(len(issues) for issues in self.issues.values())
        critical_count = len(self.issues['critical'])
        high_count = len(self.issues['high'])
        
        report = f"""# Quick Security Assessment Report

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Issues**: {total_issues}  
**Critical**: {critical_count}  
**High**: {high_count}  
**Medium**: {len(self.issues['medium'])}  
**Low**: {len(self.issues['low'])}  

## Risk Level: {'🚨 CRITICAL' if critical_count > 0 else '⚠️ HIGH' if high_count > 0 else '✅ MODERATE'}

"""
        
        # Add issues by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            if self.issues[severity]:
                report += f"\n## {severity.upper()} Severity Issues ({len(self.issues[severity])})\n\n"
                
                for i, issue in enumerate(self.issues[severity], 1):
                    report += f"### {i}. {issue['description']}\n"
                    
                    if 'file' in issue:
                        report += f"**File**: `{issue['file']}`"
                        if 'line' in issue:
                            report += f" (line {issue['line']})"
                        report += "\n"
                        
                    if 'code' in issue:
                        report += f"**Code**: `{issue['code']}`\n"
                        
                    if 'recommendation' in issue:
                        report += f"**Fix**: {issue['recommendation']}\n"
                        
                    report += "\n"
                    
        # Add recommendations
        report += """
## Top Security Recommendations

1. **Remove all hardcoded secrets** - Move to environment variables immediately
2. **Implement proper JWT** - Replace weak token generation with signed JWTs
3. **Add rate limiting** - Protect all API endpoints from abuse
4. **Enable security headers** - Add HSTS, CSP, X-Frame-Options, etc.
5. **Implement MFA** - Add multi-factor authentication for admin accounts
6. **Add input validation** - Sanitize all user inputs
7. **Enable audit logging** - Track all security-sensitive operations
8. **Regular security scans** - Integrate automated security testing

## Files with Critical Issues

"""
        # List files with critical issues
        critical_files = set()
        for issue in self.issues['critical']:
            if 'file' in issue:
                critical_files.add(issue['file'])
                
        for f in sorted(critical_files):
            report += f"- `{f}`\n"
            
        return report
        
    def save_report(self, output_dir: str) -> None:
        """Save reports to directory"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save markdown report
        with open(output_path / "QUICK_SECURITY_ASSESSMENT.md", 'w') as f:
            f.write(self.generate_report())
            
        # Save JSON report
        with open(output_path / "security-issues.json", 'w') as f:
            json.dump({
                'scan_date': datetime.now().isoformat(),
                'summary': {
                    'total': sum(len(issues) for issues in self.issues.values()),
                    'critical': len(self.issues['critical']),
                    'high': len(self.issues['high']),
                    'medium': len(self.issues['medium']),
                    'low': len(self.issues['low'])
                },
                'issues': self.issues
            }, f, indent=2)
            
def main():
    print("🚀 Running Quick Security Assessment...")
    print("=" * 50)
    
    checker = QuickSecurityChecker()
    
    # Run all checks
    checker.check_hardcoded_secrets()
    checker.check_security_headers()
    checker.check_authentication() 
    checker.check_rate_limiting()
    checker.check_input_validation()
    
    # Generate report
    report_dir = f"security-reports-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    checker.save_report(report_dir)
    
    # Print summary
    print("\n✅ Security scan complete!")
    print("\nSummary:")
    print(f"  Critical: {len(checker.issues['critical'])}")
    print(f"  High: {len(checker.issues['high'])}")
    print(f"  Medium: {len(checker.issues['medium'])}")
    print(f"  Low: {len(checker.issues['low'])}")
    print(f"\nReports saved to: {report_dir}/")
    print(f"  - {report_dir}/QUICK_SECURITY_ASSESSMENT.md")
    print(f"  - {report_dir}/security-issues.json")
    
    # Show critical issues immediately
    if checker.issues['critical']:
        print("\n🚨 CRITICAL ISSUES FOUND:")
        for issue in checker.issues['critical'][:3]:
            print(f"  - {issue['description']}")
            if 'file' in issue:
                print(f"    in {issue['file']}")
                
if __name__ == '__main__':
    main()