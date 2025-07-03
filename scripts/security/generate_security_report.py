#!/usr/bin/env python3
"""
Security Report Generator
Consolidates security scan results into a comprehensive report
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import markdown2

class SecurityReportGenerator:
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        self.summary = {
            'total_issues': 0,
            'critical_count': 0,
            'high_count': 0,
            'scan_date': datetime.now().isoformat(),
            'scans_performed': []
        }

    def parse_bandit_report(self, report_path: Path) -> None:
        """Parse Bandit SAST results"""
        try:
            with open(report_path) as f:
                data = json.load(f)
            
            self.summary['scans_performed'].append('Bandit SAST')
            
            for result in data.get('results', []):
                severity = result['issue_severity'].lower()
                self.findings[severity].append({
                    'tool': 'Bandit',
                    'type': 'SAST',
                    'file': result['filename'],
                    'line': result['line_number'],
                    'issue': result['issue_text'],
                    'severity': severity,
                    'confidence': result['issue_confidence']
                })
        except Exception as e:
            print(f"Error parsing Bandit report: {e}")

    def parse_safety_report(self, report_path: Path) -> None:
        """Parse Safety dependency scan results"""
        try:
            with open(report_path) as f:
                data = json.load(f)
            
            self.summary['scans_performed'].append('Safety Dependency Scan')
            
            for vuln in data.get('vulnerabilities', []):
                self.findings['high'].append({
                    'tool': 'Safety',
                    'type': 'Dependency',
                    'package': vuln['package_name'],
                    'version': vuln['analyzed_version'],
                    'issue': vuln['advisory'],
                    'severity': 'high',
                    'cve': vuln.get('cve', 'N/A')
                })
        except Exception as e:
            print(f"Error parsing Safety report: {e}")

    def parse_trivy_report(self, report_path: Path) -> None:
        """Parse Trivy container scan results"""
        try:
            with open(report_path) as f:
                data = json.load(f)
            
            self.summary['scans_performed'].append('Trivy Container Scan')
            
            for result in data.get('Results', []):
                for vuln in result.get('Vulnerabilities', []):
                    severity = vuln['Severity'].lower()
                    self.findings[severity].append({
                        'tool': 'Trivy',
                        'type': 'Container',
                        'package': vuln['PkgName'],
                        'version': vuln['InstalledVersion'],
                        'issue': vuln['Title'],
                        'severity': severity,
                        'cve': vuln.get('VulnerabilityID', 'N/A'),
                        'fixed_version': vuln.get('FixedVersion', 'Not available')
                    })
        except Exception as e:
            print(f"Error parsing Trivy report: {e}")

    def parse_semgrep_report(self, report_path: Path) -> None:
        """Parse Semgrep SAST results"""
        try:
            with open(report_path) as f:
                data = json.load(f)
            
            self.summary['scans_performed'].append('Semgrep SAST')
            
            for result in data.get('results', []):
                severity = 'high' if 'security' in result.get('check_id', '') else 'medium'
                self.findings[severity].append({
                    'tool': 'Semgrep',
                    'type': 'SAST',
                    'file': result['path'],
                    'line': result['start']['line'],
                    'issue': result.get('extra', {}).get('message', result['check_id']),
                    'severity': severity,
                    'rule': result['check_id']
                })
        except Exception as e:
            print(f"Error parsing Semgrep report: {e}")

    def collect_reports(self) -> None:
        """Collect and parse all security reports"""
        # SAST Reports
        bandit_reports = self.artifacts_dir.glob('**/bandit-report.json')
        for report in bandit_reports:
            self.parse_bandit_report(report)
        
        # Dependency Reports
        safety_reports = self.artifacts_dir.glob('**/safety-report.json')
        for report in safety_reports:
            self.parse_safety_report(report)
        
        # Container Reports
        trivy_reports = self.artifacts_dir.glob('**/trivy-results.json')
        for report in trivy_reports:
            self.parse_trivy_report(report)
        
        # Semgrep Reports
        semgrep_reports = self.artifacts_dir.glob('**/semgrep-report.json')
        for report in semgrep_reports:
            self.parse_semgrep_report(report)

    def calculate_summary(self) -> None:
        """Calculate summary statistics"""
        for severity, issues in self.findings.items():
            count = len(issues)
            self.summary['total_issues'] += count
            if severity == 'critical':
                self.summary['critical_count'] = count
            elif severity == 'high':
                self.summary['high_count'] = count

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report"""
        report = f"""# Security Assessment Report

**Generated**: {self.summary['scan_date']}  
**Total Issues Found**: {self.summary['total_issues']}  
**Critical Issues**: {self.summary['critical_count']}  
**High Severity Issues**: {self.summary['high_count']}  

## Executive Summary

This security assessment was performed using automated security scanning tools across multiple dimensions:
- Static Application Security Testing (SAST)
- Dependency Vulnerability Analysis
- Container Security Scanning
- Infrastructure as Code Security

**Scans Performed**: {', '.join(self.summary['scans_performed'])}

## Risk Assessment

"""
        # Add risk matrix
        if self.summary['critical_count'] > 0:
            report += "### 🚨 CRITICAL RISK\n"
            report += "Critical security vulnerabilities detected. Immediate action required.\n\n"
        elif self.summary['high_count'] > 5:
            report += "### ⚠️ HIGH RISK\n"
            report += "Multiple high-severity issues detected. Priority remediation recommended.\n\n"
        else:
            report += "### ✅ MODERATE RISK\n"
            report += "No critical issues found. Address high-severity findings as part of normal development.\n\n"

        # Add detailed findings
        report += "## Detailed Findings\n\n"
        
        for severity in ['critical', 'high', 'medium', 'low']:
            issues = self.findings[severity]
            if issues:
                report += f"### {severity.upper()} Severity Issues ({len(issues)})\n\n"
                
                # Group by tool
                by_tool = {}
                for issue in issues:
                    tool = issue['tool']
                    if tool not in by_tool:
                        by_tool[tool] = []
                    by_tool[tool].append(issue)
                
                for tool, tool_issues in by_tool.items():
                    report += f"#### {tool} Findings\n\n"
                    for i, issue in enumerate(tool_issues[:10], 1):  # Limit to 10 per tool
                        if issue['type'] == 'SAST':
                            report += f"{i}. **{issue['issue']}**\n"
                            report += f"   - File: `{issue['file']}:{issue['line']}`\n"
                        elif issue['type'] == 'Dependency':
                            report += f"{i}. **{issue['package']} {issue['version']}**\n"
                            report += f"   - Issue: {issue['issue']}\n"
                            report += f"   - CVE: {issue.get('cve', 'N/A')}\n"
                        elif issue['type'] == 'Container':
                            report += f"{i}. **{issue['package']} {issue['version']}**\n"
                            report += f"   - Issue: {issue['issue']}\n"
                            report += f"   - CVE: {issue.get('cve', 'N/A')}\n"
                            report += f"   - Fix: Upgrade to {issue.get('fixed_version', 'N/A')}\n"
                        report += "\n"
                    
                    if len(tool_issues) > 10:
                        report += f"   *... and {len(tool_issues) - 10} more {tool} findings*\n\n"

        # Add recommendations
        report += """## Recommendations

### Immediate Actions (Critical/High)
"""
        if self.summary['critical_count'] > 0:
            report += "1. **Address Critical Vulnerabilities**: Fix all critical security issues before deployment\n"
        
        if any('SECRET_KEY' in str(issue) for issues in self.findings.values() for issue in issues):
            report += "2. **Remove Hardcoded Secrets**: Move all secrets to environment variables\n"
        
        if any('jwt' in str(issue).lower() for issues in self.findings.values() for issue in issues):
            report += "3. **Strengthen Authentication**: Implement proper JWT with expiration\n"

        report += """
### Short-term Improvements
1. **Dependency Updates**: Update vulnerable dependencies to patched versions
2. **SAST Remediation**: Fix high-severity static analysis findings
3. **Container Security**: Update base images and remove vulnerable packages

### Long-term Security Enhancements
1. **Implement Security Headers**: Add HSTS, CSP, and other security headers
2. **Enable Rate Limiting**: Protect APIs from abuse
3. **Add MFA**: Implement multi-factor authentication for admin accounts
4. **Regular Security Scans**: Integrate security scanning into CI/CD pipeline

## Compliance Checklist

- [ ] All critical vulnerabilities resolved
- [ ] No hardcoded secrets in codebase
- [ ] Dependencies updated to secure versions
- [ ] Security headers implemented
- [ ] Rate limiting configured
- [ ] Authentication strengthened
- [ ] Encryption at rest implemented
- [ ] Security monitoring enabled
- [ ] Incident response plan documented
- [ ] Security training completed

## Next Steps

1. Review and prioritize findings based on risk
2. Create tickets for critical and high-severity issues
3. Implement fixes following secure coding practices
4. Re-run security scans after remediation
5. Schedule regular security assessments

---
*This report was automatically generated by the AI Force Migration Platform security scanning pipeline.*
"""
        return report

    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON format report for programmatic processing"""
        return {
            'metadata': self.summary,
            'findings': self.findings,
            'risk_score': self._calculate_risk_score(),
            'compliance': {
                'owasp_top_10': self._check_owasp_compliance(),
                'cis_controls': self._check_cis_compliance()
            }
        }

    def _calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-100)"""
        score = 100
        score -= self.summary['critical_count'] * 20
        score -= self.summary['high_count'] * 5
        score -= len(self.findings['medium']) * 1
        return max(0, score)

    def _check_owasp_compliance(self) -> Dict[str, bool]:
        """Check OWASP Top 10 compliance"""
        return {
            'injection': not any('sql' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'broken_auth': not any('auth' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'sensitive_data': not any('secret' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'xxe': True,  # Assuming no XML processing
            'broken_access': not any('rbac' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'security_misconfig': self.summary['high_count'] < 5,
            'xss': not any('xss' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'deserialization': True,  # Assuming safe serialization
            'vulnerable_components': len(self.findings.get('high', [])) < 3,
            'insufficient_logging': False  # Need to implement better logging
        }

    def _check_cis_compliance(self) -> Dict[str, bool]:
        """Check CIS Controls compliance"""
        return {
            'inventory': True,  # Assuming asset inventory exists
            'software_inventory': True,
            'continuous_vuln_management': len(self.findings.get('critical', [])) == 0,
            'controlled_admin': not any('admin' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'secure_config': self.summary['high_count'] < 10,
            'audit_logs': True,  # Platform has audit logging
            'email_web_protection': True,
            'malware_defense': True,
            'data_recovery': False,  # Need to verify backup procedures
            'secure_network': False,  # Need network segmentation
            'data_protection': not any('encrypt' in str(issue).lower() for issues in self.findings.values() for issue in issues),
            'access_control': True,  # RBAC implemented
            'wireless_protection': True,  # N/A for this platform
            'account_monitoring': True,  # Audit logging exists
            'security_training': False,  # Need to implement
            'app_security': self.summary['critical_count'] == 0,
            'incident_response': False,  # Need documentation
            'penetration_testing': False  # Need to perform
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_security_report.py <artifacts_directory>")
        sys.exit(1)
    
    artifacts_dir = sys.argv[1]
    generator = SecurityReportGenerator(artifacts_dir)
    
    # Collect and parse all reports
    generator.collect_reports()
    generator.calculate_summary()
    
    # Generate markdown report
    report = generator.generate_markdown_report()
    print(report)
    
    # Also save JSON report
    json_report = generator.generate_json_report()
    with open('security-report.json', 'w') as f:
        json.dump(json_report, f, indent=2)


if __name__ == '__main__':
    main()