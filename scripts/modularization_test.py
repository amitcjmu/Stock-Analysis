#!/usr/bin/env python3
"""
Modularization Testing Script

This script analyzes all code files in the repository and identifies files that exceed
the 300-400 lines of code (LOC) standard, providing detailed categorization and
actionable recommendations for refactoring.

Usage:
    python scripts/modularization_test.py
    python scripts/modularization_test.py --threshold 400
    python scripts/modularization_test.py --detailed
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json

class FileCategory(Enum):
    BACKEND_PYTHON = "Backend Python"
    FRONTEND_TYPESCRIPT = "Frontend TypeScript"
    FRONTEND_JAVASCRIPT = "Frontend JavaScript"
    FRONTEND_REACT = "Frontend React"
    FRONTEND_STYLES = "Frontend Styles"
    CONFIG = "Configuration"
    MIGRATION = "Database Migration"
    DOCUMENTATION = "Documentation"
    SCRIPTS = "Scripts"
    TESTS = "Tests"
    OTHER = "Other"

@dataclass
class FileAnalysis:
    path: str
    category: FileCategory
    lines_count: int
    functions_count: int
    classes_count: int
    complexity_score: float
    recommendations: List[str]

class ModularizationTester:
    """Analyzes repository files for modularization compliance."""
    
    def __init__(self, repo_root: str, threshold: int = 350):
        self.repo_root = Path(repo_root)
        self.threshold = threshold
        self.analysis_results: List[FileAnalysis] = []
        
        # File extensions to analyze
        self.code_extensions = {
            '.py': FileCategory.BACKEND_PYTHON,
            '.ts': FileCategory.FRONTEND_TYPESCRIPT,
            '.tsx': FileCategory.FRONTEND_REACT,
            '.js': FileCategory.FRONTEND_JAVASCRIPT,
            '.jsx': FileCategory.FRONTEND_REACT,
            '.css': FileCategory.FRONTEND_STYLES,
            '.scss': FileCategory.FRONTEND_STYLES,
            '.sql': FileCategory.MIGRATION,
            '.md': FileCategory.DOCUMENTATION,
            '.json': FileCategory.CONFIG,
            '.yaml': FileCategory.CONFIG,
            '.yml': FileCategory.CONFIG,
            '.sh': FileCategory.SCRIPTS,
            '.bash': FileCategory.SCRIPTS,
        }
        
        # Directories to skip
        self.skip_dirs = {
            'node_modules', '.git', '__pycache__', '.pytest_cache', 
            'dist', 'build', '.next', 'coverage', '.venv', 'venv',
            'migrations', 'alembic/versions'  # Skip auto-generated migrations
        }
        
        # Files to skip
        self.skip_files = {
            'package-lock.json', 'yarn.lock', '.env', '.env.local',
            'CHANGELOG.md', 'README.md'  # Skip large documentation files
        }

    def categorize_file(self, file_path: Path) -> FileCategory:
        """Categorize a file based on its path and extension."""
        suffix = file_path.suffix.lower()
        path_str = str(file_path).lower()
        
        # Special path-based categorization
        if 'test' in path_str or 'spec' in path_str:
            return FileCategory.TESTS
        elif 'migration' in path_str or 'alembic' in path_str:
            return FileCategory.MIGRATION
        elif 'script' in path_str:
            return FileCategory.SCRIPTS
        elif 'backend' in path_str and suffix == '.py':
            return FileCategory.BACKEND_PYTHON
        elif any(frontend_dir in path_str for frontend_dir in ['frontend', 'src', 'components', 'pages']):
            if suffix in ['.ts', '.tsx']:
                return FileCategory.FRONTEND_TYPESCRIPT if suffix == '.ts' else FileCategory.FRONTEND_REACT
            elif suffix in ['.js', '.jsx']:
                return FileCategory.FRONTEND_JAVASCRIPT if suffix == '.js' else FileCategory.FRONTEND_REACT
        
        # Fallback to extension-based categorization
        return self.code_extensions.get(suffix, FileCategory.OTHER)

    def count_lines(self, file_path: Path) -> int:
        """Count non-empty, non-comment lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            non_empty_lines = 0
            in_multiline_comment = False
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    continue
                
                # Handle Python multiline comments
                if file_path.suffix == '.py':
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                            in_multiline_comment = not in_multiline_comment
                        continue
                    elif in_multiline_comment:
                        if stripped.endswith('"""') or stripped.endswith("'''"):
                            in_multiline_comment = False
                        continue
                    elif stripped.startswith('#'):
                        continue
                
                # Handle TypeScript/JavaScript comments
                elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                    if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                        continue
                
                # Handle CSS comments
                elif file_path.suffix in ['.css', '.scss']:
                    if stripped.startswith('/*') or stripped.startswith('*'):
                        continue
                
                non_empty_lines += 1
            
            return non_empty_lines
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return 0

    def analyze_file_complexity(self, file_path: Path) -> Tuple[int, int, float]:
        """Analyze file complexity: function count, class count, complexity score."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            functions_count = 0
            classes_count = 0
            complexity_score = 0.0
            
            lines = content.split('\n')
            
            if file_path.suffix == '.py':
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('def '):
                        functions_count += 1
                    elif stripped.startswith('class '):
                        classes_count += 1
                    elif stripped.startswith('async def '):
                        functions_count += 1
                        complexity_score += 0.5  # Async adds complexity
                    
                    # Add complexity for control structures
                    if any(keyword in stripped for keyword in ['if ', 'elif ', 'for ', 'while ', 'try:', 'except:']):
                        complexity_score += 0.2
            
            elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                for line in lines:
                    stripped = line.strip()
                    if ('function ' in stripped or 
                        '=>' in stripped or 
                        'const ' in stripped and '=' in stripped and '=>' in stripped):
                        functions_count += 1
                    elif 'class ' in stripped:
                        classes_count += 1
                    elif 'interface ' in stripped or 'type ' in stripped:
                        complexity_score += 0.3  # TypeScript types add complexity
                    
                    # Add complexity for control structures
                    if any(keyword in stripped for keyword in ['if (', 'for (', 'while (', 'switch (', 'try {']):
                        complexity_score += 0.2
            
            # Calculate final complexity score
            if functions_count > 0:
                complexity_score = complexity_score / functions_count
            
            return functions_count, classes_count, complexity_score
            
        except Exception as e:
            print(f"Warning: Could not analyze complexity for {file_path}: {e}")
            return 0, 0, 0.0

    def generate_recommendations(self, analysis: FileAnalysis) -> List[str]:
        """Generate refactoring recommendations based on file analysis."""
        recommendations = []
        
        # Line count recommendations
        if analysis.lines_count > 500:
            recommendations.append("🚨 CRITICAL: File exceeds 500 LOC - requires immediate refactoring")
        elif analysis.lines_count > self.threshold:
            recommendations.append(f"⚠️  File exceeds {self.threshold} LOC standard - consider refactoring")
        
        # Function/class count recommendations
        if analysis.functions_count > 20:
            recommendations.append("📦 Consider splitting into multiple modules (>20 functions)")
        elif analysis.functions_count > 10:
            recommendations.append("🔄 Consider grouping related functions into classes")
        
        if analysis.classes_count > 5:
            recommendations.append("🏗️  Consider splitting into separate files (>5 classes)")
        
        # Complexity recommendations
        if analysis.complexity_score > 2.0:
            recommendations.append("🧠 High complexity - consider simplifying logic")
        elif analysis.complexity_score > 1.0:
            recommendations.append("🔧 Moderate complexity - review for optimization opportunities")
        
        # Category-specific recommendations
        if analysis.category == FileCategory.BACKEND_PYTHON:
            if analysis.lines_count > 400:
                recommendations.append("🐍 Python: Split into services, repositories, and models")
        elif analysis.category == FileCategory.FRONTEND_REACT:
            if analysis.lines_count > 300:
                recommendations.append("⚛️  React: Break into smaller components and custom hooks")
        elif analysis.category == FileCategory.FRONTEND_TYPESCRIPT:
            if analysis.lines_count > 350:
                recommendations.append("📘 TypeScript: Extract types, interfaces, and utilities")
        
        return recommendations

    def scan_repository(self) -> None:
        """Scan the entire repository for code files."""
        print(f"🔍 Scanning repository: {self.repo_root}")
        print(f"📏 LOC threshold: {self.threshold}")
        print("=" * 60)
        
        for root, dirs, files in os.walk(self.repo_root):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                if file in self.skip_files:
                    continue
                
                file_path = Path(root) / file
                
                # Only analyze code files
                if file_path.suffix.lower() not in self.code_extensions:
                    continue
                
                # Skip very small files (likely not meaningful)
                try:
                    if file_path.stat().st_size < 100:  # Less than 100 bytes
                        continue
                except:
                    continue
                
                # Analyze the file
                lines_count = self.count_lines(file_path)
                
                # Only include files that exceed threshold or are substantial
                if lines_count >= 50:  # Minimum threshold for analysis
                    category = self.categorize_file(file_path)
                    functions_count, classes_count, complexity_score = self.analyze_file_complexity(file_path)
                    
                    # Create relative path for cleaner output
                    relative_path = file_path.relative_to(self.repo_root)
                    
                    analysis = FileAnalysis(
                        path=str(relative_path),
                        category=category,
                        lines_count=lines_count,
                        functions_count=functions_count,
                        classes_count=classes_count,
                        complexity_score=complexity_score,
                        recommendations=[]
                    )
                    
                    # Generate recommendations
                    analysis.recommendations = self.generate_recommendations(analysis)
                    
                    self.analysis_results.append(analysis)

    def generate_report(self, detailed: bool = False) -> str:
        """Generate a comprehensive modularization report."""
        if not self.analysis_results:
            return "No code files found to analyze."
        
        # Sort by lines count (descending)
        self.analysis_results.sort(key=lambda x: x.lines_count, reverse=True)
        
        # Categorize results
        exceeding_threshold = [f for f in self.analysis_results if f.lines_count > self.threshold]
        by_category = {}
        
        for analysis in self.analysis_results:
            category = analysis.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(analysis)
        
        # Generate report
        report = []
        report.append("🎯 MODULARIZATION ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"📊 Total files analyzed: {len(self.analysis_results)}")
        report.append(f"⚠️  Files exceeding {self.threshold} LOC: {len(exceeding_threshold)}")
        report.append(f"📈 Compliance rate: {((len(self.analysis_results) - len(exceeding_threshold)) / len(self.analysis_results) * 100):.1f}%")
        report.append("")
        
        # Summary by category
        report.append("📋 SUMMARY BY CATEGORY")
        report.append("-" * 40)
        
        for category, files in sorted(by_category.items()):
            exceeding_in_category = [f for f in files if f.lines_count > self.threshold]
            avg_loc = sum(f.lines_count for f in files) / len(files)
            
            report.append(f"{category}:")
            report.append(f"  Total files: {len(files)}")
            report.append(f"  Exceeding threshold: {len(exceeding_in_category)}")
            report.append(f"  Average LOC: {avg_loc:.0f}")
            report.append("")
        
        # Detailed analysis of files exceeding threshold
        if exceeding_threshold:
            report.append("🚨 FILES EXCEEDING THRESHOLD")
            report.append("-" * 40)
            
            current_category = None
            for analysis in exceeding_threshold:
                if analysis.category.value != current_category:
                    current_category = analysis.category.value
                    report.append(f"\n📁 {current_category.upper()}")
                    report.append("─" * 30)
                
                report.append(f"\n📄 {analysis.path}")
                report.append(f"   Lines: {analysis.lines_count} LOC")
                report.append(f"   Functions: {analysis.functions_count}")
                report.append(f"   Classes: {analysis.classes_count}")
                report.append(f"   Complexity: {analysis.complexity_score:.1f}")
                
                if analysis.recommendations:
                    report.append("   Recommendations:")
                    for rec in analysis.recommendations:
                        report.append(f"     • {rec}")
        
        # Detailed breakdown if requested
        if detailed:
            report.append("\n\n📊 DETAILED BREAKDOWN")
            report.append("=" * 60)
            
            for category, files in sorted(by_category.items()):
                report.append(f"\n📁 {category.upper()}")
                report.append("─" * 30)
                
                # Sort files in category by LOC
                files.sort(key=lambda x: x.lines_count, reverse=True)
                
                for analysis in files:
                    status = "🚨" if analysis.lines_count > 500 else "⚠️ " if analysis.lines_count > self.threshold else "✅"
                    report.append(f"{status} {analysis.path:<50} {analysis.lines_count:>4} LOC")
        
        # Refactoring priorities
        report.append("\n\n🎯 REFACTORING PRIORITIES")
        report.append("-" * 40)
        
        critical_files = [f for f in exceeding_threshold if f.lines_count > 500]
        high_priority = [f for f in exceeding_threshold if 400 <= f.lines_count <= 500]
        medium_priority = [f for f in exceeding_threshold if self.threshold < f.lines_count < 400]
        
        if critical_files:
            report.append(f"\n🚨 CRITICAL (>500 LOC): {len(critical_files)} files")
            for f in critical_files[:5]:  # Show top 5
                report.append(f"   • {f.path} ({f.lines_count} LOC)")
        
        if high_priority:
            report.append(f"\n⚠️  HIGH PRIORITY (400-500 LOC): {len(high_priority)} files")
            for f in high_priority[:5]:
                report.append(f"   • {f.path} ({f.lines_count} LOC)")
        
        if medium_priority:
            report.append(f"\n🔄 MEDIUM PRIORITY ({self.threshold}-400 LOC): {len(medium_priority)} files")
        
        return "\n".join(report)

    def export_json(self, output_path: str) -> None:
        """Export analysis results to JSON for further processing."""
        data = {
            "metadata": {
                "repository_root": str(self.repo_root),
                "threshold": self.threshold,
                "total_files": len(self.analysis_results),
                "files_exceeding_threshold": len([f for f in self.analysis_results if f.lines_count > self.threshold])
            },
            "files": []
        }
        
        for analysis in self.analysis_results:
            data["files"].append({
                "path": analysis.path,
                "category": analysis.category.value,
                "lines_count": analysis.lines_count,
                "functions_count": analysis.functions_count,
                "classes_count": analysis.classes_count,
                "complexity_score": analysis.complexity_score,
                "exceeds_threshold": analysis.lines_count > self.threshold,
                "recommendations": analysis.recommendations
            })
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Analysis exported to: {output_path}")


def main():
    """Main function for the modularization testing script."""
    parser = argparse.ArgumentParser(description='Analyze repository for modularization compliance')
    parser.add_argument('--threshold', type=int, default=350, 
                       help='LOC threshold for flagging files (default: 350)')
    parser.add_argument('--detailed', action='store_true', 
                       help='Generate detailed breakdown of all files')
    parser.add_argument('--export-json', type=str, 
                       help='Export results to JSON file')
    parser.add_argument('--repo-root', type=str, default='.',
                       help='Repository root directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = ModularizationTester(args.repo_root, args.threshold)
    
    # Scan repository
    tester.scan_repository()
    
    # Generate and display report
    report = tester.generate_report(detailed=args.detailed)
    print(report)
    
    # Export JSON if requested
    if args.export_json:
        tester.export_json(args.export_json)


if __name__ == "__main__":
    main()