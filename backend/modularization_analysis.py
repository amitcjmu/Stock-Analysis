#!/usr/bin/env python3
"""
Comprehensive Modularization Analysis Tool
Analyzes code files for size, complexity, and provides refactoring recommendations.
CC generated for comprehensive codebase analysis.
"""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class FileMetrics:
    path: str
    file_type: str
    line_count: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    complexity_score: int
    priority: str
    refactoring_suggestions: List[str]

class ModularizationAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.file_metrics: List[FileMetrics] = []
        self.exclude_patterns = [
            'venv', 'node_modules', '.git', '__pycache__', 'dist', 'build',
            'postgres-data-volume', 'test-results', 'monitoring', 'observability',
            'temp', 'backups'
        ]
        
        # LOC thresholds
        self.thresholds = {
            'critical': 500,
            'high': 400,
            'medium': 350,
            'acceptable': 300
        }
        
        # File type configurations
        self.file_types = {
            '.py': {'name': 'Python', 'patterns': ['*.py']},
            '.ts': {'name': 'TypeScript', 'patterns': ['*.ts']},
            '.tsx': {'name': 'React TypeScript', 'patterns': ['*.tsx']},
            '.js': {'name': 'JavaScript', 'patterns': ['*.js']},
            '.jsx': {'name': 'React JavaScript', 'patterns': ['*.jsx']},
            '.json': {'name': 'JSON Config', 'patterns': ['*.json']},
            '.yml': {'name': 'YAML Config', 'patterns': ['*.yml', '*.yaml']},
            '.sql': {'name': 'SQL Migration', 'patterns': ['*.sql']},
            '.md': {'name': 'Documentation', 'patterns': ['*.md']},
            '.sh': {'name': 'Shell Script', 'patterns': ['*.sh', '*.bash']},
            '.css': {'name': 'CSS Styles', 'patterns': ['*.css', '*.scss']}
        }

    def should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded from analysis."""
        return any(pattern in str(path) for pattern in self.exclude_patterns)

    def count_lines(self, file_path: Path) -> Tuple[int, int, int, int]:
        """Count total, blank, comment, and code lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            blank_lines = 0
            comment_lines = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif self.is_comment_line(stripped, file_path.suffix):
                    comment_lines += 1
            
            code_lines = total_lines - blank_lines - comment_lines
            return total_lines, blank_lines, comment_lines, code_lines
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0, 0, 0, 0

    def is_comment_line(self, line: str, file_extension: str) -> bool:
        """Determine if a line is a comment based on file type."""
        comment_markers = {
            '.py': ['#', '"""', "'''"],
            '.js': ['//', '/*', '*/', '/**'],
            '.jsx': ['//', '/*', '*/', '/**'],
            '.ts': ['//', '/*', '*/', '/**'],
            '.tsx': ['//', '/*', '*/', '/**'],
            '.css': ['/*', '*/'],
            '.sh': ['#'],
            '.sql': ['--', '/*', '*/'],
            '.yml': ['#'],
            '.yaml': ['#']
        }
        
        markers = comment_markers.get(file_extension, [])
        return any(line.startswith(marker) for marker in markers)

    def calculate_complexity_score(self, file_path: Path, code_lines: int) -> int:
        """Calculate complexity score based on file content analysis."""
        complexity = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic complexity indicators
            complexity_patterns = {
                'if ': 1, 'elif ': 1, 'else:': 1,
                'for ': 2, 'while ': 2,
                'try:': 2, 'except': 2,
                'def ': 3, 'class ': 4,
                'async def': 4, 'lambda': 1,
                '&&': 1, '||': 1, 'switch': 3,
                'case ': 1, 'useEffect': 2, 'useState': 1,
                'useCallback': 2, 'useMemo': 2
            }
            
            for pattern, weight in complexity_patterns.items():
                complexity += content.count(pattern) * weight
            
            # Nested structure penalty
            nesting_level = 0
            max_nesting = 0
            for line in content.split('\n'):
                stripped = line.strip()
                if any(keyword in stripped for keyword in ['if ', 'for ', 'while ', 'def ', 'class ', 'try:']):
                    nesting_level += 1
                    max_nesting = max(max_nesting, nesting_level)
                elif stripped in ['end', '}', 'else:', 'except:', 'finally:']:
                    nesting_level = max(0, nesting_level - 1)
            
            complexity += max_nesting * 5
            
            # Length penalty
            if code_lines > 500:
                complexity += 50
            elif code_lines > 300:
                complexity += 20
            
            return complexity
            
        except Exception:
            return code_lines // 10  # Fallback to basic length-based complexity

    def generate_refactoring_suggestions(self, file_path: Path, metrics: Dict) -> List[str]:
        """Generate specific refactoring suggestions based on file analysis."""
        suggestions = []
        code_lines = metrics['code_lines']
        file_extension = file_path.suffix
        
        # General size-based suggestions
        if code_lines > 500:
            suggestions.append("CRITICAL: Split into multiple smaller modules (target <200 LOC each)")
            suggestions.append("Extract utility functions into separate helper modules")
            suggestions.append("Consider implementing facade or adapter patterns")
        elif code_lines > 400:
            suggestions.append("HIGH: Break down into 2-3 focused modules")
            suggestions.append("Extract complex logic into separate service classes")
        elif code_lines > 350:
            suggestions.append("MEDIUM: Consider extracting reusable components or utilities")
        
        # File-type specific suggestions
        if file_extension == '.py':
            suggestions.extend(self.get_python_suggestions(file_path, code_lines))
        elif file_extension in ['.ts', '.tsx']:
            suggestions.extend(self.get_typescript_suggestions(file_path, code_lines))
        elif file_extension in ['.js', '.jsx']:
            suggestions.extend(self.get_javascript_suggestions(file_path, code_lines))
        
        return suggestions

    def get_python_suggestions(self, file_path: Path, code_lines: int) -> List[str]:
        """Python-specific refactoring suggestions."""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            class_count = content.count('class ')
            function_count = content.count('def ')
            
            if class_count > 3:
                suggestions.append("Split multiple classes into separate files")
            if function_count > 10:
                suggestions.append("Group related functions into classes or modules")
            if 'FastAPI' in content or '@app.' in content:
                suggestions.append("Extract API endpoints into separate route modules")
            if 'SQLAlchemy' in content or 'session.' in content:
                suggestions.append("Separate database models and business logic")
            if content.count('import ') > 20:
                suggestions.append("Reduce dependencies by splitting functionality")
        
        except Exception:
            pass
        
        return suggestions

    def get_typescript_suggestions(self, file_path: Path, code_lines: int) -> List[str]:
        """TypeScript/React specific suggestions."""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            component_count = content.count('function ') + content.count('const ') + content.count('export ')
            hook_count = content.count('use')
            
            if 'useState' in content and content.count('useState') > 5:
                suggestions.append("Consider using useReducer for complex state management")
            if 'useEffect' in content and content.count('useEffect') > 3:
                suggestions.append("Extract side effects into custom hooks")
            if component_count > 5:
                suggestions.append("Split into separate component files")
            if hook_count > 8:
                suggestions.append("Extract custom hooks into separate files")
            if 'return (' in content and len(content.split('return (')[1].split(')')[0]) > 1000:
                suggestions.append("Break down JSX into smaller sub-components")
        
        except Exception:
            pass
        
        return suggestions

    def get_javascript_suggestions(self, file_path: Path, code_lines: int) -> List[str]:
        """JavaScript specific suggestions."""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if 'export ' in content and content.count('export ') > 5:
                suggestions.append("Split exports into focused modules")
            if content.count('function ') > 8:
                suggestions.append("Group related functions into classes or modules")
            if content.count('addEventListener') > 3:
                suggestions.append("Extract event handling into separate module")
        
        except Exception:
            pass
        
        return suggestions

    def get_priority_level(self, code_lines: int) -> str:
        """Determine priority level based on line count."""
        if code_lines >= self.thresholds['critical']:
            return 'Critical'
        elif code_lines >= self.thresholds['high']:
            return 'High'
        elif code_lines >= self.thresholds['medium']:
            return 'Medium'
        else:
            return 'Low'

    def analyze_file(self, file_path: Path) -> FileMetrics:
        """Analyze a single file and return metrics."""
        total_lines, blank_lines, comment_lines, code_lines = self.count_lines(file_path)
        complexity = self.calculate_complexity_score(file_path, code_lines)
        
        metrics_dict = {
            'code_lines': code_lines,
            'total_lines': total_lines,
            'blank_lines': blank_lines,
            'comment_lines': comment_lines
        }
        
        suggestions = self.generate_refactoring_suggestions(file_path, metrics_dict)
        priority = self.get_priority_level(code_lines)
        
        file_type = self.file_types.get(file_path.suffix, {}).get('name', 'Unknown')
        
        return FileMetrics(
            path=str(file_path.relative_to(self.root_path)),
            file_type=file_type,
            line_count=total_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            code_lines=code_lines,
            complexity_score=complexity,
            priority=priority,
            refactoring_suggestions=suggestions
        )

    def find_source_files(self) -> List[Path]:
        """Find all source code files in the repository."""
        source_files = []
        
        for ext, config in self.file_types.items():
            for pattern in config['patterns']:
                for file_path in self.root_path.rglob(pattern):
                    if file_path.is_file() and not self.should_exclude_path(file_path):
                        source_files.append(file_path)
        
        return sorted(source_files)

    def analyze_repository(self) -> Dict[str, Any]:
        """Perform comprehensive repository analysis."""
        print("Starting comprehensive modularization analysis...")
        
        source_files = self.find_source_files()
        print(f"Found {len(source_files)} source files to analyze")
        
        for file_path in source_files:
            try:
                metrics = self.analyze_file(file_path)
                if metrics.code_lines > 0:  # Only include files with actual code
                    self.file_metrics.append(metrics)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        # Filter files exceeding threshold
        oversized_files = [f for f in self.file_metrics if f.code_lines >= self.thresholds['medium']]
        
        # Group by file type
        by_type = defaultdict(list)
        for file_metric in self.file_metrics:
            by_type[file_metric.file_type].append(file_metric)
        
        # Group by priority
        by_priority = defaultdict(list)
        for file_metric in oversized_files:
            by_priority[file_metric.priority].append(file_metric)
        
        # Calculate statistics
        total_files = len(self.file_metrics)
        oversized_count = len(oversized_files)
        compliance_rate = ((total_files - oversized_count) / total_files * 100) if total_files > 0 else 100
        
        # Top offenders
        top_offenders = sorted(oversized_files, key=lambda x: x.code_lines, reverse=True)[:20]
        
        report = {
            'summary': {
                'total_files_analyzed': total_files,
                'files_exceeding_threshold': oversized_count,
                'compliance_rate': round(compliance_rate, 2),
                'thresholds': self.thresholds
            },
            'by_file_type': {
                file_type: {
                    'total_files': len(files),
                    'oversized_files': len([f for f in files if f.code_lines >= self.thresholds['medium']]),
                    'avg_code_lines': round(sum(f.code_lines for f in files) / len(files), 2) if files else 0,
                    'max_code_lines': max(f.code_lines for f in files) if files else 0
                }
                for file_type, files in by_type.items()
            },
            'by_priority': {
                priority: len(files) for priority, files in by_priority.items()
            },
            'top_offenders': [asdict(f) for f in top_offenders],
            'detailed_analysis': [asdict(f) for f in oversized_files]
        }
        
        return report

    def save_report(self, report: Dict[str, Any], output_file: str = "modularization_analysis_report.json"):
        """Save the analysis report to a JSON file."""
        output_path = self.root_path / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to: {output_path}")

def main():
    # Analyze the repository
    analyzer = ModularizationAnalyzer('/Users/chocka/CursorProjects/migrate-ui-orchestrator')
    report = analyzer.analyze_repository()
    
    # Save detailed JSON report
    analyzer.save_report(report)
    
    # Print summary
    print("\n" + "="*80)
    print("MODULARIZATION ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Files exceeding 350 LOC threshold: {report['summary']['files_exceeding_threshold']}")
    print(f"Compliance rate: {report['summary']['compliance_rate']}%")
    
    print("\nBy Priority:")
    for priority, count in report['by_priority'].items():
        print(f"  {priority}: {count} files")
    
    print("\nTop 10 Files Requiring Immediate Attention:")
    for i, file_info in enumerate(report['top_offenders'][:10], 1):
        print(f"  {i:2d}. {file_info['path']} ({file_info['code_lines']} LOC, {file_info['priority']} priority)")
    
    print("\nDetailed report saved to: modularization_analysis_report.json")

if __name__ == "__main__":
    main()