/**
 * Security validation utilities for production readiness checks
 * CC - Comprehensive security validation framework
 */

interface SecurityCheckResult {
  passed: boolean;
  issues: string[];
  critical: string[];
  warnings: string[];
}

export class SecurityValidator {
  /**
   * Validate that no sensitive console.log statements exist in production code
   */
  static validateNoSensitiveLogging(codeContent: string, fileName: string): SecurityCheckResult {
    const result: SecurityCheckResult = {
      passed: true,
      issues: [],
      critical: [],
      warnings: []
    };

    // Check for console.log statements
    const consoleLogMatches = codeContent.match(/console\.(log|debug|info|warn|error)/g);
    if (consoleLogMatches) {
      consoleLogMatches.forEach(match => {
        result.critical.push(`${fileName}: Found ${match} statement - use SecureLogger instead`);
        result.passed = false;
      });
    }

    // Check for sensitive data patterns in logging
    const sensitiveDataPatterns = [
      /console\.\w+\([^)]*(?:flow_id|client_account_id|engagement_id|user_id|api_key|token|password)/gi,
      /console\.\w+\([^)]*(?:raw_data|field_mappings|import_metadata)/gi
    ];

    sensitiveDataPatterns.forEach(pattern => {
      const matches = codeContent.match(pattern);
      if (matches) {
        matches.forEach(match => {
          result.critical.push(`${fileName}: Sensitive data logging detected: ${match.substring(0, 50)}...`);
          result.passed = false;
        });
      }
    });

    return result;
  }

  /**
   * Validate secure localStorage usage
   */
  static validateSecureStorage(codeContent: string, fileName: string): SecurityCheckResult {
    const result: SecurityCheckResult = {
      passed: true,
      issues: [],
      critical: [],
      warnings: []
    };

    // Check for direct localStorage usage
    const localStorageMatches = codeContent.match(/localStorage\.(setItem|getItem|removeItem)/g);
    if (localStorageMatches) {
      localStorageMatches.forEach(match => {
        result.critical.push(`${fileName}: Direct localStorage usage found: ${match} - use SecureStorage instead`);
        result.passed = false;
      });
    }

    // Check for unsanitized data storage
    const unsanitizedStoragePatterns = [
      /localStorage\.setItem\([^,]+,\s*[^)]*(?:urlFlowId|pathFlowId|flowId)\s*\)/gi
    ];

    unsanitizedStoragePatterns.forEach(pattern => {
      const matches = codeContent.match(pattern);
      if (matches) {
        matches.forEach(match => {
          result.critical.push(`${fileName}: Unsanitized data storage: ${match}`);
          result.passed = false;
        });
      }
    });

    return result;
  }

  /**
   * Validate URL parameter handling security
   */
  static validateUrlParameterSecurity(codeContent: string, fileName: string): SecurityCheckResult {
    const result: SecurityCheckResult = {
      passed: true,
      issues: [],
      critical: [],
      warnings: []
    };

    // Check for direct URL parameter usage without validation
    const unsafeUrlPatterns = [
      /urlParams\.get\([^)]+\)(?!\s*;\s*.*validateUrlFlowId)/gi,
      /pathMatch\[1\](?!\s*;\s*.*validateUrlFlowId)/gi,
      /window\.location\.(?:search|pathname|href)(?!.*validate)/gi
    ];

    unsafeUrlPatterns.forEach(pattern => {
      const matches = codeContent.match(pattern);
      if (matches) {
        matches.forEach(match => {
          result.warnings.push(`${fileName}: Potentially unsafe URL parameter usage: ${match}`);
        });
      }
    });

    return result;
  }

  /**
   * Validate that SecureLogger is used instead of console
   */
  static validateSecureLoggerUsage(codeContent: string, fileName: string): SecurityCheckResult {
    const result: SecurityCheckResult = {
      passed: true,
      issues: [],
      critical: [],
      warnings: []
    };

    // Check for SecureLogger import
    const hasSecureLoggerImport = /import\s+SecureLogger\s+from/.test(codeContent);
    const hasLoggingCalls = /SecureLogger\.(debug|info|warn|error)/.test(codeContent);

    if (hasLoggingCalls && !hasSecureLoggerImport) {
      result.critical.push(`${fileName}: SecureLogger calls found but import missing`);
      result.passed = false;
    }

    return result;
  }

  /**
   * Run comprehensive security validation
   */
  static runFullSecurityCheck(codeContent: string, fileName: string): SecurityCheckResult {
    const checks = [
      this.validateNoSensitiveLogging(codeContent, fileName),
      this.validateSecureStorage(codeContent, fileName),
      this.validateUrlParameterSecurity(codeContent, fileName),
      this.validateSecureLoggerUsage(codeContent, fileName)
    ];

    const combinedResult: SecurityCheckResult = {
      passed: true,
      issues: [],
      critical: [],
      warnings: []
    };

    checks.forEach(check => {
      if (!check.passed) {
        combinedResult.passed = false;
      }
      combinedResult.issues.push(...check.issues);
      combinedResult.critical.push(...check.critical);
      combinedResult.warnings.push(...check.warnings);
    });

    return combinedResult;
  }

  /**
   * Generate security report
   */
  static generateSecurityReport(results: { [fileName: string]: SecurityCheckResult }): string {
    let report = "🔒 SECURITY VALIDATION REPORT\n";
    report += "=" + "=".repeat(50) + "\n\n";

    let totalCritical = 0;
    let totalWarnings = 0;
    let allPassed = true;

    Object.entries(results).forEach(([fileName, result]) => {
      if (!result.passed) {
        allPassed = false;
      }

      totalCritical += result.critical.length;
      totalWarnings += result.warnings.length;

      if (result.critical.length > 0 || result.warnings.length > 0) {
        report += `📄 ${fileName}\n`;
        report += "-".repeat(30) + "\n";

        if (result.critical.length > 0) {
          report += "🔴 CRITICAL ISSUES:\n";
          result.critical.forEach(issue => {
            report += `  - ${issue}\n`;
          });
          report += "\n";
        }

        if (result.warnings.length > 0) {
          report += "🟡 WARNINGS:\n";
          result.warnings.forEach(warning => {
            report += `  - ${warning}\n`;
          });
          report += "\n";
        }
      }
    });

    report += "\n📊 SUMMARY\n";
    report += "-".repeat(20) + "\n";
    report += `Total Critical Issues: ${totalCritical}\n`;
    report += `Total Warnings: ${totalWarnings}\n`;
    report += `Overall Status: ${allPassed ? "✅ PASSED" : "❌ FAILED"}\n`;

    if (!allPassed) {
      report += "\n⚠️  PRODUCTION DEPLOYMENT BLOCKED\n";
      report += "Critical security issues must be resolved before deployment.\n";
    } else {
      report += "\n✅ READY FOR PRODUCTION\n";
      report += "All security checks passed.\n";
    }

    return report;
  }
}

export default SecurityValidator;
