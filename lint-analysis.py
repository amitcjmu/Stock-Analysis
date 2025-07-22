#!/usr/bin/env python3
"""
Lint Analysis Script for Migration UI Orchestrator
Analyzes ESLint output to categorize issues by priority and type
"""

import subprocess
import re
import json
from collections import defaultdict, Counter
from pathlib import Path

def run_eslint():
    """Run ESLint and capture output"""
    try:
        result = subprocess.run(
            ['npm', 'run', 'lint'], 
            capture_output=True, 
            text=True, 
            cwd='/Users/chocka/CursorProjects/migrate-ui-orchestrator'
        )
        # ESLint outputs to stderr when there are errors
        output = result.stderr if result.stderr else result.stdout
        print(f"ESLint return code: {result.returncode}")
        print(f"Output length: {len(output)}")
        return output
    except Exception as e:
        print(f"Error running ESLint: {e}")
        return ""

def parse_eslint_output(output):
    """Parse ESLint output and extract structured data"""
    lines = output.split('\n')
    
    issues = []
    current_file = None
    
    for line in lines:
        line = line.strip()
        
        # File path line
        if line.startswith('/Users/chocka/CursorProjects/migrate-ui-orchestrator/'):
            current_file = line
            continue
            
        # Issue line
        if re.match(r'^\s*\d+:\d+\s+(error|warning)', line):
            if current_file:
                match = re.match(r'^\s*(\d+):(\d+)\s+(error|warning)\s+(.+)', line)
                if match:
                    line_num, col_num, severity, message = match.groups()
                    
                    # Extract rule name if present
                    rule_match = re.search(r'([a-zA-Z/-]+)$', message)
                    rule = rule_match.group(1) if rule_match else 'unknown'
                    
                    issues.append({
                        'file': current_file,
                        'line': int(line_num),
                        'column': int(col_num),
                        'severity': severity,
                        'message': message,
                        'rule': rule
                    })
    
    return issues

def categorize_issues(issues):
    """Categorize issues by priority and type"""
    
    # Issue categories
    categories = {
        'critical': {
            'rules': ['Parsing error', 'syntax error', 'expected'],
            'keywords': ['parsing error', 'syntax error', 'unexpected token', 'expected']
        },
        'high': {
            'rules': ['react-hooks/rules-of-hooks', 'no-case-declarations'],
            'keywords': ['react hook', 'hooks must be called', 'lexical declaration']
        },
        'medium': {
            'rules': ['@typescript-eslint/no-explicit-any', 'react-hooks/exhaustive-deps', 
                     '@typescript-eslint/no-namespace', '@typescript-eslint/no-require-imports'],
            'keywords': ['unexpected any', 'missing dependency', 'namespace', 'require()']
        },
        'low': {
            'rules': ['react-refresh/only-export-components', 'prefer-const', 'no-useless-catch'],
            'keywords': ['fast refresh', 'never reassigned', 'unnecessary try/catch']
        }
    }
    
    categorized = defaultdict(list)
    
    for issue in issues:
        message_lower = issue['message'].lower()
        rule_lower = issue['rule'].lower()
        
        assigned = False
        
        # Check each category
        for category, criteria in categories.items():
            # Check rules
            for rule in criteria['rules']:
                if rule.lower() in rule_lower or rule.lower() in message_lower:
                    categorized[category].append(issue)
                    assigned = True
                    break
            
            if assigned:
                break
                
            # Check keywords
            for keyword in criteria['keywords']:
                if keyword in message_lower:
                    categorized[category].append(issue)
                    assigned = True
                    break
            
            if assigned:
                break
        
        if not assigned:
            categorized['other'].append(issue)
    
    return categorized

def analyze_files(issues):
    """Analyze files with most issues"""
    file_counts = Counter()
    
    for issue in issues:
        file_path = issue['file']
        # Extract relative path
        relative_path = file_path.replace('/Users/chocka/CursorProjects/migrate-ui-orchestrator/', '')
        file_counts[relative_path] += 1
    
    return file_counts

def analyze_rules(issues):
    """Analyze most common rules"""
    rule_counts = Counter()
    
    for issue in issues:
        rule_counts[issue['rule']] += 1
    
    return rule_counts

def generate_report(issues, categorized, file_counts, rule_counts):
    """Generate comprehensive report"""
    
    total_issues = len(issues)
    total_errors = sum(1 for issue in issues if issue['severity'] == 'error')
    total_warnings = sum(1 for issue in issues if issue['severity'] == 'warning')
    
    report = f"""
# ESLint Analysis Report - Migration UI Orchestrator

## Executive Summary
- **Total Issues**: {total_issues:,}
- **Total Errors**: {total_errors:,}
- **Total Warnings**: {total_warnings:,}

## Issue Categorization by Priority

### 1. Critical/Blocking Issues (Compilation Blockers)
**Count**: {len(categorized['critical'])}
**Impact**: These prevent successful compilation and must be fixed immediately.

Common Issues:
"""
    
    # Critical issues details
    critical_rules = Counter(issue['rule'] for issue in categorized['critical'])
    for rule, count in critical_rules.most_common(5):
        report += f"- {rule}: {count} occurrences\n"
    
    report += f"""
### 2. High Priority Issues (Runtime/Logic Errors)
**Count**: {len(categorized['high'])}
**Impact**: These can cause runtime errors or incorrect behavior.

Common Issues:
"""
    
    # High priority issues
    high_rules = Counter(issue['rule'] for issue in categorized['high'])
    for rule, count in high_rules.most_common(5):
        report += f"- {rule}: {count} occurrences\n"
    
    report += f"""
### 3. Medium Priority Issues (Type Safety & Code Quality)
**Count**: {len(categorized['medium'])}
**Impact**: These affect type safety, maintainability, and code quality.

Common Issues:
"""
    
    # Medium priority issues
    medium_rules = Counter(issue['rule'] for issue in categorized['medium'])
    for rule, count in medium_rules.most_common(5):
        report += f"- {rule}: {count} occurrences\n"
    
    report += f"""
### 4. Low Priority Issues (Style & Conventions)
**Count**: {len(categorized['low'])}
**Impact**: These are style and convention issues with minimal functional impact.

Common Issues:
"""
    
    # Low priority issues
    low_rules = Counter(issue['rule'] for issue in categorized['low'])
    for rule, count in low_rules.most_common(5):
        report += f"- {rule}: {count} occurrences\n"
    
    report += """
## Most Problematic Files (Top 20)
"""
    
    for file_path, count in file_counts.most_common(20):
        report += f"- {file_path}: {count} issues\n"
    
    report += """
## Most Common Issue Types (Top 15)
"""
    
    for rule, count in rule_counts.most_common(15):
        report += f"- {rule}: {count} occurrences\n"
    
    # Specific analysis sections
    report += f"""
## Detailed Analysis

### TypeScript Issues
- **`@typescript-eslint/no-explicit-any`**: {rule_counts.get('@typescript-eslint/no-explicit-any', 0)} occurrences
  - Impact: Poor type safety, potential runtime errors
  - Fix: Replace `any` with proper type definitions

### React Issues
- **React Hooks violations**: {rule_counts.get('react-hooks/rules-of-hooks', 0)} occurrences
  - Impact: Breaks React's rules of hooks, can cause crashes
  - Fix: Move hooks to component root level, fix conditional hooks

- **Missing Dependencies**: {rule_counts.get('react-hooks/exhaustive-deps', 0)} occurrences
  - Impact: Stale closures, incorrect behavior
  - Fix: Add missing dependencies or use callback patterns

### Parsing/Syntax Errors
- **Parsing Errors**: {len([i for i in issues if 'parsing error' in i['message'].lower()])} occurrences
  - Impact: Prevents compilation
  - Fix: Fix syntax errors, missing punctuation

### Security/Import Issues
- **require() imports**: {rule_counts.get('@typescript-eslint/no-require-imports', 0)} occurrences
  - Impact: Inconsistent module system usage
  - Fix: Convert to ES6 imports

## Recommendations

### Immediate Action Required (Critical/High Priority)
1. **Fix all parsing errors** - These prevent compilation
2. **Resolve React Hook violations** - These cause runtime crashes
3. **Address case declaration issues** - These are syntax errors

### Short-term Goals (Medium Priority)
1. **Implement proper TypeScript types** - Replace `any` with specific types
2. **Fix React Hook dependencies** - Add missing dependencies
3. **Modernize imports** - Convert require() to ES6 imports

### Long-term Improvements (Low Priority)
1. **Code style consistency** - Fix prefer-const and similar issues
2. **Component organization** - Address react-refresh violations
3. **Error handling** - Remove unnecessary try/catch wrappers

## Files Requiring Immediate Attention
"""
    
    # Show critical files
    critical_files = set()
    for issue in categorized['critical'] + categorized['high']:
        relative_path = issue['file'].replace('/Users/chocka/CursorProjects/migrate-ui-orchestrator/', '')
        critical_files.add(relative_path)
    
    for file_path in sorted(critical_files):
        critical_count = sum(1 for issue in categorized['critical'] if issue['file'].endswith(file_path))
        high_count = sum(1 for issue in categorized['high'] if issue['file'].endswith(file_path))
        if critical_count > 0 or high_count > 0:
            report += f"- {file_path}: {critical_count} critical, {high_count} high priority\n"
    
    return report

def main():
    """Main analysis function"""
    print("Running ESLint analysis...")
    
    # Run ESLint
    output = run_eslint()
    
    if not output:
        print("No ESLint output captured")
        return
    
    # Parse output
    issues = parse_eslint_output(output)
    print(f"Parsed {len(issues)} issues")
    
    # Categorize issues
    categorized = categorize_issues(issues)
    
    # Analyze files and rules
    file_counts = analyze_files(issues)
    rule_counts = analyze_rules(issues)
    
    # Generate report
    report = generate_report(issues, categorized, file_counts, rule_counts)
    
    # Write report
    with open('/Users/chocka/CursorProjects/migrate-ui-orchestrator/lint-analysis-report.md', 'w') as f:
        f.write(report)
    
    print("Analysis complete! Report saved to lint-analysis-report.md")
    print(f"Total issues analyzed: {len(issues)}")
    print(f"Critical: {len(categorized['critical'])}")
    print(f"High: {len(categorized['high'])}")
    print(f"Medium: {len(categorized['medium'])}")
    print(f"Low: {len(categorized['low'])}")

if __name__ == "__main__":
    main()